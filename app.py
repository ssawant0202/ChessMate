import os
import sys
import random
import secrets
import string
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from lichess_api import launch_game, is_game_active
from read_board import init_board_control, lcd_display_key, start_threads
from models import GameParams

def generate_random_string(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

SECRET_KEYS = ['fuck SFU', 'PEng shit', 'Shervin cool', 'Eat in a lab', 'NO ethics', 'lab=starbucks']

LICHESS_HOST = os.getenv("LICHESS_HOST", "https://lichess.org")
load_dotenv()

# Check if any arguments were passed
if len(sys.argv) > 1:
    debug = bool(int(sys.argv[1]))
else:
    debug = False
    
app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
app.config['LICHESS_CLIENT_ID'] =  os.getenv("LICHESS_CLIENT_ID")
app.config['LICHESS_AUTHORIZE_URL'] = f"{LICHESS_HOST}/oauth"
app.config['LICHESS_ACCESS_TOKEN_URL'] = f"{LICHESS_HOST}/api/token"
lcd_secret = None
debug = False
oauth = OAuth(app)
oauth.register('lichess', client_kwargs={"code_challenge_method": "S256"})

def handle_game_start(request):
    #global game_in_progress
    
    params = GameParams()
    params.side = request.form['color']
    params.time = int(request.form['time_limit']) * 60 # time in seconds
    params.time_inc = int(request.form['time_increment'])
    params.level = int(request.form['difficulty'])
    
    user_api_token = session.get('lichess_token')
    if user_api_token:
        # Initialize all board modules
        init_board_control(debug)
        # Launch lichess game via API
        launch_game(params, user_api_token)
        # Launch the board threads 
        start_threads(params.time, params.level)
        return redirect(url_for('index'))
    else:
        response = jsonify({'error': 'The lichess API token is missing'})
        response.status_code = 401
        return response
         
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        redirect_uri = url_for("authorize", _external=True)
        scopes = ("preference:read preference:write email:read challenge:read"
            " challenge:write tournament:write board:play bot:play team:write puzzle:read msg:write" 
            " study:write study:read")
        return oauth.lichess.authorize_redirect(redirect_uri, scope=scopes)
    return render_template('login.html') 

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    error = None
    if request.method == 'POST':
        entered_string = request.form['auth_string']
        if entered_string == lcd_secret:
            session['led_token'] = lcd_secret
            return redirect(url_for('index'))
        else:
            error = "Incorrect string. Please try again."
    return render_template('auth.html', error=error)

@app.route('/', methods=['GET', 'POST'])
def index():
    global lcd_secret
        
    if 'led_token' not in session and not is_game_active():
        #lcd_secret = generate_random_string()
        lcd_secret = SECRET_KEYS[random.randint(0,len(SECRET_KEYS)-1)]
        print(lcd_secret)
        lcd_display_key(lcd_secret)
        return redirect(url_for('auth'))
    if 'lichess_token' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if is_game_active():
            return jsonify({'error': 'The game has started already'})
        handle_game_start(request)

    colors = ['white', 'black']
    difficulties = list(range(1, 9))

    return render_template('index.html', colors=colors, difficulties=difficulties)

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('lichess_token', None)
    return redirect(url_for('login'))

@app.route('/authorize')
def authorize():
    token = oauth.lichess.authorize_access_token()
    session['lichess_token'] = token['access_token']
    return redirect(url_for('index'))

if __name__ == '__main__':

    app.run(host='0.0.0.0', port = 80)
