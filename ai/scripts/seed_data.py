"""Ingestion pipeline: CSV -> LLM preprocessing -> Embedding -> Qdrant.

Usage:
    uv run python scripts/seed_data.py [--data-path PATH] [--recreate]

Steps:
    1. Load Coursera parquet (6,645 courses)
    2. Preprocess with GPT-4o-mini (Skills completion + search text generation)
    3. Generate dense embeddings with text-embedding-3-large
    4. Generate sparse vectors with BM25 (fastembed)
    5. Upsert into Qdrant collection
"""

import argparse
import json
import logging
import sys
import uuid
from pathlib import Path
from typing import Any

from tqdm import tqdm

# Ensure ai/ root is on path when running as script
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.settings import get_settings
from app.domain.entities.course import CourseFactory
from app.infrastructure.embeddings.openai_embedding import embed_all
from app.infrastructure.ingestion.csv_loader import load_courses
from app.infrastructure.ingestion.llm_preprocessor import preprocess_batch
from app.infrastructure.vectordb.qdrant_adapter import (
    build_payload,
    build_sparse_vectors,
    create_client,
    ensure_collection,
    upsert_courses,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _load_checkpoint(path: Path) -> dict[str, dict[str, Any]]:
    """Load previously preprocessed courses from JSONL checkpoint."""
    processed: dict[str, dict[str, Any]] = {}
    if not path.exists():
        return processed
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record: dict[str, object] = json.loads(line)
                url = str(record.get("url", ""))
                processed[url] = record
            except json.JSONDecodeError:
                continue
    logger.info("Loaded %d preprocessed courses from checkpoint", len(processed))
    return processed


def _save_to_checkpoint(path: Path, courses: list[dict[str, Any]]) -> None:
    """Append preprocessed courses to JSONL checkpoint."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        for course in courses:
            f.write(json.dumps(course, ensure_ascii=False) + "\n")


def _assign_ids(
    courses: list[dict[str, Any]],
    checkpoint: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Assign stable UUIDs (reuse from checkpoint if available)."""
    for course in courses:
        url = str(course.get("url", ""))
        existing = checkpoint.get(url)
        course["id"] = existing["id"] if existing and "id" in existing else str(uuid.uuid4())
    return courses


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed Qdrant with Coursera course data")
    parser.add_argument("--data-path", type=str, help="Path to coursera.parquet")
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate Qdrant collection (deletes existing data)",
    )
    parser.add_argument(
        "--skip-llm",
        action="store_true",
        help="Skip LLM preprocessing (use checkpoint only)",
    )
    args = parser.parse_args()

    settings = get_settings()
    data_path = args.data_path or settings.DATA_PATH
    checkpoint_path = Path(settings.PREPROCESSED_PATH)

    logger.info("=== Lumineer Ingestion Pipeline ===")
    logger.info("Data path: %s", data_path)
    logger.info("Qdrant: %s / collection: %s", settings.QDRANT_URL, settings.QDRANT_COLLECTION)

    # ── Step 1: Load raw data ─────────────────────────────────────────────────
    logger.info("Step 1: Loading raw data...")
    raw_courses = load_courses(data_path)
    logger.info("Loaded %d courses", len(raw_courses))

    # ── Step 2: LLM Preprocessing ─────────────────────────────────────────────
    checkpoint = _load_checkpoint(checkpoint_path)
    preprocessed_all: list[dict[str, Any]] = []

    if args.skip_llm and checkpoint:
        logger.info("Step 2: Skipping LLM (using checkpoint)")
        preprocessed_all = list(checkpoint.values())
    else:
        from openai import OpenAI

        openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

        # Split into already-processed and pending
        pending = [c for c in raw_courses if str(c.get("url", "")) not in checkpoint]
        logger.info(
            "Step 2: LLM preprocessing — %d pending / %d cached",
            len(pending),
            len(raw_courses) - len(pending),
        )

        # Process pending in batches
        batch_size = settings.BATCH_SIZE_LLM
        with tqdm(total=len(pending), desc="LLM preprocessing") as pbar:
            for i in range(0, len(pending), batch_size):
                batch = pending[i : i + batch_size]
                processed_batch = preprocess_batch(
                    openai_client,
                    settings.LLM_MODEL,
                    batch,
                )
                _save_to_checkpoint(checkpoint_path, processed_batch)
                pbar.update(len(batch))

        # Reload full checkpoint
        checkpoint = _load_checkpoint(checkpoint_path)
        preprocessed_all = list(checkpoint.values())

        # For courses not in checkpoint (e.g. data added after checkpoint), use raw
        checkpoint_urls = set(checkpoint.keys())
        for course in raw_courses:
            if str(course.get("url", "")) not in checkpoint_urls:
                skills = course.get("skills", [])
                skill_list = skills if isinstance(skills, list) else []
                skill_str = ", ".join(str(s) for s in skill_list[:5]) if skill_list else ""
                course["search_text"] = f"{course.get('title', '')}. {skill_str}".strip(". ")
                preprocessed_all.append(course)

    # Assign stable IDs
    _assign_ids(preprocessed_all, checkpoint)

    # Build CourseEntity objects (validates data)
    courses = []
    for data in preprocessed_all:
        try:
            entity = CourseFactory.create(
                id=data.get("id"),
                title=data.get("title", ""),
                description=data.get("description", ""),
                skills=data.get("skills", []),
                level=data.get("level"),
                organization=data.get("organization", ""),
                rating=float(data.get("rating", 0)),
                enrolled=int(data.get("enrolled", 0)),
                num_reviews=data.get("num_reviews"),
                modules=data.get("modules"),
                schedule=data.get("schedule"),
                url=data.get("url", ""),
                instructor=data.get("instructor"),
                search_text=data.get("search_text", data.get("title", "")),
            )
            courses.append(entity)
        except Exception as e:
            logger.warning("Skipping course '%s': %s", data.get("title", "?"), e)

    logger.info("Validated %d courses", len(courses))

    # ── Step 3: Dense Embeddings ───────────────────────────────────────────────
    logger.info("Step 3: Generating dense embeddings (model: %s)...", settings.EMBEDDING_MODEL)
    from openai import OpenAI

    openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    search_texts = [c.search_text for c in courses]

    with tqdm(total=len(courses), desc="Dense embeddings") as pbar:
        dense_vectors = embed_all(
            openai_client,
            search_texts,
            model=settings.EMBEDDING_MODEL,
            dimensions=settings.EMBEDDING_DIMENSIONS,
            batch_size=settings.BATCH_SIZE_EMBEDDING,
            progress_callback=pbar.update,
        )
    logger.info("Generated %d dense vectors", len(dense_vectors))

    # ── Step 4: Sparse Vectors ────────────────────────────────────────────────
    logger.info("Step 4: Generating sparse vectors (BM25)...")
    with tqdm(total=len(courses), desc="Sparse vectors") as pbar:
        sparse_vectors = build_sparse_vectors(search_texts)
        pbar.update(len(courses))
    logger.info("Generated %d sparse vectors", len(sparse_vectors))

    # ── Step 5: Upsert into Qdrant ────────────────────────────────────────────
    logger.info("Step 5: Upserting into Qdrant...")
    qdrant_client = create_client(settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    ensure_collection(
        qdrant_client,
        settings.QDRANT_COLLECTION,
        dense_size=settings.EMBEDDING_DIMENSIONS,
        recreate=args.recreate,
    )

    course_ids = [c.id for c in courses]
    payloads = [build_payload(c.__dict__) for c in courses]

    with tqdm(total=len(courses), desc="Upserting") as pbar:
        upsert_courses(
            qdrant_client,
            settings.QDRANT_COLLECTION,
            course_ids=course_ids,
            dense_vectors=dense_vectors,
            sparse_vectors=sparse_vectors,
            payloads=payloads,
            batch_size=settings.BATCH_SIZE_UPSERT,
            progress_callback=pbar.update,
        )

    # Verify
    info = qdrant_client.get_collection(settings.QDRANT_COLLECTION)
    logger.info(
        "=== Done! Collection '%s' has %d indexed vectors ===",
        settings.QDRANT_COLLECTION,
        info.indexed_vectors_count or 0,
    )


if __name__ == "__main__":
    main()
