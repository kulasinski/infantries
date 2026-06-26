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


class PlatoonHQ(MilitaryUnit):
    """Platoon headquarters element - Lieutenant, Sergeant, mortar team"""

    def __init__(self, center_x, center_y, unit_id=None):
        super().__init__("platoon", center_x, center_y, unit_id)  # Uses platoon config

        # Create platoon HQ element using formation from YAML
        self.infantry = Infantry(center_x, center_y, unit_type='platoon', formation_name='marching')
        # Override soldier types for HQ element
        self.infantry.soldier_types = ['hq', 'hq', 'mortar', 'rifleman', 'rifleman']
        self.visual_units = [self.infantry]

    def update(self, dt):
        """Update HQ element"""
        self.infantry.update(dt)
        self.center = self.infantry.center.copy()

    def draw(self, surface, camera=None):
        """Draw HQ element with special highlighting if parent selected"""
        if self.parent_selected and self.sub_unit_index >= 0:
            # Draw with specific sub-unit color
            from settings import SUB_UNIT_COLORS
            color = SUB_UNIT_COLORS[self.sub_unit_index % len(SUB_UNIT_COLORS)]
            self._draw_infantry_with_color(surface, color, camera)
        else:
            self.infantry.draw(surface, camera)

    def _draw_infantry_with_color(self, surface, color, camera=None):
        """Draw HQ infantry with custom color override"""
        import pygame
        from settings import SOLDIER_RADIUS
        from soldier_types import draw_soldier_symbol, SOLDIER_TYPES

        # Draw each soldier with custom color but keep their symbols
        for i, pos in enumerate(self.infantry.soldiers):
            soldier_type = self.infantry.soldier_types[i] if i < len(self.infantry.soldier_types) else 'rifleman'

            # For HQ element, we'll just draw in black as specified
            draw_soldier_symbol(surface, pos[0], pos[1], soldier_type, SOLDIER_RADIUS, camera)

    def move_to(self, x, y):
        """HQ element can move if controllable"""
        if self.controllable:
            self.infantry.move_to(x, y)

    def contains_point(self, x, y):
        return self.infantry.contains_point(x, y)

    def set_gradient(self, gx, gy):
        self.infantry.set_gradient(gx, gy)


class Platoon(MilitaryUnit):
    """Platoon level - 3 squads + HQ, controllable"""

    def __init__(self, center_x, center_y, unit_id=None, formation_name='marching'):
        super().__init__("platoon", center_x, center_y, unit_id)
        self.formation_name = formation_name

        # Load formation configuration
        import yaml
        try:
            with open("settings.yaml", "r") as f:
                config = yaml.safe_load(f)
            formation_config = config["formations"]["platoon"][formation_name]
        except:
            # Fallback to default line formation
            formation_config = {
                "squad_spacing": {"x": 20.0, "y": 0.0},
                "hq_element": {
                    "position": "center_rear",
                    "offset": {"x": 0, "y": 15}
                }
            }

        # Create 3 rifle squads
        if "squad_positions" in formation_config:
            # Use explicit positions (e.g., wedge formation)
            positions = [(center_x + pos["x"], center_y + pos["y"])
                        for pos in formation_config["squad_positions"]]
        else:
            # Use spacing-based positions (e.g., line formation)
            spacing = formation_config["squad_spacing"]
            squad_spacing_x = spacing["x"]
            positions = [
                (center_x - squad_spacing_x, center_y),     # Left squad
                (center_x, center_y),                       # Center squad
                (center_x + squad_spacing_x, center_y)      # Right squad
            ]

        # Create squads
        for i, (sx, sy) in enumerate(positions):
            squad_id = f"{self.unit_id}_squad_{i+1}"
            squad = Squad(sx, sy, squad_id)
            squad.parent_unit = self
            squad.unit_number = i + 1
            squad.unit_name = f"Squad {i + 1}"
            self.child_units.append(squad)
            self.visual_units.append(squad)

        # Create Platoon HQ element
        hq_config = formation_config.get("hq_element", {})
        hq_offset = hq_config.get("offset", {"x": 0, "y": 15})
        hq_x = center_x + hq_offset["x"]
        hq_y = center_y + hq_offset["y"]

        platoon_hq_id = f"{self.unit_id}_hq"
        self.platoon_hq = PlatoonHQ(hq_x, hq_y, platoon_hq_id)
        self.platoon_hq.parent_unit = self
        self.platoon_hq.unit_name = "Platoon HQ"

        # Add HQ to child units for selection and drawing
        self.child_units.append(self.platoon_hq)
        self.visual_units.append(self.platoon_hq)

    def update(self, dt):
        """Update all squads and platoon HQ"""
        for unit in self.child_units:
            unit.update(dt)

        # Update platoon center as average of all unit positions
        if self.child_units:
            positions = [unit.center for unit in self.child_units]
            self.center = np.mean(positions, axis=0)

    def draw(self, surface, camera=None):
        """Draw all squads, platoon HQ, and platoon indicator if selected"""
        for unit in self.child_units:
            unit.draw(surface, camera)

        # Draw platoon boundary if selected or parent is selected
        if self.selected or (self.parent_selected and self.sub_unit_index >= 0):
            # Get all soldier positions from all squads and HQ in this platoon
            all_soldier_positions = []
            for unit in self.child_units:
                if hasattr(unit, 'infantry') and hasattr(unit.infantry, 'soldiers'):
                    all_soldier_positions.extend(unit.infantry.soldiers)
                elif hasattr(unit, 'child_units'):  # In case of nested units
                    for child in unit.child_units:
                        if hasattr(child, 'infantry'):
                            all_soldier_positions.extend(child.infantry.soldiers)

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

        # Move each unit (squads + HQ) by the same offset
        for unit in self.child_units:
            new_pos = unit.center + offset
            if hasattr(unit, 'infantry'):
                unit.infantry.move_to(new_pos[0], new_pos[1])
            else:
                unit.move_to(new_pos[0], new_pos[1])

    def contains_point(self, x, y):
        """Check if point is within any squad or platoon HQ"""
        return any(unit.contains_point(x, y) for unit in self.child_units)

    def set_gradient(self, gx, gy):
        """Set terrain gradient for all squads and platoon HQ"""
        for unit in self.child_units:
            unit.set_gradient(gx, gy)


class CompanyHQ(MilitaryUnit):
    """Company headquarters element - Captain, staff, communications"""

    def __init__(self, center_x, center_y, unit_id=None):
        super().__init__("company", center_x, center_y, unit_id)

        # Create company HQ element using formation from YAML
        self.infantry = Infantry(center_x, center_y, unit_type='company', formation_name='marching')
        # Override soldier types for Company HQ (Captain, XO, 1st Sgt, etc.)
        self.infantry.soldier_types = ['hq', 'hq', 'hq', 'rifleman', 'rifleman']
        self.visual_units = [self.infantry]

    def update(self, dt):
        self.infantry.update(dt)
        self.center = self.infantry.center.copy()

    def draw(self, surface, camera=None):
        if self.parent_selected and self.sub_unit_index >= 0:
            from settings import SUB_UNIT_COLORS
            color = SUB_UNIT_COLORS[self.sub_unit_index % len(SUB_UNIT_COLORS)]
            self._draw_infantry_with_color(surface, color, camera)
        else:
            self.infantry.draw(surface, camera)

    def _draw_infantry_with_color(self, surface, color, camera=None):
        from settings import SOLDIER_RADIUS
        from soldier_types import draw_soldier_symbol
        for i, pos in enumerate(self.infantry.soldiers):
            soldier_type = self.infantry.soldier_types[i] if i < len(self.infantry.soldier_types) else 'rifleman'
            draw_soldier_symbol(surface, pos[0], pos[1], soldier_type, SOLDIER_RADIUS, camera)

    def move_to(self, x, y):
        if self.controllable:
            self.infantry.move_to(x, y)

    def contains_point(self, x, y):
        return self.infantry.contains_point(x, y)

    def set_gradient(self, gx, gy):
        self.infantry.set_gradient(gx, gy)


class HeavyWeaponsSection(MilitaryUnit):
    """Heavy weapons section - machine guns or mortars"""

    def __init__(self, center_x, center_y, unit_id=None, section_type="mg"):
        super().__init__("company", center_x, center_y, unit_id)
        self.section_type = section_type

        # Create appropriate formation based on section type
        if section_type == "mg":
            # Heavy machine gun section: 2 MG teams + section leader
            pattern = [["mg", "rifleman", "mg", "rifleman"],
                      ["hq", "rifleman", "rifleman", "rifleman"]]
        else:  # mortar section
            # 81mm mortar section: 2 mortar teams + section leader
            pattern = [["mortar", "rifleman", "mortar", "rifleman"],
                      ["hq", "rifleman", "rifleman", "rifleman"]]

        # Create custom infantry formation
        self.infantry = Infantry(center_x, center_y, cols=4, rows=2, unit_type='company')
        self.infantry.soldier_types = [soldier for row in pattern for soldier in row]
        self.visual_units = [self.infantry]

    def update(self, dt):
        self.infantry.update(dt)
        self.center = self.infantry.center.copy()

    def draw(self, surface, camera=None):
        if self.parent_selected and self.sub_unit_index >= 0:
            from settings import SUB_UNIT_COLORS
            color = SUB_UNIT_COLORS[self.sub_unit_index % len(SUB_UNIT_COLORS)]
            self._draw_infantry_with_color(surface, color, camera)
        else:
            self.infantry.draw(surface, camera)

    def _draw_infantry_with_color(self, surface, color, camera=None):
        from settings import SOLDIER_RADIUS
        from soldier_types import draw_soldier_symbol
        for i, pos in enumerate(self.infantry.soldiers):
            soldier_type = self.infantry.soldier_types[i] if i < len(self.infantry.soldier_types) else 'rifleman'
            draw_soldier_symbol(surface, pos[0], pos[1], soldier_type, SOLDIER_RADIUS, camera)

    def move_to(self, x, y):
        if self.controllable:
            self.infantry.move_to(x, y)

    def contains_point(self, x, y):
        return self.infantry.contains_point(x, y)

    def set_gradient(self, gx, gy):
        self.infantry.set_gradient(gx, gy)


class Company(MilitaryUnit):
    """Company level - 3 platoons + heavy weapons, controllable"""

    def __init__(self, center_x, center_y, unit_id=None, formation_name='marching'):
        super().__init__("company", center_x, center_y, unit_id)
        self.formation_name = formation_name

        # Load formation configuration
        import yaml
        try:
            with open("settings.yaml", "r") as f:
                config = yaml.safe_load(f)
            formation_config = config["formations"]["company"][formation_name]
        except:
            # Fallback to simple triangle formation
            formation_config = {
                "rifle_platoons": {
                    "positions": [
                        {"x": 0, "y": -40},
                        {"x": -35, "y": 20},
                        {"x": 35, "y": 20}
                    ]
                },
                "company_hq": {"position": {"x": 0, "y": 50}},
                "heavy_weapons_platoon": {
                    "elements": {
                        "mg_section": {"position": {"x": -20, "y": 45}},
                        "mortar_section": {"position": {"x": 20, "y": 45}}
                    }
                }
            }

        # Create 3 rifle platoons
        rifle_config = formation_config["rifle_platoons"]
        positions = [(center_x + pos["x"], center_y + pos["y"])
                    for pos in rifle_config["positions"]]

        for i, (px, py) in enumerate(positions):
            platoon_id = f"{self.unit_id}_rifle_platoon_{i+1}"
            # Use appropriate platoon formation based on company formation
            platoon_formation = 'wedge' if formation_name == 'assault' else 'marching'
            platoon = Platoon(px, py, platoon_id, platoon_formation)
            platoon.parent_unit = self
            platoon.unit_number = i + 1
            platoon.unit_name = f"Rifle Platoon {i + 1}"
            self.child_units.append(platoon)
            self.visual_units.append(platoon)

        # Create Company HQ
        hq_config = formation_config["company_hq"]
        hq_pos = hq_config["position"]
        hq_x = center_x + hq_pos["x"]
        hq_y = center_y + hq_pos["y"]

        company_hq_id = f"{self.unit_id}_hq"
        self.company_hq = CompanyHQ(hq_x, hq_y, company_hq_id)
        self.company_hq.parent_unit = self
        self.company_hq.unit_name = "Company HQ"
        self.child_units.append(self.company_hq)
        self.visual_units.append(self.company_hq)

        # Create Heavy Weapons Platoon elements
        hw_config = formation_config["heavy_weapons_platoon"]["elements"]

        # Machine Gun Section (2 heavy MGs)
        mg_pos = hw_config["mg_section"]["position"]
        mg_x = center_x + mg_pos["x"]
        mg_y = center_y + mg_pos["y"]

        mg_section_id = f"{self.unit_id}_mg_section"
        self.mg_section = HeavyWeaponsSection(mg_x, mg_y, mg_section_id, "mg")
        self.mg_section.parent_unit = self
        self.mg_section.unit_name = "Heavy MG Section"
        self.child_units.append(self.mg_section)
        self.visual_units.append(self.mg_section)

        # Mortar Section (2 x 81mm mortars)
        mortar_pos = hw_config["mortar_section"]["position"]
        mortar_x = center_x + mortar_pos["x"]
        mortar_y = center_y + mortar_pos["y"]

        mortar_section_id = f"{self.unit_id}_mortar_section"
        self.mortar_section = HeavyWeaponsSection(mortar_x, mortar_y, mortar_section_id, "mortar")
        self.mortar_section.parent_unit = self
        self.mortar_section.unit_name = "81mm Mortar Section"
        self.child_units.append(self.mortar_section)
        self.visual_units.append(self.mortar_section)

    def update(self, dt):
        """Update all elements in the company"""
        for unit in self.child_units:
            unit.update(dt)

        # Update company center as average of all unit positions
        if self.child_units:
            positions = [unit.center for unit in self.child_units]
            self.center = np.mean(positions, axis=0)

    def draw(self, surface, camera=None):
        """Draw all elements and company indicator if selected"""
        for unit in self.child_units:
            unit.draw(surface, camera)

        # Draw company boundary if selected
        if self.selected:
            # Get all soldier positions from all units in company
            all_soldier_positions = []
            for unit in self.child_units:
                if hasattr(unit, 'infantry') and hasattr(unit.infantry, 'soldiers'):
                    # Direct infantry unit (HQ, Heavy Weapons)
                    all_soldier_positions.extend(unit.infantry.soldiers)
                elif hasattr(unit, 'child_units'):
                    # Platoon with squads
                    for child in unit.child_units:
                        if hasattr(child, 'infantry') and hasattr(child.infantry, 'soldiers'):
                            all_soldier_positions.extend(child.infantry.soldiers)

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

        # Move all units (platoons, HQ, heavy weapons) by the same offset
        for unit in self.child_units:
            new_pos = unit.center + offset
            if hasattr(unit, 'infantry'):
                # Direct infantry unit
                unit.infantry.move_to(new_pos[0], new_pos[1])
            else:
                # Complex unit (platoon)
                unit.move_to(new_pos[0], new_pos[1])

    def contains_point(self, x, y):
        """Check if point is within any company element"""
        return any(unit.contains_point(x, y) for unit in self.child_units)

    def set_gradient(self, gx, gy):
        """Set terrain gradient for all company elements"""
        for unit in self.child_units:
            unit.set_gradient(gx, gy)


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