# Function 3: Mock Knowledge Processing

Function 3 แปลง Knowledge Source ที่ Creator อัปโหลดใน Function 2 ให้เป็น text chunks
สำหรับ retrieval แบบ source-grounded ก่อนต่อ RAG, embeddings และ LLM ใน phase ถัดไป

## ขอบเขตที่ทำแล้ว

- Process ไฟล์ `.txt`, `.md` และ PDF ที่มี selectable text ใน Course ของ Creator
- เปลี่ยนสถานะ Source: `UPLOADED → PROCESSING → READY`
- แบ่ง text เป็น chunks ไม่เกิน 800 characters พร้อม overlap 120 characters
- แสดง chunks และ metadata สำหรับตรวจ source reference
- ค้น chunks ใน Course เดียวกันด้วย keyword score แบบ deterministic
- เปลี่ยน Source เป็น `FAILED` พร้อมเหตุผลหาก process ไม่สำเร็จ

## ข้อจำกัดของ Mock

- เก็บ text chunks ใน memory; restart/reload server แล้วข้อมูลหาย
- ยังไม่รองรับ parser สำหรับ DOC/DOCX และ PPT/PPTX
- PDF แบบสแกนเป็นรูปภาพจะต้องผ่าน OCR ใน phase ถัดไป
- URL source จะยังไม่ fetch เนื้อหาจาก internet
- ยังไม่มี embeddings, vector database, background worker, LLM หรือ course generation

## สิทธิ์

ทุก endpoint ต้องส่ง Bearer token ของ Creator ที่เป็นเจ้าของ Course และ Source นั้น

ล็อกอินด้วยบัญชี mock:

```json
POST /api/auth/login

{
  "email": "creator@skillsync.local",
  "password": "password123"
}
```

วาง `data.access_token` ในปุ่ม **Authorize** ของ Swagger ที่
`http://127.0.0.1:8000/docs`

## Flow

```text
Create Course
        ↓
Upload .txt / .md / .pdf source (UPLOADED)
        ↓
POST /knowledge-sources/{source_id}/process
        ↓
READY + text chunks
        ↓
Inspect chunks or search course knowledge
```

## 1. Upload a Text Source

สร้าง Course และ upload ไฟล์ `.txt`, `.md` หรือ PDF ที่เลือกข้อความได้ ตามคู่มือ
[`mock-knowledge-upload-flow.md`](mock-knowledge-upload-flow.md) จากนั้นนำ `data.id`
ของ source มาใช้ในขั้นถัดไป

## 2. Process a Source

`POST /api/knowledge-sources/{source_id}/process`

ไม่ต้องส่ง body

ตัวอย่าง response:

```json
{
  "success": true,
  "data": {
    "source": {
      "id": 1,
      "filename": "database-notes.md",
      "status": "READY",
      "chunk_count": 2,
      "processing_error": null
    },
    "chunks_created": 2
  }
}
```

ถ้าเป็น DOCX, PPTX, URL source หรือ PDF ที่ไม่มีข้อความให้ extract ระบบตอบ `422` และ
ตั้ง source status เป็น `FAILED`; Creator ตรวจรายละเอียดได้จาก
`GET /api/courses/{course_id}/knowledge-sources`

## 3. Inspect Chunks

`GET /api/knowledge-sources/{source_id}/chunks`

แต่ละ chunk มี `source_filename`, `chunk_index`, `content`, `start_char` และ
`end_char` เพื่อใช้เป็น citation ใน Function 4: AI Course Generation

## 4. Search Indexed Knowledge

`GET /api/courses/{course_id}/knowledge-search?query=primary%20key&limit=3`

ระบบคืนเฉพาะ chunks ที่มี query terms และเรียงจาก `score` สูงไปต่ำ

```json
{
  "success": true,
  "data": [
    {
      "id": "source-1-chunk-1",
      "source_id": 1,
      "source_filename": "database-notes.md",
      "chunk_index": 1,
      "content": "A primary key uniquely identifies each row.",
      "score": 1.0
    }
  ]
}
```

`score` เป็น keyword coverage สำหรับ mock เท่านั้น ไม่ใช่ semantic similarity score

## Test

```bash
cd skillsync-server
.venv/bin/python -m pytest tests/test_knowledge_processing.py -q
```

Tests ครอบคลุม status transition, chunking, retrieval, ownership และกรณี source ที่
ยังไม่รองรับ
