from __future__ import annotations

import pytest

from document_samples import valid_docx, valid_image, valid_pdf, zip_bytes
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
        ("document.exe", "application/pdf", valid_pdf(), "extension"),
        ("document.pdf", "image/png", valid_pdf(), "mime"),
        ("document.pdf", "application/pdf", valid_image("PNG"), "detected_mime"),
        ("image.png", "image/png", valid_image("JPEG"), "detected_mime"),
        ("archive.zip", "application/zip", b"PK\x03\x04synthetic", "extension"),
        ("vector.svg", "image/svg+xml", b"<svg/>", "extension"),
        ("page.html", "text/html", b"<html></html>", "extension"),
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

    assert exc_info.value.code in {"detected_mime", "malformed"}


def test_scan_only_policy_rejects_empty_and_over_limit_but_accepts_exact_boundary() -> None:
    with pytest.raises(DocumentRejected) as empty:
        validate_document_bytes(
            b"",
            original_filename="document.pdf",
            declared_content_type="application/pdf",
            policy=SCAN_ONLY_POLICY,
        )
    assert empty.value.code == "empty"

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
    assert oversized.value.code == "oversized"


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

    assert exc_info.value.code == "malformed"


def test_legacy_doc_rejects_cfb_header_only_file() -> None:
    header_only = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + bytes(504)

    with pytest.raises(DocumentRejected) as exc_info:
        validate_document_bytes(
            header_only,
            original_filename="resume.doc",
            declared_content_type="application/msword",
            policy=CANDIDATE_DOCUMENT_POLICY,
        )

    assert exc_info.value.code == "malformed"


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
    assert exc_info.value.code == "malformed"

    validated = validate_document_bytes(
        valid_docx(),
        original_filename="resume.docx",
        declared_content_type=(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ),
        policy=CANDIDATE_DOCUMENT_POLICY,
    )
    assert validated.content == valid_docx()


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


@pytest.mark.parametrize(
    "content",
    [
        valid_docx() + b"trailing-payload",
        _rewrite_docx(
            additions=(("word/document.xml", b"<duplicate />"),),
        ),
        _rewrite_docx(additions=(("word/vbaProject.bin", b"synthetic-macro"),)),
        _rewrite_docx(remove=frozenset({"_rels/.rels"})),
        _rewrite_docx(additions=(("word/high-ratio.bin", bytes(1024 * 1024)),)),
    ],
    ids=["appended", "duplicate-name", "macro", "missing-root-relationships", "high-ratio"],
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

    assert exc_info.value.code == "malformed"
