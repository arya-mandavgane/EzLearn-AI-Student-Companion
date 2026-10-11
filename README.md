# AI Study Companion

A web app where a student pastes study notes or uploads files (PDF, PNG, JPG) to get:
1. Plain-language explanations and structured exam-format answers.
2. An interactive practice quiz generated from their notes (4 MCQ + 1 short question).
3. Topic simulations with interactive visualizers (Stack and Queue).

---

## Project layout

```
ai-study-companion/
├── backend/          # FastAPI + Python
│   ├── main.py       # Endpoints: /health, /upload, /documents/{id}/text, /explain, /quiz, /quiz/{id}/answers, /simulation/plan
│   ├── ai_wrapper.py # ONLY file that calls Gemini (text + vision + mock mode)
│   ├── requirements.txt
│   └── .env.example
├── frontend/         # React + Vite + Tailwind
│   └── src/App.jsx   # 3 Tabs: Paste text, Upload file, Simulation
├── docs/PROGRESS.md
├── AGENTS.md
└── README.md
```

---

## Prerequisites

| Tool | Version tested |
|------|---------------|
| Python | 3.10+ |
| Node.js | 18+ |
| npm | 9+ |

---

## 1 · Backend setup

```bash
cd backend

# Copy the example env file
copy .env.example .env
# Set GEMINI_API_KEY=<your key> in .env (or keep AI_MOCK=true for offline mock testing)

# Create virtual environment and install dependencies
python -m venv venv

# Activate (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# Activate (macOS / Linux)
source venv/bin/activate

pip install -r requirements.txt
```

### Run the backend

```bash
# From backend/ with venv active
uvicorn main:app --reload --port 8000
```

- Health check: <http://localhost:8000/health>
- Swagger API docs: <http://localhost:8000/docs>

---

## 2 · Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open: <http://localhost:5173>

---

## Features

- **Paste text tab**: Paste study notes, choose marks (2, 5, 10), get structured explanation and exam answers.
- **Upload file tab**: Upload PDFs or photos (PNG, JPG/JPEG up to 10 MB).
  - Browser canvas image compression to 1600 px.
  - PDF page-by-page text extraction (PyMuPDF) with scanned PDF detection.
  - Photo blur detection (OpenCV) with warnings and OCR transcription.
  - Student text editing before explanation.
- **Interactive Quizzes**:
  - Click "Take a quiz" after any explanation (Paste text or Upload file tabs).
  - 5-question test (4 MCQ, 1 short-answer).
  - Single question view with progress bar.
  - Self-marking short answers with model answer reveal and Yes/No verification.
  - Immediate score tally and list of weak topics.
  - In-code answer grading without extra AI calls.
  - In-memory caching for repeated notes.
- **CS Simulation tab**:
  - Topic chooser asking "Which topic do you want to see?" with keyword entry and clickable chips ("Stack", "Queue").
  - Unsupported topics (e.g. "sorting") show friendly "not available yet" notification.
  - All simulations start completely empty (0 items, never pre-filled).
  - Custom input field for student to label their own items before Push / Enqueue.
  - **Stack**: Plate pile graphic, Push/Pop, capacity 5, underflow/overflow prevention, "Predict first" mode before pop, Python list code panel (`append`/`pop`), educational tooltips.
  - **Queue**: Line of people graphic, Enqueue/Dequeue, capacity 5, underflow/overflow prevention, "Predict first" mode before dequeue, Python collections.deque code panel (`append`/`popleft`), educational tooltips (`enqueue`, `dequeue`, `FIFO`, `front`, `rear`).
  - "Choose another topic" button to return to the chooser at any time.

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | If `AI_MOCK=false` | — | Google Gemini API key |
| `GEMINI_MODEL` | No | `gemini-3.8-flash` | Gemini model identifier |
| `AI_MOCK` | No | `false` | When `true`, returns mock responses without calling Gemini |
