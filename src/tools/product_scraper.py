from typing import Dict, Any, List, Optional
from langchain.tools import tool
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import random

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
    platforms: List[str] = ["amazon", "walmart", "target", "bestbuy", "costco"]


class ProductScraperService:
    """Product scraping service with business logic."""

    def __init__(self, config: Optional[ProductScraperConfig] = None):
        self.config = config or ProductScraperConfig()
        self.logger = logging.getLogger(f"{__name__}.ProductScraperService")

    def _simulate_platform_data(self, product_name: str, platform: str) -> Dict[str, Any]:
        """Simulate platform data (replace with real scraping)."""
        base_prices = {
            "amazon": 45.99,
            "walmart": 42.99,
            "target": 47.99,
            "bestbuy": 49.99,
            "costco": 39.99
        }
        base_price = base_prices.get(platform, 47.99)
        variation = random.uniform(-5, 5)

        return {
            "platform": platform,
            "price": round(base_price + variation, 2),
            "availability": random.choice(["In Stock", "Limited Stock", "Available in 3 days"]),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "review_count": random.randint(50, 2000),
            "shipping": random.choice(["Free", "$4.99", "$2.99"])
        }

    def _detect_category(self, product_name: str) -> str:
        """Detect product category."""
        categories = {
            "earbuds": "Electronics/Audio",
            "headphones": "Electronics/Audio",
            "phone": "Electronics/Mobile",
            "computer": "Electronics/Computing",
            "laptop": "Electronics/Computing",
            "watch": "Electronics/Wearables",
            "tv": "Electronics/TV",
        }
        product_lower = product_name.lower()
        for keyword, category in categories.items():
            if keyword in product_lower:
                return category
        return "Electronics/General"

    def _generate_description(self, product_name: str, category: str) -> str:
        """Generate a brief product description."""
        return f"{product_name} - A popular {category.split('/')[-1].lower()} product available across major North American e-commerce platforms."

    def scrape(self, product_name: str) -> ProductInfo:
        """Execute scraping for a product."""
        self.logger.info(f"Scraping product: {product_name}")

        sellers_data = []
        for platform in self.config.platforms[:self.config.max_sellers]:
            try:
                data = self._simulate_platform_data(product_name, platform)
                sellers_data.append({
                    "name": platform.capitalize() if platform != "bestbuy" else "Best Buy",
                    "price": data["price"],
                    "availability": data["availability"],
                    "rating": data["rating"]
                })
            except Exception as e:
                self.logger.warning(f"Failed to scrape {platform}: {e}")

        if not sellers_data:
            raise ToolError("product_scraper", "No platform data available")

        prices = [s["price"] for s in sellers_data]
        avg_price = sum(prices) / len(prices)
        category = self._detect_category(product_name)

        return ProductInfo(
            name=product_name,
            description=self._generate_description(product_name, category),
            average_price=round(avg_price, 2),
            price_range={"min": min(prices), "max": max(prices)},
            availability="In Stock" if any(s["availability"] == "In Stock" for s in sellers_data) else "Limited Stock",
            sellers_count=len(sellers_data),
            category=category,
            top_sellers=sorted(sellers_data, key=lambda x: x["price"])[:5],
            scraped_at=datetime.now().isoformat(),
            confidence_score=min(len(sellers_data) / self.config.max_sellers, 1.0)
        )


@tool
@tool_error_handler("scrape_product_data")
def scrape_product_data(product_name: str) -> Dict[str, Any]:
    """Collect product data from e-commerce sources.

    Analyzes multiple platforms (Amazon, Walmart, Target, Best Buy, Costco) to retrieve:
    - Average price and price range
    - Availability
    - Number of sellers
    - Top sellers with their prices

    Args:
        product_name: The product name to search for

    Returns:
        Dictionary containing all collected product information
    """
    service = ProductScraperService()
    result = service.scrape(product_name)
    return result.model_dump()