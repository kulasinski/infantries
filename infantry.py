import pygame
import numpy as np
from settings import (
    INFANTRY_COLOR, SELECTED_COLOR,
    SOLDIER_SPACING, SOLDIER_RADIUS, MOVE_SPEED,
    SLOPE_PENALTY, MIN_SPEED_FRAC,
)
from terrain import directional_slope


class Infantry:
    """A unit of soldiers that moves and forms up as a group."""

    def __init__(self, center_x, center_y, cols=5, rows=3):
        self.cols = cols
        self.rows = rows
        self.center = np.array([center_x, center_y], dtype=float)
        self.target = None          # destination center
        self.facing = 0.0           # radians, 0 = right
        self.selected = False
        self.current_speed = MOVE_SPEED  # updated each frame, exposed for HUD

        self._gx = None  # gradient arrays injected after terrain is ready
        self._gy = None

        self.soldiers = self._build_formation(self.center)

    def set_gradient(self, gx, gy):
        self._gx, self._gy = gx, gy

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

        direction = delta / dist
        self.facing = float(np.arctan2(direction[1], direction[0]))

        speed = self._effective_speed(direction)
        self.current_speed = speed
        step = min(speed * dt, dist)
        self.center += direction * step
        self.soldiers = self._build_formation(self.center)

    def _effective_speed(self, direction):
        """Unit speed = base speed penalised by the steepest uphill slope among all soldiers.

        Downhill is treated as flat (no speed bonus). Unit is only as fast as
        its slowest man.
        """
        if self._gx is None:
            return MOVE_SPEED

        dx, dy = float(direction[0]), float(direction[1])
        worst_slope = 0.0
        for pos in self.soldiers:
            slope = directional_slope(self._gx, self._gy, pos[0], pos[1], dx, dy)
            # Only uphill slope penalises; clamp downhill to 0
            worst_slope = max(worst_slope, slope)

        fraction = max(MIN_SPEED_FRAC, 1.0 - SLOPE_PENALTY * worst_slope)
        return MOVE_SPEED * fraction

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
