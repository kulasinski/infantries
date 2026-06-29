import pygame
import numpy as np
from settings import (
    INFANTRY_COLOR, SELECTED_COLOR,
    SOLDIER_SPACING, SOLDIER_RADIUS, MOVE_SPEED,
    SLOPE_PENALTY, MIN_SPEED_FRAC,
)
from terrain import directional_slope
from soldier_types import draw_soldier_symbol, assign_soldier_types, get_formation_layout, get_formation_composition


class Infantry:
    """A unit of soldiers that moves and forms up as a group."""

    def __init__(self, center_x, center_y, cols=5, rows=3, unit_type='squad', formation_name='marching'):
        self.unit_type = unit_type
        self.formation_name = formation_name
        self.center = np.array([center_x, center_y], dtype=float)
        self.target = None          # destination center
        self.facing = 0.0           # radians, 0 = right
        self.selected = False
        self.current_speed = MOVE_SPEED  # updated each frame, exposed for HUD

        self._gx = None  # gradient arrays injected after terrain is ready
        self._gy = None

        # Get formation configuration from YAML
        self.formation_layout = get_formation_layout(unit_type, formation_name)
        self.cols = self.formation_layout['dimensions']['cols']
        self.rows = self.formation_layout['dimensions']['rows']
        self.spacing = self.formation_layout['spacing']

        self.soldiers = self._build_formation(self.center)

        # Assign soldier types based on formation pattern
        self.soldier_types = get_formation_composition(unit_type, formation_name)

    def set_gradient(self, gx, gy):
        self._gx, self._gy = gx, gy

    # ------------------------------------------------------------------
    # Formation
    # ------------------------------------------------------------------

    def _build_formation(self, center):
        """Build formation based on YAML configuration pattern"""
        soldiers = []
        pattern = self.formation_layout['pattern']
        spacing_x = self.spacing['x']
        spacing_y = self.spacing['y']

        # Calculate offsets to center the formation
        offset_x = (self.cols - 1) * spacing_x / 2
        offset_y = (self.rows - 1) * spacing_y / 2

        # Build positions row by row according to pattern
        for row_idx, row_pattern in enumerate(pattern):
            for col_idx, soldier_type in enumerate(row_pattern):
                x = center[0] + col_idx * spacing_x - offset_x
                y = center[1] + row_idx * spacing_y - offset_y
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
        """Unit speed = base speed penalised by:
        1. The steepest uphill slope among all soldiers
        2. The slowest heavy weapon in the unit

        Unit is only as fast as its slowest man carrying the heaviest equipment.
        """
        if self._gx is None:
            base_speed = MOVE_SPEED
        else:
            # Calculate terrain penalty
            dx, dy = float(direction[0]), float(direction[1])
            worst_slope = 0.0
            for pos in self.soldiers:
                slope = directional_slope(self._gx, self._gy, pos[0], pos[1], dx, dy)
                # Only uphill slope penalises; clamp downhill to 0
                worst_slope = max(worst_slope, slope)

            terrain_fraction = max(MIN_SPEED_FRAC, 1.0 - SLOPE_PENALTY * worst_slope)
            base_speed = MOVE_SPEED * terrain_fraction

        # Load heavy weapon penalties from YAML
        heavy_weapon_penalties = self._get_heavy_weapon_penalties()

        # Find the heaviest weapon penalty in this unit
        heaviest_penalty = 1.0  # Start with no penalty
        for i, soldier_type in enumerate(self.soldier_types):
            if soldier_type in heavy_weapon_penalties:
                weapon_penalty = heavy_weapon_penalties[soldier_type]
                heaviest_penalty = min(heaviest_penalty, weapon_penalty)

        # Apply the heaviest weapon penalty
        final_speed = base_speed * heaviest_penalty

        # Ensure we don't go below minimum speed
        return max(final_speed, MOVE_SPEED * MIN_SPEED_FRAC)

    def _get_heavy_weapon_penalties(self):
        """Load heavy weapon penalties from YAML configuration"""
        import yaml

        try:
            with open("settings.yaml", "r") as f:
                config = yaml.safe_load(f)
            return config.get("movement", {}).get("heavy_weapon_penalties", {
                'rifleman': 1.0,
                'hq': 1.0,
                'mg': 0.75,
                'mortar': 0.6
            })
        except FileNotFoundError:
            # Fallback defaults if YAML not found
            return {
                'rifleman': 1.0,
                'hq': 1.0,
                'mg': 0.75,
                'mortar': 0.6
            }

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self, surface, camera=None):
        # Draw each soldier with their specific symbol
        for i, pos in enumerate(self.soldiers):
            soldier_type = self.soldier_types[i] if i < len(self.soldier_types) else 'rifleman'

            # Override color for selected units
            if self.selected:
                # Use gold/yellow for selected units regardless of type
                original_color = None
                from soldier_types import SOLDIER_TYPES
                if soldier_type in SOLDIER_TYPES:
                    original_color = SOLDIER_TYPES[soldier_type]['color']
                    SOLDIER_TYPES[soldier_type]['color'] = SELECTED_COLOR

            draw_soldier_symbol(surface, pos[0], pos[1], soldier_type, SOLDIER_RADIUS, camera)

            # Restore original color
            if self.selected and original_color:
                SOLDIER_TYPES[soldier_type]['color'] = original_color

        # Draw movement target if exists
        if self.target is not None:
            if camera:
                center_screen = camera.world_to_screen(self.center[0], self.center[1])
                target_screen = camera.world_to_screen(self.target[0], self.target[1])
                target_radius = camera.get_scaled_radius(4)
            else:
                center_screen = (int(self.center[0]), int(self.center[1]))
                target_screen = (int(self.target[0]), int(self.target[1]))
                target_radius = 4

            pygame.draw.line(surface, (255, 255, 100), center_screen, target_screen, 1)
            pygame.draw.circle(surface, (255, 255, 100), target_screen, target_radius, 1)

    # ------------------------------------------------------------------
    # Selection hit-test
    # ------------------------------------------------------------------

    def contains_point(self, x, y):
        # Use actual formation spacing from configuration
        half_w = (self.cols * self.spacing['x']) / 2 + 6
        half_h = (self.rows * self.spacing['y']) / 2 + 6
        return (abs(x - self.center[0]) < half_w and
                abs(y - self.center[1]) < half_h)
