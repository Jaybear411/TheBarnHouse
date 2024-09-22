# app.py
import os
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

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
            new_player = Player(name=name)
            db.session.add(new_player)
            db.session.commit()
            return redirect(url_for('manage_players'))
        return render_template('add_player.html')

    with app.app_context():
        db.create_all()

    return app

# This is used by Gunicorn
app = create_app()

if __name__ == '__main__':
    app = create_app()
    app.run(debug=False)
