# Function 9: Mock Creator Dashboard

เอกสารนี้อธิบาย Function 9 ตาม `JUMP_DAI1.pdf` หัวข้อ **9.8 Creator
Dashboard** สำหรับ Creator ดูข้อมูลการเรียนของ Course ที่ตนเองเป็นเจ้าของเท่านั้น

## ขอบเขตที่ทำแล้ว

| Requirement | สิ่งที่ API ส่งกลับ |
| --- | --- |
| FR-CD-001 Learner Count | จำนวนผู้เรียนใน `summary` และแยกตาม `courses` |
| FR-CD-002 Learner Progress | `learners[].progress_percentage` และสถานะจบ |
| FR-CD-003 Completion Rate | `completion_rate` รวมและราย Course |
| FR-CD-004 Assessment Score | `assessment_score` รายผู้เรียนและค่าเฉลี่ย |
| FR-CD-005 Common Error Analysis | `common_errors` พร้อมจำนวนครั้งและผู้เรียนที่ได้รับผลกระทบ |
| FR-CD-006 Skill Gap Overview | `skill_gaps` พร้อมจำนวนผู้เรียนที่ต้องการความช่วยเหลือ |
| FR-CD-007 Course Improvement Insight | `course_improvement_insights` พร้อม recommendation |
| FR-CD-008 Report Filtering | query `course_id`, `date_from`, `date_to` |
| FR-CD-009 / RR-EXP-003 Export Report | export `csv`, `json` และ `pdf` |

## ข้อจำกัดของ Mock

ระบบปัจจุบันยังไม่มี Function enrollment, learning progress และ assessment จริง จึงสร้าง
ข้อมูลผู้เรียนตัวอย่าง 3 คนแบบคงที่ให้ **เฉพาะ Course ที่ Creator สร้าง** เมื่อเรียก
Dashboard หรือ export report ครั้งแรก ข้อมูลนั้นอยู่ใน memory และหายเมื่อ server restart

เมื่อทำ Function การเรียนและ Assessment จริง ให้เปลี่ยน `dashboard_service.py` ไปอ่าน
ข้อมูลจริงแทน mock snapshot โดย API contract นี้ยังคงใช้ต่อได้

## สิทธิ์

ทุก endpoint ต้องส่ง Bearer token ของ role `CREATOR` และข้อมูลที่ตอบกลับจะจำกัดเฉพาะ
Course ที่เป็นของ Creator ผู้นั้นเท่านั้น หากระบุ `course_id` ที่ไม่มีหรือไม่ใช่เจ้าของ
จะได้ `404 COURSE_NOT_FOUND`

บัญชีทดสอบ:

```text
email: creator@skillsync.local
password: password123
```

## 1. ดู Dashboard

`GET /api/creator/dashboard`

Query ที่รองรับทั้งหมดเป็น optional:

| Query | ตัวอย่าง | ความหมาย |
| --- | --- | --- |
| `course_id` | `1` | ดูเฉพาะ Course ที่เป็นเจ้าของ |
| `date_from` | `2026-08-01` | รวม activity ตั้งแต่วันนั้น (YYYY-MM-DD) |
| `date_to` | `2026-08-31` | รวม activity ถึงวันนั้น (YYYY-MM-DD) |

ตัวอย่าง:

```http
GET /api/creator/dashboard?course_id=1&date_from=2026-08-01&date_to=2026-08-31
Authorization: Bearer <access_token>
```

ตัวอย่าง response:

```json
{
  "success": true,
  "data": {
    "filters": {
      "course_id": 1,
      "date_from": "2026-08-01",
      "date_to": "2026-08-31"
    },
    "summary": {
      "course_count": 1,
      "learner_count": 3,
      "completed_learner_count": 1,
      "completion_rate": 33.33,
      "average_assessment_score": 63.67
    },
    "courses": [{"course_id": 1, "course_title": "Database Fundamentals", "learner_count": 3, "completed_learner_count": 1, "completion_rate": 33.33, "average_assessment_score": 63.67}],
    "learners": [{"learner_id": 1001, "learner_name": "Aom Learner", "course_id": 1, "course_title": "Database Fundamentals", "progress_percentage": 92, "assessment_score": 88, "completed": true, "last_activity_at": "2026-08-17T10:00:00+00:00", "common_errors": ["Foreign key relationships"], "skill_gaps": []}],
    "common_errors": [{"course_id": 1, "course_title": "Database Fundamentals", "topic": "JOIN conditions", "occurrence_count": 2, "affected_learner_count": 2}],
    "skill_gaps": [{"course_id": 1, "course_title": "Database Fundamentals", "skill": "Database normalization", "affected_learner_count": 2}],
    "course_improvement_insights": [{"course_id": 1, "course_title": "Database Fundamentals", "code": "LOW_COMPLETION_RATE", "severity": "HIGH", "message": "Completion rate is 33.33%.", "recommendation": "Review lesson pacing and add checkpoints before difficult sections."}]
  }
}
```

ใน response จริง `courses` จะเป็น metrics ราย Course, `learners` เป็น progress/score
รายผู้เรียน, `common_errors` และ `skill_gaps` เป็นข้อมูล aggregate ส่วน insight จะสร้าง
จาก completion rate, average score, หัวข้อที่ผิดบ่อย และ skill gap ที่พบ

## 2. Load Dashboard Sections Independently

`GET /api/creator/dashboard` ยังคงเป็น endpoint รวมสำหรับโหลด Summary และข้อมูล Dashboard
ครั้งแรก แต่ Frontend สามารถโหลดแต่ละส่วนแยกกันได้ เพื่อไม่ให้ส่วนข้อมูลขนาดใหญ่หรือ
ส่วนที่มีปัญหาชั่วคราวทำให้หน้า Dashboard ทั้งหมดใช้งานไม่ได้

| Endpoint | ข้อมูล | Query เพิ่มเติม |
| --- | --- | --- |
| `GET /api/creator/dashboard/learners` | Progress, completion และ assessment score รายผู้เรียน | `search`, `page`, `page_size` |
| `GET /api/creator/dashboard/errors` | Common Error Analysis | - |
| `GET /api/creator/dashboard/skill-gaps` | Skill Gap Overview | - |
| `GET /api/creator/dashboard/insights` | Course Improvement Insight | - |

ทุก endpoint รองรับ `course_id`, `date_from`, `date_to` เหมือน endpoint รวม และต้อง
ผ่านสิทธิ์ Creator/ownership เช่นเดียวกัน `learners` ใช้ `page=1` และ `page_size=20`
เป็นค่าเริ่มต้น โดย `page_size` รับได้สูงสุด 100

ตัวอย่าง:

```http
GET /api/creator/dashboard/learners?course_id=1&search=beam&page=1&page_size=20
Authorization: Bearer <access_token>
```

## 3. Export Report

`GET /api/creator/dashboard/export`

ใช้ query filter เดียวกับ Dashboard และเพิ่ม `format`:

```http
GET /api/creator/dashboard/export?course_id=1&format=csv
Authorization: Bearer <access_token>
```

| `format` | Content-Type | เนื้อหา |
| --- | --- | --- |
| `csv` (ค่าเริ่มต้น) | `text/csv` | แถวข้อมูล progress/score/errors/skill gaps รายผู้เรียน |
| `json` | `application/json` | Dashboard report ทั้งก้อน |
| `pdf` | `application/pdf` | รายงาน Dashboard ที่จัดหน้าเพื่อดาวน์โหลด |

ทั้งสามแบบตอบ `Content-Disposition: attachment` เพื่อให้ Frontend ดาวน์โหลดไฟล์ได้

## HTTP Status Code

| Status | เกิดขึ้นเมื่อ | Error code |
| --- | --- | --- |
| `200 OK` | ดู Dashboard หรือ export report สำเร็จ | - |
| `400 Bad Request` | `date_from` อยู่หลัง `date_to` | `INVALID_DATE_RANGE` |
| `401 Unauthorized` | ไม่ส่ง token หรือ token ไม่ถูกต้อง | `UNAUTHORIZED` |
| `403 Forbidden` | ผู้เรียกไม่ใช่ Creator | `FORBIDDEN` |
| `404 Not Found` | ไม่พบ Course หรือ Course ไม่ใช่ของ Creator | `COURSE_NOT_FOUND` |
| `422 Unprocessable Entity` | query date, `course_id` หรือ `format` ไม่ผ่าน validation | `VALIDATION_ERROR` |

## ทดสอบผ่าน Swagger

1. เรียก `POST /api/auth/login` ด้วยบัญชี Creator แล้วคัดลอก `data.access_token`
2. กด **Authorize** และวาง token
3. เรียก `POST /api/courses` แล้วจำ `data.id` เป็น `course_id`
4. เรียก `GET /api/creator/dashboard?course_id=<course_id>`
5. ลอง filter วันที่ หรือเรียก `/api/creator/dashboard/export?course_id=<course_id>&format=csv`

## Automated Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_dashboard.py -q
```
