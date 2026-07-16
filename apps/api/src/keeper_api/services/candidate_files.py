from __future__ import annotations

import io
import posixpath
import re
import struct
import warnings
import zipfile
from dataclasses import dataclass, replace
from pathlib import PurePath
from typing import BinaryIO
from urllib.parse import unquote, urlsplit

import magic
import olefile
from defusedxml import ElementTree
from defusedxml.common import DefusedXmlException
from PIL import Image
from pypdf import PdfReader
from pypdf.errors import PyPdfError

FIVE_MIB = 5 * 1024 * 1024
TEN_MIB = 10 * 1024 * 1024
MAX_IMAGE_PIXELS = 20_000_000
PDF_TRAILING_WHITESPACE = b"\x00\x09\x0a\x0c\x0d\x20"
PNG_IEND = b"\x00\x00\x00\x00IEND\xaeB\x60\x82"
DOCX_MAX_ENTRIES = 256
DOCX_MAX_ENTRY_BYTES = 8 * 1024 * 1024
DOCX_MAX_XML_BYTES = 2 * 1024 * 1024
DOCX_MAX_TOTAL_BYTES = 20 * 1024 * 1024
DOCX_MAX_COMPRESSION_RATIO = 100
DOCX_MAX_XML_ELEMENTS = 10_000
DOCX_MAX_XML_DEPTH = 64
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"
RELATIONSHIPS_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
WORDPROCESSING_NAMESPACES = frozenset(
    {
        "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
        "http://purl.oclc.org/ooxml/wordprocessingml/main",
    }
)
OFFICE_DOCUMENT_RELATIONSHIPS = frozenset(
    {
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument",
        "http://purl.oclc.org/ooxml/officeDocument/relationships/officeDocument",
    }
)
RELATIONSHIPS_CONTENT_TYPE = "application/vnd.openxmlformats-package.relationships+xml"
WORD_DOCUMENT_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
)
Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS


class DocumentRejected(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__("document was rejected")
        self.code = code


class CandidateFileRejected(DocumentRejected):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.args = ("candidate document was rejected",)


@dataclass(frozen=True)
class CandidateFile:
    filename: str
    content_type: str
    detected_content_type: str
    content: bytes


@dataclass(frozen=True)
class DocumentPolicy:
    maximum_bytes: int
    extension_mime_types: dict[str, str]


SCAN_ONLY_POLICY = DocumentPolicy(
    maximum_bytes=FIVE_MIB,
    extension_mime_types={
        ".pdf": "application/pdf",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    },
)
CANDIDATE_DOCUMENT_POLICY = DocumentPolicy(
    maximum_bytes=TEN_MIB,
    extension_mime_types={
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
)
CATEGORIES = frozenset({"resume", "cover_letter"})


def _read_bounded(stream: BinaryIO, maximum: int) -> bytes:
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = stream.read(min(64 * 1024, maximum + 1 - size))
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
        if size > maximum:
            raise CandidateFileRejected("oversized")
    data = b"".join(chunks)
    if not data:
        raise CandidateFileRejected("empty")
    return data


def _safe_filename(original_filename: str | None) -> tuple[str, str]:
    raw_name = (original_filename or "").replace("\\", "/").split("/")[-1]
    clean_name = re.sub(r"[\x00-\x1f\x7f]", "", raw_name).strip()
    if not clean_name or len(clean_name) > 200:
        raise DocumentRejected("filename")
    path = PurePath(clean_name)
    extension = path.suffix.lower()
    if "." in path.stem:
        raise DocumentRejected("extension")
    return clean_name, extension


def _detected_mime(content: bytes) -> str:
    try:
        detected = magic.from_buffer(content, mime=True)
    except magic.MagicException as exc:
        raise DocumentRejected("detected_mime") from exc
    if not isinstance(detected, str):
        raise DocumentRejected("detected_mime")
    return detected.lower()


def _validate_pdf(content: bytes) -> None:
    eof = content.rfind(b"%%EOF")
    if eof < 0 or any(byte not in PDF_TRAILING_WHITESPACE for byte in content[eof + 5 :]):
        raise DocumentRejected("malformed")
    try:
        reader = PdfReader(io.BytesIO(content), strict=True)
        if reader.is_encrypted or len(reader.pages) < 1:
            raise DocumentRejected("malformed")
    except (OSError, PyPdfError, ValueError) as exc:
        raise DocumentRejected("malformed") from exc


def _validate_image(content: bytes, expected_mime: str) -> None:
    expected_format = {"image/jpeg": "JPEG", "image/png": "PNG"}[expected_mime]
    if (expected_mime == "image/jpeg" and not content.endswith(b"\xff\xd9")) or (
        expected_mime == "image/png" and not content.endswith(PNG_IEND)
    ):
        raise DocumentRejected("malformed")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as image:
                if image.format != expected_format or image.width < 1 or image.height < 1:
                    raise DocumentRejected("malformed")
                image.verify()
    except (
        OSError,
        SyntaxError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise DocumentRejected("malformed") from exc


def _validate_doc(content: bytes) -> None:
    if (
        not content.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
        or len(content) < 512
        or len(content) % 512 != 0
    ):
        raise DocumentRejected("malformed")
    try:
        with olefile.OleFileIO(
            io.BytesIO(content), raise_defects=olefile.DEFECT_INCORRECT
        ) as archive:
            if archive.parsing_issues or not archive.exists("WordDocument"):
                raise DocumentRejected("malformed")
            if archive.get_type("WordDocument") != olefile.STGTY_STREAM:
                raise DocumentRejected("malformed")
            word_stream = archive.openstream("WordDocument")
            fib = word_stream.read(32)
            if len(fib) != 32 or struct.unpack_from("<H", fib)[0] != 0xA5EC:
                raise DocumentRejected("malformed")
            flags = struct.unpack_from("<H", fib, 10)[0]
            table_name = "1Table" if flags & 0x0200 else "0Table"
            if (
                not archive.exists(table_name)
                or archive.get_type(table_name) != olefile.STGTY_STREAM
                or archive.get_size(table_name) < 1
            ):
                raise DocumentRejected("malformed")
    except (OSError, TypeError, ValueError, struct.error) as exc:
        raise DocumentRejected("malformed") from exc


def _validate_zip_layout(content: bytes, entries: list[zipfile.ZipInfo]) -> None:
    eocd_offset = content.rfind(b"PK\x05\x06", max(0, len(content) - 65_557))
    if eocd_offset < 0 or eocd_offset + 22 > len(content):
        raise DocumentRejected("malformed")
    try:
        (
            signature,
            disk_number,
            central_disk,
            disk_entries,
            total_entries,
            central_size,
            central_offset,
            comment_length,
        ) = struct.unpack_from("<4s4H2LH", content, eocd_offset)
    except struct.error as exc:
        raise DocumentRejected("malformed") from exc
    if (
        signature != b"PK\x05\x06"
        or disk_number != 0
        or central_disk != 0
        or disk_entries != total_entries
        or total_entries != len(entries)
        or total_entries in {0, 0xFFFF}
        or central_size == 0xFFFFFFFF
        or central_offset == 0xFFFFFFFF
        or comment_length != 0
        or eocd_offset + 22 != len(content)
        or central_offset + central_size != eocd_offset
    ):
        raise DocumentRejected("malformed")

    expected_offset = 0
    for entry in sorted(entries, key=lambda item: item.header_offset):
        if entry.header_offset != expected_offset or expected_offset + 30 > central_offset:
            raise DocumentRejected("malformed")
        try:
            local = struct.unpack_from("<4s5H3L2H", content, expected_offset)
        except struct.error as exc:
            raise DocumentRejected("malformed") from exc
        if (
            local[0] != b"PK\x03\x04"
            or local[2] & 0x08
            or local[2] != entry.flag_bits
            or local[7] != entry.compress_size
            or local[8] != entry.file_size
        ):
            raise DocumentRejected("malformed")
        expected_offset += 30 + local[9] + local[10] + entry.compress_size
    if expected_offset != central_offset:
        raise DocumentRejected("malformed")


def _safe_package_name(name: str) -> str:
    decoded = unquote(name)
    if (
        not decoded
        or "\\" in decoded
        or decoded.startswith("/")
        or any(ord(character) < 32 for character in decoded)
        or any(part in {"", ".", ".."} for part in decoded.rstrip("/").split("/"))
    ):
        raise DocumentRejected("malformed")
    return decoded


def _xml_records(
    archive: zipfile.ZipFile, entry: zipfile.ZipInfo
) -> tuple[str, list[tuple[str, dict[str, str]]]]:
    if entry.file_size > DOCX_MAX_XML_BYTES:
        raise DocumentRejected("malformed")
    root_tag = ""
    records: list[tuple[str, dict[str, str]]] = []
    depth = 0
    count = 0
    try:
        with archive.open(entry) as stream:
            for event, element in ElementTree.iterparse(stream, events=("start", "end")):
                if event == "start":
                    depth += 1
                    count += 1
                    if depth > DOCX_MAX_XML_DEPTH or count > DOCX_MAX_XML_ELEMENTS:
                        raise DocumentRejected("malformed")
                    if not root_tag:
                        root_tag = element.tag
                    records.append((element.tag, dict(element.attrib)))
                else:
                    depth -= 1
                    element.clear()
    except (DefusedXmlException, ElementTree.ParseError, OSError, ValueError) as exc:
        raise DocumentRejected("malformed") from exc
    if not root_tag or depth != 0:
        raise DocumentRejected("malformed")
    return root_tag, records


def _relationship_target(relationships_name: str, target: str) -> str:
    parsed = urlsplit(unquote(target))
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment or not parsed.path:
        raise DocumentRejected("malformed")
    if relationships_name == "_rels/.rels":
        base = ""
    else:
        marker = "/_rels/"
        if marker not in relationships_name or not relationships_name.endswith(".rels"):
            raise DocumentRejected("malformed")
        prefix, relationship_file = relationships_name.split(marker, 1)
        source = f"{prefix}/{relationship_file[:-5]}"
        base = posixpath.dirname(source)
    resolved = posixpath.normpath(posixpath.join(base, parsed.path.lstrip("/")))
    if resolved == ".." or resolved.startswith("../"):
        raise DocumentRejected("malformed")
    return resolved


def _validate_docx_relationships(
    relationships_name: str,
    records: list[tuple[str, dict[str, str]]],
    names: set[str],
) -> bool:
    root = f"{{{RELATIONSHIPS_NS}}}Relationships"
    relationship = f"{{{RELATIONSHIPS_NS}}}Relationship"
    if not records or records[0][0] != root or any(tag not in {root, relationship} for tag, _ in records):
        raise DocumentRejected("malformed")
    identifiers: set[str] = set()
    office_document = False
    for tag, attributes in records[1:]:
        if tag != relationship:
            raise DocumentRejected("malformed")
        identifier = attributes.get("Id", "")
        relationship_type = attributes.get("Type", "")
        target = attributes.get("Target", "")
        if (
            not identifier
            or identifier in identifiers
            or attributes.get("TargetMode", "Internal") != "Internal"
        ):
            raise DocumentRejected("malformed")
        identifiers.add(identifier)
        resolved = _relationship_target(relationships_name, target)
        if resolved not in names:
            raise DocumentRejected("malformed")
        if relationship_type in OFFICE_DOCUMENT_RELATIONSHIPS:
            if relationships_name != "_rels/.rels" or resolved != "word/document.xml":
                raise DocumentRejected("malformed")
            office_document = True
    return office_document


def _validate_docx(content: bytes) -> None:
    if not content.startswith(b"PK\x03\x04"):
        raise DocumentRejected("malformed")
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            _validate_zip_layout(content, entries)
            decoded_names = [_safe_package_name(entry.filename) for entry in entries]
            names = set(decoded_names)
            if len(names) != len(entries) or len({name.casefold() for name in names}) != len(names):
                raise DocumentRejected("malformed")
            required = {"[Content_Types].xml", "_rels/.rels", "word/document.xml"}
            if not required.issubset(names) or len(entries) > DOCX_MAX_ENTRIES:
                raise DocumentRejected("malformed")
            if any("vbaproject.bin" in name.casefold() for name in names):
                raise DocumentRejected("malformed")
            total_uncompressed = 0
            xml_summaries: dict[str, tuple[str, list[tuple[str, dict[str, str]]]]] = {}
            for entry, decoded_name in zip(entries, decoded_names, strict=True):
                if (
                    entry.flag_bits & 0x1
                    or entry.compress_type not in {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
                    or entry.file_size > DOCX_MAX_ENTRY_BYTES
                    or (entry.file_size and entry.compress_size == 0)
                    or (
                        entry.compress_size
                        and entry.file_size / entry.compress_size > DOCX_MAX_COMPRESSION_RATIO
                    )
                ):
                    raise DocumentRejected("malformed")
                total_uncompressed += entry.file_size
                if total_uncompressed > DOCX_MAX_TOTAL_BYTES:
                    raise DocumentRejected("malformed")
                if decoded_name.endswith((".xml", ".rels")):
                    xml_summaries[decoded_name] = _xml_records(archive, entry)
            if archive.testzip() is not None:
                raise DocumentRejected("malformed")

            content_root, content_records = xml_summaries["[Content_Types].xml"]
            types_tag = f"{{{CONTENT_TYPES_NS}}}Types"
            default_tag = f"{{{CONTENT_TYPES_NS}}}Default"
            override_tag = f"{{{CONTENT_TYPES_NS}}}Override"
            if content_root != types_tag or any(
                tag not in {types_tag, default_tag, override_tag}
                for tag, _attributes in content_records
            ):
                raise DocumentRejected("malformed")
            defaults: dict[str, str] = {}
            overrides: dict[str, str] = {}
            for tag, attributes in content_records[1:]:
                content_type = attributes.get("ContentType", "")
                if not content_type or "macroenabled" in content_type.casefold() or "vba" in content_type.casefold():
                    raise DocumentRejected("malformed")
                if tag == default_tag:
                    extension = attributes.get("Extension", "").casefold()
                    if not extension or extension in defaults:
                        raise DocumentRejected("malformed")
                    defaults[extension] = content_type
                elif tag == override_tag:
                    part_name = unquote(attributes.get("PartName", ""))
                    key = part_name.casefold()
                    if not part_name.startswith("/") or key in overrides:
                        raise DocumentRejected("malformed")
                    overrides[key] = content_type
            if defaults.get("rels") != RELATIONSHIPS_CONTENT_TYPE or overrides.get(
                "/word/document.xml"
            ) != WORD_DOCUMENT_CONTENT_TYPE:
                raise DocumentRejected("malformed")
            for name in names - {"[Content_Types].xml"}:
                if name.endswith("/"):
                    continue
                extension = name.rsplit(".", 1)[-1].casefold() if "." in name else ""
                if f"/{name}".casefold() not in overrides and extension not in defaults:
                    raise DocumentRejected("malformed")

            office_relationships = 0
            for name, (_root, records) in xml_summaries.items():
                if name.endswith(".rels"):
                    office_relationships += int(
                        _validate_docx_relationships(name, records, names)
                    )
            if office_relationships != 1:
                raise DocumentRejected("malformed")

            document_root, document_records = xml_summaries["word/document.xml"]
            if not any(
                document_root == f"{{{namespace}}}document"
                and any(tag == f"{{{namespace}}}body" for tag, _ in document_records)
                for namespace in WORDPROCESSING_NAMESPACES
            ):
                raise DocumentRejected("malformed")
    except (
        DefusedXmlException,
        KeyError,
        OSError,
        ElementTree.ParseError,
        zipfile.BadZipFile,
    ) as exc:
        raise DocumentRejected("malformed") from exc


def validate_document_bytes(
    content: bytes,
    *,
    original_filename: str | None,
    declared_content_type: str | None,
    policy: DocumentPolicy,
) -> CandidateFile:
    if not content:
        raise DocumentRejected("empty")
    if len(content) > policy.maximum_bytes:
        raise DocumentRejected("oversized")
    clean_name, extension = _safe_filename(original_filename)
    if extension not in policy.extension_mime_types:
        raise DocumentRejected("extension")
    expected_mime = policy.extension_mime_types[extension]
    if (declared_content_type or "").lower() != expected_mime:
        raise DocumentRejected("mime")
    image_signature_matches = (
        expected_mime == "image/png" and content.startswith(b"\x89PNG\r\n\x1a\n")
    ) or (expected_mime == "image/jpeg" and content.startswith(b"\xff\xd8\xff"))
    if image_signature_matches:
        _validate_image(content, expected_mime)
    detected_mime = _detected_mime(content)
    accepted_detected_types = {expected_mime}
    if extension == ".doc":
        accepted_detected_types.add("application/x-ole-storage")
    elif extension == ".docx":
        accepted_detected_types.add("application/zip")
    if detected_mime not in accepted_detected_types:
        raise DocumentRejected("detected_mime")
    if expected_mime == "application/pdf":
        _validate_pdf(content)
    elif expected_mime in {"image/jpeg", "image/png"} and not image_signature_matches:
        _validate_image(content, expected_mime)
    elif extension == ".doc":
        _validate_doc(content)
    elif extension == ".docx":
        _validate_docx(content)
    return CandidateFile(
        filename=clean_name,
        content_type=expected_mime,
        detected_content_type=detected_mime,
        content=content,
    )


def validate_candidate_file(
    stream: BinaryIO,
    *,
    category: str,
    original_filename: str | None,
    declared_content_type: str | None,
    maximum: int,
) -> CandidateFile:
    if category not in CATEGORIES:
        raise CandidateFileRejected("category")
    try:
        content = _read_bounded(stream, maximum)
        return validate_document_bytes(
            content,
            original_filename=original_filename,
            declared_content_type=declared_content_type,
            policy=replace(CANDIDATE_DOCUMENT_POLICY, maximum_bytes=maximum),
        )
    except DocumentRejected as exc:
        if isinstance(exc, CandidateFileRejected):
            raise
        raise CandidateFileRejected(exc.code) from exc
