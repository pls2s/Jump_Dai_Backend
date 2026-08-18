# Mock Authentication Flow

เอกสารนี้อธิบาย authentication และ onboarding แบบ mock สำหรับเชื่อม Frontend
ในช่วงที่ยังไม่มี database, JWT และ email provider

## ข้อจำกัด

- ข้อมูลผู้ใช้อยู่ใน memory และจะกลับเป็นค่าเริ่มต้นเมื่อ server restart หรือ reload
- Password และ verification code ใช้สำหรับ local development เท่านั้น ห้ามใช้ใน production
- Verification code คือ `123456` และไม่มีการส่ง email จริง
- Token มีรูปแบบ `mock-access-token-<user_id>` ใช้ได้เฉพาะ process ที่ออก token นั้น

## เริ่ม Server

```bash
cd D:\hackathon\Jump_Dai_Backend
python -m uvicorn app.main:app --reload
```

เปิด Swagger UI ที่ `http://127.0.0.1:8000/docs`

## Demo Accounts

ทุกบัญชีใช้ password `password123` และอยู่ใน
`app/data/mock_users.py`

| Workspace | Email | Application role |
| --- | --- | --- |
| Learner | `demo@skillsync.local` | `LEARNER` |
| Creator / Instructor | `creator@skillsync.local` | `CREATOR` |
| Organization | `organization@skillsync.local` | `CREATOR` |

`organization` เป็น workspace type สำหรับ onboarding ใน mock ชุดนี้ ส่วนสิทธิ์
application ใช้ role `CREATOR`

## Flow

```text
POST /auth/register
        ↓
POST /auth/verify-email (code 123456)
        ↓
รับ access_token
        ↓
POST /auth/workspace
        ↓
GET /auth/me
```

### 1. Register

`POST /api/auth/register`

```json
{
  "name": "Peer",
  "email": "peer@example.com",
  "password": "password123"
}
```

ผลลัพธ์มี `next_step: "email_verification"` และ
`mock_verification_code: "123456"`

### 2. Verify Email

`POST /api/auth/verify-email`

```json
{
  "email": "peer@example.com",
  "code": "123456"
}
```

เก็บ `data.access_token` จาก response สำหรับ request ที่ต้อง login

### 3. Select Workspace

`POST /api/auth/workspace`

ใน Swagger กด **Authorize** ด้านบน แล้ววางเฉพาะค่า access token (ไม่ต้องมีคำว่า
`Bearer`) จากนั้นส่ง body:

```json
{
  "workspace_type": "creator"
}
```

ค่าที่ใช้ได้: `learner`, `creator`, `organization`

### 4. Read Current User

`GET /api/auth/me`

Swagger จะส่ง Bearer token ที่ Authorize ไว้ให้ และ response จะบอก
`workspace_type`, `roles`, และ `onboarding_completed`

## Sign in ด้วยบัญชี Demo

ไม่จำเป็นต้อง register หากต้องการทดสอบ role ที่มีอยู่แล้ว:

`POST /api/auth/login`

```json
{
  "email": "creator@skillsync.local",
  "password": "password123"
}
```

นำ `data.access_token` ไป Authorize ก่อนเรียก `/api/auth/me` หรือ endpoint ที่ต้อง
login

## แก้ไข Mock Users

เพิ่มหรือแก้ `MockUserSeed` ใน `app/data/mock_users.py` แล้วรอให้ `uvicorn --reload`
restart จากนั้น login ด้วยข้อมูลใหม่ได้ทันที

## Automated Tests

```bash
cd D:\hackathon\Jump_Dai_Backend
python -m pytest -q
```

Tests ครอบคลุม demo accounts ทั้งสามแบบ, register, verify email, workspace selection,
token และ validation errors
