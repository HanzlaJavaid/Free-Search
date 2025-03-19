from pydantic import BaseModel

class SearchQueryParams(BaseModel):
  query: str
  max_results: int
  max_content: int
  timeout: int = 30000
