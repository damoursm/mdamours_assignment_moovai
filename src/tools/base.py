from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel
import logging
from functools import wraps
from datetime import datetime


class ToolResult(BaseModel):
    """Résultat standardisé pour tous les outils."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0
    timestamp: str = ""


class ToolError(Exception):
    """Exception personnalisée pour les erreurs d'outils."""
    def __init__(self, tool_name: str, message: str, original_error: Optional[Exception] = None):
        self.tool_name = tool_name
        self.message = message
        self.original_error = original_error
        super().__init__(f"[{tool_name}] {message}")


def tool_error_handler(tool_name: str):
    """Décorateur pour la gestion centralisée des erreurs."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(f"tools.{tool_name}")
            start_time = datetime.now()
            try:
                logger.info(f"Executing {tool_name} with args: {args}, kwargs: {kwargs}")
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                logger.info(f"{tool_name} completed in {execution_time:.2f}ms")
                return result
            except Exception as e:
                logger.error(f"{tool_name} failed: {str(e)}")
                raise ToolError(tool_name, str(e), e)
        return wrapper
    return decorator


def setup_logging():
    """Configure le logging pour les outils."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )