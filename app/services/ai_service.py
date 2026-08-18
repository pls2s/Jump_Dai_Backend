"""Function 4 Typhoon integration for source-grounded learning-path generation."""

from __future__ import annotations

import json
import re

from openai import OpenAI
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.ai import GeneratedLearningPath
from app.services.course_service import MockCourse
from app.services.knowledge_service import MockKnowledgeChunk

MAX_CONTEXT_CHUNKS = 12


class AIConfigurationError(Exception):
    """Raised when the server has no usable Typhoon configuration."""


class AIProviderError(Exception):
    """Raised when Typhoon cannot return a completion to the backend."""


class AIResponseError(Exception):
    """Raised when an LLM response cannot become a safe learning-path draft."""


class TyphoonAIService:
    """Call Typhoon through its OpenAI-compatible chat-completions endpoint."""

    def generate_learning_path(
        self,
        *,
        course: MockCourse,
        chunks: list[MockKnowledgeChunk],
    ) -> GeneratedLearningPath:
        """Generate and validate a curriculum draft grounded only in supplied chunks."""
        if not settings.typhoon_api_key:
            raise AIConfigurationError("TYPHOON_API_KEY is not configured on the server")
        if not chunks:
            raise AIResponseError("No ready knowledge chunks are available for this course")

        messages = self._build_messages(course=course, chunks=chunks)
        raw_response = self._create_completion(messages=messages)
        payload = self._parse_json(raw_response)
        payload["course_id"] = course.id
        payload["title"] = course.title

        try:
            learning_path = GeneratedLearningPath.model_validate(payload)
        except ValidationError as exc:
            raise AIResponseError("Typhoon returned an invalid learning-path structure") from exc

        self._validate_references(learning_path=learning_path, chunks=chunks)
        return learning_path

    def validate_learning_path(
        self,
        *,
        learning_path: GeneratedLearningPath,
        chunks: list[MockKnowledgeChunk],
    ) -> None:
        """Validate Creator edits without making another provider request."""
        self._validate_references(learning_path=learning_path, chunks=chunks)

    @staticmethod
    def _build_messages(
        *,
        course: MockCourse,
        chunks: list[MockKnowledgeChunk],
    ) -> list[dict[str, str]]:
        context = "\n\n".join(
            (
                f"[chunk_id: {chunk.id}; source: {chunk.source_filename}]\n"
                f"{chunk.content}"
            )
            for chunk in chunks[:MAX_CONTEXT_CHUNKS]
        )
        system_message = (
            "You are a curriculum designer for SkillSync. Create a concise learning path "
            "using only the supplied source chunks. Do not introduce unsupported facts. "
            "Return valid JSON only, with no Markdown fences. Every lesson must include "
            "source_references containing one or more exact chunk_id values from the sources."
        )
        user_message = f"""Create a learning-path draft for this course.

Course title: {course.title}
Description: {course.description}
Target learner: {course.target_learner}
Difficulty: {course.difficulty_level.value}
Learning objective: {course.learning_objective}

Return exactly this JSON shape:
{{
  "overview": "string",
  "modules": [
    {{
      "title": "string",
      "description": "string",
      "learning_objectives": ["string"],
      "lessons": [
        {{
          "title": "string",
          "summary": "string",
          "source_references": ["source-1-chunk-1"]
        }}
      ]
    }}
  ]
}}

Source chunks:
{context}"""
        return [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ]

    @staticmethod
    def _parse_json(raw_response: str) -> dict:
        candidate = raw_response.strip()
        code_fence = re.fullmatch(r"```(?:json)?\s*(.*?)\s*```", candidate, flags=re.DOTALL)
        if code_fence:
            candidate = code_fence.group(1)
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise AIResponseError("Typhoon did not return valid JSON") from exc
        if not isinstance(parsed, dict):
            raise AIResponseError("Typhoon returned an invalid learning-path payload")
        return parsed

    @staticmethod
    def _validate_references(
        *,
        learning_path: GeneratedLearningPath,
        chunks: list[MockKnowledgeChunk],
    ) -> None:
        valid_references = {chunk.id for chunk in chunks}
        invalid_references = {
            reference
            for module in learning_path.modules
            for lesson in module.lessons
            for reference in lesson.source_references
            if reference not in valid_references
        }
        if invalid_references:
            raise AIResponseError("Typhoon cited source chunks that were not supplied")

    @staticmethod
    def _create_completion(*, messages: list[dict[str, str]]) -> str:
        try:
            client = OpenAI(
                api_key=settings.typhoon_api_key,
                base_url=settings.typhoon_base_url,
                timeout=60.0,
            )
            completion = client.chat.completions.create(
                model=settings.typhoon_model,
                messages=messages,
                temperature=0.2,
                max_tokens=4_000,
            )
        except Exception as exc:
            raise AIProviderError("Typhoon could not complete this generation request") from exc

        content = completion.choices[0].message.content
        if not content:
            raise AIProviderError("Typhoon returned an empty completion")
        return content


typhoon_ai_service = TyphoonAIService()
