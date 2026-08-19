# Function 9.5: Mock Personalized Learning Path

This document describes the learner-facing mock API for setting a learning goal,
recording a baseline pre-assessment, identifying gaps, and generating or adapting a
personalized learning path. All private endpoints require a Bearer token for the
`LEARNER` role.

## Requirement coverage

| Requirement | Implementation |
| --- | --- |
| FR-PLP-001 Learning Goal | `PUT /api/learning/profile` stores `learning_goal` and optional `target_role`. |
| FR-PLP-002 Learning Style | The same profile stores one or more supported `learning_styles`. |
| FR-PLP-003 Pre-Assessment | `POST /api/learning/pre-assessments` records baseline topic scores. |
| FR-PLP-004 Skill Gap Analysis | `GET /api/learning/skill-gap-analysis` returns knowledge gaps and inferred skill gaps. |
| FR-PLP-005 Personalized Lesson Selection | Each generated path selects a lesson level per topic from the learner's score. |
| FR-PLP-006 Learning Path Generation | `POST /api/learning/paths` generates the learner's current path. |
| FR-PLP-007 Adaptive Learning Path | `POST /api/learning/paths/current/adapt` revises the current path from newer results. |
| FR-PLP-008 Weak Topic Detection | Scores below `passing_score` appear in `weak_topics`, ordered from lowest score. |
| FR-PLP-009 Additional Content Recommendation | Every weak topic receives targeted lesson, exercise, and reference recommendations. |

## Mock behavior

- This MVP stores profiles, assessments, and paths in memory; they reset when the backend restarts.
- The AI selection is deliberately deterministic/rule-based for integration. It chooses `FOUNDATION` lessons below 50, `BEGINNER` below the passing score, `INTERMEDIATE` from passing score to 84, and `ADVANCED` from 85 upward. Each selected lesson also returns `study_recommendations` tailored to the learner's saved styles.
- The default passing score is 70. A score below this threshold becomes a knowledge gap, inferred skill gap, and weak topic.
- Supported learning styles: `VISUAL`, `AUDITORY`, `READING_WRITING`, `KINESTHETIC`, and `MIXED`.

## 1. Save goal and learning style

`PUT /api/learning/profile`

```json
{
  "learning_goal": "Become confident building data-driven web applications.",
  "target_role": "Junior backend developer",
  "learning_styles": ["VISUAL", "KINESTHETIC"],
  "weekly_learning_hours": 6
}
```

## 2. Submit a pre-assessment

`POST /api/learning/pre-assessments`

```json
{
  "assessment_title": "Backend foundations pre-assessment",
  "passing_score": 70,
  "topic_scores": [
    {"topic": "SQL joins", "score": 42},
    {"topic": "Git workflows", "score": 65},
    {"topic": "Python functions", "score": 78}
  ]
}
```

The response includes `overall_score` and `learner_level`. Topic names must be unique within each assessment (case-insensitive).

## 3. Review gap analysis

`GET /api/learning/skill-gap-analysis`

Optionally pass `?pre_assessment_id=<id>` to analyze an earlier owned assessment. The latest assessment is used by default. The response has `knowledge_gaps`, `skill_gaps`, and `weak_topics`, including current score, target score, score gap, and severity.

## 4. Generate a personalized path

`POST /api/learning/paths`

```json
{
  "pre_assessment_id": 1
}
```

Omit `pre_assessment_id` to use the learner's latest assessment. The response contains score-matched `lessons`, weak topics, and `additional_content_recommendations`. Read it again through `GET /api/learning/paths/current`.

## 5. Adapt the current path

`POST /api/learning/paths/current/adapt`

```json
{
  "assessment_title": "Backend checkpoint 1",
  "passing_score": 70,
  "topic_scores": [
    {"topic": "SQL joins", "score": 88},
    {"topic": "Git workflows", "score": 48},
    {"topic": "Python functions", "score": 78}
  ]
}
```

This records the newest results, increments the current path `version`, sets `is_adaptive` to `true`, and returns the changed topics plus the revised path.

## Status and errors

| Status | Case | Error code |
| --- | --- | --- |
| `200 OK` | Save/read profile, gap analysis, current path, or adaptive update | - |
| `201 Created` | Submit pre-assessment or generate path | - |
| `401 Unauthorized` | Missing or invalid learner token | `UNAUTHORIZED` |
| `403 Forbidden` | Caller is not a learner | `FORBIDDEN` |
| `404 Not Found` | Profile, assessment, or current path has not been created | `LEARNING_PROFILE_NOT_FOUND`, `PRE_ASSESSMENT_NOT_FOUND`, `LEARNING_PATH_NOT_FOUND` |
| `422 Unprocessable Entity` | Invalid scores, empty styles/topics, or duplicate topics/styles | `VALIDATION_ERROR` |

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_personalized_learning.py -q
```
