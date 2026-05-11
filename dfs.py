def dfs(game_map, row, col, visited):
    rows = len(game_map)
    cols = len(game_map[0])

    # cek batas map
    if row < 0 or row >= rows or col < 0 or col >= cols:
        return

    # jika air
    if game_map[row][col] == "W":
        return

    # jika sudah dikunjungi
    if (row, col) in visited:
        return

    # tandai visited
    visited.add((row, col))

    # arah gerak
    directions = [
        (-1, 0),
        (1, 0),
        (0, -1),
        (0, 1)
    ]

    # eksplor tetangga
    for dr, dc in directions:
        dfs(game_map, row + dr, col + dc, visited)