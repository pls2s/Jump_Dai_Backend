# Function 6 — Publish Course and Public Catalog

Function 6 makes a Creator-verified AI course visible to Learners. A course cannot be published directly after generation; it must pass the Creator review step first.

## Publish a verified course

```http
POST /api/courses/{course_id}/publish
Authorization: Bearer <creator_access_token>
```

The course must be owned by that Creator and have status `VERIFIED`. On success, the status changes to `PUBLISHED`.

```json
{
  "success": true,
  "data": {
    "course_id": 2,
    "status": "PUBLISHED",
    "published_at": "2026-08-18T13:50:00Z"
  }
}
```

## Read the public catalog

These endpoints do not require a token. They return only `PUBLISHED` courses, with no Creator identity or original source-file payload.

```http
GET /api/catalog/courses
GET /api/catalog/courses/{course_id}
```

The course detail includes the verified modules and lessons. `source_references` remain visible so a future learner UI can display provenance, but original chunk text is not exposed.

## Error codes

| HTTP | Error code | Meaning |
| --- | --- | --- |
| 403 | `FORBIDDEN` | A non-Creator attempted to publish. |
| 404 | `COURSE_NOT_FOUND` | The Creator does not own that course. |
| 404 | `PUBLISHED_COURSE_NOT_FOUND` | The catalog course does not exist or is not published. |
| 409 | `COURSE_NOT_READY_TO_PUBLISH` | The learning path is not yet `VERIFIED`. |

## Swagger sequence

1. Complete Function 4 generation.
2. Review and verify with `POST /api/courses/{course_id}/verify`.
3. Call `POST /api/courses/{course_id}/publish` using the same Creator token.
4. Open `GET /api/catalog/courses` without Authorize to confirm that the course is public.

The next function is Learner enrollment and lesson-progress tracking.
