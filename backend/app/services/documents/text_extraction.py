from io import BytesIO

from pypdf import PdfReader


def extract_text_from_txt(raw_bytes: bytes) -> str:
    return raw_bytes.decode("utf-8")


def extract_text_from_pdf(raw_bytes: bytes) -> str:
    pdf_file = BytesIO(raw_bytes)
    reader = PdfReader(pdf_file)

    page_texts: list[str] = []

    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            page_texts.append(text.strip())

    return "\n\n".join(page_texts)


def extract_text_from_upload(filename: str, raw_bytes: bytes) -> str:
    lower_filename = filename.lower()

    if lower_filename.endswith("txt"):
        return extract_text_from_txt(raw_bytes)

    if lower_filename.endswith("pdf"):
        return extract_text_from_pdf(raw_bytes)

    raise ValueError("Only .txt and .pdf files are supported.")
