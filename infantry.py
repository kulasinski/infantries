import pygame
import numpy as np
from settings import (
    INFANTRY_COLOR, SELECTED_COLOR,
    SOLDIER_SPACING, SOLDIER_RADIUS, MOVE_SPEED,
)


class Infantry:
    """A unit of soldiers that moves and forms up as a group."""

    def __init__(self, center_x, center_y, cols=5, rows=3):
        self.cols = cols
        self.rows = rows
        self.center = np.array([center_x, center_y], dtype=float)
        self.target = None          # destination center
        self.facing = 0.0           # radians, 0 = right
        self.selected = False

        self.soldiers = self._build_formation(self.center)

    # ------------------------------------------------------------------
    # Formation
    # ------------------------------------------------------------------

    def _build_formation(self, center):
        soldiers = []
        offset_x = (self.cols - 1) * SOLDIER_SPACING / 2
        offset_y = (self.rows - 1) * SOLDIER_SPACING / 2
        for row in range(self.rows):
            for col in range(self.cols):
                x = center[0] + col * SOLDIER_SPACING - offset_x
                y = center[1] + row * SOLDIER_SPACING - offset_y
                soldiers.append(np.array([x, y], dtype=float))
        return soldiers

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def move_to(self, x, y):
        self.target = np.array([x, y], dtype=float)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt):
        if self.target is None:
            return

        delta = self.target - self.center
        dist = np.linalg.norm(delta)

        if dist < 2.0:
            self.center = self.target.copy()
            self.target = None
            self.soldiers = self._build_formation(self.center)
            return

        step = min(MOVE_SPEED * dt, dist)
        direction = delta / dist
        self.facing = float(np.arctan2(direction[1], direction[0]))
        self.center += direction * step
        self.soldiers = self._build_formation(self.center)

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface):
        color = SELECTED_COLOR if self.selected else INFANTRY_COLOR
        for pos in self.soldiers:
            pygame.draw.circle(surface, color, (int(pos[0]), int(pos[1])), SOLDIER_RADIUS)

        if self.target is not None:
            pygame.draw.line(
                surface, (255, 255, 100),
                (int(self.center[0]), int(self.center[1])),
                (int(self.target[0]), int(self.target[1])),
                1,
            )
            pygame.draw.circle(surface, (255, 255, 100), (int(self.target[0]), int(self.target[1])), 4, 1)

    # ------------------------------------------------------------------
    # Selection hit-test
    # ------------------------------------------------------------------

    def contains_point(self, x, y):
        half_w = (self.cols * SOLDIER_SPACING) / 2 + 6
        half_h = (self.rows * SOLDIER_SPACING) / 2 + 6
        return (abs(x - self.center[0]) < half_w and
                abs(y - self.center[1]) < half_h)
