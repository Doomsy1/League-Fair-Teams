# app/routes.py

from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import requests
import os
from . import db
from .models import Summoner
from .utils import get_summoner_mmr, get_summoner_rank, fetch_puuid, fetch_summoner_details, download_profile_icon
import logging
from itertools import combinations

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        game_name = request.form.get('game_name')
        tag_line = request.form.get('tag_line')
        if game_name and tag_line:
            # Fetch puuid using game name and tag line
            puuid = fetch_puuid(game_name, tag_line)
            if not puuid:
                logger.debug(f"PUUID not found for {game_name}#{tag_line}.")
                return render_template('index.html', summoners=Summoner.query.all(), error="PUUID not found.")
            
            # Fetch summoner details using puuid
            summoner_details = fetch_summoner_details(puuid)
            if not summoner_details:
                logger.debug(f"Summoner details not found for PUUID {puuid}.")
                return render_template('index.html', summoners=Summoner.query.all(), error="Summoner details not found.")

            summoner_level = summoner_details.get('summonerLevel', 1)
            profile_icon_id = summoner_details.get('profileIconId', 0)
            # Download and get local icon URL
            icon_url = download_profile_icon(profile_icon_id)

            # Fetch MMR and Rank
            mmr = get_summoner_mmr(game_name)
            rank = get_summoner_rank(game_name)

            # Check if summoner already exists
            existing_summoner = Summoner.query.filter_by(puuid=puuid).first()
            if existing_summoner:
                logger.debug(f"Summoner '{game_name}#{tag_line}' already exists.")
            else:
                # Add new summoner to Team 1
                new_summoner = Summoner(
                    name=game_name,
                    game_name=game_name,
                    tag_line=tag_line,
                    puuid=puuid,
                    team='team1',
                    icon_url=icon_url,
                    level=summoner_level,
                    mmr=mmr,
                    rank=rank
                )
                db.session.add(new_summoner)
                db.session.commit()
                logger.debug(f"Added summoner '{game_name}#{tag_line}' to team1 with icon '{icon_url}', MMR {mmr}, Rank {rank}, Level {summoner_level}.")

            return redirect(url_for('main.index'))
    # Fetch all summoners from the database
    summoners = Summoner.query.all()
    return render_template('index.html', summoners=summoners)

@main.route('/remove_summoner', methods=['POST'])
def remove_summoner():
    data = request.get_json()
    summoner_name = data.get('summoner_name')
    logger.debug(f"Received request to remove summoner: {summoner_name}")
    summoner = Summoner.query.filter_by(name=summoner_name).first()
    if summoner:
        db.session.delete(summoner)
        db.session.commit()
        logger.debug(f"Removed summoner '{summoner_name}' from the database.")
        return jsonify({'status': 'success'})
    else:
        logger.debug(f"Summoner '{summoner_name}' not found.")
        return jsonify({'status': 'failure', 'message': 'Summoner not found'}), 404

@main.route('/update_team', methods=['POST'])
def update_team():
    data = request.get_json()
    summoner_name = data.get('summoner_name')
    new_team = data.get('new_team')
    logger.debug(f"Received request to update summoner '{summoner_name}' to team '{new_team}'.")

    summoner = Summoner.query.filter_by(name=summoner_name).first()
    if summoner:
        # Check if the new team already has 5 players
        team_count = Summoner.query.filter_by(team=new_team).count()
        if team_count >= 5:
            logger.debug(f"Cannot move summoner '{summoner_name}' to '{new_team}': Team is full.")
            return jsonify({'status': 'failure', 'message': f"Team '{new_team}' is already full."}), 400

        summoner.team = new_team
        db.session.commit()
        logger.debug(f"Updated summoner '{summoner_name}' to team '{new_team}'.")
        return jsonify({'status': 'success'})
    else:
        logger.debug(f"Summoner '{summoner_name}' not found for team update.")
        return jsonify({'status': 'failure', 'message': 'Summoner not found'}), 404

@main.route('/balance_teams', methods=['POST'])
def balance_teams():
    # Fetch all summoners
    summoners = Summoner.query.all()

    # Extract MMRs and IDs
    summoner_list = [(s.id, s.mmr) for s in summoners]

    # Number of summoners
    n = len(summoner_list)

    if n == 0:
        return jsonify({'status': 'failure', 'message': 'No summoners to balance.'})

    if n == 1:
        # Only one player, assign to team1
        summoners[0].team = 'team1'
        db.session.commit()
        logger.debug("Only one summoner present. Assigned to team1.")
        return jsonify({'status': 'success'})

    if n > 10:
        return jsonify({'status': 'failure', 'message': 'Too many summoners. Maximum allowed is 10.'})

    # Generate all possible ways to split n players into two teams with at most 5 players each
    possible_teams = []

    summoner_ids = [s.id for s in summoners]
    summoner_mmr_dict = {s.id: s.mmr for s in summoners}

    # Generate all combinations of summoner IDs for Team 1 of size 1 to min(5, n-1)
    for team1_size in range(1, min(6, n)):
        for team1_ids in combinations(summoner_ids, team1_size):
            team2_ids = [id for id in summoner_ids if id not in team1_ids]
            if len(team2_ids) > 5:
                continue  # Team 2 would have more than 5 players

            team1_mmr = sum(summoner_mmr_dict[id] for id in team1_ids)
            team2_mmr = sum(summoner_mmr_dict[id] for id in team2_ids)
            mmr_difference = abs(team1_mmr - team2_mmr)
            possible_teams.append((mmr_difference, team1_ids, team2_ids))

    # Find the team division with the minimal MMR difference
    if possible_teams:
        possible_teams.sort(key=lambda x: x[0])  # Sort by mmr_difference
        best_team = possible_teams[0]
        best_team1_ids = best_team[1]
        best_team2_ids = best_team[2]

        # Update the teams in the database
        for summoner in summoners:
            if summoner.id in best_team1_ids:
                summoner.team = 'team1'
            else:
                summoner.team = 'team2'
        db.session.commit()

        logger.debug("Teams have been balanced.")
        return jsonify({'status': 'success'})
    else:
        return jsonify({'status': 'failure', 'message': 'No possible team divisions found.'})
