import lichess.api
import berserk
import time
import requests
import threading
import csv
import json
from models import GameParams

# Monkey-patch requests to avoid using simplejson
from requests.models import Response
def patched_json(self, **kwargs):
    return json.loads(self.text, **kwargs)
Response.json = patched_json

URL = 'https://lichess.org/'
game_not_over = False
game_status = ''
user_move = None
game_id = None
client = None
session = None
move_accepted = threading.Event()
move_done = threading.Semaphore(0)
move_legal = False
game_state = None

thread_post_moves = None
thread_main_game = None
main_signal = True

# Function to create a new game with a bot
def send_challenge(params: GameParams):
    global game_id

    parameters = {
        "clock_limit": params.time,         # Time limit for each player in seconds
        "clock_increment": params.time_inc,      # Time increment per move in seconds
        "days": None,               # Number of days the challenge is valid (None for no limit)
        "color": params.side,           # Choose color randomly (can also be "white" or "black")
        "variant": "standard",      # Chess variant (standard, chess960, etc.)
        "level": params.level                 # AI level (1-8)
    }
    print(parameters)
    response = client.challenges.create_ai(**parameters)
    game_id = response['id']
    visit_gameURL(game_id)

# Function to resign from the game
def resign_game():
    try:
        client.board.resign_game(game_id)
    except requests.exceptions.RequestException as e:
        print("Error:", e)

# Function to visit the game URL
def visit_gameURL(game_id):
    url = URL + game_id
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print("Successfully visited the URL:", response.url)
        else:
            print("Failed to visit the URL:", response.status_code)
    except requests.exceptions.RequestException as e:
        print("Error:", e)

def is_move_legal():
    return move_legal

# Function to get game moves
def get_bot_move():
    last = None
    if game_state:
        if 'moves' in game_state:
            moves = game_state['moves']
            if moves:
                last = moves.split()[-1]
    return last

def get_time_left():
    if game_state:
        white_seconds = game_state['wtime']//1000
        black_seconds = game_state['btime']//1000
        return (white_seconds, black_seconds)
    return None, None

def get_game_status():
    if game_state:
        status = game_state['status']
        return status
    return None

def add_user_move(move):
    global user_move
    user_move = move
    move_done.release()

def is_game_active():
    return game_not_over

# Function to handle game state updates
def handle_game_state_update(update):
    if update["state"]:
        return update["state"]["status"]

# Function to check if it's the player's turn
def is_my_turn(update):
    if update["game"]:
        return update["game"]["isMyTurn"]
    return False

# Function to post user moves
def post_user_moves():
    global game_not_over, user_move, move_accepted, move_legal
    while game_not_over:
        for update in client.board.stream_incoming_events():
            if is_my_turn(update) and game_not_over:
                while game_not_over:
                    if move_done.acquire(timeout=1):
                        break
                    else:
                        print("lichess: No move done")
                    
                if user_move == 'q':
                    resign_game()
                    game_not_over = False
                    break
                #print(f"Posting Move {user_move}\n")
                try:
                    client.board.make_move(game_id, user_move)
                    move_legal = True
                except:
                    move_legal = False
                move_accepted.set()
                user_move = None
                break
        #time.sleep(3)
    while (main_signal):
        time.sleep(1)
        
def main_thread():
    global client, game_not_over, game_status, game_state
    while game_not_over:
        for update in client.board.stream_game_state(game_id):
            if 'state' in update:
                game_state = update['state']              
            game_status = handle_game_state_update(update)
            game_not_over = False if game_status in ['draw', 'mate', 'resign', 'outoftime'] else True
            break

    print(f"Game Over! Status: {game_status}")
    client = None
    while (main_signal):
        time.sleep(1)

def kill_threads():
    global thread_main_game, thread_post_moves, main_signal
    main_signal = False
    if thread_main_game is not None:
        if thread_main_game.is_alive():
            thread_main_game.join()
    if thread_post_moves is not None:
        if thread_post_moves.is_alive():
            thread_post_moves.join()    
    
    print("Killed lichess threads") 
    
def launch_game(parameters: GameParams, user_api_token):
    
    global move_accepted, move_legal, game_not_over, client, session, thread_main_game, thread_post_moves, main_signal
    kill_threads()
    if session is None:
        session = berserk.TokenSession(user_api_token)
    if client is None:
        client = berserk.Client(session=session)
    game_not_over = True
    move_done.acquire(blocking=False)
    move_accepted.clear()
    send_challenge(parameters)
    thread_post_moves = threading.Thread(target=post_user_moves)
    thread_main_game = threading.Thread(target=main_thread)
    
    main_signal = True
    print("Starting game")
    thread_post_moves.start()
    thread_main_game.start()


if __name__ == "__main__":
    launch_game()