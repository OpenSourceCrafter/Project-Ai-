# AI Smart Stock Analyst — ระบบวิเคราะห์หุ้นอัจฉริยะ

Monorepo รวม **frontend** (React/Vite) และ **backend** (FastAPI + PostgreSQL +
Redis) ไว้ใน repository เดียว ทั้งสองฝั่งเชื่อมต่อกันผ่าน REST API

```
ai-smart-stock-analyst/
├── frontend/     # React + Vite — UI ทั้งหมด, เรียก backend ผ่าน src/lib/api.js
├── backend/      # FastAPI + PostgreSQL + Redis + Alembic — ดู backend/README.md
└── docker-compose.yml   # รันทั้ง stack พร้อมกัน (postgres + redis + backend + frontend)
```

## วิธี "sync" กันของ frontend ↔ backend

`frontend/src/lib/api.js` คือชั้นเชื่อมต่อทั้งหมด — ทุกฟังก์ชันยิงไปที่
`VITE_API_BASE_URL` (ค่าเริ่มต้น `http://localhost:8000`) และ **fail แบบนุ่มนวล**:
ถ้า backend ยังไม่รัน / endpoint นั้นยังเป็น stub / ยังไม่มีข้อมูลใน DB ฟังก์ชันจะ
คืนค่า `null` แทนการ error แล้ว UI จะใช้ **mock data เดิมแทนโดยอัตโนมัติ**
พร้อมแสดง badge `DEMO DATA` (สีเทา) เทียบกับ `LIVE` (สีเขียว) ที่มุมขวาบนของ
แต่ละ section (Header, Market Overview, Top 10, News, Stock Detail panel) —
เปิดแอปแล้วดูที่ badge นี้จะรู้ทันทีว่ากำลังดูข้อมูลจริงหรือ demo อยู่

| Section ในหน้าเว็บ | เรียก backend endpoint | สถานะ |
|---|---|---|
| Header (จุดเชื่อมต่อ) | `GET /healthz` | ✅ ใช้งานได้ทันที |
| Market Overview | `GET /api/market` | ✅ ใช้งานได้ทันที |
| Top 10 (ทุกแท็บ) | `GET /api/top-stocks?category=...` | ⚠️ ต้องมีข้อมูลใน `weekly_rankings` ก่อน (จาก cron job หรือ insert เอง) |
| News feed | `GET /api/news` | ✅ ใช้งานได้ทันที |
| Stock detail → ราคา | `GET /api/stocks/{ticker}/price` | ✅ ใช้งานได้ทันที |
| Stock detail → fundamentals | `GET /api/stocks/{ticker}/fundamentals` | ✅ ใช้งานได้ทันที |
| Stock detail → news | `GET /api/stocks/{ticker}/news` | ✅ ใช้งานได้ทันที |

("ใช้งานได้ทันที" = endpoint คำนวณจาก provider สด ไม่ต้องมีข้อมูลใน DB ล่วงหน้า
แค่ใส่ `MARKET_DATA_API_KEY` / `NEWS_API_KEY` ใน `backend/.env` ให้ครบ)

## รันทั้ง stack พร้อมกัน (แนะนำ)

```bash
cp backend/.env.example backend/.env      # กรอก API key จริง
cp frontend/.env.example frontend/.env    # ค่า default ใช้ได้เลยสำหรับ local dev
docker compose up --build
```
- Frontend: http://localhost:5173
- Backend Swagger docs: http://localhost:8000/docs

`docker compose` จะรัน `alembic upgrade head` ให้อัตโนมัติก่อนสตาร์ท API
(ดูใน `command:` ของ service `backend`) — ไม่ต้องรันเองแยก

## รันแยกส่วนตอน dev (ไม่ใช้ Docker)

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt --break-system-packages
# ต้องมี postgres/redis รันอยู่ (docker compose up postgres redis ก็ได้)
alembic upgrade head
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## อัปโหลดขึ้น GitHub

โปรเจกต์นี้ `git init` และ commit แรกไว้ให้แล้ว (ดูด้วย `git log`) เหลือแค่
สร้าง repo บน GitHub แล้วต่อสาย:

```bash
# 1) สร้าง repo เปล่าบน GitHub ก่อน (github.com/new) — อย่าติ๊ก "Add README"
#    เพื่อไม่ให้ชนกับ README ที่มีอยู่แล้ว

# 2) ต่อ remote แล้ว push
cd ai-smart-stock-analyst
git branch -M main
git remote add origin https://github.com/<your-username>/ai-smart-stock-analyst.git
git push -u origin main
```

ใช้ GitHub CLI แทนได้ถ้ามี:
```bash
gh repo create ai-smart-stock-analyst --private --source=. --remote=origin --push
```

**สำคัญ:** `.env` ทั้งสองฝั่ง (`backend/.env`, `frontend/.env`) ถูกกันไว้ใน
`.gitignore` แล้ว — จะไม่ถูก push ขึ้น GitHub มีแต่ `.env.example` เท่านั้นที่
ขึ้นไป ปลอดภัยเรื่อง API key รั่ว แต่ก็หมายความว่าทุกเครื่อง/ทุกคนที่ clone
repo นี้ไปต้อง `cp .env.example .env` แล้วกรอกคีย์เองใหม่ทุกครั้ง

### Deploy จริง (แยก host กัน)

Frontend (`npm run build` → static files ใน `frontend/dist/`) กับ Backend
เป็นคนละ deployment target โดยทั่วไป:

| ส่วน | โฮสติ้งที่เหมาะ | หมายเหตุ |
|---|---|---|
| Frontend | Vercel, Netlify, Cloudflare Pages | ตั้ง env var `VITE_API_BASE_URL` ให้ชี้ไป backend URL จริง (ไม่ใช่ localhost) |
| Backend | Railway, Render, Fly.io, หรือ VPS + Docker | ต้องมี managed Postgres + Redis คู่กัน, ตั้ง `APP_CORS_ORIGINS` ให้รวม domain จริงของ frontend |

## เอกสารเพิ่มเติม

- **Backend architecture, DB schema, Alembic migrations, security checklist:** [`backend/README.md`](./backend/README.md)
- **Frontend component structure, mock-data fallback logic:** ดูคอมเมนต์ใน [`frontend/src/lib/api.js`](./frontend/src/lib/api.js)
