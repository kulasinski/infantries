import pygame
import sys
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from terrain import generate_heightmap, render_terrain, compute_gradient
from infantry import Infantry


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Infantries")
    clock = pygame.time.Clock()

    heightmap = generate_heightmap()
    gx, gy = compute_gradient(heightmap)

    terrain_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    render_terrain(heightmap, terrain_surface)

    units = [
        Infantry(center_x=600, center_y=400, cols=20, rows=5),
    ]
    for unit in units:
        unit.set_gradient(gx, gy)
    selected_unit = None

    font = pygame.font.SysFont("monospace", 13)

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos

                if event.button == 1:  # left click — select
                    selected_unit = None
                    for unit in units:
                        unit.selected = False
                    for unit in units:
                        if unit.contains_point(mx, my):
                            unit.selected = True
                            selected_unit = unit
                            break

                if event.button == 3 and selected_unit:  # right click — move
                    selected_unit.move_to(mx, my)

        for unit in units:
            unit.update(dt)

        screen.blit(terrain_surface, (0, 0))

        for unit in units:
            unit.draw(screen)

        # HUD
        hints = [
            "Left-click: select unit",
            "Right-click: move selected unit",
            "ESC: quit",
        ]
        for i, line in enumerate(hints):
            surf = font.render(line, True, (220, 220, 220))
            screen.blit(surf, (10, 10 + i * 16))

        if selected_unit and selected_unit.target is not None:
            from settings import MOVE_SPEED
            pct = int(selected_unit.current_speed / MOVE_SPEED * 100)
            speed_surf = font.render(f"Speed: {pct}%", True, (255, 220, 80))
            screen.blit(speed_surf, (10, 10 + len(hints) * 16 + 6))

        pygame.display.flip()


if __name__ == "__main__":
    main()
