
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from workflows.graph import run_workflow

app = FastAPI(title="Kapruka AI Shopper API")


class requestModel(BaseModel):
    query: str = Field(min_length=2, max_length=1000)
    thread_id: str = "default-session"
    selected_product_id: Optional[str] = None


    


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/chat")
async def chat(request: requestModel):
    try:
        thread_id = request.thread_id

        
        
        result = await run_workflow(
            query=request.query,
            thread_id=request.thread_id,
            selected_product_id=request.selected_product_id
        )

        
        agent_response = result.get("response", {})
        
        return {
            "query": request.query,
            "thread_id": thread_id,
            **agent_response
        }

    except Exception as exc:
        print(f"Workflow error: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=500,
            detail="The product search workflow failed.",
        ) from exc
