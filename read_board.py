import threading
from time import sleep
import RPi_I2C_driver
from RPi import GPIO
from lichess_api import add_user_move, get_bot_move, is_game_active, get_game_status, move_accepted, is_move_legal, get_time_left
from board_detection import board_detection_init, get_user_move, report_bot_move, report_illegal_move
from chess_board import *
from models import GameParams
from trolley import *

previous_move = "a8a8"
trolley = None
mylcd = None
illegal_move = False
main_signal = True
debug = False
thread1 = None
thread2 = None

DOME_BUTTON_LED = 22

def convert_seconds_to_min_sec(seconds: int):
    # Calculate minutes and remaining seconds
    minutes, sec = divmod(seconds, 60)
    # Format the string as min:sec with leading zeros for seconds if needed
    return f"{minutes}:{sec:02}"

def lcd_init():
    global mylcd
    print('Initialising the LCD')
    if mylcd is None:
        mylcd = RPi_I2C_driver.lcd()
    
def buttons_init():
    print('Initialising the button')
    # Set the GPIO mode
    GPIO.setmode(GPIO.BCM)
    # Set up the button pin as an input with a pull-up resistor
    GPIO.setup(RPi_I2C_driver.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(DOME_BUTTON_LED, GPIO.OUT)

def lcd_start_message(level):
    mylcd.lcd_display_string_pos(f"Game set", 1, 5)
    mylcd.lcd_display_string_pos(f"Level {level}", 3, 5)
    
def lcd_display_key(lcd_secret):
    lcd_init()
    mylcd.lcd_display_secret_key(lcd_secret)

def lcd_illegal_move(move):
    mylcd.lcd_display_string(f"{move} is illegal", 1)
    mylcd.lcd_display_string("Make a new move", 3)
  
def button_led_ON():
    GPIO.output(DOME_BUTTON_LED, GPIO.HIGH)

def button_led_OFF():
    GPIO.output(DOME_BUTTON_LED, GPIO.LOW) 
    
def lcd_thread(time, level):
    global mylcd, illegal_move
    mylcd.lcd_clear()
    clear_once = 1
    lcd_start_message(level)
    sleep(3)
    while is_game_active():
        if illegal_move:
            if clear_once:
                mylcd.lcd_clear()
                clear_once = 0
            lcd_illegal_move(previous_move)
        else:
            clear_once = 1
            white_seconds, black_seconds = get_time_left()
            if not white_seconds:
                white_seconds = time
            if not black_seconds:
                black_seconds = time

            white_time = convert_seconds_to_min_sec(white_seconds)
            black_time = convert_seconds_to_min_sec(black_seconds)

            mylcd.lcd_display_chess_time(white_time, black_time)
        sleep(0.1)

    mylcd.lcd_clear()
    mylcd.lcd_display_string_pos(get_game_status(), 2, 5)
    sleep(5)
    mylcd.lcd_clear()
    mylcd.lcd_display_string("Start new game", 2)

    while (main_signal):
        sleep(1)
        
def main_thread():
    global previous_move, trolley, illegal_move
    sleep(3)
    while is_game_active():
        
        # Light the button for user
        button_led_ON()
        # Read the button status
        while(GPIO.input(RPi_I2C_driver.BUTTON_PIN) != GPIO.LOW):
            if not is_game_active():
                break
            sleep(0.1)
        
        # Stop the button light for user
        button_led_OFF()
        
        if illegal_move:
            illegal_move = False
            mylcd.lcd_clear()
            
        user_move = get_user_move()
        if debug:
            feedback = input(f'{user_move} ? ')
            if feedback == 'y':
                pass
            else:
                user_move = feedback
                
        print(f'User move: {user_move}')
        add_user_move(user_move)
        previous_move = user_move
        if user_move == 'q':
            break
        
        print("Move passed to lichess")   
        move_accepted.wait()
        move_accepted.clear()
        print("Move accepted by lichess")
        
        if is_move_legal():
            chess_board_inst.move_piece_string(user_move)
            bot_move = None
            while(bot_move is None or bot_move == previous_move):
                sleep(1)
                bot_move = get_bot_move()
                
            previous_move = bot_move
            print("Bot's move: ", bot_move)
            report_bot_move(bot_move)
            trolley.make_move(bot_move)
        else:
            report_illegal_move()
            illegal_move = True
            print(f"Illegal move {user_move}")
            #lcd_illegal_move(user_move)
    
    illegal_move = False
    trolley.take_initial_position()
    while (main_signal):
        sleep(1)

def trolley_init():
    global trolley
    if trolley is None:
        trolley = Trolley()

def kill_threads():
    global thread1, thread2, main_signal
    main_signal = False
    if thread1 is not None:
        if thread1.is_alive():
            thread1.join()
    if thread2 is not None:
        if thread2.is_alive():
            thread2.join()    
    
    print("Killed board threads")  

def init_board_control(debug_flag):
    kill_threads()
    lcd_init()
    buttons_init()
    trolley_init()
    board_detection_init()
    global debug
    debug = debug_flag
    
    
def start_threads(time, level):
    global main_signal, thread1, thread2
    thread1 = threading.Thread(target=main_thread)
    thread2 = threading.Thread(target=lcd_thread, args=(time, level))
    thread1.start()
    thread2.start()
    main_signal = True
    
if __name__ == "__main__":
    init_board_control()

