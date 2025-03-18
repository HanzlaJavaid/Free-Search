from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from ClientSearch import search_query  # Ensure the function is accessible

app = FastAPI(title="Search Service")


class SearchResult(BaseModel):
    source: str
    link: str
    context: str


@app.get("/search", response_model=List[SearchResult])
def search(query: str, max_results: int, max_content: int):
    """
    Endpoint to search for a query and return results with additional context.
    """
    try:
        results = search_query(
            query, max_results,
            max_content)  # Ensure this function returns a list of tuples/lists
        if not results:
            raise HTTPException(status_code=404, detail="No results found")
        return [
            SearchResult(source=src, link=lk, context=ctx)
            for src, lk, ctx in results
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11235)
