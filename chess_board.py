class Move:
    def __init__(self, startX, startY, endX, endY):
        self.startX = startX
        self.startY = startY
        self.endX = endX
        self.endY = endY
            
class ChessBoard:
    def __init__(self):
        # Initialize the board with pieces in their starting positions
        self.board = self.create_starting_board()
    
    def create_starting_board(self):
        # Set up the board with the standard initial positions
        starting_board = [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
            ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        ]
        return starting_board

    def display_board(self):
        for row in self.board:
            print(' '.join(row))
        print()

    def chess_to_cartesian(self, chess_position):
        # Ensure the input string is in the correct format (e.g., "a1" to "h8")
        if len(chess_position) != 4:
            raise ValueError(f"Invalid chess position format: {chess_position}")
        if not ('a' <= chess_position[0] <= 'h') or not ('1' <= chess_position[1] <= '8'):
            raise ValueError(f"Invalid chess position format: {chess_position}")
        if not ('a' <= chess_position[2] <= 'h') or not ('1' <= chess_position[3] <= '8'):
            raise ValueError(f"Invalid chess position format: {chess_position}")

        # Convert the letter part of the chess notation to x coordinate
        startX = ord(chess_position[0]) - ord('a')
        endX = ord(chess_position[2]) - ord('a')
        # Convert the numeric part of the chess notation to y coordinate
        startY = int(chess_position[1]) - 1
        endY = int(chess_position[3]) - 1

        return Move(startX, startY, endX, endY)
    
    def move_piece_string(self, move_string):
        move = self.chess_to_cartesian(move_string)
        self.move_piece(move)
        
    def move_piece(self, move: Move):
        start_col, start_row = (move.startX, 7 - move.startY)
        end_col, end_row = (move.endX, 7 - move.endY)
        print(start_col, start_row)
        print(end_col, end_row)
        # Perform the move
        self.board[end_row][end_col] = self.board[start_row][start_col]
        self.board[start_row][start_col] = '.'
    
    def get_piece(self, x, y):
        return self.board[7-y][x]

    def is_empty(self, x, y):
        if self.get_piece(x,y) == '.':
            return True
        else:
            return False
        
chess_board_inst = ChessBoard()