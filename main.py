import pygame
import sys
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from terrain import generate_heightmap, render_terrain, compute_gradient
from infantry import Infantry
from units import Company, CommandContext


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Infantries")
    clock = pygame.time.Clock()

    heightmap = generate_heightmap()
    gx, gy = compute_gradient(heightmap)

    terrain_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    render_terrain(heightmap, terrain_surface)

    # Create a single company with hierarchical structure
    company = Company(center_x=600, center_y=400, unit_id="Alpha_Company")
    company.set_gradient(gx, gy)

    # Command context for switching between levels
    command_context = CommandContext()

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

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                if event.button == 1:  # left click — select
                    selected_unit = None

                    # Clear all selections first
                    company.clear_all_selections()

                    # Select based on current command level
                    if command_context.current_level == "company":
                        if company.contains_point(mx, my):
                            company.set_selected(True)
                            selected_unit = company
                    elif command_context.current_level == "platoon":
                        for platoon in company.child_units:
                            if platoon.contains_point(mx, my):
                                platoon.set_selected(True)
                                selected_unit = platoon
                                break

                if event.button == 3 and selected_unit:  # right click — move
                    selected_unit.move_to(mx, my)

        company.update(dt)

        screen.blit(terrain_surface, (0, 0))
        company.draw(screen)

        # HUD
        hints = [
            "Left-click: select unit",
            "Right-click: move selected unit",
            "1: Platoon level, 2: Company level",
            "ESC: quit",
        ]
        for i, line in enumerate(hints):
            surf = font.render(line, True, (220, 220, 220))
            screen.blit(surf, (10, 10 + i * 16))

        # Command context display
        level_info = command_context.get_level_info()
        context_text = f"Command Level: {level_info['name']} ({level_info['size']} men) - {level_info['leadership']}"
        context_surf = font.render(context_text, True, (100, 255, 100))
        screen.blit(context_surf, (10, 10 + len(hints) * 16 + 10))

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
                screen.blit(speed_surf, (10, 10 + (len(hints) + 1) * 16 + 20))

        pygame.display.flip()


if __name__ == "__main__":
    main()
