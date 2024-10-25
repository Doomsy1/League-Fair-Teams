# app/routes.py

from flask import Blueprint, render_template, request, jsonify, current_app
import urllib.parse
import requests
from .mmr_calculator import MMRCalculator  # Import the new MMRCalculator module

routes = Blueprint('routes', __name__)

def calculate_base_mmr(tier, division, league_points, summoner_level):
    """
    Calculate the base MMR based on the tier, division, league points, and summoner level.
    
    Args:
        tier (str): The tier of the summoner.
        division (str): The division of the summoner.
        league_points (int): The league points of the summoner.
        summoner_level (int): The level of the summoner.
        
    Returns:
        int: The calculated base MMR.
    """
    tiers = ['Iron', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Master', 'Grandmaster', 'Challenger']
    divisions = {'IV': 0, 'III': 1, 'II': 2, 'I': 3}
    mmr = 0
    if tier in tiers:
        tier_index = tiers.index(tier)
        if tier in ['Master', 'Grandmaster', 'Challenger']:
            base_lps = {'Master': 2400, 'Grandmaster': 2800, 'Challenger': 3200}
            mmr = base_lps.get(tier, 0) + league_points
        else:
            base_lp = tier_index * 400
            division_offset = divisions.get(division, 0) * 100
            mmr = base_lp + division_offset + league_points
    else:
        mmr = summoner_level or 0
    return mmr

@routes.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@routes.route('/get_summoner_data', methods=['POST'])
def get_summoner_data():
    """
    Get summoner data from the Riot API and calculate MMR.
    
    Request JSON data format:
    {
        "game_name": "summoner_name",
        "tag_line": "tag_line",
        "num_of_matches": 20
    }
    
    Response JSON data format:
    {
        "status": "success" or "error",
        "summoner": {
            "game_name": "summoner_name",
            "tag_line": "tag_line",
            "puuid": "puuid",
            "accountId": "accountId",
            "summoner_id": "summoner_id",
            "icon_url": "icon_url",
            "level": 30,
            "rank": "Gold IV (75 LP)",
            "tier": "Gold",
            "division": "IV",
            "league_points": 75,
            "wins": 100,
            "losses": 80,
            "win_rate": 56,
            "mmr": 2300
        }
    }
    """
    data = request.get_json()
    user_game_name = data.get('game_name')
    user_tag_line = data.get('tag_line')
    num_of_matches = data.get('num_of_matches', 20)  # Default to 20 matches if not specified

    if not user_game_name or not user_tag_line:
        return jsonify({'status': 'error', 'message': 'Both Game Name and Tag Line are required.'}), 400

    try:
        RIOT_API_KEY = current_app.config['RIOT_API_KEY']
        encoded_game_name = urllib.parse.quote(user_game_name)
        encoded_tag_line = urllib.parse.quote(user_tag_line)
        riot_api_url = f"https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{encoded_game_name}/{encoded_tag_line}?api_key={RIOT_API_KEY}"
        response = requests.get(riot_api_url)
        
        if response.status_code == 200:
            account_data = response.json()
            puuid = account_data['puuid']
            
            # Extract the correctly cased gameName and tagLine from Riot API response
            correct_game_name = account_data.get('gameName', user_game_name)
            correct_tag_line = account_data.get('tagLine', user_tag_line)

            # Now use the puuid to get additional summoner data
            encrypted_puuid = urllib.parse.quote(puuid)
            summoner_api_url = f"https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{encrypted_puuid}?api_key={RIOT_API_KEY}"
            summoner_response = requests.get(summoner_api_url)
            
            if summoner_response.status_code == 200:
                summoner_data = summoner_response.json()
                accountId = summoner_data['accountId']
                summoner_id = summoner_data['id']
                profile_icon_id = summoner_data['profileIconId']
                summoner_level = summoner_data['summonerLevel']

                # Fetch rank data
                encrypted_summoner_id = urllib.parse.quote(summoner_id)
                league_api_url = f"https://na1.api.riotgames.com/lol/league/v4/entries/by-summoner/{encrypted_summoner_id}?api_key={RIOT_API_KEY}"
                league_response = requests.get(league_api_url)
                
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
                    else:
                        tier = 'Unranked'
                        rank = 'Unranked'
                        division = None
                        league_points = 0
                        wins = 0
                        losses = 0
                        win_rate = 0
                else:
                    tier = 'Unranked'
                    rank = 'Unranked'
                    division = None
                    league_points = 0
                    wins = 0
                    losses = 0
                    win_rate = 0

                # Calculate base MMR
                base_mmr = calculate_base_mmr(tier, division, league_points, summoner_level)

                # Get latest version for icon URL
                version_response = requests.get('https://ddragon.leagueoflegends.com/api/versions.json')
                if version_response.status_code == 200:
                    versions = version_response.json()
                    latest_version = versions[0]
                else:
                    latest_version = '13.9.1'  # Fallback version

                icon_url = f"https://ddragon.leagueoflegends.com/cdn/{latest_version}/img/profileicon/{profile_icon_id}.png"

                # Initialize MMR Calculator
                mmr_calculator = MMRCalculator(RIOT_API_KEY, num_of_matches)
                calculated_mmr = mmr_calculator.calculate_mmr({
                    'puuid': puuid,
                    'league_points': league_points,
                    'tier': tier,
                    'division': division,
                    'summoner_level': summoner_level,
                    'mmr': base_mmr
                })

                # Return summoner data with updated MMR and corrected gameName and tagLine
                return jsonify({
                    'status': 'success',
                    'summoner': {
                        'game_name': correct_game_name,    # Use correctly cased gameName from Riot API
                        'tag_line': correct_tag_line,      # Use correctly cased tagLine from Riot API
                        'puuid': puuid,
                        'accountId': accountId,
                        'summoner_id': summoner_id,
                        'icon_url': icon_url,
                        'level': summoner_level,
                        'rank': rank,
                        'tier': tier,
                        'division': division,
                        'league_points': league_points,
                        'wins': wins,
                        'losses': losses,
                        'win_rate': win_rate,
                        'mmr': calculated_mmr  # Updated MMR in the response
                    }
                }), 200
            else:
                return jsonify({'status': 'error', 'message': 'Failed to retrieve summoner information using PUUID.'}), 500
        elif response.status_code == 404:
            return jsonify({'status': 'error', 'message': 'Summoner not found. Please check the Game Name and Tag Line.'}), 404
        elif response.status_code == 403:
            return jsonify({'status': 'error', 'message': 'Invalid API key. Please check the RIOT_API_KEY in your .env file.'}), 403
        elif response.status_code == 429:
            return jsonify({'status': 'error', 'message': 'Rate limit exceeded. Please try again later.'}), 429
        else:
            return jsonify({'status': 'error', 'message': 'Failed to retrieve summoner information from Riot API.'}), 500
    except Exception as e:
        print(f"Error in /get_summoner_data: {e}")
        return jsonify({'status': 'error', 'message': 'An error occurred while contacting the Riot API.'}), 500
