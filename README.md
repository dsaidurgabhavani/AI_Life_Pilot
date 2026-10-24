# AI LifePilot — Your Intelligent Daily Life Assistant

> **AI Website Build Sprint** | **Theme 2: Reimagine Everyday Life — Make the Complex Simple**

AI LifePilot is a modern personal productivity SaaS platform engineered to eliminate daily cognitive overwhelm for students and working professionals. By combining the **Eisenhower Decision Matrix**, **deadline proximity heuristics**, **dynamic time-blocking with buffer allocation**, and a **transparent Dual-Engine AI system** (Google Gemini + deterministic Smart Heuristic Engine), AI LifePilot simplifies daily life into prioritized, focused action.

---

## 🚀 Live Demo & Quick Start

The platform consists of a **FastAPI** backend (Python) with a persistent SQLite database and a **React + TypeScript + Tailwind CSS** frontend powered by Vite and Lucide React.

### Running with one command (Windows):
Double-click `start.bat` or run:
```powershell
.\start.bat
```

### Manual Start:

#### 1. Backend (FastAPI + SQLite)
```bash
# From workspace root
python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000
```
- API Base URL: `http://127.0.0.1:8000`
- Interactive Swagger Documentation: `http://127.0.0.1:8000/docs`

#### 2. Frontend (React + Vite + TypeScript + Tailwind CSS)
```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5173
```
- Web Application: `http://127.0.0.1:5173`

---

## ✨ Core Features & Technical Highlights

### A. AI Daily Planner & Time-Blocking
- **Multi-Factor Prioritization:** Ranks tasks using Eisenhower urgency/importance, deadline proximity, and status.
- **Dynamic Chronological Schedule:** Automatically allocates start and end times within user working hours (e.g., 09:00 - 18:00), automatically reserving 15-minute cognitive shift buffers and lunch breaks.
- **Schedule Regeneration:** Allows one-click regeneration and instant updates back to the persistent database.

### B. Smart Deadline Manager
- **Live Countdown Timers:** Calculates real-time status: Overdue, Urgent (<4h), Due Today, Upcoming.
- **Actionable Interventions:** Displays intelligent risk-mitigation steps for overdue or at-risk deadlines (e.g. recommending 25m sprint timeboxes).
- **In-App Notification Drawer:** Top bell alert badge flags overdue items and provides one-click completion or focus sprint launching.

### C. Intelligent AI Assistant & Goal Decomposer
- **Dual-Engine Architecture:** Works out-of-the-box with a high-fidelity **Smart Heuristic Engine**, or seamlessly upgrades to **Google Gemini 2.5 Flash** when an API key is configured.
- **Integrity & Transparency:** Always identifies the exact engine powering each response with visual badges (`Smart Heuristic Engine` vs `Gemini 2.5 Flash`).
- **Goal Decomposition Modal:** Splits daunting goals (e.g. exams, software projects, presentations) into 4–5 bite-sized, prioritized subtasks with a 1-click button to import them directly into your database.

### D. Smart Study and Work Mode (Pomodoro Timer)
- **Dedicated Modes:** Seamless toggle between **Study Mode** and **Work Mode**.
- **Interactive Timer:** 25m focus sprints, 5m short breaks, and 15m long recovery breaks.
- **Web Audio Chimes:** Built-in synthesizer chimes (Web Audio API) when timers conclude.
- **Session Tracking:** Automatically records focus minutes to SQLite and links them with tasks.

### E. Habit Consistency Tracker
- **Real Record Streaks:** Calculates streaks and consistency rates strictly from database completion records.
- **7-Day Interactive Matrix:** Checkboxes for past 7 days with live percentage updates and celebration confetti.
- **Sample Routines:** Preloaded with reading, exercise, coding practice, and evening planning.

### F. Productivity Analytics
- **Data-Driven Metrics:** Real task completion rate, pending vs. overdue counts, focus minutes distribution, and habit consistency.
- **Recharts Visualizations:** Past 7 days focus duration area chart and category distribution bar chart.
- **Productivity Index (0-100):** Weighted multi-factor score rewarding velocity and habit chains while penalizing delays.
- **Dynamic Smart Insights:** Short, actionable tips generated directly from the user's live data.

### G. Smart Time Management
- **Overload Detection:** Compares planned durations plus buffers against available working hours.
- **Overcapacity Warnings:** Computes exact overload minutes and offers two or more practical suggestions (e.g. deferring lower-priority tasks, splitting large sessions).

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 19, TypeScript, Vite 8, Tailwind CSS v4, Lucide React, Recharts, Canvas-Confetti |
| **Backend** | Python 3.11, FastAPI, Uvicorn, Pydantic v2 |
| **Database** | SQLite3 (`lifepilot.db`) with automatic schema initialization and demo data seeder |
| **AI Integration** | Google Gemini 2.5 Flash with deterministic Smart Heuristic fallback |
| **Design System** | Clean SaaS Light Theme + Dark Mode with system preference detection |

---

## 📡 REST API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/tasks` | Get tasks with search, category, priority, status filters & sorting |
| `POST` | `/api/tasks` | Create new task with validation |
| `PATCH` | `/api/tasks/{id}` | Update task details or mark complete |
| `POST` | `/api/tasks/{id}/toggle` | Toggle task completion status |
| `DELETE` | `/api/tasks/{id}` | Delete task |
| `GET` | `/api/tasks/recommendation/next` | Return the AI-recommended next task |
| `GET` | `/api/planner/today` | Fetch daily schedule, overload status & practical suggestions |
| `POST` | `/api/planner/generate` | Trigger AI / heuristic schedule generation |
| `GET` | `/api/habits` | Get all habits with real streaks and 7-day logs |
| `POST` | `/api/habits/{id}/toggle` | Toggle habit completion for a specific date |
| `GET` | `/api/focus/sessions` | Retrieve focus session history |
| `POST` | `/api/focus/sessions` | Record completed focus session |
| `POST` | `/api/assistant/chat` | Conversational productivity copilot |
| `POST` | `/api/assistant/breakdown` | Decompose high-level goal into actionable subtasks |
| `POST` | `/api/assistant/import-subtasks`| Bulk import decomposed subtasks into database |
| `GET` | `/api/analytics/overview` | Aggregate completion rates, focus time, and smart insights |
| `GET` / `PATCH` | `/api/settings` | Get / update user settings, hours, and API keys |
| `POST` | `/api/demo/reset` | Reset database to realistic demo data |
| `POST` | `/api/demo/clear` | Clear all user data |
