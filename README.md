# Tradeskee — AI Stock Analysis (Final Year Project)

This repository contains the Tradeskee backend (FastAPI) and frontend (React) for research and demonstration purposes.

Quick Start
1. Copy environment template and edit locally:

    ```bash
    cp .env.example .env
    # Edit .env as needed (do NOT commit)
    ```

2. Create and activate a local Python virtualenv (recommended):

    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

3. Run the backend (development):

    ```bash
    uvicorn src.main:app --reload
    ```

4. Start the frontend (in a separate terminal):

    ```bash
    cd tradely
    npm install
    npm start
    ```

Notes
- Do not commit a real `.env` with secrets — use `.env.example` as the template.
- The project expects a running MongoDB for full functionality. CI uses a lightweight test DB configuration.
- For production deployment, review `src/core/config.py` for keys to set and recommended production changes.

Status
- This is a university project: working prototype, not production hardened. See `FYP_Tradeskee_Final_Report_Gavin_Skehan_21440824.pdf` for details.

Contact
- For questions, open an issue or reach out to the repository owner.