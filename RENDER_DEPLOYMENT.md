# Deploying AI LifePilot to Render

AI LifePilot is configured to deploy to [Render](https://render.com) as a high-performance, single-service application where FastAPI serves both the backend API and the compiled React SPA.

---

## Deployment Option 1: Render Blueprint (Recommended - 1-Click)

Render Blueprints use the included [`render.yaml`](render.yaml) file to automatically configure the service, container environment, and health checks.

1. **Push your code to GitHub** (already configured).
2. Log in to [dashboard.render.com](https://dashboard.render.com).
3. Click **New +** in the top right and select **Blueprint**.
4. Connect your GitHub repository: `dsaidurgabhavani/AI_Life_Pilot`.
5. Render will automatically parse `render.yaml`.
6. When prompted for environment variables, fill in:
   * **`GEMINI_API_KEY`**: Your Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
7. Click **Apply**.
8. Render will build the Docker container and deploy the app at `https://ai-lifepilot-xxxx.onrender.com`.

---

## Deployment Option 2: Render Web Service (Docker)

If you prefer to configure the Web Service manually via Render's dashboard:

1. In Render Dashboard, click **New +** → **Web Service**.
2. Select **Build and deploy from a Git repository** and pick `AI_Life_Pilot`.
3. Configure the following fields:
   * **Name**: `ai-lifepilot`
   * **Region**: Any (e.g., *Oregon (US West)* or *Frankfurt (EU)*)
   * **Branch**: `main`
   * **Runtime**: **Docker**
   * **Plan**: **Free**
4. Under **Advanced** / **Environment Variables**, add:
   | Key | Value | Description |
   | :--- | :--- | :--- |
   | `GEMINI_API_KEY` | `your_actual_gemini_key` | Enables real AI inference |
   | `GEMINI_MODEL` | `gemini-3.1-flash-lite` | Verified fast model |
   | `USER_DEFAULT_TIMEZONE` | `Asia/Kolkata` | Your preferred timezone |
5. Click **Deploy Web Service**.

---

## Deployment Option 3: Render Web Service (Native Python)

If you prefer Render's native Python runtime without Docker:

1. In Render Dashboard, click **New +** → **Web Service**.
2. Select your repository `AI_Life_Pilot`.
3. Configure the settings:
   * **Runtime**: **Python 3**
   * **Build Command**: `./build.sh`
   * **Start Command**: `python -m uvicorn main:app --app-dir backend --host 0.0.0.0 --port $PORT`
   * **Plan**: **Free**
4. Add the Environment Variables (`GEMINI_API_KEY`, `GEMINI_MODEL`).
5. Click **Deploy Web Service**.

---

## Verifying Deployment

Once deployed, Render will provide a public URL like:
`https://ai-lifepilot.onrender.com`

* **Web UI (Frontend SPA)**: `https://ai-lifepilot.onrender.com/`
* **Health Check**: `https://ai-lifepilot.onrender.com/api/health`
* **Swagger API Docs**: `https://ai-lifepilot.onrender.com/docs`
