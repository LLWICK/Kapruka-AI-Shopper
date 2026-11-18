frontend -
uv run --active streamlit run frontend/frontend.py

backend -
uv run --active python -m uvicorn main:app --reload --port 8000
