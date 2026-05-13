# Pirate Island Explorer

A Pygame-based exploration game where you navigate a procedurally generated island to find hidden treasure — before your stamina runs out.

Press **G** at any time to watch Dijkstra's algorithm find the optimal path for you.

---

## Gameplay

- Move around the island using the arrow keys
- Different terrain costs different stamina: Sand is cheapest, Forest costs more, Rocks cost the most
- Your stamina is limited — plan your route wisely
- Reach the treasure chest before you run out of stamina to win
- Press **G** to summon the AI and watch it solve the level using Dijkstra's algorithm

## Controls

| Key | Action |
|-----|--------|
| Arrow keys | Move player |
| G | Run AI pathfinder (Dijkstra) |
| Space | Start game (from menu) |
| ESC | Return to menu |

## Terrain Costs

| Terrain | Stamina Cost |
|---------|-------------|
| Sand | x1 |
| Forest | x2 |
| Rock | x3 |
| Water | Impassable |

## Difficulty Levels

| Level | Name |
|-------|------|
| 1 | Easy |
| 2 | Normal |
| 3 | Hard |
| 4 | Expert |
| 5 | Master |

Higher levels generate denser terrain and give you less stamina buffer.

---

## How It Works

The game uses two graph algorithms:

- **DFS** (`dfs.py`) — run at game start to map out all reachable tiles from the player's starting position
- **Dijkstra's Algorithm** (`dijkstra.py`) — finds the shortest (least stamina) path from the player to the treasure, weighted by terrain cost

Stamina given to the player each level is calculated as:
```
starting_stamina = optimal_cost + stamina_buffer
stamina_buffer = max(15 - (level * 2), 5)
```

This ensures every level is solvable, but tighter at higher difficulties.

---

## Project Structure

```
pirate_island_explorer/
- main.py         # Game loop, rendering, input handling
- player.py       # Player state and movement
- map_data.py     # Procedural map generation
- dijkstra.py     # Dijkstra shortest path algorithm
- dfs.py          # DFS for reachability mapping
- settings.py     # Constants (screen size, colors, tile size)
- assets/         # Images (pirate, treasure, terrain tiles, icons)
```

---

## Requirements

- Python 3.x
- Pygame

Install dependencies:

```bash
pip install pygame
```

Run the game:

```bash
python main.py
```
