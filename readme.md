# Free Search API

A FastAPI-based search service that performs web searches and retrieves content from search results.

## Overview

This API provides a search endpoint that:
- Performs a search query using a custom search engine
- Retrieves a specified number of top results
- Crawls each result page to extract content
- Returns structured data with source, link, and context for each result

---

## Installation

### Prerequisites
- Python 3.7+
- Playwright
- Beautiful Soup 4
- FastAPI
- Uvicorn

### Setup

1. **Clone this repository**
2. **Install dependencies:**
   ```sh
   pip install fastapi uvicorn pydantic playwright beautifulsoup4
   ```
3. **Install playwright browser:**
   ```sh
   playwright install chromium
   ```

### Usage
```sh
xvfb-run python main.py
```

### API Endpoint

### GET /search

Search for a query and retrieve results with additional context.

| Parameter    | Type     | Required | Default | Description |
|-------------|----------|----------|---------|-------------|
| `query`     | string   | ✅        | -       | The search query string |
| `max_results` | integer | ❌        | `3`     | Number of results to return (range: 1-5) |
| `max_content` | integer | ❌        | `2000`  | Maximum content length per result in characters (range: 100-5000) |

### Response

```json
[
  {
    "source": "source_name",
    "link": "https://example.com/page",
    "context": "Extracted content from the page..."
  }
]
```
### Example Request

```sh
curl "http://localhost:11235/search?query=fastapi+tutorial&max_results=2&max_content=1000"
```

## Public Instance

A publicly accessible demo of this API has been hosted

URL: https://freesearch.replit.app/

