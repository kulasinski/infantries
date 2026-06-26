"""
Camera system for zooming and panning.
"""
import pygame
import numpy as np
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, DEFAULT_ZOOM, MIN_ZOOM, MAX_ZOOM, ZOOM_STEP


class Camera:
    """Camera system that handles zooming and coordinate transformations"""

    def __init__(self, initial_center_x=0, initial_center_y=0):
        self.zoom = DEFAULT_ZOOM
        # Center camera on the given position (where the company is)
        self.offset_x = SCREEN_WIDTH/2 - initial_center_x * self.zoom
        self.offset_y = SCREEN_HEIGHT/2 - initial_center_y * self.zoom

        # Panning state
        self.is_panning = False
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.pan_start_offset_x = 0
        self.pan_start_offset_y = 0

    def start_pan(self, mouse_x, mouse_y):
        """Start panning operation"""
        self.is_panning = True
        self.pan_start_x = mouse_x
        self.pan_start_y = mouse_y
        self.pan_start_offset_x = self.offset_x
        self.pan_start_offset_y = self.offset_y

    def update_pan(self, mouse_x, mouse_y):
        """Update camera position during panning"""
        if self.is_panning:
            dx = mouse_x - self.pan_start_x
            dy = mouse_y - self.pan_start_y
            self.offset_x = self.pan_start_offset_x + dx
            self.offset_y = self.pan_start_offset_y + dy

    def stop_pan(self):
        """Stop panning operation"""
        self.is_panning = False

    def focus_on_unit(self, unit, screen_width, screen_height):
        """Center camera on unit and zoom so its longest dimension fills 50% of screen"""
        # Get all soldier positions from the unit
        all_positions = []
        self._collect_soldier_positions(unit, all_positions)

        if not all_positions:
            return

        # Find bounding box of all soldiers
        xs = [pos[0] for pos in all_positions]
        ys = [pos[1] for pos in all_positions]

        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        # Calculate unit dimensions
        unit_width = max_x - min_x
        unit_height = max_y - min_y

        # Add some padding to the unit dimensions
        padding = max(unit_width, unit_height) * 0.2  # 20% padding
        unit_width += padding
        unit_height += padding

        # Calculate center of unit
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        # Calculate required zoom to fit longest dimension in 50% of screen
        target_screen_width = screen_width * 0.5
        target_screen_height = screen_height * 0.5

        zoom_for_width = target_screen_width / unit_width if unit_width > 0 else self.zoom
        zoom_for_height = target_screen_height / unit_height if unit_height > 0 else self.zoom

        # Use the smaller zoom to ensure both dimensions fit
        target_zoom = min(zoom_for_width, zoom_for_height)
        target_zoom = max(MIN_ZOOM, target_zoom)  # Respect minimum zoom

        # Set new zoom and center on unit
        self.zoom = target_zoom
        self.offset_x = screen_width/2 - center_x * self.zoom
        self.offset_y = screen_height/2 - center_y * self.zoom

    def _collect_soldier_positions(self, unit, positions):
        """Recursively collect all soldier positions from a unit"""
        if hasattr(unit, 'infantry') and hasattr(unit.infantry, 'soldiers'):
            # This is a squad with soldiers
            positions.extend(unit.infantry.soldiers)
        elif hasattr(unit, 'child_units'):
            # This is a higher-level unit with child units
            for child in unit.child_units:
                self._collect_soldier_positions(child, positions)

    def handle_zoom(self, mouse_x, mouse_y, zoom_in):
        """Handle mouse wheel zoom, zooming toward mouse position"""
        old_zoom = self.zoom

        if zoom_in:
            self.zoom = min(MAX_ZOOM, self.zoom + ZOOM_STEP)
        else:
            self.zoom = max(MIN_ZOOM, self.zoom - ZOOM_STEP)

        # Zoom toward mouse position
        if self.zoom != old_zoom:
            # Convert mouse position to world coordinates using old zoom
            world_x = (mouse_x - self.offset_x) / old_zoom
            world_y = (mouse_y - self.offset_y) / old_zoom

            # Adjust offset to keep mouse position stable with new zoom
            self.offset_x = mouse_x - world_x * self.zoom
            self.offset_y = mouse_y - world_y * self.zoom

    def world_to_screen(self, world_x, world_y):
        """Convert world coordinates to screen coordinates"""
        screen_x = world_x * self.zoom + self.offset_x
        screen_y = world_y * self.zoom + self.offset_y
        return screen_x, screen_y

    def screen_to_world(self, screen_x, screen_y):
        """Convert screen coordinates to world coordinates"""
        world_x = (screen_x - self.offset_x) / self.zoom
        world_y = (screen_y - self.offset_y) / self.zoom
        return world_x, world_y

    def get_zoom_info(self):
        """Get zoom info for UI display"""
        return {
            'zoom': self.zoom,
            'zoom_percent': int(self.zoom * 100)
        }

    def apply_transform(self, surface):
        """Apply camera transformation to a surface (for drawing)"""
        # This would be used for more complex transformations
        # For now, we'll handle transforms manually in draw calls
        pass

    def get_scaled_radius(self, base_radius):
        """Get radius scaled by zoom level"""
        return max(1, int(base_radius * self.zoom))

    def get_scaled_size(self, base_size):
        """Get size scaled by zoom level"""
        return max(1, int(base_size * self.zoom))