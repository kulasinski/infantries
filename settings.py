SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

MAP_WIDTH = 1200
MAP_HEIGHT = 800

ISOHYPSE_LEVELS = 5
ISOHYPSE_COLOR = (35, 22, 8)

INFANTRY_COLOR = (210, 55, 55)
SELECTED_COLOR = (255, 210, 40)

# Hierarchical selection colors for sub-units
SUB_UNIT_COLORS = [
    (255, 255, 100),  # Yellow - first sub-unit
    (100, 150, 255),  # Blue - second sub-unit
    (255, 100, 200),  # Pink - third sub-unit
    (100, 255, 200),  # Teal - fourth sub-unit
    (150, 50, 100),   # Maroon - fifth sub-unit
]

SOLDIER_SPACING = 9
SOLDIER_RADIUS = 3
MOVE_SPEED = 80       # pixels per second on flat ground
SLOPE_PENALTY = 150.0  # speed multiplier reduction per unit of uphill slope
MIN_SPEED_FRAC = 0.2  # floor: unit never moves slower than 20% of base speed

# Camera/zoom settings
DEFAULT_ZOOM = 1.0
MIN_ZOOM = 0.5
MAX_ZOOM = 3.0
ZOOM_STEP = 0.1
