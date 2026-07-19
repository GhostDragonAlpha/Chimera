"""
scanner/__init__.py — Educational Scanner package.

Exports the Scanner class, UI data structures, and progression system.
All content feeds from core/env_education.py per graph specification.
"""

from .scanner import Scanner, ScanResult, ScanDomain, ScannerConfig
from .scanner_ui import ScannerInfoPanelData, ScanResultPanelData, UIStyle, ScanState
from .scanner_progression import ScannerProgression, TierLevel, TIER_STATS, TIER_CATEGORIES

__all__ = [
    "Scanner",
    "ScanResult",
    "ScanDomain",
    "ScannerConfig",
    "ScannerInfoPanelData",
    "ScanResultPanelData",
    "UIStyle",
    "ScanState",
    "ScannerProgression",
    "TierLevel",
    "TIER_STATS",
    "TIER_CATEGORIES",
]
