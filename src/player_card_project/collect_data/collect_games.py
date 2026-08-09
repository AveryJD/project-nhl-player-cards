# ====================================================================================================
# FUNCTIONS FOR SCRAPING NHL SCHEDULE AND TEAM STANDINGS DATA
# ====================================================================================================

# Imports
import requests
import pandas as pd
import time
from player_card_project import constants
from player_card_project import data_io
from player_card_project.collect_data import collect_utils



def scrape_schedule(season: str) -> None:
    """
    Build a CSV of the season's game-level schedule from the NHL API.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: None
    """
    season_clean = season.replace('-', '')
    games_by_id = {}

    for team in constants.TEAM_NAMES:
        url = f'https://api-web.nhle.com/v1/club-schedule-season/{team}/{season_clean}'
        response = collect_utils.request_with_retry(url, timeout=30)

        games = response.json().get('games', [])
        for game in games:
            if game.get('gameType') != 2 or game.get('gameState') not in ('FINAL', 'OFF'):
                continue

            game_id = game['id']
            if game_id in games_by_id:
                continue

            games_by_id[game_id] = {
                'Game ID': game_id,
                'Date': game.get('gameDate'),
                'Home Team': game.get('homeTeam', {}).get('abbrev'),
                'Away Team': game.get('awayTeam', {}).get('abbrev'),
            }

        # Brief delay to avoid hammering the NHL API
        time.sleep(0.10)

    schedule_df = pd.DataFrame(games_by_id.values())
    schedule_df = schedule_df.sort_values('Game ID').reset_index(drop=True)

    # Save schedule CSV
    file_name = f'{season}_schedule.csv'
    data_io.save_csv(schedule_df, 'raw_data', 'schedule', file_name)


def scrape_team_standings(season: str) -> None:
    """
    Build a CSV of regular-season team standings from the NHL API.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: None
    """
    season_clean = season.replace('-', '')

    url = f"https://api.nhle.com/stats/rest/en/team/summary?isAggregate=false&isGame=false&start=0&limit=50&cayenneExp=seasonId={season_clean}%20and%20gameTypeId=2"

    response = collect_utils.request_with_retry(url, timeout=30)
    response.raise_for_status()
    teams = response.json().get('data', [])

    # Reverse lookup built from constants.TEAM_NAMES: normalized (alias-resolved)
    team_full_name_aliases = {
        'Utah Hockey Club': 'Utah Mammoth',
        'Montréal Canadiens': 'Montreal Canadiens',
    }

    normalized_team_names = {
        team_full_name_aliases.get(full_name, full_name): abbrev
        for abbrev, full_name in constants.TEAM_NAMES.items()
    }

    rows = []
    for t in teams:
        normalized = team_full_name_aliases.get(t['teamFullName'], t['teamFullName']).strip()
        if normalized not in normalized_team_names:
            raise ValueError(f"Unrecognized team full name from NHL API: '{t['teamFullName']}'")
        abbrev = normalized_team_names[normalized]

        rows.append({
            'Team': abbrev,
            'GP': t['gamesPlayed'],
            'Wins': t['wins'],
            'Losses': t['losses'],
            'OT Losses': t['otLosses'],
            'Points': t['points'],
            'Point Pct': t['pointPct'],
            'Goals For': t['goalsFor'],
            'Goals Against': t['goalsAgainst'],
            'Goal Diff': t['goalsFor'] - t['goalsAgainst'],
            'Reg+OT Wins': t['regulationAndOtWins'],
        })

    standings_df = pd.DataFrame(rows)
    standings_df = standings_df.sort_values('Team').reset_index(drop=True)

    # Save team standings CSV
    file_name = f'{season}_team_standings.csv'
    data_io.save_csv(standings_df, 'raw_data', 'team_standings', file_name)
