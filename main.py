import pygame
import sys
import math
import random
from enum import Enum

from settings import *
from map_data import generate_map_with_difficulty, get_random_treasure_position
from player import Player
from dfs import dfs
from dijkstra import dijkstra_shortest_path, get_tile_cost

class GameState(Enum):
    MENU = 1
    LEVEL_SELECT = 2
    PLAYING = 3
    GAME_OVER = 4
    AI_DEMO = 5

pygame.init()
pygame.font.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pirate Island Explorer")
clock = pygame.time.Clock()

title_font  = pygame.font.SysFont("arial", 52, bold=True)
large_font  = pygame.font.SysFont("arial", 36, bold=True)
medium_font = pygame.font.SysFont("arial",  24, bold=True)
small_font  = pygame.font.SysFont("arial",  18)
tiny_font   = pygame.font.SysFont("arial",  14)

_raw = pygame.image.load("assets/pirate.png").convert_alpha()
pirate_img = pygame.transform.scale(_raw, (110, 110))

_raw2 = pygame.image.load("assets/treasure.png").convert_alpha()
treasure_img    = pygame.transform.scale(_raw2, (36, 36))   # game over title
treasure_img_sm = pygame.transform.scale(_raw2, (18, 18))   # HUD

level_img = pygame.transform.scale(pygame.image.load("assets/level.png").convert_alpha(), (22, 22))
steps_img = pygame.transform.scale(pygame.image.load("assets/steps.png").convert_alpha(), (22, 22))
stamina_img = pygame.transform.scale(pygame.image.load("assets/stamina.png").convert_alpha(), (22, 22))

pirate_icon = pygame.transform.scale(pygame.image.load("assets/pirate.png").convert_alpha(), (24, 24))
sand_img = pygame.transform.scale(pygame.image.load("assets/sand.png").convert_alpha(), (16, 16))
forest_img = pygame.transform.scale(pygame.image.load("assets/forest.png").convert_alpha(), (16, 16))
rock_img = pygame.transform.scale(pygame.image.load("assets/rock.png").convert_alpha(), (16, 16))
position_img = pygame.transform.scale(pygame.image.load("assets/position.png").convert_alpha(), (16, 16))
steps_hud_img = pygame.transform.scale(pygame.image.load("assets/steps.png").convert_alpha(), (16, 16))

MAP_W = COLS * TILE_SIZE   # 800
HUD_X = MAP_W
HUD_W = WIDTH - HUD_X      # 400

current_level   = 1
player          = None
visited         = set()
visible_tiles   = set()
explored_tiles  = set()
game_state      = GameState.MENU
game_map        = None
treasure_position = None
animation_counter = 0
ai_path         = []
ai_current_step = 0
particles       = []

menu_stars = [
    (random.randint(0, WIDTH), random.randint(0, HEIGHT // 2), random.random())
    for _ in range(100)
]

# ── helpers ────────────────────────────────────────────────────

def init_game(level):
    global player, visited, visible_tiles, explored_tiles
    global game_map, treasure_position, ai_path, ai_current_step, particles

    game_map          = generate_map_with_difficulty(level)
    treasure_position = get_random_treasure_position(game_map)

    _, optimal_cost   = dijkstra_shortest_path(game_map, 1, 1,
                            treasure_position[0], treasure_position[1])
    stamina_buffer    = max(15 - (level * 2), 5)
    starting_stamina  = optimal_cost + stamina_buffer

    player          = Player(1, 1, max_stamina=starting_stamina)
    visited         = set()
    visible_tiles   = set()
    explored_tiles  = set()
    ai_path         = []
    ai_current_step = 0
    particles       = []

    dfs(game_map, player.row, player.col, visited)
    reveal_area(player.row, player.col)


def reveal_area(row, col, radius=2):
    for r in range(row - radius, row + radius + 1):
        for c in range(col - radius, col + radius + 1):
            if 0 <= r < len(game_map) and 0 <= c < len(game_map[0]):
                if math.sqrt((r - row)**2 + (c - col)**2) <= radius:
                    visible_tiles.add((r, c))
                    if game_map[r][c] != "W":
                        explored_tiles.add((r, c))


def add_particles(x, y, color, count=12):
    for _ in range(count):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(1.5, 5)
        particles.append({
            'x': float(x), 'y': float(y),
            'vx': math.cos(angle) * speed,
            'vy': math.sin(angle) * speed - random.uniform(0, 2),
            'color': color,
            'life': random.randint(25, 55),
            'max_life': 55,
            'size': random.randint(3, 8),
        })


def update_particles():
    global particles
    for p in particles:
        p['x']  += p['vx']
        p['y']  += p['vy']
        p['vy'] += 0.12
        p['life'] -= 1
    particles = [p for p in particles if p['life'] > 0]


def draw_particles():
    for p in particles:
        ratio = p['life'] / p['max_life']
        size  = max(1, int(p['size'] * ratio))
        pygame.draw.circle(screen, p['color'], (int(p['x']), int(p['y'])), size)


def _dim(color, factor):
    return tuple(min(255, int(c * factor)) for c in color)


# ── tile drawing ───────────────────────────────────────────────

def draw_tile(x, y, tile_type, is_visible, is_explored):
    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)

    if not is_visible and not is_explored:
        pygame.draw.rect(screen, (18, 18, 32), rect)
        pygame.draw.rect(screen, (28, 28, 44), rect, 1)
        return

    dim = 0.55 if (not is_visible and is_explored) else 1.0

    if tile_type == "W":
        pygame.draw.rect(screen, _dim(WATER_BLUE, dim), rect)
        for wy in range(y + 14, y + TILE_SIZE, 18):
            wave_y = wy + int(3 * math.sin((x + animation_counter * 0.6) * 0.09))
            pygame.draw.line(screen, _dim(LIGHT_BLUE, dim), (x, wave_y), (x + TILE_SIZE, wave_y), 1)
        pygame.draw.rect(screen, _dim(OCEAN_BLUE, dim), rect, 1)

    elif tile_type == "L":
        pygame.draw.rect(screen, _dim(SAND, dim), rect)
        for sx in range(x + 8, x + TILE_SIZE - 4, 14):
            for sy in range(y + 8, y + TILE_SIZE - 4, 14):
                pygame.draw.circle(screen, _dim((200, 182, 110), dim),
                                   (sx + (sx % 7), sy + (sy % 5)), 2)
        pygame.draw.rect(screen, _dim((185, 162, 95), dim), rect, 1)

    elif tile_type == "F":
        pygame.draw.rect(screen, _dim(FOREST_GREEN, dim), rect)
        for tx, ty, tr in [(x+18, y+20, 12), (x+55, y+24, 10),
                           (x+36, y+52, 14), (x+62, y+55, 9)]:
            pygame.draw.circle(screen, _dim(DARK_GREEN, dim), (tx, ty), tr)
            pygame.draw.circle(screen, _dim((70, 130, 60), dim), (tx-2, ty-2), tr-3)
        pygame.draw.rect(screen, _dim(DARK_GREEN, dim), rect, 2)

    elif tile_type == "R":
        pygame.draw.rect(screen, _dim(GRAY, dim), rect)
        pygame.draw.ellipse(screen, _dim(DARK_GRAY, dim), (x+14, y+18, 28, 22))
        pygame.draw.ellipse(screen, _dim(DARK_GRAY, dim), (x+40, y+28, 22, 18))
        pygame.draw.ellipse(screen, _dim((82, 82, 82), dim), (x+16, y+20, 13, 10))
        pygame.draw.rect(screen, _dim(DARK_GRAY, dim), rect, 2)


# ── player sprite ──────────────────────────────────────────────

def draw_player(x, y, is_ai=False):
    cx = x + TILE_SIZE // 2
    cy = y + TILE_SIZE // 2

    # Shadow ellipse
    shadow_surf = pygame.Surface((34, 12), pygame.SRCALPHA)
    pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), (0, 0, 34, 12))
    screen.blit(shadow_surf, (cx - 17, cy + 26))

    # Body
    body_col = (55, 155, 215) if is_ai else (195, 55, 55)
    pygame.draw.rect(screen, body_col, (cx-10, cy-4, 20, 22), border_radius=4)
    # Belt
    pygame.draw.rect(screen, (50, 35, 15), (cx-10, cy+8, 20, 4))
    pygame.draw.circle(screen, GOLD, (cx, cy+10), 4)

    # Head
    pygame.draw.circle(screen, (238, 208, 168), (cx, cy-15), 12)

    # Hat brim + body
    hat_dark = (28, 18, 8)
    pygame.draw.rect(screen, hat_dark, (cx-17, cy-25, 34, 5), border_radius=2)
    pygame.draw.polygon(screen, hat_dark, [
        (cx-11, cy-25), (cx+11, cy-25),
        (cx+8,  cy-40), (cx-8,  cy-40),
    ])
    pygame.draw.rect(screen, GOLD, (cx-13, cy-31, 26, 3))

    # Eyes
    pygame.draw.circle(screen, BLACK, (cx-4, cy-16), 2)
    pygame.draw.circle(screen, BLACK, (cx+4, cy-16), 2)

    # Sword
    sword_col = BRIGHT_GOLD if is_ai else (210, 210, 225)
    pygame.draw.line(screen, sword_col,    (cx+11, cy+1),  (cx+26, cy-14), 3)
    pygame.draw.line(screen, GOLD,         (cx+9,  cy-1),  (cx+15, cy-1), 4)

    # Legs
    pygame.draw.rect(screen, (55, 38, 18), (cx-9, cy+16, 8, 12), border_radius=2)
    pygame.draw.rect(screen, (55, 38, 18), (cx+1, cy+16, 8, 12), border_radius=2)


# ── game map ───────────────────────────────────────────────────

def draw_game_map():
    screen.fill(NAVY_BLUE)
    tr, tc = treasure_position
    treasure_visible = (
        (tr, tc) in visible_tiles or
        (tr, tc) in explored_tiles or
        game_state in (GameState.GAME_OVER, GameState.AI_DEMO)
    )

    for row in range(len(game_map)):
        for col in range(len(game_map[0])):
            x, y = col * TILE_SIZE, row * TILE_SIZE
            is_vis = (row, col) in visible_tiles
            is_exp = (row, col) in explored_tiles
            tile   = game_map[row][col]
            if tile != "T":
                draw_tile(x, y, tile, is_vis, is_exp)
            elif not treasure_visible:
                rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(screen, (18, 18, 32), rect)
                pygame.draw.rect(screen, (28, 28, 44), rect, 1)

    # Treasure chest
    if treasure_visible:
        tx, ty = tc * TILE_SIZE, tr * TILE_SIZE
        draw_tile(tx, ty, "L", True, True)
        cx, cy = tx + TILE_SIZE // 2, ty + TILE_SIZE // 2
        pulse  = int(14 + 7 * abs(math.sin(animation_counter * 0.07)))

        # Glow rings
        for r in (pulse + 12, pulse + 6, pulse):
            gsurf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(gsurf, (255, 215, 0, 28), (r + 2, r + 2), r)
            screen.blit(gsurf, (cx - r - 2, cy - r - 2))

        # Chest body
        pygame.draw.rect(screen, (110, 65, 22), (tx+14, ty+30, 52, 36), border_radius=5)
        pygame.draw.rect(screen, (145, 92, 40), (tx+16, ty+32, 48, 13), border_radius=3)
        pygame.draw.rect(screen, GOLD, (tx+14, ty+30, 52, 36), 2, border_radius=5)
        # Hasp / lock
        pygame.draw.circle(screen, BRIGHT_GOLD, (cx, ty+44), 6)
        pygame.draw.circle(screen, GOLD,        (cx, ty+44), 6, 2)
        # Spilled coins
        for gx, gy in ((cx-16, ty+28), (cx+12, ty+26), (cx, ty+22)):
            pygame.draw.circle(screen, BRIGHT_GOLD, (gx, gy), 5)
            pygame.draw.circle(screen, GOLD,        (gx, gy), 5, 1)

    # AI path
    if game_state == GameState.AI_DEMO and ai_path:
        for i, (pr, pc) in enumerate(ai_path):
            px, py = pc * TILE_SIZE + TILE_SIZE // 2, pr * TILE_SIZE + TILE_SIZE // 2
            if i < ai_current_step:
                pygame.draw.circle(screen, BRIGHT_GOLD, (px, py), 6)
            elif i == ai_current_step:
                r = 9 + int(3 * math.sin(animation_counter * 0.2))
                pygame.draw.circle(screen, BRIGHT_GOLD, (px, py), r)
            else:
                pygame.draw.circle(screen, (200, 200, 200), (px, py), 4)

    draw_player(player.col * TILE_SIZE, player.row * TILE_SIZE,
                is_ai=(game_state == GameState.AI_DEMO))
    draw_particles()


# ── HUD ────────────────────────────────────────────────────────

def draw_hud():
    PAD = 16

    # Background + border
    pygame.draw.rect(screen, (22, 14, 32), (HUD_X, 0, HUD_W, HEIGHT))
    pygame.draw.rect(screen, GOLD,         (HUD_X, 0, HUD_W, HEIGHT), 3)
    pygame.draw.line(screen, BRIGHT_GOLD, (HUD_X + 3, 0), (HUD_X + 3, HEIGHT), 1)

    y = 18

    # Header
    hdr = medium_font.render("PIRATE LOG", True, BRIGHT_GOLD)
    hdr_rect = hdr.get_rect(centerx=HUD_X + HUD_W // 2, y=y)
    screen.blit(hdr, hdr_rect)
    screen.blit(pirate_icon, (hdr_rect.left - 30, y))
    screen.blit(pirate_icon, (hdr_rect.right + 6, y))
    y += 34
    pygame.draw.line(screen, GOLD, (HUD_X + PAD, y), (HUD_X + HUD_W - PAD, y), 2)
    y += 14

    # Level badge
    lvl_bg = pygame.Rect(HUD_X + PAD, y, HUD_W - PAD * 2, 42)
    pygame.draw.rect(screen, (55, 38, 8),   lvl_bg, border_radius=8)
    pygame.draw.rect(screen, GOLD,           lvl_bg, 2, border_radius=8)
    lv = large_font.render(f"LEVEL  {current_level}", True, BRIGHT_GOLD)
    screen.blit(lv, lv.get_rect(center=lvl_bg.center))
    y += 58

    # Stamina label + values
    screen.blit(small_font.render("STAMINA", True, LIGHT_GRAY), (HUD_X + PAD, y))
    stam_pct = player.current_stamina / player.max_stamina
    sv = small_font.render(f"{player.current_stamina} / {player.max_stamina}", True, WHITE)
    screen.blit(sv, sv.get_rect(right=HUD_X + HUD_W - PAD, y=y))
    y += 22

    bar_w = HUD_W - PAD * 2
    bar_h = 18
    bar_rect = pygame.Rect(HUD_X + PAD, y, bar_w, bar_h)
    pygame.draw.rect(screen, (38, 38, 38),  bar_rect, border_radius=9)
    pygame.draw.rect(screen, (75, 75, 75),  bar_rect, 1, border_radius=9)
    filled = int(stam_pct * bar_w)
    if filled > 0:
        bar_col = (50, 200, 80) if stam_pct > 0.5 else ((230, 175, 30) if stam_pct > 0.25 else (220, 50, 50))
        fill_r = pygame.Rect(HUD_X + PAD, y, filled, bar_h)
        pygame.draw.rect(screen, bar_col, fill_r, border_radius=9)
        # shine
        shine_r = pygame.Rect(HUD_X + PAD + 2, y + 2, max(0, filled - 4), bar_h // 2 - 2)
        if shine_r.width > 0:
            pygame.draw.rect(screen, _dim(bar_col, 1.4), shine_r, border_radius=6)  # type: ignore[arg-type]
    y += 32

    # Terrain cost legend
    pygame.draw.line(screen, (55, 38, 65), (HUD_X + PAD, y), (HUD_X + HUD_W - PAD, y), 1)
    y += 10
    screen.blit(tiny_font.render("TERRAIN COSTS", True, (148, 128, 178)), (HUD_X + PAD, y))
    y += 18
    for img, label, col, cost in (
        (sand_img,   "Sand",    SAND,        "×1"),
        (forest_img, "Forest",  FOREST_GREEN, "×2"),
        (rock_img,   "Rock",    LIGHT_GRAY,   "×3"),
    ):
        screen.blit(img, (HUD_X + PAD, y))
        screen.blit(tiny_font.render(label, True, col), (HUD_X + PAD + 20, y))
        cs = tiny_font.render(cost, True, (200, 178, 100))
        screen.blit(cs, cs.get_rect(right=HUD_X + HUD_W - PAD, y=y))
        y += 18
    y += 6

    # Stats
    pygame.draw.line(screen, (55, 38, 65), (HUD_X + PAD, y), (HUD_X + HUD_W - PAD, y), 1)
    y += 12
    screen.blit(position_img, (HUD_X + PAD, y))
    screen.blit(tiny_font.render(f"Position: ({player.col}, {player.row})", True, LIGHT_GRAY),
                (HUD_X + PAD + 20, y))
    y += 20
    screen.blit(steps_hud_img, (HUD_X + PAD, y))
    screen.blit(tiny_font.render(f"Steps: {player.distance_traveled}", True, LIGHT_GRAY),
                (HUD_X + PAD + 20, y))
    y += 28

    # Status box
    if player.treasure_found:
        sb = pygame.Rect(HUD_X + PAD, y, HUD_W - PAD * 2, 50)
        pygame.draw.rect(screen, (78, 58, 4),    sb, border_radius=8)
        pygame.draw.rect(screen, BRIGHT_GOLD,     sb, 2, border_radius=8)
        t = medium_font.render("TREASURE FOUND!", True, BRIGHT_GOLD)
        screen.blit(t, t.get_rect(center=sb.center))
        y += 62
    elif player.is_dead:
        sb = pygame.Rect(HUD_X + PAD, y, HUD_W - PAD * 2, 50)
        pygame.draw.rect(screen, (75, 8, 8),  sb, border_radius=8)
        pygame.draw.rect(screen, RED,          sb, 2, border_radius=8)
        t = medium_font.render("EXHAUSTED!", True, RED)
        screen.blit(t, t.get_rect(center=sb.center))
        y += 62
    else:
        d = abs(player.row - treasure_position[0]) + abs(player.col - treasure_position[1])
        screen.blit(treasure_img_sm, (HUD_X + PAD, y))
        screen.blit(small_font.render(f"  Treasure: ~{d} tiles", True, BRIGHT_GOLD),
                    (HUD_X + PAD + treasure_img_sm.get_width(), y))
        y += 30

    # Controls at bottom
    y = HEIGHT - 112
    pygame.draw.line(screen, (55, 38, 65), (HUD_X + PAD, y), (HUD_X + HUD_W - PAD, y), 1)
    y += 8
    screen.blit(tiny_font.render("CONTROLS", True, (148, 128, 178)), (HUD_X + PAD, y))
    y += 17
    if game_state in (GameState.PLAYING, GameState.AI_DEMO):
        for ctrl in ("↑↓←→  Move", "G  AI Pathfind (Dijkstra)", "ESC  Menu"):
            screen.blit(tiny_font.render(ctrl, True, (155, 155, 155)), (HUD_X + PAD, y))
            y += 16


# ── menu ───────────────────────────────────────────────────────

def draw_menu():
    screen.fill((8, 18, 48))

    # Twinkling stars
    for sx, sy, b in menu_stars:
        twinkle = 0.55 + 0.45 * math.sin(animation_counter * 0.05 + b * 10)
        size    = 1 if b < 0.5 else 2
        v       = int(205 * twinkle)
        pygame.draw.circle(screen, (v, v, v), (sx, int(sy)), size)

    # Crescent moon
    pygame.draw.circle(screen, (242, 242, 200), (WIDTH - 115, 78), 44)
    pygame.draw.circle(screen, (8, 22, 52),     (WIDTH - 94,  62), 37)

    # Animated layered ocean
    for i in range(6):
        amp   = 9 - i
        speed = 0.032 - i * 0.004
        r, g, b = 18, 55 + i * 14, 95 + i * 14
        pts = [(0, HEIGHT - 110 + i * 22)]
        for wx in range(0, WIDTH + 12, 10):
            wy = HEIGHT - 110 + i * 22 + int(amp * math.sin(wx * 0.018 + animation_counter * speed + i))
            pts.append((wx, wy))
        pts += [(WIDTH, HEIGHT), (0, HEIGHT)]
        pygame.draw.polygon(screen, (r, g, b), pts)

    # Title panel
    tp = pygame.Rect(WIDTH // 2 - 360, 42, 720, 150)
    pygame.draw.rect(screen, (12, 8, 4),     tp, border_radius=14)
    pygame.draw.rect(screen, GOLD,            tp, 3, border_radius=14)
    pygame.draw.rect(screen, BRIGHT_GOLD,     tp, 1, border_radius=14)
    t1 = title_font.render("PIRATE ISLAND", True, BRIGHT_GOLD)
    t2 = large_font.render("E X P L O R E R",    True, GOLD)
    screen.blit(t1, t1.get_rect(centerx=WIDTH // 2, y=62))
    screen.blit(t2, t2.get_rect(centerx=WIDTH // 2, y=132))
    screen.blit(pirate_img, (tp.x + 12, tp.y + 20))
    screen.blit(pirate_img, (tp.right - 122, tp.y + 20))

    # Subtitle
    sub = medium_font.render("~ Dijkstra's Journey ~", True, LIGHT_BLUE)
    screen.blit(sub, sub.get_rect(centerx=WIDTH // 2, y=196))

    # Info cards
    infos = [
        ("• Explore the island and find hidden treasure"),
        ("• Forests & Rocks drain your stamina faster"),
        ("• Press G to summon the AI for the fastest route"),
    ]
    card_y = 258
    for text in infos:
        card = pygame.Rect(WIDTH // 2 - 282, card_y, 564, 44)
        pygame.draw.rect(screen, (18, 28, 58),  card, border_radius=8)
        pygame.draw.rect(screen, (48, 75, 118), card, 1, border_radius=8)
        screen.blit(small_font.render(text, True, (195, 218, 255)), (card.x + 55, card.y + 12))
        card_y += 54

    # Play button with hover
    mouse_pos = pygame.mouse.get_pos()
    play_btn  = pygame.Rect(WIDTH // 2 - 125, 462, 250, 65)
    hover     = play_btn.collidepoint(mouse_pos)

    pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(play_btn.x + 5, play_btn.y + 5, play_btn.w, play_btn.h), border_radius=14)
    pygame.draw.rect(screen, (238, 188, 28) if hover else (200, 148, 10), play_btn, border_radius=14)
    pygame.draw.rect(screen, BRIGHT_GOLD, play_btn, 3, border_radius=14)
    pt = large_font.render(" PLAY ", True, BLACK)
    screen.blit(pt, pt.get_rect(center=play_btn.center))

    hint = tiny_font.render("or press SPACE", True, (110, 110, 155))
    screen.blit(hint, hint.get_rect(centerx=WIDTH // 2, y=537))

    return play_btn


# ── level select ───────────────────────────────────────────────

def draw_level_select():
    screen.fill((8, 18, 48))
    for sx, sy, b in menu_stars:
        v = int(180 * (0.55 + 0.45 * math.sin(animation_counter * 0.05 + b * 10)))
        pygame.draw.circle(screen, (v, v, v), (sx, int(sy)), 1)

    # Title
    tbg = pygame.Rect(WIDTH // 2 - 205, 38, 410, 68)
    pygame.draw.rect(screen, (12, 8, 4), tbg, border_radius=10)
    pygame.draw.rect(screen, GOLD,        tbg, 3, border_radius=10)
    tit = title_font.render("SELECT LEVEL", True, BRIGHT_GOLD)
    screen.blit(tit, tit.get_rect(center=tbg.center))

    level_data = [
        ("Easy",   "● ○ ○ ○ ○",          (48, 148, 48)),
        ("Normal", "● ● ○ ○ ○",        (95, 148, 28)),
        ("Hard",   "● ● ● ○ ○",      (175, 128, 18)),
        ("Expert", "● ● ● ● ○",    (198, 75, 18)),
        ("Master", "● ● ● ● ●",  (198, 28, 28)),
    ]
    buttons   = []
    mouse_pos = pygame.mouse.get_pos()
    btn_y     = 158

    for i, (name, stars, diff_col) in enumerate(level_data):
        level = i + 1
        btn   = pygame.Rect(WIDTH // 2 - 252, btn_y, 504, 70)
        hover = btn.collidepoint(mouse_pos)

        pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(btn.x + 4, btn.y + 4, btn.w, btn.h), border_radius=12)
        pygame.draw.rect(screen, (18, 13, 28),  btn, border_radius=12)
        border = tuple(min(255, c + 22) for c in diff_col) if hover else diff_col
        pygame.draw.rect(screen, border, btn, 3, border_radius=12)

        # Level number
        num = large_font.render(str(level), True, BRIGHT_GOLD)
        screen.blit(num, (btn.x + 28, btn.y + 18))
        pygame.draw.line(screen, diff_col, (btn.x + 58, btn.y + 10), (btn.x + 58, btn.y + 60), 1)

        # Difficulty name + stars
        screen.blit(medium_font.render(name,  True, WHITE),        (btn.x + 76, btn.y + 10))
        screen.blit(small_font.render(stars,  True, BRIGHT_GOLD),  (btn.x + 76, btn.y + 38))

        if hover:
            arrow = medium_font.render(">", True, BRIGHT_GOLD)
            screen.blit(arrow, (btn.right - 44, btn.y + 20))

        buttons.append((level, btn))
        btn_y += 86

    back = small_font.render("ESC — Back to Menu", True, (115, 115, 158))
    screen.blit(back, back.get_rect(centerx=WIDTH // 2, y=HEIGHT - 34))
    return buttons


# ── game over ──────────────────────────────────────────────────

def draw_game_over():
    ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    ov.fill((0, 0, 0, 155))
    screen.blit(ov, (0, 0))

    pw, ph = 590, 385
    panel  = pygame.Rect(WIDTH // 2 - pw // 2, HEIGHT // 2 - ph // 2, pw, ph)

    if player.treasure_found:
        pcol, bcol = (38, 28, 4),  BRIGHT_GOLD
        title_txt  = "TREASURE FOUND!"
        tcol       = BRIGHT_GOLD
    else:
        pcol, bcol = (38, 4, 4),   RED
        title_txt  = "OUT OF STAMINA"
        tcol       = RED

    # Shadow + panel
    pygame.draw.rect(screen, (0, 0, 0), pygame.Rect(panel.x + 8, panel.y + 8, panel.w, panel.h), border_radius=16)
    pygame.draw.rect(screen, pcol,  panel, border_radius=16)
    pygame.draw.rect(screen, bcol,  panel, 4, border_radius=16)

    ts       = large_font.render(title_txt, True, tcol)
    gap      = 10
    ico      = treasure_img if player.treasure_found else None
    ico_w    = ico.get_width() if ico else 0
    total_w  = (ico_w + gap) * 2 + ts.get_width() if ico else ts.get_width()
    start_x  = panel.centerx - total_w // 2
    icon_y   = panel.y + 28
    text_y   = icon_y + (treasure_img.get_height() - ts.get_height()) // 2
    if ico:
        screen.blit(ico, (start_x, icon_y))
        screen.blit(ts,  (start_x + ico_w + gap, text_y))
        screen.blit(ico, (start_x + ico_w + gap + ts.get_width() + gap, icon_y))
    else:
        screen.blit(ts, ts.get_rect(centerx=panel.centerx, y=icon_y))
    pygame.draw.line(screen, bcol, (panel.x + 30, panel.y + 78), (panel.right - 30, panel.y + 78), 2)

    stats = [
        (level_img,   "Level",             str(current_level)),
        (steps_img,   "Steps taken",       str(player.distance_traveled)),
        (stamina_img, "Remaining stamina", str(player.current_stamina)),
    ]
    sy = panel.y + 98
    for img, label, val in stats:
        screen.blit(img, (panel.x + 40, sy + 2))
        screen.blit(medium_font.render(label, True, LIGHT_GRAY),  (panel.x + 40 + img.get_width() + 10,  sy))
        vs = medium_font.render(val, True, WHITE)
        screen.blit(vs, vs.get_rect(right=panel.right - 40, y=sy))
        sy += 50

    mouse_pos = pygame.mouse.get_pos()
    btn_y     = panel.bottom - 78
    next_btn  = pygame.Rect(panel.x + 38, btn_y, 226, 52)
    menu_btn  = pygame.Rect(panel.right - 264, btn_y, 226, 52)

    ntext = "NEXT LEVEL" if player.treasure_found else "RETRY LEVEL"
    ncol  = (38, 158, 58) if player.treasure_found else (158, 128, 8)
    nhcol = (58, 200, 78) if player.treasure_found else (200, 168, 20)

    nh = next_btn.collidepoint(mouse_pos)
    mh = menu_btn.collidepoint(mouse_pos)

    pygame.draw.rect(screen, nhcol if nh else ncol, next_btn, border_radius=10)
    pygame.draw.rect(screen, WHITE, next_btn, 2, border_radius=10)
    nt = medium_font.render(ntext, True, WHITE)
    screen.blit(nt, nt.get_rect(center=next_btn.center))

    pygame.draw.rect(screen, (158, 38, 38) if mh else (118, 28, 28), menu_btn, border_radius=10)
    pygame.draw.rect(screen, WHITE, menu_btn, 2, border_radius=10)
    mt = medium_font.render("MENU", True, WHITE)
    screen.blit(mt, mt.get_rect(center=menu_btn.center))

    return next_btn, menu_btn


# ── AI demo banner ─────────────────────────────────────────────

def draw_ai_demo():
    bh    = 44
    bsurf = pygame.Surface((MAP_W, bh), pygame.SRCALPHA)
    bsurf.fill((0, 0, 0, 172))
    screen.blit(bsurf, (0, 0))

    pulse = abs(math.sin(animation_counter * 0.1))
    col   = (int(95 + 160 * pulse), int(195 + 60 * pulse), 45)
    info  = medium_font.render("🤖  AI PATHFINDING  —  Dijkstra's Algorithm", True, col)
    screen.blit(info, info.get_rect(centerx=MAP_W // 2, centery=bh // 2))

    if ai_path:
        st = small_font.render(f"Step {ai_current_step + 1} / {len(ai_path)}", True, WHITE)
        screen.blit(st, st.get_rect(right=MAP_W - 12, centery=bh // 2))


# ── main loop ──────────────────────────────────────────────────

running          = True
start_button_rect = None
level_buttons     = None
next_button_rect  = None
menu_button_rect  = None

while running:
    clock.tick(FPS)
    animation_counter += 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            mp = event.pos

            if game_state == GameState.MENU and start_button_rect:
                if start_button_rect.collidepoint(mp):
                    game_state = GameState.LEVEL_SELECT

            elif game_state == GameState.LEVEL_SELECT and level_buttons:
                for level, rect in level_buttons:
                    if rect.collidepoint(mp):
                        current_level = level
                        init_game(level)
                        game_state = GameState.PLAYING

            elif game_state == GameState.GAME_OVER:
                if next_button_rect and next_button_rect.collidepoint(mp):
                    if player.treasure_found:
                        if current_level < 5:
                            current_level += 1
                            init_game(current_level)
                            game_state = GameState.PLAYING
                        else:
                            game_state    = GameState.MENU
                            current_level = 1
                    else:
                        init_game(current_level)
                        game_state = GameState.PLAYING

                if menu_button_rect and menu_button_rect.collidepoint(mp):
                    game_state    = GameState.MENU
                    current_level = 1

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state in (GameState.PLAYING, GameState.AI_DEMO, GameState.LEVEL_SELECT):
                    game_state = GameState.MENU

            if event.key == pygame.K_SPACE and game_state == GameState.MENU:
                game_state = GameState.LEVEL_SELECT

            if event.key == pygame.K_g and game_state == GameState.PLAYING:
                ai_path, _ = dijkstra_shortest_path(
                    game_map, player.row, player.col,
                    treasure_position[0], treasure_position[1]
                )
                if ai_path:
                    game_state      = GameState.AI_DEMO
                    ai_current_step = 0

            if game_state == GameState.PLAYING and not player.is_dead:
                nr, nc = player.row, player.col
                if event.key == pygame.K_UP:    nr -= 1
                if event.key == pygame.K_DOWN:  nr += 1
                if event.key == pygame.K_LEFT:  nc -= 1
                if event.key == pygame.K_RIGHT: nc += 1

                if 0 <= nr < len(game_map) and 0 <= nc < len(game_map[0]):
                    tile = game_map[nr][nc]
                    if tile != "W":
                        player.move(nr, nc, get_tile_cost(tile))
                        reveal_area(player.row, player.col)

                        if (player.row, player.col) == treasure_position:
                            player.treasure_found = True
                            tx = treasure_position[1] * TILE_SIZE + TILE_SIZE // 2
                            ty = treasure_position[0] * TILE_SIZE + TILE_SIZE // 2
                            add_particles(tx, ty, BRIGHT_GOLD, 32)
                            add_particles(tx, ty, GOLD,        20)
                            game_state = GameState.GAME_OVER
                        elif player.is_dead:
                            game_state = GameState.GAME_OVER

    if game_state == GameState.AI_DEMO:
        if animation_counter % 10 == 0:
            if ai_current_step < len(ai_path) - 1:
                ai_current_step += 1
                np_ = ai_path[ai_current_step]
                player.move(np_[0], np_[1], get_tile_cost(game_map[np_[0]][np_[1]]))
                reveal_area(player.row, player.col)
            else:
                player.treasure_found = True
                game_state = GameState.GAME_OVER

    update_particles()

    if game_state == GameState.MENU:
        start_button_rect = draw_menu()
    elif game_state == GameState.LEVEL_SELECT:
        level_buttons = draw_level_select()
    elif game_state == GameState.PLAYING:
        draw_game_map()
        draw_hud()
    elif game_state == GameState.AI_DEMO:
        draw_game_map()
        draw_hud()
        draw_ai_demo()
    elif game_state == GameState.GAME_OVER:
        draw_game_map()
        draw_hud()
        next_button_rect, menu_button_rect = draw_game_over()

    pygame.display.flip()

pygame.quit()
sys.exit()
