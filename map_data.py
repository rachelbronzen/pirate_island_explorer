import random

GAME_MAP_BASE = [
    ["W","W","W","W","W","W","W","W","W","W"],
    ["W","L","L","F","L","R","L","L","L","W"],
    ["W","L","W","W","L","W","W","W","L","W"],
    ["W","F","L","W","L","L","L","W","L","W"],
    ["W","W","L","W","W","R","L","W","L","W"],
    ["W","L","L","L","L","W","L","L","F","W"],
    ["W","L","W","W","F","W","W","W","L","W"],
    ["W","L","L","W","L","L","L","W","L","W"],
    ["W","L","L","L","L","W","L","L","L","W"],
    ["W","W","W","W","W","W","W","W","W","W"]
]

GAME_MAP = [row[:] for row in GAME_MAP_BASE]

def generate_map_with_difficulty(level):
    """
    Generate map based on level (1-5).
    Higher levels = more obstacles (rocks and forests)
    """
    import copy
    game_map = copy.deepcopy(GAME_MAP_BASE)
    
    obstacle_count = {
        1: 2,  
        2: 4,
        3: 6,
        4: 8,
        5: 10   
    }
    
    num_obstacles = obstacle_count.get(level, 2)
    
    for _ in range(num_obstacles):
        while True:
            row = random.randint(1, 8)
            col = random.randint(1, 8)
            if game_map[row][col] == "L": 
                obstacle_type = random.choice(["R", "F"])
                game_map[row][col] = obstacle_type
                break
    
    return game_map

def get_random_treasure_position(game_map):
    """
    Get a random treasure position from accessible land tiles.
    Make sure it is far from the starting position (1,1).
    IMPORTANT: Also changes the tile on the map to "T"
    """
    valid_positions = []
    for row in range(2, 8): 
        for col in range(2, 8):
            if game_map[row][col] == "L":
                distance = abs(row - 1) + abs(col - 1)
                if distance >= 6:  
                    valid_positions.append((row, col))
    
    if valid_positions:
        treasure_pos = random.choice(valid_positions)
        game_map[treasure_pos[0]][treasure_pos[1]] = "T"
        return treasure_pos
    else:
        game_map[8][6] = "T"
        return (8, 6)
