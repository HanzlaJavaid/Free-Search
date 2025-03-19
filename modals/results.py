from pydantic import BaseModel

class SearchResult(BaseModel):
  source: str
  link: str
  context: str
