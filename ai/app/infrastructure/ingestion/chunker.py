"""Recursive chunking with overlap for course descriptions.

Implements the Recursive + Overlap strategy taught in FDE training (Day 22-25):
- Recursive splitting: paragraphs -> sentences -> characters
- Overlap for context continuity across chunk boundaries
- Structure-aware: course metadata (title, skills) is prepended to each chunk
  so that every chunk is self-contained for retrieval

Design:
- Each course produces 1+ chunks (short descriptions = 1 chunk, long = N chunks)
- Each chunk carries parent course metadata for deduplication at retrieval time
- Chunk text = metadata header + description segment
"""

import uuid

CHUNK_SIZE = 600  # characters
CHUNK_OVERLAP = 120  # characters (20% overlap)


def _build_metadata_header(course: dict) -> str:  # type: ignore[type-arg]
    """Build a compact metadata prefix for each chunk.

    Ensures every chunk is self-contained: even a chunk from the middle
    of a long description carries the course title and skills.
    """
    title = course.get("title", "")
    skills = course.get("skills", [])
    level = course.get("level") or ""
    org = course.get("organization", "")

    parts = [f"Course: {title}"]
    if org:
        parts.append(f"Organization: {org}")
    if level:
        parts.append(f"Level: {level}")
    if skills:
        parts.append(f"Skills: {', '.join(skills[:7])}")
    return " | ".join(parts)


def _recursive_split(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Split text recursively by structural separators with overlap.

    Separator hierarchy (from coarsest to finest):
      1. "\\n\\n" - paragraph breaks
      2. "\\n"   - line breaks
      3. ". "    - sentence boundaries
      4. " "     - word boundaries
      5. ""      - character level (last resort)

    Follows the RecursiveCharacterTextSplitter approach from Day 25.
    """
    separators = ["\n\n", "\n", ". ", " ", ""]

    def _split_with_sep(text: str, sep_idx: int) -> list[str]:
        if not text or len(text) <= chunk_size:
            return [text] if text.strip() else []

        if sep_idx >= len(separators):
            return _fixed_split(text, chunk_size, chunk_overlap)

        sep = separators[sep_idx]
        if not sep:
            return _fixed_split(text, chunk_size, chunk_overlap)

        segments = text.split(sep)
        chunks: list[str] = []
        current = ""

        for segment in segments:
            candidate = f"{current}{sep}{segment}" if current else segment

            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current.strip():
                    chunks.append(current.strip())
                if len(segment) > chunk_size:
                    chunks.extend(_split_with_sep(segment, sep_idx + 1))
                    current = ""
                else:
                    current = segment

        if current.strip():
            chunks.append(current.strip())

        return chunks

    raw_chunks = _split_with_sep(text, 0)

    if len(raw_chunks) <= 1:
        return raw_chunks

    # Apply overlap
    overlapped: list[str] = [raw_chunks[0]]
    for i in range(1, len(raw_chunks)):
        prev = raw_chunks[i - 1]
        tail = prev[-chunk_overlap:] if len(prev) >= chunk_overlap else prev
        merged = f"{tail} {raw_chunks[i]}"
        if len(merged) > chunk_size * 1.3:
            overlapped.append(raw_chunks[i])
        else:
            overlapped.append(merged)

    return overlapped


def _fixed_split(text: str, chunk_size: int, overlap: int) -> list[str]:
    """Fixed-size character splitting with overlap (fallback)."""
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunk = text[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def chunk_course(
    course: dict,  # type: ignore[type-arg]
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[dict]:  # type: ignore[type-arg]
    """Chunk a single course into 1+ retrieval units.

    Short descriptions produce 1 chunk.
    Long descriptions are split recursively with overlap.
    """
    description = course.get("description", "")
    search_text = course.get("search_text", "")
    header = _build_metadata_header(course)
    course_url = course.get("url", "")

    combined = f"{search_text}\n\n{description}" if search_text else description

    if len(combined) <= chunk_size:
        return [
            {
                "chunk_id": str(uuid.uuid4()),
                "course_url": course_url,
                "chunk_index": 0,
                "chunk_total": 1,
                "text": f"{header}\n{combined}",
                "search_text": search_text,
            }
        ]

    desc_chunks = _recursive_split(description, chunk_size, chunk_overlap)

    if desc_chunks:
        prefix = f"{search_text}\n\n" if search_text else ""
        desc_chunks[0] = f"{prefix}{desc_chunks[0]}"

    total = len(desc_chunks)
    return [
        {
            "chunk_id": str(uuid.uuid4()),
            "course_url": course_url,
            "chunk_index": i,
            "chunk_total": total,
            "text": f"{header}\n{chunk_text}",
            "search_text": search_text if i == 0 else "",
        }
        for i, chunk_text in enumerate(desc_chunks)
    ]


def chunk_all_courses(
    courses: list[dict],  # type: ignore[type-arg]
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[dict]:  # type: ignore[type-arg]
    """Chunk all courses and return flat list of chunk dicts."""
    all_chunks: list[dict] = []  # type: ignore[type-arg]
    for course in courses:
        all_chunks.extend(chunk_course(course, chunk_size, chunk_overlap))
    return all_chunks
