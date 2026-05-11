import heapq

def get_tile_cost(tile_type):
    """
    Menentukan bobot (cost) stamina dari setiap jenis petak.
    """
    if tile_type in ["L", "T"]:
        return 1  # Tanah lapang / Harta karun mudah dilalui
    elif tile_type == "F":
        return 2  # Hutan sedikit menguras tenaga
    elif tile_type == "R":
        return 3  # Mendaki batu sangat menguras tenaga
    return float('inf')  # Air tidak bisa dilalui

def dijkstra_shortest_path(game_map, start_row, start_col, target_row, target_col):
    """
    Menggunakan Dijkstra untuk menemukan rute dengan 'stamina cost' paling minimum.
    Mengembalikan tuple: (list_koordinat_path, total_cost_stamina)
    """
    rows = len(game_map)
    cols = len(game_map[0])
    
    # Priority Queue: (total_cost, row, col, path)
    # Dijkstra menggunakan Priority Queue agar selalu mengeksplorasi path dengan cost terendah lebih dulu
    pq = [(0, start_row, start_col, [(start_row, start_col)])]
    
    # Dictionary untuk menyimpan cost terendah untuk mencapai suatu node
    min_costs = {(start_row, start_col): 0}
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right
    
    while pq:
        current_cost, row, col, path = heapq.heappop(pq)
        
        # Jika sudah sampai ke treasure
        if row == target_row and col == target_col:
            return path, current_cost
            
        # Jika kita menemukan jalur yang lebih mahal dari yang sudah tercatat, abaikan
        if current_cost > min_costs.get((row, col), float('inf')):
            continue
            
        # Explore tetangga
        for dr, dc in directions:
            new_row = row + dr
            new_col = col + dc
            
            # Cek batas map
            if 0 <= new_row < rows and 0 <= new_col < cols:
                tile = game_map[new_row][new_col]
                
                if tile != "W":  # Jika bukan air
                    move_cost = get_tile_cost(tile)
                    new_cost = current_cost + move_cost
                    
                    # Jika menemukan jalur yang cost-nya lebih murah, update dan masukkan ke antrean
                    if new_cost < min_costs.get((new_row, new_col), float('inf')):
                        min_costs[(new_row, new_col)] = new_cost
                        new_path = path + [(new_row, new_col)]
                        heapq.heappush(pq, (new_cost, new_row, new_col, new_path))
                        
    # Jika tidak ada path yang ditemukan
    return [], 0