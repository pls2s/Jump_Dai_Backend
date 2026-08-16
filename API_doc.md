# SkillSync AI — API Documentation

**Version:** 0.1
**Status:** Draft / MVP
**Frontend:** React + Vite + TypeScript
**Backend:** FastAPI + Python
**Database:** PostgreSQL / Supabase
**AI:** LLM + RAG *(พัฒนาใน Phase ถัดไป)*

---

# 1. เอกสารนี้มีไว้ทำอะไร

เอกสารนี้เป็นข้อตกลงกลางระหว่าง

* Frontend
* Backend
* AI / RAG
* Database

เพื่อให้ทุกคนในทีมเข้าใจตรงกันว่า

> Front ต้องเรียก API อะไร
> ต้องส่งข้อมูลอะไร
> Backend ต้องตอบอะไรกลับมา
> และ Flow ของระบบทำงานอย่างไร

---

# 2. Architecture โดยรวม

```text
Frontend
React / Vite
        |
        | HTTP Request
        v
Backend API
FastAPI
        |
        +------ PostgreSQL / Supabase
        |
        +------ File Storage
        |
        +------ Document Processing
        |
        +------ RAG / Vector DB
        |
        +------ LLM
```

Local Development:

```text
Frontend
http://localhost:5173

        ↓ API

Backend
http://localhost:8000
```

---

# 3. Base URL

## Local

```text
http://localhost:8000
```

API Prefix:

```text
/api
```

ดังนั้น Endpoint จะมีรูปแบบ

```text
http://localhost:8000/api/...
```

ตัวอย่าง:

```text
GET http://localhost:8000/api/health
```

---

# 4. Frontend Environment

ฝั่ง Frontend ต้องมี

```env
VITE_API_URL=http://localhost:8000
```

แล้วเรียกผ่าน

```ts
const API_URL = import.meta.env.VITE_API_URL;
```

ห้ามเขียน URL กระจายอยู่ตาม Component เช่น

```ts
fetch("http://localhost:8000/api/courses");
```

ควรรวมไว้ใน `services/`

```text
src/
└── services/
    ├── api.ts
    ├── authApi.ts
    ├── courseApi.ts
    ├── documentApi.ts
    ├── learningApi.ts
    └── assessmentApi.ts
```

---

# 5. Content Type

API ปกติใช้

```http
Content-Type: application/json
```

ยกเว้น Upload File ใช้

```http
Content-Type: multipart/form-data
```

---

# 6. Authentication

หลังจากมีระบบ Login แล้ว Frontend จะส่ง Token มาด้วย

```http
Authorization: Bearer <access_token>
```

ตัวอย่าง

```http
GET /api/auth/me

Authorization: Bearer eyJhbGci...
```

ใน MVP แรก ถ้ายังไม่ได้ทำ Auth สามารถ Mock User ไปก่อนได้

---

# 7. Response Format

เพื่อให้ Frontend จัดการง่าย แนะนำให้ Backend ใช้รูปแบบ Response ให้สม่ำเสมอ

## Success

```json
{
  "success": true,
  "data": {}
}
```

ตัวอย่าง:

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "ER Diagram Basics"
  }
}
```

---

## Error

```json
{
  "success": false,
  "error": {
    "code": "COURSE_NOT_FOUND",
    "message": "Course not found"
  }
}
```

---

# 8. HTTP Status Code

| Status | ความหมาย                    |
| ------ | --------------------------- |
| `200`  | สำเร็จ                      |
| `201`  | สร้างข้อมูลสำเร็จ           |
| `204`  | สำเร็จ ไม่มีข้อมูล Response |
| `400`  | Request ไม่ถูกต้อง          |
| `401`  | ยังไม่ได้ Login             |
| `403`  | ไม่มีสิทธิ์                 |
| `404`  | ไม่พบข้อมูล                 |
| `409`  | ข้อมูล Conflict             |
| `422`  | Validation Error            |
| `500`  | Backend Error               |

---

# 9. User Role

ระบบ SkillSync มี Role หลัก

```text
CREATOR
LEARNER
ADMIN
```

แต่ User คนเดียวสามารถเป็นทั้ง

```text
Creator
+
Learner
```

ได้

ดังนั้นในระยะยาวไม่ควรล็อก User ว่าเป็นได้แค่ Role เดียว

---

# 10. Course Status

Course จะมีสถานะหลัก

```text
DRAFT
↓
GENERATING
↓
WAITING_VERIFICATION
↓
VERIFIED
↓
PUBLISHED
```

อาจมี

```text
FAILED
ARCHIVED
```

เพิ่มเติมภายหลัง

---

## ความหมาย

### `DRAFT`

Creator สร้าง Course แล้ว
แต่ยังไม่ได้ Generate

---

### `GENERATING`

AI กำลังสร้างเนื้อหา

---

### `WAITING_VERIFICATION`

AI Generate เสร็จแล้ว

แต่ Creator ยังไม่ได้ตรวจ

---

### `VERIFIED`

Creator ตรวจและ Approve แล้ว

---

### `PUBLISHED`

Course เปิดให้ Learner เรียนแล้ว

---

# 11. Core Flow

Flow หลักของ SkillSync

```text
Create Goal
    ↓
Upload Knowledge
    ↓
AI Generate
    ↓
Creator Review
    ↓
Creator Verify
    ↓
Publish
    ↓
Learner Enroll
    ↓
Pre-Test
    ↓
Personalized Learning
    ↓
Assessment
    ↓
Result
```

---

# 12. Endpoint Summary

## System

```text
GET    /api/health
```

## Auth

```text
POST   /api/auth/register
POST   /api/auth/login
GET    /api/auth/me
```

## Courses

```text
POST   /api/courses
GET    /api/courses
GET    /api/courses/{course_id}
PUT    /api/courses/{course_id}
DELETE /api/courses/{course_id}
```

## Documents

```text
POST   /api/courses/{course_id}/documents
GET    /api/courses/{course_id}/documents
DELETE /api/documents/{document_id}
```

## AI Generation

```text
POST   /api/courses/{course_id}/generate
GET    /api/courses/{course_id}/generation-status
```

## Course Content

```text
GET    /api/courses/{course_id}/modules
PUT    /api/modules/{module_id}
PUT    /api/lessons/{lesson_id}
DELETE /api/modules/{module_id}
DELETE /api/lessons/{lesson_id}
```

## Verification

```text
POST   /api/courses/{course_id}/verify
```

## Publish

```text
POST   /api/courses/{course_id}/publish
```

## Enrollment

```text
POST   /api/courses/{course_id}/enroll
GET    /api/enrollments
```

## Learning

```text
GET    /api/courses/{course_id}/learning-path
GET    /api/lessons/{lesson_id}
POST   /api/lessons/{lesson_id}/complete
```

## Progress

```text
GET    /api/courses/{course_id}/progress
```

## Assessment

```text
GET    /api/courses/{course_id}/assessments
GET    /api/assessments/{assessment_id}
POST   /api/assessments/{assessment_id}/submit
```

---

# 13. Health Check

## GET `/api/health`

ใช้ตรวจว่า Backend ทำงานอยู่หรือไม่

### Request

ไม่มี Body

### Response

```json
{
  "status": "ok"
}
```

### Frontend ใช้เมื่อ

* Test connection
* Debug
* เช็กว่า Backend เปิดหรือยัง

---

# 14. Authentication

## POST `/api/auth/register`

สมัครสมาชิก

### Request

```json
{
  "name": "Peer",
  "email": "peer@example.com",
  "password": "password123"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Peer",
    "email": "peer@example.com"
  }
}
```

### Frontend

หน้า:

```text
Register.tsx
```

เรียก

```ts
register({
  name,
  email,
  password
});
```

---

# 15. Login

## POST `/api/auth/login`

### Request

```json
{
  "email": "peer@example.com",
  "password": "password123"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "access_token": "JWT_TOKEN",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "name": "Peer",
      "email": "peer@example.com"
    }
  }
}
```

Frontend ต้องเก็บ Token สำหรับ Request ต่อไป

---

# 16. Current User

## GET `/api/auth/me`

ใช้ดึง User ที่ Login อยู่

### Header

```http
Authorization: Bearer <token>
```

### Response

```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "Peer",
    "email": "peer@example.com"
  }
}
```

---

# 17. Create Course

## POST `/api/courses`

Creator สร้าง Learning Goal ก่อน

### Request

```json
{
  "title": "ER Diagram Fundamentals",
  "description": "เรียนรู้พื้นฐานการออกแบบ ER Diagram",
  "goal": "ผู้เรียนสามารถออกแบบ ER Diagram จาก Business Requirement ได้"
}
```

### Backend ทำอะไร

1. Validate User
2. Create Course
3. ตั้ง status เป็น `DRAFT`
4. Save Database
5. Return Course

### Response

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "ER Diagram Fundamentals",
    "description": "เรียนรู้พื้นฐานการออกแบบ ER Diagram",
    "goal": "ผู้เรียนสามารถออกแบบ ER Diagram จาก Business Requirement ได้",
    "status": "DRAFT",
    "creator_id": 1,
    "created_at": "2026-08-16T13:00:00"
  }
}
```

---

# 18. Frontend — Create Course

หน้า

```text
CreateCourse.tsx
```

Form:

```text
Course Title
Description
Learning Goal
```

กด

```text
Create Course
```

เรียก

```ts
createCourse()
```

Backend ตอบ `course_id`

Frontend Navigate ไปหน้า

```text
/creator/courses/1/upload
```

---

# 19. Get Courses

## GET `/api/courses`

ใช้ดึง Course ของ Creator

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "ER Diagram Fundamentals",
      "status": "DRAFT"
    },
    {
      "id": 2,
      "title": "React Basic",
      "status": "PUBLISHED"
    }
  ]
}
```

Frontend ใช้ใน

```text
Creator Dashboard
My Courses
```

---

# 20. Get Course Detail

## GET `/api/courses/{course_id}`

ตัวอย่าง

```http
GET /api/courses/1
```

### Response

```json
{
  "success": true,
  "data": {
    "id": 1,
    "title": "ER Diagram Fundamentals",
    "description": "เรียนรู้พื้นฐาน ER Diagram",
    "goal": "สามารถสร้าง ER Diagram ได้",
    "status": "WAITING_VERIFICATION",
    "creator_id": 1
  }
}
```

---

# 21. Update Course

## PUT `/api/courses/{course_id}`

แก้ชื่อ / Goal / Description

### Request

```json
{
  "title": "ER Diagram Design",
  "description": "Updated description",
  "goal": "สามารถออกแบบ ER Diagram จาก Requirement จริงได้"
}
```

---

# 22. Delete Course

## DELETE `/api/courses/{course_id}`

### Response

```json
{
  "success": true
}
```

Backend ต้องตรวจว่า User เป็น Creator ของ Course นี้จริง

---

# 23. Upload Knowledge Document

นี่คือ API สำคัญมากของ SkillSync

## POST `/api/courses/{course_id}/documents`

ใช้ Upload Knowledge Source

เช่น

* PDF
* PowerPoint
* Word
* Notes

---

## Request

ใช้

```http
multipart/form-data
```

Fields:

```text
file
```

ตัวอย่าง Frontend:

```ts
const formData = new FormData();

formData.append("file", file);
```

แล้วส่ง

```ts
fetch(`${API_URL}/api/courses/${courseId}/documents`, {
  method: "POST",
  body: formData
});
```

---

# 24. Upload Response

```json
{
  "success": true,
  "data": {
    "id": 10,
    "course_id": 1,
    "filename": "database-lecture.pdf",
    "file_type": "pdf",
    "size": 2481032,
    "status": "UPLOADED"
  }
}
```

---

# 25. Document Status

Document อาจมี

```text
UPLOADED
↓
PROCESSING
↓
READY
```

ถ้าพัง:

```text
FAILED
```

---

# 26. Backend — Upload Document Flow

```text
Frontend Upload
       ↓
documents.py
       ↓
document_service.py
       ↓
File Storage
       ↓
Database Record
       ↓
Document Processing
```

ใน Phase AI:

```text
PDF
 ↓
Extract Text
 ↓
Chunk
 ↓
Embedding
 ↓
Vector DB
```

---

# 27. Get Course Documents

## GET `/api/courses/{course_id}/documents`

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": 10,
      "filename": "database-lecture.pdf",
      "status": "READY"
    },
    {
      "id": 11,
      "filename": "erd-example.pdf",
      "status": "READY"
    }
  ]
}
```

Frontend ใช้แสดง

```text
Knowledge Sources

✓ database-lecture.pdf
✓ erd-example.pdf
```

---

# 28. Delete Document

## DELETE `/api/documents/{document_id}`

ใช้ลบ Source ก่อน Generate

---

# 29. Generate Course ด้วย AI

## POST `/api/courses/{course_id}/generate`

Creator กด

```text
Generate Learning Path
```

หลัง Upload Document เสร็จ

---

## Request

อาจไม่ต้องส่ง Body เพราะ Backend มี

* Course Goal
* Documents

อยู่แล้ว

```json
{}
```

หรือสามารถเพิ่ม Option

```json
{
  "difficulty": "beginner",
  "language": "th"
}
```

---

# 30. Backend — Generate Flow

```text
Course Goal
+
Creator Documents
        ↓
Document Retrieval
        ↓
RAG
        ↓
LLM
        ↓
Generate Curriculum
        ↓
Modules
        ↓
Lessons
        ↓
Quiz
        ↓
Assessment
        ↓
Save Draft
```

ระหว่าง Generate

Course Status:

```text
GENERATING
```

Generate เสร็จ:

```text
WAITING_VERIFICATION
```

---

# 31. Generate Response

เพราะ AI อาจใช้เวลานาน แนะนำ Response ทันทีประมาณนี้

```json
{
  "success": true,
  "data": {
    "course_id": 1,
    "status": "GENERATING"
  }
}
```

จากนั้น Frontend Poll

```text
GET /api/courses/1/generation-status
```

---

# 32. Generation Status

## GET `/api/courses/{course_id}/generation-status`

### Response กำลังทำ

```json
{
  "success": true,
  "data": {
    "status": "GENERATING",
    "progress": 60
  }
}
```

### Response เสร็จ

```json
{
  "success": true,
  "data": {
    "status": "WAITING_VERIFICATION",
    "progress": 100
  }
}
```

Frontend แสดง Loading

```text
Analyzing documents...

Generating modules...

Generating lessons...

Generating assessments...
```

---

# 33. Get Generated Modules

## GET `/api/courses/{course_id}/modules`

ใช้หน้า Creator Review

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": 101,
      "title": "Entity and Attribute",
      "order": 1,
      "lessons": [
        {
          "id": 1001,
          "title": "What is an Entity?",
          "order": 1
        },
        {
          "id": 1002,
          "title": "Types of Attributes",
          "order": 2
        }
      ]
    },
    {
      "id": 102,
      "title": "Relationships",
      "order": 2,
      "lessons": []
    }
  ]
}
```

---

# 34. Lesson Detail

Lesson ควรมีประมาณนี้

```json
{
  "id": 1001,
  "module_id": 101,
  "title": "What is an Entity?",
  "content": "Entity หมายถึง...",
  "order": 1,
  "source_references": [
    {
      "document_id": 10,
      "page": 4
    }
  ]
}
```

`source_references` สำคัญ เพราะช่วยให้ Creator ดูได้ว่า AI สร้างจากเอกสารส่วนไหน

---

# 35. Edit Module

## PUT `/api/modules/{module_id}`

### Request

```json
{
  "title": "Entity, Attribute and Key",
  "order": 1
}
```

Frontend ใช้หน้า

```text
Creator Review / Course Builder
```

---

# 36. Edit Lesson

## PUT `/api/lessons/{lesson_id}`

### Request

```json
{
  "title": "Understanding Entity",
  "content": "Entity คือสิ่งที่เราต้องการเก็บข้อมูล...",
  "order": 1
}
```

Creator สามารถแก้สิ่งที่ AI Generate มาได้

---

# 37. Verification

นี่คือ Core Feature ของ SkillSync

## POST `/api/courses/{course_id}/verify`

Creator กด

```text
Verify & Approve
```

หลังตรวจ Course แล้ว

---

## Backend ต้องตรวจ

Course ต้องมีสถานะ

```text
WAITING_VERIFICATION
```

Creator ต้องเป็นเจ้าของ Course

---

## Response

```json
{
  "success": true,
  "data": {
    "course_id": 1,
    "status": "VERIFIED",
    "verified_at": "2026-08-16T15:30:00"
  }
}
```

---

# 38. ห้าม Publish ก่อน Verify

Backend ต้อง Block

```text
WAITING_VERIFICATION
↓
PUBLISHED
```

โดยตรง

ต้องผ่าน

```text
WAITING_VERIFICATION
↓
VERIFIED
↓
PUBLISHED
```

---

# 39. Publish Course

## POST `/api/courses/{course_id}/publish`

ใช้หลัง Verify แล้ว

### Response

```json
{
  "success": true,
  "data": {
    "course_id": 1,
    "status": "PUBLISHED"
  }
}
```

---

# 40. Frontend Creator Flow

หน้า Front ควรเดินประมาณนี้

```text
Dashboard
   ↓
Create Course
   ↓
Define Goal
   ↓
Upload Documents
   ↓
Generate
   ↓
Generating Screen
   ↓
Review Course
   ↓
Edit
   ↓
Verify
   ↓
Publish
```

---

# 41. Learner Enroll

## POST `/api/courses/{course_id}/enroll`

Learner กด

```text
Start Learning
```

### Response

```json
{
  "success": true,
  "data": {
    "enrollment_id": 500,
    "course_id": 1,
    "learner_id": 20,
    "status": "ACTIVE",
    "progress": 0
  }
}
```

---

# 42. Enrollment Status

แนะนำ

```text
ACTIVE
COMPLETED
DROPPED
```

---

# 43. Get My Enrollments

## GET `/api/enrollments`

### Response

```json
{
  "success": true,
  "data": [
    {
      "enrollment_id": 500,
      "course": {
        "id": 1,
        "title": "ER Diagram Fundamentals"
      },
      "progress": 40,
      "status": "ACTIVE"
    }
  ]
}
```

ใช้ใน Learner Dashboard

---

# 44. Learning Path

## GET `/api/courses/{course_id}/learning-path`

ใช้ดึง Module / Lesson ที่ Learner ต้องเรียน

### Response

```json
{
  "success": true,
  "data": {
    "course_id": 1,
    "progress": 25,
    "modules": [
      {
        "id": 101,
        "title": "Entity and Attribute",
        "status": "COMPLETED"
      },
      {
        "id": 102,
        "title": "Relationships",
        "status": "IN_PROGRESS"
      },
      {
        "id": 103,
        "title": "Cardinality",
        "status": "LOCKED"
      }
    ]
  }
}
```

---

# 45. Personalized Learning

ใน Phase แรก API สามารถส่ง Path เดียวก่อน

Phase ถัดไปสามารถส่ง Path ตาม User

```text
Learner A
→ Module 1
→ Module 2
→ Module 3

Learner B
→ Skip Module 1
→ Module 2
→ Extra Exercise
```

ดังนั้น Frontend **อย่า Hardcode ลำดับ Module เอง**

ให้ Backend เป็นคนส่งลำดับมา

---

# 46. Get Lesson

## GET `/api/lessons/{lesson_id}`

### Response

```json
{
  "success": true,
  "data": {
    "id": 1001,
    "title": "What is an Entity?",
    "content": "Entity คือ...",
    "module_id": 101,
    "status": "IN_PROGRESS"
  }
}
```

---

# 47. Complete Lesson

## POST `/api/lessons/{lesson_id}/complete`

Learner กด

```text
Complete Lesson
```

### Response

```json
{
  "success": true,
  "data": {
    "lesson_id": 1001,
    "status": "COMPLETED",
    "course_progress": 30
  }
}
```

---

# 48. Course Progress

## GET `/api/courses/{course_id}/progress`

### Response

```json
{
  "success": true,
  "data": {
    "course_id": 1,
    "progress": 60,
    "completed_lessons": 6,
    "total_lessons": 10,
    "current_module": {
      "id": 103,
      "title": "Cardinality"
    }
  }
}
```

---

# 49. Assessment List

## GET `/api/courses/{course_id}/assessments`

### Response

```json
{
  "success": true,
  "data": [
    {
      "id": 700,
      "title": "Entity Quiz",
      "type": "QUIZ",
      "status": "COMPLETED"
    },
    {
      "id": 701,
      "title": "Final ER Diagram",
      "type": "PROJECT",
      "status": "AVAILABLE"
    }
  ]
}
```

---

# 50. Assessment Type

อาจมี

```text
QUIZ
EXERCISE
PROJECT
FINAL
```

---

# 51. Get Assessment

## GET `/api/assessments/{assessment_id}`

### Response Quiz

```json
{
  "success": true,
  "data": {
    "id": 700,
    "title": "Entity Quiz",
    "type": "QUIZ",
    "questions": [
      {
        "id": 1,
        "question": "ข้อใดคือ Entity?",
        "type": "MULTIPLE_CHOICE",
        "choices": [
          {
            "id": "A",
            "text": "Customer"
          },
          {
            "id": "B",
            "text": "Blue"
          }
        ]
      }
    ]
  }
}
```

**ห้ามส่ง `correct_answer` ไป Frontend ก่อน Submit**

---

# 52. Submit Assessment

## POST `/api/assessments/{assessment_id}/submit`

### Request

```json
{
  "answers": [
    {
      "question_id": 1,
      "answer": "A"
    }
  ]
}
```

### Response

```json
{
  "success": true,
  "data": {
    "assessment_id": 700,
    "score": 80,
    "passed": true
  }
}
```

---

# 53. Practical Assessment

สำหรับ Project-Based Assessment

Request อาจเป็น

```json
{
  "submission_text": "คำอธิบาย...",
  "file_url": "..."
}
```

แต่ Feature นี้ทำ Phase หลังได้

---

# 54. Pre-Test

สำหรับ Personalized Learning ใน Phase ต่อไป

```text
GET  /api/courses/{course_id}/pretest

POST /api/courses/{course_id}/pretest/submit
```

ผล Pre-Test ใช้สร้าง Learning Path

---

# 55. AI Tutor — Future Endpoint

ยังไม่ใช่ MVP แรก

```text
POST /api/courses/{course_id}/ai-tutor
```

### Request

```json
{
  "lesson_id": 1001,
  "message": "ช่วยอธิบาย Entity แบบง่าย ๆ"
}
```

### Backend

```text
Question
+
Course Sources
+
Current Lesson
        ↓
RAG
        ↓
LLM
```

### Response

```json
{
  "success": true,
  "data": {
    "message": "Entity คือสิ่งที่เราต้องการเก็บข้อมูล...",
    "sources": [
      {
        "document_id": 10,
        "page": 4
      }
    ]
  }
}
```

---

# 56. Frontend Service Mapping

แนะนำ Frontend ทำแบบนี้

```text
src/services/
```

---

## `api.ts`

เก็บ Base Request

```ts
const API_URL = import.meta.env.VITE_API_URL;

export async function apiFetch(
  path: string,
  options: RequestInit = {}
) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error("API request failed");
  }

  return response.json();
}
```

Upload File ห้ามใช้ Header JSON ตัวเดียวกัน ต้องใช้ `FormData`

---

# 57. `courseApi.ts`

ควรมี

```ts
createCourse()

getCourses()

getCourse()

updateCourse()

deleteCourse()

generateCourse()

getGenerationStatus()

verifyCourse()

publishCourse()
```

---

# 58. `documentApi.ts`

ควรมี

```ts
uploadDocument()

getDocuments()

deleteDocument()
```

---

# 59. `learningApi.ts`

ควรมี

```ts
enrollCourse()

getEnrollments()

getLearningPath()

getLesson()

completeLesson()

getProgress()
```

---

# 60. `assessmentApi.ts`

ควรมี

```ts
getAssessments()

getAssessment()

submitAssessment()
```

---

# 61. Frontend Type

Front ควรสร้าง Type ให้ตรงกับ API

ตัวอย่าง

```ts
export interface Course {
  id: number;
  title: string;
  description: string;
  goal: string;
  status:
    | "DRAFT"
    | "GENERATING"
    | "WAITING_VERIFICATION"
    | "VERIFIED"
    | "PUBLISHED";
}
```

---

## Document

```ts
export interface CourseDocument {
  id: number;
  course_id: number;
  filename: string;
  file_type: string;
  status:
    | "UPLOADED"
    | "PROCESSING"
    | "READY"
    | "FAILED";
}
```

---

## Module

```ts
export interface LearningModule {
  id: number;
  title: string;
  order: number;
  lessons: Lesson[];
}
```

---

## Lesson

```ts
export interface Lesson {
  id: number;
  module_id: number;
  title: string;
  content: string;
  order: number;
}
```

---

# 62. Backend Structure Mapping

API แต่ละตัวควรไหลแบบนี้

```text
Request
   ↓
Route
   ↓
Schema Validation
   ↓
Service
   ↓
Database / AI / Storage
   ↓
Response
```

ตัวอย่าง Generate:

```text
POST /courses/1/generate
          ↓
courses.py
          ↓
course_service.py
          ↓
rag_service.py
          ↓
ai_service.py
          ↓
Database
```

---

# 63. Backend Route Responsibility

Route ทำแค่

* รับ Request
* Check Auth
* Validate
* เรียก Service
* Return Response

ไม่ควรเขียน AI Logic ทั้งหมดใน Route

ไม่ควรเป็น

```text
courses.py
└── 500 lines AI + DB + Validation
```

ควรแยกเป็น

```text
courses.py
    ↓
course_service.py
    ↓
ai_service.py
rag_service.py
database
```

---

# 64. Frontend Responsibility

Frontend รับผิดชอบ

* UI
* Form
* Loading
* Error Message
* Navigation
* Display Data
* เรียก API

Frontend **ไม่ควรตัดสิน Business Logic สำคัญเอง**

ตัวอย่าง:

อย่าให้ Front ตัดสินว่า

```ts
if (course.status === "WAITING_VERIFICATION") {
   course.status = "PUBLISHED";
}
```

ต้องเรียก Backend

```text
POST /verify

POST /publish
```

---

# 65. Backend Responsibility

Backend รับผิดชอบ

* Validation
* Permission
* Course Status
* Database
* File Processing
* AI
* RAG
* Verification
* Progress
* Assessment
* Security

---

# 66. Error ที่ Front ต้องรองรับ

ตัวอย่าง Backend:

```json
{
  "success": false,
  "error": {
    "code": "DOCUMENT_REQUIRED",
    "message": "Please upload at least one document before generating."
  }
}
```

Frontend แสดง

```text
กรุณาอัปโหลดเอกสารอย่างน้อย 1 ไฟล์ก่อน Generate
```

---

# 67. Recommended Error Code

## Course

```text
COURSE_NOT_FOUND

COURSE_NOT_VERIFIED

COURSE_ALREADY_PUBLISHED

INVALID_COURSE_STATUS
```

## Document

```text
DOCUMENT_NOT_FOUND

DOCUMENT_REQUIRED

UNSUPPORTED_FILE_TYPE

DOCUMENT_PROCESSING_FAILED
```

## Auth

```text
INVALID_CREDENTIALS

UNAUTHORIZED

FORBIDDEN
```

## AI

```text
AI_GENERATION_FAILED

KNOWLEDGE_SOURCE_NOT_READY
```

---

# 68. CORS

Backend Local ต้องอนุญาต Frontend

```text
http://localhost:5173
```

FastAPI:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

ไม่ควรเปิด

```text
*
```

ใน Production

---

# 69. Local Development

แต่ละคน Clone 2 Repository

```text
skillsync-client

skillsync-server
```

---

## Backend

```bash
cd skillsync-server
```

สร้าง venv

```bash
python -m venv .venv
```

Activate

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

Install

```bash
pip install -r requirements.txt
```

Run

```bash
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

---

# 70. Frontend

```bash
cd skillsync-client
```

```bash
npm install
```

```bash
npm run dev
```

Frontend:

```text
http://localhost:5173
```

---

# 71. Local Connection

```text
Browser
   ↓
localhost:5173
Frontend
   ↓
VITE_API_URL
   ↓
localhost:8000
Backend
```

ทั้ง Front และ Back ต้องเปิดพร้อมกัน

---

# 72. ตัวอย่าง End-to-End Flow

สมมติ Creator ต้องการสร้าง Course

> **ER Diagram**

---

## Step 1

Frontend:

```text
Create Course
```

เรียก:

```http
POST /api/courses
```

Backend ตอบ:

```json
{
  "id": 1,
  "status": "DRAFT"
}
```

---

## Step 2

Frontend ไปหน้า

```text
Upload Knowledge
```

Creator Upload

```text
database.pdf
```

เรียก

```http
POST /api/courses/1/documents
```

---

## Step 3

Backend Process Document

```text
UPLOADED
↓
PROCESSING
↓
READY
```

---

## Step 4

Creator กด

```text
Generate
```

Frontend:

```http
POST /api/courses/1/generate
```

---

## Step 5

Backend:

```text
Goal
+
database.pdf
   ↓
RAG
   ↓
AI
```

สร้าง

```text
Module 1
Entity

Module 2
Relationship

Module 3
Cardinality

Final Assessment
ER Diagram Design
```

---

## Step 6

Course:

```text
WAITING_VERIFICATION
```

Frontend เปิดหน้า Review

```http
GET /api/courses/1/modules
```

---

## Step 7

Creator แก้ Lesson

```http
PUT /api/lessons/1001
```

---

## Step 8

Creator กด

```text
Verify
```

เรียก

```http
POST /api/courses/1/verify
```

Course:

```text
VERIFIED
```

---

## Step 9

Creator กด Publish

```http
POST /api/courses/1/publish
```

Course:

```text
PUBLISHED
```

---

## Step 10

Learner กด Start

```http
POST /api/courses/1/enroll
```

---

## Step 11

Frontend ดึง Path

```http
GET /api/courses/1/learning-path
```

---

## Step 12

Learner เรียน

```http
GET /api/lessons/1001
```

---

## Step 13

เรียนจบ Lesson

```http
POST /api/lessons/1001/complete
```

---

## Step 14

ทำ Assessment

```http
POST /api/assessments/700/submit
```

---

# 73. API ที่ MVP ควรทำก่อน

ไม่ต้องทำทุก API พร้อมกัน

## Sprint 1

```text
GET  /health

POST /courses
GET  /courses
GET  /courses/{id}
```

---

## Sprint 2

```text
POST /courses/{id}/documents
GET  /courses/{id}/documents
```

---

## Sprint 3

```text
POST /courses/{id}/generate
GET  /courses/{id}/generation-status
GET  /courses/{id}/modules
```

---

## Sprint 4

```text
PUT  /modules/{id}
PUT  /lessons/{id}

POST /courses/{id}/verify
POST /courses/{id}/publish
```

---

## Sprint 5

```text
POST /courses/{id}/enroll

GET /courses/{id}/learning-path

GET /lessons/{id}

POST /lessons/{id}/complete
```

---

## Sprint 6

```text
GET  /assessments/{id}
POST /assessments/{id}/submit
```

หลังจาก Core Flow ทำงานแล้วค่อยเพิ่ม

```text
Auth
Personalization
Pre-Test
AI Tutor
Analytics
Portfolio
```

---

# 74. เวลาฝั่ง Front รอ Backend

Frontend ไม่จำเป็นต้องหยุดรอ

สามารถใช้ Mock Data

```ts
const mockCourse = {
  id: 1,
  title: "ER Diagram Fundamentals",
  status: "WAITING_VERIFICATION"
};
```

แต่ Interface ต้องพยายามให้ตรง API Doc

พอ Backend เสร็จ

เปลี่ยนจาก

```text
Mock
```

เป็น

```text
API
```

ได้ทันที

---

# 75. วิธีแก้ API Contract

ถ้าฝั่งใดฝั่งหนึ่งต้องการเปลี่ยน เช่น

จาก

```json
{
  "course_name": "React"
}
```

เป็น

```json
{
  "title": "React"
}
```

ต้องแจ้งอีกฝั่งก่อน

ไม่ควรเปลี่ยน Backend Response เองแล้ว Push โดยไม่บอก Front

API Doc นี้ถือเป็น

# **Contract ระหว่าง Front และ Back**

---

# 76. Naming Convention

แนะนำใช้

## URL

```text
lowercase
plural nouns
```

ดี:

```text
/api/courses

/api/documents

/api/assessments
```

ไม่แนะนำ:

```text
/api/getCourse

/api/CreateDocument

/api/assessmentData
```

---

# 77. JSON Naming

ใช้

```text
snake_case
```

เช่น

```json
{
  "course_id": 1,
  "creator_id": 10,
  "created_at": "..."
}
```

Frontend TypeScript map ตาม API ได้ตรง ๆ

---

# 78. Date Format

ใช้ ISO 8601

```text
2026-08-16T15:30:00Z
```

ไม่ควรส่ง

```text
16/8/69
```

เพราะ Front จัด Format เองได้

---

# 79. สิ่งที่ Front และ Back ต้องตกลงก่อนทำ Feature

ก่อนเริ่ม Feature ใหม่ ให้ตกลง 5 อย่างนี้

### 1. Endpoint

ตัวอย่าง

```text
POST /api/courses/{id}/generate
```

### 2. Request

Front ต้องส่งอะไร

### 3. Response

Back จะตอบอะไร

### 4. Error

มีกรณีอะไรบ้าง

### 5. Status

ข้อมูลจะเปลี่ยนสถานะอย่างไร

---

# 80. Core Rule ของ SkillSync

สิ่งที่ Backend ต้องรักษาไว้เสมอคือ

```text
Creator Uploads Knowledge
          ↓
AI Generates
          ↓
Creator Reviews
          ↓
Creator Verifies
          ↓
Publish
          ↓
Learner
```

AI Generated Content **ห้าม Publish อัตโนมัติ**

Creator ต้องเป็นคน Verify ก่อนเสมอ

---

# สรุปสำหรับ Frontend

Frontend ทำ

```text
UI
Form
Upload
Loading
Review
Display
Navigation
Call API
```

แล้วเรียก Backend ผ่าน

```text
src/services/
```

Front ไม่ต้องทำ

```text
Database
AI
RAG
Course Status Logic
Permission
```

---

# สรุปสำหรับ Backend

Backend ทำ

```text
API
Validation
Database
Authentication
Upload
Document Processing
AI
RAG
Verification
Course Status
Learning Progress
Assessment
```

แล้วส่ง JSON ให้ Frontend

---

# สรุปสั้นที่สุด

```text
Frontend
= คนใช้เห็นและกด

Backend
= รับสิ่งที่ Front ส่งมาแล้วทำงาน

Database
= เก็บข้อมูล

AI / RAG
= อ่าน Source และช่วยสร้าง Learning

API
= ตัวกลางที่ทำให้ Front กับ Back คุยกัน
```

Core Architecture:

```text
Creator
   ↓
Frontend
   ↓
API
   ↓
Backend
   ↓
Document + AI + Database
   ↓
API Response
   ↓
Frontend
   ↓
Creator Verify
   ↓
Learner
```

## SkillSync Core Flow

**Upload Knowledge → AI Builds → You Verify → They Learn.**
