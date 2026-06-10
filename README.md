# Infantries

A Total War-style RTS prototype focused on commanding infantry units.

## Assumptions (Phase 1)

- **Top-down 2D view.** The map is rendered as a flat top-down projection with isohypse (contour lines) showing elevation. No camera tilt or 3D projection yet.
- **Procedural terrain.** Height is generated with Gaussian-smoothed noise. Terrain is purely visual — elevation does not yet affect movement speed, line of sight, or combat.
- **Infantry as a formation.** A unit is a rectangular grid of soldiers (cols × rows). The whole unit shares one destination and moves as a block. No individual soldier pathfinding.
- **No collision.** Units can overlap. Pathfinding is direct straight-line movement.
- **No combat.** Phase 1 covers movement and selection only.
- **Mouse controls only.** Left-click selects a unit; right-click orders a move. Voice/NLP command interface is Phase 2.
- **Single map.** No scrolling, zooming, or camera yet.

## Backlog

- [ ] Isometric 3D render mode (in addition to current isohypse top-down view)
- [ ] Terrain affects movement speed (uphill slower)
- [ ] Line-of-sight / fog of war
- [ ] Multiple formation shapes (column, wedge, line, square)
- [ ] Combat: ranged fire, melee
- [ ] Enemy AI units
- [ ] NLP / voice command interface (Phase 2)
- [ ] Map scrolling and zoom
- [ ] Unit morale and fatigue

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Controls

| Input | Action |
|---|---|
| Left-click | Select unit |
| Right-click | Move selected unit to cursor |
| ESC | Quit |

## Project Structure

```
main.py        — game loop, event handling
terrain.py     — heightmap generation, isohypse rendering
infantry.py    — Infantry unit: formation, movement, drawing
settings.py    — global constants
```
