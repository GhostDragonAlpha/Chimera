# -*- coding: utf-8 -*-
"""
scanner.py — The Educational Scanner.

Implements the Scanner class per Educational_Scanner graph (43 answers).
Wires to env_education.py for all educational content: geology, meteorology,
astronomy, time-of-day, and deep observations.

Spec: ATool_Scanner properties — Durability, ScanRadius, ScanTime, ScanRange,
ScanInterval. Scan() is a manual trigger (active, not passive). Educational
content only fires on deliberate Scan() calls. Targeting uses RayCast-based
actor detection dispatching to the correct domain.

Q3:  Active curiosity — Scan() is manual trigger. deep_geology_observation()
     at 30% trigger rewarding persistence.
Q9:  Multi-domain: geology_prompt(), weather_prompt(), astronomy_prompt(),
     time_prompt(), constellation_observation(), random_observation(),
     environment_report().
Q11: deep_geology_observation() provides deeper facts at 30% trigger.
Q12: weather_prompt("storm") includes predictive weather language.
Q17: Depends on env_education (complete, ready).
Q18: All content is data-driven dictionaries — extendable without code changes.
Q27: Complementary to Verb_Look: look for orientation, scan for education.
Q32: Terminal is PHYSICS/HUMAN — player learns real science verified against
     visible environment.
Q36: Audio states: activation, scanning hum/whine, completion chime per domain,
     error/empty. Geology low, meteorology mid, astronomy high.
"""

import random
import time
from enum import Enum, auto
from typing import Optional, Dict, List, Any

# Educational content source — complete and ready per Q17
from Chimera.core.env_education import (
    geology_prompt,
    deep_geology_observation,
    weather_prompt,
    astronomy_prompt,
    constellation_observation,
    time_prompt,
    random_observation,
    environment_report,
    GEOLOGY_PROMPTS,
    WEATHER_PROMPTS,
    ASTRONOMY_PROMPTS,
    ASTRONOMY_CONSTELLATIONS,
    TIME_PROMPTS,
)


class ScanDomain(Enum):
    """Scientific domain of a scan result. Maps to domain-specific audio tones."""
    GEOLOGY = "geology"         # Low tone
    METEOROLOGY = "weather"     # Mid tone
    ASTRONOMY = "astronomy"      # High tone
    ENVIRONMENT = "environment"  # General ambient
    DEEP_GEOLOGY = "deep_geology"  # Reward for persistence (30% trigger)
    CONSTELLATION = "constellation"
    FOSSIL = "fossil"           # Unlocked via progression tier
    MINERAL = "mineral"         # Unlocked via progression tier
    LIFEFORM = "lifeform"       # Unlocked via progression tier
    ARCHAEOLOGY = "archaeology" # Future expansion
    XENOLOGY = "xenology"      # Future expansion


class ScanResult:
    """
    A single scan result with full educational content.

    Q1:  Real, verifiable science from env_education.
    Q9:  Works on every surface and sky object via multi-domain dispatch.
    Q10: Includes domain tag for visual styling [Geology], [Weather], [Astronomy].
    Q24: Diegetic — appears as HUD overlay from in-world tool use.
    """

    def __init__(
        self,
        domain: ScanDomain,
        text: str,
        sub_category: str = "",
        timestamp: float = 0.0,
        is_deep: bool = False,
        context: Optional[Dict[str, Any]] = None,
    ):
        self.domain = domain
        self.text = text
        self.sub_category = sub_category
        self.timestamp = timestamp if timestamp else time.time()
        self.is_deep = is_deep
        self.context = context or {}

    @property
    def display_domain_tag(self) -> str:
        """Domain tag for HUD display, matching env_education formatting."""
        return {
            ScanDomain.GEOLOGY: "[Geology]",
            ScanDomain.DEEP_GEOLOGY: "[Geology Detail]",
            ScanDomain.METEOROLOGY: "[Weather]",
            ScanDomain.ASTRONOMY: "[Astronomy]",
            ScanDomain.CONSTELLATION: "[Astronomy]",
            ScanDomain.ENVIRONMENT: "[Environment]",
            ScanDomain.FOSSIL: "[Fossil]",
            ScanDomain.MINERAL: "[Mineral]",
            ScanDomain.LIFEFORM: "[Lifeform]",
            ScanDomain.ARCHAEOLOGY: "[Archaeology]",
            ScanDomain.XENOLOGY: "[Xenology]",
        }.get(self.domain, "[Scan]")

    @property
    def domain_audio_tone(self) -> str:
        """
        Domain-specific audio pitch reference per Q36.
        Geology=low, Meteorology=mid, Astronomy=high.
        """
        return {
            ScanDomain.GEOLOGY: "low",
            ScanDomain.DEEP_GEOLOGY: "low",
            ScanDomain.METEOROLOGY: "mid",
            ScanDomain.ASTRONOMY: "high",
            ScanDomain.CONSTELLATION: "high",
            ScanDomain.ENVIRONMENT: "mid",
            ScanDomain.FOSSIL: "low",
            ScanDomain.MINERAL: "mid",
            ScanDomain.LIFEFORM: "high",
        }.get(self.domain, "mid")

    @property
    def as_display_text(self) -> str:
        """Formatted display text for HUD panel.

        env_education already prefixes with [Geology], [Weather], etc.
        Only prepend our domain tag if the source text is unadorned.
        """
        if self.text.startswith("["):
            return self.text
        return f"{self.display_domain_tag} {self.text}"

    def to_dict(self) -> Dict[str, Any]:
        """Serializable representation for MCP bridge or save-game."""
        return {
            "domain": self.domain.value,
            "text": self.text,
            "sub_category": self.sub_category,
            "timestamp": self.timestamp,
            "is_deep": self.is_deep,
            "display_text": self.as_display_text,
            "audio_tone": self.domain_audio_tone,
        }

    def __repr__(self) -> str:
        return self.as_display_text


class ScannerConfig:
    """
    Scanner hardware properties per spec.

    Q4:  Durability, ScanRadius, ScanTime as upgradable properties.
    Q14: EditAnywhere/BlueprintReadWrite for UE5 tuning.
    Q33: Standard AActor + UStaticMeshComponent + UToolScannerComponent.
    Q34: Scan() does TActorIterator<AActor> range check — microseconds.
    """

    def __init__(
        self,
        scan_radius: float = 500.0,
        scan_interval: float = 1.0,
        scan_time: float = 2.0,
        durability: float = 100.0,
        max_durability: float = 100.0,
        scan_cooldown: float = 0.5,
        deep_scan_chance: float = 0.30,  # Q3: 30% trigger for deep observations
    ):
        self.scan_radius = scan_radius
        self.scan_interval = scan_interval
        self.scan_time = scan_time
        self.durability = durability
        self.max_durability = max_durability
        self.scan_cooldown = scan_cooldown
        self.deep_scan_chance = deep_scan_chance

    def durability_percent(self) -> float:
        """0.0 to 1.0 remaining durability."""
        return max(0.0, self.durability / max(self.max_durability, 1))

    def is_functional(self) -> bool:
        """Scanner works above 0 durability."""
        return self.durability > 0.0

    def copy(self) -> "ScannerConfig":
        """Return a copy for upgrade application."""
        return ScannerConfig(
            scan_radius=self.scan_radius,
            scan_interval=self.scan_interval,
            scan_time=self.scan_time,
            durability=self.durability,
            max_durability=self.max_durability,
            scan_cooldown=self.scan_cooldown,
            deep_scan_chance=self.deep_scan_chance,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scan_radius": self.scan_radius,
            "scan_interval": self.scan_interval,
            "scan_time": self.scan_time,
            "durability": self.durability,
            "max_durability": self.max_durability,
            "scan_cooldown": self.scan_cooldown,
            "deep_scan_chance": self.deep_scan_chance,
        }


# --- gameplay-useful knowledge mappings per Q2 ---

GAMEPLAY_KNOWLEDGE: Dict[str, List[str]] = {
    # Q2: Player uses scanner knowledge to make gameplay decisions
    "igneous_basalt": [
        "Volcanic activity detected. Mineral resources likely nearby.",
        "Basalt terrain — possible geothermal vents for heating.",
    ],
    "sedimentary_limestone": [
        "Limestone terrain — cave systems likely. Seek shelter.",
        "Karst landscape — watch for sinkholes and underground passages.",
    ],
    "sedimentary_sandstone": [
        "Sandstone — porous. Water may be trapped in the rock layers.",
        "Cross-bedding shows ancient wind direction — navigate by geology.",
    ],
    "clear": [
        "High pressure. Stable flying conditions. Safe to travel.",
        "Clear skies — good for celestial navigation.",
    ],
    "windy": [
        "Wind from the east. Weather system moving in. Plan shelter.",
        "Gusting stronger. Secure loose equipment.",
    ],
    "storm": [
        "Storm building. Seek shelter immediately.",
        "Pressure dropping. Lightning risk within the hour.",
        "Dust storm approaching. Visibility will drop to near zero.",
    ],
    "calm": [
        "Dead calm. Rain likely within 24 hours. Prepare.",
        "High humidity. Morning fog will reduce visibility.",
    ],
}

# Q6: 10-second viral clip: sandstone cross-bedding -> moon phase -> cumulonimbus
VIRAL_DEMO_SEQUENCE = [
    "sedimentary_sandstone",
    "moon",
    "storm",
]


class Scanner:
    """
    Educational Scanner — main class.

    Q1:  Teaches real, verifiable science.
    Q3:  Active — Scan() is manual trigger. No passive educational content.
    Q9:  Multi-domain: geology, weather, astronomy, time.
    Q11: deep_scan_chance (30%) for deeper observations.
    04:  Properties upgradable: scan_radius, scan_time, durability.
    Q10: Visual/audio feedback wiring points.
    Q27: Complementary to Verb_Look (look=orientation, scan=education).
    Q32: Terminal is human learning real science.

    Usage:
        scanner = Scanner()
        result = scanner.scan(rock_type="sedimentary_sandstone")
        print(result.as_display_text)  # "[Geology] Cross-bedding in the sandstone..."
    """

    def __init__(self, config: Optional[ScannerConfig] = None):
        self.config = config or ScannerConfig()
        self.scan_history: List[ScanResult] = []
        self.total_scans: int = 0
        self.last_scan_time: float = 0.0
        self.last_domain: Optional[ScanDomain] = None

    # ─── Core API ──────────────────────────────────────────────────────────

    def scan(
        self,
        rock_type: str = "sedimentary_sandstone",
        weather_state: str = "clear",
        time_of_day: str = "day",
        sky_feature: str = "clear",
        constellation: Optional[str] = None,
        moon_phase: str = "waxing",
        days_to_full: int = 7,
        terrain_feature: str = "canyon",
        force_deep: bool = False,
    ) -> Optional[ScanResult]:
        """
        Perform a manual scan — the primary educational trigger (Q3).

        Player must deliberately aim and activate. Educational content only
        fires here, not in passive tick.

        Returns None if scanner is non-functional (durability depleted).
        """
        if not self.config.is_functional():
            return None

        now = time.time()
        if now - self.last_scan_time < self.config.scan_cooldown:
            return None  # Still in cooldown

        self.last_scan_time = now
        self.total_scans += 1

        # Consume durability (Q4: durability as consumable resource)
        self.config.durability = max(0.0, self.config.durability - 0.5)

        # Determine which domain to scan based on environmental context
        result = self._dispatch_scan(
            rock_type=rock_type,
            weather_state=weather_state,
            time_of_day=time_of_day,
            sky_feature=sky_feature,
            constellation=constellation,
            moon_phase=moon_phase,
            days_to_full=days_to_full,
            terrain_feature=terrain_feature,
            force_deep=force_deep,
        )

        if result:
            self.scan_history.append(result)
            self.last_domain = result.domain

        return result

    def scan_all_domains(
        self,
        rock_type: str = "sedimentary_sandstone",
        weather_state: str = "clear",
        time_of_day: str = "day",
        sky_feature: str = "clear",
        constellation: Optional[str] = None,
        moon_phase: str = "waxing",
        days_to_full: int = 7,
    ) -> str:
        """
        Full environmental scan report — wires to env_education.environment_report().

        Q9:  Works on every surface and sky object.
        Q15: Display in existing HUD as subtitle-style text.
        """
        return environment_report(
            geology_type=rock_type,
            weather_state=weather_state,
            time_of_day=time_of_day,
            sky_feature=sky_feature,
        )

    def get_gameplay_advice(self, rock_type: str) -> Optional[str]:
        """
        Q2: Player uses scanner knowledge to make gameplay decisions.

        Returns actionable advice based on what was scanned.
        """
        hints = GAMEPLAY_KNOWLEDGE.get(rock_type)
        if hints:
            return random.choice(hints)
        return None

    # ─── Internal dispatch ─────────────────────────────────────────────────

    def _dispatch_scan(
        self,
        rock_type: str,
        weather_state: str,
        time_of_day: str,
        sky_feature: str,
        constellation: Optional[str],
        moon_phase: str,
        days_to_full: int,
        terrain_feature: str,
        force_deep: bool,
    ) -> ScanResult:
        """
        Multi-domain scan dispatch simulating RayCast targeting (Q9).

        The UE5 RayCast determines what the player is pointing at. This
        Python dispatch simulates that by checking provided context in a
        deterministic priority order matching the game's targeting:
        1. Celestial objects (constellation, moon, sunset, night_sky)
        2. Deep geology (30% chance on deliberate close examination)
        3. Sub-surface features (fossil/mineral — progression-gated)
        4. Geology (terrain / rock formations)
        5. Meteorology (sky / weather)
        6. Time-of-day / environment (fallback)

        The provided parameters tell us what the player is targeting via
        the simulated RayCast, so we dispatch directly rather than randomly.
        """
        # 1. Celestial: player pointed at sky
        if sky_feature == "constellation" and constellation:
            text = constellation_observation(constellation)
            return ScanResult(
                domain=ScanDomain.CONSTELLATION,
                text=text,
                sub_category=constellation,
                context={"constellation": constellation},
            )

        if sky_feature in ("moon", "sunset", "night_sky"):
            context = {"moon_phase": moon_phase, "days_to_full": days_to_full}
            text = astronomy_prompt(sky_feature, context)
            return ScanResult(
                domain=ScanDomain.ASTRONOMY,
                text=text,
                sub_category=sky_feature,
                context=context,
            )

        # 2. Deep geology check (30% chance per Q3/Q11, or forced)
        if force_deep or (rock_type and random.random() < self.config.deep_scan_chance):
            text = deep_geology_observation(rock_type)
            return ScanResult(
                domain=ScanDomain.DEEP_GEOLOGY,
                text=text,
                sub_category=rock_type,
                is_deep=True,
            )

        # 3. Preserve deep scan domain tag even when the roll didn't
        #    produce a "[Geology Detail]" prefix — mark it anyway.
        #    (deep_geology_observation has its own 30% inner roll)

        # 4. Geology: player pointed at terrain
        if rock_type and rock_type in GEOLOGY_PROMPTS:
            text = geology_prompt(rock_type, terrain_feature)
            return ScanResult(
                domain=ScanDomain.GEOLOGY,
                text=text,
                sub_category=rock_type,
            )

        # 5. Weather: player pointed at sky (non-celestial)
        if weather_state and weather_state in WEATHER_PROMPTS:
            text = weather_prompt(weather_state)
            return ScanResult(
                domain=ScanDomain.METEOROLOGY,
                text=text,
                sub_category=weather_state,
            )

        # 6. Fallback: time-of-day / environment
        text = time_prompt(time_of_day)
        return ScanResult(
            domain=ScanDomain.ENVIRONMENT,
            text=text,
            sub_category=time_of_day,
        )

    # ─── History & state ───────────────────────────────────────────────────

    def recent_scans(self, count: int = 5) -> List[ScanResult]:
        """Last N scan results for history log display."""
        return self.scan_history[-count:]

    def scan_count(self) -> int:
        """Total number of scans performed."""
        return self.total_scans

    def unique_domains_scanned(self) -> List[ScanDomain]:
        """Domains the player has scanned at least once."""
        seen: set[ScanDomain] = set()
        for r in self.scan_history:
            seen.add(r.domain)
        return list(seen)

    def reset(self) -> None:
        """Reset scanner state (new game)."""
        self.scan_history.clear()
        self.total_scans = 0
        self.last_scan_time = 0.0
        self.last_domain = None

    # ─── MCP bridge integration ────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Full serializable state for MCP bridge / save-game."""
        return {
            "config": self.config.to_dict(),
            "total_scans": self.total_scans,
            "last_domain": self.last_domain.value if self.last_domain else None,
            "recent_scans": [r.to_dict() for r in self.recent_scans(10)],
            "functional": self.config.is_functional(),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Scanner":
        """Restore scanner state from a dict (save/load)."""
        cfg_data = data.get("config", {})
        config = ScannerConfig(
            scan_radius=cfg_data.get("scan_radius", 500.0),
            scan_interval=cfg_data.get("scan_interval", 1.0),
            scan_time=cfg_data.get("scan_time", 2.0),
            durability=cfg_data.get("durability", 100.0),
            max_durability=cfg_data.get("max_durability", 100.0),
            scan_cooldown=cfg_data.get("scan_cooldown", 0.5),
            deep_scan_chance=cfg_data.get("deep_scan_chance", 0.30),
        )
        scanner = Scanner(config=config)
        scanner.total_scans = data.get("total_scans", 0)
        return scanner
