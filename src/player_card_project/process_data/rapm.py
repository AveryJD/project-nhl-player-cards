# ====================================================================================================
# REGULARIZED ADJUSTED PLUS-MINUS (RAPM)
# ====================================================================================================

# Imports
import functools
import numpy as np
import pandas as pd
import scipy.sparse as sp
from sklearn.linear_model import Ridge
from sklearn.model_selection import GroupKFold

from player_card_project import constants
from player_card_project import data_io
from player_card_project.process_data import war
from player_card_project.process_data import xgoals as xg


DATA_DIR = constants.DATA_DIR


# ====================================================================================================
# STINT RECONSTRUCTION
# ====================================================================================================

def time_to_seconds(time_str: str) -> int:
    """
    Convert a 'MM:SS' clock string into total seconds.

    :param time_str: A str clock value in 'MM:SS' format
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
    goalie_ids = set(ids_df.loc[ids_df['Position'] == 'G', 'Player ID'])
    return goalie_ids


@functools.lru_cache(maxsize=None)
def build_season_stints(season: str) -> pd.DataFrame:
    """
    Reconstruct every on-ice lineup stint for a season (a maximal time interval within one game/period where both teams' on-ice skaters are unchanged), with each team's goals scored during it. Memoized (functools.lru_cache) since this is the most expensive, most-often-independently-re-run computation in the pipeline; call build_season_stints.cache_clear() if shift data is ever re-scraped mid-process.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: A DataFrame of reconstructed on-ice stints, one row per stint
    """
    shifts_df = data_io.load_shifts_csv(season).copy()

    time_pattern = r'^\d{1,2}:\d{2}$'
    valid_time = (
        shifts_df['Start Time'].astype(str).str.match(time_pattern, na=False)
        & shifts_df['End Time'].astype(str).str.match(time_pattern, na=False)
    )
    shifts_df = shifts_df[valid_time].copy()
    shifts_df['Player ID'] = shifts_df['Player ID'].astype(int)
    shifts_df['Start Sec'] = shifts_df['Start Time'].apply(time_to_seconds)
    shifts_df['End Sec'] = shifts_df['End Time'].apply(time_to_seconds)
    shifts_df = shifts_df[shifts_df['End Sec'] > shifts_df['Start Sec']]

    goalie_ids = goalie_id_set(season)

    goals_df = data_io.load_goals_csv(season).copy()
    valid_goal_time = goals_df['Time'].astype(str).str.match(time_pattern, na=False)
    goals_df = goals_df[valid_goal_time].copy()
    goals_df['Sec'] = goals_df['Time'].apply(time_to_seconds)
    goals_by_period = {key: grp for key, grp in goals_df.groupby(['Game ID', 'Period'])}

    empty_goals = pd.DataFrame(columns=['Team', 'Sec'])

    stint_records = []
    unmatched_goals = 0

    for (game_id, period), period_df in shifts_df.groupby(['Game ID', 'Period']):
        teams = period_df['Team'].unique()
        if len(teams) != 2:
            continue
        team_a, team_b = sorted(teams)

        player_ids = period_df['Player ID'].to_numpy()
        team_arr = period_df['Team'].to_numpy()
        start_arr = period_df['Start Sec'].to_numpy()
        end_arr = period_df['End Sec'].to_numpy()

        boundaries = sorted(set(start_arr.tolist()) | set(end_arr.tolist()))
        if len(boundaries) < 2:
            continue

        period_goals = goals_by_period.get((game_id, period), empty_goals)
        goal_secs = period_goals['Sec'].to_numpy() if len(period_goals) else np.array([])
        goal_teams = period_goals['Team'].to_numpy() if len(period_goals) else np.array([])

        # Pass 1: compute the exact on-ice lineup for every raw boundary-to-boundary sub-segment (every start/end timestamp is its own boundary, so sampling each sub-segment at its own start instant is always correct)
        sub_segments = []
        for i in range(len(boundaries) - 1):
            seg_start, seg_end = boundaries[i], boundaries[i + 1]

            active_mask = (start_arr <= seg_start) & (end_arr > seg_start)
            if not active_mask.any():
                continue

            active_players = player_ids[active_mask]
            active_teams = team_arr[active_mask]

            team_a_players = set(active_players[active_teams == team_a])
            team_b_players = set(active_players[active_teams == team_b])

            team_a_skaters = frozenset(p for p in team_a_players if p not in goalie_ids)
            team_b_skaters = frozenset(p for p in team_b_players if p not in goalie_ids)
            n_a, n_b = len(team_a_skaters), len(team_b_skaters)

            # Sanity bound
            if n_a == 0 or n_b == 0 or n_a > 6 or n_b > 6:
                continue

            team_a_goalie_on = any(p in goalie_ids for p in team_a_players)
            team_b_goalie_on = any(p in goalie_ids for p in team_b_players)
            # Which specific goalie, not just whether one is on
            team_a_goalie_id = next((p for p in team_a_players if p in goalie_ids), None)
            team_b_goalie_id = next((p for p in team_b_players if p in goalie_ids), None)

            if i == 0:
                # First sub-segment of the period
                left_bound = goal_secs >= seg_start
            else:
                # Exclusive on the left otherwise: a goal at the exact same second as this segment's start belongs to the preceding segment
                left_bound = goal_secs > seg_start

            if i == len(boundaries) - 2:
                # Last sub-segment of the period
                in_seg = left_bound
            else:
                # Inclusive on the right: a goal at the exact same second as this segment's end is credited to this ending segment
                in_seg = left_bound & (goal_secs <= seg_end)

            goals_a = int(np.sum(in_seg & (goal_teams == team_a)))
            goals_b = int(np.sum(in_seg & (goal_teams == team_b)))

            sub_segments.append((
                seg_start, seg_end, team_a_skaters, team_a_goalie_on, goals_a,
                team_b_skaters, team_b_goalie_on, goals_b,
                team_a_goalie_id, team_b_goalie_id,
            ))

        # Pass 2: collapse consecutive sub-segments sharing the exact same on-ice lineup into one stint, so near-simultaneous shift-timestamp noise doesn't inflate the stint table
        cur = None
        for seg_start, seg_end, ta_sk, ta_g, ga, tb_sk, tb_g, gb, ta_gid, tb_gid in sub_segments:
            key = (ta_sk, ta_g, tb_sk, tb_g)
            if cur is not None and cur['key'] == key and cur['end'] == seg_start:
                cur['end'] = seg_end
                cur['goals_a'] += ga
                cur['goals_b'] += gb
            else:
                if cur is not None:
                    stint_records.append({
                        'Game ID': game_id, 'Period': period,
                        'Start': cur['start'], 'End': cur['end'], 'Duration': cur['end'] - cur['start'],
                        'Team A': team_a, 'Team A Skaters': cur['key'][0],
                        'Team A Goalie On': cur['key'][1], 'Team A Goals': cur['goals_a'],
                        'Team A Goalie ID': cur['goalie_a'],
                        'Team B': team_b, 'Team B Skaters': cur['key'][2],
                        'Team B Goalie On': cur['key'][3], 'Team B Goals': cur['goals_b'],
                        'Team B Goalie ID': cur['goalie_b'],
                    })
                cur = {
                    'key': key, 'start': seg_start, 'end': seg_end, 'goals_a': ga, 'goals_b': gb,
                    'goalie_a': ta_gid, 'goalie_b': tb_gid,
                }
        if cur is not None:
            stint_records.append({
                'Game ID': game_id, 'Period': period,
                'Start': cur['start'], 'End': cur['end'], 'Duration': cur['end'] - cur['start'],
                'Team A': team_a, 'Team A Skaters': cur['key'][0],
                'Team A Goalie On': cur['key'][1], 'Team A Goals': cur['goals_a'],
                'Team A Goalie ID': cur['goalie_a'],
                'Team B': team_b, 'Team B Skaters': cur['key'][2],
                'Team B Goalie On': cur['key'][3], 'Team B Goals': cur['goals_b'],
                'Team B Goalie ID': cur['goalie_b'],
            })

        # Diagnostic only: goals that fell entirely outside every reconstructed sub-segment
        if len(goal_secs):
            covered = (goal_secs >= boundaries[0])
            unmatched_goals += int((~covered).sum())

    stints_df = pd.DataFrame(stint_records)

    return stints_df


# ====================================================================================================
# CONTEXTUAL OVERLAYS
# ====================================================================================================

def attach_xg_to_stints(stints_df: pd.DataFrame, season: str, bundle: dict = None) -> pd.DataFrame:
    """
    Sum each stint's predicted xG per team (unblocked shot attempts only), adding 'Team A xG'/'Team B xG' columns, used by compute_season_rapm_xg in place of the goals-only response.

    :param stints_df: A season's stints DataFrame
    :param season: A str representing the season ('YYYY-YYYY')
    :param bundle: An optional pre-loaded xG model bundle; loaded from disk if not given
    :return: The stints DataFrame with 'Team A xG'/'Team B xG' columns added
    """
    out = stints_df.copy()
    if out.empty:
        out['Team A xG'] = pd.Series(dtype=float)
        out['Team B xG'] = pd.Series(dtype=float)
    else:
        shots_df = data_io.load_shot_events_csv(season)
        shots_df = shots_df[shots_df['Event Type'].isin(constants.UNBLOCKED_EVENT_TYPES)].copy()

        time_pattern = r'^\d{1,2}:\d{2}$'
        valid_time = shots_df['Time'].astype(str).str.match(time_pattern, na=False)
        shots_df = shots_df[valid_time].copy()

        if shots_df.empty:
            out['Team A xG'] = 0.0
            out['Team B xG'] = 0.0
        else:
            if bundle is None:
                bundle = xg.load_xg_model()

            feats = xg.engineer_features(shots_df)
            feats = xg.attach_strength_state_from_stints(feats, out)
            # Score State and the handedness features are the other xG features needed before predicting
            if 'Score State' not in feats.columns:
                feats = xg.attach_score_state_to_shots(feats)
            if 'Off Wing' not in feats.columns:
                feats = xg.attach_handedness_features(feats)
            feats = feats.reset_index(drop=True)
            feats['xG'] = xg.predict_xg_by_strength(feats, bundle)
            feats['Sec'] = feats['Time'].apply(time_to_seconds)

            out = out.reset_index(drop=True)
            team_a_xg = np.zeros(len(out))
            team_b_xg = np.zeros(len(out))

            xg_by_period = {key: grp for key, grp in feats.groupby(['Game ID', 'Period'])}

            for (game_id, period), period_df in out.groupby(['Game ID', 'Period']):
                period_shots = xg_by_period.get((game_id, period))
                if period_shots is None or period_shots.empty:
                    continue

                local_idx = period_df.index.to_numpy()
                order = np.argsort(period_df['Start'].to_numpy())
                sorted_local_idx = local_idx[order]
                sorted_starts = period_df['Start'].to_numpy()[order]
                sorted_ends = period_df['End'].to_numpy()[order]
                team_a = period_df['Team A'].iloc[0]
                team_b = period_df['Team B'].iloc[0]
                last_pos = len(sorted_starts) - 1

                shot_secs = period_shots['Sec'].to_numpy()
                shot_teams = period_shots['Team'].to_numpy()
                shot_xg = period_shots['xG'].to_numpy()

                for s_sec, s_team, s_xg in zip(shot_secs, shot_teams, shot_xg):
                    if np.isnan(s_xg):
                        # No per-strength xG model for this shot's strength state
                        continue
                    pos = np.searchsorted(sorted_starts, s_sec, side='right') - 1
                    pos = max(0, min(pos, last_pos))
                    # Tie-break: a shot on the exact stint boundary goes to the ending stint, only when the two stints actually touch
                    if pos > 0 and s_sec == sorted_starts[pos] and sorted_ends[pos - 1] == s_sec:
                        pos -= 1
                    elif not (pos == last_pos or s_sec < sorted_ends[pos]):
                        # Falls in a gap between stints 
                        continue 

                    stint_idx = sorted_local_idx[pos]
                    if s_team == team_a:
                        team_a_xg[stint_idx] += s_xg
                    elif s_team == team_b:
                        team_b_xg[stint_idx] += s_xg

            out['Team A xG'] = team_a_xg
            out['Team B xG'] = team_b_xg
    return out


def attach_score_state(stints_df: pd.DataFrame, season: str) -> pd.DataFrame:
    """
    Attach each stint's score differential as of the moment it started (not counting a goal scored during the stint), capped at +/-constants.SCORE_STATE_CAP, as 'Team A Score State'/'Team B Score State'.

    :param stints_df: A season's stints DataFrame
    :param season: A str representing the season ('YYYY-YYYY')
    :return: The stints DataFrame with 'Team A Score State'/'Team B Score State' columns added
    """
    out = stints_df.copy()
    if out.empty:
        out['Team A Score State'] = pd.Series(dtype=int)
        out['Team B Score State'] = pd.Series(dtype=int)
    else:
        goals_df = data_io.load_goals_csv(season).copy()

        time_pattern = r'^\d{1,2}:\d{2}$'
        valid_time = goals_df['Time'].astype(str).str.match(time_pattern, na=False)
        goals_df = goals_df[valid_time].copy()
        goals_df['Sec'] = goals_df['Time'].apply(time_to_seconds)
        # Cumulative goal count needs a global, period-independent clock (periods are 1200 seconds)
        goals_df['Abs Sec'] = (goals_df['Period'] - 1) * 1200 + goals_df['Sec']
        goals_by_game = {key: grp.sort_values('Abs Sec') for key, grp in goals_df.groupby('Game ID')}

        out = out.reset_index(drop=True)
        out['Abs Start'] = (out['Period'] - 1) * 1200 + out['Start']

        team_a_state = np.zeros(len(out), dtype=int)
        team_b_state = np.zeros(len(out), dtype=int)

        for game_id, game_df in out.groupby('Game ID'):
            game_goals = goals_by_game.get(game_id)
            if game_goals is None or game_goals.empty:
                continue

            goal_abs_secs = game_goals['Abs Sec'].to_numpy()
            goal_teams = game_goals['Team'].to_numpy()

            for idx, row in game_df.iterrows():
                prior_mask = goal_abs_secs < row['Abs Start']
                team_a_goals = int(np.sum(prior_mask & (goal_teams == row['Team A'])))
                team_b_goals = int(np.sum(prior_mask & (goal_teams == row['Team B'])))
                team_a_state[idx] = team_a_goals - team_b_goals
                team_b_state[idx] = team_b_goals - team_a_goals

        out['Team A Score State'] = np.clip(team_a_state, -constants.SCORE_STATE_CAP, constants.SCORE_STATE_CAP)
        out['Team B Score State'] = np.clip(team_b_state, -constants.SCORE_STATE_CAP, constants.SCORE_STATE_CAP)
        out = out.drop(columns=['Abs Start'])
    return out


def attach_pp_expiry(stints_df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag stints beginning within constants.PP_EXPIRY_WINDOW_SECONDS of a same-ice PP/PK just ending, as 'Team A PP Expiry'/'Team B PP Expiry' (1/0).

    :param stints_df: A season's stints DataFrame
    :return: The stints DataFrame with 'Team A PP Expiry'/'Team B PP Expiry' columns added
    """
    out = stints_df.copy()
    if out.empty:
        out['Team A PP Expiry'] = pd.Series(dtype=int)
        out['Team B PP Expiry'] = pd.Series(dtype=int)
    else:
        out = out.reset_index(drop=True)
        team_a_expiry = np.zeros(len(out), dtype=int)
        team_b_expiry = np.zeros(len(out), dtype=int)

        for (game_id, period), period_df in out.groupby(['Game ID', 'Period']):
            period_df = period_df.sort_values('Start')
            prev_a_n, prev_b_n, prev_end = None, None, None

            for idx, row in period_df.iterrows():
                was_special_teams = prev_a_n is not None and prev_a_n != prev_b_n
                just_ended = prev_end is not None and (row['Start'] - prev_end) <= constants.PP_EXPIRY_WINDOW_SECONDS
                cur_is_es = len(row['Team A Skaters']) == len(row['Team B Skaters'])

                if was_special_teams and just_ended and cur_is_es:
                    team_a_expiry[idx] = 1
                    team_b_expiry[idx] = 1

                prev_a_n, prev_b_n = len(row['Team A Skaters']), len(row['Team B Skaters'])
                prev_end = row['End']

        out['Team A PP Expiry'] = team_a_expiry
        out['Team B PP Expiry'] = team_b_expiry
    return out


def attach_pp_start_type(stints_df: pd.DataFrame, season: str) -> pd.DataFrame:
    """
    Flag special-teams stints that began on-the-fly (immediately out of an ES stint, no faceoff at the stint's own start second) rather than via whistle-and-draw, as 'Team A/B PP Start OTF' (same value for both sides).

    :param stints_df: A season's stints DataFrame
    :param season: A str representing the season ('YYYY-YYYY')
    :return: The stints DataFrame with 'Team A PP Start OTF'/'Team B PP Start OTF' columns added
    """
    cols = ['Team A PP Start OTF', 'Team B PP Start OTF']
    out = stints_df.copy()
    if out.empty:
        for col in cols:
            out[col] = pd.Series(dtype=int)
    else:
        faceoffs_df = data_io.load_faceoffs_csv(season).copy()
        time_pattern = r'^\d{1,2}:\d{2}$'
        valid_time = faceoffs_df['Time'].astype(str).str.match(time_pattern, na=False)
        faceoffs_df = faceoffs_df[valid_time].copy()
        faceoffs_df['Sec'] = faceoffs_df['Time'].apply(time_to_seconds)
        faceoff_secs_by_period = {
            key: set(grp['Sec']) for key, grp in faceoffs_df.groupby(['Game ID', 'Period'])
        }

        out = out.reset_index(drop=True)
        otf_flag = np.zeros(len(out), dtype=int)

        for (game_id, period), period_df in out.groupby(['Game ID', 'Period']):
            period_df = period_df.sort_values('Start')
            period_faceoff_secs = faceoff_secs_by_period.get((game_id, period), set())
            prev_a_n, prev_b_n, prev_end = None, None, None

            for idx, row in period_df.iterrows():
                prev_was_es = prev_a_n is not None and prev_a_n == prev_b_n
                just_changed = prev_end is not None and (row['Start'] - prev_end) <= constants.PP_EXPIRY_WINDOW_SECONDS
                cur_is_special_teams = len(row['Team A Skaters']) != len(row['Team B Skaters'])
                no_faceoff = row['Start'] not in period_faceoff_secs

                if prev_was_es and just_changed and cur_is_special_teams and no_faceoff:
                    otf_flag[idx] = 1

                prev_a_n, prev_b_n = len(row['Team A Skaters']), len(row['Team B Skaters'])
                prev_end = row['End']

        out['Team A PP Start OTF'] = otf_flag
        out['Team B PP Start OTF'] = otf_flag
    return out


def attach_zone_start(stints_df: pd.DataFrame, season: str) -> pd.DataFrame:
    """
    Attach each stint's zone start ('O'/'D'/'N' one-hot columns per team, from the faceoff exactly at the stint's start second, per zone_perspective; on-the-fly starts get all-0).

    :param stints_df: A season's stints DataFrame
    :param season: A str representing the season ('YYYY-YYYY')
    :return: The stints DataFrame with per-team zone-start one-hot columns added
    """
    # Which side of a faceoff collect_stats.get_game_faceoffs' 'Zone' column is relative to
    zone_perspective = 'winner'

    cols = [
        'Team A Zone O', 'Team A Zone D', 'Team A Zone N',
        'Team B Zone O', 'Team B Zone D', 'Team B Zone N',
    ]
    out = stints_df.copy()
    if out.empty:
        for col in cols:
            out[col] = pd.Series(dtype=int)
    else:
        faceoffs_df = data_io.load_faceoffs_csv(season).copy()
        time_pattern = r'^\d{1,2}:\d{2}$'
        valid_time = faceoffs_df['Time'].astype(str).str.match(time_pattern, na=False)
        faceoffs_df = faceoffs_df[valid_time].copy()
        faceoffs_df['Sec'] = faceoffs_df['Time'].apply(time_to_seconds)
        faceoffs_by_period = {key: grp for key, grp in faceoffs_df.groupby(['Game ID', 'Period'])}

        out = out.reset_index(drop=True)
        zone_arrs = {col: np.zeros(len(out), dtype=int) for col in cols}

        for (game_id, period), period_df in out.groupby(['Game ID', 'Period']):
            period_faceoffs = faceoffs_by_period.get((game_id, period))
            if period_faceoffs is None or period_faceoffs.empty:
                continue

            fo_secs = period_faceoffs['Sec'].to_numpy()
            fo_teams = period_faceoffs['Team'].to_numpy()
            fo_zones = period_faceoffs['Zone'].to_numpy()

            for idx, row in period_df.iterrows():
                # A faceoff exactly at this stint's start second is what created the stint boundary
                at_start = fo_secs == row['Start']
                if not at_start.any():
                    continue

                fo_team = fo_teams[at_start][0]
                fo_zone = fo_zones[at_start][0]
                if pd.isna(fo_zone) or fo_zone not in ('O', 'D', 'N'):
                    continue

                # fo_team is the faceoff winner; zone_perspective controls whether fo_zone is relative to the winner (as scraped) or needs flipping to the loser's perspective
                winner_zone = fo_zone
                if fo_team == row['Team A']:
                    a_zone, b_zone = winner_zone, {'O': 'D', 'D': 'O', 'N': 'N'}[winner_zone]
                elif fo_team == row['Team B']:
                    b_zone, a_zone = winner_zone, {'O': 'D', 'D': 'O', 'N': 'N'}[winner_zone]
                else:
                    continue

                if zone_perspective == 'loser':
                    a_zone = {'O': 'D', 'D': 'O', 'N': 'N'}[a_zone]
                    b_zone = {'O': 'D', 'D': 'O', 'N': 'N'}[b_zone]

                if a_zone == 'O':
                    zone_arrs['Team A Zone O'][idx] = 1
                elif a_zone == 'D':
                    zone_arrs['Team A Zone D'][idx] = 1
                else:
                    zone_arrs['Team A Zone N'][idx] = 1
                if b_zone == 'O':
                    zone_arrs['Team B Zone O'][idx] = 1
                elif b_zone == 'D':
                    zone_arrs['Team B Zone D'][idx] = 1
                else:
                    zone_arrs['Team B Zone N'][idx] = 1

        for col in cols:
            out[col] = zone_arrs[col]
    return out


def attach_home_ice(stints_df: pd.DataFrame, season: str) -> pd.DataFrame:
    """
    Attach whether each team was the home team for that game, as 'Team A Home'/'Team B Home' (1/0).

    :param stints_df: A season's stints DataFrame
    :param season: A str representing the season ('YYYY-YYYY')
    :return: The stints DataFrame with 'Team A Home'/'Team B Home' columns added
    """
    out = stints_df.copy()
    if out.empty:
        out['Team A Home'] = pd.Series(dtype=int)
        out['Team B Home'] = pd.Series(dtype=int)
    else:
        schedule_df = data_io.load_schedule_csv(season)
        home_by_game = schedule_df.set_index('Game ID')['Home Team'].to_dict()
        home_team = out['Game ID'].map(home_by_game)

        out['Team A Home'] = (out['Team A'] == home_team).astype(int)
        out['Team B Home'] = (out['Team B'] == home_team).astype(int)
    return out


def attach_back_to_back(stints_df: pd.DataFrame, season: str) -> pd.DataFrame:
    """
    Attach whether each team was playing the second game of a back-to-back, as 'Team A B2B'/'Team B B2B' (1/0).

    :param stints_df: A season's stints DataFrame
    :param season: A str representing the season ('YYYY-YYYY')
    :return: The stints DataFrame with 'Team A B2B'/'Team B B2B' columns added
    """
    out = stints_df.copy()
    if out.empty:
        out['Team A B2B'] = pd.Series(dtype=int)
        out['Team B B2B'] = pd.Series(dtype=int)
    else:
        schedule_df = data_io.load_schedule_csv(season).copy()
        schedule_df['Date'] = pd.to_datetime(schedule_df['Date'], errors='coerce')
        date_by_game = schedule_df.set_index('Game ID')['Date'].to_dict()

        # Every team's sorted list of game dates, used to check whether this team also played yesterday
        team_dates = {}
        for _, row in schedule_df.iterrows():
            if pd.isna(row['Date']):
                continue
            for team in (row['Home Team'], row['Away Team']):
                team_dates.setdefault(team, set()).add(row['Date'].normalize())

        game_ids = out['Game ID']

        team_a_b2b = []
        for team, game_id in zip(out['Team A'], game_ids):
            game_date = date_by_game.get(game_id)
            if game_date is None or pd.isna(game_date) or team not in team_dates:
                team_a_b2b.append(0)
            else:
                team_a_b2b.append(int((game_date.normalize() - pd.Timedelta(days=1)) in team_dates[team]))
        out['Team A B2B'] = team_a_b2b

        team_b_b2b = []
        for team, game_id in zip(out['Team B'], game_ids):
            game_date = date_by_game.get(game_id)
            if game_date is None or pd.isna(game_date) or team not in team_dates:
                team_b_b2b.append(0)
            else:
                team_b_b2b.append(int((game_date.normalize() - pd.Timedelta(days=1)) in team_dates[team]))
        out['Team B B2B'] = team_b_b2b
    return out


def attach_interaction_terms(stints_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add score-state x zone-start and PP-expiry x home-ice interaction columns; must be called after every other attach_* function.

    :param stints_df: A season's stints DataFrame with every other attach_* overlay already applied
    :return: The stints DataFrame with interaction columns added
    """
    out = stints_df.copy()

    for team in ('Team A', 'Team B'):
        score_col = f'{team} Score State'
        zone_o_col = f'{team} Zone O'
        zone_d_col = f'{team} Zone D'
        expiry_col = f'{team} PP Expiry'
        home_col = f'{team} Home'

        score = out.get(score_col, pd.Series(0, index=out.index))
        zone_o = out.get(zone_o_col, pd.Series(0, index=out.index))
        zone_d = out.get(zone_d_col, pd.Series(0, index=out.index))
        expiry = out.get(expiry_col, pd.Series(0, index=out.index))
        home = out.get(home_col, pd.Series(0, index=out.index))

        out[f'{team} Score×Zone O'] = score * zone_o
        out[f'{team} Score×Zone D'] = score * zone_d
        out[f'{team} Expiry×Home'] = expiry * home

    return out


def build_context_features(stints_df: pd.DataFrame, season: str, bundle: dict = None) -> pd.DataFrame:
    """
    Run every attach_* contextual overlay in sequence.

    :param stints_df: A season's stints DataFrame
    :param season: A str representing the season ('YYYY-YYYY')
    :param bundle: An optional pre-loaded xG model bundle, passed through to attach_xg_to_stints
    :return: The stints DataFrame with every contextual overlay column added
    """
    # Order matters only for attach_interaction_terms, which must run last
    out = attach_xg_to_stints(stints_df, season, bundle=bundle)
    out = attach_score_state(out, season)
    out = attach_pp_expiry(out)
    out = attach_pp_start_type(out, season)
    out = attach_zone_start(out, season)
    out = attach_home_ice(out, season)
    out = attach_back_to_back(out, season)
    out = attach_interaction_terms(out)
    return out


# ====================================================================================================
# STINT -> REGRESSION ROW EXPANSION
# ====================================================================================================

# Column schema for build_season_stints' regression-row expansions (expand_es_rows/expand_pp_rows/etc.)
ROW_COLUMNS = ['Game ID', 'Duration', 'Off Skaters', 'Def Skaters', 'Goals For']

def perspective_rows(stints_df: pd.DataFrame, focal_is_a: bool) -> pd.DataFrame:
    """
    Re-key a stints DataFrame to one team's perspective (Off Skaters/Def Skaters/Goals For), carrying through any optional context columns present.

    :param stints_df: A DataFrame from build_season_stints, optionally with context columns attached
    :param focal_is_a: True to key from Team A's perspective (Off = Team A), False for Team B's
    :return: A DataFrame with 'Game ID', 'Duration', 'Off Skaters', 'Def Skaters', 'Goals For', plus
             any optional context columns present on stints_df, re-keyed to the focal team
    """
    if focal_is_a:
        off_col, off_goals_col, def_col = 'Team A Skaters', 'Team A Goals', 'Team B Skaters'
        off_suffix, def_suffix = 'Team A', 'Team B'
    else:
        off_col, off_goals_col, def_col = 'Team B Skaters', 'Team B Goals', 'Team A Skaters'
        off_suffix, def_suffix = 'Team B', 'Team A'

    data = {
        'Game ID': stints_df['Game ID'],
        'Duration': stints_df['Duration'],
        'Off Skaters': stints_df[off_col],
        'Def Skaters': stints_df[def_col],
        'Goals For': stints_df[off_goals_col],
    }

    # Optional Team A/Team B column pairs carried through into Off/Def-perspective row columns if present on the stints_df being expanded, see build_context_features. ('Team col suffix', 'Off output column', 'Def output column or None')
    optinal_column_specs = [
        ('xG', 'xG For', None),
        ('Zone O', 'Off Zone Start O', None),
        ('Zone D', 'Off Zone Start D', None),
        ('Score State', 'Off Score State', None),
        ('PP Expiry', 'Off PP Expiry', None),
        ('PP Start OTF', 'Off PP Start OTF', None),
        ('Home', 'Off Home', None),
        ('B2B', 'Off B2B', 'Def B2B'),
        ('Score×Zone O', 'Off Score×Zone O', None),
        ('Score×Zone D', 'Off Score×Zone D', None),
        ('Expiry×Home', 'Off Expiry×Home', 'Def Expiry×Home'),
    ]

    # Carry through any optional context columns present, re-keyed to the focal team's perspective
    for team_suffix, off_name, def_name in optinal_column_specs:
        off_source = f'{off_suffix} {team_suffix}'
        if off_source in stints_df.columns:
            data[off_name] = stints_df[off_source]
        if def_name is not None:
            def_source = f'{def_suffix} {team_suffix}'
            if def_source in stints_df.columns:
                data[def_name] = stints_df[def_source]

    result = pd.DataFrame(data)
    return result


def expand_es_rows(stints_df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand stints into 5-on-5 even-strength regression rows, one per team-perspective (two rows per qualifying stint).

    :param stints_df: A season's stints DataFrame
    :return: A DataFrame of ROW_COLUMNS regression rows for qualifying 5v5 stints
    """
    if stints_df.empty:
        result = pd.DataFrame(columns=ROW_COLUMNS)
    else:
        # Both sides of a 5v5 stint qualify, so expand each stint into a pair of rows
        es_mask = (
            (stints_df['Team A Skaters'].apply(len) == 5)
            & (stints_df['Team B Skaters'].apply(len) == 5)
            & stints_df['Team A Goalie On']
            & stints_df['Team B Goalie On']
        )
        es = stints_df[es_mask]
        result = pd.concat([perspective_rows(es, True), perspective_rows(es, False)], ignore_index=True)
    return result


def expand_pp_rows(stints_df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand stints into 5-on-4 power-play regression rows, one per qualifying stint. This is the joint fit whose "offense" side becomes ppl_score and sign-flipped "defense" side becomes pkl_score.

    :param stints_df: A season's stints DataFrame
    :return: A DataFrame of ROW_COLUMNS regression rows for qualifying 5v4 stints
    """
    if stints_df.empty:
        result = pd.DataFrame(columns=ROW_COLUMNS)
    else:
        # Either team can be the 5-skater side, so pool both directions into one joint fit
        a_pp_mask = (
            (stints_df['Team A Skaters'].apply(len) == 5)
            & (stints_df['Team B Skaters'].apply(len) == 4)
            & stints_df['Team A Goalie On']
            & stints_df['Team B Goalie On']
        )
        b_pp_mask = (
            (stints_df['Team B Skaters'].apply(len) == 5)
            & (stints_df['Team A Skaters'].apply(len) == 4)
            & stints_df['Team B Goalie On']
            & stints_df['Team A Goalie On']
        )

        a_pp_rows = perspective_rows(stints_df[a_pp_mask], True)
        b_pp_rows = perspective_rows(stints_df[b_pp_mask], False)
        result = pd.concat([a_pp_rows, b_pp_rows], ignore_index=True)
    return result


def expand_pk_offense_rows(stints_df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand the same 5-on-4 stints as expand_pp_rows into rows from the shorthanded team's own offense perspective, used by model_training.fit_penalty_xg_per_minute (not by RAPM itself).

    :param stints_df: A season's stints DataFrame
    :return: A DataFrame of ROW_COLUMNS regression rows for the shorthanded team's own offense
    """
    if stints_df.empty:
        result = pd.DataFrame(columns=ROW_COLUMNS)
    else:
        a_pp_mask = (
            (stints_df['Team A Skaters'].apply(len) == 5)
            & (stints_df['Team B Skaters'].apply(len) == 4)
            & stints_df['Team A Goalie On']
            & stints_df['Team B Goalie On']
        )
        b_pp_mask = (
            (stints_df['Team B Skaters'].apply(len) == 5)
            & (stints_df['Team A Skaters'].apply(len) == 4)
            & stints_df['Team B Goalie On']
            & stints_df['Team A Goalie On']
        )

        # Opposite focal side from expand_pp_rows: the 4-skater PK unit's own offense
        a_pk_rows = perspective_rows(stints_df[a_pp_mask], False)
        b_pk_rows = perspective_rows(stints_df[b_pp_mask], True)
        result = pd.concat([a_pk_rows, b_pk_rows], ignore_index=True)
    return result


def expand_5v3_offense_rows(stints_df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand stints into 5-on-3 regression rows from the advantaged team's own perspective, used by model_training.fit_penalty_xg_per_minute (there's no 3v5-offense counterpart since it has too few rows to be reliable).

    :param stints_df: A season's stints DataFrame
    :return: A DataFrame of ROW_COLUMNS regression rows for the advantaged team's own offense
    """
    if stints_df.empty:
        result = pd.DataFrame(columns=ROW_COLUMNS)
    else:
        a_adv_mask = (
            (stints_df['Team A Skaters'].apply(len) == 5)
            & (stints_df['Team B Skaters'].apply(len) == 3)
            & stints_df['Team A Goalie On']
            & stints_df['Team B Goalie On']
        )
        b_adv_mask = (
            (stints_df['Team B Skaters'].apply(len) == 5)
            & (stints_df['Team A Skaters'].apply(len) == 3)
            & stints_df['Team B Goalie On']
            & stints_df['Team A Goalie On']
        )

        a_rows = perspective_rows(stints_df[a_adv_mask], True)
        b_rows = perspective_rows(stints_df[b_adv_mask], False)
        result = pd.concat([a_rows, b_rows], ignore_index=True)
    return result


# ====================================================================================================
# CROSS-SEASON PRIOR (SEE THIS MODULE'S HEADER DOCSTRING)
# ====================================================================================================

def previous_seasons(season: str, n: int) -> list:
    """
    The `n` seasons chronologically before `season`, most recent first, as 'YYYY-YYYY' strings.

    :param season: A str representing the season ('YYYY-YYYY')
    :param n: The int number of prior seasons to return
    :return: A list of str prior seasons, most recent first
    """
    # Season strings are 'YYYY-YYYY', so step back one year at a time from the season's start year
    start_year = int(season[:4])
    seasons = [f'{start_year - i - 1}-{start_year - i}' for i in range(n)]
    return seasons


def build_rapm_prior_accumulators(
    season: str, off_col: str, def_col: str, situation_off: str, situation_def: str,
    lookback: int = constants.PRIOR_LOOKBACK_SEASONS,
) -> dict:
    """
    The TOI-weighted-sum/TOI-total accumulation step of build_rapm_prior, split out (doesn't depend on PRIOR_STABILIZATION_TOI) so a candidate stabilization value can be tested against one accumulation pass without re-walking the RAPM CSVs.

    :param season: A str representing the season ('YYYY-YYYY')
    :param off_col: See build_rapm_prior
    :param def_col: See build_rapm_prior
    :param situation_off: See build_rapm_prior
    :param situation_def: See build_rapm_prior
    :param lookback: See build_rapm_prior
    :return: A dict {'off_weighted_sum': {Player ID: float}, 'off_weight_total': {Player ID: float},
             'def_weighted_sum': {...}, 'def_weight_total': {...}}, where both weighted sums are already
             in fit-space (def negated, matching build_rapm_prior's docstring)
    """
    off_weighted_sum, off_weight_total = {}, {}
    def_weighted_sum, def_weight_total = {}, {}

    # Pool TOI-weighted history across every prior season in the lookback window
    for prior_season in previous_seasons(season, lookback):
        try:
            rapm_df = data_io.load_rapm_scores_csv(prior_season)
        except FileNotFoundError:
            continue
        rapm_indexed = rapm_df.set_index('Player ID')

        off_toi = war.total_toi_by_id(prior_season, situation_off)
        for pid, rate in rapm_indexed[off_col].dropna().items():
            toi = float(off_toi.get(pid, 0.0))
            if toi <= 0:
                continue
            off_weighted_sum[pid] = off_weighted_sum.get(pid, 0.0) + rate * toi
            off_weight_total[pid] = off_weight_total.get(pid, 0.0) + toi

        # Defense side is negated here so both sides end up in the same fit-space sign convention
        def_toi = war.total_toi_by_id(prior_season, situation_def)
        for pid, rate in (-rapm_indexed[def_col]).dropna().items():
            toi = float(def_toi.get(pid, 0.0))
            if toi <= 0:
                continue
            def_weighted_sum[pid] = def_weighted_sum.get(pid, 0.0) + rate * toi
            def_weight_total[pid] = def_weight_total.get(pid, 0.0) + toi

    accumulators = {
        'off_weighted_sum': off_weighted_sum, 'off_weight_total': off_weight_total,
        'def_weighted_sum': def_weighted_sum, 'def_weight_total': def_weight_total,
    }
    return accumulators


def apply_prior_stabilization(accumulators: dict, off_stabilization: float, def_stabilization: float) -> dict:
    """
    The final division step of build_rapm_prior, which shrinks each player's TOI-weighted historical average toward 0.0 by the given stabilization minutes; split out so this cheap step can be re-run per candidate value without re-walking any CSVs.

    :param accumulators: A dict from build_rapm_prior_accumulators
    :param off_stabilization: Stabilization TOI (minutes) for the offense side
    :param def_stabilization: Stabilization TOI (minutes) for the defense side
    :return: A dict {'off': {Player ID: prior float}, 'def': {Player ID: prior float}}, the same shape
             as build_rapm_prior's return value
    """
    off_prior = {
        pid: accumulators['off_weighted_sum'][pid] / (total + off_stabilization)
        for pid, total in accumulators['off_weight_total'].items()
    }
    def_prior = {
        pid: accumulators['def_weighted_sum'][pid] / (total + def_stabilization)
        for pid, total in accumulators['def_weight_total'].items()
    }
    prior = {'off': off_prior, 'def': def_prior}
    return prior


def build_rapm_prior(
    season: str, off_col: str, def_col: str, situation_off: str, situation_def: str,
    lookback: int = constants.PRIOR_LOOKBACK_SEASONS,
) -> dict:
    """
    Build a TOI-credibility-weighted cross-season prior for one fit_rapm call's off_coef/def_coef; see this module's header docstring's cross-season prior section.

    :param season: A str representing the season ('YYYY-YYYY')
    :param off_col: The saved rapm_scores column matching this fit's off_coef ('evo_rapm' for the ES
                     fit, 'ppl_rapm' for the PP/PK fit)
    :param def_col: The saved rapm_scores column matching this fit's def_coef ('evd_rapm' or
                     'pkl_rapm'). Both are sign-flipped relative to fit-space by
                     rapm_scores_to_dataframe (saved_value = -def_coef), so this function negates them
                     back to fit-space before weighting/returning
    :param situation_off: The load_save.load_stats_csv situation ('5v5' or '5v4') whose TOI weights
                           off_col's history (see war.total_toi_by_id)
    :param situation_def: The load_save.load_stats_csv situation ('5v5' or '4v5') whose TOI weights
                           def_col's history
    :param lookback: How many prior seasons to pool (default constants.PRIOR_LOOKBACK_SEASONS)
    :return: A dict {'off': {Player ID: prior float}, 'def': {Player ID: prior float}}, both in
             fit-space (matching what fit_rapm's off_coef/def_coef mean), not the saved-CSV's
             sign-flipped def convention
    """
    accumulators = build_rapm_prior_accumulators(season, off_col, def_col, situation_off, situation_def, lookback)
    prior = apply_prior_stabilization(
        accumulators, constants.PRIOR_STABILIZATION_TOI.get(situation_off, 500.0), constants.PRIOR_STABILIZATION_TOI.get(situation_def, 500.0),
    )
    return prior


# ====================================================================================================
# RIDGE FITTING
# ====================================================================================================

def weighted_r2(y_true: np.ndarray, y_pred: np.ndarray, weights: np.ndarray) -> float:
    """
    Weighted out-of-fold R^2, weighting each row the same way it was weighted during fitting (by stint duration).

    :param y_true: An array of actual response values
    :param y_pred: An array of predicted response values
    :param weights: An array of per-row weights (stint duration)
    :return: A float weighted R^2; NaN if the weighted total variance is 0
    """
    weighted_mean = np.average(y_true, weights=weights)
    ss_res = np.sum(weights * (y_true - y_pred) ** 2)
    ss_tot = np.sum(weights * (y_true - weighted_mean) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else np.nan
    return r2


def build_design_matrix(rows_df: pd.DataFrame, context_cols: tuple = ()) -> tuple:
    """
    Build the sparse design matrix for a set of regression rows: one-hot offense/defense player indicators followed by dense context covariate columns if requested and present.

    :param rows_df: A DataFrame of expanded regression rows, optionally with dense context columns attached
    :param context_cols: Names of dense context columns to append as extra design matrix columns.
                          A requested column missing from rows_df is filled with 0.0 (a harmless,
                          zero-variance column) rather than raising, so callers can pass the same
                          context_cols regardless of which contextual overlays actually ran.
    :return: A tuple (X, off_players, def_players), where X is a sparse CSR matrix with one column per
             offense player, one per defense player, then one per context_cols entry (in that order);
             off_players/def_players are the sorted lists giving each block's column order
    """

    # Every distinct player seen in each role gets its own one-hot column, in sorted order
    off_players = sorted(set().union(*rows_df['Off Skaters'])) if len(rows_df) else []
    def_players = sorted(set().union(*rows_df['Def Skaters'])) if len(rows_df) else []
    off_index = {p: i for i, p in enumerate(off_players)}
    def_index = {p: i for i, p in enumerate(def_players)}

    off_rows, off_cols = [], []
    def_rows, def_cols = [], []
    for i, (offs, defs) in enumerate(zip(rows_df['Off Skaters'].to_numpy(), rows_df['Def Skaters'].to_numpy())):
        for p in offs:
            off_rows.append(i)
            off_cols.append(off_index[p])
        for p in defs:
            def_rows.append(i)
            def_cols.append(def_index[p])

    n = len(rows_df)
    X_off = sp.csr_matrix((np.ones(len(off_rows)), (off_rows, off_cols)), shape=(n, len(off_players)))
    X_def = sp.csr_matrix((np.ones(len(def_rows)), (def_rows, def_cols)), shape=(n, len(def_players)))

    blocks = [X_off, X_def]

    # Missing context columns are filled with 0.0 rather than raising, so callers can pass a fixed context_cols
    if context_cols:
        context_arr = rows_df.reindex(columns=list(context_cols), fill_value=0.0).fillna(0.0).to_numpy(dtype=float)
        blocks.append(sp.csr_matrix(context_arr))

    X = sp.hstack(blocks).tocsr()

    design_matrix = (X, off_players, def_players)
    return design_matrix


def fit_rapm(
    rows_df: pd.DataFrame, response_col: str = 'Goals For', context_cols: tuple = (),
    n_splits: int = constants.RAPM_CV_SPLITS, alphas: np.ndarray = constants.ALPHA_GRID,
    off_prior: dict = None, def_prior: dict = None, context_alpha: float = constants.CONTEXT_ALPHA_FIXED,
) -> dict:
    """
    Fit a ridge-regularized adjusted plus-minus model on expanded regression rows: each row's response rate/60 (response_col / stint duration, capped at constants.RATE_CAP) is regressed on offense/defense player indicators plus dense context covariates if given, weighted by stint duration, with alpha chosen by GroupKFold-by-Game-ID CV. Context columns get their own (lighter) fixed penalty via a column-scaling trick (see separate regularization note below). off_prior/def_prior shrink each player's coefficient toward their own cross-season prior instead of 0, via the standard ridge-with-offset identity; with no prior given this is bit-for-bit identical to plain ridge-to-zero.

    Separate regularization for context vs. player columns: player indicator columns (~600-800,
    one-hot and highly collinear) need heavy regularization; context covariates (a handful of dense,
    well-observed columns) need much lighter shrinkage. Implemented via a column-scaling trick:
    context columns are scaled by sqrt(alpha_player / constants.CONTEXT_ALPHA_FIXED) before fitting, equivalent
    to penalising them with constants.CONTEXT_ALPHA_FIXED while penalising player columns with alpha_player
    (if b_c' = b_c * sqrt(alpha_c / alpha_p) and X_c' = X_c * sqrt(alpha_p / alpha_c), then
    X_c @ b_c = X_c' @ b_c' and alpha_p * ||b_c'||^2 = alpha_c * ||b_c||^2). Context coefficients are
    unscaled back after fitting; the scale is per-candidate-alpha in the CV loop so predictions stay
    comparable across alphas.

    :param rows_df: A DataFrame of expanded regression rows, one per team-perspective stint (see
                     expand_es_rows/expand_pp_rows), plus response_col and (if used) context_cols
    :param response_col: Which column to regress on, either 'Goals For' (default, always present) or
                          'xG For' (present only if the stints_df this was expanded from went
                          through attach_xg_to_stints/build_context_features first)
    :param context_cols: Names of dense context columns to include; a column
                          missing from rows_df is treated as all-zero rather than raising, see
                          build_design_matrix
    :param n_splits: Number of GroupKFold splits used for alpha selection
    :param alphas: Ridge alpha grid to search
    :param off_prior: Optional {Player ID: prior coefficient} dict (see build_rapm_prior's 'off' key).
                       A player missing from this dict is treated as a 0.0 prior, the same as
                       before this existed. Context coefficients have no cross-season prior concept
                       and are always shrunk toward 0 regardless of this argument.
    :param def_prior: Optional {Player ID: prior coefficient} dict (see build_rapm_prior's 'def' key),
                       in fit-space (not the sign-flipped saved-CSV convention)
    :param context_alpha: The fixed ridge penalty for context covariates (default constants.CONTEXT_ALPHA_FIXED,
                           see separate regularization note above). Exposed as a parameter so
                           candidate values can be compared via this function's own cv_r2 without
                           monkeypatching this module.
    :return: A dict with keys 'off_coef'/'def_coef' (Player ID -> coefficient dicts), 'context_coef'
             (context column name -> coefficient dict), 'intercept', 'alpha' (the chosen ridge
             penalty), 'cv_r2' (its mean cross-validated weighted R^2), 'cv_r2_grid' (every searched
             alpha's mean CV R^2, for the model report), 'n_rows', 'n_off_players', 'n_def_players',
             'n_off_prior'/'n_def_prior' (how many players off_prior/def_prior actually supplied a
             prior for, for the model report; 0 if no prior was given). All coefficient dicts are
             empty if rows_df is empty.
    """

    if rows_df.empty:
        fit_result = {
            'off_coef': {}, 'def_coef': {}, 'context_coef': {}, 'intercept': 0.0, 'alpha': None,
            'cv_r2': None, 'cv_r2_grid': {}, 'n_rows': 0, 'n_off_players': 0, 'n_def_players': 0,
            'n_off_prior': 0, 'n_def_prior': 0,
        }
    else:
        X, off_players, def_players = build_design_matrix(rows_df, context_cols=context_cols)
        n_off, n_def = len(off_players), len(def_players)
        n_player_cols = n_off + n_def
        use_context_scaling = bool(context_cols) and n_player_cols > 0

        duration_hours = rows_df['Duration'].to_numpy() / 3600.0
        rate = rows_df[response_col].to_numpy() / duration_hours
        y_full = np.clip(rate, 0.0, constants.RATE_CAP)
        weights = duration_hours
        groups = rows_df['Game ID'].to_numpy()

        # Defense in depth: Ridge can't fit through a NaN target (a hard crash, not graceful degradation). attach_xg_to_stints already skips NaN-scored shots, but drop any NaN response row here too (with a visible print) so one bad row degrades this fit instead of crashing the whole multi-season batch run
        valid_response = ~np.isnan(y_full)
        if not valid_response.all():
            X = X[valid_response]
            y_full = y_full[valid_response]
            weights = weights[valid_response]
            groups = groups[valid_response]

        off_prior = off_prior or {}
        def_prior = def_prior or {}
        b0_off = np.array([off_prior.get(p, 0.0) for p in off_players], dtype=float)
        b0_def = np.array([def_prior.get(p, 0.0) for p in def_players], dtype=float)
        b0 = np.concatenate([b0_off, b0_def, np.zeros(len(context_cols))])
        has_prior = bool(np.any(b0 != 0.0))

        # The offset trick (see docstring): fit ordinary shrink-toward-zero ridge on the residual response after subtracting what the prior alone predicts, then add the prior back once at the end
        offset = (X @ b0) if has_prior else np.zeros(len(y_full))
        y_target = y_full - offset

        n_groups = len(np.unique(groups))
        effective_splits = max(2, min(n_splits, n_groups))

        # Cross-validate every candidate alpha, scaling context columns per-alpha to keep their fixed penalty
        cv_scores = {a: [] for a in alphas}
        if n_groups >= 2:
            gkf = GroupKFold(n_splits=effective_splits)
            # Pre-split the full matrix once per fold; re-scale context per alpha inside the inner loop
            for train_idx, test_idx in gkf.split(X, y_target, groups=groups):
                X_train_base, X_test_base = X[train_idx], X[test_idx]
                y_train = y_target[train_idx]
                y_test_full, offset_test = y_full[test_idx], offset[test_idx]
                w_train, w_test = weights[train_idx], weights[test_idx]
                for a in alphas:
                    scale = np.sqrt(float(a) / context_alpha) if use_context_scaling else 1.0

                    # Scale context columns (n_player_cols onward) by `scale`, leaving player columns as-is
                    if not use_context_scaling or scale == 1.0:
                        X_tr = X_train_base
                    else:
                        X_tr = sp.hstack(
                            [X_train_base[:, :n_player_cols], X_train_base[:, n_player_cols:] * scale]
                        ).tocsr()
                    if not use_context_scaling or scale == 1.0:
                        X_te = X_test_base
                    else:
                        X_te = sp.hstack(
                            [X_test_base[:, :n_player_cols], X_test_base[:, n_player_cols:] * scale]
                        ).tocsr()

                    model = Ridge(alpha=a, fit_intercept=True, solver='sparse_cg')
                    model.fit(X_tr, y_train, sample_weight=w_train)
                    pred_full = model.predict(X_te) + offset_test
                    cv_scores[a].append(weighted_r2(y_test_full, pred_full, w_test))

        mean_cv_r2 = {float(a): float(np.nanmean(scores)) if scores else float('nan') for a, scores in cv_scores.items()}
        valid_alphas = {a: r2 for a, r2 in mean_cv_r2.items() if not np.isnan(r2)}
        best_alpha = max(valid_alphas, key=valid_alphas.get) if valid_alphas else float(alphas[len(alphas) // 2])

        # Refit the winning alpha on the full (non-held-out) data for the coefficients actually returned
        best_scale = np.sqrt(best_alpha / context_alpha) if use_context_scaling else 1.0
        if not use_context_scaling or best_scale == 1.0:
            X_final = X
        else:
            X_final = sp.hstack([X[:, :n_player_cols], X[:, n_player_cols:] * best_scale]).tocsr()
        final_model = Ridge(alpha=best_alpha, fit_intercept=True, solver='sparse_cg')
        final_model.fit(X_final, y_target, sample_weight=weights)

        coef_scaled = final_model.coef_ + b0
        off_coef = dict(zip(off_players, coef_scaled[:n_off].tolist()))
        def_coef = dict(zip(def_players, coef_scaled[n_off:n_player_cols].tolist()))

        # Unscale context coefficients: fitted in X_c' = X_c * scale space, so b_c = b_c' * scale
        context_coef_scaled = coef_scaled[n_player_cols:]
        context_coef_unscaled = context_coef_scaled * best_scale if use_context_scaling else context_coef_scaled
        context_coef = (
            dict(zip(context_cols, context_coef_unscaled.tolist())) if context_cols else {}
        )

        fit_result = {
            'off_coef': off_coef, 'def_coef': def_coef, 'context_coef': context_coef,
            'intercept': float(final_model.intercept_), 'alpha': float(best_alpha),
            'cv_r2': mean_cv_r2.get(best_alpha), 'cv_r2_grid': mean_cv_r2,
            'n_rows': int(len(y_full)),
            'n_off_players': len(off_players), 'n_def_players': len(def_players),
            'n_off_prior': len(off_prior), 'n_def_prior': len(def_prior),
        }
    return fit_result


# ====================================================================================================
# SEASON ORCHESTRATION
# ====================================================================================================

def compute_season_rapm(season: str) -> dict:
    """
    Build a season's stints and fit both RAPM regressions (5-on-5 ES, and the joint 5-on-4 PP/PK fit) on goals, no context, no prior. This is the simple sanity-check baseline.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: A dict with keys 'season', 'es' (fit_rapm output), 'pp' (fit_rapm output), 'n_stints', 'n_es_rows', 'n_pp_rows'
    """
    stints_df = build_season_stints(season)
    es_rows = expand_es_rows(stints_df)
    pp_rows = expand_pp_rows(stints_df)

    es_fit = fit_rapm(es_rows)
    pp_fit = fit_rapm(pp_rows)

    result = {
        'season': season, 'es': es_fit, 'pp': pp_fit,
        'n_stints': int(len(stints_df)), 'n_es_rows': int(len(es_rows)), 'n_pp_rows': int(len(pp_rows)),
    }
    return result


def compute_season_rapm_xg(season: str, bundle: dict = None, lookback_seasons: int = constants.PRIOR_LOOKBACK_SEASONS) -> dict:
    """
    The real pipeline: build a season's stints, attach xG and every contextual covariate, then fit both RAPM regressions on xG rate with context covariates and a cross-season prior (if lookback_seasons > 0). Falls back to goal rate for whichever fit has no 'xG For' column.

    :param season: A str representing the season ('YYYY-YYYY')
    :param bundle: A trained xG model bundle (xg_model.load_xg_model()); loaded automatically if
                    not given
    :param lookback_seasons: How many prior seasons' saved RAPM scores feed the cross-season prior
                              (default constants.PRIOR_LOOKBACK_SEASONS); 0 disables the prior entirely
    :return: A dict with keys 'season', 'es' (fit_rapm output, plus 'response_col'), 'pp' (same),
             'n_stints', 'n_es_rows', 'n_pp_rows'
    """
    stints_df = build_season_stints(season)
    stints_df = build_context_features(stints_df, season, bundle=bundle)

    es_rows = expand_es_rows(stints_df)
    pp_rows = expand_pp_rows(stints_df)

    es_response = 'xG For' if 'xG For' in es_rows.columns and not es_rows.empty else 'Goals For'
    pp_response = 'xG For' if 'xG For' in pp_rows.columns and not pp_rows.empty else 'Goals For'

    # Cross-season TOI-weighted priors, skipped entirely if the caller disabled lookback
    es_off_prior, es_def_prior, pp_off_prior, pp_def_prior = {}, {}, {}, {}
    if lookback_seasons > 0:
        es_prior = build_rapm_prior(season, 'evo_rapm', 'evd_rapm', '5v5', '5v5', lookback=lookback_seasons)
        pp_prior = build_rapm_prior(season, 'ppl_rapm', 'pkl_rapm', '5v4', '4v5', lookback=lookback_seasons)
        es_off_prior, es_def_prior = es_prior['off'], es_prior['def']
        pp_off_prior, pp_def_prior = pp_prior['off'], pp_prior['def']

    # The full set of dense context covariate columns compute_season_rapm_xg's fit includes alongside the sparse player indicators, kept fixed so the design matrix's layout is stable
    context_columns = (
        'Off Zone Start O', 'Off Zone Start D', 'Off Score State', 'Off PP Expiry', 'Off Home',
        'Off B2B', 'Def B2B', 'Off PP Start OTF',
        'Off Score×Zone O', 'Off Score×Zone D',
        'Off Expiry×Home', 'Def Expiry×Home',
    )

    es_fit = fit_rapm(
        es_rows, response_col=es_response, context_cols=context_columns,
        off_prior=es_off_prior, def_prior=es_def_prior,
    )
    pp_fit = fit_rapm(
        pp_rows, response_col=pp_response, context_cols=context_columns,
        off_prior=pp_off_prior, def_prior=pp_def_prior,
        alphas=constants.ALPHA_GRID_PP,
    )
    es_fit['response_col'] = es_response
    pp_fit['response_col'] = pp_response

    result = {
        'season': season, 'es': es_fit, 'pp': pp_fit,
        'n_stints': int(len(stints_df)), 'n_es_rows': int(len(es_rows)), 'n_pp_rows': int(len(pp_rows)),
    }
    return result


def rapm_scores_to_dataframe(fit_result: dict, off_name: str, def_name: str) -> pd.DataFrame:
    """
    Convert one fit_rapm() result into a tidy per-player DataFrame, sign-flipping the defense coefficient so higher always means better.

    :param fit_result: A dict returned by fit_rapm
    :param off_name: The output column name for the offense coefficient
    :param def_name: The output column name for the sign-flipped defense coefficient
    :return: A DataFrame with 'Player ID', off_name, and def_name columns
    """
    off_coef, def_coef = fit_result['off_coef'], fit_result['def_coef']
    all_ids = sorted(set(off_coef) | set(def_coef))
    # Sign-flip the defense coefficient so higher is always better, matching the offense side's convention
    records = [
        {'Player ID': pid, off_name: off_coef.get(pid, 0.0), def_name: -def_coef.get(pid, 0.0)}
        for pid in all_ids
    ]
    result = pd.DataFrame(records, columns=['Player ID', off_name, def_name])
    return result


def make_and_save_rapm_scores(season: str) -> None:
    """
    Compute and save a season's RAPM scores (evo_rapm/evd_rapm from the ES fit, ppl_rapm/pkl_rapm from the joint PP/PK fit).

    :param season: A str representing the season ('YYYY-YYYY')
    :return: None
    """
    result = compute_season_rapm(season)

    # ES and PP/PK fits are separate regressions, so merge them into one row per player
    es_df = rapm_scores_to_dataframe(result['es'], 'evo_rapm', 'evd_rapm')
    pp_df = rapm_scores_to_dataframe(result['pp'], 'ppl_rapm', 'pkl_rapm')

    combined = es_df.merge(pp_df, on='Player ID', how='outer')
    combined.insert(0, 'Season', season)

    data_io.save_csv(combined, 'processed_data', 'rapm_scores', f'{season}_rapm_scores.csv')


def make_and_save_rapm_scores_xg(season: str, bundle: dict = None, lookback_seasons: int = constants.PRIOR_LOOKBACK_SEASONS) -> None:
    """
    The xG + contextual-covariates counterpart to make_and_save_rapm_scores, with the same output shape/location; meant to supersede the goals-only version once a season has shot-event/faceoff/schedule data scraped.

    :param season: A str representing the season ('YYYY-YYYY')
    :param bundle: An optional pre-loaded xG model bundle, passed through to compute_season_rapm_xg
    :param lookback_seasons: How many prior seasons' saved RAPM scores feed the cross-season prior; 0 disables the prior
    :return: None
    """
    result = compute_season_rapm_xg(season, bundle=bundle, lookback_seasons=lookback_seasons)

    es_df = rapm_scores_to_dataframe(result['es'], 'evo_rapm', 'evd_rapm')
    pp_df = rapm_scores_to_dataframe(result['pp'], 'ppl_rapm', 'pkl_rapm')

    combined = es_df.merge(pp_df, on='Player ID', how='outer')
    combined.insert(0, 'Season', season)

    data_io.save_csv(combined, 'processed_data', 'rapm_scores', f'{season}_rapm_scores.csv')
