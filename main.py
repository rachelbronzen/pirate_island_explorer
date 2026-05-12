import pygame
import sys
import math
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
pygame.display.set_caption("⚓ Pirate Island Explorer ⚓")
clock = pygame.time.Clock()

title_font = pygame.font.SysFont("arial", 48, bold=True)
large_font = pygame.font.SysFont("arial", 36, bold=True)
medium_font = pygame.font.SysFont("arial", 24, bold=True)
small_font = pygame.font.SysFont("arial", 18)
tiny_font = pygame.font.SysFont("arial", 14)

current_level = 1
player = None
visited = set()
visible_tiles = set()
explored_tiles = set()
game_state = GameState.MENU
game_map = None
treasure_position = None
animation_counter = 0
ai_path = []
ai_current_step = 0

def init_game(level):
    """Initialize game with a certain level"""
    global player, visited, visible_tiles, explored_tiles, game_map, treasure_position, ai_path, ai_current_step
    
    game_map = generate_map_with_difficulty(level)
    treasure_position = get_random_treasure_position(game_map)
    
    optimal_path, optimal_cost = dijkstra_shortest_path(game_map, 1, 1, treasure_position[0], treasure_position[1])
    
    stamina_buffer = max(15 - (level * 2), 5) 
    starting_stamina = optimal_cost + stamina_buffer
    
    player = Player(1, 1, max_stamina=starting_stamina)
    
    visited = set()
    visible_tiles = set()
    explored_tiles = set()
    ai_path = []
    ai_current_step = 0
    
    dfs(game_map, player.row, player.col, visited)
    reveal_area(player.row, player.col)

def reveal_area(row, col, radius=2):
    for r in range(row - radius, row + radius + 1):
        for c in range(col - radius, col + radius + 1):
            if 0 <= r < len(game_map) and 0 <= c < len(game_map[0]):
                distance = math.sqrt((r - row)**2 + (c - col)**2)
                if distance <= radius:
                    visible_tiles.add((r, c))
                    if game_map[r][c] != "W":
                        explored_tiles.add((r, c))

def draw_tile(x, y, tile_type, is_visible, is_explored):
    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
    
    if not is_visible and tile_type != "T":
        pygame.draw.rect(screen, DARK_GRAY, rect)
        pygame.draw.rect(screen, BLACK, rect, 2)
        if not is_explored: return
    
    if not is_visible and not is_explored:
        pygame.draw.rect(screen, DARK_GRAY, rect)
        pygame.draw.rect(screen, BLACK, rect, 2)
        return
    
    if tile_type == "W":
        pygame.draw.rect(screen, WATER_BLUE, rect)
        if (int(x/TILE_SIZE) + int(y/TILE_SIZE)) % 2 == 0:
            pygame.draw.line(screen, LIGHT_BLUE, (x, y+20), (x+TILE_SIZE, y+20), 1)
        pygame.draw.rect(screen, OCEAN_BLUE, rect, 2)
    elif tile_type == "L":
        pygame.draw.rect(screen, SAND, rect)
        pygame.draw.rect(screen, DARK_BROWN, rect, 1)
    elif tile_type == "F":
        pygame.draw.rect(screen, FOREST_GREEN, rect)
        pygame.draw.rect(screen, DARK_GREEN, rect, 2)
    elif tile_type == "R":
        pygame.draw.rect(screen, GRAY, rect)
        pygame.draw.rect(screen, DARK_GRAY, rect, 2)
        pygame.draw.circle(screen, DARK_GRAY, (x + TILE_SIZE//2, y + TILE_SIZE//2), 15)

def draw_player(x, y, is_ai=False):
    color = BRIGHT_GOLD if is_ai else WHITE
    pygame.draw.circle(screen, color, (x + TILE_SIZE//2, y + 20), 10)
    pygame.draw.polygon(screen, BLACK, [
        (x + TILE_SIZE//2 - 15, y + 10),
        (x + TILE_SIZE//2 + 15, y + 10),
        (x + TILE_SIZE//2 + 10, y + 5)
    ])
    pygame.draw.rect(screen, RED if not is_ai else GOLD, (x + TILE_SIZE//2 - 8, y + 28, 16, 20))
    pygame.draw.line(screen, BLACK, (x + TILE_SIZE//2 - 5, y + 48), (x + TILE_SIZE//2 - 5, y + 60), 3)
    pygame.draw.line(screen, BLACK, (x + TILE_SIZE//2 + 5, y + 48), (x + TILE_SIZE//2 + 5, y + 60), 3)
    pygame.draw.line(screen, GOLD, (x + TILE_SIZE//2 + 8, y + 35), (x + TILE_SIZE - 15, y + 20), 4)

def draw_game_map():
    screen.fill(NAVY_BLUE)
    treasure_row, treasure_col = treasure_position
    is_treasure_revealed = (treasure_row, treasure_col) in visible_tiles or \
                           (treasure_row, treasure_col) in explored_tiles or \
                           game_state in [GameState.GAME_OVER, GameState.AI_DEMO]

    for row in range(len(game_map)):
        for col in range(len(game_map[0])):
            x = col * TILE_SIZE
            y = row * TILE_SIZE
            is_visible = (row, col) in visible_tiles
            is_explored = (row, col) in explored_tiles
            tile_type = game_map[row][col]
            
            if tile_type != "T":
                draw_tile(x, y, tile_type, is_visible, is_explored)
            else:
                if not is_treasure_revealed:
                    rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                    pygame.draw.rect(screen, DARK_GRAY, rect)
                    pygame.draw.rect(screen, BLACK, rect, 2)
    
    if is_treasure_revealed:
        treasure_x = treasure_col * TILE_SIZE
        treasure_y = treasure_row * TILE_SIZE
        treasure_rect = pygame.Rect(treasure_x, treasure_y, TILE_SIZE, TILE_SIZE)
        pulse = int(10 + 5 * abs(math.sin(animation_counter * 0.1)))
        
        pygame.draw.rect(screen, BRIGHT_GOLD, treasure_rect)
        pygame.draw.rect(screen, GOLD, treasure_rect, 5)
        pygame.draw.circle(screen, GOLD, (treasure_x + TILE_SIZE//2, treasure_y + TILE_SIZE//2), 25)
        pygame.draw.circle(screen, BRIGHT_GOLD, (treasure_x + TILE_SIZE//2, treasure_y + TILE_SIZE//2), 20)
        pygame.draw.circle(screen, BRIGHT_GOLD, (treasure_x + TILE_SIZE//2, treasure_y + TILE_SIZE//2), pulse, 2)
        text = large_font.render("💰", True, BRIGHT_GOLD)
        text_rect = text.get_rect(center=(treasure_x + TILE_SIZE//2, treasure_y + TILE_SIZE//2))
        screen.blit(text, text_rect)
    
    if game_state == GameState.AI_DEMO and ai_path:
        for i, (path_row, path_col) in enumerate(ai_path):
            x = path_col * TILE_SIZE + TILE_SIZE // 2
            y = path_row * TILE_SIZE + TILE_SIZE // 2
            if i < ai_current_step: pygame.draw.circle(screen, BRIGHT_GOLD, (x, y), 8)
            elif i == ai_current_step: pygame.draw.circle(screen, BRIGHT_GOLD, (x, y), 12)
            else: pygame.draw.circle(screen, WHITE, (x, y), 4)
    
    player_x = player.col * TILE_SIZE
    player_y = player.row * TILE_SIZE
    draw_player(player_x, player_y, is_ai=(game_state == GameState.AI_DEMO))

def draw_hud():
    hud_x = len(game_map[0]) * TILE_SIZE
    hud_width = WIDTH - hud_x
    
    pygame.draw.rect(screen, DARK_BROWN, (hud_x, 0, hud_width, HEIGHT))
    pygame.draw.rect(screen, GOLD, (hud_x, 0, hud_width, HEIGHT), 3)
    
    y_offset = 20
    line_height = 50
    
    info_title = small_font.render("Stamina Cost:", True, BRIGHT_GOLD)
    screen.blit(info_title, (hud_x + 20, y_offset))
    y_offset += 25
    screen.blit(tiny_font.render("Sand (Kuning) = 1", True, SAND), (hud_x + 20, y_offset))
    y_offset += 20
    screen.blit(tiny_font.render("Forest (Hijau) = 2", True, FOREST_GREEN), (hud_x + 20, y_offset))
    y_offset += 20
    screen.blit(tiny_font.render("Rock (Abu-abu) = 3", True, LIGHT_GRAY), (hud_x + 20, y_offset))
    y_offset += 40
    
    level_text = large_font.render(f"LEVEL {current_level}", True, BRIGHT_GOLD)
    screen.blit(level_text, (hud_x + 20, y_offset))
    y_offset += 60
    
    stamina_pct = player.current_stamina / player.max_stamina
    stamina_color = FOREST_GREEN if stamina_pct > 0.5 else (BRIGHT_GOLD if stamina_pct > 0.25 else RED)
    
    stam_text = small_font.render(f"Stamina: {player.current_stamina} / {player.max_stamina}", True, WHITE)
    screen.blit(stam_text, (hud_x + 20, y_offset))
    y_offset += 25
    
    bar_width = 150
    bar_height = 20
    pygame.draw.rect(screen, DARK_GRAY, (hud_x + 20, y_offset, bar_width, bar_height))
    pygame.draw.rect(screen, WHITE, (hud_x + 20, y_offset, bar_width, bar_height), 2)
    filled_width = int(stamina_pct * bar_width)
    if filled_width > 0:
        pygame.draw.rect(screen, stamina_color, (hud_x + 20, y_offset, filled_width, bar_height))
    y_offset += 50
    
    pos_text = small_font.render(f"Post: ({player.col}, {player.row})", True, WHITE)
    screen.blit(pos_text, (hud_x + 20, y_offset))
    y_offset += 40
    
    if player.treasure_found:
        treasure_text = large_font.render("💰 FOUND!", True, BRIGHT_GOLD)
        pygame.draw.rect(screen, RED, (hud_x + 10, y_offset, hud_width - 20, 50))
        pygame.draw.rect(screen, BRIGHT_GOLD, (hud_x + 10, y_offset, hud_width - 20, 50), 3)
        screen.blit(treasure_text, (hud_x + 15, y_offset + 5))
    elif player.is_dead:
        dead_text = large_font.render("☠️ EXHAUSTED", True, RED)
        screen.blit(dead_text, (hud_x + 15, y_offset + 5))
    else:
        treasure_dist = abs(player.row - treasure_position[0]) + abs(player.col - treasure_position[1])
        treasure_text = small_font.render(f"🗺️ Treasure Distance: {treasure_dist}", True, BRIGHT_GOLD)
        screen.blit(treasure_text, (hud_x + 20, y_offset))
    
    y_offset = HEIGHT - 120
    if game_state == GameState.PLAYING:
        for control in ["Arrow Keys - Move", "G - Ask AI for Help (Dijkstra)", "ESC - Menu"]:
            text = tiny_font.render(control, True, LIGHT_GRAY)
            screen.blit(text, (hud_x + 20, y_offset))
            y_offset += 25

def draw_menu():
    screen.fill(NAVY_BLUE)
    title = title_font.render("⚓ PIRATE ISLAND ⚓", True, GOLD)
    title_rect = title.get_rect(center=(WIDTH // 2, 80))
    screen.blit(title, title_rect)
    
    subtitle = large_font.render("Dijkstra's Journey", True, BRIGHT_GOLD)
    subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, 150))
    screen.blit(subtitle, subtitle_rect)
    
    desc_y = 280
    descriptions = [
    "Explore the island and find the treasure before your stamina runs out!",
    "Be careful!!"
    "Forests & Rocks drain your energy.",
    "Press G if you give up, the AI (Dijkstra) will find the most efficient route.",
    ]
    for desc in descriptions:
        text = small_font.render(desc, True, WHITE)
        text_rect = text.get_rect(center=(WIDTH // 2, desc_y))
        screen.blit(text, text_rect)
        desc_y += 40
    
    button_y = 500
    button_rect = pygame.Rect((WIDTH - 200) // 2, button_y, 200, 60)
    pygame.draw.rect(screen, BRIGHT_GOLD, button_rect)
    pygame.draw.rect(screen, RED, button_rect, 3)
    start_text = large_font.render("PLAY", True, BLACK)
    start_rect = start_text.get_rect(center=button_rect.center)
    screen.blit(start_text, start_rect)
    
    return button_rect

def draw_game_over():
    screen.fill(NAVY_BLUE)
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(200)
    overlay.fill(BLACK)
    screen.blit(overlay, (0, 0))
    
    if player.treasure_found:
        title = title_font.render("🏆 TREASURE FOUND! 🏆", True, BRIGHT_GOLD)
    else:
        title = title_font.render("☠️ OUT OF STAMINA! ☠️", True, RED)
        
    title_rect = title.get_rect(center=(WIDTH // 2, 150))
    screen.blit(title, title_rect)
    
    stats_y = 300
    stats = [
        f"Level: {current_level}",
        f"Distance Traveled: {player.distance_traveled} steps",
        f"Remaining Stamina: {player.current_stamina}",
    ]
    for stat in stats:
        text = medium_font.render(stat, True, WHITE)
        text_rect = text.get_rect(center=(WIDTH // 2, stats_y))
        screen.blit(text, text_rect)
        stats_y += 60
    
    next_button_rect = pygame.Rect((WIDTH - 200) // 2 - 120, 550, 200, 50)
    
    pygame.draw.rect(screen, FOREST_GREEN if player.treasure_found else GOLD, next_button_rect)
    pygame.draw.rect(screen, WHITE, next_button_rect, 3)
    btn_text = "NEXT LEVEL" if player.treasure_found else "RETRY LEVEL"
    text = medium_font.render(btn_text, True, BLACK)
    text_rect = text.get_rect(center=next_button_rect.center)
    screen.blit(text, text_rect)
    
    menu_button_rect = pygame.Rect((WIDTH - 200) // 2 + 120, 550, 200, 50)
    pygame.draw.rect(screen, RED, menu_button_rect)
    pygame.draw.rect(screen, WHITE, menu_button_rect, 3)
    menu_text = medium_font.render("MENU", True, BLACK)
    menu_rect = menu_text.get_rect(center=menu_button_rect.center)
    screen.blit(menu_text, menu_rect)
    
    return next_button_rect, menu_button_rect

def draw_level_select():
    screen.fill(NAVY_BLUE)
    title = title_font.render("SELECT LEVEL", True, GOLD)
    title_rect = title.get_rect(center=(WIDTH // 2, 80))
    screen.blit(title, title_rect)
    
    buttons = []
    button_y = 200
    for level in range(1, 6):
        button_rect = pygame.Rect((WIDTH - 300) // 2, button_y, 300, 60)
        pygame.draw.rect(screen, BRIGHT_GOLD, button_rect)
        pygame.draw.rect(screen, RED, button_rect, 3)
        level_text = medium_font.render(f"LEVEL {level}", True, BLACK)
        level_rect = level_text.get_rect(center=(button_rect.centerx, button_y + 30))
        screen.blit(level_text, level_rect)
        buttons.append((level, button_rect))
        button_y += 90
    return buttons

def draw_ai_demo():
    info_text = medium_font.render("🤖 AI SEARCHING FOR THE MOST EFFICIENT DIJKSTRA ROUTE", True, BRIGHT_GOLD)
    info_rect = info_text.get_rect(center=(WIDTH // 2, 20))
    screen.blit(info_text, info_rect)
    if ai_path:
        path_info = small_font.render(f"Steps: {ai_current_step + 1} / {len(ai_path)}", True, WHITE)
        screen.blit(path_info, (20, HEIGHT - 40))

running = True
start_button_rect = None
level_buttons = None
next_button_rect = None
menu_button_rect = None

while running:
    clock.tick(FPS)
    animation_counter += 1
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            
            if game_state == GameState.MENU and start_button_rect:
                if start_button_rect.collidepoint(mouse_pos):
                    game_state = GameState.LEVEL_SELECT
            
            elif game_state == GameState.LEVEL_SELECT and level_buttons:
                for level, rect in level_buttons:
                    if rect.collidepoint(mouse_pos):
                        current_level = level
                        init_game(level)
                        game_state = GameState.PLAYING
            
            elif game_state == GameState.GAME_OVER:
                if next_button_rect and next_button_rect.collidepoint(mouse_pos):
                    if player.treasure_found:
                        if current_level < 5:
                            current_level += 1
                            init_game(current_level)
                            game_state = GameState.PLAYING
                        else:
                            game_state = GameState.MENU
                            current_level = 1
                    else:
                        init_game(current_level)
                        game_state = GameState.PLAYING
                
                if menu_button_rect and menu_button_rect.collidepoint(mouse_pos):
                    game_state = GameState.MENU
                    current_level = 1
        
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state in [GameState.PLAYING, GameState.AI_DEMO]:
                    game_state = GameState.MENU
            
            if event.key == pygame.K_SPACE and game_state == GameState.MENU:
                game_state = GameState.LEVEL_SELECT
            
            if event.key == pygame.K_g and game_state == GameState.PLAYING:
                ai_path, ai_cost = dijkstra_shortest_path(game_map, player.row, player.col, 
                                                          treasure_position[0], treasure_position[1])
                if ai_path:
                    game_state = GameState.AI_DEMO
                    ai_current_step = 0
            
            if game_state == GameState.PLAYING and not player.is_dead:
                new_row, new_col = player.row, player.col
                if event.key == pygame.K_UP: new_row -= 1
                if event.key == pygame.K_DOWN: new_row += 1
                if event.key == pygame.K_LEFT: new_col -= 1
                if event.key == pygame.K_RIGHT: new_col += 1
                
                if 0 <= new_row < len(game_map) and 0 <= new_col < len(game_map[0]):
                    target_tile = game_map[new_row][new_col]
                    if target_tile != "W":
                        move_cost = get_tile_cost(target_tile)
                        player.move(new_row, new_col, move_cost)
                        reveal_area(player.row, player.col)
                        
                        if (player.row, player.col) == treasure_position:
                            player.treasure_found = True
                            game_state = GameState.GAME_OVER
                        elif player.is_dead:
                            game_state = GameState.GAME_OVER
    
    if game_state == GameState.AI_DEMO:
        if animation_counter % 10 == 0: 
            if ai_current_step < len(ai_path) - 1:
                ai_current_step += 1
                next_pos = ai_path[ai_current_step]
                
                target_tile = game_map[next_pos[0]][next_pos[1]]
                player.move(next_pos[0], next_pos[1], get_tile_cost(target_tile))
                reveal_area(player.row, player.col)
            else:
                player.treasure_found = True
                game_state = GameState.GAME_OVER
    
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