# ====================================================================================================
# FUNCTIONS FOR SCRAPING PLAY-BY-PLAY, SHIFT, AND BOXSCORE STATS
# ====================================================================================================

# Imports
import requests
import pandas as pd
import os
import re
import unicodedata
from bs4 import BeautifulSoup
from player_card_project import constants
from player_card_project import data_io
from player_card_project.collect_data import collect_utils

DATA_DIR = constants.DATA_DIR


# ====================================================================================================
# FUNCTIONS FOR SCRAPING PLAY-BY-PLAY EVENTS (FACEOFFS, GOALS, SHOT/PENALTY/POSSESSION EVENTS)
# ====================================================================================================

def get_game_faceoffs(game_id: int, pbp_data: dict = None) -> pd.DataFrame:
    """
    Fetch every faceoff event for a game.

    :param game_id: The int NHL game ID to fetch faceoffs for
    :param pbp_data: An optional pre-fetched play-by-play payload (get_game_play_by_play)
    :return: A DataFrame of faceoff events
    """
    columns = ['Game ID', 'Period', 'Time', 'Team', 'Zone']

    data = pbp_data if pbp_data is not None else collect_utils.get_game_play_by_play(game_id)
    plays = data.get('plays', [])
    team_id_to_abbrev = collect_utils.team_id_to_abbrev_map(data)

    rows = []
    # Build one row per faceoff event
    for play in plays:
        if play.get('typeDescKey') != 'faceoff':
            continue

        details = play.get('details', {})
        period = play.get('periodDescriptor', {}).get('number')
        time_in_period = play.get('timeInPeriod')
        team_id = details.get('eventOwnerTeamId')
        team_abbrev = team_id_to_abbrev.get(team_id)
        zone = details.get('zoneCode')

        if period is None or time_in_period is None or team_abbrev is None:
            continue

        rows.append({
            'Game ID': game_id,
            'Period': period,
            'Time': time_in_period,
            'Team': team_abbrev,
            'Zone': zone,
        })

    faceoffs_df = pd.DataFrame(rows, columns=columns)
    return faceoffs_df


def get_game_goals(game_id: int, pbp_data: dict = None) -> pd.DataFrame:
    """
    Fetch goal events for a game.

    :param game_id: The int NHL game ID to fetch goals for
    :param pbp_data: An optional pre-fetched play-by-play payload (get_game_play_by_play)
    :return: A DataFrame of goal events
    """
    columns = ['Game ID', 'Period', 'Time', 'Team', 'Assist 1 Player ID', 'Assist 2 Player ID']

    data = pbp_data if pbp_data is not None else collect_utils.get_game_play_by_play(game_id)
    plays = data.get('plays', [])
    team_id_to_abbrev = collect_utils.team_id_to_abbrev_map(data)

    rows = []
    # Build one row per goal event
    for play in plays:
        if play.get('typeDescKey') != 'goal':
            continue

        # Exclude shootout goals
        if play.get('periodDescriptor', {}).get('periodType') == 'SO':
            continue

        details = play.get('details', {})
        period = play.get('periodDescriptor', {}).get('number')
        time_in_period = play.get('timeInPeriod')
        team_id = details.get('eventOwnerTeamId')
        team_abbrev = team_id_to_abbrev.get(team_id)

        if period is None or time_in_period is None or team_abbrev is None:
            continue

        rows.append({
            'Game ID': game_id,
            'Period': period,
            'Time': time_in_period,
            'Team': team_abbrev,
            'Assist 1 Player ID': details.get('assist1PlayerId'),
            'Assist 2 Player ID': details.get('assist2PlayerId'),
        })

    goals_df = pd.DataFrame(rows, columns=columns)
    return goals_df


def get_game_shot_events(game_id: int, pbp_data: dict = None) -> pd.DataFrame:
    """
    Fetch shot attempts for a game.

    :param game_id: The int NHL game ID to fetch shot events for
    :param pbp_data: An optional pre-fetched play-by-play payload (get_game_play_by_play)
    :return: A DataFrame of shot events
    """
    data = pbp_data if pbp_data is not None else collect_utils.get_game_play_by_play(game_id)
    plays = data.get('plays', [])
    plays = sorted(plays, key=lambda p: p.get('sortOrder', 0))
    team_id_to_abbrev = collect_utils.team_id_to_abbrev_map(data)

    rows = []
    # Tracks the most recent play (any type) so each shot can record what preceded it (rebound/rush context)
    prior_event = None 

    for play in plays:
        # Exclude shootout shots
        if play.get('periodDescriptor', {}).get('periodType') == 'SO':
            continue

        type_desc = play.get('typeDescKey')
        details = play.get('details', {})
        period = play.get('periodDescriptor', {}).get('number')
        time_in_period = play.get('timeInPeriod')
        team_id = details.get('eventOwnerTeamId')
        team_abbrev = team_id_to_abbrev.get(team_id)
        x = details.get('xCoord')
        y = details.get('yCoord')

        shot_event_types = ('goal', 'shot-on-goal', 'missed-shot', 'blocked-shot')

        shooter_field_by_type = {
            'goal': 'scoringPlayerId',
            'shot-on-goal': 'shootingPlayerId',
            'missed-shot': 'shootingPlayerId',
            'blocked-shot': 'shootingPlayerId',
        }

        if type_desc in shot_event_types:
            shooter_field = shooter_field_by_type[type_desc]
            shooter_id = details.get(shooter_field)
            goalie_id = details.get('goalieInNetId')
            shot_type = details.get('shotType')
            zone = details.get('zoneCode')

            if period is not None and time_in_period is not None and team_abbrev is not None:
                if prior_event is not None:
                    prior_type, prior_team, prior_period, prior_time, prior_x, prior_y = prior_event
                    # Only attach prior-event context from the same period
                    if prior_period != period:
                        prior_type = prior_team = prior_time = prior_x = prior_y = None
                else:
                    prior_type = prior_team = prior_time = prior_x = prior_y = None

                rows.append({
                    'Game ID': game_id,
                    'Period': period,
                    'Time': time_in_period,
                    'Team': team_abbrev,
                    'Event Type': type_desc,
                    'Shot Type': shot_type,
                    'Shooter Player ID': shooter_id,
                    'Goalie Player ID': goalie_id,
                    'X': x,
                    'Y': y,
                    'Zone': zone,
                    'Prior Event Type': prior_type,
                    'Prior Event Team': prior_team,
                    'Prior Event Time': prior_time,
                    'Prior Event X': prior_x,
                    'Prior Event Y': prior_y,
                })

        # Update prior-event tracking for the next shot, but only if this play has usable fields
        if type_desc is not None and period is not None and time_in_period is not None:
            prior_event = (type_desc, team_abbrev, period, time_in_period, x, y)

    shot_event_columns = [
        'Game ID', 'Period', 'Time', 'Team', 'Event Type', 'Shot Type', 'Shooter Player ID',
        'Goalie Player ID', 'X', 'Y', 'Zone', 'Prior Event Type', 'Prior Event Team',
        'Prior Event Time', 'Prior Event X', 'Prior Event Y',
    ]

    shot_events_df = pd.DataFrame(rows, columns=shot_event_columns)
    return shot_events_df


def get_game_penalty_events(game_id: int, pbp_data: dict = None) -> pd.DataFrame:
    """
    Fetch every penalty event for a game.

    :param game_id: The int NHL game ID to fetch penalty events for
    :param pbp_data: An optional pre-fetched play-by-play payload (get_game_play_by_play)
    :return: A DataFrame of penalty events
    """
    data = pbp_data if pbp_data is not None else collect_utils.get_game_play_by_play(game_id)
    plays = data.get('plays', [])
    plays = sorted(plays, key=lambda p: p.get('sortOrder', 0))
    team_id_to_abbrev = collect_utils.team_id_to_abbrev_map(data)

    rows = []
    # Build one row per penalty event
    for play in plays:
        if play.get('typeDescKey') != 'penalty':
            continue

        period = play.get('periodDescriptor', {}).get('number')
        time_in_period = play.get('timeInPeriod')
        details = play.get('details', {})
        duration = details.get('duration')

        if period is None or time_in_period is None or duration is None:
            continue

        team_id = details.get('eventOwnerTeamId')
        rows.append({
            'Game ID': game_id,
            'Period': period,
            'Time': time_in_period,
            'Team': team_id_to_abbrev.get(team_id),
            'Penalty Player ID': details.get('committedByPlayerId'),
            'Drew Player ID': details.get('drawnByPlayerId'),
            'Penalty Type': details.get('descKey'),
            'Duration': duration,
        })

    penalty_event_columns = [
        'Game ID', 'Period', 'Time', 'Team',
        'Penalty Player ID', 'Drew Player ID', 'Penalty Type', 'Duration',
    ]

    penalty_events_df = pd.DataFrame(rows, columns=penalty_event_columns)
    return penalty_events_df


def get_game_possession_events(game_id: int, pbp_data: dict = None) -> pd.DataFrame:
    """
    Fetch every hit/giveaway/takeaway event for a game.

    :param game_id: The int NHL game ID to fetch possession events for
    :param pbp_data: An optional pre-fetched play-by-play payload (get_game_play_by_play)
    :return: A DataFrame of possession events
    """
    data = pbp_data if pbp_data is not None else collect_utils.get_game_play_by_play(game_id)
    plays = data.get('plays', [])
    team_id_to_abbrev = collect_utils.team_id_to_abbrev_map(data)

    possession_event_types = ('hit', 'giveaway', 'takeaway')

    rows = []
    # Build one row per hit/giveaway/takeaway event
    for play in plays:
        event_type = play.get('typeDescKey')
        if event_type not in possession_event_types:
            continue

        period = play.get('periodDescriptor', {}).get('number')
        time_in_period = play.get('timeInPeriod')
        if period is None or time_in_period is None:
            continue

        details = play.get('details', {})
        team_id = details.get('eventOwnerTeamId')

        if event_type == 'hit':
            player_id = details.get('hittingPlayerId')
            hittee_id = details.get('hitteePlayerId')
        else:
            player_id = details.get('playerId')
            hittee_id = None

        if player_id is None:
            continue

        rows.append({
            'Game ID': game_id,
            'Period': period,
            'Time': time_in_period,
            'Team': team_id_to_abbrev.get(team_id),
            'Event Type': event_type,
            'Player ID': player_id,
            'Hittee Player ID': hittee_id,
        })

    possession_event_columns = [
        'Game ID', 'Period', 'Time', 'Team', 'Event Type', 'Player ID', 'Hittee Player ID',
    ]

    possession_events_df = pd.DataFrame(rows, columns=possession_event_columns)
    return possession_events_df


def get_game_play_by_play_outputs(game_id: int) -> tuple:
    """
    Fetch a game's play-by-play once and parse all five event types from it.

    :param game_id: The int NHL game ID to fetch play-by-play outputs for
    :return: A tuple of event DataFrames
    """
    pbp_data = collect_utils.get_game_play_by_play(game_id)
    outputs = (
        get_game_faceoffs(game_id, pbp_data),
        get_game_goals(game_id, pbp_data),
        get_game_shot_events(game_id, pbp_data),
        get_game_penalty_events(game_id, pbp_data),
        get_game_possession_events(game_id, pbp_data),
    )
    return outputs


def scrape_play_by_play(season: str) -> None:
    """
    Scrape faceoffs/goals/shot_events/penalty_events/possession_events together.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: None
    """
    collect_utils.scrape_generic(
        ids=collect_utils.get_season_game_ids(season),
        fetch_fn=get_game_play_by_play_outputs,
        outputs=[
            ('faceoffs', f'{season}_faceoffs.csv'),
            ('goals', f'{season}_goals.csv'),
            ('shot_events', f'{season}_shot_events.csv'),
            ('penalty_events', f'{season}_penalty_events.csv'),
            ('possession_events', f'{season}_possession_events.csv'),
        ],
        no_data_folder='play_by_play',
        no_data_file_name=f'{season}_play_by_play_no_data.csv',
        label=f'{season} play-by-play',
        id_column='Game ID',
    )


# ====================================================================================================
# FUNCTIONS FOR SCRAPING NHL SHIFT CHART DATA
# ====================================================================================================

# Shift HTML report name consistenicy overides
SHIFT_REPORT_NAME_OVERRIDES = {
    ('NICKLAS GROSSMAN', 'DAL'): 8471269,
    ('CHRISTOPHER BOURQUE', 'WSH'): 8471246,
    ('CHRISTOPHER BOURQUE', 'PIT'): 8471246,
    ('JEFF DROUIN DESLAURIERS', 'EDM'): 8470074,
    ('ALEXANDRE PICARD', 'OTT'): 8470678,
    ('ALEXANDRE PICARD', 'CAR'): 8470678,
    ('ALEXANDRE PICARD', 'CBJ'): 8471221,
}


def get_shift_chart(game_id: int) -> pd.DataFrame:
    """
    Fetch and parse the shift chart for a single game from the NHL stats API.

    :param game_id: The int NHL game ID to fetch shifts for
    :return: A DataFrame of individual player shifts for the game
    """
    url = f'https://api.nhle.com/stats/rest/en/shiftcharts?cayenneExp=gameId={game_id}'
    response = collect_utils.request_with_retry(url, timeout=30)

    rows = response.json().get('data', [])
    if not rows:
        return pd.DataFrame()

    shifts_df = pd.DataFrame(rows)

    # Only keep shift events that represent actual on-ice shifts (drop stoppages/empty rows)
    required = ['playerId', 'teamAbbrev', 'period', 'startTime', 'endTime']
    shifts_df = shifts_df.dropna(subset=required)

    shifts_df['Player'] = shifts_df['firstName'].astype(str) + ' ' + shifts_df['lastName'].astype(str)

    # Rename columns to the project's naming convention
    shifts_df = shifts_df.rename(columns={
        'gameId': 'Game ID',
        'playerId': 'Player ID',
        'teamAbbrev': 'Team',
        'period': 'Period',
        'startTime': 'Start Time',
        'endTime': 'End Time',
        'duration': 'Duration',
    })

    keep_cols = ['Game ID', 'Player ID', 'Player', 'Team', 'Period', 'Start Time', 'End Time', 'Duration']
    shifts_df = shifts_df[[c for c in keep_cols if c in shifts_df.columns]]

    return shifts_df


def normalize_player_name(name: str) -> str:
    """
    Normalize a name for matching, e.g. 'Tim Stützle' -> 'TIM STUTZLE' (upper, strip accents/punctuation).
    Used by get_shift_chart_html to match classic 'Time on Ice' report names back to a real Player ID.

    :param name: A player name str
    :return: The normalized name str
    """
    normalized = unicodedata.normalize('NFKD', name)
    normalized = ''.join(c for c in normalized if not unicodedata.combining(c))
    normalized = re.sub(r'[^A-Za-z\s]', ' ', normalized)
    normalized_name = ' '.join(normalized.upper().split())
    return normalized_name


def get_shift_chart_html(game_id: int) -> pd.DataFrame:
    """
    Fetch and parse a single game's shift chart from the classic NHL 'Time on Ice' HTML reports.
    Used as a fallback for games the JSON shiftcharts API has nothing for.

    :param game_id: The int NHL game ID to fetch shifts for
    :return: A DataFrame of individual player shifts for the game
    """
    game_id_str = str(game_id)
    start_year = int(game_id_str[:4])
    season = f'{start_year}-{start_year + 1}'
    report_number = game_id_str[4:]

    schedule_df = data_io.load_schedule_csv(season)
    player_ids_df = data_io.load_player_ids_csv(season)

    game_row = schedule_df[schedule_df['Game ID'] == game_id]

    home_abbrev = game_row.iloc[0]['Home Team']
    away_abbrev = game_row.iloc[0]['Away Team']
    season_clean = season.replace('-', '')

    # Patterns for the two row types in a shift report: player headers and shift-detail rows
    shift_report_header_re = re.compile(r'^\d{1,2}\s+([A-Za-zÀ-ſ\'\.\- ]+),\s*([A-Za-zÀ-ſ\'\.\- ]+)$')
    shift_report_leading_ints_re = re.compile(r'^(\d+)\s+(\d+)\s+(.*)$')
    shift_report_time_token_re = re.compile(r'\d{1,2}:\d{2}')

    # Fetch and parse each team's classic Time on Ice shift report HTML into individual shift rows
    pieces = []
    for report_code, team_abbrev in [('TV', away_abbrev), ('TH', home_abbrev)]:
        url = f'https://www.nhl.com/scores/htmlreports/{season_clean}/{report_code}{report_number}.HTM'
        response = collect_utils.request_with_retry(url, timeout=30)

        soup = BeautifulSoup(response.text, 'html.parser')
        report_rows = []
        current_name = None
        current_last_name = None

        for tr in soup.find_all('tr'):
            text = ' '.join(tr.stripped_strings)
            if not text:
                continue

            # Shift-detail row
            int_match = shift_report_leading_ints_re.match(text)
            if int_match:
                rest = int_match.group(3)
                if '/' in rest and current_name is not None:
                    times = shift_report_time_token_re.findall(rest)
                    if len(times) >= 5:
                        report_rows.append({
                            'Report Name': current_name,
                            'Report Last Name': current_last_name,
                            'Period': int(int_match.group(2)),
                            'Start Time': times[0].zfill(5),
                            'End Time': times[2].zfill(5),
                            'Duration': times[4].zfill(5),
                        })
                continue

            # Player-header row
            header_match = shift_report_header_re.match(text)
            if header_match:
                last, first = header_match.group(1).strip(), header_match.group(2).strip()
                current_name = f'{first} {last}'
                current_last_name = last

        team_shifts = pd.DataFrame(
            report_rows, columns=['Report Name', 'Report Last Name', 'Period', 'Start Time', 'End Time', 'Duration'],
        )
        if team_shifts.empty:
            continue
        team_shifts['Team'] = team_abbrev
        pieces.append(team_shifts)

    if not pieces:
        return pd.DataFrame()

    shifts_df = pd.concat(pieces, ignore_index=True)

    # Resolve the report name to a real Player/Player ID
    lookup = player_ids_df[['Player', 'Team', 'Player ID']].copy()
    lookup['_key'] = lookup['Player'].map(normalize_player_name)
    lookup = lookup.drop_duplicates(subset=['_key', 'Team'])
    lookup['_tokens'] = lookup['_key'].str.split()

    # How many distinct Player IDs share this normalized name across every team
    name_id_counts = lookup.drop_duplicates(subset=['_key', 'Player ID']).groupby('_key')['Player ID'].nunique()

    exact_lookup = lookup.set_index(['_key', 'Team'])[['Player', 'Player ID']]
    name_only_lookup = lookup.drop_duplicates(subset='_key').set_index('_key')[['Player', 'Player ID']]
    id_to_name = player_ids_df.drop_duplicates(subset='Player ID').set_index('Player ID')['Player']

    shifts_df['_key'] = shifts_df['Report Name'].map(normalize_player_name)

    # Resolve each unique (name, team) once, then broadcast back onto every shift row for that player
    unique_rows = shifts_df[['_key', 'Team', 'Report Last Name']].drop_duplicates(subset=['_key', 'Team'])

    resolutions = []
    for _, row in unique_rows.iterrows():
        key, team, last_name = row['_key'], row['Team'], row['Report Last Name']
        player, player_id = None, None

        # Tier 0: known report quirk for this specific (name, team)
        override_id = SHIFT_REPORT_NAME_OVERRIDES.get((key, team))
        if override_id is not None:
            player, player_id = id_to_name.get(override_id, str(override_id)), override_id

        # Tier 1: exact name, this specific team
        if (key, team) in exact_lookup.index:
            match = exact_lookup.loc[[(key, team)]]
            if len(match) == 1:
                player, player_id = match.iloc[0]['Player'], match.iloc[0]['Player ID']

        # Tier 2: exact name, globally unique across every team this season
        if player_id is None and name_id_counts.get(key, 0) == 1:
            match = name_only_lookup.loc[[key]]
            player, player_id = match.iloc[0]['Player'], match.iloc[0]['Player ID']

        # Tier 3: last name only, team-scoped first, then globally unique
        if player_id is None and pd.notna(last_name):
            last_tokens = tuple(normalize_player_name(last_name).split())
            n = len(last_tokens)
            if n > 0:
                pool = lookup[lookup['_tokens'].apply(lambda toks: tuple(toks[-n:]) == last_tokens)]
                team_pool = pool[pool['Team'] == team]
                if len(team_pool) == 1:
                    player, player_id = team_pool.iloc[0]['Player'], team_pool.iloc[0]['Player ID']
                else:
                    global_pool = pool.drop_duplicates(subset='Player ID')
                    if len(global_pool) == 1:
                        player, player_id = global_pool.iloc[0]['Player'], global_pool.iloc[0]['Player ID']

        resolutions.append({'_key': key, 'Team': team, 'Player': player, 'Player ID': player_id})

    resolution_df = pd.DataFrame(resolutions, columns=['_key', 'Team', 'Player', 'Player ID'])
    merged = shifts_df.merge(resolution_df, on=['_key', 'Team'], how='left')

    # Drop shifts that couldn't be resolved to a Player ID
    merged = merged.dropna(subset=['Player ID']).copy()
    merged['Player ID'] = merged['Player ID'].astype(int)
    shifts_df = merged.drop(columns=['Report Name', 'Report Last Name', '_key'])
    if shifts_df.empty:
        return pd.DataFrame()

    shifts_df.insert(0, 'Game ID', game_id)
    keep_cols = ['Game ID', 'Player ID', 'Player', 'Team', 'Period', 'Start Time', 'End Time', 'Duration']
    shifts_df = shifts_df[keep_cols]
    return shifts_df


def get_shift_chart_with_html_fallback(game_id: int) -> pd.DataFrame:
    """
    get_shift_chart, falling back to get_shift_chart_html when the JSON API has nothing for this game.

    :param game_id: The int NHL game ID to fetch shifts for
    :return: A DataFrame of individual player shifts for the game
    """
    shifts_df = get_shift_chart(game_id)
    if not shifts_df.empty:
        return shifts_df
    fallback_shifts_df = get_shift_chart_html(game_id)
    return fallback_shifts_df


def scrape_shifts(season: str) -> None:
    """
    Scrape shift charts for every regular season game in a season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: None
    """
    collect_utils.scrape_generic(
        ids=collect_utils.get_season_game_ids(season),
        fetch_fn=get_shift_chart_with_html_fallback,
        outputs=[('shifts', f'{season}_shifts.csv')],
        no_data_folder='shifts',
        no_data_file_name=f'{season}_shifts_no_data.csv',
        label=f'{season} shifts',
        id_column='Game ID',
    )


# ====================================================================================================
# FUNCTIONS FOR SCRAPING NHL BOXSCORE DATA (GP/TOI + GOALIE SITUATIONAL STATS, INDEPENDENT OF SHIFTS)
# ====================================================================================================

def get_game_boxscore_stats(game_id: int) -> tuple:
    """
    Fetch and parse the boxscore for a single game.

    :param game_id: The int NHL game ID to fetch the boxscore for
    :return: A tuple of boxscore DataFrames
    """
    url = f'https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore'
    response = collect_utils.request_with_retry(url, timeout=30)

    data = response.json()
    player_stats = data.get('playerByGameStats')

    away_abbrev = data.get('awayTeam', {}).get('abbrev')
    home_abbrev = data.get('homeTeam', {}).get('abbrev')

    skater_rows = []
    goalie_rows = []

    # Build one row per skater/goalie appearance
    for side_key, team_abbrev in [('awayTeam', away_abbrev), ('homeTeam', home_abbrev)]:
        side_stats = player_stats.get(side_key, {})

        for group in ('forwards', 'defense'):
            for p in side_stats.get(group, []):
                # Convert 'MM:SS' TOI into minutes as a float, or NaN if not parseable
                toi_str = p.get('toi')
                if pd.isna(toi_str) or toi_str in (None, ''):
                    toi = float('nan')
                else:
                    try:
                        toi_minutes, toi_seconds = toi_str.split(':')
                        toi = int(toi_minutes) + int(toi_seconds) / 60.0
                    except (ValueError, AttributeError):
                        toi = float('nan')

                skater_rows.append({
                    'Game ID': game_id,
                    'Player ID': p.get('playerId'),
                    'Team': team_abbrev,
                    'Position': p.get('position'),
                    'TOI': toi,
                    'Shifts': p.get('shifts'),
                })

        for g in side_stats.get('goalies', []):
            # Convert MM:SS TOI into minutes as a float, or NaN if not parseable
            toi_str = g.get('toi')
            if pd.isna(toi_str) or toi_str in (None, ''):
                toi = float('nan')
            else:
                try:
                    toi_minutes, toi_seconds = toi_str.split(':')
                    toi = int(toi_minutes) + int(toi_seconds) / 60.0
                except (ValueError, AttributeError):
                    toi = float('nan')

            # Split each saves/shotsFaced string into (saves, shots_faced) ints, defaulting to (0, 0) if not parseable
            ev_value = g.get('evenStrengthShotsAgainst')
            if pd.isna(ev_value) or not isinstance(ev_value, str) or '/' not in ev_value:
                ev_shots = 0
            else:
                try:
                    _, ev_shots_str = ev_value.split('/')
                    ev_shots = int(ev_shots_str)
                except ValueError:
                    ev_shots = 0

            pk_value = g.get('powerPlayShotsAgainst')
            if pd.isna(pk_value) or not isinstance(pk_value, str) or '/' not in pk_value:
                pk_shots = 0
            else:
                try:
                    _, pk_shots_str = pk_value.split('/')
                    pk_shots = int(pk_shots_str)
                except ValueError:
                    pk_shots = 0

            own_pp_value = g.get('shorthandedShotsAgainst')
            if pd.isna(own_pp_value) or not isinstance(own_pp_value, str) or '/' not in own_pp_value:
                own_pp_shots = 0
            else:
                try:
                    _, own_pp_shots_str = own_pp_value.split('/')
                    own_pp_shots = int(own_pp_shots_str)
                except ValueError:
                    own_pp_shots = 0

            goalie_rows.append({
                'Game ID': game_id,
                'Player ID': g.get('playerId'),
                'Team': team_abbrev,
                'Starter': bool(g.get('starter', False)),
                'TOI': toi,
                'EV Shots Against': ev_shots,
                'EV Goals Against': g.get('evenStrengthGoalsAgainst', 0),
                'PK Shots Against': pk_shots,
                'PK Goals Against': g.get('powerPlayGoalsAgainst', 0),
                'Own PP Shots Against': own_pp_shots,
                'Own PP Goals Against': g.get('shorthandedGoalsAgainst', 0),
                'Shots Against': g.get('shotsAgainst', 0),
                'Goals Against': g.get('goalsAgainst', 0),
                'Saves': g.get('saves', 0),
            })

    boxscore_skater_columns = ['Game ID', 'Player ID', 'Team', 'Position', 'TOI', 'Shifts']
    boxscore_goalie_columns = [
        'Game ID', 'Player ID', 'Team', 'Starter', 'TOI',
        'EV Shots Against', 'EV Goals Against',
        'PK Shots Against', 'PK Goals Against',
        'Own PP Shots Against', 'Own PP Goals Against',
        'Shots Against', 'Goals Against', 'Saves',
    ]

    skater_df = pd.DataFrame(skater_rows, columns=boxscore_skater_columns) if skater_rows else pd.DataFrame(columns=boxscore_skater_columns)
    goalie_df = pd.DataFrame(goalie_rows, columns=boxscore_goalie_columns) if goalie_rows else pd.DataFrame(columns=boxscore_goalie_columns)
    return skater_df, goalie_df


def scrape_boxscore(season: str) -> None:
    """
    Scrape the boxscore for every regular season game in a season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: None
    """
    collect_utils.scrape_generic(
        ids=collect_utils.get_season_game_ids(season),
        fetch_fn=get_game_boxscore_stats,
        outputs=[
            ('boxscore', f'{season}_boxscore_skater_toi.csv'),
            ('boxscore', f'{season}_boxscore_goalie_stats.csv'),
        ],
        no_data_folder='boxscore',
        no_data_file_name=f'{season}_boxscore_no_data.csv',
        label=f'{season} boxscore',
        id_column='Game ID',
    )


# ====================================================================================================
# FUNCTIONS FOR SCRAPING NHL GOALIE GAME LOGS
# ====================================================================================================

def get_goalie_game_log(goalie_id: int, season: str, player_name: str) -> pd.DataFrame:
    """
    Fetch a single goalie's game log for a season.

    :param goalie_id: The int NHL player ID for the goalie
    :param season: A str representing the season ('YYYY-YYYY')
    :param player_name: The goalie's full name, used to label each row
    :return: A DataFrame of the goalie's game log rows for the season
    """
    season_clean = season.replace('-', '')
    url = f'https://api-web.nhle.com/v1/player/{goalie_id}/game-log/{season_clean}/2'
    response = collect_utils.request_with_retry(url, timeout=30)

    rows = []
    if response.status_code == 200:
        for g in response.json().get('gameLog', []):
            rows.append({
                'Player': player_name,
                'Player ID': goalie_id,
                'Team': g.get('teamAbbrev'),
                'Game ID': g.get('gameId'),
                'Date': g.get('gameDate'),
                'Opponent': g.get('opponentAbbrev'),
                'Home/Road': g.get('homeRoadFlag'),
                'Result': g.get('decision'),
                'Shots Against': g.get('shotsAgainst'),
                'Goals Against': g.get('goalsAgainst'),
                'Save %': g.get('savePctg'),
                'Shutouts': g.get('shutouts'),
                'TOI': g.get('toi'),
            })

    goalie_log_columns = [
        'Player', 'Player ID', 'Team', 'Game ID', 'Date', 'Opponent',
        'Home/Road', 'Result', 'Shots Against', 'Goals Against',
        'Save %', 'Shutouts', 'TOI',
    ]
    return pd.DataFrame(rows, columns=goalie_log_columns)


def fetch_goalie_log(goalie_id: int, season: str, goalie_names: dict) -> pd.DataFrame:
    """
    Look up a goalie's name and fetch their game log for a season.

    :param goalie_id: The int NHL player ID for the goalie
    :param season: A str representing the season ('YYYY-YYYY')
    :param goalie_names: A dict mapping goalie Player ID to full name
    :return: A DataFrame of the goalie's game log rows for the season
    """
    goalie_log = get_goalie_game_log(goalie_id, season, goalie_names[goalie_id])
    return goalie_log


def scrape_goalie_game_logs(season: str) -> None:
    """
    Scrape game logs for all goalies for a given season.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: None
    """
    prev_season = data_io.get_prev_season(season)
    next_season = data_io.get_next_season(season)

    # Load player_ids CSVs for the current, previous, and next seasons
    player_ids_columns = ['Player', 'Player ID', 'Team', 'Position']

    current_season_path = os.path.join(f'{DATA_DIR}/player_card_data/raw_data/player_ids', f'{season}_player_ids.csv')
    current_season_player_ids = pd.read_csv(current_season_path) if os.path.exists(current_season_path) else pd.DataFrame(columns=player_ids_columns)

    prev_season_path = os.path.join(f'{DATA_DIR}/player_card_data/raw_data/player_ids', f'{prev_season}_player_ids.csv')
    prev_season_player_ids = pd.read_csv(prev_season_path) if os.path.exists(prev_season_path) else pd.DataFrame(columns=player_ids_columns)

    next_season_path = os.path.join(f'{DATA_DIR}/player_card_data/raw_data/player_ids', f'{next_season}_player_ids.csv')
    next_season_player_ids = pd.read_csv(next_season_path) if os.path.exists(next_season_path) else pd.DataFrame(columns=player_ids_columns)

    all_player_ids = pd.concat(
        [current_season_player_ids, prev_season_player_ids, next_season_player_ids],
        ignore_index=True,
    )
    goalies_all = all_player_ids[all_player_ids['Position'] == 'G'].copy()
    goalie_fetch_data = goalies_all.groupby('Player ID').agg(player_name=('Player', 'first')).reset_index()
    goalie_fetch_data = goalie_fetch_data.dropna(subset=['Player ID'])

    goalie_ids = goalie_fetch_data['Player ID'].astype(int).tolist()
    goalie_names = dict(zip(goalie_fetch_data['Player ID'].astype(int), goalie_fetch_data['player_name']))

    collect_utils.scrape_generic(
        ids=goalie_ids,
        fetch_fn=lambda goalie_id: fetch_goalie_log(goalie_id, season, goalie_names),
        outputs=[('goalie_logs', f'{season}_goalie_logs.csv')],
        no_data_folder='goalie_logs',
        no_data_file_name=f'{season}_goalie_logs_no_data.csv',
        label=f'{season} goalie logs',
        id_column='Player ID',
    )
