# ====================================================================================================
# FUNCTIONS FOR TURNING RAW SHIFT CHARTS INTO TEAMMATE/COMPETITION TOI OVERLAP MATRICES
# ====================================================================================================

# Imports
import numpy as np
import pandas as pd
from collections import defaultdict

from player_card_project import constants
from player_card_project import data_io

DATA_DIR = constants.DATA_DIR


def time_to_seconds(time_str: str) -> int:
    """
    Convert a MM:SS clock string into total seconds.

    :param time_str: A str clock value in MM:SS format
    :return: The int total number of seconds
    """
    minutes, seconds = str(time_str).split(':')
    total_seconds = int(minutes) * 60 + int(seconds)
    return total_seconds


def goalie_id_set(season: str) -> set:
    """
    Get the set of Player IDs who are goalies for a season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: A set of int goalie Player IDs
    """
    ids_df = data_io.load_player_ids_csv(season)
    id_set = set(ids_df.loc[ids_df['Position'] == 'G', 'Player ID'])
    return id_set


def period_overlap_seconds(player_ids: np.ndarray, teams: np.ndarray, start_secs: np.ndarray, end_secs: np.ndarray, goalie_ids: set) -> dict:
    """
    Compute shared on-ice seconds between every pair of players in a (Game ID, Period) group, split by strength situation.

    :param player_ids: An array of int Player IDs, one per shift row
    :param teams: An array of str team abbreviations, one per shift row
    :param start_secs: An array of int shift start times in seconds, one per shift row
    :param end_secs: An array of int shift end times in seconds, one per shift row
    :param goalie_ids: A set of int Player IDs who are goalies, used to compute skater-only strength counts
    :return: A dict mapping (Player ID, Other Player ID, same_team, situation) to shared on-ice seconds
    """
    max_len = int(end_secs.max()) + 1
    unique_players = pd.unique(player_ids)
    player_idx = {pid: i for i, pid in enumerate(unique_players)}

    # First team seen for each player is used to classify teammate/opponent pairs
    team_of = {}
    for pid, team in zip(player_ids, teams):
        team_of.setdefault(pid, team)

    # Build a boolean on-ice timeline per player for this period
    timeline = np.zeros((len(unique_players), max_len), dtype=np.int16)
    for pid, start, end in zip(player_ids, start_secs, end_secs):
        timeline[player_idx[pid], start:end] = 1

    unique_teams = sorted(set(team_of.values()))

    # Per-team skater-only on-ice counts, used to derive each team's strength situation
    skater_counts = {}
    for team in unique_teams:
        skater_rows = [
            player_idx[pid] for pid in unique_players
            if team_of[pid] == team and pid not in goalie_ids
        ]
        if skater_rows:
            skater_counts[team] = timeline[skater_rows].sum(axis=0)
        else:
            skater_counts[team] = np.zeros(max_len, dtype=np.int16)

    # Strength state needs exactly two teams on ice; falls back to even strength otherwise
    code_to_situation = {0: 'ES', 1: 'PP', 2: 'PK'}

    if len(unique_teams) == 2:
        team_a, team_b = unique_teams
        diff = skater_counts[team_a].astype(np.int16) - skater_counts[team_b].astype(np.int16)
        # situation code from team_a's perspective: 0 = ES, 1 = PP (more skaters), 2 = PK (fewer)
        situation_a = np.where(diff > 0, 1, np.where(diff < 0, 2, 0))
        situation_by_team = {
            team_a: situation_a,
            team_b: np.where(situation_a == 1, 2, np.where(situation_a == 2, 1, 0)),
        }
    else:
        situation_by_team = {team: np.zeros(max_len, dtype=np.int16) for team in unique_teams}

    # Masked per-player timelines for each situation code (on-ice AND team in that situation)
    masked = {0: {}, 1: {}, 2: {}}
    for pid in unique_players:
        row = timeline[player_idx[pid]]
        situation_codes = situation_by_team[team_of[pid]]
        for code in (0, 1, 2):
            masked[code][pid] = row * (situation_codes == code)

    pair_seconds = {}
    n = len(unique_players)
    for i in range(n):
        for j in range(i + 1, n):
            pid_a, pid_b = unique_players[i], unique_players[j]
            same_team = team_of.get(pid_a) == team_of.get(pid_b)

            if same_team:
                for code, situation in code_to_situation.items():
                    shared = int(np.dot(masked[code][pid_a], masked[code][pid_b]))
                    if shared <= 0:
                        continue
                    pair_seconds[(pid_a, pid_b, True, situation)] = shared
                    pair_seconds[(pid_b, pid_a, True, situation)] = shared
            else:
                # ES seconds are symmetric: both teams are at equal strength simultaneously
                es_shared = int(np.dot(masked[0][pid_a], timeline[j]))
                if es_shared > 0:
                    pair_seconds[(pid_a, pid_b, False, 'ES')] = es_shared
                    pair_seconds[(pid_b, pid_a, False, 'ES')] = es_shared

                # Seconds pid_a's team is on the PP, facing pid_b (who is therefore on the PK)
                a_pp_shared = int(np.dot(masked[1][pid_a], timeline[j]))
                if a_pp_shared > 0:
                    pair_seconds[(pid_a, pid_b, False, 'PP')] = a_pp_shared
                    pair_seconds[(pid_b, pid_a, False, 'PK')] = a_pp_shared

                # Seconds pid_a's team is on the PK, facing pid_b (who is therefore on the PP)
                a_pk_shared = int(np.dot(masked[2][pid_a], timeline[j]))
                if a_pk_shared > 0:
                    pair_seconds[(pid_a, pid_b, False, 'PK')] = a_pk_shared
                    pair_seconds[(pid_b, pid_a, False, 'PP')] = a_pk_shared

    return pair_seconds


def compute_season_toi_matrices(season: str) -> tuple:
    """
    Compute season-long teammate/competition shared-TOI matrices, split by strength situation.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: A tuple of teammate and competition TOI DataFrames
    """
    shifts_df = data_io.load_shifts_csv(season).copy()

    # Drop shifts with a missing/malformed clock value before converting to seconds
    time_pattern = r'^\d{1,2}:\d{2}$'
    valid_time = (
        shifts_df['Start Time'].astype(str).str.match(time_pattern, na=False)
        & shifts_df['End Time'].astype(str).str.match(time_pattern, na=False)
    )

    shifts_df = shifts_df[valid_time]

    shifts_df['Start Sec'] = shifts_df['Start Time'].apply(time_to_seconds)
    shifts_df['End Sec'] = shifts_df['End Time'].apply(time_to_seconds)

    # Drop shifts where the clock didn't advance (bad/duplicate rows)
    shifts_df = shifts_df[shifts_df['End Sec'] > shifts_df['Start Sec']]

    id_to_name = shifts_df.drop_duplicates('Player ID').set_index('Player ID')['Player'].to_dict()

    goalie_ids = goalie_id_set(season)

    teammate_totals = defaultdict(int)
    competition_totals = defaultdict(int)

    for _, period_df in shifts_df.groupby(['Game ID', 'Period']):
        pair_seconds = period_overlap_seconds(
            period_df['Player ID'].to_numpy(),
            period_df['Team'].to_numpy(),
            period_df['Start Sec'].to_numpy(),
            period_df['End Sec'].to_numpy(),
            goalie_ids,
        )

        for (pid_a, pid_b, same_team, situation), seconds in pair_seconds.items():
            target = teammate_totals if same_team else competition_totals
            target[(pid_a, pid_b, situation)] += seconds

    columns = ['Player ID', 'Player', 'Other Player ID', 'Other Player', 'Shared TOI', 'Situation']

    teammate_records = []
    for (pid_a, pid_b, situation), seconds in teammate_totals.items():
        teammate_records.append({
            'Player ID': pid_a,
            'Player': id_to_name.get(pid_a),
            'Other Player ID': pid_b,
            'Other Player': id_to_name.get(pid_b),
            'Shared TOI': seconds,
            'Situation': situation,
        })

    competition_records = []
    for (pid_a, pid_b, situation), seconds in competition_totals.items():
        competition_records.append({
            'Player ID': pid_a,
            'Player': id_to_name.get(pid_a),
            'Other Player ID': pid_b,
            'Other Player': id_to_name.get(pid_b),
            'Shared TOI': seconds,
            'Situation': situation,
        })

    # Explicit columns so an empty dict still saves/loads as a valid CSV
    teammate_toi_df = pd.DataFrame(teammate_records, columns=columns)
    competition_toi_df = pd.DataFrame(competition_records, columns=columns)

    return teammate_toi_df, competition_toi_df


def make_and_save_toi_matrices(season: str) -> None:
    """
    Compute and save the teammate/competition TOI matrices for a season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: None
    """
    teammate_toi_df, competition_toi_df = compute_season_toi_matrices(season)

    data_io.save_csv(teammate_toi_df, 'processed_data', 'shift_toi', f'{season}_teammate_toi.csv')
    data_io.save_csv(competition_toi_df, 'processed_data', 'shift_toi', f'{season}_competition_toi.csv')
