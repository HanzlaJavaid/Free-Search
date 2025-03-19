from modals.results import SearchResult
from modals.inputs import SearchQueryParams
from runnables.searchengines import SearXNGEngine
from typing import List

def searxng_query(params: SearchQueryParams) -> List[SearchResult]:
  engine = SearXNGEngine(params)
  articles = engine.fetch_search_results()
  results = []

  for idx, article in enumerate(articles):
      print(
          f"Crawling {idx+1}/{min(params.max_results, len(articles))}: {article.link}")
      results.append(engine.fetch_article_content(article))

  return results
