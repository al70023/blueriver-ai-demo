def chunk_text(text: str, chunk_size: int = 1000) -> list[str]:
    cleaned_text = text.strip()

    if not cleaned_text:
        return []

    chunks: list[str] = []

    for start in range(0, len(cleaned_text), chunk_size):
        chunk = cleaned_text[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)

    return chunks
