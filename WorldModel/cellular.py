"""
Cellular Construction Rules — how cells assemble into structures.

Not positions for splats — RULES for cell generation. Each cell type
has its own set of rules for color, shape, placement, connection.

A tree is not a collection of splats. It is a set of rules that
produce splats at the right positions with the right properties.
"""

import numpy as np
import math
from dataclasses import dataclass, field


@dataclass
class CellRule:
    """Rules for generating a cell of a given type."""
    color_base: tuple[float, float, float]
    color_var: tuple[float, float, float]
    size_base: float
    size_var: float
    opacity: float = 0.9
    edge_rule: str = "round"      # "round", "sharp", "serrated"
    vein_rule: str = "none"       # "none", "central", "parallel", "branching"
    texture_rule: str = "smooth"  # "smooth", "rough", "bark"


@dataclass
class CellNode:
    """A single cell in the tree — leaf, bark, or stem."""
    position: np.ndarray
    rule: CellRule
    parent: "CellNode | None" = None
    children: list = field(default_factory=list)
    depth: int = 0


class TreeCells:
    """Generate tree cells with proper construction rules."""

    def __init__(self):
        self.rules = {
            "leaf": CellRule(
                color_base=(0.1, 0.6, 0.1),
                color_var=(0.05, 0.3, 0.05),
                size_base=2.0,
                size_var=2.0,
                edge_rule="serrated",
                vein_rule="branching",
                texture_rule="smooth",
            ),
            "bark": CellRule(
                color_base=(0.3, 0.16, 0.08),
                color_var=(0.05, 0.03, 0.02),
                size_base=3.0,
                size_var=2.0,
                texture_rule="rough",
            ),
            "stem": CellRule(
                color_base=(0.25, 0.18, 0.1),
                color_var=(0.04, 0.04, 0.03),
                size_base=2.0,
                size_var=1.5,
            ),
        }

    def make_leaf(self, center: np.ndarray, size: float = 1.0) -> dict:
        """Generate one leaf cell with proper rules."""
        rule = self.rules["leaf"]

        # Leaf color varies from base to tip
        leaf_t = np.random.uniform(0, 1)
        color = [
            np.clip(rule.color_base[0] + np.random.uniform(-rule.color_var[0], rule.color_var[0]) + leaf_t * 0.1, 0, 1),
            np.clip(rule.color_base[1] + np.random.uniform(-rule.color_var[1], rule.color_var[1]), 0, 1),
            np.clip(rule.color_base[2] + np.random.uniform(-rule.color_var[2], rule.color_var[2]), 0, 1),
        ]

        # Leaf is NOT a sphere — it has a dominant axis
        aspect = np.random.uniform(0.6, 1.4)
        s = rule.size_base * size * np.random.uniform(0.5, 1.5)
        scale = [s * aspect, s, s * np.random.uniform(0.1, 0.5)]

        return {
            "position": center,
            "color": color,
            "scale": scale,
            "opacity": rule.opacity,
            "rule": rule,
        }

    def make_bark(self, center: np.ndarray, radius: float, angle: float = 0) -> dict:
        """Generate one bark cell with proper rules."""
        rule = self.rules["bark"]

        # Bark color varies with depth and angle
        color = [
            np.clip(rule.color_base[0] + np.random.uniform(-rule.color_var[0], rule.color_var[0]), 0, 1),
            np.clip(rule.color_base[1] + np.random.uniform(-rule.color_var[1], rule.color_var[1]), 0, 1),
            np.clip(rule.color_base[2] + np.random.uniform(-rule.color_var[2], rule.color_var[2]), 0, 1),
        ]

        s = rule.size_base * radius * np.random.uniform(0.5, 1.5)
        return {
            "position": center,
            "color": color,
            "scale": [s, s, s],
            "opacity": rule.opacity,
            "rule": rule,
        }

    def make_stem(self, center: np.ndarray, radius: float) -> dict:
        """Generate one stem cell (branch/trunk)."""
        rule = self.rules["stem"]

        color = [
            np.clip(rule.color_base[0] + np.random.uniform(-rule.color_var[0], rule.color_var[0]), 0, 1),
            np.clip(rule.color_base[1] + np.random.uniform(-rule.color_var[1], rule.color_var[1]), 0, 1),
            np.clip(rule.color_base[2] + np.random.uniform(-rule.color_var[2], rule.color_var[2]), 0, 1),
        ]

        s = rule.size_base * radius * np.random.uniform(0.5, 1.5)
        return {
            "position": center,
            "color": color,
            "scale": [s, s, s],
            "opacity": rule.opacity,
            "rule": rule,
        }

    def grow_branch(self, start: np.ndarray, direction: np.ndarray, length: float,
                    radius: float, depth: int, max_depth: int,
                    cells: list, parent_depth: int = 0):
        """Generate a branch with proper cellular construction."""

        # Stem cells along the branch
        n_cells = max(20, int(length * radius * 2))
        for i in range(n_cells):
            t = i / (n_cells - 1)
            pos = start + direction * length * t
            r = radius * (1.0 - t * 0.6)

            # Each cell is a bark/stem cell
            for _ in range(max(1, int(r * 2))):
                ox = np.random.normal(0, r / 3)
                oy = np.random.normal(0, r / 3)
                oz = np.random.normal(0, r / 3)
                cell_center = pos + np.array([ox, oy, oz])
                if depth >= max_depth - 1:
                    cells.append(self.make_bark(cell_center, r, angle=t))
                else:
                    cells.append(self.make_stem(cell_center, r))

        # If at max depth, spawn leaf cluster at end
        if depth >= max_depth - 1:
            end = start + direction * length
            # Large leaf cluster at branch tip — proportional to radius
            n_leaves = max(100, int(radius * 40))
            for _ in range(n_leaves):
                leaf_pos = end + np.random.normal(0, radius * 2.5, 3)
                # Constrain leaves to canopy hemisphere (above branch)
                leaf_pos[2] = max(leaf_pos[2], end[2] + radius * 0.3)
                cells.append(self.make_leaf(leaf_pos, size=radius * 0.5))
            # Additional leaves along the branch itself (not just tip)
            n_side = max(20, int(radius * 20))
            for _ in range(n_side):
                t = np.random.uniform(0.5, 1.0)
                leaf_pos = start + direction * length * t + np.random.normal(0, radius * 1.5, 3)
                leaf_pos[2] = max(leaf_pos[2], end[2] + radius * 0.2)
                cells.append(self.make_leaf(leaf_pos, size=radius * 0.4))

        # Sub-branches
        if depth < max_depth - 1:
            n_sub = 2 if depth < 2 else 1
            for _ in range(n_sub):
                t_split = np.random.uniform(0.3, 0.8)
                split_pos = start + direction * length * t_split
                angle_h = math.atan2(direction[0], direction[1]) + np.random.uniform(-0.5, 0.5)
                angle_v = math.atan2(math.sqrt(direction[0]**2 + direction[1]**2), direction[2]) + np.random.uniform(0.2, 0.9)
                new_dir = np.array([
                    math.sin(angle_v) * math.sin(angle_h),
                    math.sin(angle_v) * math.cos(angle_h),
                    math.cos(angle_v),
                ])
                new_dir /= np.linalg.norm(new_dir)
                self.grow_branch(split_pos, new_dir, length * 0.55, radius * 0.55,
                               depth + 1, max_depth, cells, parent_depth + 1)


def grow_cellular_tree(trunk_height=300, trunk_radius=14, max_depth=4, seed=42) -> list:
    """Generate a complete tree with cellular construction rules."""
    cells = TreeCells()
    all_cells = []

    # Trunk
    trunk_dir = np.array([0, 0.15, 0.85])
    trunk_dir /= np.linalg.norm(trunk_dir)
    cells.grow_branch(np.array([0, -trunk_height / 2, 0]), trunk_dir,
                     trunk_height * 0.6, trunk_radius, 0, max_depth, all_cells)

    return all_cells
