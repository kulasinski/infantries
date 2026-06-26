"""
Dynamic scale bar with metric units for the map.
"""
import pygame
import math

def get_appropriate_scale_distance(camera_zoom):
    """
    Calculate an appropriate scale bar distance based on zoom level.
    Returns distance in meters and pixels.
    """
    # Assume 1 pixel = 1 meter at 100% zoom (this is our baseline)
    meters_per_pixel = 1.0 / camera_zoom

    # Target scale bar length in pixels (should be readable but not too long)
    target_pixels = 100

    # Calculate actual meters this would represent
    actual_meters = target_pixels * meters_per_pixel

    # Round to nice metric values
    nice_distances = [1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000, 5000]

    # Find the closest nice distance
    best_distance = min(nice_distances, key=lambda x: abs(x - actual_meters))

    # Calculate pixels for this nice distance
    scale_pixels = best_distance / meters_per_pixel

    return best_distance, int(scale_pixels)

def format_distance(meters):
    """Format distance with appropriate units (m or km)"""
    if meters >= 1000:
        km = meters / 1000
        if km == int(km):
            return f"{int(km)} km"
        else:
            return f"{km:.1f} km"
    else:
        return f"{int(meters)} m"

def draw_scale_bar(surface, camera, font):
    """
    Draw a dynamic scale bar in the upper right corner.
    """
    screen_width = surface.get_width()

    # Get appropriate scale
    distance_meters, scale_pixels = get_appropriate_scale_distance(camera.zoom)

    if scale_pixels < 10:  # Too small to be useful
        return

    # Position in upper right corner
    margin = 20
    bar_y = margin + 20
    bar_end_x = screen_width - margin
    bar_start_x = bar_end_x - scale_pixels

    # Colors
    bar_color = (255, 255, 255)
    text_color = (255, 255, 255)
    background_color = (0, 0, 0)

    # Draw background rectangle for better visibility
    bg_width = scale_pixels + 10
    bg_height = 30
    bg_rect = pygame.Rect(bar_start_x - 5, bar_y - 15, bg_width, bg_height)
    pygame.draw.rect(surface, background_color, bg_rect)
    pygame.draw.rect(surface, bar_color, bg_rect, 1)

    # Draw scale bar
    line_thickness = 2
    tick_height = 8

    # Main horizontal line
    pygame.draw.line(surface, bar_color,
                    (bar_start_x, bar_y), (bar_end_x, bar_y), line_thickness)

    # Start tick
    pygame.draw.line(surface, bar_color,
                    (bar_start_x, bar_y - tick_height//2),
                    (bar_start_x, bar_y + tick_height//2), line_thickness)

    # End tick
    pygame.draw.line(surface, bar_color,
                    (bar_end_x, bar_y - tick_height//2),
                    (bar_end_x, bar_y + tick_height//2), line_thickness)

    # Middle tick (optional, for longer scales)
    if scale_pixels > 80:
        mid_x = (bar_start_x + bar_end_x) // 2
        pygame.draw.line(surface, bar_color,
                        (mid_x, bar_y - tick_height//4),
                        (mid_x, bar_y + tick_height//4), 1)

    # Text label
    distance_text = format_distance(distance_meters)
    text_surf = font.render(distance_text, True, text_color)
    text_rect = text_surf.get_rect()

    # Center text above the scale bar
    text_x = (bar_start_x + bar_end_x) // 2 - text_rect.width // 2
    text_y = bar_y - 12

    surface.blit(text_surf, (text_x, text_y))

def get_world_coordinates_info(camera, mouse_x, mouse_y, font):
    """
    Get world coordinate information for debugging/info display.
    Returns a surface with coordinate text.
    """
    world_x, world_y = camera.screen_to_world(mouse_x, mouse_y)

    coord_text = f"World: ({int(world_x)}, {int(world_y)})"
    text_color = (200, 200, 200)

    return font.render(coord_text, True, text_color)