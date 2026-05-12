import heapq

def get_tile_cost(tile_type):
    """
    Determine the stamina weight (cost) of each type of plot.
    """
    if tile_type in ["L", "T"]:
        return 1  
    elif tile_type == "F":
        return 2  
    elif tile_type == "R":
        return 3 
    return float('inf')  

def dijkstra_shortest_path(game_map, start_row, start_col, target_row, target_col):
    """
    Uses Dijkstra to find the route with the minimum 'stamina cost'.
    Returns a tuple: (list_coordinates_path, total_stamina_cost)
    """
    rows = len(game_map)
    cols = len(game_map[0])
    
    pq = [(0, start_row, start_col, [(start_row, start_col)])]
    
    min_costs = {(start_row, start_col): 0}
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  
    
    while pq:
        current_cost, row, col, path = heapq.heappop(pq)
        
        if row == target_row and col == target_col:
            return path, current_cost
            
        if current_cost > min_costs.get((row, col), float('inf')):
            continue
            
        for dr, dc in directions:
            new_row = row + dr
            new_col = col + dc
            
            if 0 <= new_row < rows and 0 <= new_col < cols:
                tile = game_map[new_row][new_col]
                
                if tile != "W": 
                    move_cost = get_tile_cost(tile)
                    new_cost = current_cost + move_cost
                    
                    if new_cost < min_costs.get((new_row, new_col), float('inf')):
                        min_costs[(new_row, new_col)] = new_cost
                        new_path = path + [(new_row, new_col)]
                        heapq.heappush(pq, (new_cost, new_row, new_col, new_path))
                        
    return [], 0