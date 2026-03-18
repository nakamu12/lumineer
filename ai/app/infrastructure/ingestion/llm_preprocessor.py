"""LLM preprocessing: Skills补完 + search text generation via GPT-4o-mini."""

import json
import logging
from typing import Any

from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a course metadata processor. For each course, output a JSON array.
Each element must have:
- "skills": array of 3-7 skill strings (infer from description if empty)
- "search_text": concise 1-2 sentence string combining title, key skills, and learning outcome
Keep search_text under 200 characters. Output ONLY valid JSON, no markdown."""

USER_TEMPLATE = """Process these courses and return a JSON array with {count} elements:

{courses_json}"""


def _build_course_input(course: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": course["title"],
        "skills": course["skills"],
        "description": course["description"][:500] if course["description"] else "",
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call_llm(client: OpenAI, model: str, batch: list[dict[str, Any]]) -> list[dict[str, Any]]:
    courses_input = [_build_course_input(c) for c in batch]
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_TEMPLATE.format(
                    count=len(batch),
                    courses_json=json.dumps(courses_input, ensure_ascii=False),
                ),
            },
        ],
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content or "[]"

    # The model returns a JSON object with an array inside
    parsed: Any = json.loads(content)
    # Try common keys
    if isinstance(parsed, list):
        return list(parsed)
    for key in ("courses", "results", "data", "items"):
        if key in parsed and isinstance(parsed[key], list):
            return list(parsed[key])
    # Fallback: first list value found
    for v in parsed.values():
        if isinstance(v, list):
            return list(v)
    return []


def preprocess_batch(
    client: OpenAI,
    model: str,
    batch: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Preprocess a batch of courses with LLM.

    Returns list of dicts with keys: skills, search_text.
    Falls back to original data on error.
    """
    try:
        results = _call_llm(client, model, batch)
    except Exception as e:
        logger.warning("LLM batch failed, using fallback: %s", e)
        results = []

    processed = []
    for i, course in enumerate(batch):
        if i < len(results) and isinstance(results[i], dict):
            llm_result = results[i]
            skills = llm_result.get("skills")
            search_text = llm_result.get("search_text", "")

            # Use LLM skills only if original is empty
            if course["skills"]:
                final_skills = course["skills"]
            elif isinstance(skills, list) and skills:
                final_skills = [str(s).strip() for s in skills if s]
            else:
                final_skills = course["skills"]

            # Fallback search_text
            if not search_text:
                skill_str = ", ".join(final_skills[:5]) if final_skills else ""
                search_text = f"{course['title']}. {skill_str}".strip(". ")
        else:
            # Fallback
            final_skills = course["skills"]
            skill_str = ", ".join(final_skills[:5]) if final_skills else ""
            search_text = f"{course['title']}. {skill_str}".strip(". ")

        processed.append(
            {
                **course,
                "skills": final_skills,
                "search_text": search_text,
            }
        )

    return processed
