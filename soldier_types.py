"""
Soldier types and their visual representations using mini icons/symbols.
"""
import pygame
import math

# Soldier type definitions
SOLDIER_TYPES = {
    'rifleman': {
        'name': 'Rifleman',
        'symbol': 'rifle',
        'color': (210, 55, 55),  # Standard red
    },
    'hq': {
        'name': 'HQ/Sergeant',
        'symbol': 'radio',
        'color': (255, 215, 0),  # Gold for leadership
    },
    'mg': {
        'name': 'Machine Gun',
        'symbol': 'mg_cross',
        'color': (100, 100, 255),  # Blue for heavy weapons
    },
    'mortar': {
        'name': 'Mortar',
        'symbol': 'mortar_dot',
        'color': (255, 100, 100),  # Light red for indirect fire
    }
}

def draw_soldier_symbol(surface, x, y, soldier_type, radius=3, camera=None):
    """Draw a soldier symbol at the given position using black letters"""
    if soldier_type not in SOLDIER_TYPES:
        soldier_type = 'rifleman'

    # Apply camera transformation if provided
    if camera:
        x, y = camera.world_to_screen(x, y)
        radius = camera.get_scaled_radius(radius)

    # Convert to integer coordinates
    x, y = int(x), int(y)

    # Get the letter for this soldier type
    letter_map = {
        'rifleman': 'R',
        'hq': 'HQ',
        'mg': 'MG',
        'mortar': 'M'
    }

    letter = letter_map.get(soldier_type, 'R')

    # Choose font size based on zoom/radius
    if radius >= 6:
        font_size = 12
    elif radius >= 4:
        font_size = 10
    else:
        font_size = 8

    # Create font and render text in black
    font = pygame.font.Font(None, font_size)
    text_surface = font.render(letter, True, (0, 0, 0))  # Black text
    text_rect = text_surface.get_rect()

    # Center the text on the position
    text_rect.center = (x, y)

    # Draw the letter directly without background
    surface.blit(text_surface, text_rect)


def get_squad_composition():
    """Return the composition of a standard 10-man squad"""
    return [
        'hq',        # Squad leader/sergeant
        'rifleman',  # Rifleman 1
        'rifleman',  # Rifleman 2
        'rifleman',  # Rifleman 3
        'rifleman',  # Rifleman 4
        'mg',        # Machine gunner
        'rifleman',  # Rifleman 5 (MG assistant)
        'rifleman',  # Rifleman 6
        'rifleman',  # Rifleman 7
        'rifleman',  # Rifleman 8
    ]


def get_formation_composition(unit_type, formation_name="marching"):
    """
    Get soldier composition based on formation configuration from YAML.
    Returns flattened list of soldier types in formation order.
    """
    import yaml

    try:
        with open("settings.yaml", "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        # Fallback to default if YAML not found
        return get_squad_composition()

    formations = config.get("formations", {})
    unit_formations = formations.get(unit_type, {})
    formation = unit_formations.get(formation_name, {})
    pattern = formation.get("pattern", [])

    if not pattern:
        # Fallback to original composition
        return get_squad_composition()

    # Flatten the 2D pattern into a 1D list
    composition = []
    for row in pattern:
        composition.extend(row)

    return composition


def get_formation_layout(unit_type, formation_name="marching"):
    """
    Get formation layout information from YAML configuration.
    Returns dict with pattern, spacing, and dimensions.
    """
    import yaml

    try:
        with open("settings.yaml", "r") as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        # Fallback defaults
        return {
            "pattern": [["rifleman", "rifleman", "mg", "rifleman", "rifleman"],
                       ["rifleman", "rifleman", "hq", "rifleman", "rifleman"]],
            "spacing": {"x": 3.0, "y": 3.0},
            "dimensions": {"cols": 5, "rows": 2}
        }

    formations = config.get("formations", {})
    unit_formations = formations.get(unit_type, {})
    formation = unit_formations.get(formation_name, {})

    # Handle platoon HQ element specially
    if unit_type == "platoon" and "hq_element" in formation:
        hq_element = formation["hq_element"]
        return {
            "pattern": hq_element["pattern"],
            "spacing": hq_element["spacing"],
            "dimensions": {
                "cols": len(hq_element["pattern"][0]),
                "rows": len(hq_element["pattern"])
            }
        }

    # Handle company HQ element specially
    if unit_type == "company" and "company_hq" in formation:
        company_hq = formation["company_hq"]
        return {
            "pattern": company_hq["pattern"],
            "spacing": company_hq["spacing"],
            "dimensions": {
                "cols": len(company_hq["pattern"][0]),
                "rows": len(company_hq["pattern"])
            }
        }

    # Provide defaults if missing
    default_layout = {
        "pattern": [["rifleman", "rifleman", "mg", "rifleman", "rifleman"],
                   ["rifleman", "rifleman", "hq", "rifleman", "rifleman"]],
        "spacing": {"x": 3.0, "y": 3.0},
        "dimensions": {"cols": 5, "rows": 2}
    }

    return {
        "pattern": formation.get("pattern", default_layout["pattern"]),
        "spacing": formation.get("spacing", default_layout["spacing"]),
        "dimensions": formation.get("dimensions", default_layout["dimensions"])
    }


def get_platoon_hq_composition():
    """Return the composition of platoon headquarters element"""
    return [
        'hq',     # Platoon leader (Lieutenant)
        'hq',     # Platoon sergeant
        'hq',     # Additional HQ staff
        'mortar', # Mortar team leader
        'rifleman', # Mortar assistant
    ]


def assign_soldier_types(unit_type, total_soldiers):
    """
    Assign soldier types based on unit type and formation size.
    Returns list of soldier types for each position.
    """
    if unit_type == 'squad':
        composition = get_squad_composition()
        # Pad with riflemen if we have more soldiers than composition
        while len(composition) < total_soldiers:
            composition.append('rifleman')
        return composition[:total_soldiers]

    elif unit_type == 'platoon_hq':
        composition = get_platoon_hq_composition()
        while len(composition) < total_soldiers:
            composition.append('rifleman')
        return composition[:total_soldiers]

    else:
        # Default: mostly riflemen with some specialists
        types = []
        for i in range(total_soldiers):
            if i == 0:
                types.append('hq')  # First soldier is always HQ
            elif i % 6 == 0:  # Every 6th soldier is MG
                types.append('mg')
            elif i % 12 == 0:  # Every 12th soldier is mortar
                types.append('mortar')
            else:
                types.append('rifleman')
        return types


def get_unit_legend():
    """Return legend information for UI display"""
    legend = []
    letter_map = {
        'rifleman': 'R',
        'hq': 'HQ',
        'mg': 'MG',
        'mortar': 'M'
    }

    for type_key, config in SOLDIER_TYPES.items():
        letter = letter_map.get(type_key, 'R')
        legend.append(f"{letter} {config['name']}")

    return legend