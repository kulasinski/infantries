"""
Military unit hierarchy system with command and control structure.
"""
import yaml
import pygame
import numpy as np
from infantry import Infantry


def load_unit_config():
    """Load unit configuration from settings.yaml"""
    with open("settings.yaml", "r") as f:
        return yaml.safe_load(f)


class CommandLevel:
    """Represents a command level (squad, platoon, company, etc.)"""
    def __init__(self, name, config):
        self.name = name
        self.size = config["size"]
        self.leadership = config["leadership"]
        self.description = config["description"]
        self.composition = config.get("composition", {})


class MilitaryUnit:
    """Base class for all military units with command structure"""

    def __init__(self, unit_type, center_x, center_y, unit_id=None):
        self.unit_type = unit_type
        self.unit_id = unit_id or f"{unit_type}_{id(self)}"
        self.center = np.array([center_x, center_y], dtype=float)
        self.selected = False
        self.parent_selected = False  # True when parent unit is selected
        self.sub_unit_index = -1  # Index for color when parent is selected
        self.controllable = True  # Will be set based on HQ availability

        # Unit naming
        self.unit_name = ""  # Will be set during scenario generation
        self.unit_number = 0  # Numeric identifier within type

        # Load unit configuration
        self.config = load_unit_config()
        self.unit_info = self.config["units"][unit_type]

        # Check if unit has headquarters (controllable)
        controllable_units = self.config["command_structure"]["controllable_units"]
        self.controllable = unit_type in controllable_units

        # Child units
        self.child_units = []
        self.parent_unit = None

        # Visual representation (will be overridden by subclasses)
        self.visual_units = []

    def set_selected(self, selected):
        """Set selection state and cascade to IMMEDIATE child units only"""
        self.selected = selected

        # When this unit is selected, mark ONLY immediate child units as parent_selected
        for i, child in enumerate(self.child_units):
            child.parent_selected = selected
            child.sub_unit_index = i if selected else -1

            # For immediate children that have their own children (like platoons),
            # propagate the color to their children so soldiers get colored too
            if hasattr(child, 'child_units') and selected:
                for grandchild in child.child_units:
                    grandchild.parent_selected = True  # Enable coloring
                    grandchild.sub_unit_index = i  # Use SAME color as parent platoon

    def clear_all_selections(self):
        """Clear all selection states recursively"""
        self.selected = False
        self.parent_selected = False
        self.sub_unit_index = -1
        for child in self.child_units:
            child.clear_all_selections()

    def get_display_name(self):
        """Get formatted display name with parent context"""
        if not self.unit_name:
            return f"{self.unit_type.title()} {self.unit_number}"

        if self.parent_unit and hasattr(self.parent_unit, 'unit_name') and self.parent_unit.unit_name:
            return f"{self.unit_name} ({self.parent_unit.unit_name})"
        else:
            return self.unit_name


class Squad(MilitaryUnit):
    """Squad level - basic tactical unit, not directly controllable"""

    def __init__(self, center_x, center_y, unit_id=None):
        super().__init__("squad", center_x, center_y, unit_id)

        # Create Infantry visual representation
        # Use YAML-configured formation for squad marching formation
        self.infantry = Infantry(center_x, center_y, unit_type='squad', formation_name='marching')
        self.visual_units = [self.infantry]

    def update(self, dt):
        """Update squad - autonomous movement"""
        self.infantry.update(dt)
        # Update center position from infantry
        self.center = self.infantry.center.copy()

    def draw(self, surface, camera=None):
        # Override infantry colors if parent is selected
        if self.parent_selected and self.sub_unit_index >= 0:
            # Draw with specific sub-unit color
            from settings import SUB_UNIT_COLORS
            color = SUB_UNIT_COLORS[self.sub_unit_index % len(SUB_UNIT_COLORS)]
            self._draw_infantry_with_color(surface, color, camera)
        else:
            self.infantry.draw(surface, camera)

    def _draw_infantry_with_color(self, surface, color, camera=None):
        """Draw infantry with custom color override"""
        import pygame
        from settings import SOLDIER_RADIUS
        from soldier_types import draw_soldier_symbol

        # Draw each soldier with custom color but keep their symbols
        for i, pos in enumerate(self.infantry.soldiers):
            soldier_type = self.infantry.soldier_types[i] if i < len(self.infantry.soldier_types) else 'rifleman'

            # Temporarily override the soldier type color
            from soldier_types import SOLDIER_TYPES
            original_color = SOLDIER_TYPES[soldier_type]['color']
            SOLDIER_TYPES[soldier_type]['color'] = color

            draw_soldier_symbol(surface, pos[0], pos[1], soldier_type, SOLDIER_RADIUS, camera)

            # Restore original color
            SOLDIER_TYPES[soldier_type]['color'] = original_color

        # Draw movement target if exists
        if self.infantry.target is not None:
            if camera:
                center_screen = camera.world_to_screen(self.infantry.center[0], self.infantry.center[1])
                target_screen = camera.world_to_screen(self.infantry.target[0], self.infantry.target[1])
                target_radius = camera.get_scaled_radius(4)
            else:
                center_screen = (int(self.infantry.center[0]), int(self.infantry.center[1]))
                target_screen = (int(self.infantry.target[0]), int(self.infantry.target[1]))
                target_radius = 4

            pygame.draw.line(surface, (255, 255, 100), center_screen, target_screen, 1)
            pygame.draw.circle(surface, (255, 255, 100), target_screen, target_radius, 1)

    def move_to(self, x, y):
        """Squads can only move if no parent or if parent allows it"""
        if self.controllable:  # Should be False for squads
            self.infantry.move_to(x, y)

    def contains_point(self, x, y):
        return self.infantry.contains_point(x, y)

    def set_gradient(self, gx, gy):
        self.infantry.set_gradient(gx, gy)


class Platoon(MilitaryUnit):
    """Platoon level - 3 squads + HQ, controllable"""

    def __init__(self, center_x, center_y, unit_id=None):
        super().__init__("platoon", center_x, center_y, unit_id)

        # Create 3 squads in proper line formation
        # Each squad width = (cols-1) * x_spacing = (5-1) * 3 = 12m
        squad_width = 12
        squad_spacing = squad_width + 8  # Squad width + 8m gap = 20m
        positions = [
            (center_x - squad_spacing, center_y),     # Left squad
            (center_x, center_y),                     # Center squad (HQ)
            (center_x + squad_spacing, center_y)      # Right squad
        ]

        for i, (sx, sy) in enumerate(positions):
            squad_id = f"{self.unit_id}_squad_{i+1}"
            squad = Squad(sx, sy, squad_id)
            squad.parent_unit = self
            squad.unit_number = i + 1
            squad.unit_name = f"Squad {i + 1}"
            self.child_units.append(squad)
            self.visual_units.append(squad)

    def update(self, dt):
        """Update all squads in the platoon"""
        for squad in self.child_units:
            squad.update(dt)

        # Update platoon center as average of squad positions
        if self.child_units:
            positions = [squad.center for squad in self.child_units]
            self.center = np.mean(positions, axis=0)

    def draw(self, surface, camera=None):
        """Draw all squads and platoon indicator if selected"""
        for squad in self.child_units:
            squad.draw(surface, camera)

        # Draw platoon boundary if selected or parent is selected
        if self.selected or (self.parent_selected and self.sub_unit_index >= 0):
            # Get all soldier positions from all squads in this platoon
            all_soldier_positions = []
            for squad in self.child_units:
                all_soldier_positions.extend(squad.infantry.soldiers)

            if all_soldier_positions and camera:
                # Transform all soldier positions to screen coordinates
                screen_positions = [camera.world_to_screen(pos[0], pos[1]) for pos in all_soldier_positions]

                # Find min/max screen coordinates
                screen_xs = [pos[0] for pos in screen_positions]
                screen_ys = [pos[1] for pos in screen_positions]

                min_x = min(screen_xs) - 10  # Simple pixel margin
                max_x = max(screen_xs) + 10
                min_y = min(screen_ys) - 10
                max_y = max(screen_ys) + 10

            elif all_soldier_positions:
                # Fallback without camera
                world_xs = [pos[0] for pos in all_soldier_positions]
                world_ys = [pos[1] for pos in all_soldier_positions]
                min_x = min(world_xs) - 10
                max_x = max(world_xs) + 10
                min_y = min(world_ys) - 10
                max_y = max(world_ys) + 10
            else:
                return  # No positions to draw

            if self.selected:
                color = (100, 255, 100)  # Green for direct selection
                thickness = 2
            else:
                # Use sub-unit specific color when parent is selected
                from settings import SUB_UNIT_COLORS
                color = SUB_UNIT_COLORS[self.sub_unit_index % len(SUB_UNIT_COLORS)]
                thickness = 2

            pygame.draw.rect(surface, color,
                           (int(min_x), int(min_y),
                            int(max_x - min_x), int(max_y - min_y)), thickness)

            # Draw unit name above rectangle if selected
            if self.selected:
                display_name = self.get_display_name()
                if display_name:
                    # Create a simple font (we'll improve this)
                    font = pygame.font.SysFont("monospace", 12)
                    name_surf = font.render(display_name, True, (255, 255, 255))
                    name_rect = name_surf.get_rect()

                    # Position above the rectangle, centered
                    name_x = (min_x + max_x) // 2 - name_rect.width // 2
                    name_y = min_y - 18

                    # Draw background for better visibility
                    bg_rect = pygame.Rect(name_x - 2, name_y - 2, name_rect.width + 4, name_rect.height + 4)
                    pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect)
                    pygame.draw.rect(surface, (255, 255, 255), bg_rect, 1)

                    surface.blit(name_surf, (name_x, name_y))

    def move_to(self, x, y):
        """Move entire platoon, maintaining formation"""
        if not self.controllable:
            return

        # Calculate offset from current center to target
        offset = np.array([x, y]) - self.center

        # Move each squad by the same offset
        for squad in self.child_units:
            new_pos = squad.center + offset
            squad.infantry.move_to(new_pos[0], new_pos[1])

    def contains_point(self, x, y):
        """Check if point is within any squad"""
        return any(squad.contains_point(x, y) for squad in self.child_units)

    def set_gradient(self, gx, gy):
        """Set terrain gradient for all squads"""
        for squad in self.child_units:
            squad.set_gradient(gx, gy)


class Company(MilitaryUnit):
    """Company level - 3 platoons + heavy weapons, controllable"""

    def __init__(self, center_x, center_y, unit_id=None):
        super().__init__("company", center_x, center_y, unit_id)

        # Create 3 platoons in proper triangular formation
        # Each platoon spans 3 squads: width = 2*20 + 12 = 52px (updated for new spacing)
        platoon_width = 52
        platoon_spacing = platoon_width + 15  # Platoon width + 15px gap = 67px
        vertical_offset = 40  # Vertical spacing for triangle

        positions = [
            (center_x, center_y - vertical_offset),           # Front platoon
            (center_x - platoon_spacing//2, center_y + vertical_offset//2),  # Left rear
            (center_x + platoon_spacing//2, center_y + vertical_offset//2)   # Right rear
        ]

        for i, (px, py) in enumerate(positions):
            platoon_id = f"{self.unit_id}_platoon_{i+1}"
            platoon = Platoon(px, py, platoon_id)
            platoon.parent_unit = self
            platoon.unit_number = i + 1
            platoon.unit_name = f"Platoon {i + 1}"
            self.child_units.append(platoon)
            self.visual_units.append(platoon)

    def update(self, dt):
        """Update all platoons in the company"""
        for platoon in self.child_units:
            platoon.update(dt)

        # Update company center
        if self.child_units:
            positions = [platoon.center for platoon in self.child_units]
            self.center = np.mean(positions, axis=0)

    def draw(self, surface, camera=None):
        """Draw all platoons and company indicator if selected"""
        for platoon in self.child_units:
            platoon.draw(surface, camera)

        # Draw company boundary if selected
        if self.selected:
            # Get all soldier positions from all squads in all platoons
            all_soldier_positions = []
            for platoon in self.child_units:
                for squad in platoon.child_units:
                    all_soldier_positions.extend(squad.infantry.soldiers)

            if all_soldier_positions and camera:
                # Transform all soldier positions to screen coordinates
                screen_positions = [camera.world_to_screen(pos[0], pos[1]) for pos in all_soldier_positions]

                # Find min/max screen coordinates
                screen_xs = [pos[0] for pos in screen_positions]
                screen_ys = [pos[1] for pos in screen_positions]

                min_x = min(screen_xs) - 15  # Slightly larger margin for company
                max_x = max(screen_xs) + 15
                min_y = min(screen_ys) - 15
                max_y = max(screen_ys) + 15

            elif all_soldier_positions:
                # Fallback without camera
                world_xs = [pos[0] for pos in all_soldier_positions]
                world_ys = [pos[1] for pos in all_soldier_positions]
                min_x = min(world_xs) - 15
                max_x = max(world_xs) + 15
                min_y = min(world_ys) - 15
                max_y = max(world_ys) + 15
            else:
                return  # No positions to draw

            pygame.draw.rect(surface, (255, 100, 100),
                           (int(min_x), int(min_y),
                            int(max_x - min_x), int(max_y - min_y)), 3)

            # Draw company name above rectangle
            display_name = self.get_display_name()
            if display_name:
                font = pygame.font.SysFont("monospace", 12)
                name_surf = font.render(display_name, True, (255, 255, 255))
                name_rect = name_surf.get_rect()

                # Position above the rectangle, centered
                name_x = (min_x + max_x) // 2 - name_rect.width // 2
                name_y = min_y - 18

                # Draw background for better visibility
                bg_rect = pygame.Rect(name_x - 2, name_y - 2, name_rect.width + 4, name_rect.height + 4)
                pygame.draw.rect(surface, (0, 0, 0, 180), bg_rect)
                pygame.draw.rect(surface, (255, 255, 255), bg_rect, 1)

                surface.blit(name_surf, (name_x, name_y))

    def move_to(self, x, y):
        """Move entire company, maintaining formation"""
        if not self.controllable:
            return

        # Calculate offset from current center to target
        offset = np.array([x, y]) - self.center

        # Move each platoon by the same offset
        for platoon in self.child_units:
            new_pos = platoon.center + offset
            platoon.move_to(new_pos[0], new_pos[1])

    def contains_point(self, x, y):
        """Check if point is within any platoon"""
        return any(platoon.contains_point(x, y) for platoon in self.child_units)

    def set_gradient(self, gx, gy):
        """Set terrain gradient for all platoons"""
        for platoon in self.child_units:
            platoon.set_gradient(gx, gy)


class CommandContext:
    """Manages the current command context level and switching"""

    def __init__(self):
        self.config = load_unit_config()
        self.controllable_units = self.config["command_structure"]["controllable_units"]
        self.current_level_index = 0  # Start with platoon
        self.current_level = self.controllable_units[self.current_level_index]

    def switch_level(self, direction):
        """Switch command level up (1) or down (-1)"""
        new_index = self.current_level_index + direction
        if 0 <= new_index < len(self.controllable_units):
            self.current_level_index = new_index
            self.current_level = self.controllable_units[self.current_level_index]
            return True
        return False

    def get_level_info(self):
        """Get current level info for UI display"""
        unit_info = self.config["units"][self.current_level]
        return {
            "name": self.current_level.title(),
            "size": unit_info["size"],
            "leadership": unit_info["leadership"],
            "description": unit_info["description"]
        }

    def get_keyboard_shortcuts(self):
        """Get keyboard shortcuts for each level"""
        shortcuts = {}
        for i, level in enumerate(self.controllable_units):
            shortcuts[i + 1] = level.title()  # 1=Platoon, 2=Company, etc.
        return shortcuts