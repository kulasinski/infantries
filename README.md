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

## Google

During World War II, a standard infantry division was the smallest military formation capable of completely independent operations, typically numbering 12,000 to 15,000 soldiers. 
Most major powers utilized a triangular division structure, meaning the organization built upward in groups of three (e.g., three rifle squads to a platoon, three platoons to a company, and three regiments to a division).
The Hierarchy of WWII Infantry UnitsSquad / Section (8–12 men): Led by a Sergeant. 

The basic tactical unit built around a central weapon system, usually a light machine gun (like the British Bren or German MG42) or semi-automatic rifles.
Platoon (30–40 men): Led by a Lieutenant. Consisted of three rifle squads and a small headquarters element, sometimes including a light mortar or heavy weapons team.
Company (120–200 men): Led by a Captain. Composed of three rifle platoons, a heavy weapons platoon (heavy machine guns and mortars), and a headquarters unit.
Battalion (800–1,000 men): Led by a Lieutenant Colonel. Composed of three rifle companies, a heavy weapons company, and a headquarters/supply company. This was the lowest level to have its own dedicated staff.
Regiment / Brigade (2,500–3,000 men): Led by a Colonel. Composed of three infantry battalions and supported by dedicated anti-tank and cannon companies.
Division (12,000–15,000 men): Led by a Major General. Composed of three infantry regiments combined with divisional artillery, combat engineers, medical units, and reconnaissance troops.

Division Component Breakdown
A standard WWII triangular infantry division was not just made of infantry; it combined multiple branches of combat arms to fight self-sufficiently:
Infantry Core: Three infantry regiments providing the primary front-line fighting power.Divisional Artillery: Usually four artillery battalions (often three organic light howitzer battalions and one medium howitzer battalion) to provide immediate indirect fire support.Combat Engineers: One battalion responsible for clearing minefields, building bridges, and constructing fortifications.Reconnaissance: A mechanized or cavalry troop tasked with scouting ahead of the division's main advance.Support & Logistics: Dedicated medical, signals, quartermaster, ordnance, and military police companies to sustain the division in the field.Major National VariationsUnited States: Heavily motorized and relied on massive organic artillery support. The US favored a rigid, highly standardized triangular division that remained exceptionally well-supplied.Germany: Utilized a similar triangular structure, but faced severe manpower shortages later in the war, reducing divisions to six battalions instead of nine (the Volksgrenadier model). They also relied heavily on horses for logistics, despite their "blitzkrieg" reputation.Soviet Union: Formed "Rifle Divisions" which were significantly smaller than Western divisions (often numbering only 5,000 to 8,000 men due to high casualties). They compensated for smaller division sizes by massing them into massive "Armies" and "Fronts."Great Britain: Used a "Brigade" system instead of regiments. A British division contained three infantry brigades, but each brigade was made of three battalions from entirely different regional regiments to preserve regional traditions and morale.If you would like to explore deeper, let me know if you want to focus on a specific country's blueprint (like the US or Germany), look into specialized divisions (like airborne or armored), or view the exact weapon loadouts for these units.