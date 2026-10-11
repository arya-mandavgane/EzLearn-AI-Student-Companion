# PROGRESS

Last updated: 2026-10-11 — Brand Updated to EzLearn (ℰℓ Logo), Navbar Cleaned, Auth & Theme Verified ✅

---

## ✅ Done

### Brand Identity & UI Polish (EzLearn)
- **Brand Name**: Renamed application from "Study Companion" / "AI Study Companion" to **EzLearn**.
- **Cursive `ℰℓ` Logo**: Designed and integrated a stylish cursive `ℰℓ` logo badge (`'Dancing Script'`, `'Brush Script MT'`, `'Great Vibes'`, `'Caveat'`, cursive fallback) across:
  - Browser tab: `frontend/public/favicon.svg` with high-res SVG cursive `ℰℓ` over an indigo-purple gradient rounded square.
  - Sidebar: Brand header with `ℰℓ` badge and "EzLearn" gradient typography.
  - Empty Chat state: Welcome screen centered `ℰℓ` badge with "Welcome to EzLearn".
  - Shell header: `frontend/src/components/AppShell.jsx` updated with `ℰℓ` badge.
  - Google Fonts: Preconnected and loaded `Dancing Script` and `Great Vibes` in `frontend/index.html`.
- **Top-Right Simulation Shortcuts Removal**:
  - Removed top navbar `Simulations Quick Launcher` buttons (`📚 Stack`, `🎟️ Queue`, `📊 Sorting`) and modal container from `frontend/src/App.jsx`.
  - Simulations remain exclusively contextual and inline inside chat turns under Step 3 (`ProcessSimulationView`).
- **Dark/Light Mode Fix**:
  - Configured `@custom-variant dark (&:where(.dark, .dark *));` in `frontend/src/index.css` for Tailwind CSS v4 class-based theme toggling.
- **User Registration & Guest Isolation**:
  - User registration collects `name`, `email`, `age`, and password.
  - Guest users only have volatile access to their current chat session; chat history and performance reports are strictly locked to registered signed-in users.
  - All mock/dummy users and chat records cleared from SQLite database.
- **Deployment & Cloud Hosting**:
  - `render.yaml` & `backend/start.py`: Configured Render Blueprint for 1-click backend deployment with dynamic `PORT` binding, health check support, and robust CORS parsing. Backend is verified live on Render.
  - `vercel.json`: Added Vercel configuration for 1-click frontend deployment with SPA routing. Frontend is verified live on Vercel.
  - `frontend/src/App.jsx` & `frontend/src/lib/api.js`: Full-stack integration verified with seamless user registration, JWT authentication, and guest session isolation.
- **Verification**:
  - Full-stack live authentication verified end-to-end between Vercel and Render.
  - Frontend production build (`npm run build`) succeeded with 0 errors.
  - Backend automated test suite (33 tests in `app/tests`) passed with 100% OK.

### Phase 1 — Core MVP
- `backend/ai_wrapper.py` — Gemini SDK wrapper with retry logic and error handling
- `backend/main.py` — FastAPI app with `/health` and `/explain` endpoints; CORS enabled
- `backend/requirements.txt` — initial dependencies (FastAPI, uvicorn, python-dotenv, google-genai)
- `backend/.env.example` — template for secret config
- `frontend/` — React + Vite + Tailwind scaffold
- `frontend/src/App.jsx` — single-page UI: notes input, marks selector (2/5/10), explanation card, exam answer card, loading skeleton, error display
- `frontend/src/index.css` — Tailwind v4 import
- `frontend/vite.config.js` — Vite + Tailwind v4 plugin
- `.gitignore` — excludes `.env`, `node_modules`, `venv`, `__pycache__`
- `README.md` — exact run commands for both apps
- `AGENTS.md` — project rules for AI agents

### Phase 2 — Multi-modal & Document Ingestion
- `backend/ai_wrapper.py` — `generate_from_image(image_bytes, mime_type, prompt)` using single shared Gemini client
- `backend/main.py`:
  - `POST /upload`: Validates file size (max 10 MB) and MIME type via magic bytes. Rejects other types.
  - PDF processing: PyMuPDF page-by-page text extraction. Rejects scanned PDFs with prompt to upload photos.
  - Photo processing: OpenCV blur check with warning, Gemini vision transcription.
  - In-memory document storage: `_documents` dict.
  - `PUT /documents/{document_id}/text`: Persists student's corrected text.
  - `POST /explain`: Accepts `text` or `document_id`. Truncates >8000 chars with warning. Wraps notes in `<<<NOTES_START>>>` delimiters.
- `backend/requirements.txt`: Added `PyMuPDF`, `opencv-python-headless`, `numpy`, and `python-multipart`.
- `frontend/src/App.jsx`: Two-tab layout (Paste text / Upload file) with canvas image compression to 1600 px, per-page text editor, and warning boxes.

### Phase 3 — Quizzes, Caching & Dynamic Simulations
- `backend/ai_wrapper.py`:
  - Added Mock Mode toggle via `AI_MOCK` environment variable (`AI_MOCK=true`).
  - Returns fixed mock responses for `/explain`, `/quiz`, OCR, and simulation template classification when active.
- `backend/.env.example`: Added `AI_MOCK=false`.
- `backend/main.py`:
  - `POST /quiz`: Generates 5 questions (4 MCQ, 1 short) from notes or uploaded document. Validates JSON with retry. Returns questions with stripped correct answers.
  - `POST /quiz/{quiz_id}/answers`: Scores quiz answers in code. MCQs scored by exact string matching; short questions scored by user self-marking (`is_correct`). Returns score, total, per-question review with explanation, and `weak_topics`.
  - In-memory caching: Caches `/explain` and `/quiz` results by content hash to prevent duplicate AI invocations.
  - `POST /simulation/plan`: Matches input keywords without AI first (`stack`, `push`, `pop`, `lifo` -> "stack"; `queue`, `enqueue`, `dequeue`, `fifo` -> "queue"). Only falls back to AI if unmatched. Returns template, title, and fixed 2-sentence intro, or a friendly message listing supported topics.
- `frontend/src/App.jsx`:
  - "Take a quiz" button shown after explanations in both "Paste text" and "Upload file" tabs.
  - Interactive quiz flow: one question at a time, progress bar, large tap-friendly MCQ options, short question text box with "Show answer" and self-marking Yes/No buttons.
  - Result screen: score tally, weak topics highlight, per-question breakdown with explanation, and "New quiz" reset button.
  - Simulation Tab redesign:
    - Starts with an empty chooser asking "Which topic do you want to see?" with a text box, "Show simulation" button, clickable chips for "Stack" and "Queue", and note: "More topics are coming soon."
    - Shows friendly "not available yet" notification when unsupported topics (e.g. "sorting") are requested.
    - Simulations start empty (0 items, never pre-filled).
    - Small input field allowing students to type their own custom plate/person labels before pushing or enqueuing.
    - Stack simulation: visual plate pile, Push/Pop, capacity limit 5, underflow/overflow alerts, "Predict first" mode before pop, Python list code panel (`append`/`pop`), educational tooltips.
    - Queue simulation: visual waiting line of people, Enqueue/Dequeue, capacity limit 5, underflow/overflow alerts, "Predict first" mode before dequeue, Python collections.deque code panel (`append`/`popleft`), educational tooltips (`enqueue`, `dequeue`, `FIFO`, `front`, `rear`).
    - "Choose another topic" button to return to the chooser at any time.

### Phase 0 — Foundations, Modular Contracts & App Shell (Working Prototype Alignment)
- `backend/app/` architecture established:
  - `core/`: `config.py` (Pydantic Settings v2 from `.env`), `logging.py` (structured logger), `security.py` (JWT & security stubs)
  - `ai/`: `provider.py` (unified provider wrapper for Gemini & mock), `mock.py` (deterministic mocks for explain, quiz, OCR, RAG, simulations), versioned prompt templates in `prompts/`
  - `schemas/`: Complete Pydantic schemas for all endpoints (`common.py`, `auth.py`, `inputs.py`, `explain.py`, `ask.py`, `quiz.py`, `mastery.py`, `simulation.py`)
  - `api/`: Routers for `misc` (/health, /report-error), `auth` (Phase 1 stubs), `inputs` (/text, /file, /voice, /url, /{id}, /{id}/text), `explain` (/explain, /feedback), `ask` (/ask RAG stub), `quiz` (/generate, /{id}/submit), `mastery` (stubs), `simulations` (/catalog, /plan), `sync` (stub)
  - `app/main.py`: FastAPI app with `/api/*` contract + root-level legacy route aliases for seamless backward compatibility
- `frontend/` enhancements:
  - `src/lib/api.js`: Resilient API client with offline detection and mock fallback adapter
  - `src/lib/i18n.jsx` & `src/locales/`: Vanilla React i18n supporting English, Hindi, and Marathi
  - `src/lib/theme.jsx`: Dark / light mode state provider syncing with system preferences and HTML class
  - `src/components/`: Reusable `AppShell.jsx` (mobile bottom nav + desktop sidebar), `Onboarding.jsx` (3-step walkthrough), `LoadingSpinner.jsx`, `ErrorBox.jsx`, `OfflineBanner.jsx`
  - `src/mocks/`: Complete mock fixtures for health, explain, quiz, and simulation catalog
- Infrastructure: `docker-compose.yml`, `backend/Dockerfile`, updated `.env.example`
- Live Gemini AI Integration (`gemini-3.8-flash`):
  - Enabled live model generation via `AI_MOCK=false` in `backend/.env`.
  - Added native `response_mime_type="application/json"` config in `app/ai/provider.py` for guaranteed valid JSON responses.
  - Relaxed minimum character length constraints on `ExplainRequest` so any short topic keyword or question can be explained.
  - Fixed JSON extraction in `_parse_ai_json` to clean markdown code fences and bracket boundaries cleanly.
  - Added route fallback handling in frontend (`/explain` and `/api/explain`).
- Universal Simulation Engine (All Topics Supported):
  - Upgraded simulation planning in `app/api/simulations.py` to support **ANY topic** (Science, Algorithms, Math, Biology, etc.) rather than only Stack and Queue.
  - Dedicated visual engines retained for `Stack` and `Queue`.
  - Added `ProcessSimulationView` in `frontend/src/App.jsx` for all other concepts (e.g. Binary Search, Photosynthesis, Bubble Sort, Recursion) featuring:
    - Intuitive everyday analogies.
    - Interactive step-by-step stepper navigation (Step 1 to N).
    - Color-coded dynamic visual element canvas (active, target, completed, eliminated, highlighted).
    - Interactive "Predict what happens next" challenges with instant educational feedback.
    - Core logic / code panel for each step.
- Verified end-to-end: Live explain works for any topic notes; simulations generate interactively for any queried topic.

### Phase 1 — Accounts and Data Layer (Completed ✅)
- SQLAlchemy Models & SQLite Persistence:
  - `backend/app/models/models.py`: Complete relational schema covering `users`, `inputs`, `chunks`, `explanations`, `quizzes`, `quiz_attempts`, `mastery`, `revisions`, `feedback`, and `error_reports`.
  - `backend/app/models/database.py`: SQLite engine, SessionLocal, Base, `get_db` generator, and `init_db()` table creation on startup.
- Authentication & Security Core:
  - `backend/app/core/security.py`: Secure password hashing with bcrypt, JWT token creation & decoding with PyJWT (HS256, 32+ byte secret key).
  - FastAPI dependencies: `get_current_user` (strict 401 guard) and `get_current_user_optional` (supports guests without disruption).
- Auth API Router:
  - `backend/app/api/auth.py`:
    - `POST /api/auth/register`: Validates email and minimum 6-character password, prevents duplicates (409 Conflict), hashes password, creates user, issues JWT.
    - `POST /api/auth/login`: Authenticates credentials, checks active status, returns JWT access token + profile.
    - `GET /api/auth/me`: Protected route returning authenticated user's profile and usage tally.
    - `GET /api/auth/google/*`: Friendly status stubs for Google Sign-in.
- Testing & Cross-User Data Isolation:
  - `backend/app/tests/test_auth.py`: 7 automated tests covering registration, duplicate rejection, wrong password rejection, valid login, protected route enforcement, and cross-user data isolation (all passed).
- Frontend Authentication UX:
  - `frontend/src/components/AuthModal.jsx`: Clean modal dialog with tabs for Log In and Create Account, form validation, error banners, and "Continue as Guest" fallback.
  - `frontend/src/App.jsx`: Top status bar displaying active student profile pill or "Guest Mode" indicator, with instant sign-in and sign-out controls.

### Phase 2 — Input Processing Pipeline (Completed ✅)
- Text Cleaning, Normalization & Security:
  - `backend/app/services/text_cleaner.py`:
    - `clean_text`: Strips null bytes, non-printable control characters, normalizes line breaks.
    - `validate_text`: Rejects empty strings and emoji/symbol-only inputs with informative HTTP 422 messages.
    - `detect_language`: Identifies **English** (`en`), **Hindi** (`hi`), **Marathi** (`mr`), and **Hinglish** (`hinglish`).
    - `check_prompt_injection`: Scans for adversarial overrides (e.g. "ignore previous instructions") and attaches security warnings while treating student notes purely as study data.
- Multimodal Audio & Vision Ingestion:
  - `backend/app/ai/provider.py`: Implemented `generate_from_audio` using Gemini multimodal speech understanding. Audio bytes are strictly discarded from memory immediately after transcription.
  - `backend/app/api/inputs.py`:
    - `POST /inputs/text`: Cleans text, detects language, flags injection attempts, and saves to database.
    - `POST /inputs/file`: Dispatches background job (`BackgroundTasks`) with live progress increments (15% -> 30% -> 60% -> 100%), PyMuPDF text extraction, and OpenCV blur detection.
    - `POST /inputs/voice`: Ingests audio up to 60 seconds, returns cleaned transcript with detected language and DB record.
    - `POST /inputs/url`: Gracefully returns status `coming_soon` with friendly guidance.
    - `GET /inputs/{id}`: Status polling endpoint returning progress percentage, page breakdown, and warnings.
    - `PATCH /inputs/{id}/text`: Persists student's edited text.
- Testing Suite:
  - `backend/app/tests/test_inputs.py`: 10 comprehensive tests covering empty text, emoji-only text, language detection for English, Hindi, Marathi, Hinglish, prompt injection defense, unsupported files, and corrupt PDFs (all 17 total tests in `app/tests/` passing).
- Audio Transcription Speed & Real-time Voice Experience:
  - Switched model configuration to `gemini-flash-lite-latest` in `.env`, resolving the 429 quota exhaustion from `gemini-3.8-flash`.
  - Added intelligent multi-model fallback chain in `app/ai/provider.py` (`gemini-flash-lite-latest`, `gemini-2.5-flash-lite`) to eliminate rate-limit freezes.
  - Added live real-time speech recognition in `VoiceTab` via browser Web Speech API: speech streams live into the textarea as the student talks with zero delay, backed by AI audio transcription.
- Study Resource Rule Enforcement (Strict Input Validation):
  - Added `validate_study_resource()` in `backend/app/services/text_cleaner.py`: rejects random commands (e.g. "tell me a joke", "sing a song", "who are you"), conversational chit-chat, greetings, and empty inputs with explicit instructions to attach or paste notes/resources in the respective format.
  - Wired into `POST /api/inputs/text`, `POST /inputs/text`, `POST /api/inputs/voice`, `POST /inputs/voice`, and `POST /explain`.
  - Added client-side validation `validateStudyResourceClient()` in `frontend/src/App.jsx` across both `PasteTab` and `VoiceTab`, showing informative guidance and blocking invalid requests before server dispatch.
  - Added resource-requirement guidance banners on input areas reminding users that notes/resources must be provided.
  - Automated tests updated in `backend/app/tests/test_inputs.py`: added `test_11_random_command_rejected_with_instructions` (18/18 tests passing across test suite).

### Phase 3 — RAG with Citations (Complete ✅)
- `backend/app/services/chunking.py`:
  - Intelligent document and text chunking preserving page boundaries and heading titles (`chunk_pages`, `chunk_plain_text`).
  - Generates verifiable snippets and chunk IDs for every section.
- `backend/app/services/vector_store.py`:
  - In-memory & SQLite vector store (`VectorStore`, `global_vector_store`) supporting cosine similarity and token overlap retrieval.
  - Relevance threshold (`0.25`) enforcing strict "not_found_in_notes" classification when queries fall below relevance.
  - Per-user data isolation filtering by `user_id`.
- `backend/app/ai/provider.py`:
  - Live embedding function `embed(texts)` with deterministic semantic token hash fallback for mock mode or offline execution.
- `backend/app/api/inputs.py`:
  - Automatic chunking and vector indexing upon notes text ingestion (`POST /api/inputs/text`), background file processing (`POST /api/inputs/file`), and text updates (`PATCH /api/inputs/{id}/text`).
- `backend/app/api/ask.py`:
  - `POST /api/ask` endpoint answering questions strictly using retrieved note passages with exact page and chunk citations.
  - Returns `not_found_in_notes: true` with a labeled general answer for off-topic questions.
  - Prompt injection defense: text in notes treated as data only, never executed.
- Frontend (`frontend/src/App.jsx`):
  - `AskNotesSection` component integrated into `PasteTab`, `UploadTab`, and `VoiceTab`.
  - Interactive page citation chips (`📄 Page 1`) that display original snippet popovers on click.
  - Clear visual banner for questions not found in notes.
- Testing Suite (`backend/app/tests/test_rag.py`):
  - 5 comprehensive tests: chunking, vector retrieval, valid citations, off-topic not-found detection, and prompt injection defense.
  - All 23 tests passing across the backend test suite.

---

### Phase 4 — Topic Detection & Explanations (Complete ✅)
- Versioned Prompt Templates:
  - `backend/app/ai/prompts/classify.txt`: Pedagogy-driven topic-type classifier returning `simulation | analogy | comparison_table | worked_example` plus topic and subtopic.
  - `backend/app/ai/prompts/explain.txt`: Rich explanation prompt returning real-life picture first, structured summary, sections, key terms in English with native meanings, comparison tables, and worked example steps.
- Backend Explanation Engine (`backend/app/api/explain.py`):
  - `POST /api/explain`: Generates validated Explanation JSON with depth level (`simple`, `normal`, `exam_ready`) and exam marks (`2`, `5`, `10`).
  - `POST /api/explain/{id}/feedback`: "This didn't help" button records feedback and automatically regenerates in the next best format (`analogy` -> `comparison_table` -> `worked_example` -> `simulation`).
  - `POST /api/report-error`: Records student bug/issue reports.
  - Multi-language support across English, Hindi, Marathi, and Hinglish.
  - Full backward compatibility with Phase 1-3 clients (`simple_explanation`, `exam_answer`).
- Frontend Format Renderers (`frontend/src/App.jsx`):
  - `MultiFormatExplanationCard`:
    - Real-life picture card shown first with everyday physical analogy.
    - Comparison Table renderer with responsive header and data cells.
    - Worked Example renderer with sequential step breakdown.
    - Simulation callout button launching hands-on interactive simulations.
    - Key Technical Terms grid (English term + native language meaning).
    - Feedback bar ("👍 Yes", "👎 This didn't help (Try another format)", and "Report Error").
  - `LevelSelector`: Quick switcher between 🌱 Simple, 📖 Normal, and 🎯 Exam Ready depth.
- Testing Suite (`backend/app/tests/test_explain_phase4.py`):
  - 6 comprehensive tests: topic classification, comparison table structure, worked example format, feedback format switching, Hindi output, and backward compatibility (all 29 tests passing across backend test suite).

### AI Chatbot Interface & Dynamic Resource Pipeline (Gemini WebApp Style) ✅
- Backend Chatbot Architecture (`backend/app/api/chat.py` & `backend/app/models/models.py`):
  - Database models: `ConversationRecord`, `MessageRecord`, `ChatResourceRecord` storing messages and multi-modal resources dynamically per chat.
  - Resource Ingestion: `/api/chat/conversations/{id}/resources/text` and `/api/chat/conversations/{id}/resources/upload` with OCR (images/camera/gallery), speech transcription (audio/mic), and PDF page extraction.
  - Strict Resource Rule Enforced: Students cannot send messages in a chat without adding study resources first (`HTTP 400` validation).
  - Dynamic Hybrid RAG with citations, using internal vector store first, gracefully synthesizing external references when required.
  - Turn-based generation adhering to required structure:
    1. **What you asked** (highlighted prompt bubble)
    2. **Explanation** (everyday analogy first, concept summary, key terms, citations)
    3. **Demonstration / Simulation** (interactive process visualizer)
    4. **10-Question Quiz** (scored in code, single-attempt lock)
    5. **AI Suggestions** (analyzes strengths, weaknesses, must-do topics, and asks for user comments)
  - Performance Reports Endpoint (`/api/chat/reports/{timeframe}`):
    - Computes overall accuracy, strengths, weaknesses, and must-do revision topics across Daily, Weekly, and Monthly timeframes.
- Frontend Gemini WebApp Redesign (`frontend/src/App.jsx`, `Sidebar.jsx`, `ResourceModal.jsx`, `TenQuestionQuiz.jsx`):
  - Left Sidebar with 5 Tiers:
    1. 📅 Daily report
    2. 📊 Weekly report
    3. 📈 Monthly report
    4. ➕ Start new conversation
    5. 💬 History list with delete and resource counts
  - Top-Right: Dark / Light mode toggle and sign-in status pill.
  - Chat input bar: `+` button on leftmost side, text input, and submit button on rightmost side.
  - Single-attempt locked quiz component with result review and student feedback space.
  - All 33 automated tests passing across the backend suite (`test_chat.py`, `test_explain_phase4.py`, `test_rag.py`, `test_inputs.py`, `test_auth.py`).

---

### Phase 5 — Interactive Simulations (Complete ✅)
- **Shared Simulation Architecture & Routing** (`frontend/src/components/SimulationView.jsx`):
  - Dynamic template dispatcher (`ProcessSimulationView`) automatically selecting between **Stack**, **Queue**, **Sorting**, or **Universal Process Simulation** for arbitrary subjects.
  - Dedicated simulation launcher in the top navbar allowing immediate hands-on exploration of any data structure or algorithm.
- **Dedicated Stack Visualizer (`StackSimulation`)**:
  - Cafeteria plate pile metaphor (bottom-to-top rendering).
  - Push, Pop, and Peek operations with live capacity tracking (max 5 plates).
  - Clear **Stack Overflow** and **Stack Underflow** alert states.
  - Interactive **Predict-then-Reveal** challenge mode before pop operations.
  - Live Python list code panel dynamically tracing `stack.append()`, `stack.pop()`, and `stack[-1]`.
- **Dedicated Queue Visualizer (`QueueSimulation`)**:
  - Ticket counter waiting line metaphor with visible **FRONT** and **REAR** markers.
  - Enqueue (adds to rear), Dequeue (serves from front), and Peek (inspects front).
  - Capacity limit of 5 with overflow and underflow warnings.
  - Interactive **Predict-then-Reveal** challenge mode before dequeue.
  - Live Python `collections.deque` code panel tracing `queue.append()`, `queue.popleft()`, and `queue[0]`.
- **Dedicated Sorting Visualizer (`SortingSimulation`)**:
  - Multi-algorithm support: **Bubble Sort**, **Selection Sort**, and **Insertion Sort**.
  - Step-by-step navigation controls (Back, Forward, Reset).
  - Comparisons articulated in plain words ("Is 8 greater than 3? Yes, so swap them!").
  - Predict-then-reveal challenges on every swap decision.
  - Dynamic visual bar chart heights with active comparison highlighting and live Python algorithm code execution tracing.
- **Universal Process Engine (`UniversalProcessSimulation`)**:
  - Handles all other topics (Science, Math, Biology, General processes) with intuitive analogies, stepper navigation, and predict-what-happens-next queries.

### User Management, Guest Volatile Chats & Theme Engine Overhaul ✅
- **Registration with Core Demographics**:
  - `backend/app/models/models.py` & `backend/app/api/auth.py`: Added `name`, `email`, and `age` validation on user registration (`POST /api/auth/register`).
  - `frontend/src/components/AuthModal.jsx`: Updated registration form to collect **Full Name**, **Age**, **Email Address**, and **Password** (min 6 chars).
  - Profile header displays student name and age badge (`Name (Age y)`) with **Sign Out** button.
- **Strict Guest vs Registered User Chat Access**:
  - **Guest Users**: Can only access their current active chat session. Chats are completely **volatile** and not recorded to history. The sidebar displays a clear locked indicator (`🔒 Registered Only`) explaining that history and reports are preserved for registered users.
  - **Registered & Signed-In Users**: Only see their own chat history and performance metrics in the left sidebar. Cross-user data isolation strictly enforced via JWT authentication across all chat endpoints (`GET /api/chat/conversations`, `GET /api/chat/conversations/{id}`, `DELETE /api/chat/conversations/{id}`, and `GET /api/chat/reports/{timeframe}`).
  - Cleaned & reset the database: wiped all old sample/mock chats and sample users (`study_companion.db`).
- **Dark & Light Mode Toggle Fix**:
  - Added `@custom-variant dark (&:where(.dark, .dark *));` to `frontend/src/index.css`.
  - In Tailwind CSS v4, this enables immediate class-based dark mode switching via the `dark` class on the `<html>` root element. Both light and dark themes toggle instantly with full visual contrast across all components.

---

## 🔄 In Progress

_User Management, Guest Volatile Sessions & Dark Theme Fix Complete. Ready for Phase 6 (Mastery Tracking & Spaced Repetition)._

---

## 🔜 Next (Phase 6 — Mastery Tracking & Spaced Repetition)
- Leitner box / SM-2 spaced repetition interval computation.
- Weak topics auto-tagging and must-do review schedule.
- Mastery status badges (Novice, Developing, Mastered).
- Sync queue for offline study session caching.

---

## ▶ How to run

### Backend
```bash
cd backend
.\venv\Scripts\Activate.ps1       # Windows PowerShell
pip install -r requirements.txt   # first time only
uvicorn main:app --reload --port 8000
```
Set `AI_MOCK=false` in `backend/.env` to connect to live Gemini API.

### Frontend
```bash
cd frontend
npm install    # first time only
npm run dev
```

Open <http://localhost:5173> in browser.
