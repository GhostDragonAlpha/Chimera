"""controller.py -- THE STATE MACHINE between the hands and the legs.

The operator's goal (2026-07-30): a realistic human walking around on the planet, driven by a
state machine -- walk forward and backward, sidestep left and right, steer left and right, jump.

The states are NAMED because a body is not a velocity vector: it is in one thing at a time, and
which thing it is in decides what the legs do next. Every state obeys the one shape the
CONTROLLER_MAP law demands -- APPLY EFFORT IN A DIRECTION, STOP WHEN A SENSOR SAYS STOP:

    IDLE       BALANCE      no drive; hold (the stand policy's job)
    WALK_F     STEP         effort forward, at the measured walk speed
    WALK_B     STEP         effort backward, slower -- measured backward walking runs ~0.8x
    SIDESTEP_L STEP         effort lateral-left (the cross-step)
    SIDESTEP_R STEP         effort lateral-right
    TURN_L     STEER        yaw rate left, walking pace
    TURN_R     STEER        yaw rate right
    JUMP       one-shot     crouch-launch-land; exits when the ground comes back (the sensor)

Transitions are HYSTERESIS-FREE but honest: a state holds only while its key is held, and JUMP
overlays (you can jump mid-walk and land back into it). The drive that leaves here is the exact
contract Walker.move() already consumes (fwd, strafe, turn), so the controller plugs between the
keyboard and the walker's process law without touching it.

    keys -> Controller.update(dt) -> {state, fwd, strafe, turn_rate} -> Walker.move() / Walker.look()

Speeds and jump impulse are NOT set here -- they are theHuman's derivations (walk/run Froude,
jump from muscle work / g), read out of the Walker, because the body and the ground decide those.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# the states, named
IDLE = "IDLE"
WALK_F = "WALK_F"
WALK_B = "WALK_B"
SIDESTEP_L = "SIDESTEP_L"
SIDESTEP_R = "SIDESTEP_R"
TURN_L = "TURN_L"
TURN_R = "TURN_R"
JUMP = "JUMP"

BACKWARD_FACTOR = 0.8        # measured: backward gait runs slower than forward (Winter, gait texts)
TURN_RATE = 1.6              # rad/s -- a brisk but controllable steer (a person turns ~90 deg/s+)


@dataclass
class Drive:
    state: str
    fwd: float = 0.0
    strafe: float = 0.0
    turn_rate: float = 0.0        # rad/s into Walker.look()
    sprint: bool = False
    crouch: bool = False
    jump: bool = False
    angle: float = 0.0            # the step direction (rad, player frame) -- for HUD/animation


class Controller:
    """The state machine. One state at a time; JUMP overlays and returns to whatever it left."""

    def __init__(self):
        self.state = IDLE
        self._return_state = IDLE      # what JUMP hands back to on landing
        self.jumping = False

    def update(self, dt: float, keys: dict, on_ground: bool) -> Drive:
        """keys: {'fwd','back','left','right','turn_l','turn_r','sprint','crouch','jump'}
        booleans. on_ground: the walker's own contact sensor -- the stop condition for JUMP."""
        if self.jumping:
            if on_ground:
                # LANDED -- the sensor said stop. Back to whatever we were doing.
                self.jumping = False
                self.state = self._return_state
            else:
                return Drive(state=JUMP)
        # one state at a time, priority: jump > steer > step > idle
        if keys.get("jump") and on_ground:
            self._return_state = self._base_state(keys)
            self.jumping = True
            self.state = JUMP
            return Drive(state=JUMP, jump=True)
        self.state = self._base_state(keys)
        d = Drive(state=self.state,
                  sprint=bool(keys.get("sprint")),
                  crouch=bool(keys.get("crouch")))
        if self.state == WALK_F:
            d.fwd = 1.0
        elif self.state == WALK_B:
            d.fwd = -BACKWARD_FACTOR
        elif self.state == SIDESTEP_L:
            d.strafe = -1.0
        elif self.state == SIDESTEP_R:
            d.strafe = 1.0
        elif self.state == TURN_L:
            d.turn_rate = TURN_RATE
        elif self.state == TURN_R:
            d.turn_rate = -TURN_RATE
        return d

    @staticmethod
    def _base_state(keys) -> str:
        if keys.get("turn_l"):
            return TURN_L
        if keys.get("turn_r"):
            return TURN_R
        if keys.get("fwd"):
            return WALK_F
        if keys.get("back"):
            return WALK_B
        if keys.get("left"):
            return SIDESTEP_L
        if keys.get("right"):
            return SIDESTEP_R
        return IDLE


def drive_walker(walker, controller: Controller, keys: dict, dt: float):
    """The glue: one tick of the state machine applied to a Walker -- steer, then step."""
    d = controller.update(dt, keys, walker.on_ground)
    if d.turn_rate:
        walker.look(d.turn_rate * dt, 0.0)
    walker.move(d.fwd, d.strafe, d.sprint, d.jump, d.crouch, dt)
    return d


def drive_walker_vector(walker, controller: Controller, fwd: float, strafe: float,
                        sprint: bool, crouch: bool, jump: bool, dt: float,
                        turn_l: bool = False, turn_r: bool = False):
    """THE STICK'S ANGLE IS THE STEP DIRECTION; ITS DEFLECTION IS THE SPEED (the operator's
    control law for analog). A thumbstick hands in a full 360-degree vector; the keyboard's
    eight key combinations are just eight of those directions. Both arrive here as (fwd,
    strafe) FLOATS -- magnitude scales the speed, direction is the pair -- and the facing
    rotates it, because Walker.move() already integrates in the player's own frame (the
    Call-of-Duty rule: W is wherever you look). The named states still resolve for the HUD
    and the animation, from the dominant axis; the drive carries the full analog vector."""
    mag = min(1.0, (fwd * fwd + strafe * strafe) ** 0.5)
    if controller.jumping:
        if walker.on_ground:
            controller.jumping = False
            controller.state = controller._return_state
        else:
            return Drive(state=JUMP)
    if jump and walker.on_ground:
        controller._return_state = controller.state
        controller.jumping = True
        controller.state = JUMP
        return Drive(state=JUMP, jump=True)
    if turn_l:
        controller.state = TURN_L
        walker.look(TURN_RATE * dt, 0.0)
    elif turn_r:
        controller.state = TURN_R
        walker.look(-TURN_RATE * dt, 0.0)
    elif mag > 0.05:
        # the HUD's nearest named direction; the DRIVE below stays analog
        if abs(fwd) >= abs(strafe):
            controller.state = WALK_F if fwd > 0 else WALK_B
        else:
            controller.state = SIDESTEP_R if strafe > 0 else SIDESTEP_L
    else:
        controller.state = IDLE
    d = Drive(state=controller.state, fwd=fwd * (BACKWARD_FACTOR if fwd < 0 else 1.0),
              strafe=strafe, sprint=bool(sprint), crouch=bool(crouch))
    d.angle = math.atan2(strafe, fwd) if mag > 0.05 else 0.0
    walker.move(d.fwd, d.strafe, d.sprint, False, d.crouch, dt)
    return d
