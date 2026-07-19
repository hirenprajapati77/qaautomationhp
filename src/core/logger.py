"""
Shared logger used across every module in the framework.

Why a wrapper instead of calling logging.getLogger() everywhere?
- One consistent log format across API, E2E, ML and RAG suites.
- Easy to redirect all framework logs to a file for CI artifact upload.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

_CONFIGURED = False


def _configure_root_handlers() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    root = logging.getLogger("qa_framework")
    root.setLevel(level)
    root.handlers.clear()

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)

    log_file = os.getenv("LOG_FILE", "").strip()
    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _configure_root_handlers()
    logger = logging.getLogger(f"qa_framework.{name}")
    logger.setLevel(logging.getLogger("qa_framework").level)
    logger.propagate = True
    return logger
