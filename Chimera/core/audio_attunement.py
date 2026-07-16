"""Audio Attunement Component - THE AUDIO MINIGAME, coded as MetaSound parameter modulation.

This module implements UChimeraAttunementComponent logic for attunement with the chimera/erisaid.
The audio minigame requires generating an inverse-phase acoustic wave to cancel out the 
chimera's sound rather than matching it; actively tuning pitch, volume, or tempo to match 
the target will increase the 'dissonance' meter and prevent attunement.

Three hum emitters on the Erisaid's shell each drive one harmonic-frequency Oscillator into
AB_Attunement via a BeatFrequency node (|dial - target|): FACE an emitter to isolate it 
(the spatialize() pan math collapses the other two off-axis); turn the suit-radio dial until
the beat-frequency wobble — read straight off the audio bus — slows toward 0 Hz; hold under
tolerance for hold_to_lock_s to lock. Three locks across three different days = attunement.
Firing a weapon nearby deafens it for a season (writes deaf_until_day).
"""

from dataclasses import dataclass, field
from typing import Optional, Set, List


@dataclass
class ERISAIDConfig:
    """Configuration for the Erisaid audio attunement minigame."""
    hum_base_hz: float = 41.0
    harmonics: tuple = (1.0, 2.667, 4.333)
    dial_tolerance_hz: float = 0.8
    hold_to_lock_s: float = 2.0
    facing_cos_min: float = 0.90
    attune_visits_min: int = 3
    deaf_days_after_gunfire: int = 30


@dataclass
class MetaSoundNode:
    """Represents a MetaSound node in the attunement graph."""
    node_type: str
    params: dict = field(default_factory=dict)
    children: List['MetaSoundNode'] = field(default_factory=list)


@dataclass
class UChimeraAttunementComponent:
    """THE AUDIO MINIGAME, coded as MetaSound parameter modulation, fully spatial.

    Three hum emitters on the Erisaid's shell each drive one harmonic-frequency 
    Oscillator into AB_Attunement via a BeatFrequency node (|dial - target|):
    FACE an emitter to isolate it (the spatialize() pan math collapses the other two off-axis);
    turn the suit-radio dial until the beat-frequency wobble — read straight off the audio bus —
    slows toward 0 Hz; hold under tolerance for hold_to_lock_s to lock.
    
    Three locks across three different days = attunement. Firing a weapon nearby deafens it 
    for a season (writes deaf_until_day).
    """
    
    config: ERISAIDConfig = field(default_factory=ERISAIDConfig)
    emitter_offsets: List[List[float]] = field(default_factory=lambda: [
        [-6.0, 1.5, 2.0],
        [0.0, 2.2, 3.4],
        [6.0, 1.8, 2.6]
    ])
    
    # MetaSound nodes for the attunement graph
    harmonic_oscillators: List[MetaSoundNode] = field(init=False)
    dial_param: MetaSoundNode = field(init=False)
    beat_graphs: List[MetaSoundNode] = field(init=False)
    
    # State tracking
    matched: Set[int] = field(default_factory=set)
    visit_days: Set[int] = field(default_factory=set)
    deaf_until_day: int = -1
    dial_hz: float = 35.0
    _hold_t: float = 0.0
    _active_idx: Optional[int] = None

    def __post_init__(self):
        """Initialize MetaSound nodes after dataclass creation."""
        self.harmonic_oscillators = [
            MetaSoundNode(
                node_type="Oscillator", 
                params={"freq": self.config.hum_base_hz * r}
            )
            for r in self.config.harmonics
        ]
        
        self.dial_param = MetaSoundNode(
            node_type="ParamFloat", 
            params={"name": "DialHz", "default": 35.0}
        )
        
        self.beat_graphs = [
            MetaSoundNode(
                node_type="BeatFrequency",
                params={},
                children=[osc, self.dial_param]
            )
            for osc in self.harmonic_oscillators
        ]

    @property
    def targets(self) -> List[float]:
        """Return the target harmonic frequencies."""
        return [self.config.hum_base_hz * r for r in self.config.harmonics]

    @property
    def attuned(self) -> bool:
        """Check if attunement is complete (3 locks across 3+ different days)."""
        return len(self.matched) == 3 and len(self.visit_days) >= self.config.attune_visits_min

    def beat_wobble_hz(self, idx: int, bus_value: float, t: float) -> float:
        """Calculate the beat wobble frequency for a given emitter index.
        
        The beat wobble is |dial - target| where dial is the suit-radio parameter
        and target is the harmonic oscillator frequency.
        """
        if idx < 0 or idx >= len(self.harmonic_oscillators):
            return 0.0
            
        target_freq = self.targets[idx]
        wobble = abs(self.dial_hz - target_freq)
        
        # Simulate bus publish (in real UE, this would send to AB_Attunement bus)
        # bus.Send(wobble)
        
        return wobble

    def tick(self, current_day: int, player_distance_to_erisaid: float, 
             player_facing_cos: float, best_emitter_idx: Optional[int] = None) -> bool:
        """Tick the attunement component.
        
        Returns True if a lock was achieved during this tick.
        """
        # Check if deafened by recent gunfire
        if current_day < self.deaf_until_day:
            self._active_idx, self._hold_t = None, 0.0
            return False
            
        # Check distance to Erisaid (must be within 25 units)
        if player_distance_to_erisaid > 25.0:
            self._active_idx, self._hold_t = None, 0.0
            return False
            
        # Record visit day
        self.visit_days.add(current_day)
        
        # Check if best emitter is valid and not already matched
        if best_emitter_idx is None or best_emitter_idx in self.matched:
            self._active_idx, self._hold_t = None, 0.0
            return False
            
        # Check facing cosine (must be >= facing_cos_min to isolate emitter)
        if player_facing_cos < self.config.facing_cos_min:
            self._active_idx, self._hold_t = None, 0.0
            return False
            
        self._active_idx = best_emitter_idx
        
        # Calculate beat wobble for the active emitter
        target_freq = self.targets[best_emitter_idx]
        wobble = abs(self.dial_hz - target_freq)
        
        if wobble <= self.config.dial_tolerance_hz:
            self._hold_t += 1.0  # Simulated dt=1.0 for tick
            if self._hold_t >= self.config.hold_to_lock_s:
                self.matched.add(best_emitter_idx)  # Felt CLUNK in the chest
                self._hold_t = 0.0
                return True
        else:
            self._hold_t = 0.0
            
        return False

    def on_gunfire_nearby(self, current_day: int) -> None:
        """Handle gunfire nearby - deafens attunement for a season."""
        self.deaf_until_day = current_day + self.config.deaf_days_after_gunfire
