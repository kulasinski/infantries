import pygame
import sys
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, MAP_WIDTH, MAP_HEIGHT
from terrain import generate_heightmap, render_terrain, compute_gradient
from infantry import Infantry
from units import Company, CommandContext
from camera import Camera
from scale_bar import draw_scale_bar


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Infantries")
    clock = pygame.time.Clock()

    heightmap = generate_heightmap()
    gx, gy = compute_gradient(heightmap)

    # Create terrain surface that covers the whole map
    terrain_surface = pygame.Surface((MAP_WIDTH, MAP_HEIGHT))
    render_terrain(heightmap, terrain_surface)

    # Create a single company with hierarchical structure
    company = Company(center_x=600, center_y=400, unit_id="Alpha_Company")
    company.unit_name = "Alpha Company"
    company.unit_number = 1
    company.set_gradient(gx, gy)

    # Command context for switching between levels
    command_context = CommandContext()

    # Camera system - center on company position
    camera = Camera(initial_center_x=600, initial_center_y=400)

    selected_unit = None

    font = pygame.font.SysFont("monospace", 13)

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                # Keyboard shortcuts for command levels (1-4 keys)
                level_keys = {
                    pygame.K_1: 0,  # Platoon
                    pygame.K_2: 1,  # Company
                    pygame.K_3: 2,  # Battalion (when implemented)
                    pygame.K_4: 3,  # Regiment (when implemented)
                }

                # Zoom controls
                if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    # Zoom in (+ or = key)
                    mx, my = pygame.mouse.get_pos()
                    camera.handle_zoom(mx, my, True)
                elif event.key == pygame.K_MINUS:
                    # Zoom out (- key)
                    mx, my = pygame.mouse.get_pos()
                    camera.handle_zoom(mx, my, False)

                if event.key in level_keys:
                    target_index = level_keys[event.key]
                    if target_index < len(command_context.controllable_units):
                        old_index = command_context.current_level_index
                        command_context.current_level_index = target_index
                        command_context.current_level = command_context.controllable_units[target_index]

                        # Smart selection inheritance
                        new_selected_unit = None

                        if selected_unit:
                            if target_index > old_index:
                                # Going UP (1->2): select parent
                                if hasattr(selected_unit, 'parent_unit') and selected_unit.parent_unit:
                                    new_selected_unit = selected_unit.parent_unit

                            elif target_index < old_index:
                                # Going DOWN (2->1): select first child
                                if hasattr(selected_unit, 'child_units') and selected_unit.child_units:
                                    new_selected_unit = selected_unit.child_units[0]

                        # Clear all selections first
                        company.clear_all_selections()

                        # Apply new selection if we found one
                        if new_selected_unit:
                            new_selected_unit.set_selected(True)
                            selected_unit = new_selected_unit
                        else:
                            selected_unit = None

            if event.type == pygame.MOUSEWHEEL:
                # Handle zoom with mouse wheel (standard RTS behavior)
                mx, my = pygame.mouse.get_pos()
                zoom_in = event.y > 0  # Scroll up = zoom in
                camera.handle_zoom(mx, my, zoom_in)

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                if event.button == 2:  # middle mouse button — start panning
                    camera.start_pan(mx, my)

                elif event.button == 1:  # left click — select
                    selected_unit = None

                    # Clear all selections first
                    company.clear_all_selections()

                    # Convert mouse coordinates to world coordinates
                    world_mx, world_my = camera.screen_to_world(mx, my)

                    # Select based on current command level
                    if command_context.current_level == "company":
                        if company.contains_point(world_mx, world_my):
                            company.set_selected(True)
                            selected_unit = company
                    elif command_context.current_level == "platoon":
                        for platoon in company.child_units:
                            if platoon.contains_point(world_mx, world_my):
                                platoon.set_selected(True)
                                selected_unit = platoon
                                break

                elif event.button == 3 and selected_unit:  # right click — move
                    world_mx, world_my = camera.screen_to_world(mx, my)
                    selected_unit.move_to(world_mx, world_my)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 2:  # middle mouse button release — stop panning
                    camera.stop_pan()

            if event.type == pygame.MOUSEMOTION:
                # Update camera panning if middle mouse is held
                if camera.is_panning:
                    mx, my = event.pos
                    camera.update_pan(mx, my)

        company.update(dt)

        # Clear screen
        screen.fill((0, 0, 0))

        # Draw terrain with camera transform
        # Calculate where to draw the terrain surface on screen
        terrain_screen_x, terrain_screen_y = camera.world_to_screen(0, 0)
        scaled_width = int(MAP_WIDTH * camera.zoom)
        scaled_height = int(MAP_HEIGHT * camera.zoom)

        # Scale terrain surface and draw it
        if camera.zoom != 1.0:
            scaled_terrain = pygame.transform.scale(terrain_surface, (scaled_width, scaled_height))
        else:
            scaled_terrain = terrain_surface

        screen.blit(scaled_terrain, (terrain_screen_x, terrain_screen_y))

        # Draw units
        company.draw(screen, camera)

        # HUD
        hints = [
            "Left-click: select unit",
            "Right-click: move selected unit",
            "Mouse wheel: zoom in/out",
            "Middle mouse drag: pan camera",
            "1: Platoon level, 2: Company level",
            "ESC: quit",
        ]
        for i, line in enumerate(hints):
            surf = font.render(line, True, (220, 220, 220))
            screen.blit(surf, (10, 10 + i * 16))

        # Unit legend
        from soldier_types import get_unit_legend
        legend = get_unit_legend()
        legend_title = font.render("Units:", True, (180, 180, 180))
        screen.blit(legend_title, (10, 10 + (len(hints) + 1) * 16))

        for i, legend_item in enumerate(legend):
            surf = font.render(legend_item, True, (160, 160, 160))
            screen.blit(surf, (20, 10 + (len(hints) + 2 + i) * 16))

        # Command context display
        level_info = command_context.get_level_info()
        zoom_info = camera.get_zoom_info()
        context_text = f"Command Level: {level_info['name']} ({level_info['size']} men) - {level_info['leadership']}"
        zoom_text = f"Zoom: {zoom_info['zoom_percent']}%"

        context_surf = font.render(context_text, True, (100, 255, 100))
        zoom_surf = font.render(zoom_text, True, (100, 200, 255))

        context_y = 10 + (len(hints) + 1 + len(legend) + 1) * 16 + 10
        screen.blit(context_surf, (10, context_y))
        screen.blit(zoom_surf, (10, context_y + 16))

        # Speed display for selected unit (if applicable)
        if selected_unit and hasattr(selected_unit, 'child_units'):
            # For hierarchical units, show if any child unit is moving
            moving_units = []
            for child in selected_unit.child_units:
                if hasattr(child, 'child_units'):  # Platoon level
                    for squad in child.child_units:
                        if hasattr(squad.infantry, 'target') and squad.infantry.target is not None:
                            moving_units.append(squad.infantry)
                elif hasattr(child, 'infantry'):  # Squad level
                    if child.infantry.target is not None:
                        moving_units.append(child.infantry)

            if moving_units:
                avg_speed = sum(unit.current_speed for unit in moving_units) / len(moving_units)
                from settings import MOVE_SPEED
                pct = int(avg_speed / MOVE_SPEED * 100)
                speed_surf = font.render(f"Formation Speed: {pct}%", True, (255, 220, 80))
                speed_y = context_y + 32  # Account for zoom text
                screen.blit(speed_surf, (10, speed_y))

        # Draw scale bar in upper right corner
        draw_scale_bar(screen, camera, font)

        pygame.display.flip()


if __name__ == "__main__":
    main()
