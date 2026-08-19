# Mock Learner Delivery, Assessment, and Management APIs

This MVP adds the APIs that connect a published course to learner activity,
assessment feedback, and adaptive personalized learning. All data is held in
memory and resets when the server restarts.

## Learner course flow

All learner endpoints require a Bearer token for `demo@skillsync.local` or
another account with the `LEARNER` role.

| Endpoint | Purpose |
| --- | --- |
| `POST /api/courses/{course_id}/enroll` | Enroll in a published course. The operation is idempotent. |
| `GET /api/learning/courses/{course_id}/path` | Read generated lessons with the learner's completion state. |
| `GET /api/lessons/{lesson_id}` | Read an enrolled lesson. |
| `POST /api/lessons/{lesson_id}/complete` | Mark a lesson as complete and return updated progress. |
| `GET /api/learning/courses/{course_id}/progress` | Read completion percentage and counts. |

The learner path endpoint deliberately uses `/api/learning/courses/...` so it
does not conflict with the Creator-only course draft endpoint
`GET /api/courses/{course_id}/learning-path`.

## Assessment flow

Creators can define or generate course assessments:

| Endpoint | Purpose |
| --- | --- |
| `POST /api/courses/{course_id}/assessments` | Create a `QUIZ`, `POST_ASSESSMENT`, or `PRACTICAL` assessment. |
| `POST /api/courses/{course_id}/assessments/generate` | Deterministically create quiz, post-assessment, and practical-task definitions from the generated course lessons. |
| `GET /api/courses/{course_id}/assessments` | List assessments. Creators require ownership; Learners require enrollment. |
| `POST /api/assessments/{assessment_id}/submit` | Submit topic scores and, for practical work, text or URL evidence. |
| `GET /api/assessments/{assessment_id}/attempts` | Creator reads submitted attempts. |
| `PATCH /api/assessments/{assessment_id}/attempts/{attempt_id}/review` | Creator records a score adjustment and reason. |

Submitting an assessment returns score, strengths, improvement topics, and
feedback. If that learner already generated a Personalized Learning Path, the
new topic scores automatically create the next adaptive path version and return
it as `adapted_learning_path`.

## Course, content, and account management

| Endpoint | Purpose |
| --- | --- |
| `PUT /api/courses/{course_id}` | Edit draft/failed course metadata and Advanced-course certificate settings. |
| `DELETE /api/courses/{course_id}` | Delete a draft/failed course. |
| `POST /api/courses/{course_id}/knowledge-sources/text` | Add creator-authored text for knowledge processing. |
| `POST /api/auth/logout` | Invalidate the current mock token. |
| `GET`, `PUT /api/users/me` | Read or change the authenticated user's display name. |
| `GET /api/users` | List accounts for an `ADMIN` user. |
| `PUT /api/users/{user_id}/roles` | Replace a user's roles as an `ADMIN`. |
| `PATCH /api/users/{user_id}/status` | Suspend or reactivate an account as an `ADMIN`. Suspension invalidates its tokens. |

The local admin demo account is `admin@skillsync.local` with password
`password123`.

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_learner_delivery.py -q
```
