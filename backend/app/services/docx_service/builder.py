from __future__ import annotations

from html import escape
from io import BytesIO
from zipfile import ZIP_DEFLATED, ZipFile


_WORD_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def build_docx_package(document_text: str) -> bytes:
    """Build a minimal valid DOCX OPC package from plain document text.

    This deterministic builder owns binary DOCX correctness. It intentionally
    does not rely on LLM output or text bytes masquerading as .docx content.
    """

    buffer = BytesIO()
    with ZipFile(buffer, mode="w", compression=ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", _content_types_xml())
        package.writestr("_rels/.rels", _root_relationships_xml())
        package.writestr("word/document.xml", _document_xml(document_text))
        package.writestr("word/styles.xml", _styles_xml())
    return buffer.getvalue()


def _content_types_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
"""


def _root_relationships_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
"""


def _document_xml(document_text: str) -> str:
    paragraphs = document_text.splitlines() or [""]
    paragraph_xml = "\n".join(_paragraph_xml(line) for line in paragraphs)
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="{_WORD_NS}">
  <w:body>
{paragraph_xml}
    <w:sectPr>
      <w:pgSz w:w="12240" w:h="15840"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
"""


def _paragraph_xml(text: str) -> str:
    style = ""
    visible_text = text
    if text.startswith("# "):
        style = '<w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
        visible_text = text[2:]
    return f"""    <w:p>
      {style}
      <w:r>
        {_text_xml(visible_text)}
      </w:r>
    </w:p>"""


def _text_xml(text: str) -> str:
    escaped = escape(text, quote=False)
    preserve = ' xml:space="preserve"' if text != text.strip() else ""
    return f"<w:t{preserve}>{escaped}</w:t>"


def _styles_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="{_WORD_NS}">
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal">
    <w:name w:val="Normal"/>
  </w:style>
  <w:style w:type="paragraph" w:styleId="Heading1">
    <w:name w:val="heading 1"/>
    <w:basedOn w:val="Normal"/>
    <w:next w:val="Normal"/>
    <w:pPr>
      <w:outlineLvl w:val="0"/>
    </w:pPr>
    <w:rPr>
      <w:b/>
      <w:sz w:val="32"/>
    </w:rPr>
  </w:style>
</w:styles>
"""
