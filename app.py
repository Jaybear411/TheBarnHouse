# app.py
import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask import session
from flask import jsonify

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///poker_game.db')
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith("postgres://"):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace("postgres://", "postgresql://", 1)
    
    db.init_app(app)

    class Player(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        name = db.Column(db.String(100), nullable=False)
        balance = db.Column(db.Float, default=0)
        games_played = db.Column(db.Integer, default=0)

    app.secret_key = os.environ.get('SECRET_KEY', 'your_secret_key_here')

    with app.app_context():
        db.create_all()

    @app.route('/')
    def home():
        return render_template('home.html')

    @app.route('/manage_players')
    def manage_players():
        players = Player.query.all()
        return render_template('manage_players.html', players=players)

    @app.route('/update_player/<int:player_id>', methods=['GET', 'POST'])
    def update_player(player_id):
        player = Player.query.get_or_404(player_id)
        if request.method == 'POST':
            change = float(request.form['change'])
            player.balance += change
            player.games_played += 1
            db.session.commit()
            return redirect(url_for('manage_players'))
        return render_template('update_player.html', player=player)

    @app.route('/add_player', methods=['GET', 'POST'])
    def add_player():
        if request.method == 'POST':
            name = request.form['name']
            buy_in = float(request.form['buy_in'])
            new_player = Player(name=name, balance=-buy_in)
            db.session.add(new_player)
            db.session.commit()
            return redirect(url_for('manage_players'))
        return render_template('add_player.html')

    @app.route('/setup_game/<int:game_number>')
    def setup_game(game_number):
        if f'game_{game_number}_players' not in session:
            session[f'game_{game_number}_players'] = [None] * 9
        players = session[f'game_{game_number}_players']
        
        # Add balance information to players
        for i, player in enumerate(players):
            if player:
                db_player = Player.query.get(player['id'])
                if db_player:
                    player['balance'] = db_player.balance
                    players[i] = player
        
        session[f'game_{game_number}_players'] = players
        return render_template('setup_game.html', game_number=game_number, players=players)

    @app.route('/add_player/<int:game_number>/<int:slot>', methods=['GET', 'POST'])
    def add_player_to_game(game_number, slot):
        if request.method == 'POST':
            name = request.form['name']
            try:
                buy_in = float(request.form['buy_in'])
            except ValueError:
                return "Invalid buy-in amount", 400

            new_player = Player(name=name, balance=-buy_in)
            db.session.add(new_player)
            db.session.commit()

            players = session.get(f'game_{game_number}_players', [None] * 9)
            players[slot] = {'id': new_player.id, 'name': name, 'buy_in': buy_in, 'balance': -buy_in}
            session[f'game_{game_number}_players'] = players
            return redirect(url_for('setup_game', game_number=game_number))
        return render_template('add_player.html', game_number=game_number, slot=slot)

    @app.route('/clear_game/<int:game_number>')
    def clear_game(game_number):
        if f'game_{game_number}_players' in session:
            del session[f'game_{game_number}_players']
        return redirect(url_for('home'))

    @app.route('/update_player_in_game/<int:game_number>/<int:slot>', methods=['POST'])
    def update_player_in_game(game_number, slot):
        players = session.get(f'game_{game_number}_players', [None] * 9)
        player = players[slot]
        if player:
            change = float(request.form['change'])
            player['balance'] = player.get('balance', 0) + change
            players[slot] = player
            session[f'game_{game_number}_players'] = players
            
            # Update the player in the database
            db_player = Player.query.get(player['id'])
            if db_player:
                db_player.balance += change
                db_player.games_played += 1
                db.session.commit()
            
            return jsonify({'success': True, 'new_balance': player['balance']})
        return jsonify({'success': False, 'error': 'Player not found'}), 404

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=False)