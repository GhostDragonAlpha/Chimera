"""edu_prompt_selector.py — Context-aware prompt selection engine.

Implements the Prompt_Selection_Logic spec from Demo_Educational_Triggers:
- 3 tiered prompts per zone (intro/detail/advanced)
- Tier advancement on revisit
- Chaining via 'then_prompt_id'
- Context filters: required_time, required_weather
- Deterministic: pure function of (zone_id, player_progress, time_of_day, weather_state)
- Priority-sorted selection
- Suppression during combat/dialogue
- Hot-reload via file watcher

Usage:
    selector = EduPromptSelector("path/to/EduPrompts.json")
    prompt = selector.select_prompt("Canyon_Entrance_Strata", player_progress, "day", "clear")
    if prompt:
        print(prompt["text"])
        selector.record_fire(prompt["id"], zone_id)
"""

import json
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class PromptRecord:
    """A single educational prompt with context filters."""
    id: str
    tier: str                # "intro", "detail", "advanced"
    zone_id: Optional[str]   # None for global prompts (weather/astronomy)
    text: str
    then_prompt_id: Optional[str]
    required_time: Optional[str]   # "dawn", "day", "dusk", "night" or None
    required_weather: Optional[str] # "clear", "windy", "storm", "calm" or None
    priority: int            # 0-3, higher = more important
    cooldown_seconds: int    # minimum seconds between re-fires


@dataclass
class PlayerProgress:
    """Tracked per-zone progress across visits."""
    zone_progress: Dict[str, str] = field(default_factory=dict)
    # zone_id -> tier_last_seen ("intro", "detail", "advanced")
    last_fire_times: Dict[str, float] = field(default_factory=dict)
    # prompt_id -> timestamp of last fire
    fired_prompts: set = field(default_factory=set)
    # set of prompt_ids that have been shown


TIER_ORDER = ["intro", "detail", "advanced"]

COOLDOWN_QUEUE_MAX_DEPTH = 5


class EduPromptSelector:
    """Deterministic, context-aware educational prompt selector.

    Pure function of (zone_id, player_progress, time_of_day, weather_state).
    Same inputs always yield same prompt.
    """

    def __init__(self, json_path: str = None):
        self.json_path = json_path or str(
            Path(__file__).parent.parent / "docs" / "features" / "EduPrompts.json"
        )
        self.prompts: Dict[str, PromptRecord] = {}
        self.prompts_by_zone: Dict[str, List[str]] = {}  # zone_id -> [prompt_ids]
        self.global_prompts: List[str] = []  # prompt_ids with zone_id=None
        self._lock = threading.Lock()
        self._last_mtime = 0.0
        self._load_prompts()

    def _load_prompts(self) -> None:
        """Load prompts from JSON file. Thread-safe."""
        path = Path(self.json_path)
        if not path.exists():
            raise FileNotFoundError(f"EduPrompts.json not found at {self.json_path}")

        mtime = path.stat().st_mtime
        if mtime <= self._last_mtime:
            return  # No change; skip reload

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        prompts_data = data.get("prompts", {})
        new_prompts: Dict[str, PromptRecord] = {}
        new_by_zone: Dict[str, List[str]] = {}
        new_global: List[str] = []

        for pid, pdata in prompts_data.items():
            record = PromptRecord(
                id=pid,
                tier=pdata.get("tier", "intro"),
                zone_id=pdata.get("zone_id"),
                text=pdata.get("text", ""),
                then_prompt_id=pdata.get("then_prompt_id"),
                required_time=pdata.get("required_time"),
                required_weather=pdata.get("required_weather"),
                priority=pdata.get("priority", 0),
                cooldown_seconds=pdata.get("cooldown_seconds", 30),
            )
            new_prompts[pid] = record
            zone_id = record.zone_id
            if zone_id:
                new_by_zone.setdefault(zone_id, []).append(pid)
            else:
                new_global.append(pid)

        with self._lock:
            self.prompts = new_prompts
            self.prompts_by_zone = new_by_zone
            self.global_prompts = new_global
            self._last_mtime = mtime

        print(f"[EduPromptSelector] Loaded {len(new_prompts)} prompts "
              f"({len(new_by_zone)} zones, {len(new_global)} global)")

    def hot_reload(self) -> bool:
        """Check for changes on disk and reload if modified. Returns True if reloaded."""
        path = Path(self.json_path)
        if not path.exists():
            return False
        mtime = path.stat().st_mtime
        if mtime > self._last_mtime:
            self._load_prompts()
            return True
        return False

    def _get_next_tier(self, zone_id: str, progress: PlayerProgress) -> str:
        """Determine which tier the player should see next for this zone."""
        last_tier = progress.zone_progress.get(zone_id)
        if last_tier is None:
            return "intro"
        try:
            idx = TIER_ORDER.index(last_tier)
            next_idx = min(idx + 1, len(TIER_ORDER) - 1)
            return TIER_ORDER[next_idx]
        except ValueError:
            return "intro"

    def _is_on_cooldown(self, prompt_id: str, progress: PlayerProgress) -> bool:
        """Check if a prompt is still on cooldown."""
        record = self.prompts.get(prompt_id)
        if not record:
            return True
        last_fire = progress.last_fire_times.get(prompt_id, 0.0)
        elapsed = time.time() - last_fire
        return elapsed < record.cooldown_seconds

    def _matches_context(self, record: PromptRecord,
                         time_of_day: str, weather_state: str) -> bool:
        """Check if prompt passes context filters."""
        if record.required_time and record.required_time != time_of_day:
            return False
        if record.required_weather and record.required_weather != weather_state:
            return False
        return True

    def select_prompt(self, zone_id: Optional[str],
                      progress: PlayerProgress,
                      time_of_day: str = "day",
                      weather_state: str = "clear",
                      suppressed: bool = False) -> Optional[PromptRecord]:
        """Select the best prompt for current context.

        Deterministic: same inputs always yield same prompt.

        Args:
            zone_id: Current zone the player is in, or None for global selection.
            progress: Player's per-zone progress tracking.
            time_of_day: Current time ("dawn", "day", "dusk", "night").
            weather_state: Current weather ("clear", "windy", "storm", "calm").
            suppressed: True if player is in combat/dialogue (queues instead).

        Returns:
            PromptRecord to display, or None if no eligible prompt.

        Raises:
            ValueError if inputs are invalid.
        """
        if suppressed:
            # Prompt queues; returns None, caller should retry when suppressed ends
            return None

        # Validate inputs
        valid_times = {"dawn", "day", "dusk", "night"}
        valid_weather = {"clear", "windy", "storm", "calm"}
        if time_of_day not in valid_times:
            raise ValueError(f"Invalid time_of_day '{time_of_day}'. Must be one of {valid_times}")
        if weather_state not in valid_weather:
            raise ValueError(f"Invalid weather_state '{weather_state}'. Must be one of {valid_weather}")

        # Hot-reload check
        self.hot_reload()

        with self._lock:
            # Gather candidate prompt IDs
            candidate_ids: List[str] = []

            if zone_id:
                # Zone-specific prompts
                candidate_ids = list(self.prompts_by_zone.get(zone_id, []))

            # Add global prompts (weather, astronomy) that pass context
            for gid in self.global_prompts:
                rec = self.prompts.get(gid)
                if rec and gid not in candidate_ids:
                    # Global prompts are always candidates if context matches
                    candidate_ids.append(gid)

            if not candidate_ids:
                return None

            # Score candidates
            candidates: List[Tuple[int, int, str, PromptRecord]] = []
            # (priority_score, tier_score, prompt_id, record)

            target_tier = self._get_next_tier(zone_id or "__global__", progress)

            for pid in candidate_ids:
                record = self.prompts.get(pid)
                if not record:
                    continue

                # Skip if on cooldown
                if self._is_on_cooldown(pid, progress):
                    continue

                # Check context filters
                if not self._matches_context(record, time_of_day, weather_state):
                    continue

                # Score: higher priority wins; tier match preferred
                tier_score = 0
                if record.tier == target_tier:
                    tier_score = 3
                elif TIER_ORDER.index(record.tier) < TIER_ORDER.index(target_tier):
                    # Lower tier = fallback (still valid)
                    tier_score = 1
                else:
                    # Higher tier = available but not preferred
                    tier_score = 2

                priority_score = record.priority * 10

                # Deterministic tiebreak: prompt_id string
                candidates.append((priority_score, tier_score, pid, record))

            if not candidates:
                return None

            # Sort: highest priority first, then highest tier match, then alphabetically
            candidates.sort(key=lambda x: (-x[0], -x[1], x[2]))
            return candidates[0][3]

    def record_fire(self, prompt_id: str, zone_id: Optional[str],
                    progress: PlayerProgress) -> None:
        """Record that a prompt fired, updating player progress and cooldowns.

        Args:
            prompt_id: The id of the prompt that fired.
            zone_id: The zone the player was in.
            progress: Player progress to update (mutated in-place).

        Returns:
            A chained prompt_id if the prompt has a then_prompt_id, else None.
        """
        record = self.prompts.get(prompt_id)
        if not record:
            return

        now = time.time()
        progress.last_fire_times[prompt_id] = now
        progress.fired_prompts.add(prompt_id)

        # Advance tier for this zone
        if record.zone_id:
            progress.zone_progress[record.zone_id] = record.tier

        # Chain: return next prompt_id if exists
        if record.then_prompt_id:
            return record.then_prompt_id

    def get_prompts_for_test(self, zone_id: str = None) -> List[PromptRecord]:
        """Get all prompts for a zone (or all zones) for test-mode sequential fire.

        Used by ch.EduTriggers.TestMode.
        """
        results = []
        with self._lock:
            if zone_id:
                pids = self.prompts_by_zone.get(zone_id, [])
            else:
                pids = list(self.prompts.keys())

            for pid in pids:
                rec = self.prompts.get(pid)
                if rec:
                    results.append(rec)
        return sorted(results, key=lambda r: (r.priority, r.tier))


# Queue for suppressed / rapid successive triggers
class PromptQueue:
    """FIFO queue for pending educational prompts.

    Implements queue from HUD spec: TQueue<FPromptData> semantics.
    Max depth COOLDOWN_QUEUE_MAX_DEPTH (5); older entries dropped with warning.
    """

    def __init__(self, max_depth: int = COOLDOWN_QUEUE_MAX_DEPTH):
        self.max_depth = max_depth
        self._queue: List[PromptRecord] = []

    def enqueue(self, prompt: PromptRecord) -> None:
        """Add prompt to queue. Drops oldest if at max depth."""
        if len(self._queue) >= self.max_depth:
            dropped = self._queue.pop(0)
            print(f"[EduPromptQueue] WARNING: Queue full, dropping '{dropped.id}'")
        self._queue.append(prompt)

    def dequeue(self) -> Optional[PromptRecord]:
        """Remove and return next prompt, or None if empty."""
        if not self._queue:
            return None
        return self._queue.pop(0)

    def peek(self) -> Optional[PromptRecord]:
        """View next prompt without removing."""
        if not self._queue:
            return None
        return self._queue[0]

    def clear(self) -> None:
        """Clear all queued prompts."""
        self._queue.clear()

    @property
    def is_empty(self) -> bool:
        return len(self._queue) == 0

    @property
    def count(self) -> int:
        return len(self._queue)


# Convenience
def create_default_selector() -> EduPromptSelector:
    """Create selector loading from the default EduPrompts.json location."""
    return EduPromptSelector()
