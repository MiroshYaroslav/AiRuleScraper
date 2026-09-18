import httpx
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)


async def find_internal_links(base_url: str) -> set[str]:
    logger.info(f"Crawling for links on: {base_url}")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AiRuleCrawler/1.0"
    }
    links = set()
    domain = urlparse(base_url).netloc

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
            response = await client.get(base_url, headers=headers)
            if response.status_code != 200:
                logger.error(f"Crawler failed to fetch {base_url}")
                return links

            soup = BeautifulSoup(response.text, "lxml")

            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                full_url = urljoin(base_url, href)

                full_url = full_url.split("#")[0]
                if urlparse(full_url).netloc == domain:
                    links.add(full_url)

            logger.info(f"Found {len(links)} internal links.")
            return links
    except Exception as e:
        logger.error(f"Crawler error: {e}", exc_info=True)
        return links
