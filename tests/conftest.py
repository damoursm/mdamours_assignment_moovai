import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def sample_product_name():
    return "écouteurs sans fil"


@pytest.fixture
def sample_category():
    return "Electronics/Audio"


@pytest.fixture
def sample_product_data():
    return {
        "name": "écouteurs sans fil",
        "average_price": 49.99,
        "price_range": {"min": 35.00, "max": 75.00},
        "availability": "En stock",
        "sellers_count": 3,
        "category": "Electronics/Audio",
        "top_sellers": [
            {"name": "Amazon", "price": 45.99},
            {"name": "Fnac", "price": 52.99}
        ]
    }


@pytest.fixture
def sample_competitor_data():
    return {
        "category": "Electronics/Audio",
        "competitors": [
            {"name": "Sony", "market_share": 22.0, "price_strategy": "Premium"}
        ],
        "opportunities": ["Segment entrée de gamme sous-exploité"],
        "threats": ["Guerre des prix potentielle"]
    }


@pytest.fixture
def sample_sentiment_data():
    return {
        "product": "écouteurs sans fil",
        "overall_score": 4.2,
        "total_reviews": 1250,
        "sentiment_breakdown": {"positive": 0.78, "negative": 0.12, "neutral": 0.10},
        "recommendation_rate": 0.85,
        "nps_score": 45,
        "key_themes": {"positive": [], "negative": []}
    }