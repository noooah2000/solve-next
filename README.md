# SolveNext

A Python project with FastAPI backend and Streamlit frontend.

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   ```

2. Activate the virtual environment:
   - **macOS/Linux:**
     ```bash
     source .venv/bin/activate
     ```
   - **Windows:**
     ```bash
     .venv\Scripts\activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your API keys in `.env`

## Running the Application

Make sure you have activated your virtual environment:
```bash
source .venv/bin/activate
```

### Backend
```bash
cd backend
uvicorn main:app --reload
```
The API will be available at `http://127.0.0.1:8000`

### Frontend
```bash
cd frontend
streamlit run app.py
```
