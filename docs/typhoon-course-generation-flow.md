# Function 4 — Typhoon Course Generation

Function 4 turns processed knowledge chunks into a creator-reviewable learning-path draft. It calls Typhoon through the OpenAI-compatible API configured in `.env`.

## Configuration

Copy `.env.example` to `.env`, then add the API key obtained from Typhoon:

```env
TYPHOON_API_KEY=your_typhoon_api_key_here
TYPHOON_MODEL=typhoon-v2.5-30b-a3b-instruct
TYPHOON_BASE_URL=https://api.opentyphoon.ai/v1
```

Do not commit `.env`. The request sends the extracted chunks from the selected course to Typhoon, so only upload material that is appropriate to send to that provider.

## Swagger test flow

Start the server and open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

1. Use `POST /api/auth/login` with `creator@skillsync.local` / `password123`.
2. Click **Authorize** and enter `Bearer <access_token>`.
3. Create a course with `POST /api/courses` (or use an existing course you own).
4. Upload a TXT, Markdown, or selectable-text PDF with `POST /api/courses/{course_id}/documents`.
5. Call `POST /api/knowledge-sources/{source_id}/process` and confirm `status: READY`.
6. Call `POST /api/courses/{course_id}/generate`.
7. The successful result has `status: WAITING_VERIFICATION`, `progress: 100`, and `learning_path`. Each lesson contains `source_references`, such as `source-1-chunk-1`.
8. Use `GET /api/courses/{course_id}/generation-status` to read the last result.

## Important responses

| HTTP | Error code | Meaning |
| --- | --- | --- |
| 400 | `AI_GENERATION_REQUIRES_READY_SOURCE` | No processed chunks exist for this course. |
| 403 | `FORBIDDEN` | The account is not a Creator. |
| 404 | `COURSE_NOT_FOUND` | The course is not owned by this Creator. |
| 502 | `AI_PROVIDER_ERROR` | Typhoon could not complete the request. |
| 502 | `AI_RESPONSE_INVALID` | The generated JSON was unusable or cited an unknown source chunk. |
| 503 | `AI_PROVIDER_NOT_CONFIGURED` | `TYPHOON_API_KEY` is missing from `.env`. |

This MVP waits for the model response in the same request. A production version should queue the work and expose progress asynchronously.
