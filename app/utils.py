# app/utils.py

import requests
import os
from flask import current_app
from . import db
from .models import Summoner
import logging

def get_latest_ddragon_version():
    versions_url = 'https://ddragon.leagueoflegends.com/api/versions.json'
    try:
        response = requests.get(versions_url)
        if response.status_code == 200:
            versions = response.json()
            latest_version = versions[0]
            return latest_version
        else:
            logging.error(f"Failed to fetch DDragon versions: {response.status_code}")
            return '13.6.1'  # Fallback to a default version
    except Exception as e:
        logging.error(f"Exception occurred while fetching DDragon versions: {e}")
        return '13.6.1'

def download_profile_icon(icon_id):
    latest_version = get_latest_ddragon_version()
    icon_url = f'https://ddragon.leagueoflegends.com/cdn/{latest_version}/img/profileicon/{icon_id}.png'
    local_path = os.path.join('app', 'static', 'profile_icons', f'{icon_id}.png')

    if not os.path.exists(os.path.dirname(local_path)):
        os.makedirs(os.path.dirname(local_path))

    if not os.path.isfile(local_path):
        try:
            response = requests.get(icon_url)
            if response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                logging.debug(f"Downloaded profile icon {icon_id}.png")
            else:
                logging.error(f"Failed to download profile icon {icon_id}: {response.status_code}")
        except Exception as e:
            logging.error(f"Exception occurred while downloading profile icon {icon_id}: {e}")

    return url_for('static', filename=f'profile_icons/{icon_id}.png')

def fetch_puuid(game_name, tag_line):
    api_key = os.getenv('RIOT_API_KEY')
    if not api_key:
        logging.error("RIOT_API_KEY not set in environment variables.")
        return None

    account_url = f'https://americas.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}'
    headers = {"X-Riot-Token": api_key}

    try:
        response = requests.get(account_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return data.get('puuid')
        else:
            logging.error(f"Failed to fetch PUUID for {game_name}#{tag_line}: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Exception occurred while fetching PUUID: {e}")
        return None

def fetch_summoner_details(puuid):
    api_key = os.getenv('RIOT_API_KEY')
    if not api_key:
        logging.error("RIOT_API_KEY not set in environment variables.")
        return None

    summoner_url = f'https://na1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}'
    headers = {"X-Riot-Token": api_key}

    try:
        response = requests.get(summoner_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return {
                'id': data.get('id'),
                'accountId': data.get('accountId'),
                'puuid': data.get('puuid'),
                'profileIconId': data.get('profileIconId'),
                'revisionDate': data.get('revisionDate'),
                'summonerLevel': data.get('summonerLevel')
            }
        else:
            logging.error(f"Failed to fetch summoner details for PUUID {puuid}: {response.status_code}")
            return None
    except Exception as e:
        logging.error(f"Exception occurred while fetching summoner details: {e}")
        return None

def get_summoner_mmr(summoner_name):
    # Placeholder function to calculate MMR
    # For now, return 100
    return 100

def get_summoner_rank(summoner_name):
    # Placeholder function to get rank
    # For now, return 'Silver IV'
    return 'Silver IV'
