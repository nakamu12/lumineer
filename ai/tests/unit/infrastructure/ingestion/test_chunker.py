"""Unit tests for chunker module."""

from app.infrastructure.ingestion.chunker import (
    _build_metadata_header,
    _fixed_split,
    _recursive_split,
    chunk_all_courses,
    chunk_course,
)


def _make_course(**overrides):
    defaults = dict(
        title="ML Specialization",
        description="Short description.",
        skills=["Python", "TensorFlow"],
        level="Beginner",
        organization="Stanford",
        rating=4.8,
        enrolled=12000,
        url="https://coursera.org/ml",
        search_text="ML Specialization. Python, TensorFlow",
    )
    defaults.update(overrides)
    return defaults


class TestBuildMetadataHeader:
    def test_includes_title(self) -> None:
        header = _build_metadata_header(_make_course())
        assert "ML Specialization" in header

    def test_includes_skills(self) -> None:
        header = _build_metadata_header(_make_course())
        assert "Python" in header
        assert "TensorFlow" in header

    def test_includes_organization(self) -> None:
        header = _build_metadata_header(_make_course())
        assert "Stanford" in header


class TestRecursiveSplit:
    def test_short_text_no_split(self) -> None:
        chunks = _recursive_split("Hello world", 600, 120)
        assert len(chunks) == 1
        assert chunks[0] == "Hello world"

    def test_paragraph_boundary(self) -> None:
        text = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = _recursive_split(text, 30, 5)
        assert len(chunks) >= 2

    def test_sentence_boundary(self) -> None:
        text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        chunks = _recursive_split(text, 40, 10)
        assert len(chunks) >= 2

    def test_overlap_applied(self) -> None:
        text = "A" * 300 + "\n\n" + "B" * 300 + "\n\n" + "C" * 300
        chunks = _recursive_split(text, 350, 50)
        assert len(chunks) >= 2
        if len(chunks) >= 2:
            assert chunks[1].startswith("A" * 50) or len(chunks[1]) > 300

    def test_empty_text(self) -> None:
        assert _recursive_split("", 600, 120) == []
        assert _recursive_split("   ", 600, 120) == []


class TestFixedSplit:
    def test_basic_split(self) -> None:
        text = "A" * 1200
        chunks = _fixed_split(text, 500, 50)
        assert len(chunks) >= 2

    def test_overlap_step(self) -> None:
        text = "A" * 1000
        chunks = _fixed_split(text, 500, 100)
        assert len(chunks) == 3


class TestChunkCourse:
    def test_short_course_single_chunk(self) -> None:
        course = _make_course(description="Short desc.")
        chunks = chunk_course(course)
        assert len(chunks) == 1
        assert chunks[0]["chunk_index"] == 0
        assert chunks[0]["chunk_total"] == 1
        assert "ML Specialization" in chunks[0]["text"]
        assert chunks[0]["course_url"] == "https://coursera.org/ml"

    def test_long_course_multiple_chunks(self) -> None:
        long_desc = "This is a long paragraph. " * 200
        course = _make_course(description=long_desc)
        chunks = chunk_course(course)
        assert len(chunks) > 1
        for i, chunk in enumerate(chunks):
            assert chunk["chunk_index"] == i
            assert chunk["chunk_total"] == len(chunks)
            assert "ML Specialization" in chunk["text"]

    def test_search_text_in_first_chunk_only(self) -> None:
        long_desc = "Word " * 500
        course = _make_course(description=long_desc)
        chunks = chunk_course(course)
        assert chunks[0]["search_text"] != ""
        for chunk in chunks[1:]:
            assert chunk["search_text"] == ""

    def test_chunk_ids_are_unique(self) -> None:
        long_desc = "Sentence here. " * 300
        course = _make_course(description=long_desc)
        chunks = chunk_course(course)
        ids = [c["chunk_id"] for c in chunks]
        assert len(ids) == len(set(ids))


class TestChunkAllCourses:
    def test_multiple_courses(self) -> None:
        courses = [
            _make_course(description="Short.", url="url1"),
            _make_course(description="Also short.", url="url2"),
        ]
        chunks = chunk_all_courses(courses)
        assert len(chunks) == 2

    def test_mixed_lengths(self) -> None:
        courses = [
            _make_course(description="Short.", url="url1"),
            _make_course(description="Long text. " * 300, url="url2"),
        ]
        chunks = chunk_all_courses(courses)
        assert len(chunks) > 2
