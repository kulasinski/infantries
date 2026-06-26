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


class Squad(MilitaryUnit):
    """Squad level - basic tactical unit, not directly controllable"""

    def __init__(self, center_x, center_y, unit_id=None):
        super().__init__("squad", center_x, center_y, unit_id)

        # Create Infantry visual representation
        # Squad is 2x5 formation (10 soldiers)
        self.infantry = Infantry(center_x, center_y, cols=5, rows=2)
        self.visual_units = [self.infantry]

    def update(self, dt):
        """Update squad - autonomous movement"""
        self.infantry.update(dt)
        # Update center position from infantry
        self.center = self.infantry.center.copy()

    def draw(self, surface):
        # Override infantry colors if parent is selected
        if self.parent_selected and self.sub_unit_index >= 0:
            # Draw with specific sub-unit color
            from settings import SUB_UNIT_COLORS
            color = SUB_UNIT_COLORS[self.sub_unit_index % len(SUB_UNIT_COLORS)]
            self._draw_infantry_with_color(surface, color)
        else:
            self.infantry.draw(surface)

    def _draw_infantry_with_color(self, surface, color):
        """Draw infantry with custom color"""
        import pygame
        from settings import SOLDIER_RADIUS

        for pos in self.infantry.soldiers:
            pygame.draw.circle(surface, color, (int(pos[0]), int(pos[1])), SOLDIER_RADIUS)

        # Draw movement target if exists
        if self.infantry.target is not None:
            pygame.draw.line(
                surface, (255, 255, 100),
                (int(self.infantry.center[0]), int(self.infantry.center[1])),
                (int(self.infantry.target[0]), int(self.infantry.target[1])),
                1,
            )
            pygame.draw.circle(surface, (255, 255, 100),
                             (int(self.infantry.target[0]), int(self.infantry.target[1])), 4, 1)

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
        # Each squad is 5x2 soldiers: width=(5-1)*9=36px, height=(2-1)*9=9px
        squad_width = 36
        squad_spacing = squad_width + 15  # Squad width + 15px gap = 51px
        positions = [
            (center_x - squad_spacing, center_y),     # Left squad
            (center_x, center_y),                     # Center squad (HQ)
            (center_x + squad_spacing, center_y)      # Right squad
        ]

        for i, (sx, sy) in enumerate(positions):
            squad_id = f"{self.unit_id}_squad_{i+1}"
            squad = Squad(sx, sy, squad_id)
            squad.parent_unit = self
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

    def draw(self, surface):
        """Draw all squads and platoon indicator if selected"""
        for squad in self.child_units:
            squad.draw(surface)

        # Draw platoon boundary if selected or parent is selected
        if self.selected:
            # Calculate bounding box of all squads with proper margins
            positions = [squad.center for squad in self.child_units]
            min_x = min(pos[0] for pos in positions) - 30  # Half squad width + margin
            max_x = max(pos[0] for pos in positions) + 30
            min_y = min(pos[1] for pos in positions) - 20
            max_y = max(pos[1] for pos in positions) + 20

            pygame.draw.rect(surface, (100, 255, 100),
                           (int(min_x), int(min_y),
                            int(max_x - min_x), int(max_y - min_y)), 2)
        elif self.parent_selected and self.sub_unit_index >= 0:
            # Draw with specific sub-unit color when parent company is selected
            from settings import SUB_UNIT_COLORS
            color = SUB_UNIT_COLORS[self.sub_unit_index % len(SUB_UNIT_COLORS)]

            positions = [squad.center for squad in self.child_units]
            min_x = min(pos[0] for pos in positions) - 30
            max_x = max(pos[0] for pos in positions) + 30
            min_y = min(pos[1] for pos in positions) - 20
            max_y = max(pos[1] for pos in positions) + 20

            pygame.draw.rect(surface, color,  # Use sub-unit specific color
                           (int(min_x), int(min_y),
                            int(max_x - min_x), int(max_y - min_y)), 2)

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
        # Each platoon spans 3 squads: width = 2*51 + 36 = 138px
        platoon_width = 138
        platoon_spacing = platoon_width + 20  # Platoon width + 20px gap = 158px
        vertical_offset = 60  # Vertical spacing for triangle

        positions = [
            (center_x, center_y - vertical_offset),           # Front platoon
            (center_x - platoon_spacing//2, center_y + vertical_offset//2),  # Left rear
            (center_x + platoon_spacing//2, center_y + vertical_offset//2)   # Right rear
        ]

        for i, (px, py) in enumerate(positions):
            platoon_id = f"{self.unit_id}_platoon_{i+1}"
            platoon = Platoon(px, py, platoon_id)
            platoon.parent_unit = self
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

    def draw(self, surface):
        """Draw all platoons and company indicator if selected"""
        for platoon in self.child_units:
            platoon.draw(surface)

        # Draw company boundary if selected
        if self.selected:
            positions = [platoon.center for platoon in self.child_units]
            min_x = min(pos[0] for pos in positions) - 80  # Half platoon width + margin
            max_x = max(pos[0] for pos in positions) + 80
            min_y = min(pos[1] for pos in positions) - 40
            max_y = max(pos[1] for pos in positions) + 40

            pygame.draw.rect(surface, (255, 100, 100),
                           (int(min_x), int(min_y),
                            int(max_x - min_x), int(max_y - min_y)), 3)

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