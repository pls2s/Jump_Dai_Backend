# SkillSync AI — Backend

Backend สำหรับโปรเจกต์ **SkillSync AI**
พัฒนาด้วย **FastAPI + Python**

ระบบนี้ทำหน้าที่เป็น API หลักสำหรับเชื่อมต่อ Frontend, Database, ระบบอัปโหลดเอกสาร และในอนาคตจะรองรับ AI / RAG สำหรับสร้าง Learning Path จากเอกสารที่ Creator อัปโหลด

---

## ภาพรวมของ Backend

Backend จะรับผิดชอบงานหลัก เช่น

* Authentication และการจัดการผู้ใช้
* Creator / Learner
* Course และ Learning Path
* Upload เอกสาร
* จัดการ Knowledge Source
* AI Generate บทเรียน
* Creator Verification
* Quiz และ Assessment
* Progress ของผู้เรียน
* Personalized Learning
* เชื่อมต่อ Database
* เชื่อมต่อ AI / RAG ในอนาคต

---

# Core Flow ของ SkillSync

Flow หลักของระบบคือ

```text
Creator
   ↓
กำหนด Learning Goal
   ↓
Upload Knowledge
PDF / Slide / Note / Document
   ↓
Backend
   ↓
Document Processing
   ↓
AI / RAG
   ↓
Generate Learning Content
   ↓
Creator Review
   ↓
Verify & Approve
   ↓
Publish
   ↓
Learner
   ↓
Personalized Learning
   ↓
Assessment
```

แนวคิดสำคัญคือ

```text
Human Provides Knowledge
        ↓
AI Structures Learning
        ↓
Human Verifies Quality
        ↓
AI Personalizes Learning
```

AI จะไม่ควรสร้างบทเรียนแล้ว Publish ให้ผู้เรียนทันที

ทุก Course ต้องผ่านการตรวจสอบจาก Creator ก่อน

---

# Tech Stack

## Backend

* Python
* FastAPI
* Pydantic

## Database

วางแผนใช้

* PostgreSQL
* Supabase

## AI

วางแผนเพิ่มในภายหลัง

* LLM API
* RAG
* Embeddings
* Vector Database / pgvector

## Testing

* Pytest
* FastAPI TestClient
* HTTPX

## Deployment

* Docker
* Cloud Deployment

---

# โครงสร้าง Project

```text
skillsync-server/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   │
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── health.py
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── courses.py
│   │       ├── documents.py
│   │       ├── learning.py
│   │       └── assessments.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── security.py
│   │
│   ├── database/
│   │   ├── __init__.py
│   │   ├── session.py
│   │   └── base.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── course.py
│   │   ├── document.py
│   │   ├── module.py
│   │   ├── lesson.py
│   │   ├── enrollment.py
│   │   ├── progress.py
│   │   ├── assessment.py
│   │   └── verification.py
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── course.py
│   │   ├── document.py
│   │   ├── learning.py
│   │   └── assessment.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── document_service.py
│   │   ├── ai_service.py
│   │   ├── rag_service.py
│   │   ├── course_service.py
│   │   └── assessment_service.py
│   │
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
│
├── tests/
│   ├── __init__.py
│   └── test_health.py
│
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── Dockerfile
```

---

# อธิบายแต่ละ Folder

## `app/`

เป็น Folder หลักของ Backend

โค้ดทั้งหมดของ FastAPI จะอยู่ในนี้

---

## `app/main.py`

เป็นจุดเริ่มต้นของ Backend

ใช้สำหรับสร้าง FastAPI Application

ตัวอย่าง

```python
from fastapi import FastAPI

app = FastAPI(
    title="SkillSync AI API",
    version="0.1.0"
)
```

เวลารัน Backend เราจะเรียกไฟล์นี้

```bash
uvicorn app.main:app --reload
```

---

# `app/api/`

ใช้เก็บ API Routes

เช่น

```text
/api/auth
/api/users
/api/courses
/api/documents
/api/learning
/api/assessments
```

---

## `api/router.py`

ใช้รวม Route ทั้งหมดเข้าด้วยกัน

ตัวอย่าง

```text
health
auth
users
courses
documents
learning
assessments
```

แล้วนำ Router หลักไปใส่ใน `main.py`

---

# `api/routes/`

เก็บ Endpoint ของแต่ละ Feature

---

## `health.py`

ใช้ตรวจสอบว่า Backend ยังทำงานอยู่หรือไม่

Endpoint

```http
GET /api/health
```

Response

```json
{
  "status": "ok"
}
```

---

## `auth.py`

ในอนาคตใช้สำหรับระบบ

* Login
* Register
* Logout
* Token
* Authentication

---

## `users.py`

ใช้สำหรับข้อมูล User

เช่น

```text
GET /users/me
GET /users/{id}
PUT /users/{id}
```

User สามารถมี Role เช่น

```text
creator
learner
admin
```

ผู้ใช้หนึ่งคนอาจเป็นทั้ง Creator และ Learner ได้ในอนาคต

---

# `courses.py`

ใช้สำหรับจัดการ Learning Course

ตัวอย่าง Feature

```text
Create Course
Edit Course
Delete Course
Generate Course
Verify Course
Publish Course
```

Flow ตัวอย่าง

```text
DRAFT
  ↓
GENERATED
  ↓
WAITING_VERIFICATION
  ↓
VERIFIED
  ↓
PUBLISHED
```

สถานะนี้สำคัญมาก เพราะ Course ที่ AI สร้างยังไม่ควร Publish ทันที

---

# `documents.py`

ใช้สำหรับจัดการ Knowledge Source

ตัวอย่าง

```text
Upload PDF
Upload Document
Delete Document
View Document
Process Document
```

เอกสารที่ Upload จะถูกใช้เป็น Source ให้ AI

ตัวอย่าง

```text
PDF
PowerPoint
Lecture Note
Training Manual
Guideline
Document
```

---

# `learning.py`

ใช้สำหรับ Feature ฝั่งผู้เรียน เช่น

* Join Course
* Learning Path
* Lesson Progress
* Personalized Learning
* Adaptive Learning

ในช่วง MVP อาจทำแค่

```text
Join Course
View Lesson
Complete Lesson
View Progress
```

ก่อน

---

# `assessments.py`

ใช้สำหรับ

* Quiz
* Exercise
* Assessment
* Final Assessment

เป้าหมายคือไม่ได้วัดแค่ว่า

```text
เรียนจบหรือไม่
```

แต่ต้องสามารถวัดว่า

```text
ผู้เรียนบรรลุ Learning Goal หรือไม่
```

---

# `core/`

เก็บ Configuration หลักของระบบ

---

## `config.py`

ใช้สำหรับ Environment Variables

เช่น

```text
APP_NAME
APP_ENV
API_PREFIX

DATABASE_URL

SUPABASE_URL
SUPABASE_KEY

LLM_API_KEY
```

ค่าพวก Secret Key ห้ามเขียนลง Source Code โดยตรง

ต้องเก็บไว้ใน `.env`

---

## `security.py`

ในอนาคตใช้เกี่ยวกับ

* Password Hash
* JWT
* Authentication
* Authorization

---

# `database/`

ใช้สำหรับการเชื่อมต่อ Database

วางแผนใช้

```text
PostgreSQL
+
Supabase
```

---

## `session.py`

ใช้สร้าง Database Connection / Session

---

## `base.py`

ใช้สำหรับ Base Model ของ Database

---

# `models/`

เก็บ Database Model

Entity หลักของ SkillSync มีประมาณนี้

---

## User

ข้อมูลผู้ใช้

```text
id
name
email
role
created_at
```

---

## Course

Learning Program ที่ Creator สร้าง

```text
id
creator_id
title
goal
description
status
created_at
```

---

## Document

Source ที่ Creator Upload

```text
id
course_id
filename
file_url
file_type
status
```

---

## Module

Module ภายใน Course

```text
Course
 ├── Module 1
 ├── Module 2
 └── Module 3
```

---

## Lesson

Lesson จะอยู่ภายใน Module

```text
Course
  ↓
Module
  ↓
Lesson
```

---

## Enrollment

ใช้เชื่อม

```text
Learner
   ↕
Course
```

ตัวอย่าง

```text
learner_id
course_id
status
enrolled_at
```

---

## Progress

เก็บ Progress ของ Learner

เช่น

```text
lesson_completed
score
progress_percentage
```

---

## Assessment

ใช้เก็บ

* Quiz
* Assignment
* Final Assessment

---

## Verification

ใช้เก็บข้อมูลการ Verify

เช่น

```text
course_id
creator_id
verified_at
status
```

ในอนาคตอาจเพิ่ม

```text
AI_GENERATED

CREATOR_VERIFIED

EXPERT_VERIFIED
```

---

# `schemas/`

ใช้สำหรับ Request / Response ของ API

ใช้ Pydantic

เช่น

```python
class KnowledgeUploadCourseCreate(BaseModel):
    title: str
    description: str
    target_learner: str
    difficulty_level: str
    learning_objective: str
```

Frontend ส่ง

```json
{
  "title": "ER Diagram Basics",
  "description": "พื้นฐานการออกแบบ ER Diagram",
  "target_learner": "ผู้เริ่มต้นด้านการพัฒนาซอฟต์แวร์",
  "difficulty_level": "BEGINNER",
  "learning_objective": "สามารถออกแบบ ER Diagram ได้"
}
```

Backend จะ Validate ข้อมูลผ่าน Schema ก่อน

---

# `services/`

Folder นี้ใช้เก็บ Business Logic หลัก

อย่าเอา Logic จำนวนมากไปใส่ใน Route

แนวคิดคือ

```text
Route
  ↓
Service
  ↓
Database / AI
```

---

## `document_service.py`

รับผิดชอบเรื่อง Document

ในอนาคตจะทำ

```text
Upload
Extract Text
Split Chunk
Process Document
```

---

## `ai_service.py`

ใช้ติดต่อ LLM

ตัวอย่างงานในอนาคต

```text
Generate Curriculum
Generate Lesson
Generate Quiz
Generate Assessment
```

---

## `rag_service.py`

ใช้สำหรับระบบ RAG

Flow คร่าว ๆ

```text
Creator Upload Document
        ↓
Extract Text
        ↓
Split Chunks
        ↓
Embedding
        ↓
Vector Database
        ↓
Retrieve Relevant Knowledge
        ↓
LLM
```

จุดสำคัญคือ AI ควรใช้ข้อมูลจากเอกสารของ Creator เป็นหลัก

ไม่ใช่สร้างเนื้อหาจากความรู้ทั่วไปของ AI อย่างเดียว

---

## `course_service.py`

Business Logic ของ Course

ตัวอย่าง

```text
Create Course
Generate Course
Verify Course
Publish Course
```

---

## `assessment_service.py`

ใช้สำหรับ

* Generate Quiz
* Evaluate Assessment
* Calculate Score

---

# `utils/`

Utility Functions ที่ใช้ร่วมกันหลายส่วน

ไม่ควรเอา Business Logic หลักมาใส่ใน Folder นี้

---

# `tests/`

ใช้สำหรับ Automated Testing

ตอนเริ่ม Project มีอย่างน้อย

```text
test_health.py
```

เพื่อเช็กว่า API ทำงาน

Run Test ด้วย

```bash
pytest
```

---

# การติดตั้ง Project

## 1. Clone Repository

```bash
git clone <repository-url>
```

จากนั้นเข้า Folder

```bash
cd skillsync-server
```

---

# 2. สร้าง Virtual Environment

Mac / Linux

```bash
python3 -m venv .venv
```

เปิดใช้งาน

```bash
source .venv/bin/activate
```

Windows

```bash
python -m venv .venv
```

เปิดใช้งาน

```bash
.venv\Scripts\activate
```

---

# 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

# 4. Environment Variables

Copy

```text
.env.example
```

เป็น

```text
.env
```

ตัวอย่าง

```env
APP_NAME=SkillSync AI API
APP_ENV=development
API_PREFIX=/api

DATABASE_URL=

SUPABASE_URL=
SUPABASE_KEY=

LLM_API_KEY=
```

---

# ห้าม Push `.env`

ไฟล์

```text
.env
```

จะมี Secret Key

ดังนั้นต้องอยู่ใน `.gitignore`

ห้าม Commit ขึ้น GitHub

---

# 5. Run Backend

```bash
uvicorn app.main:app --reload
```

ถ้ารันสำเร็จจะเปิดที่

```text
http://localhost:8000
```

---

# API Documentation

FastAPI สร้าง API Documentation ให้อัตโนมัติ

Swagger UI

```text
http://localhost:8000/docs
```

ReDoc

```text
http://localhost:8000/redoc
```

เวลา Frontend ต้องการดูว่า Backend มี API อะไร ให้เข้า `/docs` ได้เลย

---

# Test Health API

เปิด

```text
http://localhost:8000/api/health
```

ควรได้

```json
{
  "status": "ok"
}
```

---

# การทำงานร่วมกับ Frontend

Frontend Repository

```text
skillsync-client
```

Backend Repository

```text
skillsync-server
```

Frontend จะเรียก Backend ผ่าน REST API

ตัวอย่าง

```text
SkillSync Client
       ↓
    REST API
       ↓
SkillSync Server
       ↓
Database / AI / Storage
```

Local Development

Frontend

```text
http://localhost:5173
```

Backend

```text
http://localhost:8000
```

ดังนั้น Frontend `.env`

```env
VITE_API_URL=http://localhost:8000
```

---

# API ที่วางแผนไว้

## Authentication

```http
POST /api/auth/register
POST /api/auth/login
```

---

## Function 2 — Course Configuration

```http
POST /api/courses
```

ใช้สร้าง course context สำหรับ Knowledge Source เท่านั้น ยังไม่มี Course CRUD ใน
Function 2 และ response จะมี `certificate_available: true` เมื่อ
`difficulty_level` เป็น `ADVANCED`

---

## Knowledge Documents

```http
POST /api/courses/{course_id}/documents

GET /api/courses/{course_id}/documents

DELETE /api/documents/{document_id}

POST /api/courses/{course_id}/knowledge-sources/manual

POST /api/courses/{course_id}/knowledge-sources/url

GET /api/courses/{course_id}/knowledge-sources
```

---

## AI Generate

```http
POST /api/courses/{course_id}/generate
```

Flow

```text
Course Goal
+
Documents
    ↓
AI / RAG
    ↓
Modules
Lessons
Exercises
Quiz
Assessment
```

---

# Verification

```http
POST /api/courses/{course_id}/verify
```

ก่อน Verify

```text
WAITING_VERIFICATION
```

หลัง Verify

```text
VERIFIED
```

---

# Publish

```http
POST /api/courses/{course_id}/publish
```

ควร Publish ได้เฉพาะ Course ที่

```text
VERIFIED
```

แล้วเท่านั้น

---

# Learning

```http
POST /api/courses/{course_id}/enroll

GET /api/courses/{course_id}/learning-path

GET /api/lessons/{lesson_id}

POST /api/lessons/{lesson_id}/complete
```

---

# Assessment

```http
GET /api/courses/{course_id}/assessment

POST /api/assessments/{assessment_id}/submit
```

---

# Git Workflow ของทีม

Branch หลัก

```text
main
  ↑
 dev
```

ทุก Feature ให้แตก Branch จาก `dev`

ตัวอย่าง

```text
dev
 ├── feature/auth
 ├── feature/course
 ├── feature/document-upload
 ├── feature/ai-generation
 ├── feature/verification
 └── feature/assessment
```

---

# เริ่มทำ Feature

ก่อนเริ่มควรดึง Code ล่าสุด

```bash
git checkout dev
```

```bash
git pull origin dev
```

จากนั้นสร้าง Branch

```bash
git checkout -b feature/document-upload
```

---

# Commit

ตัวอย่าง

```bash
git add .
```

```bash
git commit -m "feat: add document upload endpoint"
```

จากนั้น Push

```bash
git push origin feature/document-upload
```

แล้วเปิด Pull Request

```text
feature/document-upload
        ↓
       dev
```

ไม่ควร Push Feature เข้า `main` ตรง ๆ

---

# Commit Convention

แนะนำให้ใช้รูปแบบนี้

```text
feat:
fix:
chore:
docs:
refactor:
test:
```

ตัวอย่าง

```text
feat: add course creation endpoint
```

```text
feat: add document upload service
```

```text
fix: resolve course status validation
```

```text
docs: update backend setup guide
```

```text
test: add health endpoint tests
```

```text
chore: initialize FastAPI backend
```

---

# สิ่งที่ยังไม่ต้องทำใน First Version

ช่วงแรกยังไม่จำเป็นต้องรีบทำทุกอย่างพร้อมกัน

ให้เริ่มจาก

```text
1. FastAPI Structure
2. Health API
3. Database
4. User
5. Course
6. Document Upload
```

จากนั้นค่อยเพิ่ม

```text
7. Document Processing
8. AI
9. RAG
10. Verification
11. Learner
12. Assessment
13. Personalization
```

---

# MVP Backend Priority

ลำดับที่แนะนำ

## Phase 1

```text
FastAPI
Database
User
Course
```

## Phase 2

```text
Document Upload
Document Storage
Document Processing
```

## Phase 3

```text
RAG
AI Course Generation
```

## Phase 4

```text
Creator Verification
Publish
```

## Phase 5

```text
Enrollment
Lesson
Progress
Quiz
Assessment
```

## Phase 6

```text
Personalized Learning
Adaptive Learning
AI Tutor
```

---

# กฎสำคัญของ Backend

## 1. อย่าใส่ Secret ลง GitHub

ห้าม Commit

```text
.env
API Key
Database Password
Supabase Secret
```

---

## 2. AI Content ต้อง Verify ก่อน Publish

Flow ต้องเป็น

```text
AI Generated
     ↓
Creator Review
     ↓
Creator Verified
     ↓
Published
```

ห้ามข้าม Verification

---

## 3. AI ต้องอิง Knowledge Source

เป้าหมายคือ

```text
Creator Documents
      ↓
     RAG
      ↓
     LLM
```

ไม่ใช่

```text
Prompt
 ↓
LLM เดาล้วน ๆ
```

---

## 4. Route ไม่ควรมี Business Logic เยอะ

ควรแยกเป็น

```text
Route
 ↓
Service
 ↓
Database / AI
```

เพื่อให้ Code อ่านง่ายและแก้ง่าย

---

# เป้าหมายของ Repository นี้

Backend ของ SkillSync จะพัฒนาจากระบบ API พื้นฐานไปสู่ระบบที่สามารถทำ Flow นี้ได้ครบ

```text
Creator
   ↓
Create Goal
   ↓
Upload Knowledge
   ↓
AI Generate
   ↓
Creator Verify
   ↓
Publish
   ↓
Learner
   ↓
Personalized Learning
   ↓
Assessment
   ↓
Verified Learning Outcome
```

## Core Principle

> **Creator เป็นเจ้าของความรู้
> AI ช่วยเปลี่ยนความรู้ให้เป็นการเรียน
> Creator ตรวจสอบก่อนเผยแพร่
> และ AI ช่วยปรับการเรียนให้เหมาะกับ Learner แต่ละคน**
