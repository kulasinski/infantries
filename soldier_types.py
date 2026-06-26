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
    },
    'radio': {
        'name': 'Radio Operator',
        'symbol': 'radio',
        'color': (100, 255, 100),  # Green for communications
    }
}

def draw_soldier_symbol(surface, x, y, soldier_type, radius=3, camera=None):
    """Draw a soldier symbol at the given position"""
    if soldier_type not in SOLDIER_TYPES:
        soldier_type = 'rifleman'

    config = SOLDIER_TYPES[soldier_type]
    symbol = config['symbol']
    color = config['color']

    # Apply camera transformation if provided
    if camera:
        x, y = camera.world_to_screen(x, y)
        radius = camera.get_scaled_radius(radius)

    # Convert to integer coordinates
    x, y = int(x), int(y)

    if symbol == 'rifle':
        # Draw a small vertical line for rifle (scale with zoom)
        line_width = max(1, radius // 2)
        pygame.draw.line(surface, color, (x, y-radius), (x, y+radius), line_width)
        # Add small dot for soldier
        dot_radius = max(1, radius // 2)
        pygame.draw.circle(surface, color, (x, y), dot_radius)

    elif symbol == 'radio':
        # Draw wavy lines for radio waves (scale with zoom)
        line_size = max(2, radius)
        line_width = max(1, radius // 3)
        pygame.draw.line(surface, color, (x-line_size, y-line_size), (x+line_size, y+line_size), line_width)
        pygame.draw.line(surface, color, (x-line_size, y+line_size), (x+line_size, y-line_size), line_width)
        # Center dot
        dot_radius = max(1, radius // 2)
        pygame.draw.circle(surface, color, (x, y), dot_radius)

    elif symbol == 'mg_cross':
        # Draw cross for machine gun (scale with zoom)
        cross_size = max(2, radius)
        line_width = max(1, radius // 2)
        pygame.draw.line(surface, color, (x-cross_size, y), (x+cross_size, y), line_width)
        pygame.draw.line(surface, color, (x, y-cross_size), (x, y+cross_size), line_width)

    elif symbol == 'mortar_dot':
        # Draw larger dot for mortar
        pygame.draw.circle(surface, color, (x, y), radius)
        # Add small inner dot
        inner_radius = max(1, radius // 2)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), inner_radius)

    else:
        # Fallback: regular circle
        pygame.draw.circle(surface, color, (x, y), radius)


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


def get_platoon_hq_composition():
    """Return the composition of platoon headquarters element"""
    return [
        'hq',     # Platoon leader (Lieutenant)
        'hq',     # Platoon sergeant
        'radio',  # Radio operator
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
            elif i % 10 == 0:  # Every 10th soldier is radio
                types.append('radio')
            else:
                types.append('rifleman')
        return types


def get_unit_legend():
    """Return legend information for UI display"""
    legend = []
    for type_key, config in SOLDIER_TYPES.items():
        symbol_desc = {
            'rifle': '|',
            'radio': '~',
            'mg_cross': '+',
            'mortar_dot': '●',
        }.get(config['symbol'], '○')

        legend.append(f"{symbol_desc} {config['name']}")

    return legend