# -*- coding: utf-8 -*-
"""
scanner_progression.py — Scanner progression tiers.

Per Scanner_Progression_System graph (26 answers). Defines upgrade tiers,
category unlocks, and knowledge milestones.

Q1:  Unlock deeper science: surface-ID -> composition analysis -> formation history.
Q3:  Feels like real scientific instrument advancement (bigger dish = more data).
Q4:  Ships incrementally: v1=radius, v2=categories, v3=composition analysis.
Q8:  Casual vs completionist pacing — scan count based, not XP-gated.
Q11: Data-driven upgrade tiers for modding via JSON.
Q13: No dependency on Player_Progression/XP system.
Q15: Derived from Educational_Scanner Q4 (upgradable properties).
Q23: Serves educational RPG goal — player earns deeper knowledge through curiosity.
Q26: Terminal is PLAYER MASTERY — deeper knowledge through curiosity.

Progression model:
  Tier 1: Basic Scanner   — 500m radius, 2s scan time, 100 durability
  Tier 2: Enhanced Scanner — 750m radius, 1.5s scan time, 150 durability, +mineral detection
  Tier 3: Advanced Scanner — 1000m radius, 1.0s scan time, 200 durability, +fossil detection
  Tier 4: Survey Scanner   — 1500m radius, 0.5s scan time, 300 durability, +lifeform detection
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Optional, Dict, List, Any
import math


# ─── Constants ─────────────────────────────────────────────────────────────

# Scans needed to unlock each tier
SCANS_PER_TIER = {
    1: 0,      # Starting tier
    2: 25,     # 25 scans to unlock Tier 2
    3: 75,     # 75 scans to unlock Tier 3
    4: 200,    # 200 scans to unlock Tier 4
}

# Category unlocks per tier
TIER_CATEGORIES = {
    1: ["geology", "weather", "astronomy", "environment", "constellation"],
    2: ["geology", "weather", "astronomy", "environment", "constellation", "mineral"],
    3: ["geology", "weather", "astronomy", "environment", "constellation", "mineral", "fossil"],
    4: [
        "geology", "weather", "astronomy", "environment", "constellation",
        "mineral", "fossil", "lifeform", "archaeology", "xenology",
    ],
}

CATEGORY_DISPLAY_NAMES = {
    "mineral": "Mineral Detection",
    "fossil": "Fossil Detection",
    "lifeform": "Lifeform Detection",
    "archaeology": "Archaeology Scan",
    "xenology": "Xenology Scan",
}


class TierLevel(IntEnum):
    """Scanner tier levels."""
    BASIC = 1
    ENHANCED = 2
    ADVANCED = 3
    SURVEY = 4


@dataclass
class TierStats:
    """
    Scanner hardware stats for a given tier.

    Q4:  ATool_Scanner properties: Durability, ScanRadius, ScanTime.
    Q15: Derived from upgradable properties identified in parent feature.
    """
    scan_radius: float          # Meters
    scan_time: float            # Seconds per scan
    max_durability: float       # Total durability pool
    durability_regen: float     # Passive regen per scan? (future)
    deep_scan_chance: float     # Base deep scan probability
    cooldown_reduction: float   # Multiplier on base cooldown
    durability_cost_per_scan: float  # Durability consumed per scan


# Tier stat definitions
TIER_STATS: Dict[int, TierStats] = {
    1: TierStats(
        scan_radius=500.0,
        scan_time=2.0,
        max_durability=100.0,
        durability_regen=0.0,
        deep_scan_chance=0.30,
        cooldown_reduction=1.0,
        durability_cost_per_scan=1.0,
    ),
    2: TierStats(
        scan_radius=750.0,
        scan_time=1.5,
        max_durability=150.0,
        durability_regen=0.0,
        deep_scan_chance=0.35,
        cooldown_reduction=0.80,
        durability_cost_per_scan=0.85,
    ),
    3: TierStats(
        scan_radius=1000.0,
        scan_time=1.0,
        max_durability=200.0,
        durability_regen=0.0,
        deep_scan_chance=0.40,
        cooldown_reduction=0.65,
        durability_cost_per_scan=0.70,
    ),
    4: TierStats(
        scan_radius=1500.0,
        scan_time=0.5,
        max_durability=300.0,
        durability_regen=0.0,
        deep_scan_chance=0.50,
        cooldown_reduction=0.50,
        durability_cost_per_scan=0.50,
    ),
}

# Knowledge milestones — deeper science per tier (Q1, Q26)
# Each milestone adds educational depth to scan results
TIER_KNOWLEDGE_MILESTONES: Dict[int, Dict[str, List[str]]] = {
    1: {
        "geology": ["Surface identification: basic rock type recognition."],
        "weather": ["Basic weather state identification."],
        "astronomy": ["Basic celestial object identification."],
    },
    2: {
        "mineral": ["Mineral composition analysis unlocked.",
                     "Can now identify trace elements in rock formations."],
        "geology": ["Composition analysis: mineral content within rock types."],
        "weather": ["Pressure trend tracking: predict weather changes within 1 hour."],
    },
    3: {
        "fossil": ["Fossil detection unlocked.",
                    "Can identify embedded fossil structures in sedimentary rock.",
                    "Fossil identification adds geological timeline context."],
        "geology": ["Formation history: full geological timeline reconstruction."],
        "weather": ["Extended forecasting: predict weather up to 6 hours ahead."],
        "astronomy": ["Deep sky observation: identify star types and distances."],
    },
    4: {
        "lifeform": ["Lifeform detection unlocked.",
                      "Can detect microbial signatures and dormant biological material.",
                      "Lifeform analysis adds biosphere context to environmental scans."],
        "archaeology": ["Archaeology scan: detect artificial structures and artifacts.",
                        "Can identify ruins, tools, and structural remnants."],
        "xenology": ["Xenology scan: identify anomalous non-native materials.",
                     "Detects off-world chemical signatures and technology fragments."],
        "geology": ["Planetary geology context: full crust-to-mantle profile."],
        "astronomy": ["Astronomical position fixing: precise stellar navigation data."],
    },
}


@dataclass
class ScannerProgression:
    """
    Scanner progression system.

    Tracks total scans, current tier, unlocked categories, and knowledge
    milestones. Scan-count-based progression (Q8: casual-friendly pacing).

    Q4:  Ship incrementally: v1 radius, v2 new categories, v3 composition.
    Q11: Data-driven tiers for modding via JSON.
    Q13: Works independently of Player_Progression/XP.
    """

    current_tier: int = 1
    total_scans: int = 0

    # Per-category scan counters for milestone tracking
    category_scans: Dict[str, int] = field(default_factory=lambda: {
        cat: 0 for cat in TIER_CATEGORIES[1]
    })

    # Unlocked categories (beyond the base set)
    unlocked_categories: List[str] = field(default_factory=list)

    # Knowledge milestones achieved
    achieved_milestones: List[str] = field(default_factory=list)

    # Upgrade notifications pending display
    pending_upgrade_notifications: List[str] = field(default_factory=list)

    # ─── Queries ───────────────────────────────────────────────────────────

    @property
    def scans_to_next_tier(self) -> Optional[int]:
        """Scans remaining to unlock next tier, or None if max tier."""
        if self.current_tier >= 4:
            return None
        next_tier = self.current_tier + 1
        required = SCANS_PER_TIER[next_tier]
        return max(0, required - self.total_scans)

    @property
    def tier_stats(self) -> TierStats:
        """Scanner hardware stats for current tier."""
        return TIER_STATS[self.current_tier]

    @property
    def available_categories(self) -> List[str]:
        """All scan categories available at current tier."""
        base = TIER_CATEGORIES[self.current_tier][:]
        for cat in self.unlocked_categories:
            if cat not in base:
                base.append(cat)
        return base

    @property
    def tier_progress(self) -> float:
        """0.0 to 1.0 progress toward next tier."""
        next_tier = self.current_tier + 1
        if next_tier > 4:
            return 1.0
        current_required = SCANS_PER_TIER[self.current_tier] if self.current_tier > 1 else 0
        next_required = SCANS_PER_TIER[next_tier]
        progress = (self.total_scans - current_required) / max(1, next_required - current_required)
        return min(1.0, max(0.0, progress))

    def category_is_unlocked(self, category: str) -> bool:
        """Check if a scan category is available at current progression."""
        return category in self.available_categories

    # ─── Recording scans ───────────────────────────────────────────────────

    def record_scan(self, category: str) -> Optional[str]:
        """
        Record a scan and check for progression unlocks.

        Q8: Scan-count-based progression.
        Q24: Casual vs completionist pacing — scans accumulate naturally.

        Returns an upgrade notification string if a milestone was reached,
        or None.
        """
        self.total_scans += 1
        self.category_scans[category] = self.category_scans.get(category, 0) + 1

        notification = None

        # Check tier unlock
        next_tier = self.current_tier + 1
        if next_tier <= 4 and self.total_scans >= SCANS_PER_TIER[next_tier]:
            notification = self._unlock_tier(next_tier)

        # Check knowledge milestones for current tier
        milestone_text = self._check_milestones(category)
        if milestone_text:
            if notification:
                notification += f" | {milestone_text}"
            else:
                notification = milestone_text

        return notification

    def _unlock_tier(self, tier: int) -> str:
        """Unlock a new scanner tier."""
        self.current_tier = tier
        new_categories = TIER_CATEGORIES[tier]
        stats = TIER_STATS[tier]

        message_parts = [f"=== SCANNER UPGRADE: TIER {tier} ==="]

        # Report stat improvements
        if tier > 1:
            prev_stats = TIER_STATS[tier - 1]
            radius_pct = ((stats.scan_radius / prev_stats.scan_radius) - 1) * 100
            time_pct = ((prev_stats.scan_time / stats.scan_time) - 1) * 100
            dura_pct = ((stats.max_durability / prev_stats.max_durability) - 1) * 100
            message_parts.append(
                f"Radius: +{radius_pct:.0f}% | Speed: +{time_pct:.0f}% | "
                f"Durability: +{dura_pct:.0f}%"
            )

        # Report new categories
        if tier > 1:
            prev_cats = set(TIER_CATEGORIES[tier - 1])
            new_cats = [c for c in TIER_CATEGORIES[tier] if c not in prev_cats]
            if new_cats:
                cat_names = [CATEGORY_DISPLAY_NAMES.get(c, c.capitalize()) for c in new_cats]
                message_parts.append(f"New detection mode: {', '.join(cat_names)}")
                self.unlocked_categories.extend(new_cats)

        notification = "\n".join(message_parts)
        self.pending_upgrade_notifications.append(notification)
        return notification

    def _check_milestones(self, category: str) -> Optional[str]:
        """Check if a knowledge milestone was reached for this category."""
        milestones = TIER_KNOWLEDGE_MILESTONES.get(self.current_tier, {}).get(category, [])
        if not milestones:
            return None

        cat_count = self.category_scans.get(category, 0)

        # Grant milestone every N scans (diminishing returns)
        # First milestone at 1 scan, second at 5, third at 15
        grant_thresholds = [1, 5, 15]
        milestone_granted = False
        for i, threshold in enumerate(grant_thresholds):
            if cat_count >= threshold and i < len(milestones):
                milestone_key = f"{self.current_tier}_{category}_{i}"
                if milestone_key not in self.achieved_milestones:
                    self.achieved_milestones.append(milestone_key)
                    milestone_granted = True

        if milestone_granted:
            # Grant the latest applicable milestone
            eligible = [m for i, m in enumerate(milestones)
                        if f"{self.current_tier}_{category}_{i}" in self.achieved_milestones]
            if eligible:
                return f"Knowledge unlocked: {eligible[-1]}"

        return None

    # ─── Save / Load ───────────────────────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        """Serializable state."""
        return {
            "current_tier": self.current_tier,
            "total_scans": self.total_scans,
            "category_scans": dict(self.category_scans),
            "unlocked_categories": list(self.unlocked_categories),
            "achieved_milestones": list(self.achieved_milestones),
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "ScannerProgression":
        """Restore from saved state."""
        prog = ScannerProgression(
            current_tier=data.get("current_tier", 1),
            total_scans=data.get("total_scans", 0),
        )
        # Ensure all base categories exist
        for cat in TIER_CATEGORIES[1]:
            prog.category_scans[cat] = data.get("category_scans", {}).get(cat, 0)
        # Add any extra categories
        for cat, count in data.get("category_scans", {}).items():
            if cat not in prog.category_scans:
                prog.category_scans[cat] = count
        prog.unlocked_categories = list(data.get("unlocked_categories", []))
        prog.achieved_milestones = list(data.get("achieved_milestones", []))
        return prog


# ─── Convenience function for building the progression data ────────────────

def apply_progression_to_config(
    progression: ScannerProgression,
    config: Any,  # ScannerConfig from scanner.py
) -> dict:
    """
    Apply current progression tier stats to a ScannerConfig.

    Returns a dict of the modified properties for the MCP bridge.
    """
    stats = progression.tier_stats
    return {
        "scan_radius": stats.scan_radius,
        "scan_time": stats.scan_time,
        "max_durability": stats.max_durability,
        "durability": min(config.durability, stats.max_durability),
        "deep_scan_chance": stats.deep_scan_chance,
        "scan_cooldown": 0.5 * stats.cooldown_reduction,
        "available_categories": progression.available_categories,
        "tier": progression.current_tier,
        "scans_to_next_tier": progression.scans_to_next_tier,
    }
