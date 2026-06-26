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