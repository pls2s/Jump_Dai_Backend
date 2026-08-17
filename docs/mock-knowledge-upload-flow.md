# Function 2: Mock Knowledge Upload

เอกสารนี้อธิบาย Function 2 ตาม `JUMP_DAI.pdf`: **Knowledge Upload** สำหรับ
Creator ตั้งค่าคอร์สและเพิ่ม Knowledge Source ก่อนนำไปใช้ใน AI Knowledge
Processing และ AI Course Generator

## ขอบเขตที่ทำแล้ว

- ข้อมูลคอร์ส: ชื่อ, คำอธิบาย, Learning Objective, ระดับความยาก และการเปิดใช้
  Certificate รวมถึง Target Learner
- Upload ไฟล์: PDF, Word, PowerPoint, TXT และ Markdown
- เพิ่มแหล่งความรู้แบบ Manual Content
- เพิ่มแหล่งความรู้จาก URL แบบ HTTP/HTTPS
- ดูรายการไฟล์ หรือรายการ Knowledge Source ทั้งหมด
- ลบ Knowledge Source

## ข้อจำกัดของ Mock

- ข้อมูลและเนื้อหาไฟล์อยู่ใน memory ของ FastAPI เท่านั้น; restart หรือ reload
  server แล้วข้อมูลจะหาย
- URL จะถูกตรวจรูปแบบและเก็บเป็น reference เท่านั้น ยังไม่มีการดึงเนื้อหา URL
- ไฟล์ยังไม่ถูก extract text, chunk, embed หรือบันทึกลง database/object storage
- ไฟล์ที่รับได้มีขนาดไม่เกิน 10 MB

## เริ่ม Server

```powershell
cd D:\hackathon\Jump_Dai_Backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

เปิด Swagger UI ที่ `http://127.0.0.1:8000/docs`

## สิทธิ์ที่ต้องใช้

ทุก endpoint ของ Function 2 ต้องส่ง Bearer token ของผู้ใช้ role `CREATOR`
และ Creator ต้องเป็นเจ้าของ Course นั้น

บัญชีทดลอง:

```text
email: creator@skillsync.local
password: password123
```

เรียก `POST /api/auth/login` แล้วคัดลอก `data.access_token` ไปกด **Authorize**
ใน Swagger (วางเฉพาะค่า token)

## Flow การใช้งาน

```text
Login as Creator
        ↓
Initialize Function 2 course configuration
        ↓
Add file / manual content / URL knowledge source
        ↓
Review knowledge sources
        ↓
Delete an unwanted source (before AI generation)
```

## 1. ตั้งค่า Course สำหรับ Knowledge Source

`POST /api/courses`

```json
{
  "title": "Database Fundamentals",
  "description": "คอร์สพื้นฐานการออกแบบฐานข้อมูล",
  "target_learner": "ผู้เริ่มต้นเรียนรู้การออกแบบฐานข้อมูล",
  "difficulty_level": "BEGINNER",
  "certification_enabled": true,
  "learning_objective": "ออกแบบ relational database เบื้องต้นได้"
}
```

ค่า `difficulty_level` ที่รองรับคือ `BEGINNER`, `INTERMEDIATE`, `ADVANCED`
และคอร์สใหม่จะมีสถานะ `DRAFT` เสมอ ใช้ค่า `data.id` ที่ตอบกลับเป็น `course_id`
ใน endpoint ถัดไป Endpoint นี้มีไว้ตั้งค่าและผูก Knowledge Source ของ Function 2
เท่านั้น จึงยังไม่มี API สำหรับ list, update หรือ delete course

## 2. Upload File

`POST /api/courses/{course_id}/documents`

ใช้ `multipart/form-data` โดยมี field ชื่อ `file`

| รองรับ | ไม่รองรับ |
| --- | --- |
| `.pdf`, `.doc`, `.docx` | เช่น `.exe`, `.zip` |
| `.ppt`, `.pptx` | |
| `.txt`, `.md` | |

ตัวอย่าง response:

```json
{
  "success": true,
  "data": {
    "id": 1,
    "course_id": 1,
    "filename": "database-lecture.pdf",
    "file_type": "pdf",
    "size": 2048,
    "source_type": "FILE",
    "status": "UPLOADED"
  }
}
```

## 3. เพิ่ม Manual Content

`POST /api/courses/{course_id}/knowledge-sources/manual`

```json
{
  "title": "Normalization Notes",
  "content": "1NF, 2NF และ 3NF คือหลักการจัดรูปแบบข้อมูล"
}
```

## 4. เพิ่ม URL Source

`POST /api/courses/{course_id}/knowledge-sources/url`

```json
{
  "title": "Database Reference",
  "url": "https://example.com/database-guide"
}
```

URL ต้องเป็น HTTP หรือ HTTPS ที่สมบูรณ์

## 5. ดูและลบ Source

| Endpoint | ผลลัพธ์ |
| --- | --- |
| `GET /api/courses/{course_id}/documents` | แสดงเฉพาะไฟล์ที่ upload |
| `GET /api/courses/{course_id}/knowledge-sources` | แสดง FILE, MANUAL และ URL ทั้งหมด |
| `DELETE /api/documents/{document_id}` | ลบ Knowledge Source แล้วตอบ `{"success": true}` |

## HTTP Status Code

| Status | เกิดขึ้นเมื่อ | Error code ที่ตอบกลับ |
| --- | --- | --- |
| `201 Created` | สร้าง Course configuration หรือเพิ่ม Knowledge Source สำเร็จ | - |
| `200 OK` | ดูรายการ หรือลบ Source สำเร็จ | - |
| `400 Bad Request` | นามสกุลไฟล์ไม่รองรับ หรือไฟล์ว่าง | `UNSUPPORTED_FILE_TYPE`, `EMPTY_FILE` |
| `401 Unauthorized` | ไม่ส่ง token หรือ token ใช้ไม่ได้ | `UNAUTHORIZED` |
| `403 Forbidden` | ผู้ใช้ไม่ใช่ Creator | `FORBIDDEN` |
| `404 Not Found` | ไม่พบ Course, Document หรือไม่ได้เป็นเจ้าของ Course | `COURSE_NOT_FOUND`, `DOCUMENT_NOT_FOUND` |
| `413 Payload Too Large` | ไฟล์ใหญ่เกิน 10 MB | `FILE_TOO_LARGE` |
| `422 Unprocessable Entity` | body ไม่ครบ, URL ไม่ถูกต้อง หรือค่า field ไม่ผ่าน validation | `VALIDATION_ERROR` |
| `405 Method Not Allowed` | เรียก `GET /api/courses` ซึ่งเป็น course list ที่อยู่นอก Function 2 | - |

รูปแบบ error ทุกกรณี:

```json
{
  "success": false,
  "error": {
    "code": "UNSUPPORTED_FILE_TYPE",
    "message": "Upload a PDF, document, slide, or text file"
  }
}
```

## Automated Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_documents.py -q
```

การทดสอบครอบคลุม file upload, manual content, URL source, list, delete และ
HTTP status/error code หลักของ Function 2
