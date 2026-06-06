# SahityaAI

SahityaAI is a bilingual essay evaluation platform for English and Kannada writing. It combines a BERT-based scoring model with rule-based text analysis to generate essay scores, trait-level feedback, grammar suggestions, and usage analytics.

The repository contains:
- A FastAPI backend that serves scoring, analysis, and dashboard APIs.
- A React + Vite frontend for evaluating essays and browsing results.
- Trained model weights and supporting NLP scripts for preprocessing, language detection, and scoring experiments.
- Sample datasets used during development and evaluation.

## What the app does

When a user submits an essay, the backend:
- Detects the language.
- Runs the BERT scoring model to produce a score and grade.
- Runs text analysis for traits like content, organization, language use, conventions, and vocabulary.
- Uses LanguageTool to identify grammar issues.
- Optionally saves the result to a local SQLite database.

The frontend provides pages for:
- Dashboard overview.
- Essay evaluation.
- AI tutor/chat-style help.
- Analytics.
- Settings.

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite, PyTorch, Transformers, LanguageTool, textstat
- Frontend: React 19, TypeScript, Vite, React Router, Axios, Recharts
- Model assets: PyTorch checkpoint stored in `bert_all_prompts_best.pt`

## Repository Layout

```text
.
├── README.md
├── backend/
│   ├── main.py            # FastAPI app and API routes
│   ├── analyzer.py        # Grammar, readability, trait, and text analysis
│   ├── scorer.py          # BERT scoring service
│   ├── database.py        # SQLite setup and DB session helpers
│   ├── models.py          # SQLAlchemy ORM models
│   ├── schemas.py         # Pydantic request/response models
│   ├── requirements.txt   # Python dependencies
│   └── sahitya.db         # Generated local SQLite database
├── frontend/
│   ├── src/
│   │   ├── App.tsx        # Route wiring
│   │   ├── api/client.ts  # Frontend API client
│   │   ├── components/    # Shared UI components
│   │   └── pages/         # Dashboard, Evaluate, Tutor, Analytics, Settings
│   ├── package.json
│   └── README.md          # Vite template documentation
├── bert_all_prompts_best.pt  # Trained essay scoring checkpoint
├── training_set_rel3.tsv      # ASAP-style training data
├── asap_english_clean.csv     # Cleaned English sample data
├── asap_kannada_full.csv      # Kannada essay data
├── asap_kannada_full_v2.csv   # Alternate Kannada dataset version
├── asap_kannada_full_final.csv # Final Kannada dataset version
├── asap_kannada_test.csv      # Kannada test split
├── asap_kannada_test_normalized.csv # Normalized Kannada test split
├── bert_scorer.py             # Standalone scoring script
├── preprocessing.py           # Data preprocessing helpers
├── kannada_data_gen.py        # Kannada data generation utilities
├── kannada_data_eval.py       # Kannada evaluation helpers
├── lang_detector.py           # Language detection helper
├── hi.py                      # Supporting helper script
└── test.py                    # Local test or experimentation script
```

## How the Backend Works

The backend exposes these main routes:

- `POST /api/evaluate`  
  Evaluates an essay, returns score, grade, trait breakdown, grammar errors, language detection, and analytics.

- `GET /api/essays`  
  Returns saved essays from SQLite.

- `GET /api/essays/{essay_id}`  
  Returns a full saved essay record.

- `DELETE /api/essays/{essay_id}`  
  Deletes a saved essay.

- `GET /api/dashboard`  
  Returns summary statistics for the dashboard.

- `GET /api/analytics`  
  Returns aggregated writing metrics and score trends.

- `GET /api/health`  
  Returns backend health status and whether the model is loaded.

FastAPI also serves interactive documentation at:
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

## Setup

### 1. Backend

Install Python dependencies and start the API server.

```bash
cd backend
python -m venv .venv
```

Activate the environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then install dependencies and run the server:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Notes:
- The first run may take longer because the BERT checkpoint is loaded into memory.
- LanguageTool may also download resources on first use.
- SQLite data is stored in `backend/sahitya.db` and is created automatically.

### 2. Frontend

Install dependencies and start the Vite dev server.

```bash
cd frontend
npm install
npm run dev
```

The frontend usually runs at:
- `http://localhost:5173`

## Frontend Pages

- `/` Dashboard with summary cards and recent essays.
- `/evaluate` Essay evaluation editor and detailed feedback.
- `/tutor` AI tutor workflow.
- `/analytics` Writing analytics and charts.
- `/settings` Application preferences.

## Data and Model Files

This repository includes several generated or curated data files. They are useful for development, experimentation, and model evaluation:

- `training_set_rel3.tsv` is the main ASAP-style training dataset.
- `asap_english_clean.csv` is a cleaned English dataset variant.
- `asap_kannada_full.csv`, `asap_kannada_full_v2.csv`, and `asap_kannada_full_final.csv` are Kannada dataset versions used during iteration.
- `asap_kannada_test.csv` and `asap_kannada_test_normalized.csv` are test splits.
- `bert_all_prompts_best.pt` is the trained PyTorch checkpoint used by the backend scorer.

## Development Notes

- The backend uses CORS for the local Vite dev server.
- Essay scoring is done through the backend API, not in the browser.
- The frontend stores no model state locally; it only renders API responses.
- If you update the backend analysis logic, keep the `backend/schemas.py` response models aligned with the frontend types in `frontend/src/api/client.ts`.

## Common Troubleshooting

- If evaluation returns a 500 error, check the backend console first. Grammar parsing or model loading issues will show there.
- If the frontend keeps re-rendering or freezing on the evaluation page, check the language auto-detection logic in `frontend/src/pages/Evaluate.tsx`.
- If `language_tool_python` fails on first run, allow the download to finish and restart the backend.
- If the database seems empty, remember that essays are only saved when the request uses `save: true`.

## License

No license file is currently included in the repository.
