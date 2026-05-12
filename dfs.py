def dfs(game_map, row, col, visited):
    rows = len(game_map)
    cols = len(game_map[0])

    if row < 0 or row >= rows or col < 0 or col >= cols:
        return

    if game_map[row][col] == "W":
        return

    if (row, col) in visited:
        return

    visited.add((row, col))

    directions = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1)
    ]

    for dr, dc in directions:
        dfs(game_map, row + dr, col + dc, visited)