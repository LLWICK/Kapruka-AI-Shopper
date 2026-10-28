
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from workflows.graph import run_workflow

app = FastAPI(title="Kapruka AI Shopper API")


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    thread_id: str = "default-session"


    


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def search(request: SearchRequest):
    try:
        thread_id = request.thread_id
        result = await run_workflow(request.query, thread_id)
        
        search = result.get("search_agent_output")
        
        return {
            "query": request.query,
            "products": search.products if search else [],
        }

    except Exception as exc:
        print(f"Workflow error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="The product search workflow failed.",
        ) from exc
