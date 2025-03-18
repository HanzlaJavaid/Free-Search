from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import time


def search_query(query: str, max_results: int, max_content: int, timeout=6000):
    # Use Playwright to fetch the raw HTML
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(f"https://priv.au/search?q={query}")
        html_content = page.content()
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

    print(result_links)

    # For each retrieved link, crawl the page to get contents
    results_with_context = []
    # Only crawl the first 3 links
    for source, link in result_links[:max_results]:
        try:
            # Use Playwright to crawl the page
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                context = browser.new_context()
                page = context.new_page()

                # Navigate to the URL
                page.goto(link, wait_until="domcontentloaded", timeout=timeout)

                # Wait for the page to load completely
                page.wait_for_load_state("networkidle", timeout=timeout)
                time.sleep(2)  # Additional wait to ensure JavaScript execution

                # Extract the page content
                page_content = page.content()

                # Parse the content with BeautifulSoup
                content_soup = BeautifulSoup(page_content, 'html.parser')

                # Remove script, style elements, and unwanted tags
                for tag in content_soup(
                    ["script", "style", "meta", "link", "noscript"]):
                    tag.decompose()

                # Extract text from the body
                body = content_soup.find('body')
                if body:
                    # Get all text from the body and clean it up
                    text_content = body.get_text(separator=' ', strip=True)
                    # Normalize whitespace
                    text_content = ' '.join(text_content.split())
                    # Truncate if too long (first 1000 characters)
                    context_text = text_content[:max_content] + "..." if len(
                        text_content) > max_content else text_content
                else:
                    context_text = "No content could be extracted"

                browser.close()

                results_with_context.append((source, link, context_text))

        except Exception as e:
            print(f"Error crawling {link}: {str(e)}")
            results_with_context.append(
                (source, link, f"Error fetching content: {str(e)}"))

    return results_with_context


def main():
    while True:
        query = input("Enter your search query (or type 'exit' to quit): ")
        if query.lower() == 'exit':
            print("Exiting...")
            break

        results = search_query(query, 3, 500)
        if results:
            print("\nSearch Results:")
            for source, link, context in results:
                print(f"{source}: {link}\n  Context: {context}\n")
        else:
            print("No results found.")


if __name__ == "__main__":
    main()
