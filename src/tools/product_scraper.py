from typing import Dict, Any, List, Optional
from langchain.tools import tool
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import httpx
from bs4 import BeautifulSoup
import re

from src.tools.base import tool_error_handler, ToolError

logger = logging.getLogger(__name__)


class ProductInfo(BaseModel):
    """Product data structure."""
    name: str
    description: str
    average_price: float
    price_range: Dict[str, float]
    availability: str
    sellers_count: int
    category: str
    top_sellers: List[Dict[str, Any]]
    scraped_at: str
    confidence_score: float = Field(ge=0, le=1)


class ProductScraperConfig(BaseModel):
    """Scraper configuration."""
    max_sellers: int = 10
    include_historical: bool = False
    timeout: float = 30.0


class ProductScraperService:
    """Product scraping service using web scraping."""

    def __init__(self, config: Optional[ProductScraperConfig] = None):
        self.config = config or ProductScraperConfig()
        self.logger = logging.getLogger(f"{__name__}.ProductScraperService")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    async def _search_product_prices(self, product_name: str) -> List[Dict[str, Any]]:
        """Search for product prices using web scraping."""
        sellers = []
        search_query = f"{product_name} price buy"

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                url = f"https://html.duckduckgo.com/html/?q={search_query}"
                response = await client.get(url, headers=self.headers)
                soup = BeautifulSoup(response.text, "html.parser")

                results = soup.select(".result")
                for result in results[:self.config.max_sellers]:
                    title_elem = result.select_one(".result__title")
                    snippet_elem = result.select_one(".result__snippet")
                    url_elem = result.select_one(".result__url")

                    if not title_elem:
                        continue

                    title = title_elem.get_text().strip()
                    snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                    source_url = url_elem.get_text().strip() if url_elem else ""

                    # Extract price from snippet
                    price = self._extract_price(snippet + " " + title)
                    if price:
                        seller_name = self._extract_seller_name(source_url, title)
                        sellers.append({
                            "name": seller_name,
                            "price": price,
                            "availability": self._extract_availability(snippet),
                            "rating": self._extract_rating(snippet),
                            "source": source_url
                        })
            except Exception as e:
                self.logger.warning(f"Search failed: {e}")

        return sellers

    def _extract_price(self, text: str) -> Optional[float]:
        """Extract price from text."""
        patterns = [
            r"\$(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)",
            r"(\d{1,4}(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|dollars?)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                price_str = matches[0].replace(",", "")
                try:
                    price = float(price_str)
                    if 0.01 < price < 100000:  # Reasonable price range
                        return round(price, 2)
                except ValueError:
                    continue
        return None

    def _extract_seller_name(self, url: str, title: str) -> str:
        """Extract seller name from URL or title."""
        known_sellers = {
            "amazon": "Amazon",
            "walmart": "Walmart",
            "target": "Target",
            "bestbuy": "Best Buy",
            "costco": "Costco",
            "ebay": "eBay",
            "newegg": "Newegg"
        }
        url_lower = url.lower()
        for key, name in known_sellers.items():
            if key in url_lower:
                return name
        # Extract domain name
        domain_match = re.search(r"(?:www\.)?([a-zA-Z0-9-]+)\.", url)
        if domain_match:
            return domain_match.group(1).capitalize()
        return "Online Retailer"

    def _extract_availability(self, text: str) -> str:
        """Extract availability from text."""
        text_lower = text.lower()
        if "out of stock" in text_lower or "unavailable" in text_lower:
            return "Out of Stock"
        if "limited" in text_lower or "few left" in text_lower:
            return "Limited Stock"
        if "in stock" in text_lower or "available" in text_lower:
            return "In Stock"
        return "Check Website"

    def _extract_rating(self, text: str) -> Optional[float]:
        """Extract rating from text."""
        patterns = [
            r"(\d(?:\.\d)?)\s*(?:out of\s*5|/5|stars?)",
            r"rating[:\s]+(\d(?:\.\d)?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                rating = float(match.group(1))
                if 0 <= rating <= 5:
                    return round(rating, 1)
        return None

    async def _detect_category_from_web(self, product_name: str) -> str:
        """Detect product category by scraping web search results."""
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                query = f"{product_name} category type product"
                url = f"https://html.duckduckgo.com/html/?q={query}"
                response = await client.get(url, headers=self.headers)
                soup = BeautifulSoup(response.text, "html.parser")

                snippets = soup.select(".result__snippet")
                combined_text = " ".join(
                    s.get_text().strip() for s in snippets[:5]
                ).lower()

                # Extract category-like phrases from results
                category_indicators = self._extract_category_phrases(combined_text, product_name)
                if category_indicators:
                    return category_indicators

            except Exception as e:
                self.logger.warning(f"Category detection failed: {e}")

        return "General Product"

    def _extract_category_phrases(self, text: str, product_name: str) -> str:
        """Extract category phrases from scraped text."""
        # Common category indicator patterns
        patterns = [
            rf"{product_name.lower()}\s+is\s+(?:a|an)\s+([a-z\s]+?)(?:\.|,|that)",
            r"category[:\s]+([a-z\s/&]+?)(?:\.|,|\s{2})",
            r"(?:type|kind)\s+of\s+([a-z\s]+?)(?:\.|,|\s{2})",
            r"(?:shop|buy|browse)\s+([a-z\s]+?)(?:\s+at|\s+from|\.|,)",
            r"in\s+(?:the\s+)?([a-z\s]+?)\s+(?:category|section|department)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                category = match.group(1).strip()
                # Clean up and capitalize
                if 2 < len(category) < 50:
                    return category.title()

        # Fallback: extract most relevant noun phrases
        return self._infer_category_from_context(text)

    def _infer_category_from_context(self, text: str) -> str:
        """Infer category from context when no explicit category found."""
        # Find frequently mentioned product-related terms
        words = re.findall(r'\b[a-z]{4,}\b', text)
        word_freq = {}

        # Filter out common stopwords and count
        stopwords = {
            "this", "that", "with", "from", "have", "will", "your", "about",
            "more", "when", "which", "their", "been", "would", "could", "should",
            "price", "prices", "buy", "shop", "product", "products", "best",
            "review", "reviews", "online", "store", "stores", "sale", "deal"
        }

        for word in words:
            if word not in stopwords:
                word_freq[word] = word_freq.get(word, 0) + 1

        # Get top terms as category hint
        if word_freq:
            top_terms = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:2]
            return " ".join(term.title() for term, _ in top_terms)

        return "General Product"

    async def _scrape_description(self, product_name: str) -> str:
        """Scrape product description from web."""
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            try:
                query = f"{product_name} product description features"
                url = f"https://html.duckduckgo.com/html/?q={query}"
                response = await client.get(url, headers=self.headers)
                soup = BeautifulSoup(response.text, "html.parser")

                snippets = soup.select(".result__snippet")
                if snippets:
                    return snippets[0].get_text().strip()[:300]
            except Exception as e:
                self.logger.warning(f"Description scrape failed: {e}")

        return f"{product_name} - Product information scraped from online sources."

    async def scrape_async(self, product_name: str) -> ProductInfo:
        """Execute scraping for a product."""
        self.logger.info(f"Scraping product: {product_name}")

        sellers_data = await self._search_product_prices(product_name)
        description = await self._scrape_description(product_name)
        category = await self._detect_category_from_web(product_name)

        if not sellers_data:
            # Return minimal data instead of raising error
            self.logger.warning(f"No price data found for: {product_name}, returning minimal info")
            return ProductInfo(
                name=product_name,
                description=description if description else f"No detailed information found for {product_name}",
                average_price=0.0,
                price_range={"min": 0.0, "max": 0.0},
                availability="Unknown",
                sellers_count=0,
                category=category,
                top_sellers=[],
                scraped_at=datetime.now().isoformat(),
                confidence_score=0.0
            )

        prices = [s["price"] for s in sellers_data]
        avg_price = sum(prices) / len(prices)

        availability_list = [s["availability"] for s in sellers_data]
        if "In Stock" in availability_list:
            overall_availability = "In Stock"
        elif "Limited Stock" in availability_list:
            overall_availability = "Limited Stock"
        else:
            overall_availability = "Check Website"

        return ProductInfo(
            name=product_name,
            description=description,
            average_price=round(avg_price, 2),
            price_range={"min": min(prices), "max": max(prices)},
            availability=overall_availability,
            sellers_count=len(sellers_data),
            category=category,
            top_sellers=sorted(sellers_data, key=lambda x: x["price"])[:5],
            scraped_at=datetime.now().isoformat(),
            confidence_score=min(len(sellers_data) / self.config.max_sellers, 1.0)
        )

    def scrape(self, product_name: str) -> ProductInfo:
        """Synchronous wrapper for scrape_async."""
        import asyncio
        return asyncio.run(self.scrape_async(product_name))


@tool
@tool_error_handler("scrape_product_data")
def scrape_product_data(product_name: str) -> Dict[str, Any]:
    """Collect product data from e-commerce sources using web scraping.

    Scrapes the web to retrieve:
    - Average price and price range from multiple sellers
    - Availability status
    - Seller information with prices
    - Product descriptions

    Args:
        product_name: The product name to search for

    Returns:
        Dictionary containing all collected product information
    """
    service = ProductScraperService()
    result = service.scrape(product_name)
    return result.model_dump()