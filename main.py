import random
import time
from presto import Presto
import random
import machine
import ntptime
import config

# Initialize Presto
presto = Presto()
display = presto.display

rtc = machine.RTC()
wifi = presto.connect()
touch = presto.touch
touch.poll()

class MazeGenerator:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Initialize maze (all walls)
        self.maze = [[1 for _ in range(width)] for _ in range(height)]
        self.visited = [[False for _ in range(width)] for _ in range(height)]
        
        # Calculate the size of the space in the upper right
        self.space_width = width // 4  # Width 1/4
        self.space_height = height // 8  # Height 1/8
        
        # Set the upper right space as a passage
        self.create_empty_space()
        
    def create_empty_space(self):
        """Create a space in the upper right and set walls at the boundary"""
        start_x = self.width - self.space_width
        start_y = 0
        
        # Make the space area a passage
        for y in range(start_y, start_y + self.space_height):
            for x in range(start_x, self.width):
                if self.is_valid_cell(x, y):
                    self.maze[y][x] = 0  # Make it a passage
                    self.visited[y][x] = True  # Mark as visited
        
        # Create walls at the boundary
        self.create_space_boundary(start_x, start_y)
        
    def is_valid_cell(self, x, y):
        """Check if the cell is within a valid range"""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def create_space_boundary(self, start_x, start_y):
        """Create walls at the boundary of the space"""
        # Left boundary (vertical wall)
        boundary_x = start_x - 1
        if boundary_x >= 0:
            for y in range(start_y, start_y + self.space_height):
                if self.is_valid_cell(boundary_x, y):
                    self.maze[y][boundary_x] = 1  # Wall
                    self.visited[y][boundary_x] = True
        
        # Bottom boundary (horizontal wall)
        boundary_y = start_y + self.space_height
        if boundary_y < self.height:
            for x in range(start_x, self.width):
                if self.is_valid_cell(x, boundary_y):
                    self.maze[boundary_y][x] = 1  # Wall
                    self.visited[boundary_y][x] = True
        
        # Wall at the bottom left corner (L-shaped corner)
        corner_x = start_x - 1
        corner_y = start_y + self.space_height
        if (self.is_valid_cell(corner_x, corner_y)):
            self.maze[corner_y][corner_x] = 1  # Wall
            self.visited[corner_y][corner_x] = True
    
    def is_boundary_cell(self, x, y):
        """Check if the cell is at the boundary of the space"""
        start_x = self.width - self.space_width
        start_y = 0
        boundary_y = start_y + self.space_height
        
        # Left boundary
        if x == start_x - 1 and start_y <= y < start_y + self.space_height:
            return True
        # Bottom boundary
        if y == boundary_y and start_x <= x < self.width:
            return True
        # Bottom left corner
        if x == start_x - 1 and y == boundary_y:
            return True
            
        return False
    
    def is_in_empty_space(self, x, y):
        """Check if the coordinates are within the upper right space"""
        start_x = self.width - self.space_width
        start_y = 0
        return (start_x <= x < self.width and 
                start_y <= y < start_y + self.space_height)
    
    def get_neighbors(self, x, y):
        """Get adjacent cells (cells two steps away)"""
        neighbors = []
        directions = [(0, -2), (2, 0), (0, 2), (-2, 0)]  # Up, right, down, left
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if (self.is_valid_cell(nx, ny) and 
                not self.visited[ny][nx] and 
                not self.is_in_empty_space(nx, ny) and  # Exclude space interior
                not self.is_boundary_cell(nx, ny)):     # Exclude boundaries too
                neighbors.append((nx, ny))
        
        return neighbors
    
    def generate_maze(self):
        """Generate a maze using depth-first search"""
        # Start point (odd coordinates)
        start_x, start_y = 1, 1
        
        # Adjust if the start point is within the space
        if self.is_in_empty_space(start_x, start_y):
            start_x = 1
            start_y = self.space_height + 1
            if start_y % 2 == 0:  # Make it odd coordinates
                start_y += 1
        
        self.maze[start_y][start_x] = 0  # Passage
        self.visited[start_y][start_x] = True
        
        stack = [(start_x, start_y)]
        
        while stack:
            current_x, current_y = stack[-1]
            neighbors = self.get_neighbors(current_x, current_y)
            
            if neighbors:
                # Randomly select an adjacent cell
                next_x, next_y = random.choice(neighbors)
                
                # Remove the wall between the current cell and the next cell
                wall_x = (current_x + next_x) // 2
                wall_y = (current_y + next_y) // 2
                
                # Ensure the wall is not within the space or at the boundary
                if (not self.is_in_empty_space(wall_x, wall_y) and
                    not self.is_boundary_cell(wall_x, wall_y)):
                    self.maze[wall_y][wall_x] = 0  # Convert wall to passage
                    self.maze[next_y][next_x] = 0  # Convert next cell to passage
                    self.visited[next_y][next_x] = True
                    
                    stack.append((next_x, next_y))
                else:
                    # Skip if within the space
                    continue
            else:
                stack.pop()
        
        # Set the goal point (near the bottom right, but avoiding the space)
        goal_x = self.width - 2
        goal_y = self.height - 2
        
        # Adjust if the goal is within the space
        if self.is_in_empty_space(goal_x, goal_y):
            goal_x = self.width - self.space_width - 2
        
        self.maze[goal_y][goal_x] = 0

        return

class MazeSolver:
    def __init__(self, maze, maze_display):
        self.maze = maze
        self.width = len(maze[0])
        self.height = len(maze)
        
        # Adjust the start point (avoiding the space)
        self.start = (1, 1)
        if maze_display.generator.is_in_empty_space(1, 1):
            start_y = maze_display.generator.space_height + 1
            if start_y % 2 == 0:
                start_y += 1
            self.start = (1, start_y)
        
        # Adjust the goal point
        goal_x = self.width - 2
        goal_y = self.height - 2
        if maze_display.generator.is_in_empty_space(goal_x, goal_y):
            goal_x = self.width - maze_display.generator.space_width - 2
        self.goal = (goal_x, goal_y)
        
        self.path = []
        self.visited_cells = set()
        self.display = maze_display
        
    def is_valid_move(self, x, y):
        """Check if movement is possible"""
        return (0 <= x < self.width and 
                0 <= y < self.height and 
                self.maze[y][x] == 0)
    
    def shuffle_list(self, lst):
        """Randomly shuffle a list"""
        for i in range(len(lst) - 1, 0, -1):
            j = random.randint(0, i)
            lst[i], lst[j] = lst[j], lst[i]
        return lst

    def solve(self):
        stack = [self.start]
        visited = set()
        parent = {}  # Record the parent of each node
        visited.add(self.start)
        parent[self.start] = None
        
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        shuffle_dirs = self.shuffle_list(directions)
        
        count = 0
        sleep_time = 0.01
        count_limit = 2 /sleep_time # clock overwrite each 2sec
        while stack:
            # check touch
            if self.display.get_touch():
                # stop solve
                return False

            x, y = stack.pop()

            if count > count_limit:
                count = 0
                self.display.draw_clock_in_space()
            count += 1

            # Visual feedback
            self.display.draw_cell(x, y, self.display.COLOR_SOLVE)
            presto.update()
            time.sleep(sleep_time)
    
            # Reached the goal
            if (x, y) == self.goal:
                # Calculate and build the path in reverse
                path = []
                current = (x, y)
                while current is not None:
                    path.append(current)
                    current = parent[current]
                self.path = path[::-1]  # Reverse to get start→goal order

                # solved
                return True
            
            # Explore adjacent cells
            for dx, dy in shuffle_dirs:
                nx, ny = x + dx, y + dy
                
                if self.is_valid_move(nx, ny) and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    self.visited_cells.add((nx, ny))
                    parent[(nx, ny)] = (x, y)
                    stack.append((nx, ny))
                    
            self.display.draw_cell(x, y, self.display.COLOR_DONE)
        
        return False

class MazeDisplay:
        
    def __init__(self, maze_generator):
        self.size_set(maze_generator)

        # Create pen colors
        self.COLOR_WALL = display.create_pen(64, 64, 128)       # Wall
        self.COLOR_STREET = display.create_pen(224, 224, 224)   # Passage
        self.COLOR_EMPTY_SPACE = self.COLOR_WALL
        self.COLOR_BOUNDARY = self.COLOR_WALL
        self.COLOR_START = display.create_pen(0, 255, 0)        # Start
        self.COLOR_GOAL = display.create_pen(255, 0, 0)         # Goal
        self.COLOR_SOLVE = display.create_pen(100, 120, 255)    # Solution path
        self.COLOR_DONE = display.create_pen(180, 180, 180)     # Explored
        self.COLOR_CURRENT = display.create_pen(255, 100, 100)  # Current position
        self.COLOR_BACK = display.create_pen(0, 0, 0)
        self.COLOR_CLOCK_TEXT = display.create_pen(255, 255, 255)     # Clock text (white)
        
    def size_set(self, maze_generator):
        self.maze = maze_generator.maze
        self.width = maze_generator.width
        self.height = maze_generator.height
        self.generator = maze_generator  # Keep reference
        
        # Calculate scaling to match Presto display size
        self.display_width, self.display_height = display.get_bounds()
        self.cell_width = self.display_width // self.width
        self.cell_height = self.display_height // self.height

    def get_touch(self):
        if touch.state:
            print("touch! {}, {}".format(touch.x, touch.y))

            # change maze size
            sizes = [19, 33, 79, 119]

            for n in range(len(sizes)):
                if  sizes[n] == config.MAZE_WIDTH:
                    break
            n += 1
            if n >= len(sizes):
                n = 0

            config.MAZE_WIDTH = sizes[n]
            config.MAZE_HEIGHT = sizes[n]

            # Display maze size Change!
            display.set_pen(self.COLOR_STREET)
            display.rectangle(0, self.display_height//2-20, self.display_width, 40)
            display.set_pen(self.COLOR_GOAL)
            display.text(f"CHANGE SIZE {sizes[n]}", 16, self.display_height//2 - 8, self.display_width, 3)
            presto.update()

            time.sleep(1)
        
            return True

        return False

    def get_current_time(self):

        """Get the current time in HH:MM format"""
        current_t = rtc.datetime()
        hours = current_t[4]

        hours += config.GMT_OFFSET
        if hours > 24:
            hours -= 24
        minutes =  current_t[5]
        secs =  current_t[6]

        return f"{hours:02d}:{minutes:02d}"
    
    def draw_clock_in_space(self):
        """Draw a clock in the upper right space"""

        # Get the range of the space
        start_x = self.width - self.generator.space_width
        start_y = 0
        space_width = self.generator.space_width
        space_height = self.generator.space_height

        # Calculate the center position of the space (pixel coordinates)
        space_pixel_x = start_x * self.cell_width
        space_pixel_y = start_y * self.cell_height
        space_pixel_width = space_width * self.cell_width
        space_pixel_height = space_height * self.cell_height
        
        display.set_pen(self.COLOR_EMPTY_SPACE)
        display.rectangle(space_pixel_x, space_pixel_y, space_pixel_width, space_pixel_height)
        
        # Center position of the clock text
        center_x = space_pixel_x + space_pixel_width // 2
        center_y = space_pixel_y + space_pixel_height // 2
        
        # Get the current time
        time_str = self.get_current_time()
        
        # Display the time
        y_offset = 0
        if self.width < 80:
            y_offset = 2

        # TEXT
        display.set_pen(self.COLOR_SOLVE)
        display.text(time_str, center_x - 21, center_y - 8 + y_offset, 0, 2)

        # SHADOW
        display.set_pen(self.COLOR_CLOCK_TEXT)
        display.text(time_str, center_x - 22, center_y - 7 + y_offset, 0, 2)
    
    def draw_maze(self, solver=None, current_pos=None, show_visited=False):
        """Draw the maze on the Presto display"""

        display.set_pen(self.COLOR_BACK)
        display.clear()
        display.set_font("bitmap8")
        
        for y in range(self.height):
            for x in range(self.width):
                # Calculate the display position of the cell
                draw_x = x * self.cell_width
                draw_y = y * self.cell_height
                
                # Set the basic color
                if self.generator.is_in_empty_space(x, y):
                    # Upper right space
                    display.set_pen(self.COLOR_EMPTY_SPACE)
                elif self.generator.is_boundary_cell(x, y):
                    # Boundary wall
                    display.set_pen(self.COLOR_BOUNDARY)
                elif self.maze[y][x] == 1:  # Wall
                    display.set_pen(self.COLOR_WALL)
                else:  # Passage
                    display.set_pen(self.COLOR_STREET)
                    
                # Fill with rectangle
                display.rectangle(draw_x, draw_y, self.cell_width, self.cell_height)
        
        # Current position
        if current_pos:
            x, y = current_pos
            display.set_pen(self.COLOR_CURRENT)
            display.rectangle(x * self.cell_width, y * self.cell_height, 
                             self.cell_width, self.cell_height)
        
        # Start point
        start_x, start_y = 1, 1
        if self.generator.is_in_empty_space(start_x, start_y):
            start_y = self.generator.space_height + 1
            if start_y % 2 == 0:
                start_y += 1
        self.draw_cell(start_x, start_y, self.COLOR_START)
        
        # Goal point
        goal_x = self.width - 2
        goal_y = self.height - 2
        if self.generator.is_in_empty_space(goal_x, goal_y):
            goal_x = self.width - self.generator.space_width - 2
        self.draw_cell(goal_x, goal_y, self.COLOR_GOAL)
        
        # Draw a clock in the upper right space
        self.draw_clock_in_space()
        
        # Update screen
        presto.update()
    
    def draw_cell(self, x, y, color):
        """Draw only the specified cell"""
        draw_x = x * self.cell_width
        draw_y = y * self.cell_height
        display.set_pen(color)
        display.rectangle(draw_x, draw_y, self.cell_width, self.cell_height)
    
    def animate_solution(self, solver):
        """Display the solution process as an animation"""
        if not solver.path:
            return
        
        print("Displaying solution animation...")
        for pos in solver.path:
            # check touch
            if self.get_touch():
                return False

            self.draw_cell(pos[0], pos[1], self.COLOR_SOLVE)

            # Update screen
            presto.update()
            time.sleep(0.05)

        # Redraw start and goal
        start_x, start_y = solver.start
        goal_x, goal_y = solver.goal
        self.draw_cell(start_x, start_y, self.COLOR_START)
        self.draw_cell(goal_x, goal_y, self.COLOR_GOAL)
        
        presto.update()

        print(f"Solution complete! Path length: {len(solver.path)}")
        return True

def main():
    """Main function"""
    print("Starting maze generation and solution program...")
    
    
    while True:
        
        maze_width = config.MAZE_WIDTH
        maze_height = config.MAZE_HEIGHT

        print(f"\nGenerating a new maze... {maze_width}x{maze_height}")

        # Generate maze
        generator = MazeGenerator(maze_width, maze_height)
        generator.generate_maze()
        
        # Display maze
        maze_display = MazeDisplay(generator)
        if maze_display.draw_maze():
            continue
        
        # Solve the maze
        print("Solving the maze...")
        solver = MazeSolver(generator.maze, maze_display)
        if solver.solve():
            if not maze_display.animate_solution(solver):
                continue
        else:
            continue

        print(f"Generating the next maze in {config.NEXT_SLEEP} seconds...")
        for n in range(config.NEXT_SLEEP*10):
            maze_display.get_touch()
            time.sleep(0.1)
        
if __name__ == "__main__":
    if config.HAS_WIFI:
        try:
            wifi = presto.connect()
        except ValueError as e:
            while True:
                print(e)
        except ImportError as e:
            while True:
                print(e)
        try:
            ntptime.settime()
        except OSError:
            while True:
                print("Unable to get time.\n\nCheck your network try again.")
                time.sleep(1)

    main()
