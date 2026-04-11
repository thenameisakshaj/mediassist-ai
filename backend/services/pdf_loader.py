from pathlib import Path

from pypdf import PdfReader

from utils.helpers import clean_text


def load_pdf_pages(pdf_path: Path) -> list[dict]:
    if not pdf_path.exists():
        raise FileNotFoundError(
            f"Medical PDF not found at {pdf_path}. Add your book PDF before indexing."
        )

    reader = PdfReader(str(pdf_path))
    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = clean_text(page.extract_text() or "")
        if text:
            pages.append(
                {
                    "text": text,
                    "metadata": {
                        "source": pdf_path.name,
                        "page": page_number,
                    },
                }
            )

    if not pages:
        raise ValueError("No extractable text was found in the medical PDF.")

    return pages
