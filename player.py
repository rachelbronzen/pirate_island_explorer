class Player:
    def __init__(self, row, col, max_stamina=50):
        self.row = row
        self.col = col
        self.visited_count = 0
        self.treasure_found = False
        self.distance_traveled = 0
        self.direction = 'right'
        
        self.max_stamina = max_stamina
        self.current_stamina = max_stamina
        self.is_dead = False
    
    def move(self, new_row, new_col, stamina_cost):
        self.distance_traveled += 1
        self.row = new_row
        self.col = new_col
        
        self.current_stamina -= stamina_cost
        if self.current_stamina <= 0:
            self.current_stamina = 0
            self.is_dead = True