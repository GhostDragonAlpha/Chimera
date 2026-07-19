# -*- coding: utf-8 -*-
"""
scanner_ui.py — Scanner UI data structures for HUD display.

Per Scanner_UI_Display graph (26 answers). Defines the data model that feeds
into the UE5 UMG ScannerInfoPanel widget.

Q1:  Diegetic instrument readout, not textbook popup.
Q3:  Feels like in-world instrument readout, not a menu screen.
Q4:  Built with existing UMG TextBlock + Image widgets.
Q8:  Accessible: screen-reader friendly text, pattern fallback for color.
Q9:  Audio deferred to v2, v1 text-only.
Q15: Derived from Educational_Scanner Q10 gap.
Q16: No conflict with Verb_Look description overlay.
Q23: Serves educational RPG goal — player learns real science.
Q26: Terminal is PLAYER LEARNING.

UI layout per graph:
  ┌─────────────────────────────┐
  │  [Geology]  ⛰️              │  (domain icon + tag)
  │  Cross-bedding in the       │
  │  sandstone — ancient dune   │  (educational text)
  │  fields, now stone.         │
  │  ─────────────────────────  │
  │  ████████░░░░  80%          │  (scan progress bar)
  │  Scan radius: 500m          │  (stats line)
  └─────────────────────────────┘
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict, List, Any
import time


class ScanState(Enum):
    """Visual state of the scanner UI overlay."""
    IDLE = "idle"              # No scan in progress, no results displayed
    TARGETING = "targeting"    # Reticle active, targeting environment
    SCANNING = "scanning"      # Scan in progress, progress bar filling
    RESULT = "result"          # Scan complete, result displayed
    NO_DETECTION = "no_detection"  # Nothing scannable in crosshair
    ERROR = "error"            # Hardware error (durability depleted)
    UPGRADE = "upgrade"        # New upgrade unlocked


@dataclass
class UIStyle:
    """
    Visual styling for the scanner HUD panel.

    Q8:  Font size and contrast accessible.
    Q11: Color-coded states need pattern fallback.
    Q12: Accommodates text expansion for localization (German noun-compounds).
    """

    # Colors (RGBA 0-1 range for UE5 linear color)
    geology_color: tuple = (0.6, 0.4, 0.2, 1.0)    # Brown/earth
    weather_color: tuple = (0.2, 0.5, 0.8, 1.0)     # Blue/sky
    astronomy_color: tuple = (0.3, 0.2, 0.6, 1.0)   # Purple/space
    environment_color: tuple = (0.3, 0.8, 0.3, 1.0) # Green/ambient
    deep_color: tuple = (0.9, 0.6, 0.1, 1.0)        # Gold/deep observation
    error_color: tuple = (0.8, 0.2, 0.2, 1.0)       # Red/error
    idle_color: tuple = (0.5, 0.5, 0.5, 1.0)        # Gray/idle
    upgrade_color: tuple = (0.9, 0.8, 0.1, 1.0)     # Gold/upgrade

    # Patterns for colorblind accessibility (Q8)
    # Each domain has a distinct pattern/texture identifier for UMG Image
    domain_patterns: Dict[str, str] = field(default_factory=lambda: {
        "geology": "Pattern_Stripes_Diagonal",
        "weather": "Pattern_Dots",
        "astronomy": "Pattern_Stars",
        "environment": "Pattern_Grid",
        "deep_geology": "Pattern_Chevron",
        "fossil": "Pattern_Bones",
        "mineral": "Pattern_Crystals",
    })

    # Font
    font_size_title: int = 16
    font_size_body: int = 14
    font_size_detail: int = 12
    font_face: str = "Monospace"  # Scientific instrument feel (Q3)

    # Layout
    panel_width: int = 400
    panel_height: int = 300
    panel_margin: int = 20
    text_padding: int = 8


@dataclass
class ScanProgressInfo:
    """
    Scan progress indicator data.

    Q10: Q9 says audio deferred to v2. Progress is visual only in v1.
    """
    is_scanning: bool = False
    progress: float = 0.0          # 0.0 to 1.0
    estimated_time_remaining: float = 0.0
    start_time: float = 0.0


@dataclass
class TargetReticleData:
    """
    Targeting reticle state — appears when player aims the scanner.

    Q3: Feels like in-world instrument readout.
    """
    is_active: bool = False
    has_target: bool = False
    target_name: str = ""
    target_domain: str = ""
    target_distance: float = 0.0
    reticle_size: float = 32.0  # Pixels
    is_in_scan_range: bool = True


@dataclass
class KnowledgeLogEntry:
    """
    Single entry in the knowledge log — persistent scan record.

    Q26: Terminal is PLAYER LEARNING. The log records what the player learned.
    """
    timestamp: float = 0.0
    domain: str = ""
    text: str = ""
    is_deep: bool = False
    category: str = ""


@dataclass
class ScanResultPanelData:
    """
    The main scan result panel — displayed after a successful scan.

    Q1:  Science as natural readout, not textbook popup.
    Q15: Fills the gap identified in Educational_Scanner Q10.
    """

    # Display state
    is_visible: bool = False
    state: ScanState = ScanState.IDLE

    # Scan result content
    domain_tag: str = ""            # "[Geology]", "[Weather]", etc.
    domain_icon: str = ""           # Icon path for UMG Image widget
    educational_text: str = ""      # The main educational content
    sub_category: str = ""          # Rock type / weather / constellation name
    gameplay_advice: Optional[str] = None  # Q2: actionable gameplay info

    # Domain color for panel tinting (Q8: pattern fallback for color)
    domain_color: tuple = (0.5, 0.5, 0.5, 1.0)
    domain_pattern: str = ""        # For colorblind accessibility

    # Timing
    display_duration: float = 8.0   # Seconds to show result
    displayed_at: float = 0.0
    is_deep_observation: bool = False  # Gold border for deep scans (Q11)

    # Progress
    progress: ScanProgressInfo = field(default_factory=ScanProgressInfo)

    # Reticle
    reticle: TargetReticleData = field(default_factory=TargetReticleData)

    # Audio cues (data for UE5 MetaSound system, Q9 deferred to v2)
    audio_cue: str = ""             # Activation/scan/completion/error
    audio_tone: str = "mid"         # low=geology, mid=weather, high=astronomy

    # Stats line
    stats_line: str = ""            # e.g., "Scan radius: 500m | Durability: 85%"


@dataclass
class ScannerInfoPanelData:
    """
    Full HUD scanner panel state — the top-level UI container.

    Q4:  Can be built with existing UMG TextBlock + Image widgets.
    Q16: No conflict with Verb_Look description overlay (separate HUD region).
    Q23: Directly serves the educational RPG goal.
    """

    # Visibility
    is_visible: bool = False
    panel_opacity: float = 1.0

    # Current result
    current_scan: ScanResultPanelData = field(default_factory=ScanResultPanelData)

    # Knowledge log (persistent across session)
    knowledge_log: List[KnowledgeLogEntry] = field(default_factory=list)
    max_log_entries: int = 50

    # History overlay (recent scans for quick reference)
    show_history: bool = False
    recent_scans: List[ScanResultPanelData] = field(default_factory=list)
    max_history: int = 10

    # Notification queue (upgrade unlocks, achievements, etc.)
    notifications: List[str] = field(default_factory=list)

    # Style
    style: UIStyle = field(default_factory=UIStyle)

    # Upgrade notification
    upgrade_notification: Optional[str] = None
    upgrade_display_time: float = 0.0

    # ─── State management ──────────────────────────────────────────────────

    def show_scan_result(self, domain: str, text: str, sub_category: str = "",
                         is_deep: bool = False, gameplay_advice: Optional[str] = None,
                         audio_tone: str = "mid") -> None:
        """
        Populate panel with a scan result.

        Q1:  Science as natural readout.
        Q26: Each scan is a teachable moment reaching PLAYER LEARNING.
        """
        style = self.style

        # Determine display properties from domain
        domain_tag = {
            "geology": "[Geology]",
            "deep_geology": "[Geology Detail]",
            "weather": "[Weather]",
            "astronomy": "[Astronomy]",
            "constellation": "[Astronomy]",
            "environment": "[Environment]",
            "fossil": "[Fossil]",
            "mineral": "[Mineral]",
            "lifeform": "[Lifeform]",
        }.get(domain, "[Scan]")

        domain_color = {
            "geology": style.geology_color,
            "deep_geology": style.deep_color,
            "weather": style.weather_color,
            "astronomy": style.astronomy_color,
            "constellation": style.astronomy_color,
            "environment": style.environment_color,
        }.get(domain, style.idle_color)

        domain_pattern = style.domain_patterns.get(domain, "Pattern_Grid")
        domain_icon = f"Icon_{domain.capitalize()}" if domain else ""

        self.current_scan = ScanResultPanelData(
            is_visible=True,
            state=ScanState.RESULT,
            domain_tag=domain_tag,
            domain_icon=domain_icon,
            educational_text=text,
            sub_category=sub_category,
            gameplay_advice=gameplay_advice,
            domain_color=domain_color,
            domain_pattern=domain_pattern,
            display_duration=8.0,
            displayed_at=time.time(),
            is_deep_observation=is_deep,
            audio_tone=audio_tone,
            stats_line=self._build_stats_line(),
        )

        # Record in knowledge log
        self.knowledge_log.append(KnowledgeLogEntry(
            timestamp=time.time(),
            domain=domain,
            text=text,
            is_deep=is_deep,
            category=sub_category or domain,
        ))
        if len(self.knowledge_log) > self.max_log_entries:
            self.knowledge_log = self.knowledge_log[-self.max_log_entries:]

        # Record in recent history
        self.recent_scans.append(self.current_scan)
        if len(self.recent_scans) > self.max_history:
            self.recent_scans = self.recent_scans[-self.max_history:]

    def show_scanning_progress(self) -> None:
        """Show scanning-in-progress state with progress bar."""
        self.current_scan.state = ScanState.SCANNING
        self.current_scan.is_visible = True
        self.current_scan.progress = ScanProgressInfo(
            is_scanning=True,
            progress=0.0,
            estimated_time_remaining=2.0,
            start_time=time.time(),
        )

    def show_no_detection(self) -> None:
        """Show no-detection feedback when nothing scannable in crosshair."""
        self.current_scan.state = ScanState.NO_DETECTION
        self.current_scan.is_visible = True
        self.current_scan.educational_text = "No detectable features in range."
        self.current_scan.domain_color = self.style.error_color
        self.current_scan.audio_cue = "error"
        self.current_scan.displayed_at = time.time()

    def show_upgrade_unlock(self, upgrade_name: str) -> None:
        """Display upgrade unlock notification."""
        self.upgrade_notification = upgrade_name
        self.upgrade_display_time = time.time()
        self.notifications.append(f"Scanner upgrade: {upgrade_name}")

    def clear_result(self) -> None:
        """Clear the current scan result from display."""
        self.current_scan = ScanResultPanelData()
        self.upgrade_notification = None

    def _build_stats_line(self) -> str:
        """Build the stats line from current config."""
        return ""  # Populated by the progression system

    def to_dict(self) -> Dict[str, Any]:
        """Serializable state for save/restore."""
        return {
            "knowledge_log": [
                {
                    "timestamp": e.timestamp,
                    "domain": e.domain,
                    "text": e.text,
                    "is_deep": e.is_deep,
                    "category": e.category,
                }
                for e in self.knowledge_log
            ],
            "recent_scans": [
                {
                    "domain_tag": s.domain_tag,
                    "educational_text": s.educational_text,
                    "sub_category": s.sub_category,
                    "is_deep_observation": s.is_deep_observation,
                }
                for s in self.recent_scans
            ],
        }
