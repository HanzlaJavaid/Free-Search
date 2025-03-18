from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import time
import random


def search_query(query: str,
                 max_results: int,
                 max_content: int,
                 timeout=30000):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            page.goto(f"https://priv.au/search?q={query}", timeout=timeout)
            html_content = page.content()
        except Exception as e:
            print(f"Error during search: {str(e)}")
            browser.close()
            return []
        finally:
            browser.close()

    soup = BeautifulSoup(html_content, 'html.parser')
    articles = soup.find_all('article', class_='result')
    result_links = []

    for article in articles:
        a_tag = article.find('a', class_='url_header')
        if not (a_tag and a_tag.has_attr('href')):
            continue
        link = a_tag['href']

        source = ""
        engines_div = article.find('div', class_='engines')
        if engines_div:
            source_span = engines_div.find('span')
            if source_span:
                source = source_span.get_text(strip=True)

        result_links.append((source, link))

    print(f"Found {len(result_links)} results")

    results_with_context = []

    for idx, (source, link) in enumerate(result_links[:max_results]):
        print(
            f"Crawling {idx+1}/{min(max_results, len(result_links))}: {link}")

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

                    if idx > 0:
                        delay = random.uniform(1, 3)
                        time.sleep(delay)

                    try:
                        response = page.goto(link,
                                             wait_until="domcontentloaded",
                                             timeout=timeout)

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
                                f"Network didn't become idle for {link}, continuing anyway..."
                            )

                        page_content = page.content()

                    except Exception as nav_error:
                        print(
                            f"Navigation error on attempt {attempt+1} for {link}: {str(nav_error)}"
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
                        context_text = text_content[:max_content] + "..." if len(
                            text_content) > max_content else text_content
                    else:
                        context_text = "No content could be extracted"

                    browser.close()
                    results_with_context.append((source, link, context_text))
                    break

            except Exception as e:
                print(
                    f"Error on attempt {attempt+1} crawling {link}: {str(e)}")
                if attempt == 2:
                    results_with_context.append(
                        (source, link, f"Error fetching content: {str(e)}"))

    return results_with_context
