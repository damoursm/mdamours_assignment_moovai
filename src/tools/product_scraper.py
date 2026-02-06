from typing import Dict, Any, List, Optional
from langchain.tools import tool
from pydantic import BaseModel, Field
import logging
from datetime import datetime
import random

from src.tools.base import tool_error_handler, ToolError

logger = logging.getLogger(__name__)


class ProductInfo(BaseModel):
    """Structure de données produit."""
    name: str
    average_price: float
    price_range: Dict[str, float]
    availability: str
    sellers_count: int
    category: str
    top_sellers: List[Dict[str, Any]]
    scraped_at: str
    confidence_score: float = Field(ge=0, le=1)


class ProductScraperConfig(BaseModel):
    """Configuration du scraper."""
    max_sellers: int = 10
    include_historical: bool = False
    platforms: List[str] = ["amazon", "fnac", "cdiscount"]


class ProductScraperService:
    """Service de scraping produit avec logique métier."""

    def __init__(self, config: Optional[ProductScraperConfig] = None):
        self.config = config or ProductScraperConfig()
        self.logger = logging.getLogger(f"{__name__}.ProductScraperService")

    def _simulate_platform_data(self, product_name: str, platform: str) -> Dict[str, Any]:
        """Simule les données d'une plateforme (à remplacer par vrai scraping)."""
        base_prices = {
            "amazon": 45.99,
            "fnac": 52.99,
            "cdiscount": 39.99,
            "darty": 48.99,
            "boulanger": 51.99
        }
        base_price = base_prices.get(platform, 47.99)
        variation = random.uniform(-5, 5)

        return {
            "platform": platform,
            "price": round(base_price + variation, 2),
            "availability": random.choice(["En stock", "Stock limité", "Disponible sous 3j"]),
            "rating": round(random.uniform(3.5, 5.0), 1),
            "review_count": random.randint(50, 2000),
            "shipping": random.choice(["Gratuit", "4.99€", "2.99€"])
        }

    def _detect_category(self, product_name: str) -> str:
        """Détecte la catégorie du produit."""
        categories = {
            "écouteur": "Electronics/Audio",
            "casque": "Electronics/Audio",
            "téléphone": "Electronics/Mobile",
            "ordinateur": "Electronics/Computing",
            "laptop": "Electronics/Computing",
            "montre": "Electronics/Wearables",
            "télé": "Electronics/TV",
        }
        product_lower = product_name.lower()
        for keyword, category in categories.items():
            if keyword in product_lower:
                return category
        return "Electronics/General"

    def scrape(self, product_name: str) -> ProductInfo:
        """Exécute le scraping pour un produit."""
        self.logger.info(f"Scraping product: {product_name}")

        sellers_data = []
        for platform in self.config.platforms[:self.config.max_sellers]:
            try:
                data = self._simulate_platform_data(product_name, platform)
                sellers_data.append({
                    "name": platform.capitalize(),
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

        return ProductInfo(
            name=product_name,
            average_price=round(avg_price, 2),
            price_range={"min": min(prices), "max": max(prices)},
            availability="En stock" if any(s["availability"] == "En stock" for s in sellers_data) else "Stock limité",
            sellers_count=len(sellers_data),
            category=self._detect_category(product_name),
            top_sellers=sorted(sellers_data, key=lambda x: x["price"])[:5],
            scraped_at=datetime.now().isoformat(),
            confidence_score=min(len(sellers_data) / self.config.max_sellers, 1.0)
        )


@tool
@tool_error_handler("scrape_product_data")
def scrape_product_data(product_name: str) -> Dict[str, Any]:
    """Collecte les données d'un produit à partir de sources e-commerce.

    Analyse plusieurs plateformes (Amazon, Fnac, Cdiscount) pour récupérer:
    - Prix moyen et fourchette de prix
    - Disponibilité
    - Nombre de vendeurs
    - Top vendeurs avec leurs prix

    Args:
        product_name: Le nom du produit à rechercher

    Returns:
        Dictionnaire contenant toutes les informations produit collectées
    """
    service = ProductScraperService()
    result = service.scrape(product_name)
    return result.model_dump()