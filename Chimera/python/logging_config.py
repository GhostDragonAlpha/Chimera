"""
Logging configuration with structured JSON format, rotation, multiple handlers,
and per-module log level management. Follows config.py logger setup patterns.
"""

import json
import logging
import os
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """Structured JSON log formatter with timestamp, level, message, and context."""

    def format(self, record: logging.LogRecord) -> str:
        entry: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if hasattr(record, 'context') and record.context:
            entry["context"] = record.context
        exc_text = self.formatException(record.exc_info) if record.exc_info else None
        if exc_text and exc_text != "None":
            entry["exception"] = exc_text.strip()
        return json.dumps(entry)


class ConfigurableLogger:
    """Logging manager with structured output, rotation, handlers, and per-module levels."""

    def __init__(self, name: str = "Chimera", base_log_dir: Optional[Path] = None):
        self.logger = logging.getLogger(name)
        self.base_log_dir = base_log_dir or (Path.cwd() / "Saved" / "Logs")
        self._handlers_added: set[str] = set()

    def setup(
        self,
        level: str = "INFO",
        json_format: bool = True,
        max_bytes: int = 10 * 1024 * 1024,
        backup_count: int = 5,
        rotate_by_time: bool = False,
    ) -> None:
        """Configure logger with console + file handlers and optional rotation."""
        self.logger.setLevel(getattr(logging, level.upper(), logging.INFO))

        fmt_cls = JSONFormatter if json_format else logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler
        console = logging.StreamHandler()
        console.setFormatter(fmt_cls)
        self.logger.addHandler(console)
        self._handlers_added.add("console")

        # File handler with rotation
        self.base_log_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.base_log_dir / "chimera.log"

        if rotate_by_time:
            file_handler = TimedRotatingFileHandler(
                log_file, when="midnight", backupCount=backup_count
            )
        else:
            file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)

        file_handler.setFormatter(fmt_cls)
        self.logger.addHandler(file_handler)
        self._handlers_added.add("file")

    def add_network_handler(self, host: str, port: int, fmt: Optional[logging.Formatter] = None) -> None:
        """Add a TCP network handler for remote log aggregation."""
        handler = logging.handlers.SocketHandler(host, port)
        handler.setFormatter(fmt or JSONFormatter())
        self.logger.addHandler(handler)
        self._handlers_added.add(f"network:{host}:{port}")

    def set_module_level(self, module_name: str, level: str) -> None:
        """Set log level for a specific module/sublogger."""
        child = self.logger.getChild(module_name)
        child.setLevel(getattr(logging, level.upper(), logging.INFO))

    def get_module_logger(self, name: str) -> logging.Logger:
        """Get a child logger for a specific module."""
        return self.logger.getLoggerAdapter((name,) if not name.endswith('.logger') else (name[7:],)).logger  # noqa: E731

    def log_structured(self, level: str, message: str, context: dict = None) -> None:
        """Log a structured JSON record with optional context fields."""
        record = self.logger.makeRecord(
            self.logger.name, getattr(logging, level.upper()),
            "unknown", 0, message, (), None
        )
        if context:
            record.context = context
        handler_list = [h for h in self.logger.handlers if isinstance(h, JSONFormatter.__class__)]
        for handler in self.logger.handlers:
            if hasattr(handler, 'formatter') and isinstance(handler.formatter, JSONFormatter):
                print(handler.formatter.format(record))
