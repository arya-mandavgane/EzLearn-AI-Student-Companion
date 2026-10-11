# AGENTS.md — Rules for AI agents and developers

## Working style
1. **Small, working steps**: Make one change at a time; verify it works before moving on.
2. **Update docs last**: The final step of every task must be updating `docs/PROGRESS.md`.
3. **AI calls only through ai_wrapper.py**: Never call Gemini (or any AI API) directly from
   routes or other modules. Always go through `backend/ai_wrapper.py`.
4. **Never commit secrets**: `.env` files must stay in `.gitignore`. Use `.env.example`
   as the committed template.
5. **No new libraries or big rewrites without asking**: If a new dependency or major refactor
   is needed, pause and ask the project owner before proceeding.

## Project structure
```
ai-study-companion/
├── backend/          # FastAPI Python backend
│   ├── main.py       # Routes and app entry point
│   ├── ai_wrapper.py # ONLY file that calls Gemini
│   └── .env          # Secret keys (never commit)
├── frontend/         # React + Vite + Tailwind frontend
│   └── src/
│       └── App.jsx   # Single-page UI
├── docs/
│   └── PROGRESS.md   # Kept up to date after every task
├── AGENTS.md         # This file
└── README.md         # Run commands and overview
```

## Phase rules
- **Phase 1** (current): Single explain endpoint, no auth, no database.
- Do not start Phase 2 (quiz generation, history, etc.) until explicitly told to.
