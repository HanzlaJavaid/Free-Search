from pydantic import BaseModel

class Article(BaseModel):
  source: str
  link: str