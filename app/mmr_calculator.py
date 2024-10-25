# app/mmr_calculator.py

"""
Components:
- League Points (LP)
- KDA (Kills/Deaths/Assists)
- Gold Earned Per Minute
- Damage Dealt Per Minute
- Win Percentage
"""

import requests
from flask import current_app
from typing import List, Dict
import concurrent.futures

class MMRCalculator:
    def __init__(self, riot_api_key: str, num_of_matches: int = 20):
        self.api_key = riot_api_key
        self.num_of_matches = num_of_matches
        self.base_url = "https://americas.api.riotgames.com"
        self.match_endpoint = "/lol/match/v5/matches/by-puuid/{puuid}/ids"
        self.detail_endpoint = "/lol/match/v5/matches/{matchId}"

    def fetch_match_ids(self, puuid: str, queue: int = 420, type_: str = "ranked") -> List[str]:
        """
        Fetch recent match IDs for a player based on PUUID.

        Args:
            puuid (str): Player's unique identifier.
            queue (int, optional): Queue ID filter (default is 420 for Ranked Solo/Duo).
            type_ (str, optional): Type of match (default is "ranked").

        Returns:
            List[str]: List of match IDs.
        """
        endpoint = self.match_endpoint.format(puuid=puuid)
        params = {
            "start": 0,
            "count": self.num_of_matches,
            "queue": queue,
            "type": type_
        }
        url = self.base_url + endpoint
        headers = {"X-Riot-Token": self.api_key}

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            # Handle errors or rate limiting
            response.raise_for_status()

    def fetch_match_details(self, match_id: str) -> Dict:
        """
        Fetch detailed match data for a given match ID.

        Args:
            match_id (str): The ID of the match.

        Returns:
            Dict: Match details.
        """
        endpoint = self.detail_endpoint.format(matchId=match_id)
        url = self.base_url + endpoint
        headers = {"X-Riot-Token": self.api_key}

        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            # Handle errors or rate limiting
            response.raise_for_status()

    def calculate_mmr(self, summoner_data: Dict) -> int:
        """
        Calculate MMR based on summoner's performance metrics.

        Args:
            summoner_data (Dict): Summoner's data including PUUID and other details.

        Returns:
            int: Calculated MMR.
        """
        puuid = summoner_data.get('puuid')
        if not puuid:
            return 0  # Unable to calculate MMR without PUUID

        try:
            match_ids = self.fetch_match_ids(puuid)
        except Exception as e:
            print(f"Error fetching match IDs: {e}")
            return summoner_data.get('mmr', 0)  # Fallback to existing MMR

        if not match_ids:
            return summoner_data.get('mmr', 0)  # Fallback to existing MMR

        total_kills = 0
        total_deaths = 0
        total_assists = 0
        total_gold = 0
        total_damage = 0
        total_wins = 0
        matches_played = 0

        # Define a helper function for fetching and processing a single match
        def process_match(match_id):
            """
            Process a single match to extract performance metrics.
            
            Args:
                match_id (str): Match ID to process.
                
            Returns:
                Dict: Performance metrics for the match.
            """
            try:
                match_details = self.fetch_match_details(match_id)
                participant_identity = next(
                    (p for p in match_details.get('info', {}).get('participants', []) if p.get('puuid') == puuid),
                    None
                )

                if participant_identity:
                    kills = participant_identity.get('kills', 0)
                    deaths = participant_identity.get('deaths', 0) or 1  # Avoid division by zero
                    assists = participant_identity.get('assists', 0)
                    gold_earned = participant_identity.get('goldEarned', 0)
                    damage_dealt = participant_identity.get('totalDamageDealtToChampions', 0)
                    time_played = participant_identity.get('timePlayed', 1)  # Avoid division by zero
                    win = participant_identity.get('win', False)

                    return {
                        'kills': kills,
                        'deaths': deaths,
                        'assists': assists,
                        'gold_earned_per_min': (gold_earned / time_played) * 60,
                        'damage_dealt_per_min': (damage_dealt / time_played) * 60,
                        'win': win
                    }
            except Exception as e:
                print(f"Error processing match {match_id}: {e}")
                return None

        # Use ThreadPoolExecutor to fetch match details in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all match processing tasks
            future_to_match = {executor.submit(process_match, match_id): match_id for match_id in match_ids}
            
            for future in concurrent.futures.as_completed(future_to_match):
                match_id = future_to_match[future]
                try:
                    result = future.result()
                    if result:
                        total_kills += result['kills']
                        total_deaths += result['deaths']
                        total_assists += result['assists']
                        total_gold += result['gold_earned_per_min']
                        total_damage += result['damage_dealt_per_min']
                        total_wins += int(result['win'])
                        matches_played += 1
                except Exception as e:
                    print(f"Error retrieving result for match {match_id}: {e}")
                    continue  # Skip this match and continue with others

        if matches_played == 0:
            return summoner_data.get('mmr', 0)  # Fallback if no matches processed

        # Calculate averages and ratios
        kd_ratio = total_kills / total_deaths
        ad_ratio = total_assists / total_deaths
        gold_per_min = total_gold / matches_played
        damage_per_min = total_damage / matches_played
        win_percentage = (total_wins / matches_played) * 100

        # Apply weights
        mmr = (
            (summoner_data.get('league_points', 0)) * 1 +
            (kd_ratio * 98) +
            (ad_ratio * 23) +
            (gold_per_min * 50) +
            (damage_per_min * 20) +
            (win_percentage * 300)
        )

        return int(mmr)