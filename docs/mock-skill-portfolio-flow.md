# Function 9.7: Mock Skill Evidence / Portfolio

เอกสารนี้อธิบาย Function 9.7 สำหรับผู้เรียนบันทึกหลักฐานจาก Practical Assessment,
สร้าง Skill Portfolio และตรวจสอบ credential แบบ mock โดยข้อมูลอยู่ใน memory ของ
FastAPI และจะหายเมื่อ server restart หรือ reload

## ขอบเขตที่ทำแล้ว

| Requirement | การทำงานของ API |
| --- | --- |
| FR-SEP-001 Practical Evidence | บันทึกหลักฐานและคะแนนผ่าน `POST /api/skill-evidence` |
| FR-SEP-002 Verified Skill | Skill จะปรากฏใน Portfolio เมื่อ `score >= passing_score` |
| FR-SEP-003 Competency Score | ส่งคะแนนและ `competency_level` กลับใน Evidence/Portfolio |
| FR-SEP-004 Skill Portfolio | `GET /api/skill-portfolio` สร้าง Portfolio จาก Skill ที่ผ่านเกณฑ์ |
| FR-SEP-005 Portfolio Evidence | Portfolio ผูก Skill กับ evidence URL และ Practical Assessment ที่ใช้พิสูจน์ |
| FR-SEP-006 Portfolio Sharing | `POST /api/skill-portfolio/share` สร้าง public share link |
| FR-SEP-007 Digital Badge | ออก Digital Badge หนึ่งรายการต่อ Skill ที่ผ่านเกณฑ์ |
| FR-SEP-008 Certificate | ออก Certificate เมื่อ Final Assessment ของ Course ผ่านเกณฑ์ |
| FR-SEP-009 Credential Verification | ตรวจ Certificate/Badge ผ่าน public verification endpoint |

## กติกา Mock

- ทุก endpoint ที่สร้างหรือดู Portfolio ส่วนตัวต้องใช้ Bearer token ของ role `LEARNER`
- เนื่องจากยังไม่มี Function enrollment และ assessment จริง Request จึงส่ง Course และ
  Assessment metadata มาพร้อม Evidence ชั่วคราว
- คะแนนผ่านคือ `passing_score` ของ Evidence (ค่าเริ่มต้น `70`)
- Competency: `FOUNDATION` 0-49, `DEVELOPING` 50-69, `PROFICIENT` 70-84 และ
  `ADVANCED` 85-100
- Evidence ที่ผ่านเกณฑ์จะออก Digital Badge หากยังไม่มี Badge ของ Skill นั้น
- Evidence ที่ผ่านเกณฑ์และตั้ง `is_course_final_assessment: true` จะออก Certificate
  หากยังไม่มี Certificate ของ Course นั้น

## Demo account

```text
email: demo@skillsync.local
password: password123
```

Login ด้วย `POST /api/auth/login` แล้วใช้ `data.access_token` ใน Swagger Authorize
ก่อนเรียก private endpoint

## 1. Submit Practical Evidence

`POST /api/skill-evidence`

```json
{
  "course_id": 10,
  "course_title": "Database Fundamentals",
  "assessment_id": "practical-sql-1",
  "assessment_title": "Practical SQL Project",
  "skill": "SQL joins",
  "score": 88,
  "passing_score": 70,
  "evidence_title": "Customer reporting query",
  "evidence_url": "https://portfolio.example/sql-joins",
  "is_course_final_assessment": true
}
```

เมื่อ Evidence ผ่านเกณฑ์ response จะมี `verified_skill` และอาจมี `issued_badge` กับ
`issued_certificate` หากเข้าเงื่อนไข

## 2. View Portfolio

`GET /api/skill-portfolio`

response มี `skills[]` ที่เก็บ `competency_score`, `competency_level` และ `evidence[]`
ที่เชื่อมกับ assessment/evidence URL รวมถึง `credentials[]` ของผู้เรียน

## 3. Share Portfolio

`POST /api/skill-portfolio/share`

response คืน `share_url` เช่น:

```text
http://127.0.0.1:8000/api/skill-portfolio/shared/<share_token>
```

ผู้รับลิงก์เรียก `GET /api/skill-portfolio/shared/{share_token}` ได้โดยไม่ต้อง login

## 4. Verify Credential

`GET /api/credentials/{credential_id}/verify`

เป็น public endpoint และตอบชนิด credential, ผู้เรียน, Skill/Course, วันที่ออก และ
สถานะ `VALID` หรือ `REVOKED` (mock ปัจจุบันออกเฉพาะ `VALID`)

## HTTP Status Code

| Status | กรณี | Error code |
| --- | --- | --- |
| `201 Created` | บันทึก Evidence สำเร็จ | - |
| `200 OK` | ดู Portfolio, share หรือ verify credential สำเร็จ | - |
| `401 Unauthorized` | ไม่ส่งหรือส่ง Bearer token ไม่ถูกต้อง | `UNAUTHORIZED` |
| `403 Forbidden` | ผู้เรียกไม่ใช่ Learner | `FORBIDDEN` |
| `404 Not Found` | share link หรือ credential ไม่พบ | `PORTFOLIO_SHARE_NOT_FOUND`, `CREDENTIAL_NOT_FOUND` |
| `422 Unprocessable Entity` | body ไม่ครบ, score นอกช่วง หรือ URL ไม่ถูกต้อง | `VALIDATION_ERROR` |

## Automated Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_skill_portfolio.py -q
```
