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
def search(
    query: str, 
    max_results: int = 3, 
    max_content: int = 2000
):
    """
    Endpoint to search for a query and return results with additional context.

    Parameters:
    - query: The search query string
    - max_results: Number of results to return (1-5, default: 3)
    - max_content: Maximum content length per result (100-5000, default: 2000)
    """
    # Validate max_results
    if max_results < 1 or max_results > 5:
        raise HTTPException(
            status_code=400, 
            detail="max_results must be between 1 and 5"
        )

    # Validate max_content
    if max_content < 100 or max_content > 5000:
        raise HTTPException(
            status_code=400, 
            detail="max_content must be between 100 and 5000"
        )

    try:
        results = search_query(
            query, max_results, max_content)  # Ensure this function returns a list of tuples/lists
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
