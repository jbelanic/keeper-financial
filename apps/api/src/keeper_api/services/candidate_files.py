from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import PurePath
from typing import BinaryIO


class CandidateFileRejected(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__("candidate document was rejected")
        self.code = code


@dataclass(frozen=True)
class CandidateFile:
    filename: str
    content_type: str
    content: bytes


DOCUMENT_TYPES = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
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


def _docx_signature(data: bytes) -> bool:
    if not data.startswith(b"PK\x03\x04"):
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            names = set(archive.namelist())
            return "[Content_Types].xml" in names and any(
                name.startswith("word/") for name in names
            )
    except (OSError, zipfile.BadZipFile):
        return False


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
    raw_name = (original_filename or "").replace("\\", "/").split("/")[-1]
    clean_name = re.sub(r"[\x00-\x1f\x7f]", "", raw_name).strip()
    if not clean_name or len(clean_name) > 200:
        raise CandidateFileRejected("filename")
    path = PurePath(clean_name)
    extension = path.suffix.lower()
    if extension not in DOCUMENT_TYPES or "." in path.stem:
        raise CandidateFileRejected("extension")
    expected_mime = DOCUMENT_TYPES[extension]
    if (declared_content_type or "").lower() != expected_mime:
        raise CandidateFileRejected("mime")
    data = _read_bounded(stream, maximum)
    signature_matches = (
        data.startswith(b"%PDF-")
        if extension == ".pdf"
        else data.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
        if extension == ".doc"
        else _docx_signature(data)
    )
    if not signature_matches:
        raise CandidateFileRejected("signature")
    return CandidateFile(filename=clean_name, content_type=expected_mime, content=data)
