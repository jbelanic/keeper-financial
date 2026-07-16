from __future__ import annotations

import io
import zipfile


def eicar_bytes() -> bytes:
    return b"".join(
        (
            b"X5O!P%@AP[4",
            bytes((92,)),
            b"PZX54(P^)7CC)7}$EI",
            b"CAR-STANDARD-ANTIVIRUS-",
            b"TEST-FILE!$H+H*",
        )
    )


def valid_pdf(*, minimum_size: int = 0, comment: bytes | None = None) -> bytes:
    header = b"%PDF-1.4\n"
    objects = [
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n",
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 1 1] "
        b"/Resources << >> /Contents 4 0 R >>\nendobj\n",
        b"4 0 obj\n<< /Length 0 >>\nstream\n\nendstream\nendobj\n",
    ]

    def build(padding: int) -> bytes:
        prefix = header + (b"%" + comment + b"\n" if comment else b"")
        prefix += b"%" + b"p" * (padding - 2) + b"\n" if padding else b""
        offsets: list[int] = []
        body = bytearray(prefix)
        for obj in objects:
            offsets.append(len(body))
            body.extend(obj)
        xref_offset = len(body)
        body.extend(b"xref\n0 5\n0000000000 65535 f \n")
        for offset in offsets:
            body.extend(f"{offset:010d} 00000 n \n".encode())
        body.extend(
            b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n"
            + str(xref_offset).encode()
            + b"\n%%EOF\n"
        )
        return bytes(body)

    initial = build(0)
    if len(initial) >= minimum_size:
        return initial
    padding = minimum_size - len(initial)
    result = build(padding)
    while len(result) != minimum_size:
        padding -= len(result) - minimum_size
        result = build(padding)
    return result


def valid_image(image_format: str) -> bytes:
    from PIL import Image

    output = io.BytesIO()
    Image.new("RGB", (2, 2), color=(23, 45, 67)).save(output, format=image_format)
    return output.getvalue()


def zip_bytes() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("payload.txt", "bounded synthetic payload")
    return output.getvalue()


def valid_docx() -> bytes:
    """A minimal genuine OPC/WordprocessingML package with no optional parts."""
    content_types = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>"""
    package_relationships = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>"""
    document = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:r><w:t>Synthetic document</w:t></w:r></w:p><w:sectPr/></w:body>
</w:document>"""
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", package_relationships)
        archive.writestr("word/document.xml", document)
    return output.getvalue()
