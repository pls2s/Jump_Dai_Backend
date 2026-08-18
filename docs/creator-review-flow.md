# Function 5 — Creator Review and Verify

Function 5 is the mandatory review step after Function 4 generates an AI learning-path draft. A generated draft is never published automatically.

## Prerequisite

The Creator must own the course and call `POST /api/courses/{course_id}/generate` successfully first. The course must be in `WAITING_VERIFICATION` state.

## Endpoints

### Get the draft

```http
GET /api/courses/{course_id}/learning-path
Authorization: Bearer <creator_access_token>
```

Returns the overview, modules, lessons, and every lesson's `source_references`.

### Edit the draft

```http
PUT /api/courses/{course_id}/learning-path
Authorization: Bearer <creator_access_token>
Content-Type: application/json
```

```json
{
  "overview": "A Creator-reviewed course overview.",
  "modules": [
    {
      "title": "Keys and relationships",
      "description": "Learn how related tables connect.",
      "learning_objectives": ["Recognize a foreign key."],
      "lessons": [
        {
          "title": "Connecting related tables",
          "summary": "A foreign key connects a child table to its parent.",
          "source_references": ["source-1-chunk-1"]
        }
      ]
    }
  ]
}
```

The server checks that every `source_references` value still points to a processed chunk in the course. It does not call Typhoon again.

### Verify the draft

```http
POST /api/courses/{course_id}/verify
Authorization: Bearer <creator_access_token>
```

The response changes the course status from `WAITING_VERIFICATION` to `VERIFIED`:

```json
{
  "success": true,
  "data": {
    "course_id": 2,
    "status": "VERIFIED",
    "verified_at": "2026-08-18T13:40:00Z"
  }
}
```

`VERIFIED` means the Creator has accepted the learning path. Publishing it for Learners is the next function and is intentionally separate.

## Error codes

| HTTP | Error code | Meaning |
| --- | --- | --- |
| 403 | `FORBIDDEN` | The authenticated user is not a Creator. |
| 404 | `COURSE_NOT_FOUND` | The course is not owned by this Creator. |
| 409 | `LEARNING_PATH_NOT_READY_FOR_VERIFICATION` | Generation has not finished, or the draft is already verified. |
| 422 | `LEARNING_PATH_INVALID_SOURCE_REFERENCE` | An edited lesson cites a chunk that is not in the course. |
