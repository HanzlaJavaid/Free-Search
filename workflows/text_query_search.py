import concurrent.futures
import time
from modals.results import SearchResult
from modals.inputs import SearchQueryParams
from runnables.searchengines import SearXNGEngine
from typing import List


def searxng_query(params: SearchQueryParams) -> List[SearchResult]:
    """
    Basic search query to publicly available SearXNG instances,
    crawling results in parallel using threading.
    """
    engine = SearXNGEngine(params)
    engine.build()
    articles = engine.fetch_search_results()

    articles_to_crawl = articles[:params.max_results]
    num_to_crawl = len(articles_to_crawl)

    if not articles_to_crawl:
        print("No articles found or max_results is 0.")
        return []

    print(
        f"Found {len(articles)} results. Starting parallel crawl for the first {num_to_crawl} articles..."
    )

    results = []
    start_time = time.time()  # Optional: Start timing

    num_workers = min(10, num_to_crawl)

    with concurrent.futures.ThreadPoolExecutor(
            max_workers=num_workers) as executor:
        try:
            results_iterator = executor.map(engine.fetch_article_content,
                                            articles_to_crawl)
            results = list(results_iterator)

        except Exception as e:
            print(f"An error occurred during parallel crawling: {e}")

    end_time = time.time()  # Optional: End timing
    print(
        f"Finished crawling {len(results)} articles in {end_time - start_time:.2f} seconds."
    )

    return results
