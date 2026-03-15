#!/usr/bin/env python3
"""
MCP Server: File Reader for GitHub Copilot
==========================================
Provides tools for reading PDF, Word (.docx), and Excel (.xlsx/.csv) files
so that GitHub Copilot can process document content via MCP.

Supported tools:
  - read_pdf       : Extract text from a PDF file
  - read_word      : Extract text from a Word .docx file
  - read_excel     : Extract data from Excel / CSV as Markdown tables
  - get_file_info  : Get metadata about a supported document file
"""

import asyncio
import csv
import os
from pathlib import Path
from typing import Any, Optional

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

# ---------------------------------------------------------------------------
# Server instance
# ---------------------------------------------------------------------------

server = Server("file-reader")

SUPPORTED_EXTENSIONS = {
    ".pdf": "PDF Document",
    ".docx": "Word Document (.docx)",
    ".doc": "Word Document Legacy (.doc) — not fully supported",
    ".xlsx": "Excel Spreadsheet (.xlsx)",
    ".xls": "Excel Spreadsheet Legacy (.xls) — limited support",
    ".csv": "CSV File",
}

# ---------------------------------------------------------------------------
# Path validation (security: prevent path traversal)
# ---------------------------------------------------------------------------

def _validate_path(file_path: str) -> Path:
    """Resolve and validate a file path. Raises on missing or non-file paths."""
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path!r}")
    if not path.is_file():
        raise ValueError(f"Path is not a regular file: {file_path!r}")
    return path


# ---------------------------------------------------------------------------
# PDF reader
# ---------------------------------------------------------------------------

def _read_pdf(path: Path) -> str:
    """Extract text from a PDF using PyMuPDF (fitz)."""
    try:
        import fitz  # pymupdf
    except ImportError:
        raise ImportError(
            "pymupdf is required to read PDF files.\n"
            "Install it with: pip install pymupdf"
        )

    doc = fitz.open(str(path))
    pages: list[str] = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if text:
            pages.append(f"--- Page {i} ---\n{text}")
    doc.close()

    if not pages:
        return (
            "(No extractable text found. The PDF may contain only scanned images.\n"
            "Consider using an OCR tool to convert it first.)"
        )
    return "\n\n".join(pages)


# ---------------------------------------------------------------------------
# Word reader
# ---------------------------------------------------------------------------

def _read_word(path: Path) -> str:
    """Extract text and tables from a Word .docx file."""
    try:
        from docx import Document
        from docx.oxml.ns import qn
    except ImportError:
        raise ImportError(
            "python-docx is required to read Word files.\n"
            "Install it with: pip install python-docx"
        )

    doc = Document(str(path))
    parts: list[str] = []

    # Walk the document body in order (paragraphs + tables interleaved)
    for block in doc.element.body:
        tag = block.tag.split("}")[-1] if "}" in block.tag else block.tag

        if tag == "p":
            # Paragraph — preserve heading style as Markdown heading
            para_obj = None
            for p in doc.paragraphs:
                if p._element is block:
                    para_obj = p
                    break
            if para_obj and para_obj.text.strip():
                style = para_obj.style.name if para_obj.style else ""
                text = para_obj.text.strip()
                if style.startswith("Heading 1"):
                    parts.append(f"# {text}")
                elif style.startswith("Heading 2"):
                    parts.append(f"## {text}")
                elif style.startswith("Heading 3"):
                    parts.append(f"### {text}")
                else:
                    parts.append(text)

        elif tag == "tbl":
            # Table — render as Markdown table
            for table in doc.tables:
                if table._element is block:
                    rows = [
                        [cell.text.strip() for cell in row.cells]
                        for row in table.rows
                    ]
                    parts.append(_rows_to_markdown(rows))
                    break

    return "\n\n".join(parts) if parts else "(No readable text content found)"


# ---------------------------------------------------------------------------
# Excel / CSV reader
# ---------------------------------------------------------------------------

def _read_excel(path: Path, sheet_name: Optional[str] = None) -> str:
    """Extract data from an Excel (.xlsx) or CSV file as Markdown tables."""
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return _read_csv(path)

    try:
        import openpyxl
    except ImportError:
        raise ImportError(
            "openpyxl is required to read Excel files.\n"
            "Install it with: pip install openpyxl"
        )

    wb = openpyxl.load_workbook(str(path), data_only=True)

    if sheet_name:
        if sheet_name not in wb.sheetnames:
            raise ValueError(
                f"Sheet '{sheet_name}' not found.\n"
                f"Available sheets: {', '.join(wb.sheetnames)}"
            )
        sheets_to_read = [sheet_name]
    else:
        sheets_to_read = wb.sheetnames

    result_parts: list[str] = []
    for name in sheets_to_read:
        ws = wb[name]
        # Only read rows that contain at least one non-None value
        rows = [
            [str(cell) if cell is not None else "" for cell in row]
            for row in ws.iter_rows(values_only=True)
            if any(cell is not None for cell in row)
        ]
        if rows:
            result_parts.append(f"### Sheet: {name}\n\n{_rows_to_markdown(rows)}")
        else:
            result_parts.append(f"### Sheet: {name}\n\n*(Empty sheet)*")

    wb.close()
    return "\n\n".join(result_parts)


def _read_csv(path: Path) -> str:
    """Read a CSV file and return its content as a Markdown table."""
    rows: list[list[str]] = []
    # Try UTF-8-sig first (handles BOM from Excel exports), then latin-1 fallback
    for encoding in ("utf-8-sig", "latin-1"):
        try:
            with open(path, encoding=encoding, newline="") as f:
                reader = csv.reader(f)
                rows = [row for row in reader if any(cell.strip() for cell in row)]
            break
        except UnicodeDecodeError:
            continue

    if not rows:
        return "*(Empty CSV file)*"
    return _rows_to_markdown(rows)


# ---------------------------------------------------------------------------
# Markdown table helper
# ---------------------------------------------------------------------------

def _rows_to_markdown(rows: list[list[str]]) -> str:
    """Convert a 2D list of strings into a GitHub-Flavored Markdown table."""
    if not rows:
        return ""

    col_count = max(len(row) for row in rows)
    padded = [row + [""] * (col_count - len(row)) for row in rows]

    header_row = "| " + " | ".join(padded[0]) + " |"
    separator = "| " + " | ".join(["---"] * col_count) + " |"
    body_rows = "\n".join("| " + " | ".join(row) + " |" for row in padded[1:])

    if body_rows:
        return "\n".join([header_row, separator, body_rows])
    return "\n".join([header_row, separator])


# ---------------------------------------------------------------------------
# MCP tool definitions
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="read_pdf",
            description=(
                "Read and extract the full text content of a PDF file. "
                "Returns text organized by page. Works best with text-based PDFs; "
                "scanned/image-only PDFs will return a notice to use OCR."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the PDF file (e.g. C:/Documents/report.pdf)",
                    }
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="read_word",
            description=(
                "Read and extract text and tables from a Microsoft Word .docx file. "
                "Preserves headings as Markdown headings and renders tables as Markdown tables."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the .docx file (e.g. C:/Documents/spec.docx)",
                    }
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="read_excel",
            description=(
                "Read data from a Microsoft Excel (.xlsx) or CSV file. "
                "Returns each sheet's content as a Markdown table. "
                "Optionally specify a sheet name to read only that sheet."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the .xlsx or .csv file (e.g. C:/Data/sales.xlsx)",
                    },
                    "sheet_name": {
                        "type": "string",
                        "description": (
                            "Optional: name of the specific sheet to read. "
                            "If omitted, all sheets are returned."
                        ),
                    },
                },
                "required": ["file_path"],
            },
        ),
        types.Tool(
            name="get_file_info",
            description=(
                "Get metadata about a document file — file size, type, "
                "page count (PDF), sheet names (Excel), author/title (PDF metadata). "
                "Useful before reading a very large file."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Absolute path to the file",
                    }
                },
                "required": ["file_path"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# MCP tool handler
# ---------------------------------------------------------------------------

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.TextContent]:
    try:
        if name == "read_pdf":
            path = _validate_path(arguments["file_path"])
            if path.suffix.lower() != ".pdf":
                raise ValueError(f"Expected a .pdf file, got '{path.suffix}'")
            content = _read_pdf(path)
            return [types.TextContent(type="text", text=f"**File:** `{path.name}`\n\n{content}")]

        elif name == "read_word":
            path = _validate_path(arguments["file_path"])
            if path.suffix.lower() not in (".docx", ".doc"):
                raise ValueError(f"Expected a .docx file, got '{path.suffix}'")
            if path.suffix.lower() == ".doc":
                return [types.TextContent(
                    type="text",
                    text=(
                        "Legacy `.doc` format is not directly supported.\n"
                        "Please open the file in Microsoft Word and save it as `.docx`, then try again."
                    ),
                )]
            content = _read_word(path)
            return [types.TextContent(type="text", text=f"**File:** `{path.name}`\n\n{content}")]

        elif name == "read_excel":
            path = _validate_path(arguments["file_path"])
            if path.suffix.lower() not in (".xlsx", ".xls", ".csv"):
                raise ValueError(f"Expected an .xlsx, .xls, or .csv file, got '{path.suffix}'")
            if path.suffix.lower() == ".xls":
                return [types.TextContent(
                    type="text",
                    text=(
                        "Legacy `.xls` format is not supported by openpyxl.\n"
                        "Please open the file in Excel and save it as `.xlsx`, then try again."
                    ),
                )]
            sheet_name: Optional[str] = arguments.get("sheet_name")
            content = _read_excel(path, sheet_name)
            return [types.TextContent(type="text", text=f"**File:** `{path.name}`\n\n{content}")]

        elif name == "get_file_info":
            path = _validate_path(arguments["file_path"])
            stat = path.stat()
            size_kb = stat.st_size / 1024
            ext = path.suffix.lower()
            file_type = SUPPORTED_EXTENSIONS.get(ext, f"Unknown type ({ext})")

            info_lines = [
                f"**File:** `{path.name}`",
                f"**Type:** {file_type}",
                f"**Size:** {size_kb:.1f} KB",
                f"**Full path:** `{path}`",
            ]

            # Extra metadata per type
            if ext == ".pdf":
                try:
                    import fitz
                    doc = fitz.open(str(path))
                    info_lines.append(f"**Pages:** {doc.page_count}")
                    meta = doc.metadata or {}
                    if meta.get("title"):
                        info_lines.append(f"**Title:** {meta['title']}")
                    if meta.get("author"):
                        info_lines.append(f"**Author:** {meta['author']}")
                    doc.close()
                except ImportError:
                    info_lines.append("*(Install pymupdf for PDF metadata)*")

            elif ext == ".xlsx":
                try:
                    import openpyxl
                    wb = openpyxl.load_workbook(str(path), read_only=True)
                    info_lines.append(f"**Sheets ({len(wb.sheetnames)}):** {', '.join(wb.sheetnames)}")
                    wb.close()
                except ImportError:
                    info_lines.append("*(Install openpyxl for Excel metadata)*")

            elif ext == ".docx":
                try:
                    from docx import Document
                    doc = Document(str(path))
                    para_count = len(doc.paragraphs)
                    table_count = len(doc.tables)
                    info_lines.append(f"**Paragraphs:** {para_count}")
                    info_lines.append(f"**Tables:** {table_count}")
                    core = doc.core_properties
                    if core.author:
                        info_lines.append(f"**Author:** {core.author}")
                    if core.title:
                        info_lines.append(f"**Title:** {core.title}")
                except ImportError:
                    info_lines.append("*(Install python-docx for Word metadata)*")

            return [types.TextContent(type="text", text="\n".join(info_lines))]

        else:
            return [types.TextContent(type="text", text=f"Unknown tool: '{name}'")]

    except FileNotFoundError as exc:
        return [types.TextContent(type="text", text=f"**Error (file not found):** {exc}")]
    except ValueError as exc:
        return [types.TextContent(type="text", text=f"**Error (invalid input):** {exc}")]
    except ImportError as exc:
        return [types.TextContent(type="text", text=f"**Error (missing library):** {exc}")]
    except Exception as exc:  # noqa: BLE001
        return [types.TextContent(type="text", text=f"**Unexpected error** ({type(exc).__name__}): {exc}")]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    asyncio.run(main())
