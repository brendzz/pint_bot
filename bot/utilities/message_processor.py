"""Platform-agnostic text chunking helpers.

Used by platform adapters to split long descriptions into chunks that
fit their platform limits. Contains no platform-specific code.
"""

def split_text_into_chunks(text: str, limit: int) -> list[str]:
    """Splits a long text into chunks that fit within a character limit."""
    chunks = []
    current_chunk = ""

    for paragraph in text.split('\n'):
        current_chunk, new_chunks = process_paragraph(paragraph, current_chunk, limit)
        chunks.extend(new_chunks)

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def process_paragraph(paragraph: str, current_chunk: str, limit: int) -> tuple[str, list[str]]:
    """Processes a paragraph and decides whether to start a new chunk or continue the current one."""
    chunks = []
    to_add = ("\n" if current_chunk else "") + paragraph

    if len(current_chunk) + len(to_add) > limit:
        if current_chunk:
            chunks.append(current_chunk)

        if len(paragraph) > limit:
            chunks.extend(chunk_paragraph(paragraph, limit))
            return "", chunks

        return paragraph, chunks

    return current_chunk + to_add, chunks

def chunk_paragraph(paragraph: str, limit: int) -> list[str]:
    """Splits a single long paragraph into smaller parts."""
    return [paragraph[i:i + limit] for i in range(0, len(paragraph), limit)]
