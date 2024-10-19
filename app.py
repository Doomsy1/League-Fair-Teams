# app.py

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import urllib.parse
import requests
import time
import os

app = Flask(__name__)

# Load environment variables
load_dotenv()
RIOT_API_KEY = os.getenv('RIOT_API_KEY')

# Configuration for SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///summoners.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key_here'  # Replace with a secure key in production

db = SQLAlchemy(app)

# Cache configuration
CACHE_DURATION = 3600  # Cache duration in seconds (1 hour)

# In-memory cache dictionaries
summoner_cache = {}
version_cache = {'version': None, 'timestamp': 0}

# Summoner Model
class Summoner(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_name = db.Column(db.String(80), nullable=False)
    tag_line = db.Column(db.String(80), nullable=False)
    puuid = db.Column(db.String(128), nullable=False, unique=True)
    accountId = db.Column(db.String(56), nullable=False, unique=True)
    summoner_id = db.Column(db.String(63), nullable=False, unique=True)
    team = db.Column(db.String(10), nullable=False, default='team1')

    def __repr__(self):
        return f"<Summoner {self.game_name}#{self.tag_line}>"

# Initialize the database
with app.app_context():
    db.create_all()

def get_latest_version():
    current_time = time.time()
    if version_cache['version'] is None or (current_time - version_cache['timestamp']) > CACHE_DURATION:
        try:
            response = requests.get('https://ddragon.leagueoflegends.com/api/versions.json')
            if response.status_code == 200:
                versions = response.json()
                version_cache['version'] = versions[0]
                version_cache['timestamp'] = current_time
            else:
                version_cache['version'] = '13.9.1'  # Fallback version
        except Exception:
            version_cache['version'] = '13.9.1'  # Fallback version
    return version_cache['version']

def calculate_total_lp(tier, division, league_points):
    tiers = ['Iron', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster', 'Challenger']
    divisions = {'IV': 0, 'III': 1, 'II': 2, 'I': 3}
    if tier in tiers:
        tier_index = tiers.index(tier)
    else:
        tier_index = 0  # Default to Iron if tier not found
    if tier in ['Master', 'Grandmaster', 'Challenger']:
        base_lps = {'Master': 2400, 'Grandmaster': 2800, 'Challenger': 3200}
        base_lp = base_lps.get(tier, 0)
        total_lp = base_lp + league_points
    else:
        base_lp = tier_index * 400
        division_offset = divisions.get(division, 0) * 100
        total_lp = base_lp + division_offset + league_points
    return total_lp

def get_summoner_data(summoner):
    current_time = time.time()
    cached_data = summoner_cache.get(summoner.puuid)

    if cached_data and (current_time - cached_data['timestamp']) < CACHE_DURATION:
        return cached_data['data']

    # Fetch updatable data using Summoner ID
    encrypted_summoner_id = urllib.parse.quote(summoner.summoner_id)
    summoner_api_url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/{encrypted_summoner_id}?api_key={RIOT_API_KEY}"
    league_api_url = f"https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{encrypted_summoner_id}?api_key={RIOT_API_KEY}"

    try:
        summoner_response = requests.get(summoner_api_url)
        league_response = requests.get(league_api_url)

        if summoner_response.status_code == 200:
            summoner_data = summoner_response.json()
            profile_icon_id = summoner_data['profileIconId']
            summoner_level = summoner_data['summonerLevel']
            latest_version = get_latest_version()
            icon_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/img/profileicon/{profile_icon_id}.png"
        else:
            icon_url = 'https://via.placeholder.com/40'
            summoner_level = 'N/A'

        if league_response.status_code == 200:
            league_data = league_response.json()
            # Get ranked solo queue data
            rank_info = next((entry for entry in league_data if entry['queueType'] == 'RANKED_SOLO_5x5'), None)
            if rank_info:
                tier = rank_info['tier']
                division = rank_info['rank']
                league_points = rank_info['leaguePoints']
                wins = rank_info['wins']
                losses = rank_info['losses']
                total_games = wins + losses
                win_rate = round((wins / total_games) * 100) if total_games > 0 else 0
                rank = f"{tier} {division} ({league_points} LP)"
                mmr = calculate_total_lp(tier, division, league_points)
            else:
                rank = 'Unranked'
                tier = 'Unranked'
                division = None
                league_points = 0
                wins = 0
                losses = 0
                win_rate = 0
                mmr = int(summoner_level)
        else:
            rank = 'Unranked'
            tier = 'Unranked'
            division = None
            league_points = 0
            wins = 0
            losses = 0
            win_rate = 0
            mmr = int(summoner_level)

        data = {
            'icon_url': icon_url,
            'level': summoner_level,
            'rank': rank,
            'tier': tier,
            'division': division,
            'league_points': league_points,
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'mmr': mmr
        }

        # Update the cache
        summoner_cache[summoner.puuid] = {
            'data': data,
            'timestamp': current_time
        }

        return data

    except Exception as e:
        print(f"Error fetching summoner data: {e}")
        # Return placeholder data on error
        return {
            'icon_url': 'https://via.placeholder.com/40',
            'level': 'N/A',
            'rank': 'Unranked',
            'tier': 'Unranked',
            'division': None,
            'league_points': 0,
            'wins': 0,
            'losses': 0,
            'win_rate': 0,
            'mmr': 0
        }

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    summoners_data = []

    if request.method == 'POST':
        game_name = request.form.get('game_name')
        tag_line = request.form.get('tag_line')

        if not game_name or not tag_line:
            error = "Both Game Name and Tag Line are required."
        else:
            # Check if summoner already exists
            existing = Summoner.query.filter_by(game_name=game_name, tag_line=tag_line).first()
            if existing:
                error = "Summoner already exists."
            else:
                # Summoner does not exist, use Riot API to get puuid
                try:
                    encoded_game_name = urllib.parse.quote(game_name)
                    encoded_tag_line = urllib.parse.quote(tag_line)
                    riot_api_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{encoded_game_name}/{encoded_tag_line}?api_key={RIOT_API_KEY}"
                    response = requests.get(riot_api_url)
                    if response.status_code == 200:
                        data = response.json()
                        puuid = data['puuid']

                        # Now use the puuid to get additional summoner data
                        encrypted_puuid = urllib.parse.quote(puuid)
                        summoner_api_url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{encrypted_puuid}?api_key={RIOT_API_KEY}"
                        summoner_response = requests.get(summoner_api_url)
                        if summoner_response.status_code == 200:
                            summoner_data = summoner_response.json()
                            accountId = summoner_data['accountId']
                            summoner_id = summoner_data['id']
                            # Save the summoner to the database
                            new_summoner = Summoner(
                                game_name=game_name,
                                tag_line=tag_line,
                                puuid=puuid,
                                accountId=accountId,
                                summoner_id=summoner_id,
                                team='team1'  # Default team
                            )
                            db.session.add(new_summoner)
                            db.session.commit()
                        else:
                            error = "Failed to retrieve summoner information using PUUID."
                    elif response.status_code == 404:
                        error = "Summoner not found. Please check the Game Name and Tag Line."
                    elif response.status_code == 403:
                        error = "Invalid API key. Please check the RIOT_API_KEY in your .env file."
                    elif response.status_code == 429:
                        error = "Rate limit exceeded. Please try again later."
                    else:
                        error = "Failed to retrieve summoner information from Riot API."
                except Exception:
                    error = "An error occurred while contacting the Riot API."

        # Redirect to prevent form resubmission
        return redirect(url_for('index'))

    summoners = Summoner.query.all()

    # Prepare data for rendering
    for summoner in summoners:
        data = get_summoner_data(summoner)
        summoners_data.append({
            'game_name': summoner.game_name,
            'tag_line': summoner.tag_line,
            'puuid': summoner.puuid,
            'accountId': summoner.accountId,
            'summoner_id': summoner.summoner_id,
            'team': summoner.team,
            'icon_url': data['icon_url'],
            'level': data['level'],
            'rank': data['rank'],
            'tier': data['tier'],
            'division': data['division'],
            'league_points': data['league_points'],
            'wins': data['wins'],
            'losses': data['losses'],
            'win_rate': data['win_rate'],
            'mmr': data['mmr']
        })

    return render_template('index.html', summoners=summoners_data, error=error)

@app.route('/remove_summoner', methods=['POST'])
def remove_summoner():
    data = request.get_json()
    summoner_name = data.get('summoner_name')

    if not summoner_name:
        return jsonify({'status': 'error', 'message': 'No summoner name provided.'}), 400

    try:
        game_name, tag_line = summoner_name.split('#')
        summoner = Summoner.query.filter_by(game_name=game_name, tag_line=tag_line).first()
        if summoner:
            # Remove from cache
            summoner_cache.pop(summoner.puuid, None)
            db.session.delete(summoner)
            db.session.commit()
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Summoner not found.'}), 404
    except Exception:
        return jsonify({'status': 'error', 'message': 'Invalid summoner name format.'}), 400

@app.route('/update_team', methods=['POST'])
def update_team():
    data = request.get_json()
    summoner_name = data.get('summoner_name')
    new_team = data.get('new_team')

    if not summoner_name or not new_team:
        return jsonify({'status': 'error', 'message': 'Missing data.'}), 400

    try:
        game_name, tag_line = summoner_name.split('#')
        summoner = Summoner.query.filter_by(game_name=game_name, tag_line=tag_line).first()
        if summoner:
            summoner.team = new_team
            db.session.commit()
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Summoner not found.'}), 404
    except Exception:
        return jsonify({'status': 'error', 'message': 'Invalid data format.'}), 400

@app.route('/balance_teams', methods=['POST'])
def balance_teams():
    try:
        summoners = Summoner.query.all()
        # Fetch MMR (using 'mmr' from cached data)
        summoner_mmrs = []
        for summoner in summoners:
            data = get_summoner_data(summoner)
            mmr = data['mmr']
            summoner_mmrs.append((summoner, mmr))

        # Sort summoners by MMR descending
        summoner_mmrs.sort(key=lambda x: x[1], reverse=True)

        team1 = []
        team2 = []
        total_mmr_team1 = 0
        total_mmr_team2 = 0

        for summoner, mmr in summoner_mmrs:
            if total_mmr_team1 <= total_mmr_team2:
                summoner.team = 'team1'
                team1.append(summoner)
                total_mmr_team1 += mmr
            else:
                summoner.team = 'team2'
                team2.append(summoner)
                total_mmr_team2 += mmr

        db.session.commit()
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': 'Failed to balance teams.'}), 500

@app.route('/clear_players', methods=['POST'])
def clear_players():
    try:
        Summoner.query.delete()
        db.session.commit()
        # Clear caches
        summoner_cache.clear()
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        print(e)
        return jsonify({'status': 'error', 'message': 'Failed to clear players.'}), 500

if __name__ == '__main__':
    app.run(debug=True)
