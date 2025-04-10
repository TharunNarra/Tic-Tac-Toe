from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import random
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key = '8gdQTbFaIK'  # Change this to a secure secret key

# Database configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'Tharun@2003',
    'database': 'game_db'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

def check_winner(board):
    # Check rows
    for i in range(0, 9, 3):
        if board[i] == board[i+1] == board[i+2] != ' ':
            return board[i]
    
    # Check columns
    for i in range(3):
        if board[i] == board[i+3] == board[i+6] != ' ':
            return board[i]
    
    # Check diagonals
    if board[0] == board[4] == board[8] != ' ':
        return board[0]
    if board[2] == board[4] == board[6] != ' ':
        return board[2]
    
    # Check for tie
    if ' ' not in board:
        return 'Tie'
    
    return None

def make_ai_move(board):
    """Simple random AI move"""
    empty_spots = [i for i, spot in enumerate(board) if spot == ' ']
    return random.choice(empty_spots)

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!')
            return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('Username and password are required!')
            return redirect(url_for('register'))
        
        hashed_password = generate_password_hash(password)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', 
                         (username, hashed_password))
            conn.commit()
            
            # Log the user in immediately after registration
            cursor.execute('SELECT id FROM users WHERE username = %s', (username,))
            user_id = cursor.fetchone()[0]
            session['user_id'] = user_id
            session['username'] = username
            
            flash('Registration successful!')
            return redirect(url_for('dashboard'))
        except mysql.connector.Error as err:
            if err.errno == 1062:  # Duplicate entry
                flash('Username already exists!')
            else:
                flash('An error occurred during registration.')
            return redirect(url_for('register'))
        finally:
            cursor.close()
            conn.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('You have been logged out.')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get user's scores
        cursor.execute('''
            SELECT game_type, score, DATE_FORMAT(played_at, '%Y-%m-%d %H:%i') as date 
            FROM scores 
            WHERE user_id = %s 
            ORDER BY played_at DESC 
            LIMIT 10
        ''', (session['user_id'],))
        scores = cursor.fetchall()
        
        return render_template('dashboard.html', 
                             username=session['username'], 
                             scores=scores)
    except Exception as e:
        flash('Error loading dashboard')
        return redirect(url_for('home'))
    finally:
        cursor.close()
        conn.close()

@app.route('/tictactoe')
def tictactoe_home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get user's active games
        cursor.execute('''
            SELECT g.id, g.status, g.is_singleplayer,
                   u1.username as player_x_name, 
                   u2.username as player_o_name,
                   g.current_player
            FROM tictactoe_games g
            LEFT JOIN users u1 ON g.player_x = u1.id
            LEFT JOIN users u2 ON g.player_o = u2.id
            WHERE (g.player_x = %s OR g.player_o = %s) 
            AND g.status IN ('waiting', 'in_progress')
        ''', (session['user_id'], session['user_id']))
        active_games = cursor.fetchall()
        
        # Get available games to join
        cursor.execute('''
            SELECT g.id, u.username as player_x_name
            FROM tictactoe_games g
            JOIN users u ON g.player_x = u.id
            WHERE g.player_o IS NULL 
            AND g.status = 'waiting'
            AND g.player_x != %s
            AND g.is_singleplayer = FALSE
        ''', (session['user_id'],))
        available_games = cursor.fetchall()
        
        # Get completed games (MySQL version)
        cursor.execute('''
            SELECT g.id, 
                   u1.username as player_x_name, 
                   u2.username as player_o_name,
                   u3.username as winner_name,
                   DATE_FORMAT(g.updated_at, '%%Y-%%m-%%d %%H:%%i') as date,
                   g.is_singleplayer
            FROM tictactoe_games g
            LEFT JOIN users u1 ON g.player_x = u1.id
            LEFT JOIN users u2 ON g.player_o = u2.id
            LEFT JOIN users u3 ON g.winner = u3.id
            WHERE (g.player_x = %s OR g.player_o = %s) 
            AND g.status = 'completed'
            ORDER BY g.updated_at DESC
            LIMIT 10
        ''', (session['user_id'], session['user_id']))
        completed_games = cursor.fetchall()
        
        return render_template('tictactoe_home.html', 
                             active_games=active_games,
                             available_games=available_games,
                             completed_games=completed_games)
    except Exception as e:
        flash(f'Error loading games: {str(e)}')  # Show actual error
        app.logger.error(f"Error in tictactoe_home: {str(e)}")  # Log to console
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        conn.close()

@app.route('/tictactoe/new', methods=['POST'])
def tictactoe_new():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    is_singleplayer = request.form.get('singleplayer') == 'true'
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if is_singleplayer:
            # Create singleplayer game
            cursor.execute('''
                INSERT INTO tictactoe_games 
                (player_x, status, is_singleplayer)
                VALUES (%s, 'in_progress', TRUE)
            ''', (session['user_id'],))
            game_id = cursor.lastrowid
            conn.commit()
            flash('New singleplayer game started!')
            return redirect(url_for('tictactoe_play', game_id=game_id))
        else:
            # Create multiplayer game
            cursor.execute('''
                INSERT INTO tictactoe_games 
                (player_x, status, is_singleplayer)
                VALUES (%s, 'waiting', FALSE)
            ''', (session['user_id'],))
            game_id = cursor.lastrowid
            conn.commit()
            flash('Multiplayer game created! Waiting for opponent...')
            return redirect(url_for('tictactoe_home'))
    except Exception as e:
        conn.rollback()
        flash('Error creating game')
        return redirect(url_for('tictactoe_home'))
    finally:
        cursor.close()
        conn.close()

@app.route('/tictactoe/join/<int:game_id>', methods=['POST'])
def tictactoe_join(game_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Verify game is available to join
        cursor.execute('''
            SELECT * FROM tictactoe_games 
            WHERE id = %s 
            AND player_o IS NULL 
            AND status = 'waiting'
            AND is_singleplayer = FALSE
            AND player_x != %s
        ''', (game_id, session['user_id']))
        game = cursor.fetchone()
        
        if not game:
            flash('Game is no longer available')
            return redirect(url_for('tictactoe_home'))
        
        # Join the game
        cursor.execute('''
            UPDATE tictactoe_games 
            SET player_o = %s, 
                status = 'in_progress', 
                current_player = 'X'
            WHERE id = %s
        ''', (session['user_id'], game_id))
        conn.commit()
        
        flash('You have joined the game!')
        return redirect(url_for('tictactoe_play', game_id=game_id))
    except Exception as e:
        conn.rollback()
        flash('Error joining game')
        return redirect(url_for('tictactoe_home'))
    finally:
        cursor.close()
        conn.close()

@app.route('/tictactoe/play/<int:game_id>')
def tictactoe_play(game_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT g.*, 
                   u1.username as player_x_name, 
                   u2.username as player_o_name
            FROM tictactoe_games g
            LEFT JOIN users u1 ON g.player_x = u1.id
            LEFT JOIN users u2 ON g.player_o = u2.id
            WHERE g.id = %s 
            AND (g.player_x = %s OR g.player_o = %s)
        ''', (game_id, session['user_id'], session['user_id']))
        game = cursor.fetchone()
        
        if not game:
            flash('Game not found')
            return redirect(url_for('tictactoe_home'))
        
        player_symbol = 'X' if session['user_id'] == game['player_x'] else 'O'
        is_my_turn = (game['current_player'] == player_symbol and 
                      game['status'] == 'in_progress')
        
        return render_template('tictactoe_play.html', 
                             game=game,
                             player_symbol=player_symbol,
                             is_my_turn=is_my_turn)
    except Exception as e:
        flash('Error loading game')
        return redirect(url_for('tictactoe_home'))
    finally:
        cursor.close()
        conn.close()

@app.route('/tictactoe/move/<int:game_id>', methods=['POST'])
def tictactoe_move(game_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    position = int(request.form.get('position'))
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get game state with lock
        cursor.execute('''
            SELECT * FROM tictactoe_games 
            WHERE id = %s 
            AND status = 'in_progress'
            FOR UPDATE
        ''', (game_id,))
        game = cursor.fetchone()
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        # Verify it's the player's turn
        player_symbol = 'X' if session['user_id'] == game['player_x'] else 'O'
        if game['current_player'] != player_symbol:
            return jsonify({'error': 'Not your turn'}), 400
        
        # Verify move is valid
        board = list(game['board_state'])
        if position < 0 or position >= 9 or board[position] != ' ':
            return jsonify({'error': 'Invalid move'}), 400
        
        # Make the move
        board[position] = player_symbol
        new_board = ''.join(board)
        
        # Check for winner
        winner = check_winner(new_board)
        status = game['status']
        winner_id = None
        
        if winner:
            status = 'completed'
            if winner == 'X':
                winner_id = game['player_x']
            elif winner == 'O' and not game['is_singleplayer']:
                winner_id = game['player_o']
            
            # Record the win
            if winner_id:
                cursor.execute('''
                    INSERT INTO scores (user_id, score, game_type)
                    VALUES (%s, 1, 'tictactoe')
                ''', (winner_id,))
        
        # Handle computer move in singleplayer
        ai_move_made = False
        if game['is_singleplayer'] and not winner and ' ' in new_board:
            time.sleep(random.uniform(0.5, 1.5))  # Simulate thinking
            
            board = list(new_board)
            ai_position = make_ai_move(board)
            board[ai_position] = 'O'
            new_board = ''.join(board)
            ai_move_made = True
            
            # Check if computer won
            winner = check_winner(new_board)
            if winner == 'O':
                status = 'completed'
        
        # Update game state
        cursor.execute('''
            UPDATE tictactoe_games 
            SET board_state = %s,
                current_player = %s,
                status = %s,
                winner = %s,
                updated_at = NOW()
            WHERE id = %s
        ''', (
            new_board,
            'X' if (not winner and game['is_singleplayer']) else 'O' if player_symbol == 'X' else 'X',
            status,
            winner_id,
            game_id
        ))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'board': new_board,
            'game_over': bool(winner),
            'winner': winner,
            'is_my_turn': not ai_move_made and not bool(winner) and game['is_singleplayer']
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/tictactoe/state/<int:game_id>')
def tictactoe_state(game_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute('''
            SELECT * FROM tictactoe_games 
            WHERE id = %s 
            AND (player_x = %s OR player_o = %s)
        ''', (game_id, session['user_id'], session['user_id']))
        game = cursor.fetchone()
        
        if not game:
            return jsonify({'error': 'Game not found'}), 404
        
        player_symbol = 'X' if session['user_id'] == game['player_x'] else 'O'
        
        return jsonify({
            'board': game['board_state'],
            'current_player': game['current_player'],
            'status': game['status'],
            'is_my_turn': (game['current_player'] == player_symbol and 
                          game['status'] == 'in_progress'),
            'game_over': game['status'] == 'completed'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=True)
