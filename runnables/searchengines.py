from modals.inputs import SearchQueryParams
from modals.results import SearchResult
from modals.types import Article

from typing import List
import time
import random

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, Page, Browser, TimeoutError as PlaywrightTimeoutError

from runnables.builders import get_online_instances

import logging
from typing import List, Optional

# Setup basic logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SearXNGEngine:
    """
    Interface to conntect with SearXNG
    """

    def __init__(self, params: SearchQueryParams):
        self.params = params
        self.instances = []

    def build(self):
        self.instances = get_online_instances()

    def _scrape_page(self, soup: BeautifulSoup) -> List[Article]:
        """Helper function to extract articles from a BeautifulSoup object."""
        articles_found = soup.find_all('article', class_='result')
        result_links = []

        if not articles_found:
            logger.debug("No 'article.result' elements found on page content.")
            return []  # No articles found is not an error, just no results

        for article in articles_found:
            a_tag = article.find('a', class_='url_header')
            if not (a_tag and a_tag.has_attr('href')):
                logger.warning(
                    "Skipping article, missing 'a.url_header' tag or href attribute."
                )
                continue
            link = a_tag['href']

            source = ""
            engines_div = article.find('div', class_='engines')
            if engines_div:
                source_span = engines_div.find('span')
                if source_span:
                    source = source_span.get_text(strip=True)
                else:
                    logger.debug(
                        "Found 'div.engines' but no 'span' inside for an article."
                    )
            else:
                logger.debug("No 'div.engines' found for an article.")

            result_links.append(Article(source=source, link=link))

        return result_links

    def fetch_search_results(self) -> List[Article]:
        """
        Iterates through instances, attempts search, and returns results
        from the first successful attempt that yields articles.
        """
        browser: Optional[
            Browser] = None  # Define browser outside try for access in finally

        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)

                for instance in self.instances:
                    page: Optional[Page] = None
                    logger.info(f"Attempting search on instance: {instance}")
                    try:
                        page = browser.new_page()
                        search_url = f"{instance}/search?q={self.params.query}"
                        logger.debug(f"Navigating to: {search_url}")
                        page.goto(search_url, timeout=self.params.timeout)

                        html_content = page.content()
                        soup = BeautifulSoup(html_content, 'html.parser')

                        scraped_articles = self._scrape_page(soup)

                        if scraped_articles:
                            logger.info(
                                f"Successfully found {len(scraped_articles)} results on {instance}"
                            )
                            return scraped_articles[:self.params.max_results]
                        else:
                            logger.warning(
                                f"Scraping completed on {instance}, but no valid articles found."
                            )

                    except PlaywrightTimeoutError:
                        logger.warning(
                            f"Timeout occurred for instance: {instance}")
                    except PlaywrightException as e:
                        logger.error(
                            f"Playwright error on instance {instance}: {e}")
                    except Exception as e:
                        logger.error(
                            f"Unexpected error during search on instance {instance}: {str(e)}",
                            exc_info=True)
                    finally:
                        if page:
                            try:
                                page.close(
                                )  # Ensure page is closed after each attempt
                                logger.debug(
                                    f"Closed page for instance: {instance}")
                            except PlaywrightException as e:
                                logger.error(
                                    f"Error closing page for instance {instance}: {e}"
                                )

                logger.warning("All instances failed to return results.")
                return []

        except Exception as e:
            logger.critical(
                f"An unexpected critical error occurred outside the instance loop: {e}",
                exc_info=True)
            return []
        finally:
            if browser:
                try:
                    browser.close()
                    logger.info("Browser closed.")
                except Exception as e:
                    logger.error(f"Error closing browser: {e}")

    def fetch_article_content(self, article: Article) -> SearchResult:
        # Try up to 3 times for each link
        for attempt in range(3):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)

                    context = browser.new_context(
                        user_agent=
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                        viewport={
                            "width": 1920,
                            "height": 1080
                        })

                    page = context.new_page()

                    if attempt > 0:
                        delay = random.uniform(1, 3)
                        time.sleep(delay)

                    try:
                        response = page.goto(article.link,
                                             wait_until="domcontentloaded",
                                             timeout=self.params.timeout)

                        if response is None or response.status >= 400:
                            raise Exception(
                                f"Received error status: {response.status if response else 'No response'}"
                            )

                        page.wait_for_timeout(2000)

                        try:
                            page.wait_for_load_state("networkidle",
                                                     timeout=10000)
                        except PlaywrightTimeoutError:
                            print(
                                f"Network didn't become idle for {article.link}, continuing anyway..."
                            )

                        page_content = page.content()

                    except Exception as nav_error:
                        print(
                            f"Navigation error on attempt {attempt+1} for {article.link}: {str(nav_error)}"
                        )
                        if attempt == 2:
                            raise
                        continue

                    content_soup = BeautifulSoup(page_content, 'html.parser')

                    for tag in content_soup(
                        ["script", "style", "meta", "link", "noscript"]):
                        tag.decompose()

                    body = content_soup.find('body')
                    if body:
                        text_content = body.get_text(separator=' ', strip=True)
                        text_content = ' '.join(text_content.split())
                        context_text = text_content[:self.params.
                                                    max_content] + "..." if len(
                                                        text_content
                                                    ) > self.params.max_content else text_content
                    else:
                        context_text = "No content could be extracted"

                    browser.close()
                    return SearchResult(source=article.source,
                                        link=article.link,
                                        context=context_text)
            except Exception as e:
                print(
                    f"Error on attempt {attempt+1} crawling {article.link}: {str(e)}"
                )
                if attempt == 2:
                    return SearchResult(
                        source=article.source,
                        link=article.link,
                        context=f"Error fetching content: {str(e)}")
