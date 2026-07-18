from __future__ import annotations

import pytest

from document_samples import valid_docx, valid_image, valid_legacy_doc, valid_pdf, zip_bytes
from keeper_api.services import candidate_files
from keeper_api.services.candidate_files import (
    CANDIDATE_DOCUMENT_POLICY,
    SCAN_ONLY_POLICY,
    DocumentRejected,
    validate_document_bytes,
)

FIVE_MIB = 5 * 1024 * 1024


@pytest.mark.parametrize(
    ("filename", "content_type", "content"),
    [
        ("document.pdf", "application/pdf", valid_pdf()),
        ("image.jpg", "image/jpeg", valid_image("JPEG")),
        ("image.jpeg", "image/jpeg", valid_image("JPEG")),
        ("image.png", "image/png", valid_image("PNG")),
    ],
)
def test_scan_only_policy_accepts_structurally_valid_allowlisted_files(
    filename: str, content_type: str, content: bytes
) -> None:
    validated = validate_document_bytes(
        content,
        original_filename=filename,
        declared_content_type=content_type,
        policy=SCAN_ONLY_POLICY,
    )

    assert validated.filename == filename
    assert validated.content_type == content_type
    assert validated.content == content


@pytest.mark.parametrize(
    ("filename", "content_type", "content", "code"),
    [
        ("document.exe", "application/pdf", valid_pdf(), "unsupported_extension"),
        ("document.pdf", "image/png", valid_pdf(), "declared_mime_mismatch"),
        (
            "document.pdf",
            "application/pdf",
            valid_image("PNG"),
            "detected_mime_mismatch",
        ),
        ("image.png", "image/png", valid_image("JPEG"), "detected_mime_mismatch"),
        (
            "archive.zip",
            "application/zip",
            b"PK\x03\x04synthetic",
            "unsupported_extension",
        ),
        ("vector.svg", "image/svg+xml", b"<svg/>", "unsupported_extension"),
        ("page.html", "text/html", b"<html></html>", "unsupported_extension"),
    ],
)
def test_scan_only_policy_rejects_spoofing_and_unapproved_types(
    filename: str, content_type: str, content: bytes, code: str
) -> None:
    with pytest.raises(DocumentRejected) as exc_info:
        validate_document_bytes(
            content,
            original_filename=filename,
            declared_content_type=content_type,
            policy=SCAN_ONLY_POLICY,
        )

    assert exc_info.value.code == code


@pytest.mark.parametrize(
    ("filename", "content_type", "content"),
    [
        ("document.pdf", "application/pdf", b"%PDF-1.7\nnot structurally valid\n%%EOF"),
        ("image.jpg", "image/jpeg", b"\xff\xd8\xfftruncated"),
        ("image.png", "image/png", b"\x89PNG\r\n\x1a\ntruncated"),
    ],
)
def test_scan_only_policy_rejects_malformed_documents(
    filename: str, content_type: str, content: bytes
) -> None:
    with pytest.raises(DocumentRejected) as exc_info:
        validate_document_bytes(
            content,
            original_filename=filename,
            declared_content_type=content_type,
            policy=SCAN_ONLY_POLICY,
        )

    assert exc_info.value.code in {
        "detected_mime_mismatch",
        "malformed",
        "pdf_structure_invalid",
    }


def test_scan_only_policy_rejects_empty_and_over_limit_but_accepts_exact_boundary() -> None:
    with pytest.raises(DocumentRejected) as empty:
        validate_document_bytes(
            b"",
            original_filename="document.pdf",
            declared_content_type="application/pdf",
            policy=SCAN_ONLY_POLICY,
        )
    assert empty.value.code == "empty_file"

    exact = valid_pdf(minimum_size=FIVE_MIB)
    assert len(exact) == FIVE_MIB
    assert (
        len(
            validate_document_bytes(
                exact,
                original_filename="document.pdf",
                declared_content_type="application/pdf",
                policy=SCAN_ONLY_POLICY,
            ).content
        )
        == FIVE_MIB
    )

    with pytest.raises(DocumentRejected) as oversized:
        validate_document_bytes(
            exact + b"x",
            original_filename="document.pdf",
            declared_content_type="application/pdf",
            policy=SCAN_ONLY_POLICY,
        )
    assert oversized.value.code == "file_too_large"


def test_candidate_pdf_accepts_readable_common_trailing_comments() -> None:
    content = valid_pdf(
        trailing_comments=(b"% bounded generator metadata\n% common printable post-EOF comment\n")
    )

    validated = validate_document_bytes(
        content,
        original_filename="resume.pdf",
        declared_content_type="application/pdf",
        policy=CANDIDATE_DOCUMENT_POLICY,
    )

    assert validated.detected_content_type == "application/pdf"


@pytest.mark.parametrize(
    "content",
    [
        b"%PDF-1.7\n%%EOF\n",
        valid_pdf().replace(b"startxref", b"truncated-xref"),
    ],
    ids=["header-only", "truncated-xref"],
)
def test_candidate_pdf_rejects_structurally_unreadable_files(content: bytes) -> None:
    with pytest.raises(DocumentRejected) as exc_info:
        validate_document_bytes(
            content,
            original_filename="resume.pdf",
            declared_content_type="application/pdf",
            policy=CANDIDATE_DOCUMENT_POLICY,
        )

    assert exc_info.value.code == "pdf_structure_invalid"


@pytest.mark.parametrize(
    ("filename", "content_type", "content"),
    [
        ("document.pdf", "application/pdf", valid_pdf() + zip_bytes()),
        ("image.jpg", "image/jpeg", valid_image("JPEG") + zip_bytes()),
        ("image.png", "image/png", valid_image("PNG") + zip_bytes()),
        ("image.jpg", "image/jpeg", valid_image("JPEG") + b"trailing"),
        ("image.png", "image/png", valid_image("PNG") + b"trailing"),
    ],
    ids=["pdf-zip", "jpeg-zip", "png-zip", "jpeg-trailing", "png-trailing"],
)
def test_structural_validation_rejects_valid_document_with_appended_zip_polyglot(
    filename: str, content_type: str, content: bytes
) -> None:
    with pytest.raises(DocumentRejected) as exc_info:
        validate_document_bytes(
            content,
            original_filename=filename,
            declared_content_type=content_type,
            policy=SCAN_ONLY_POLICY,
        )

    assert exc_info.value.code == (
        "pdf_structure_invalid" if filename.endswith(".pdf") else "malformed"
    )


def test_legacy_doc_rejects_cfb_header_only_file() -> None:
    header_only = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + bytes(504)

    with pytest.raises(DocumentRejected) as exc_info:
        validate_document_bytes(
            header_only,
            original_filename="resume.doc",
            declared_content_type="application/msword",
            policy=CANDIDATE_DOCUMENT_POLICY,
        )

    assert exc_info.value.code == "legacy_doc_invalid"


def test_legacy_doc_accepts_word_cfb_and_rejects_arbitrary_ole_container(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    validated = validate_document_bytes(
        valid_legacy_doc(),
        original_filename="resume.doc",
        declared_content_type="application/msword",
        policy=CANDIDATE_DOCUMENT_POLICY,
    )
    assert validated.detected_content_type in {
        "application/msword",
        "application/x-ole-storage",
    }

    monkeypatch.setattr(
        candidate_files.magic,
        "from_buffer",
        lambda *_args, **_kwargs: "application/x-ole-storage",
    )
    with pytest.raises(DocumentRejected) as exc_info:
        validate_document_bytes(
            valid_legacy_doc(word_stream_name="Workbook"),
            original_filename="resume.doc",
            declared_content_type="application/msword",
            policy=CANDIDATE_DOCUMENT_POLICY,
        )

    assert exc_info.value.code == "legacy_doc_invalid"


def test_docx_rejects_skeletal_non_opc_archive_but_accepts_real_minimal_package() -> None:
    import io
    import zipfile

    skeletal = io.BytesIO()
    with zipfile.ZipFile(skeletal, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types />")
        archive.writestr("word/document.xml", "<document />")

    with pytest.raises(DocumentRejected) as exc_info:
        validate_document_bytes(
            skeletal.getvalue(),
            original_filename="resume.docx",
            declared_content_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
            policy=CANDIDATE_DOCUMENT_POLICY,
        )
    assert exc_info.value.code == "docx_structure_invalid"

    validated = validate_document_bytes(
        valid_docx(),
        original_filename="resume.docx",
        declared_content_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        policy=CANDIDATE_DOCUMENT_POLICY,
    )
    assert validated.content == valid_docx()


def test_docx_accepts_standard_streaming_zip_data_descriptors() -> None:
    content = valid_docx(data_descriptors=True)

    validated = validate_document_bytes(
        content,
        original_filename="resume.docx",
        declared_content_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        policy=CANDIDATE_DOCUMENT_POLICY,
    )

    assert validated.content == content


@pytest.mark.parametrize(
    "detected_mime",
    [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/zip",
    ],
)
def test_docx_accepts_official_or_zip_detection_after_structure_proof(
    monkeypatch: pytest.MonkeyPatch, detected_mime: str
) -> None:
    monkeypatch.setattr(
        candidate_files.magic, "from_buffer", lambda *_args, **_kwargs: detected_mime
    )

    validated = validate_document_bytes(
        valid_docx(data_descriptors=True),
        original_filename="resume.docx",
        declared_content_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        policy=CANDIDATE_DOCUMENT_POLICY,
    )

    assert validated.detected_content_type == detected_mime


def _rewrite_docx(
    *,
    remove: frozenset[str] = frozenset(),
    additions: tuple[tuple[str, bytes], ...] = (),
) -> bytes:
    import io
    import zipfile

    source = zipfile.ZipFile(io.BytesIO(valid_docx()))
    output = io.BytesIO()
    with source, zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as target:
        for info in source.infolist():
            if info.filename not in remove:
                target.writestr(info.filename, source.read(info))
        for name, data in additions:
            target.writestr(name, data)
    return output.getvalue()


def _set_first_zip_entry_flag(content: bytes, flag: int) -> bytes:
    changed = bytearray(content)
    local = changed.find(b"PK\x03\x04")
    central = changed.find(b"PK\x01\x02")
    assert local >= 0 and central >= 0
    current_local = int.from_bytes(changed[local + 6 : local + 8], "little")
    current_central = int.from_bytes(changed[central + 8 : central + 10], "little")
    changed[local + 6 : local + 8] = (current_local | flag).to_bytes(2, "little")
    changed[central + 8 : central + 10] = (current_central | flag).to_bytes(2, "little")
    return bytes(changed)


def _docx_with_external_relationship(target: str) -> bytes:
    relationships = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink" Target="{target}" TargetMode="External"/>
</Relationships>""".encode()
    return _rewrite_docx(additions=(("word/_rels/document.xml.rels", relationships),))


def test_docx_accepts_bounded_external_hyperlink_but_rejects_active_scheme() -> None:
    validated = validate_document_bytes(
        _docx_with_external_relationship("https://example.test/profile"),
        original_filename="resume.docx",
        declared_content_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        policy=CANDIDATE_DOCUMENT_POLICY,
    )
    assert validated.detected_content_type in candidate_files.DOCX_DETECTED_MIME_TYPES

    with pytest.raises(DocumentRejected) as exc_info:
        validate_document_bytes(
            _docx_with_external_relationship("javascript:synthetic"),
            original_filename="resume.docx",
            declared_content_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
            policy=CANDIDATE_DOCUMENT_POLICY,
        )

    assert exc_info.value.code == "docx_structure_invalid"


@pytest.mark.parametrize(
    "content",
    [
        valid_docx()[:-20],
        valid_docx() + b"trailing-payload",
        _rewrite_docx(
            additions=(("word/document.xml", b"<duplicate />"),),
        ),
        _rewrite_docx(additions=(("word/vbaProject.bin", b"synthetic-macro"),)),
        _rewrite_docx(remove=frozenset({"_rels/.rels"})),
        _rewrite_docx(additions=(("../traversal.xml", b"<unsafe />"),)),
        _set_first_zip_entry_flag(valid_docx(), 0x1),
        _rewrite_docx(additions=(("word/high-ratio.bin", bytes(1024 * 1024)),)),
    ],
    ids=[
        "malformed-zip",
        "appended",
        "duplicate-name",
        "macro",
        "missing-root-relationships",
        "path-traversal",
        "encrypted",
        "high-ratio",
    ],
)
def test_docx_rejects_noncanonical_unsafe_or_resource_amplifying_packages(
    content: bytes,
) -> None:
    with pytest.raises(DocumentRejected) as exc_info:
        validate_document_bytes(
            content,
            original_filename="resume.docx",
            declared_content_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
            policy=CANDIDATE_DOCUMENT_POLICY,
        )

    assert exc_info.value.code == "docx_structure_invalid"


def test_docx_rejects_expanded_size_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(candidate_files, "DOCX_MAX_TOTAL_BYTES", 512)

    with pytest.raises(DocumentRejected) as exc_info:
        validate_document_bytes(
            valid_docx(),
            original_filename="resume.docx",
            declared_content_type=(
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ),
            policy=CANDIDATE_DOCUMENT_POLICY,
        )

    assert exc_info.value.code == "docx_structure_invalid"


@pytest.mark.parametrize(
    ("filename", "declared_mime", "detected_mime", "expected_code"),
    [
        ("resume.txt", "text/plain", "text/plain", "unsupported_extension"),
        ("resume.pdf", "application/msword", "application/pdf", "declared_mime_mismatch"),
        ("resume.pdf", "application/pdf", "application/zip", "detected_mime_mismatch"),
    ],
)
def test_candidate_validation_reports_safe_type_categories(
    monkeypatch: pytest.MonkeyPatch,
    filename: str,
    declared_mime: str,
    detected_mime: str,
    expected_code: str,
) -> None:
    monkeypatch.setattr(
        candidate_files.magic, "from_buffer", lambda *_args, **_kwargs: detected_mime
    )

    with pytest.raises(DocumentRejected) as exc_info:
        validate_document_bytes(
            valid_pdf(),
            original_filename=filename,
            declared_content_type=declared_mime,
            policy=CANDIDATE_DOCUMENT_POLICY,
        )

    assert exc_info.value.code == expected_code
