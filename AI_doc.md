# SkillSync AI — Backend AI Documentation

**Document:** `AI_DOC.md`
**Version:** 0.1
**Status:** Draft / MVP
**Backend:** Python + FastAPI
**AI Architecture:** LLM + RAG + Human Verification
**Vector Storage:** PostgreSQL + pgvector / Supabase
**Core Principle:** **Source-Grounded AI + Human-in-the-Loop**

---

# 1. เอกสารนี้มีไว้ทำอะไร

เอกสารนี้อธิบายระบบ AI ฝั่ง Backend ของ **SkillSync AI**

มีไว้ให้ทีม Backend และ AI เข้าใจตรงกันว่า

* AI รับข้อมูลอะไร
* AI อ่านเอกสารยังไง
* RAG ทำงานตรงไหน
* AI สร้างบทเรียนยังไง
* Course ถูก Generate อย่างไร
* Creator Verify ตรงไหน
* AI Tutor ใช้ข้อมูลจากไหน
* Assessment สร้างอย่างไร
* ข้อมูลอะไรต้องเก็บใน Database
* Frontend ติดต่อ AI ผ่าน API ไหน
* ระบบต้องป้องกัน AI Hallucination อย่างไร

---

# 2. Core Concept ของ AI

AI ของ SkillSync ไม่ควรทำงานแบบ

```text
User Prompt
   ↓
LLM
   ↓
Generate Course
```

เพราะ AI อาจใช้ความรู้ทั่วไปของตัวเองและสร้างข้อมูลที่ไม่มีอยู่ใน Source

SkillSync จะใช้แนวคิด

```text
Creator
   ↓
Learning Goal
+
Knowledge Documents
   ↓
Document Processing
   ↓
Knowledge Base
   ↓
RAG
   ↓
LLM
   ↓
Generated Learning Content
   ↓
Creator Verification
   ↓
Publish
```

ดังนั้น Core Principle คือ

# **Human Provides Knowledge**

Creator เป็นคนเลือก Source

↓

# **AI Structures Learning**

AI ช่วยเปลี่ยน Source เป็นบทเรียน

↓

# **Human Verifies Quality**

Creator ตรวจสอบ Output

↓

# **AI Personalizes Learning**

AI ช่วยปรับการเรียนให้ Learner

---

# 3. AI มีหน้าที่อะไรใน SkillSync

AI ไม่ได้มีหน้าที่เดียว

แบ่งออกเป็นประมาณ 6 ส่วนหลัก

```text
1. Document Understanding
2. Knowledge Retrieval
3. Curriculum Generation
4. Learning Content Generation
5. Assessment Generation
6. AI Tutor / Personalization
```

---

# 4. ภาพรวม AI Architecture

```text
                  Creator
                     │
          ┌──────────┴──────────┐
          │                     │
     Learning Goal         Upload Documents
                                │
                                ▼
                      Document Processing
                                │
                     Extract / Clean Text
                                │
                             Chunking
                                │
                           Embeddings
                                │
                                ▼
                       Vector Database
                          PostgreSQL
                           + pgvector
                                │
                                │
                     ┌──────────┴──────────┐
                     │                     │
                     ▼                     ▼
                  Retrieval              Metadata
                     │
                     ▼
                    RAG
                     │
                     ▼
                    LLM
                     │
          ┌──────────┼────────────┐
          │          │            │
      Curriculum   Lessons     Assessments
          │          │            │
          └──────────┼────────────┘
                     │
                     ▼
               Generated Draft
                     │
                     ▼
              Creator Verify
                     │
                     ▼
                  Publish
                     │
                     ▼
                  Learner
```

---

# 5. Backend AI Folder Structure

แนะนำประมาณนี้

```text
app/
│
├── services/
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── llm_service.py
│   │   ├── embedding_service.py
│   │   ├── retrieval_service.py
│   │   ├── curriculum_service.py
│   │   ├── lesson_service.py
│   │   ├── assessment_service.py
│   │   ├── tutor_service.py
│   │   └── personalization_service.py
│   │
│   ├── documents/
│   │   ├── document_service.py
│   │   ├── parser_service.py
│   │   ├── chunk_service.py
│   │   └── knowledge_service.py
│   │
│   └── course_service.py
│
├── prompts/
│   ├── curriculum_prompt.py
│   ├── lesson_prompt.py
│   ├── quiz_prompt.py
│   ├── assessment_prompt.py
│   └── tutor_prompt.py
│
├── models/
│   ├── document.py
│   ├── document_chunk.py
│   ├── course.py
│   ├── module.py
│   ├── lesson.py
│   └── assessment.py
│
└── schemas/
    ├── ai.py
    ├── course.py
    └── learning.py
```

---

# 6. ทำไมควรแยก AI Service

อย่าใส่ AI Logic ทั้งหมดไว้ใน

```text
courses.py
```

หรือ

```text
ai_service.py
```

ไฟล์เดียว

เพราะเมื่อ Feature เพิ่มขึ้นจะดูแลยากมาก

ควรเป็น

```text
API Route
   ↓
Course Service
   ↓
AI Service
   ↓
RAG / LLM / Database
```

ตัวอย่าง

```text
POST /courses/1/generate
        ↓
course_service.py
        ↓
curriculum_service.py
        ↓
retrieval_service.py
        ↓
llm_service.py
```

---

# 7. Document Processing Pipeline

ก่อน AI Generate Course ได้

Document ต้องผ่าน Processing ก่อน

Flow:

```text
Upload File
   ↓
Store Original File
   ↓
Extract Text
   ↓
Clean Text
   ↓
Split into Chunks
   ↓
Generate Embeddings
   ↓
Save Chunks + Embeddings
   ↓
Document Status = READY
```

---

# 8. Document Status

แนะนำให้มี

```text
UPLOADED
↓
PROCESSING
↓
READY
```

ถ้าเกิด Error

```text
FAILED
```

AI Generate Course ต้องใช้ Document ที่มี Status

```text
READY
```

เท่านั้น

---

# 9. Supported Document Types

MVP แนะนำเริ่มจาก

```text
PDF
TXT
DOCX
```

ถ้าทีมมีเวลาเพิ่ม

```text
PPTX
Markdown
Web Text
```

แต่ **MVP ควรเริ่ม PDF ก่อน**

เพราะ Demo ง่ายและ Scope ไม่ใหญ่เกินไป

---

# 10. Document Parsing

ตัวอย่าง

```text
database.pdf
```

Backend ทำ

```text
PDF
 ↓
Extract Text
 ↓
Page 1
Page 2
Page 3
...
```

ควรเก็บ Page Number ไว้ด้วย

เพราะภายหลังต้องสามารถบอก Creator ได้ว่า

> Lesson นี้อ้างอิงจากหน้าไหนของเอกสาร

---

# 11. Document Chunk

หลัง Extract Text แล้ว

ไม่ควรส่งเอกสารทั้งเล่มเข้า LLM ทุกครั้ง

ต้อง Split เป็น

```text
Chunk 1
Chunk 2
Chunk 3
...
```

ตัวอย่าง

```text
Document
   ↓
Page 1-2 → Chunk 1
Page 2-3 → Chunk 2
Page 3-4 → Chunk 3
```

แต่ควร Split ตาม Semantic Content ถ้าทำได้

เช่น

```text
Topic: Entity
Topic: Attribute
Topic: Relationship
```

ดีกว่าตัดตามจำนวนตัวอักษรแบบไม่สน Context

---

# 12. ข้อมูลที่ควรเก็บในแต่ละ Chunk

ตัวอย่าง

```json
{
  "id": 1001,
  "document_id": 10,
  "course_id": 1,
  "content": "Entity คือ...",
  "page_start": 4,
  "page_end": 5,
  "chunk_index": 3
}
```

และมี

```text
embedding
```

สำหรับ Vector Search

---

# 13. Embedding

Embedding ใช้เปลี่ยน Text เป็น Vector

ตัวอย่าง

```text
"Entity คือสิ่งที่เราต้องการเก็บข้อมูล"
          ↓
Embedding Model
          ↓
[0.012, -0.391, 0.883, ...]
```

Vector นี้จะใช้ค้นหาเนื้อหาที่มีความหมายใกล้กัน

---

# 14. Vector Database

วางแผนใช้

```text
PostgreSQL
+
pgvector
```

หรือ Supabase ที่ใช้ PostgreSQL อยู่แล้ว

เก็บ

```text
document_chunks
+
embedding
```

ตัวอย่าง Concept

```text
document_chunks
---------------
id
document_id
course_id
content
page_start
page_end
embedding
```

---

# 15. RAG คืออะไรใน SkillSync

RAG =

**Retrieval-Augmented Generation**

หน้าที่คือ

> ก่อนให้ LLM ตอบหรือสร้างอะไร ให้ค้นข้อมูลจากเอกสารของ Creator มาก่อน

Flow

```text
Question / Goal
      ↓
Embedding
      ↓
Vector Search
      ↓
Relevant Chunks
      ↓
Prompt
      ↓
LLM
```

---

# 16. ตัวอย่าง RAG

Creator Upload

```text
Database Lecture.pdf
```

Goal

> ผู้เรียนต้องสามารถออกแบบ ER Diagram ได้

ระบบค้น

```text
Entity
Attribute
Relationship
Cardinality
Primary Key
Weak Entity
```

จาก Source ก่อน

แล้วเอาข้อมูลที่ Retrieve ได้ส่งเข้า LLM

---

# 17. สิ่งที่ไม่ควรทำ

ไม่ควรทำแบบ

```text
Prompt:

"สร้างบทเรียน ER Diagram ให้หน่อย"
```

แล้วให้ LLM Generate จากความรู้ตัวเองทั้งหมด

เพราะอาจ

* ไม่ตรงกับ Source ของ Creator
* เพิ่มข้อมูลที่ Creator ไม่ต้องการ
* ใช้ Terminology คนละแบบ
* เกิด Hallucination

---

# 18. Retrieval Flow

ตัวอย่าง Backend

```text
Goal
"ออกแบบ ER Diagram ได้"

      ↓

Create Search Queries

"Entity"
"Attribute"
"Relationship"
"Cardinality"

      ↓

Vector Search

      ↓

Top Relevant Chunks

      ↓

Send Context to LLM
```

---

# 19. Retrieval Result

ตัวอย่าง

```json
[
  {
    "content": "Entity หมายถึง...",
    "document_id": 10,
    "page": 4,
    "score": 0.91
  },
  {
    "content": "Relationship คือ...",
    "document_id": 10,
    "page": 8,
    "score": 0.88
  }
]
```

---

# 20. Source Reference

Generated Content ควรเก็บ Source Reference

เช่น Lesson

```json
{
  "id": 1001,
  "title": "Understanding Entity",
  "content": "Entity คือ...",
  "source_references": [
    {
      "document_id": 10,
      "page": 4
    },
    {
      "document_id": 10,
      "page": 5
    }
  ]
}
```

ทำให้ Creator ตรวจได้ว่า AI ใช้อะไรเป็น Source

---

# 21. Course Generation Pipeline

เมื่อ Creator กด

```text
Generate Course
```

Backend ทำ

```text
1. Load Course Goal
2. Load READY Documents
3. Retrieve Relevant Knowledge
4. Generate Learning Objectives
5. Generate Course Structure
6. Generate Modules
7. Generate Lessons
8. Generate Exercises
9. Generate Quiz
10. Generate Final Assessment
11. Save Draft
12. Set WAITING_VERIFICATION
```

---

# 22. Step 1 — Generate Learning Objectives

Input

```text
Goal:
ผู้เรียนสามารถออกแบบ ER Diagram จาก Business Requirement ได้

Source:
Creator Documents
```

AI Generate เช่น

```text
Learning Objectives

1. อธิบาย Entity และ Attribute ได้
2. ระบุ Primary Key ได้
3. วิเคราะห์ Relationship ได้
4. กำหนด Cardinality ได้
5. สร้าง ER Diagram จาก Requirement ได้
```

---

# 23. Step 2 — Curriculum Generation

จาก Learning Objectives

AI สร้าง

```text
Course
│
├── Module 1: Entity and Attribute
│
├── Module 2: Primary Key
│
├── Module 3: Relationship
│
├── Module 4: Cardinality
│
└── Module 5: ER Diagram Design
```

---

# 24. Curriculum Output Format

สำคัญมาก

LLM ไม่ควรตอบเป็นข้อความ Free Text อย่างเดียว

ควรบังคับให้ตอบ Structured JSON

ตัวอย่าง

```json
{
  "title": "ER Diagram Fundamentals",
  "learning_objectives": [
    "Identify entities and attributes",
    "Define relationships",
    "Create ER diagrams"
  ],
  "modules": [
    {
      "title": "Entity and Attribute",
      "order": 1
    },
    {
      "title": "Relationship",
      "order": 2
    }
  ]
}
```

---

# 25. ทำไมต้อง Structured Output

เพราะ Backend ต้องสามารถ

```text
LLM Output
   ↓
Validate
   ↓
Pydantic Schema
   ↓
Database
```

ได้

ไม่ควร Parse Markdown จาก AI แบบเดา ๆ

---

# 26. Pydantic Schema ตัวอย่าง

Concept

```python
class GeneratedModule(BaseModel):
    title: str
    description: str
    order: int


class GeneratedCourse(BaseModel):
    title: str
    learning_objectives: list[str]
    modules: list[GeneratedModule]
```

ถ้า LLM Response ไม่ตรง Schema

Backend ต้อง

```text
Reject / Retry
```

ไม่ควร Save ข้อมูลผิดลง Database

---

# 27. Lesson Generation

หลัง Module ถูกสร้าง

ระบบ Generate Lesson ทีละ Module

ตัวอย่าง

```text
Module:
Entity and Attribute
```

AI อาจสร้าง

```text
Lesson 1: What is an Entity?
Lesson 2: Types of Entity
Lesson 3: Understanding Attributes
Lesson 4: Attribute Types
```

---

# 28. Lesson Structure

Lesson ควรมีประมาณ

```json
{
  "title": "What is an Entity?",
  "objective": "ผู้เรียนสามารถอธิบาย Entity ได้",
  "content": "...",
  "examples": [],
  "key_points": [],
  "source_references": []
}
```

---

# 29. Lesson Content Rule

AI ต้องได้รับ Instruction ว่า

```text
Use only the provided knowledge context
as the primary source.
```

ถ้าข้อมูลใน Source ไม่เพียงพอ

AI ไม่ควรสร้างเองแบบมั่ว

สามารถตอบสถานะ เช่น

```text
INSUFFICIENT_SOURCE
```

เพื่อให้ Creator เพิ่ม Document

---

# 30. Prompt หลักควรมีอะไร

Prompt ไม่ควรมีแค่

```text
สร้างบทเรียนจากข้อมูลนี้
```

ควรมี

```text
SYSTEM ROLE
TASK
COURSE GOAL
SOURCE CONTEXT
OUTPUT FORMAT
GROUNDING RULE
LANGUAGE
RESTRICTIONS
```

---

# 31. Curriculum Prompt Concept

```text
You are an AI learning designer for SkillSync.

Your task is to create a learning curriculum based primarily
on the knowledge sources provided by the creator.

Course Goal:
{course_goal}

Knowledge Context:
{retrieved_context}

Rules:
- Use the provided source as the main knowledge base.
- Do not invent unsupported facts.
- Organize content from foundational to advanced.
- Align every module with the course goal.
- Do not publish or claim verification.
- Return structured JSON only.
```

---

# 32. Lesson Prompt Concept

```text
Create a lesson for the following module.

Course Goal:
{goal}

Module:
{module}

Retrieved Source:
{context}

Create:
- lesson title
- learning objective
- explanation
- examples
- key points

Only use information grounded in the source.
```

---

# 33. Quiz Generation

Quiz ต้อง Generate จาก

```text
Lesson Content
+
Learning Objective
+
Source
```

ไม่ควร Generate แยกจาก Course Context

---

# 34. Quiz Example

```json
{
  "question": "ข้อใดคือตัวอย่าง Entity?",
  "type": "MULTIPLE_CHOICE",
  "choices": [
    {
      "id": "A",
      "text": "Customer"
    },
    {
      "id": "B",
      "text": "Green"
    }
  ],
  "correct_answer": "A",
  "explanation": "Customer สามารถเป็น Entity..."
}
```

---

# 35. Correct Answer

Backend สามารถเก็บ

```text
correct_answer
```

แต่ **ห้ามส่ง Correct Answer ให้ Frontend ก่อน Learner Submit**

Frontend GET Assessment ควรได้

```json
{
  "question": "...",
  "choices": []
}
```

แต่ไม่มี

```text
correct_answer
```

---

# 36. Assessment Generation

Final Assessment ต้องวัด Goal จริง

ตัวอย่าง

Goal

```text
สามารถออกแบบ ER Diagram ได้
```

ไม่ควร Final แค่

```text
20 Multiple Choice
```

ควรมี

```text
Practical Task
```

เช่น

> ให้ Business Requirement แล้วให้ออกแบบ ER Diagram

---

# 37. Assessment Types

รองรับในอนาคต

```text
MULTIPLE_CHOICE
SHORT_ANSWER
EXERCISE
PROJECT
PRACTICAL_TASK
```

MVP อาจเริ่ม

```text
MULTIPLE_CHOICE
+
SHORT_ANSWER
```

ก่อน

---

# 38. Creator Verification

นี่คือ Rule สำคัญที่สุด

AI Generate แล้ว

```text
status = WAITING_VERIFICATION
```

ห้าม

```text
status = PUBLISHED
```

ทันที

---

# 39. Verification Flow

```text
AI Generate
   ↓
WAITING_VERIFICATION
   ↓
Creator Review
   ↓
Creator Edit
   ↓
Creator Approve
   ↓
VERIFIED
   ↓
Publish
```

---

# 40. AI กับ Verification แยกหน้าที่กัน

AI มีสิทธิ์

```text
Generate
Suggest
Regenerate
Explain
```

AI ไม่มีสิทธิ์

```text
Verify
Publish
```

คนเดียวที่ Verify ได้คือ

```text
Creator
```

หรือ Expert ในอนาคต

---

# 41. Content Status

Generated Content อาจมี

```text
AI_GENERATED
CREATOR_EDITED
CREATOR_VERIFIED
```

อนาคต

```text
EXPERT_VERIFIED
```

---

# 42. Regenerate Feature

Creator สามารถเลือกบางส่วนแล้ว

```text
Regenerate
```

เช่น

```text
Regenerate Lesson
Regenerate Quiz
Regenerate Explanation
```

ไม่จำเป็นต้อง Generate Course ใหม่ทั้งหมด

---

# 43. Regenerate Flow

```text
Creator
   ↓
Select Lesson
   ↓
Regenerate
   ↓
Retrieve Original Source
   ↓
LLM
   ↓
New Draft
   ↓
Creator Review
```

หลัง Regenerate

Lesson ควรกลับเป็น

```text
AI_GENERATED
```

และต้อง Verify ใหม่

---

# 44. AI Tutor

หลัง Course Publish

Learner สามารถถาม AI Tutor

ตัวอย่าง

> Primary Key คืออะไร?

แต่ AI Tutor ไม่ควรตอบแบบ General Chatbot

---

# 45. AI Tutor Context

AI Tutor ใช้

```text
Course
+
Current Module
+
Current Lesson
+
Creator Documents
+
Learner Question
```

Flow

```text
Learner Question
      ↓
Retrieve Course Knowledge
      ↓
Current Lesson Context
      ↓
LLM
      ↓
Answer
```

---

# 46. AI Tutor Scope

AI Tutor ควร

* อธิบายเนื้อหาใหม่
* ยกตัวอย่าง
* สรุป
* ให้ Hint
* ช่วยทบทวน

ไม่ควร

* เปลี่ยนเนื้อหา Course
* Verify Content
* Publish
* แก้ Source
* เปิดเฉลย Assessment โดยตรง

---

# 47. AI Tutor Response

ตัวอย่าง

```json
{
  "message": "Primary Key คือ...",
  "sources": [
    {
      "document_id": 10,
      "page": 5
    }
  ]
}
```

ควรมี Source กลับไปด้วย

---

# 48. Personalization

Personalized Learning เป็น Phase หลัง MVP

Input ที่สามารถใช้

```text
Pre-Test Score
Quiz Results
Completed Lessons
Error Patterns
Learning Speed
Assessment Results
```

---

# 49. Personalized Path

ตัวอย่าง

Course เดียวกัน

```text
Learner A
Beginner
   ↓
Module 1
Module 2
Module 3
Module 4
```

Learner B

```text
Pre-Test ผ่าน Module 1
   ↓
Module 2
Module 3
Module 4
```

Learner C

```text
Module 1
Module 2
↓
คะแนนต่ำ
↓
Extra Exercise
↓
Module 3
```

---

# 50. Personalization Rule

ในช่วงแรกอย่าให้ LLM ตัดสินทุกอย่างเอง

แนะนำให้ใช้

```text
Rule-Based
+
AI Recommendation
```

ตัวอย่าง

```text
Pre-Test > 80%
→ สามารถ Skip Basic Module

Quiz < 50%
→ Add Review

Quiz 50-79%
→ Continue + Extra Practice

Quiz >= 80%
→ Continue
```

AI ช่วย Generate Resource เพิ่ม

แต่ Logic หลัก Backend ควบคุม

---

# 51. AI ไม่ควรควบคุม Business Rule

ตัวอย่าง

ไม่ควรให้ LLM ตัดสินว่า

```text
Course publish ได้ไหม
```

Backend Logic เป็นคนตัดสิน

ไม่ใช่ AI

---

# 52. Backend Business Rules

AI

```text
Generate Content
```

Backend

```text
Permission
Course Status
Verification
Publishing
Enrollment
Progress
Scoring
```

Database

```text
Persist Data
```

Frontend

```text
Display + User Interaction
```

---

# 53. AI Generation API

API

```text
POST /api/courses/{course_id}/generate
```

Backend

```text
course_service
   ↓
validate course
   ↓
validate documents
   ↓
set GENERATING
   ↓
AI pipeline
```

---

# 54. Generation Status

Frontend ไม่ควรรอ HTTP Request ยาวมาก

ควร

```text
POST Generate
   ↓
Backend Start Job
   ↓
Return GENERATING
```

Frontend Poll

```text
GET /api/courses/{id}/generation-status
```

---

# 55. Future Background Job

MVP สามารถทำง่ายก่อน

แต่ในอนาคต AI Generate อาจใช้เวลา

สามารถแยกเป็น Background Worker

เช่น Concept:

```text
FastAPI
  ↓
Job Queue
  ↓
AI Worker
  ↓
Database
```

ไม่จำเป็นต้องทำใน First Version

---

# 56. AI Job Status

แนะนำ

```text
PENDING
PROCESSING
COMPLETED
FAILED
```

เช่น

```json
{
  "job_id": "gen_001",
  "course_id": 1,
  "status": "PROCESSING",
  "progress": 60
}
```

---

# 57. AI Error Handling

AI สามารถ Fail ได้

เช่น

```text
LLM Timeout
Invalid JSON
Rate Limit
No Source
Vector Search Error
Parsing Error
```

Backend ต้อง Handle

ไม่ควร Crash ทั้ง API

---

# 58. AI Error Code

แนะนำ

```text
AI_GENERATION_FAILED
AI_TIMEOUT
AI_INVALID_OUTPUT
AI_RATE_LIMITED

DOCUMENT_PROCESSING_FAILED

NO_KNOWLEDGE_SOURCE

INSUFFICIENT_SOURCE

RETRIEVAL_FAILED
```

---

# 59. ตัวอย่าง Error

```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_SOURCE",
    "message": "The uploaded documents do not contain enough information to generate this lesson."
  }
}
```

Frontend แสดง

> เอกสารที่อัปโหลดยังมีข้อมูลไม่เพียงพอ กรุณาเพิ่ม Source

---

# 60. Retry Strategy

หาก LLM ตอบ JSON ผิด

Backend อาจ Retry

```text
Request
 ↓
LLM
 ↓
Invalid Schema
 ↓
Retry Once
 ↓
Fail
```

ไม่ควร Retry ไม่จำกัด

---

# 61. LLM Service

ไฟล์

```text
llm_service.py
```

ควรเป็น Layer กลางสำหรับติดต่อ LLM Provider

Service อื่นไม่ควรเรียก Provider โดยตรงทุกที่

---

# 62. LLM Abstraction

แทนที่จะเขียน

```text
OpenAI call
```

ในทุก Service

ให้เป็น

```text
Curriculum Service
      ↓
LLM Service
      ↓
Provider
```

ทำให้ในอนาคตเปลี่ยน Model ได้ง่าย

---

# 63. Environment Variables

ตัวอย่าง

```env
LLM_API_KEY=
LLM_MODEL=

EMBEDDING_MODEL=

DATABASE_URL=

VECTOR_SEARCH_LIMIT=5
```

ห้าม Commit

```text
API KEY
```

ลง GitHub

---

# 64. Prompt Files

Prompt ควรแยกออกจาก Business Logic

```text
prompts/
├── curriculum_prompt.py
├── lesson_prompt.py
├── quiz_prompt.py
├── assessment_prompt.py
└── tutor_prompt.py
```

ข้อดี

* แก้ Prompt ง่าย
* Version ง่าย
* Test ง่าย
* Backend ไม่รก

---

# 65. Prompt Versioning

ในอนาคตแนะนำเก็บ

```text
prompt_version
```

เช่น

```text
curriculum_v1
lesson_v2
```

เพราะ Prompt เปลี่ยนแล้ว Output อาจเปลี่ยน

---

# 66. AI Generated Metadata

Generated Content ควรเก็บ Metadata เช่น

```json
{
  "generated_by": "AI",
  "model": "MODEL_NAME",
  "prompt_version": "lesson_v1",
  "generated_at": "...",
  "verified": false
}
```

ไม่จำเป็นต้องส่งทุกอย่างให้ Frontend

แต่ช่วย Debug

---

# 67. Generated Content Database

ตัวอย่าง Lesson

```text
lessons
-------
id
module_id
title
content
order
generation_status
verified
created_at
updated_at
```

Source relation อาจแยกตาราง

```text
lesson_sources
--------------
lesson_id
document_chunk_id
```

---

# 68. ทำไมควรเก็บ Source Relation

เพราะสามารถทำ

```text
Lesson
   ↓
View Source
   ↓
Database Lecture.pdf
Page 4
```

ให้ Creator ตรวจสอบได้ง่าย

นี่เป็น Feature สำคัญของ

**Human Verification**

---

# 69. Source-Grounded Score

ในอนาคตอาจเพิ่ม

```text
grounding_score
```

เพื่อบอกว่าบทเรียนมี Source รองรับมากน้อยแค่ไหน

แต่ **ไม่จำเป็นสำหรับ MVP**

---

# 70. Security ของ Knowledge Documents

เอกสาร Creator อาจเป็น

* Note ส่วนตัว
* เอกสารภายในบริษัท
* Training Manual
* Company SOP

ดังนั้น AI Retrieval ต้องแยก Scope

---

# 71. Retrieval Scope

ห้าม Vector Search ข้าม Course แบบไม่ตั้งใจ

เช่น User ถามใน Course A

ต้องค้นเฉพาะ

```text
course_id = A
```

ไม่ใช่ค้นทั้ง Database

---

# 72. Multi-Tenant Future

เมื่อมีองค์กร

ต้อง Scope ด้วย

```text
organization_id
```

ประมาณ

```text
Organization
   ↓
Workspace
   ↓
Course
   ↓
Documents
```

เพื่อไม่ให้ข้อมูลบริษัท A หลุดไปบริษัท B

---

# 73. AI Logging

ควร Log อย่างน้อย

```text
AI task
Course ID
Model
Duration
Success / Failed
Error
```

หลีกเลี่ยงการ Log

```text
API Key
Password
Sensitive Document Content
```

โดยไม่จำเป็น

---

# 74. AI Usage Tracking

ในอนาคตถ้าต้องคุม Cost

ควรเก็บ

```text
input_tokens
output_tokens
model
feature
user_id
course_id
```

ทำให้รู้ว่า Feature ไหนใช้ AI Cost มาก

---

# 75. AI Cost Optimization

ในอนาคตสามารถลด Cost ด้วย

### 1. Cache

ไม่ Generate ซ้ำถ้า Source ไม่เปลี่ยน

### 2. Generate ทีละส่วน

ไม่ส่ง Course ทั้งหมดทุก Request

### 3. Small Model

ใช้ Task ง่ายกับ Model เล็ก

### 4. Retrieval

ส่งเฉพาะ Context ที่เกี่ยวข้อง

แทนส่งเอกสารทั้งเล่ม

---

# 76. Cache Concept

ตัวอย่าง

Creator กดเปิด Lesson

ไม่ต้อง Generate ใหม่ทุกครั้ง

Content ต้องถูก

```text
Generate
↓
Save Database
↓
Read from Database
```

AI ใช้ตอน

```text
Generate / Regenerate / Tutor
```

เท่านั้น

---

# 77. AI Testing

AI Test มีหลาย Layer

---

## Unit Test

Test

```text
Chunking
Schema Validation
Retrieval
Status Logic
```

---

## Mock LLM Test

ไม่ควรเรียก LLM จริงทุก Test

ใช้ Mock Response

เช่น

```json
{
  "modules": [
    {
      "title": "Entity"
    }
  ]
}
```

แล้ว Test Backend Logic

---

# 78. Integration Test

Flow

```text
Upload Document
↓
Process
↓
Retrieve
↓
Generate
↓
Save
```

---

# 79. Quality Test

ทีมควรมี Test Documents ชุดเดิม

เช่น

```text
database_test.pdf
```

แล้วดูว่า AI Generate

```text
Entity
Attribute
Relationship
Cardinality
```

ครบไหม

---

# 80. Hallucination Test

สร้างคำถามที่ไม่มีใน Source

เช่น Source ไม่มีเรื่อง

```text
Normalization
```

แต่ถาม AI

> สร้าง Lesson 3NF

AI ควร

```text
ไม่ Generate แบบมั่ว
```

แต่แจ้งว่า

```text
Source ไม่เพียงพอ
```

---

# 81. MVP AI Scope

MVP รอบแรกแนะนำทำแค่

```text
1. Upload PDF
2. Extract Text
3. Chunk
4. Embedding
5. Vector Search
6. Generate Course Structure
7. Generate Lessons
8. Generate Quiz
9. Creator Verify
```

ยังไม่ต้องรีบทำ

```text
Adaptive Learning
AI Tutor
Automatic Project Grading
Complex Agent
Multi-Agent
```

---

# 82. MVP Development Order

## Phase 1 — Document

```text
Upload
↓
Parse
↓
Chunk
↓
Store
```

---

## Phase 2 — RAG

```text
Embedding
↓
Vector DB
↓
Retrieve
```

---

## Phase 3 — Generation

```text
Goal
+
Retrieved Source
↓
Curriculum
↓
Lesson
↓
Quiz
```

---

## Phase 4 — Verification

```text
Draft
↓
Creator Edit
↓
Verify
↓
Publish
```

---

## Phase 5 — AI Tutor

หลัง Core Flow เสถียร

---

## Phase 6 — Personalization

หลังมีข้อมูล Learner จริง

---

# 83. ตัวอย่าง End-to-End AI Flow

Creator สร้าง Course

```text
Title:
ER Diagram

Goal:
ผู้เรียนสามารถออกแบบ ER Diagram ได้
```

Upload

```text
database.pdf
```

↓

Backend

```text
Extract
```

↓

ได้

```text
Entity
Attribute
Relationship
Cardinality
```

↓

Chunk

↓

Embedding

↓

Vector DB

↓

Creator กด Generate

↓

AI Retrieve Source

↓

Generate

```text
Module 1
Entity & Attribute

Module 2
Relationship

Module 3
Cardinality

Module 4
ER Diagram Design
```

↓

Generate Lessons

↓

Generate Quiz

↓

Save

↓

```text
WAITING_VERIFICATION
```

↓

Creator ตรวจ

↓

Edit

↓

Verify

↓

```text
VERIFIED
```

↓

Publish

↓

Learner

---

# 84. Example AI Service Flow

```text
POST /courses/1/generate
          ↓
course_service.generate_course()
          ↓
knowledge_service.get_course_knowledge()
          ↓
retrieval_service.retrieve()
          ↓
curriculum_service.generate()
          ↓
llm_service.generate_structured()
          ↓
Pydantic Validation
          ↓
Database
```

---

# 85. Lesson Generation Flow

```text
Module
+
Course Goal
+
Relevant Chunks
      ↓
lesson_service
      ↓
LLM
      ↓
Structured Lesson
      ↓
Validate
      ↓
Save
```

---

# 86. Assessment Flow

```text
Learning Objective
+
Lesson Content
+
Source
      ↓
assessment_service
      ↓
Generate Questions
      ↓
Validate
      ↓
Creator Review
```

Assessment AI-generated จึงต้องอยู่ใน Verification เช่นเดียวกับ Lesson

---

# 87. สิ่งที่ Frontend ต้องรู้เกี่ยวกับ AI

Frontend **ไม่เรียก LLM โดยตรง**

ห้าม

```text
Frontend
↓
LLM API
```

ต้องเป็น

```text
Frontend
↓
FastAPI
↓
AI Service
↓
LLM
```

เพราะ API Key ต้องอยู่ Backend

---

# 88. Frontend AI Flow

Frontend แค่

```text
Upload
Generate
Show Loading
Show Draft
Edit
Verify
```

ไม่ต้องรู้

* Prompt
* Embedding
* Chunk
* RAG
* API Key
* Vector DB

---

# 89. API ที่ Front ใช้กับ AI

หลัก ๆ

```text
POST /api/courses/{id}/documents

POST /api/courses/{id}/generate

GET /api/courses/{id}/generation-status

GET /api/courses/{id}/modules

PUT /api/lessons/{id}

POST /api/courses/{id}/verify
```

อนาคต

```text
POST /api/lessons/{id}/regenerate

POST /api/courses/{id}/ai-tutor
```

---

# 90. AI Rules ที่ทีมต้องจำ

## Rule 1

AI ต้องใช้ Creator Documents เป็น Source หลัก

---

## Rule 2

AI Generated Content ห้าม Publish อัตโนมัติ

---

## Rule 3

Creator ต้อง Verify ก่อน

---

## Rule 4

Generated Content ควรสามารถ Trace กลับไป Source ได้

---

## Rule 5

Backend ต้อง Validate Output จาก LLM

---

## Rule 6

Frontend ห้ามเรียก LLM Provider โดยตรง

---

## Rule 7

Business Logic สำคัญต้องอยู่ Backend ไม่ใช่ AI

---

## Rule 8

ถ้า Source ไม่พอ ให้แจ้งว่าไม่พอ แทนการเดา

---

# 91. Core AI Architecture Summary

```text
Creator
  │
  ├── Goal
  │
  └── Documents
          ↓
   Document Processing
          ↓
      Knowledge Base
          ↓
         RAG
          ↓
         LLM
          ↓
   Structured Output
          ↓
      Validation
          ↓
      Save Draft
          ↓
   Creator Verification
          ↓
        Publish
          ↓
        Learner
```

---

# 92. สรุปหน้าที่แต่ละส่วน

## Document Processing

```text
เอกสาร → Text
```

## Chunking

```text
Text → Knowledge Pieces
```

## Embedding

```text
Knowledge → Vector
```

## Vector DB

```text
เก็บและค้น Knowledge
```

## RAG

```text
หา Source ที่เกี่ยวข้อง
```

## LLM

```text
จัดความรู้เป็น Learning Content
```

## Pydantic

```text
ตรวจ Output
```

## Database

```text
เก็บ Course / Lesson / Assessment
```

## Creator

```text
Verify
```

## Learner

```text
Learn
```

---

# 93. Core Principle ของ AI ใน SkillSync

SkillSync ไม่ได้ออกแบบมาเพื่อให้

> **AI เป็นผู้เชี่ยวชาญที่สร้างความรู้แทนมนุษย์**

แต่ให้ AI เป็น

> **เครื่องมือที่ช่วยเปลี่ยนความรู้ของมนุษย์ ให้กลายเป็น Learning Experience ที่มีโครงสร้าง**

ดังนั้น Flow ที่สำคัญที่สุดคือ

# **Creator Uploads Knowledge**

↓

# **AI Builds Learning**

↓

# **Creator Verifies**

↓

# **Learner Learns**

---

# 94. Short Summary สำหรับทีม

```text
Creator Upload PDF
        ↓
Backend Extract Text
        ↓
Chunk
        ↓
Embedding
        ↓
Vector DB
        ↓
RAG ดึงข้อมูลที่เกี่ยวข้อง
        ↓
LLM สร้าง Module / Lesson / Quiz
        ↓
Backend Validate
        ↓
Save เป็น Draft
        ↓
Creator ตรวจ
        ↓
Verify
        ↓
Publish
```

## ประโยคที่ทีมต้องจำ

> **AI ช่วยสร้าง แต่ Source มาจาก Creator และ Creator ต้องเป็นคน Verify ก่อนทุกครั้ง**

# **Upload Knowledge. AI Builds. You Verify. They Learn.**
