import httpx
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


async def fetch_article_text(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AiRuleScraper/1.0"
    }
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(
                    f"Failed to fetch URL {url}, status: {response.status_code}"
                )
                return ""

            soup = BeautifulSoup(response.text, "lxml")

            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            text = soup.get_text(separator="\n", strip=True)
            return text
    except Exception as e:
        logger.error(f"Error scraping URL {url}: {e}", exc_info=True)
        return ""
