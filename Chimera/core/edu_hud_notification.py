"""edu_hud_notification.py — Visor-readout notification system prototype.

Implements the HUD_Notification_System spec from Demo_Educational_Triggers:
- 18pt minimum font at 1080p (scales with DPI)
- White-on-dark with 4.5:1 contrast ratio
- 8s auto-dismiss with 2s fade (WCAG 2.2.1/2.2.3)
- Lower-center FOV positioning (y-offset -150 from center)
- Semi-transparent black bar with white text (v1 simple)
- Fade-in: 500ms, hold: min 6s, fade-out: 500ms
- Dismiss-on-input for faster readers
- Event-driven (NewEduPrompt event)
- TQueue<FPromptData> semantics, max depth 5
- EduJournal.txt saved to player save dir
- CVar: ch.EduTriggers.HideNotifications
- SafeZone-aware positioning

This is a Python prototype of the UE5 UMG widget logic.
"""

import json
import os
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Callable


# --- Constants from spec ---
FONT_SIZE_PT = 18          # 18pt minimum at 1080p, scales with DPI
FONT_SIZE_MIN_PT = 14      # Below 720p shrink to 14pt minimum
CONTRAST_RATIO = 4.5       # White-on-dark, 4.5:1 WCAG AA
HOLD_DURATION_S = 8.0      # Auto-dismiss after 8s
FADE_IN_S = 0.5            # Fade-in animation: 500ms
FADE_OUT_S = 0.5           # Fade-out animation: 500ms
MIN_HOLD_S = 6.0           # WCAG 2.2.1 minimum readable duration
TOTAL_DURATION_S = 9.0     # Fade-in + hold + fade-out
Y_OFFSET_FROM_CENTER = -150  # Lower-center position at 1080p
SCREEN_HEIGHT_FRACTION = 0.05  # ~5% of screen height
QUEUE_MAX_DEPTH = 5
SAVE_FILE = "EduJournal.txt"

# ANSI color codes for terminal prototype
class Style:
    BOLD = "\033[1m"
    DIM = "\033[2m"
    WHITE = "\033[97m"
    BLACK_BG = "\033[40m"
    DARK_BG = "\033[48;2;20;20;20m"
    RESET = "\033[0m"
    CLEAR_LINE = "\033[2K\r"


@dataclass
class FPromptData:
    """Data structure for a notification event. Mirrors UE5 FPromptData."""
    text: str
    prompt_id: str
    zone_id: Optional[str]
    tier: str
    priority: int
    timestamp: float = field(default_factory=time.time)


class NotificationAnimator:
    """Controls notification fade-in, hold, fade-out animation cycle.

    State machine: IDLE -> FADING_IN -> HOLDING -> FADING_OUT -> IDLE
    """

    IDLE = "idle"
    FADING_IN = "fading_in"
    HOLDING = "holding"
    FADING_OUT = "fading_out"

    def __init__(self):
        self.state = self.IDLE
        self.opacity = 0.0
        self.elapsed = 0.0
        self._start_time = 0.0

    def start(self) -> None:
        """Begin animation cycle for a new notification."""
        self.state = self.FADING_IN
        self.opacity = 0.0
        self.elapsed = 0.0
        self._start_time = time.time()

    def update(self, dt: float) -> str:
        """Advance animation by dt seconds. Returns current state."""
        self.elapsed += dt

        if self.state == self.FADING_IN:
            self.opacity = min(1.0, self.elapsed / FADE_IN_S)
            if self.elapsed >= FADE_IN_S:
                self.state = self.HOLDING
                self.opacity = 1.0

        elif self.state == self.HOLDING:
            hold_elapsed = self.elapsed - FADE_IN_S
            if hold_elapsed >= HOLD_DURATION_S:
                self.state = self.FADING_OUT

        elif self.state == self.FADING_OUT:
            fade_out_elapsed = self.elapsed - FADE_IN_S - HOLD_DURATION_S
            self.opacity = max(0.0, 1.0 - (fade_out_elapsed / FADE_OUT_S))
            if fade_out_elapsed >= FADE_OUT_S:
                self.state = self.IDLE
                self.opacity = 0.0

        return self.state

    def dismiss(self) -> None:
        """Immediate dismiss (on player input)."""
        if self.state in (self.FADING_IN, self.HOLDING):
            self.state = self.FADING_OUT
            self.elapsed = FADE_IN_S + HOLD_DURATION_S  # Start fade-out now

    @property
    def is_active(self) -> bool:
        return self.state != self.IDLE

    @property
    def remaining_hold(self) -> float:
        """Seconds remaining in hold phase. 0 if not holding."""
        if self.state == self.HOLDING:
            return HOLD_DURATION_S - (self.elapsed - FADE_IN_S)
        return 0.0


class NotificationQueue:
    """FIFO queue for pending notifications. Max depth 5.

    Mirrors UE5 TQueue<FPromptData> behavior.
    """

    def __init__(self, max_depth: int = QUEUE_MAX_DEPTH):
        self.max_depth = max_depth
        self._queue: List[FPromptData] = []

    def enqueue(self, data: FPromptData) -> None:
        """Add notification. Drops oldest at max depth with warning."""
        if len(self._queue) >= self.max_depth:
            dropped = self._queue.pop(0)
            print(f"[EduHUD] WARNING: Queue full, dropping prompt '{dropped.prompt_id}'")
        self._queue.append(data)

    def dequeue(self) -> Optional[FPromptData]:
        """Remove and return next notification, or None if empty."""
        if not self._queue:
            return None
        return self._queue.pop(0)

    def peek(self) -> Optional[FPromptData]:
        """View next without removing."""
        if not self._queue:
            return None
        return self._queue[0]

    def clear(self) -> None:
        self._queue.clear()

    @property
    def count(self) -> int:
        return len(self._queue)

    @property
    def is_empty(self) -> bool:
        return len(self._queue) == 0


class EduJournal:
    """In-game journal for re-reading dismissed educational notifications.

    Mirrors EduJournal.txt saved to player save directory.
    """

    def __init__(self, save_dir: str = None):
        if save_dir is None:
            save_dir = str(Path.home() / ".chimera" / "saves")
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.journal_path = self.save_dir / SAVE_FILE
        self._entries: List[dict] = []
        self._load()

    def _load(self) -> None:
        """Load existing journal from disk."""
        if self.journal_path.exists():
            try:
                with open(self.journal_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                self._entries.append(json.loads(line))
                            except json.JSONDecodeError:
                                self._entries.append({"text": line, "source": "unknown"})
            except Exception as e:
                print(f"[EduJournal] Error loading: {e}")

    def add_entry(self, text: str, prompt_id: str, zone_id: Optional[str] = None) -> None:
        """Add a dismissed notification to the journal."""
        entry = {
            "text": text,
            "prompt_id": prompt_id,
            "zone_id": zone_id or "global",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        }
        self._entries.append(entry)
        self._append_to_file(entry)

    def _append_to_file(self, entry: dict) -> None:
        """Append entry to journal file."""
        try:
            with open(self.journal_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            print(f"[EduJournal] Error writing: {e}")

    def get_entries(self, zone_id: Optional[str] = None) -> List[dict]:
        """Get journal entries, optionally filtered by zone."""
        if zone_id:
            return [e for e in self._entries if e.get("zone_id") == zone_id]
        return list(self._entries)

    @property
    def entry_count(self) -> int:
        return len(self._entries)

    def print_journal(self) -> None:
        """Print journal to console (for in-game pause menu access)."""
        print(f"\n{'='*60}")
        print(f"  EDUCATIONAL JOURNAL ({self.entry_count} entries)")
        print(f"{'='*60}")
        for entry in self._entries:
            print(f"\n  [{entry.get('timestamp', '?')}]")
            print(f"  {entry.get('text', '')}")
            print(f"  (Zone: {entry.get('zone_id', '?')})")
        print(f"\n{'='*60}\n")


class EduHUD:
    """Main HUD notification controller.

    Event-driven: fires on 'NewEduPrompt' event.
    Manages queue, animation cycle, journal logging.
    """

    def __init__(self, journal: EduJournal = None, visible: bool = True):
        self.queue = NotificationQueue()
        self.animator = NotificationAnimator()
        self.current_prompt: Optional[FPromptData] = None
        self.journal = journal or EduJournal()
        self.visible = visible
        self._listeners: List[Callable] = []
        self._lock = threading.Lock()

    def on_new_prompt(self, text: str, prompt_id: str, zone_id: Optional[str] = None,
                      tier: str = "intro", priority: int = 0) -> None:
        """Handle 'NewEduPrompt' event. Routes to queue or display immediately."""
        if not self.visible:
            return

        data = FPromptData(
            text=text,
            prompt_id=prompt_id,
            zone_id=zone_id,
            tier=tier,
            priority=priority,
        )

        with self._lock:
            if self.animator.is_active:
                # Queue while current notification is displayed
                self.queue.enqueue(data)
                print(f"[EduHUD] Queued '{prompt_id}' (queue depth: {self.queue.count})")
            else:
                # Display immediately
                self._display(data)

            # Notify listeners
            for listener in self._listeners:
                try:
                    listener(data)
                except Exception:
                    pass

    def _display(self, data: FPromptData) -> None:
        """Begin displaying a notification."""
        self.current_prompt = data
        self.animator.start()
        self._render()

    def _render(self) -> None:
        """Render the notification bar (console prototype of HUD overlay)."""
        if not self.current_prompt or not self.visible:
            return

        text = self.current_prompt.text
        opacity = self.animator.opacity
        state = self.animator.state

        # Simulate the visor readout appearance
        if opacity > 0.01:
            bar_width = 72
            text_truncated = text[:bar_width - 4] + "..." if len(text) > bar_width - 4 else text
            padding = (bar_width - len(text_truncated)) // 2
            padded_text = " " * padding + text_truncated + " " * (bar_width - padding - len(text_truncated))

            # Dark bar with white text (semi-transparent)
            bar = f"{Style.DARK_BG}{Style.WHITE}{padded_text}{Style.RESET}"
            print(f"{Style.CLEAR_LINE}{bar}", end="", flush=True)

            if state == self.animator.FADING_IN:
                print(f"  [{Style.DIM}fade-in{Style.RESET}]", end="", flush=True)
            elif state == self.animator.HOLDING:
                remaining = self.animator.remaining_hold
                print(f"  [{Style.DIM}{remaining:.1f}s{Style.RESET}]", end="", flush=True)
            elif state == self.animator.FADING_OUT:
                print(f"  [{Style.DIM}fade-out{Style.RESET}]", end="", flush=True)
        else:
            print(f"{Style.CLEAR_LINE}{' ' * 80}", end="", flush=True)

    def tick(self, dt: float = 0.05) -> None:
        """Advance animation cycle by one tick.

        Call this from the main loop (equivalent to UE5 widget Tick).
        """
        with self._lock:
            old_state = self.animator.state
            new_state = self.animator.update(dt)

            if new_state != old_state and new_state == self.animator.IDLE:
                # Notification finished: log to journal and show next in queue
                if self.current_prompt:
                    self.journal.add_entry(
                        self.current_prompt.text,
                        self.current_prompt.prompt_id,
                        self.current_prompt.zone_id,
                    )
                    self.current_prompt = None

                if not self.queue.is_empty:
                    next_data = self.queue.dequeue()
                    self._display(next_data)
                else:
                    # Clear the display line
                    print(f"{Style.CLEAR_LINE}{' ' * 80}", end="", flush=True)

            self._render()

    def dismiss(self) -> None:
        """Immediately dismiss current notification (on player input)."""
        with self._lock:
            if self.animator.is_active:
                self.animator.dismiss()

    def show(self) -> None:
        """Show notifications (ch.EduTriggers.HideNotifications 0)."""
        self.visible = True

    def hide(self) -> None:
        """Hide notifications (ch.EduTriggers.HideNotifications 1)."""
        self.visible = False
        with self._lock:
            self.queue.clear()
            self.current_prompt = None
            self.animator.state = self.animator.IDLE
        print(f"{Style.CLEAR_LINE}{' ' * 80}", end="", flush=True)

    def toggle(self) -> bool:
        """Toggle visibility. Returns new visible state."""
        if self.visible:
            self.hide()
        else:
            self.show()
        return self.visible

    def add_listener(self, callback: Callable[[FPromptData], None]) -> None:
        """Register callback for new prompt events."""
        self._listeners.append(callback)

    def debug_state(self) -> str:
        """Return current state for debug visualization (ch.EduTriggers.Visualize 1)."""
        with self._lock:
            parts = [
                f"Visible: {self.visible}",
                f"Anim: {self.animator.state}",
                f"Opacity: {self.animator.opacity:.2f}",
                f"Queue: {self.queue.count}",
                f"Journal: {self.journal.entry_count}",
            ]
            if self.current_prompt:
                parts.append(f"Current: {self.current_prompt.prompt_id}")
            return " | ".join(parts)


def notification_characteristics() -> dict:
    """Return design parameters from the spec for documentation/validation."""
    return {
        "font_size_pt": FONT_SIZE_PT,
        "font_size_min_pt": FONT_SIZE_MIN_PT,
        "contrast_ratio": CONTRAST_RATIO,
        "hold_duration_s": HOLD_DURATION_S,
        "fade_in_s": FADE_IN_S,
        "fade_out_s": FADE_OUT_S,
        "total_duration_s": TOTAL_DURATION_S,
        "position": "lower-center FOV",
        "y_offset_from_center_1080p": Y_OFFSET_FROM_CENTER,
        "screen_height_fraction": SCREEN_HEIGHT_FRACTION,
        "queue_max_depth": QUEUE_MAX_DEPTH,
        "style": "semi-transparent black bar with white text",
        "wcag_compliance": ["WCAG 2.2.1 (min 6s readable)", "WCAG 2.2.3 (dismiss on input)"],
        "accessibility": "DPI-scaled font, SafeZone-aware, 4.5:1 contrast ratio",
    }
