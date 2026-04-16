import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

TIMEOUT = 15


def validate_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def scrape_page(url: str) -> str:
    """Fetch and extract meaningful text from a recipe page."""
    if not validate_url(url):
        raise ValueError(f"Invalid URL: {url}")

    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("Request timed out. The page took too long to respond.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Could not connect to the URL. Check your internet connection.")
    except requests.exceptions.HTTPError as e:
        raise RuntimeError(f"HTTP error {e.response.status_code} when fetching the page.")

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove non-content tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form", "ads"]):
        tag.decompose()

    # Try to focus on the main content area
    main_content = (
        soup.find("main")
        or soup.find("article")
        or soup.find(class_=re.compile(r"recipe|content|post", re.I))
        or soup.body
    )

    if not main_content:
        raise RuntimeError("Could not extract content from the page.")

    text = main_content.get_text(separator="\n", strip=True)

    # Collapse excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    if len(text.strip()) < 200:
        raise RuntimeError("Page content is too short — this may not be a recipe page.")

    # Limit to 12,000 chars to stay within LLM context limits
    return text[:12000]
