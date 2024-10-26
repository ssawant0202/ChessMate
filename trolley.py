import sys
import time
from TMC2209.src.TMC_2209_StepperDriver import *
from RPi import GPIO
from chess_board import chess_board_inst, Move
# Pins assignment
MAGNET_PIN = 18

ENABLE0_PIN = 21
STEP0_PIN = 16
DIR0_PIN = 20

ENABLE1_PIN = 26
STEP1_PIN = 13
DIR1_PIN = 19

# Define variables for aDir, bDir, aPower, bPower
aDir = 0
bDir = 1
aPower = 2
bPower = 3

SQUARE_STEP = 505
DIAG_STEP = 1010

class Trolley:

    # Motor control settings [aDir, bDir, aPower, bPower]
    MOTOR_DIREC = {
        "XLEFT": [-1, 1, 1, 1],
        "XRIGHT": [1, -1, 1, 1],
        "YDOWN": [-1, -1, 1, 1],
        "YUP": [1, 1, 1, 1],
        "DDOWNL": [-1, -1, 1, 0],
        "DDOWNR": [-1, 1, 0, 1],
        "DUPL": [-1, -1, 0, 1],
        "DUPR": [1, -1, 1, 0]
    }

    def __init__(self, free_speed = 1000, free_acceleration = 1000, loaded_speed = 500, loaded_acceleration = 300):

        self.free_speed = free_speed
        self.free_acceleration = free_acceleration
        self.loaded_speed = loaded_speed
        self.loaded_acceleration = loaded_acceleration
        self.currentX = 7
        self.currentY = 7
        self.stallguard_threshold_1 = 250
        self.stallguard_threshold_2 = 250
        self.castling = None
        # Pin Setup for ElectroMagnet
        GPIO.setmode(GPIO.BCM)  
        GPIO.setup(MAGNET_PIN, GPIO.OUT)  
        self.magnet_OFF()

        # Set up the 2 Core XY motors
        self.tmc2 = TMC_2209(ENABLE0_PIN, STEP0_PIN, DIR0_PIN, driver_address=0)
        self.tmc1 = TMC_2209(ENABLE1_PIN, STEP1_PIN, DIR1_PIN, driver_address=1)

        for tmc in [self.tmc1, self.tmc2]:

            tmc.tmc_logger.set_loglevel(Loglevel.DEBUG)
            tmc.set_direction_reg(False)
            tmc.set_current(300)
            tmc.set_interpolation(True)
            tmc.set_spreadcycle(False)
            tmc.set_microstepping_resolution(2)
            tmc.set_internal_rsense(False)
            tmc.set_motor_enabled(True)
            
        self.move_to_chess_origin()
        self.take_initial_position()

    def move_to_chess_origin(self):
        
        for tmc in [self.tmc1, self.tmc2]:
            tmc.set_acceleration(self.free_acceleration)
            tmc.set_max_speed(self.free_speed)
            
        #Find one edge
        self.move_in_direction(1, "DDOWNL")
        self.tmc2.run_to_position_steps_threaded(10000, MovementAbsRel.RELATIVE)
        self.tmc1.take_me_home(threshold=self.stallguard_threshold_1)
        self.tmc2.stop()
        self.tmc2.set_motor_enabled(False)
        
        # Find the physical origin
        self.tmc1.take_me_home(threshold=self.stallguard_threshold_2)
        self.tmc2.set_motor_enabled(True)
        
        # Move to chess origin
        self.move_in_direction(0.75, "XLEFT")

    def move_in_direction(self, inc, direction: str):
        
        print(inc, direction)
        if direction in self.MOTOR_DIREC:
            bits = self.MOTOR_DIREC[direction]
            if direction in ["XLEFT", "XRIGHT", "YUP", "YDOWN"]: 
                base_step = int(SQUARE_STEP*inc)
            elif direction in ["DUPL", "DUPR", "DDOWNL", "DDOWNR"]:
                base_step = int(DIAG_STEP*inc)

            if bits[aPower]:
                steps = base_step * bits[aDir]
                self.tmc1.run_to_position_steps_threaded(steps, MovementAbsRel.RELATIVE)
            if bits[bPower]:
                steps = base_step * bits[bDir]
                self.tmc2.run_to_position_steps_threaded(steps, MovementAbsRel.RELATIVE)

            self.tmc1.wait_for_movement_finished_threaded()
            self.tmc2.wait_for_movement_finished_threaded()

    def move_rook_castling(self):
        if self.castling[0] == 'white':
            self.move_in_direction(0.5, 'YUP')
        elif self.castling[0] == 'black':
            self.move_in_direction(0.5, 'YDOWN')
            
        if self.castling[1] == 'short':
            self.move_in_direction(2, 'XLEFT')
        elif self.castling[1] == 'long':
            self.move_in_direction(3, 'XRIGHT')
        
        if self.castling[0] == 'black':
            self.move_in_direction(0.5, 'YUP')
        elif self.castling[0] == 'white':
            self.move_in_direction(0.5, 'YDOWN')     
    
    def check_path_for_knight(self, move: Move):
        delta_x = move.endX - move.startX
        
        if abs(delta_x) == 2:
            x_middle = int((move.startX + move.endX)/2)
            if chess_board_inst.is_empty(x_middle, move.endY):
                first_move = Move(move.startX, move.startY, x_middle, move.endY)
                self.calculate_movement(first_move)
                second_move = Move(x_middle, move.endY, move.endX, move.endY)
                self.calculate_movement(second_move)
                return True
            elif chess_board_inst.is_empty(x_middle, move.startY):
                first_move = Move(move.startX, move.startY, x_middle, move.startY)
                self.calculate_movement(first_move)
                second_move = Move(x_middle, move.startY, move.endX, move.endY)
                self.calculate_movement(second_move)
                return True
        else:
            y_middle = int((move.startY + move.endY)/2)
            if chess_board_inst.is_empty(move.startX, y_middle):
                first_move = Move(move.startX, move.startY, move.startX, y_middle)
                self.calculate_movement(first_move)
                second_move = Move(move.startX, y_middle, move.endX, move.endY)
                self.calculate_movement(second_move)
                return True
            
            if chess_board_inst.is_empty(move.endX, y_middle):
                first_move = Move(move.startX, move.startY, move.endX, y_middle)
                self.calculate_movement(first_move)
                second_move = Move(move.endX, y_middle, move.endX, move.endY)
                self.calculate_movement(second_move)
                return True
        
        return False
        
    def move_knight(self, delta_x, delta_y):

        if abs(delta_x) == 2 and abs(delta_y) == 1:
            self.move_in_direction(0.5, 'YUP' if delta_y > 0 else 'YDOWN')
            self.move_in_direction(2, 'XRIGHT' if delta_x > 0 else 'XLEFT')
            self.move_in_direction(0.5, 'YUP' if delta_y > 0 else 'YDOWN')
        elif abs(delta_x) == 1 and abs(delta_y) == 2:
            self.move_in_direction(0.5, 'XRIGHT' if delta_x > 0 else 'XLEFT')
            self.move_in_direction(2, 'YUP' if delta_y > 0 else 'YDOWN')
            self.move_in_direction(0.5, 'XRIGHT' if delta_x > 0 else 'XLEFT')

    def check_castling_move(self, move: Move):
        piece_to_move = chess_board_inst.get_piece(move.startX, move.startY)
        if piece_to_move == 'k' and move.startY == 7:
            if move.startX == 4 and move.endX == 6:
                return ('black', 'short', 'h8f8')
            elif move.startX == 4 and move.endX == 2:
                return ('black', 'long', 'a8d8')
        
        if piece_to_move == 'K' and move.startY == 0:
            if move.startX == 4 and move.endX == 6:
                return ('white', 'short', 'h1f1')
            elif move.startX == 4 and move.endX == 2:
                return ('white', 'long', 'a1d1')
        
        return None
    
    def is_knight_move(self, delta_x, delta_y):
        return (abs(delta_x) == 2 and abs(delta_y) == 1) or (abs(delta_x) == 1 and abs(delta_y) == 2)

    def calculate_movement(self, move: Move, rook_castling = False, loaded_move = False):
        # Calculate differences in x and y coordinates
        delta_x = move.endX - move.startX
        delta_y = move.endY - move.startY
        
        if delta_x == 0 and delta_y == 0:
            return 
        
        print(f"DeltaX: {delta_x}, DeltaY: {delta_y}")
        
        if loaded_move:
            if rook_castling:
                self.move_rook_castling()
                self.castling = None
                return
            
            self.castling = self.check_castling_move(move)
                
            if self.is_knight_move(delta_x, delta_y):
                if self.check_path_for_knight(move):
                    return
                self.move_knight(delta_x, delta_y)
                return
                
        if delta_x == delta_y:
            if delta_x > 0:
                self.move_in_direction(delta_x, "DUPR")
            else:
                self.move_in_direction(-delta_x, "DDOWNL")
        elif delta_x == -delta_y:
            if delta_x > 0:
                self.move_in_direction(delta_x, "DUPL")
            else:
                self.move_in_direction(-delta_x, "DDOWNR")
        else:
            if delta_x > 0:
                self.move_in_direction(delta_x, "XRIGHT")
            elif delta_x < 0:
                self.move_in_direction(-delta_x, "XLEFT")

            if delta_y > 0:
                self.move_in_direction(delta_y, "YUP")
            elif delta_y < 0:
                self.move_in_direction(-delta_y, "YDOWN")

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

    def make_move(self, move_string, rook_castling = False):
        move = self.chess_to_cartesian(move_string)
        if rook_castling:
            print(move_string)
        # Bring the trolley to the piece
        free_move = Move(self.currentX, self.currentY, move.startX, move.startY)
        self.set_speed_acceleration(loaded=False)
        self.calculate_movement(free_move)

        # Make a move with that piece
        self.set_speed_acceleration(loaded=True)
        self.magnet_ON()
        self.calculate_movement(move, rook_castling=rook_castling, loaded_move=True)
        time.sleep(1)
        self.magnet_OFF()

        self.currentX = move.endX
        self.currentY = move.endY
        chess_board_inst.move_piece(move)
        
        if self.castling is not None:
            print(self.castling)
            self.make_move(self.castling[2], rook_castling = True)

    def take_initial_position(self):
        chess_board_inst.board = chess_board_inst.create_starting_board()
        free_move = Move(self.currentX, self.currentY, 3, 7)
        self.set_speed_acceleration(loaded=False)
        self.calculate_movement(free_move)
        self.currentX = 3
        self.currentY = 7
        
    def demo_test(self):
        # Prompt the user for a direction
        while(True):
            position = input("Enter move: ")
            # move = self.chess_to_cartesian(position)
            # self.calculate_movement(move)
            self.make_move(position)

    def set_speed_acceleration(self, loaded):
        for tmc in [self.tmc1, self.tmc2]:    
            if loaded:        
                tmc.set_acceleration(self.loaded_acceleration)
                tmc.set_max_speed(self.loaded_speed)
            else:
                tmc.set_acceleration(self.free_acceleration)
                tmc.set_max_speed(self.free_speed)

    def magnet_ON(self):
        GPIO.output(MAGNET_PIN, GPIO.HIGH)

    def magnet_OFF(self):
        GPIO.output(MAGNET_PIN, GPIO.LOW)

    def __del__(self):
        self.take_initial_position()
        GPIO.cleanup(MAGNET_PIN)


if __name__ == "__main__":
    trolley = Trolley()
    trolley.demo_test()
    