import pygame
import numpy as np
from scipy.ndimage import gaussian_filter
from settings import MAP_WIDTH, MAP_HEIGHT, ISOHYPSE_LEVELS, ISOHYPSE_COLOR


def generate_heightmap(seed=42):
    rng = np.random.default_rng(seed)
    xs = np.linspace(0, 1, MAP_WIDTH)
    ys = np.linspace(0, 1, MAP_HEIGHT)
    xg, yg = np.meshgrid(xs, ys)

    # Right half is elevated: smooth sigmoid transition at x=0.5
    flat_mask = 1.0 / (1.0 + np.exp(-20 * (xg - 0.52)))

    # Longitudinal ridge running roughly along y=0.5, on the right half
    ridge_y_center = 0.5
    ridge_width = 0.18
    ridge = np.exp(-((yg - ridge_y_center) ** 2) / (2 * ridge_width ** 2))

    # Single peak: tallest point on the ridge, at about 75% along x
    peak_x, peak_y = 0.75, 0.50
    peak_rx, peak_ry = 0.10, 0.09
    peak = np.exp(-(((xg - peak_x) / peak_rx) ** 2 + ((yg - peak_y) / peak_ry) ** 2))

    h = flat_mask * (0.5 * ridge + 0.5 * peak)

    # Light noise so the flat plain isn't perfectly zero and contours look natural
    noise = rng.random((MAP_HEIGHT, MAP_WIDTH)).astype(np.float32)
    noise = gaussian_filter(noise, sigma=12) * 0.04
    h = h + noise

    h = (h - h.min()) / (h.max() - h.min())
    return h.astype(np.float32)


def height_at(heightmap, x, y):
    xi = int(np.clip(x, 0, MAP_WIDTH - 1))
    yi = int(np.clip(y, 0, MAP_HEIGHT - 1))
    return float(heightmap[yi, xi])


def render_terrain(heightmap, surface):
    # Shade each pixel by elevation: flat=dark green, elevated=lighter
    r = (50 + (heightmap * 40)).astype(np.uint8)
    g = (85 + (heightmap * 50)).astype(np.uint8)
    b = (30 + (heightmap * 20)).astype(np.uint8)
    rgb = np.stack([r, g, b], axis=2)
    pygame.surfarray.blit_array(surface, rgb.transpose(1, 0, 2))

    for level in range(1, ISOHYPSE_LEVELS + 1):
        threshold = level / ISOHYPSE_LEVELS
        _draw_contour(heightmap, surface, threshold)


def _draw_contour(heightmap, surface, threshold):
    h, w = heightmap.shape
    step = 3  # sample every N pixels for performance

    for y in range(0, h - step, step):
        for x in range(0, w - step, step):
            v00 = heightmap[y, x]
            v10 = heightmap[y, x + step] if x + step < w else v00
            v01 = heightmap[y + step, x] if y + step < h else v00

            crosses_h = (v00 < threshold) != (v10 < threshold)
            crosses_v = (v00 < threshold) != (v01 < threshold)

            if crosses_h:
                t = (threshold - v00) / (v10 - v00 + 1e-9)
                px = int(x + t * step)
                py = y
                pygame.draw.circle(surface, ISOHYPSE_COLOR, (px, py), 1)

            if crosses_v:
                t = (threshold - v00) / (v01 - v00 + 1e-9)
                px = x
                py = int(y + t * step)
                pygame.draw.circle(surface, ISOHYPSE_COLOR, (px, py), 1)
