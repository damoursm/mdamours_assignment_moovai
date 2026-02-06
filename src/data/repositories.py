from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime, timedelta
import json
import hashlib
from pathlib import Path

from src.data.models import AnalysisRecord, RequestHistory, CachedData, AgentConfiguration


class BaseRepository(ABC):
    @abstractmethod
    def save(self, entity): pass

    @abstractmethod
    def get(self, id: str): pass

    @abstractmethod
    def delete(self, id: str): pass


class AnalysisRepository:
    """Repository pour les analyses."""

    def __init__(self, storage_path: str = "data/analyses"):
        self.path = Path(storage_path)
        self.path.mkdir(parents=True, exist_ok=True)

    def save(self, record: AnalysisRecord) -> str:
        file_path = self.path / f"{record.id}.json"
        file_path.write_text(record.model_dump_json(indent=2))
        return record.id

    def get(self, id: str) -> Optional[AnalysisRecord]:
        file_path = self.path / f"{id}.json"
        if file_path.exists():
            return AnalysisRecord.model_validate_json(file_path.read_text())
        return None

    def get_by_product(self, product_name: str, limit: int = 10) -> List[AnalysisRecord]:
        results = []
        for file in self.path.glob("*.json"):
            record = AnalysisRecord.model_validate_json(file.read_text())
            if record.product_name.lower() == product_name.lower():
                results.append(record)
        return sorted(results, key=lambda x: x.created_at, reverse=True)[:limit]

    def delete(self, id: str) -> bool:
        file_path = self.path / f"{id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False


class CacheRepository:
    """Repository pour le cache."""

    def __init__(self, storage_path: str = "data/cache", default_ttl_hours: int = 24):
        self.path = Path(storage_path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.default_ttl = timedelta(hours=default_ttl_hours)

    @staticmethod
    def _generate_key(tool_name: str, input_data: str) -> str:
        input_hash = hashlib.md5(input_data.encode()).hexdigest()[:12]
        return f"{tool_name}:{input_hash}"

    def set(self, tool_name: str, input_data: str, data: dict, ttl_hours: Optional[int] = None) -> str:
        key = self._generate_key(tool_name, input_data)
        ttl = timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl

        cached = CachedData(
            key=key,
            data=data,
            expires_at=datetime.now() + ttl,
            source_tool=tool_name
        )

        file_path = self.path / f"{key.replace(':', '_')}.json"
        file_path.write_text(cached.model_dump_json(indent=2))
        return key

    def get(self, tool_name: str, input_data: str) -> Optional[dict]:
        key = self._generate_key(tool_name, input_data)
        file_path = self.path / f"{key.replace(':', '_')}.json"

        if not file_path.exists():
            return None

        cached = CachedData.model_validate_json(file_path.read_text())

        if datetime.now() > cached.expires_at:
            file_path.unlink()
            return None

        cached.hit_count += 1
        file_path.write_text(cached.model_dump_json(indent=2))
        return cached.data

    def clear_expired(self) -> int:
        count = 0
        for file in self.path.glob("*.json"):
            cached = CachedData.model_validate_json(file.read_text())
            if datetime.now() > cached.expires_at:
                file.unlink()
                count += 1
        return count


class ConfigurationRepository:
    """Repository pour les configurations."""

    def __init__(self, storage_path: str = "data/config"):
        self.path = Path(storage_path)
        self.path.mkdir(parents=True, exist_ok=True)

    def save(self, config: AgentConfiguration) -> str:
        config.updated_at = datetime.now()
        file_path = self.path / f"{config.id}.json"
        file_path.write_text(config.model_dump_json(indent=2))
        return config.id

    def get(self, id: str) -> Optional[AgentConfiguration]:
        file_path = self.path / f"{id}.json"
        if file_path.exists():
            return AgentConfiguration.model_validate_json(file_path.read_text())
        return None

    def get_active(self) -> Optional[AgentConfiguration]:
        for file in self.path.glob("*.json"):
            config = AgentConfiguration.model_validate_json(file.read_text())
            if config.is_active:
                return config
        return None

    def list_all(self) -> List[AgentConfiguration]:
        return [
            AgentConfiguration.model_validate_json(f.read_text())
            for f in self.path.glob("*.json")
        ]