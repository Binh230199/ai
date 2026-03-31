from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse


def normalize_input_path(raw_value: str) -> Path:
    if raw_value.startswith("file://"):
        parsed = urlparse(raw_value)
        parsed_path = unquote(parsed.path or "")
        if re.match(r"^/[A-Za-z]:", parsed_path):
            parsed_path = parsed_path[1:]
        if parsed.netloc and parsed.netloc not in {"", "localhost"}:
            parsed_path = f"//{parsed.netloc}{parsed_path}"
        return Path(parsed_path)
    return Path(raw_value)


def extract_with_pymupdf(pdf_path: Path) -> tuple[str, str]:
    import fitz  # type: ignore

    chunks: list[str] = []
    document = fitz.open(pdf_path)
    try:
        for index, page in enumerate(document):
            chunks.append(f"[[PAGE {index + 1}]]\n{page.get_text('text')}")
    finally:
        document.close()
    return "\n\n".join(chunks), "pymupdf"


def extract_with_pypdf(pdf_path: Path) -> tuple[str, str]:
    from pypdf import PdfReader  # type: ignore

    reader = PdfReader(str(pdf_path))
    chunks: list[str] = []
    for index, page in enumerate(reader.pages):
        chunks.append(f"[[PAGE {index + 1}]]\n{page.extract_text() or ''}")
    return "\n\n".join(chunks), "pypdf"


def extract_pdf_text(pdf_path: Path) -> tuple[str, str]:
    errors: list[str] = []
    for extractor in (extract_with_pymupdf, extract_with_pypdf):
        try:
            return extractor(pdf_path)
        except Exception as exc:  # pragma: no cover - fallback path
            errors.append(f"{extractor.__name__}: {exc}")
    raise RuntimeError(
        "Failed to parse the PDF. Install dependencies from requirements.txt. "
        f"Attempted extractors: {' | '.join(errors)}"
    )


def normalize_lines(raw_text: str) -> list[str]:
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"\s+", " ", line).strip() for line in normalized.split("\n")]
    return lines


def classify_heading(line: str) -> tuple[bool, int]:
    if re.match(r"^[A-Z]\d+(?:-\d+)+\b", line):
        return True, 3
    numbered = re.match(r"^(\d+(?:\.\d+)*)\s+.+$", line)
    if numbered:
        level = min(6, 1 + numbered.group(1).count(".") + 1)
        return True, level
    if len(line) <= 80 and re.match(r"^[A-Z0-9 /(),.:_-]+$", line):
        return True, 2
    return False, 0


def to_markdown(raw_text: str) -> str:
    output: list[str] = []
    previous_blank = False
    for line in normalize_lines(raw_text):
        if not line:
            if not previous_blank:
                output.append("")
            previous_blank = True
            continue

        previous_blank = False
        is_heading, level = classify_heading(line)
        if is_heading:
            output.append(f"{'#' * level} {line}")
            output.append("")
            continue

        if re.match(r"^[*-]\s+", line) or re.match(r"^\d+[.)]\s+", line):
            output.append(line)
            continue

        output.append(line)
    return "\n".join(output).strip() + "\n"


def to_text(raw_text: str) -> str:
    lines = normalize_lines(raw_text)
    return "\n".join(lines).strip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parse a guideline PDF into markdown or plain text."
    )
    parser.add_argument("input", help="PDF path or file URI")
    parser.add_argument("output", help="Output file path")
    parser.add_argument(
        "--format",
        choices=["markdown", "text"],
        default="markdown",
        help="Output format",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = normalize_input_path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Input PDF does not exist: {input_path}", file=sys.stderr)
        return 1

    raw_text, extractor_name = extract_pdf_text(input_path)
    rendered = to_markdown(raw_text) if args.format == "markdown" else to_text(raw_text)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")

    print(f"Parsed {input_path} -> {output_path} using {extractor_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
