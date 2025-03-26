from playwright.sync_api import sync_playwright, Error as PlaywrightError
from bs4 import BeautifulSoup


def get_local_instances():
    ## Todo: Add local searxng integration
    pass

def get_online_instances():
    html_content = None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            try:
                page = browser.new_page()
                page.goto("https://searx.space/")
                html_content = page.content()
            except Exception as page_error:
                print("Error during page navigation or content extraction:",
                      page_error)
                return []
            finally:
                browser.close()
    except PlaywrightError as pw_error:
        print("Error initializing Playwright:", pw_error)
        return []
    except Exception as e:
        print("Unexpected error during Playwright session:", e)
        return []

    if html_content is None:
        print("No HTML content retrieved.")
        return []

    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        rows = soup.find_all('tr')
        sites = []
        for row in rows:
            url_cell = row.find('td', class_='column-url')
            if url_cell:
                anchor = url_cell.find('a')
                if anchor and anchor.has_attr('href'):
                    url = anchor['href']
                    if url.startswith('http'):
                        sites.append(url)
        # Remove duplicates while preserving order
        unique_sites = []
        for site in sites:
            if site not in unique_sites:
                unique_sites.append(site)
        return unique_sites
    except Exception as parse_error:
        print("Error processing HTML content:", parse_error)
        return []
