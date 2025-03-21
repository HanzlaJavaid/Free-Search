from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup


def get_online_instances()
    with sync_playwright() as p:
      browser = p.chromium.launch(headless=False)
      page = browser.new_page()
      page.goto("https://searx.space/")
      html_content = page.content()
      browser.close()
      soup = BeautifulSoup(html_content,'html.parser')
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
