"""解析层：把 docx / pdf 抽成结构化文本。任何情况不裸抛 500。"""

from pathlib import Path

from docx import Document
import pdfplumber

from ..constants import ERR_NO_TEXT_LAYER
from ..errors import (
    EmptyFileError,
    EncryptedPdfError,
    NoTextLayerError,
    UnsupportedTypeError,
)

SUPPORTED_EXTS = {".docx", ".pdf"}
PDF_MIN_CHARS = 50  # 少于该字数判定为无文本层扫描件
DOCX_NO_TEXT_MSG = "该 docx 无可提取正文，请检查文件是否损坏"


def parse_file(path) -> dict:
    """解析文件，返回 {text, char_count, source_type, warnings}。"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"文件不存在: {p}")

    size = p.stat().st_size
    if size == 0:
        raise EmptyFileError()

    ext = p.suffix.lower()
    if ext not in SUPPORTED_EXTS:
        raise UnsupportedTypeError()

    if ext == ".docx":
        return _parse_docx(p)
    return _parse_pdf(p)


def _parse_docx(p: Path) -> dict:
    try:
        doc = Document(str(p))
    except Exception as exc:  # 损坏 docx 不裸抛 500，文案按 docx 类型给
        msg = str(exc).lower()
        if "encrypted" in msg or "password" in msg:
            raise EncryptedPdfError("该 docx 已加密，无法解析") from exc
        raise NoTextLayerError(DOCX_NO_TEXT_MSG) from exc

    parts = []
    for para in doc.paragraphs:
        parts.append(para.text)
    for table in doc.tables:
        for row in table.rows:
            parts.append(" | ".join(cell.text for cell in row.cells))
    text = "\n".join(parts)

    if len(text.strip()) < PDF_MIN_CHARS:
        raise NoTextLayerError(DOCX_NO_TEXT_MSG)

    return {
        "text": text,
        "char_count": len(text),
        "source_type": "docx",
        "warnings": [],
    }


def _parse_pdf(p: Path) -> dict:
    try:
        with pdfplumber.open(str(p)) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
    except Exception as exc:  # 不裸抛，统一映射为契约错误码
        msg = str(exc).lower()
        if "encrypted" in msg or "password" in msg or "crypto" in msg:
            raise EncryptedPdfError() from exc
        raise NoTextLayerError() from exc

    text = "\n".join(pages)
    if len(text.strip()) < PDF_MIN_CHARS:
        raise NoTextLayerError()

    return {
        "text": text,
        "char_count": len(text),
        "source_type": "pdf",
        "warnings": [],
    }
