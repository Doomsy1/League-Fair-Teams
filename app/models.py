# app/models.py

from . import db

class Summoner(db.Model):
    __tablename__ = 'summoner'  # Explicitly define table name

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    game_name = db.Column(db.String(100), nullable=False)
    tag_line = db.Column(db.String(100), nullable=False)
    puuid = db.Column(db.String(100), unique=True, nullable=False)
    team = db.Column(db.String(10), nullable=False)
    icon_url = db.Column(db.String(200), nullable=False)
    level = db.Column(db.Integer, nullable=False, default=1)
    mmr = db.Column(db.Integer, nullable=False, default=100)  # Added MMR field
    rank = db.Column(db.String(50), nullable=False, default='Silver IV')  # Added Rank field

    def __repr__(self):
        return f"<Summoner {self.name}>"
