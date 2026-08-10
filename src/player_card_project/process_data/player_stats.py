# ====================================================================================================
# FUNCTIONS FOR GETTING ALL PLAYER STATS TOGETHER
# ====================================================================================================

# Imports
import numpy as np
import pandas as pd

from player_card_project import constants
from player_card_project import data_io
from player_card_project.process_data import rapm
from player_card_project.process_data import xgoals as xg

DATA_DIR = constants.DATA_DIR

# Skater situation buckets, mapped to the matching per-stint 'Situation' string from expand_player_stints
skater_situation_filters = {'all': None, '5v5': '5v5', '5v4': '5v4', '4v5': '4v5'}


# ====================================================================================================
# STINT EXPANSION
# ====================================================================================================

def stint_situation(n_own: int, n_opp: int, own_goalie: bool, opp_goalie: bool) -> str:
    """
    Classify a stint's situation from one team's own perspective.

    :param n_own: The int number of the own team's skaters on ice
    :param n_opp: The int number of the opposing team's skaters on ice
    :param own_goalie: Whether the own team's goalie is on ice
    :param opp_goalie: Whether the opposing team's goalie is on ice
    :return: A str situation label
    """
    if not opp_goalie:
        label = 'EN_for'
    elif not own_goalie:
        label = 'EN_against'
    else:
        label = f'{n_own}v{n_opp}'
    return label


def attach_sog_to_stints(stints_df: pd.DataFrame, season: str) -> pd.DataFrame:
    """
    Sum each stint's shots-on-goal per team, adding 'Team A SOG'/'Team B SOG' columns.

    :param stints_df: A season's stints DataFrame
    :param season: A str representing the season ('YYYY-YYYY')
    :return: The stints DataFrame with 'Team A SOG'/'Team B SOG' columns added
    """
    out = stints_df.copy()
    if out.empty:
        out['Team A SOG'] = pd.Series(dtype=float)
        out['Team B SOG'] = pd.Series(dtype=float)
    else:
        shots_df = data_io.load_shot_events_csv(season)

        # Only goals and saved shots count as shots-on-goal
        shots_df = shots_df[shots_df['Event Type'].isin(('goal', 'shot-on-goal'))].copy()

        # Drop any event with a malformed/missing time string before converting to seconds
        time_pattern = r'^\d{1,2}:\d{2}$'
        valid_time = shots_df['Time'].astype(str).str.match(time_pattern, na=False)
        shots_df = shots_df[valid_time].copy()

        if shots_df.empty:
            out['Team A SOG'] = 0.0
            out['Team B SOG'] = 0.0
        else:
            shots_df['Sec'] = shots_df['Time'].apply(rapm.time_to_seconds)

            out = out.reset_index(drop=True)
            team_a_sog = np.zeros(len(out))
            team_b_sog = np.zeros(len(out))

            # Group shots by (Game ID, Period) for fast per-period lookup below
            sog_by_period = {key: grp for key, grp in shots_df.groupby(['Game ID', 'Period'])}

            # Assign each shot to whichever stint was on the ice at its timestamp
            for (game_id, period), period_df in out.groupby(['Game ID', 'Period']):
                period_shots = sog_by_period.get((game_id, period))
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

                for s_sec, s_team in zip(shot_secs, shot_teams):
                    pos = np.searchsorted(sorted_starts, s_sec, side='right') - 1
                    pos = max(0, min(pos, last_pos))
                    # Tie-break: a shot on the exact stint boundary goes to the ending stint, only when the two stints actually touch
                    if pos > 0 and s_sec == sorted_starts[pos] and sorted_ends[pos - 1] == s_sec:
                        pos -= 1
                    elif not (pos == last_pos or s_sec < sorted_ends[pos]):
                        continue

                    stint_idx = sorted_local_idx[pos]
                    if s_team == team_a:
                        team_a_sog[stint_idx] += 1
                    elif s_team == team_b:
                        team_b_sog[stint_idx] += 1

            out['Team A SOG'] = team_a_sog
            out['Team B SOG'] = team_b_sog
    return out


def expand_player_stints(stints_df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand each stint into one row per on-ice skater, carrying their own team's GF/xGF/SOGF and the opponent's against, plus situation and zone-start flags.

    :param stints_df: A season's stints DataFrame
    :return: A DataFrame with one row per on-ice skater per stint
    """

    # Not every stints_df build has xG/SOG/zone-start columns attached yet
    has_xg = 'Team A xG' in stints_df.columns
    has_sog = 'Team A SOG' in stints_df.columns
    has_zone = 'Team A Zone O' in stints_df.columns

    records = []
    # Walk each stint from both teams' perspectives
    for _, row in stints_df.iterrows():
        for side in ('A', 'B'):
            other = 'B' if side == 'A' else 'A'
            skaters = row[f'Team {side} Skaters']
            if not skaters:
                continue

            own_n, opp_n = len(skaters), len(row[f'Team {other} Skaters'])
            own_goalie = row[f'Team {side} Goalie On']
            opp_goalie = row[f'Team {other} Goalie On']
            situation = stint_situation(own_n, opp_n, own_goalie, opp_goalie)

            gf = row[f'Team {side} Goals']
            ga = row[f'Team {other} Goals']
            xgf = row[f'Team {side} xG'] if has_xg else 0.0
            xga = row[f'Team {other} xG'] if has_xg else 0.0
            sogf = row[f'Team {side} SOG'] if has_sog else 0.0
            soga = row[f'Team {other} SOG'] if has_sog else 0.0
            zone_o = row[f'Team {side} Zone O'] if has_zone else 0
            zone_d = row[f'Team {side} Zone D'] if has_zone else 0
            zone_n = row[f'Team {side} Zone N'] if has_zone else 0

            team_name = row[f'Team {side}']
            game_id = row['Game ID']
            duration = row['Duration']

            # Emit one row per skater on this side of the stint
            for pid in skaters:
                records.append({
                    'Game ID': game_id, 'Player ID': pid, 'Team': team_name,
                    'Situation': situation, 'Duration': duration,
                    'GF': gf, 'GA': ga, 'xGF': xgf, 'xGA': xga, 'SOGF': sogf, 'SOGA': soga,
                    'Zone O': zone_o, 'Zone D': zone_d, 'Zone N': zone_n,
                })

    player_stint_columns = [
        'Game ID', 'Player ID', 'Team', 'Situation', 'Duration',
        'GF', 'GA', 'xGF', 'xGA', 'SOGF', 'SOGA', 'Zone O', 'Zone D', 'Zone N',
    ]

    result = pd.DataFrame(records, columns=player_stint_columns)
    return result


def expand_goalie_stints(stints_df: pd.DataFrame) -> pd.DataFrame:
    """
    Expand each stint into one row per goalie actually in net, crediting them with the stint's duration in their own team's situation.

    :param stints_df: A season's stints DataFrame
    :return: A DataFrame with one row per goalie per stint
    """
    records = []
    # Walk each stint from both teams' perspectives
    for _, row in stints_df.iterrows():
        for side in ('A', 'B'):
            other = 'B' if side == 'A' else 'A'
            goalie_id = row[f'Team {side} Goalie ID']
            if goalie_id is None or pd.isna(goalie_id):
                continue

            own_n, opp_n = len(row[f'Team {side} Skaters']), len(row[f'Team {other} Skaters'])
            own_goalie = row[f'Team {side} Goalie On']
            opp_goalie = row[f'Team {other} Goalie On']
            situation = stint_situation(own_n, opp_n, own_goalie, opp_goalie)

            records.append({
                'Game ID': row['Game ID'], 'Player ID': goalie_id, 'Team': row[f'Team {side}'],
                'Situation': situation, 'Duration': row['Duration'],
            })

    goalie_stint_columns = ['Game ID', 'Player ID', 'Team', 'Situation', 'Duration']
    goalie_stints = pd.DataFrame(records, columns=goalie_stint_columns)

    return goalie_stints


def filter_by_situation(df: pd.DataFrame, situation: str, filters: dict) -> pd.DataFrame:
    """
    Restrict a stint/event DataFrame to one situation bucket via its 'Situation' column.

    :param df: A stint/event DataFrame
    :param situation: A str situation bucket key (e.g. 'all', '5v5')
    :param filters: A dict mapping situation bucket key to the target 'Situation' value (or None for no filtering)
    :return: The filtered DataFrame
    """
    target = filters.get(situation)
    if target is None:
        result = df
    else:
        result = df[df['Situation'] == target]
    return result


# ====================================================================================================
# SKATER TOI / GP
# ====================================================================================================

def compute_skater_gp(season: str) -> pd.Series:
    """
    Every skater's games-played count for a season, from boxscore-derived per-game TOI (not the shift chart, which has real NHL-side gaps), falling back to shifts if no boxscore data exists yet.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: A Series of GP counts indexed by Player ID
    """
    result = None

    # Prefer boxscore-derived TOI
    try:
        boxscore_df = data_io.load_boxscore_skater_toi_csv(season)
        if not boxscore_df.empty:
            work = boxscore_df[['Player ID', 'Game ID']].dropna().copy()
            work['Player ID'] = work['Player ID'].astype(int)
            result = work.drop_duplicates().groupby('Player ID')['Game ID'].nunique()
    except FileNotFoundError:
        pass

    if result is None:
        # Fall back to the shift chart if boxscore data isn't available
        shifts_df = data_io.load_shifts_csv(season)

        if shifts_df.empty:
            result = pd.Series(dtype=int)
        else:
            work = shifts_df[['Player ID', 'Game ID']].dropna().copy()
            work['Player ID'] = work['Player ID'].astype(int)
            result = work.drop_duplicates().groupby('Player ID')['Game ID'].nunique()

    return result


def compute_skater_toi(player_stints_df: pd.DataFrame, situation: str, season: str = None) -> pd.Series:
    """
    Every skater's TOI (minutes) for one situation bucket.

    :param player_stints_df: A per-skater expanded stints DataFrame from expand_player_stints
    :param situation: A str situation bucket key ('all', '5v5', '5v4', or '4v5')
    :param season: An optional str season ('YYYY-YYYY'), used to prefer boxscore-derived totals for 'all'
    :return: A Series of TOI minutes indexed by Player ID
    """
    result = None

    # 'all' situation prefers the boxscore-derived total when it's available
    if situation == 'all' and season is not None:
        try:
            boxscore_df = data_io.load_boxscore_skater_toi_csv(season)
            if not boxscore_df.empty:
                work = boxscore_df[['Player ID', 'TOI']].dropna(subset=['Player ID']).copy()
                work['Player ID'] = work['Player ID'].astype(int)
                boxscore_result = work.groupby('Player ID')['TOI'].sum()
                if not boxscore_result.empty:
                    result = boxscore_result
        except FileNotFoundError:
            pass

    if result is None:
        if player_stints_df.empty:
            result = pd.Series(dtype=float)
        else:
            # Otherwise (or for 5v5/5v4/4v5), derive TOI from the expanded stints
            filtered = filter_by_situation(player_stints_df, situation, skater_situation_filters)
            if filtered.empty:
                result = pd.Series(dtype=float)
            else:
                result = filtered.groupby('Player ID')['Duration'].sum() / 60.0

    return result


# ====================================================================================================
# SKATER ON-ICE STATS
# ====================================================================================================

def compute_skater_onice_stats(player_stints_df: pd.DataFrame, situation: str) -> pd.DataFrame:
    """
    Every skater's on-ice GF%, xGF%, and PDO (on-ice shooting% + save%, as fractions) for one situation bucket.

    :param player_stints_df: A per-skater expanded stints DataFrame from expand_player_stints
    :param situation: A str situation bucket key ('all', '5v5', '5v4', or '4v5')
    :return: A DataFrame of GF%/xGF%/PDO indexed by Player ID
    """
    cols = ['GF%', 'xGF%', 'PDO']
    if player_stints_df.empty:
        result = pd.DataFrame(columns=cols)
    else:
        filtered = filter_by_situation(player_stints_df, situation, skater_situation_filters)
        if filtered.empty:
            result = pd.DataFrame(columns=cols)
        else:
            # Sum GF/GA/xGF/xGA/SOGF/SOGA per player across their filtered stints
            agg = filtered.groupby('Player ID').agg(
                GF=('GF', 'sum'), GA=('GA', 'sum'), xGF=('xGF', 'sum'), xGA=('xGA', 'sum'),
                SOGF=('SOGF', 'sum'), SOGA=('SOGA', 'sum'),
            )

            gf_total = agg['GF'] + agg['GA']
            xgf_total = agg['xGF'] + agg['xGA']

            result = pd.DataFrame(index=agg.index)
            result['GF%'] = np.where(gf_total > 0, agg['GF'] / gf_total * 100, np.nan)
            result['xGF%'] = np.where(xgf_total > 0, agg['xGF'] / xgf_total * 100, np.nan)

            # On-ice shooting% and save% while this player was on the ice
            onice_sh_pct = np.where(agg['SOGF'] > 0, agg['GF'] / agg['SOGF'], 0.0)
            onice_sv_pct = np.where(agg['SOGA'] > 0, 1 - (agg['GA'] / agg['SOGA']), 0.0)
            result['PDO'] = onice_sh_pct + onice_sv_pct

            result = result[cols]
    return result


# ====================================================================================================
# INDIVIDUAL EVENT STATS
# ====================================================================================================

def compute_skater_goals_assists(season: str, situation: str, stints_df: pd.DataFrame) -> pd.DataFrame:
    """
    Every skater's individual Goals, Total/First/Second Assists, and Total Points for one situation bucket, from shot_events.csv and goals.csv.

    :param season: A str representing the season ('YYYY-YYYY')
    :param situation: A str situation bucket key ('all', '5v5', '5v4', or '4v5')
    :param stints_df: A season's stints DataFrame, used to strength-tag events
    :return: A DataFrame of goals/assists/points indexed by Player ID
    """
    cols = ['Goals', 'Total Assists', 'First Assists', 'Second Assists', 'Total Points']

    # Goals, from shot_events.csv
    goals_series = pd.Series(dtype=int)

    shots_df = data_io.load_shot_events_csv(season)
    shots_df = shots_df[shots_df['Event Type'] == 'goal'].dropna(subset=['Shooter Player ID']).copy()
    if not shots_df.empty:
        target = skater_situation_filters.get(situation)
        # Only strength-tag when a real filter applies ('all' counts every goal regardless)
        if target is not None:
            shots_df = xg.attach_strength_state_from_stints(shots_df, stints_df)
            shots_df = shots_df[shots_df['Strength'] == target]
        shots_df = shots_df.copy()
        shots_df['Shooter Player ID'] = shots_df['Shooter Player ID'].astype(int)
        goals_series = shots_df.groupby('Shooter Player ID').size()

    # Assists, from goals.csv
    first_assist_series = pd.Series(dtype=int)
    second_assist_series = pd.Series(dtype=int)

    goals_df = data_io.load_goals_csv(season).copy()
    if not goals_df.empty and not stints_df.empty:
        goals_df = xg.attach_strength_state_from_stints(goals_df, stints_df)
        target = skater_situation_filters.get(situation)
        if target is not None:
            goals_df = goals_df[goals_df['Strength'] == target]

        first = goals_df.dropna(subset=['Assist 1 Player ID']).copy()
        if not first.empty:
            first['Assist 1 Player ID'] = first['Assist 1 Player ID'].astype(int)
            first_assist_series = first.groupby('Assist 1 Player ID').size()

        second = goals_df.dropna(subset=['Assist 2 Player ID']).copy()
        if not second.empty:
            second['Assist 2 Player ID'] = second['Assist 2 Player ID'].astype(int)
            second_assist_series = second.groupby('Assist 2 Player ID').size()

    all_ids = goals_series.index.union(first_assist_series.index).union(second_assist_series.index)
    if len(all_ids) == 0:
        result = pd.DataFrame(columns=cols)
    else:
        result = pd.DataFrame(index=all_ids)
        result['Goals'] = goals_series.reindex(all_ids).fillna(0).astype(int)
        result['First Assists'] = first_assist_series.reindex(all_ids).fillna(0).astype(int)
        result['Second Assists'] = second_assist_series.reindex(all_ids).fillna(0).astype(int)
        result['Total Assists'] = result['First Assists'] + result['Second Assists']
        result['Total Points'] = result['Goals'] + result['Total Assists']
        result.index.name = 'Player ID'
        result = result[cols]
    return result


def compute_skater_possession_events(season: str, situation: str, stints_df: pd.DataFrame) -> pd.DataFrame:
    """
    Every skater's individual Hits, Hits Taken, Giveaways, and Takeaways for one situation bucket, from possession_events.csv.

    :param season: A str representing the season ('YYYY-YYYY')
    :param situation: A str situation bucket key ('all', '5v5', '5v4', or '4v5')
    :param stints_df: A season's stints DataFrame, used to strength-tag events
    :return: A DataFrame of hits/giveaways/takeaways indexed by Player ID
    """
    cols = ['Hits', 'Hits Taken', 'Giveaways', 'Takeaways']

    events_df = data_io.load_possession_events_csv(season).copy()

    if events_df.empty or stints_df.empty:
        result = pd.DataFrame(columns=cols)
    else:
        events_df = xg.attach_strength_state_from_stints(events_df, stints_df)
        target = skater_situation_filters.get(situation)
        if target is not None:
            events_df = events_df[events_df['Strength'] == target]

        # Split possession events into the four individual event types this stat table tracks
        hits = events_df[events_df['Event Type'] == 'hit'].dropna(subset=['Player ID']).copy()
        hits_taken = events_df[events_df['Event Type'] == 'hit'].dropna(subset=['Hittee Player ID']).copy()
        giveaways = events_df[events_df['Event Type'] == 'giveaway'].dropna(subset=['Player ID']).copy()
        takeaways = events_df[events_df['Event Type'] == 'takeaway'].dropna(subset=['Player ID']).copy()

        hits_series = pd.Series(dtype=int)
        if not hits.empty:
            hits['Player ID'] = hits['Player ID'].astype(int)
            hits_series = hits.groupby('Player ID').size()

        hits_taken_series = pd.Series(dtype=int)
        if not hits_taken.empty:
            hits_taken['Hittee Player ID'] = hits_taken['Hittee Player ID'].astype(int)
            hits_taken_series = hits_taken.groupby('Hittee Player ID').size()

        giveaways_series = pd.Series(dtype=int)
        if not giveaways.empty:
            giveaways['Player ID'] = giveaways['Player ID'].astype(int)
            giveaways_series = giveaways.groupby('Player ID').size()

        takeaways_series = pd.Series(dtype=int)
        if not takeaways.empty:
            takeaways['Player ID'] = takeaways['Player ID'].astype(int)
            takeaways_series = takeaways.groupby('Player ID').size()

        all_ids = (
            hits_series.index.union(hits_taken_series.index)
            .union(giveaways_series.index).union(takeaways_series.index)
        )
        if len(all_ids) == 0:
            result = pd.DataFrame(columns=cols)
        else:
            result = pd.DataFrame(index=all_ids)
            result['Hits'] = hits_series.reindex(all_ids).fillna(0).astype(int)
            result['Hits Taken'] = hits_taken_series.reindex(all_ids).fillna(0).astype(int)
            result['Giveaways'] = giveaways_series.reindex(all_ids).fillna(0).astype(int)
            result['Takeaways'] = takeaways_series.reindex(all_ids).fillna(0).astype(int)
            result.index.name = 'Player ID'
    return result


def compute_skater_penalties(season: str, situation: str, stints_df: pd.DataFrame) -> pd.DataFrame:
    """
    Every skater's Penalties Drawn and Total Penalties (taken) for one situation bucket, from penalty_events.csv (2-, 4-, 5-min penalties only).

    :param season: A str representing the season ('YYYY-YYYY')
    :param situation: A str situation bucket key ('all', '5v5', '5v4', or '4v5')
    :param stints_df: A season's stints DataFrame, used to strength-tag events
    :return: A DataFrame of penalties drawn/taken indexed by Player ID
    """
    cols = ['Penalties Drawn', 'Total Penalties']

    penalties_df = data_io.load_penalty_events_csv(season).copy()

    if penalties_df.empty or stints_df.empty:
        result = pd.DataFrame(columns=cols)
    else:
        # Only 2-/4-/5-minute penalties have a single attributable individual player
        penalties_df = penalties_df[penalties_df['Duration'].isin([2, 4, 5])].copy()
        if penalties_df.empty:
            result = pd.DataFrame(columns=cols)
        else:
            penalties_df = xg.attach_strength_state_from_stints(penalties_df, stints_df)
            target = skater_situation_filters.get(situation)
            if target is not None:
                penalties_df = penalties_df[penalties_df['Strength'] == target]

            # Split into penalties drawn vs. penalties taken
            drawn = penalties_df.dropna(subset=['Drew Player ID']).copy()
            taken = penalties_df.dropna(subset=['Penalty Player ID']).copy()

            drawn_series = pd.Series(dtype=int)
            if not drawn.empty:
                drawn['Drew Player ID'] = drawn['Drew Player ID'].astype(int)
                drawn_series = drawn.groupby('Drew Player ID').size()

            taken_series = pd.Series(dtype=int)
            if not taken.empty:
                taken['Penalty Player ID'] = taken['Penalty Player ID'].astype(int)
                taken_series = taken.groupby('Penalty Player ID').size()

            all_ids = drawn_series.index.union(taken_series.index)
            if len(all_ids) == 0:
                result = pd.DataFrame(columns=cols)
            else:
                result = pd.DataFrame(index=all_ids)
                result['Penalties Drawn'] = drawn_series.reindex(all_ids).fillna(0).astype(int)
                result['Total Penalties'] = taken_series.reindex(all_ids).fillna(0).astype(int)
                result.index.name = 'Player ID'
    return result


def compute_skater_zone_starts(player_stints_df: pd.DataFrame, situation: str) -> pd.DataFrame:
    """
    Every skater's Off./Neu./Def. Zone Start counts for one situation bucket, from expand_player_stints' zone-start columns.

    :param player_stints_df: A per-skater expanded stints DataFrame from expand_player_stints
    :param situation: A str situation bucket key ('all', '5v5', '5v4', or '4v5')
    :return: A DataFrame of zone-start counts indexed by Player ID
    """
    cols = ['Off. Zone Starts', 'Neu. Zone Starts', 'Def. Zone Starts']
    if player_stints_df.empty:
        result = pd.DataFrame(columns=cols)
    else:
        filtered = filter_by_situation(player_stints_df, situation, skater_situation_filters)
        if filtered.empty:
            result = pd.DataFrame(columns=cols)
        else:
            # Sum zone-start flags per player across their filtered stints
            agg = filtered.groupby('Player ID').agg(
                **{
                    'Off. Zone Starts': ('Zone O', 'sum'),
                    'Neu. Zone Starts': ('Zone N', 'sum'),
                    'Def. Zone Starts': ('Zone D', 'sum'),
                }
            )
            result = agg[cols].astype(int)
    return result


# ====================================================================================================
# GOALIE STATS
# ====================================================================================================

def compute_goalie_gp(season: str, goalie_ids: set) -> pd.Series:
    """
    Every goalie's games-played count for a season, restricted to known goalie IDs, from boxscore data (falls back to shifts).

    :param season: A str representing the season ('YYYY-YYYY')
    :param goalie_ids: A set of int goalie Player IDs to restrict the result to
    :return: A Series of GP counts indexed by Player ID
    """
    result = None

    # Prefer boxscore-derived TOI
    try:
        boxscore_df = data_io.load_boxscore_goalie_stats_csv(season)
        if not boxscore_df.empty:
            work = boxscore_df[['Player ID', 'Game ID', 'TOI']].dropna(subset=['Player ID', 'Game ID']).copy()
            work['Player ID'] = work['Player ID'].astype(int)
            work = work[work['Player ID'].isin(goalie_ids)]
            # Drop dressed-but-never-played rows (TOI == 0) so a healthy scratch backup isn't counted as a game played
            work = work[work['TOI'] > 0]
            if not work.empty:
                result = work.drop_duplicates(subset=['Player ID', 'Game ID']).groupby('Player ID')['Game ID'].nunique()
    except FileNotFoundError:
        pass

    if result is None:
        # Fall back to the shift chart if boxscore data isn't available yet
        shifts_df = data_io.load_shifts_csv(season)

        if shifts_df.empty:
            result = pd.Series(dtype=int)
        else:
            work = shifts_df[['Player ID', 'Game ID']].dropna().copy()
            work['Player ID'] = work['Player ID'].astype(int)
            work = work[work['Player ID'].isin(goalie_ids)]
            if work.empty:
                result = pd.Series(dtype=int)
            else:
                result = work.drop_duplicates().groupby('Player ID')['Game ID'].nunique()

    return result


def compute_goalie_toi(season: str, situation: str, stints_df: pd.DataFrame = None) -> pd.Series:
    """
    Every goalie's TOI (minutes) for one situation bucket, from expand_goalie_stints.

    :param season: A str representing the season ('YYYY-YYYY')
    :param situation: A str situation bucket key ('all', '5v5', or '4v5')
    :param stints_df: An optional pre-built season stints DataFrame; built from scratch if not given
    :return: A Series of TOI minutes indexed by Player ID
    """
    # Goalie situation buckets, from the goalie's own team's perspective
    goalie_situation_filters = {'all': None, '5v5': '5v5', '4v5': '4v5'}

    # Build stints from scratch if not already provided by a shared bundle
    if stints_df is None:
        stints_df = rapm.build_season_stints(season)
    goalie_stints = expand_goalie_stints(stints_df)

    if goalie_stints.empty:
        result = pd.Series(dtype=float)
    else:
        target = goalie_situation_filters.get(situation)
        if target is not None:
            goalie_stints = goalie_stints[goalie_stints['Situation'] == target]
        if goalie_stints.empty:
            result = pd.Series(dtype=float)
        else:
            result = goalie_stints.groupby('Player ID')['Duration'].sum() / 60.0

    return result


def danger(xg_val: float) -> str:
    """
    Bucket a shot's predicted xG into this project's own HD/MD/LD danger tier.

    :param xg_val: The float predicted xG value for a shot
    :return: A str danger tier ('HD', 'MD', or 'LD')
    """
    if xg_val >= constants.HIGH_DANGER_XG_THRESHOLD:
        tier = 'HD'
    elif xg_val >= constants.MEDIUM_DANGER_XG_THRESHOLD:
        tier = 'MD'
    else:
        tier = 'LD'
    return tier


def compute_goalie_shot_stats(season: str, situation: str, stints_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Every goalie's Shots Against/Saves/Goals Against/SV%/GAA/xG Against, HD/MD/LD danger-zone splits, and Rebound Attempts Against, for one situation bucket.

    :param season: A str representing the season ('YYYY-YYYY')
    :param situation: A str situation bucket key ('all', '5v5', or '4v5')
    :param stints_df: An optional pre-built season stints DataFrame, used to strength-tag shots
    :return: A DataFrame of goalie shot stats indexed by Player ID
    """
    cols = [
        'Shots Against', 'Saves', 'Goals Against', 'SV%', 'GAA', 'xG Against',
        'HD Shots Against', 'HD Saves', 'HD Goals Against', 'HD xG Against',
        'MD Shots Against', 'MD Saves', 'MD Goals Against', 'MD xG Against',
        'LD Shots Against', 'LD Saves', 'LD Goals Against', 'LD xG Against',
        'Rebound Attempts Against', 'Rebound xG Against',
    ]

    strength_by_situation = {'all': None, '5v5': '5v5', '4v5': '5v4'}
    target_strength = strength_by_situation.get(situation)

    shots_df = data_io.load_shot_events_csv(season)

    # Restrict to unblocked shot attempts against a known goalie
    shots_df = shots_df[shots_df['Event Type'].isin(constants.UNBLOCKED_SHOT_EVENTS)].copy()
    shots_df = shots_df.dropna(subset=['Goalie Player ID']).copy()
    if shots_df.empty:
        result = pd.DataFrame(columns=cols)
    else:
        shots_df['Goalie Player ID'] = shots_df['Goalie Player ID'].astype(int)
        shots_df = xg.engineer_features(shots_df)
        if stints_df is not None:
            shots_df = xg.attach_strength_state_from_stints(shots_df, stints_df)
        else:
            shots_df = xg.attach_strength_state(shots_df, season)

        if target_strength is not None:
            shots_df = shots_df[shots_df['Strength'] == target_strength]

        if shots_df.empty:
            result = pd.DataFrame(columns=cols)
        else:
            # Predict xG for each shot using the trained model
            bundle = xg.load_xg_model()
            shots_df = shots_df.reset_index(drop=True)
            shots_df['xG'] = xg.predict_xg(shots_df, season=season, bundle=bundle)

            shots_df['Goal'] = (shots_df['Event Type'] == 'goal').astype(int)
            shots_df['SOG'] = (shots_df['Event Type'].isin(('goal', 'shot-on-goal'))).astype(int)

            # Bucket each shot into HD/MD/LD danger tiers
            shots_df['Danger'] = shots_df['xG'].apply(danger)
            # xG of this shot if it was itself a rebound, so rebound_score can weight rebounds by danger
            shots_df['Rebound xG'] = shots_df['xG'] * shots_df['Is Rebound']

            # Only shots-on-goal count toward Shots Against/Saves; xG-based columns use every unblocked attempt
            sog_df = shots_df[shots_df['SOG'] == 1]

            agg = shots_df.groupby('Goalie Player ID').agg(
                xG_Against=('xG', 'sum'),
                Rebound_Attempts_Against=('Is Rebound', 'sum'),
                Rebound_xG_Against=('Rebound xG', 'sum'),
            )

            sog_agg = sog_df.groupby('Goalie Player ID').agg(
                Shots_Against=('SOG', 'sum'),
                Goals_Against=('Goal', 'sum'),
            )

            # Assemble HD/MD/LD shot/goal splits per goalie
            danger_agg = (
                sog_df.groupby(['Goalie Player ID', 'Danger'])
                .agg(Shots=('SOG', 'sum'), Goals=('Goal', 'sum'))
                .unstack(fill_value=0)
            )

            # Per-tier xG Against comes from shots_df, not sog_df, so it sums to the overall 'xG Against' total
            danger_xg_agg = (
                shots_df.groupby(['Goalie Player ID', 'Danger'])
                .agg(xG=('xG', 'sum'))
                .unstack(fill_value=0)
            )

            result = agg.join(sog_agg, how='outer').fillna(0.0)
            result['Saves'] = result['Shots_Against'] - result['Goals_Against']
            result['SV%'] = np.where(
                result['Shots_Against'] > 0, result['Saves'] / result['Shots_Against'], np.nan
            )

            for tier in ('HD', 'MD', 'LD'):
                shots_col = ('Shots', tier)
                goals_col = ('Goals', tier)
                xg_col = ('xG', tier)
                result[f'{tier} Shots Against'] = danger_agg[shots_col].reindex(result.index).fillna(0) if shots_col in danger_agg.columns else 0
                result[f'{tier} Goals Against'] = danger_agg[goals_col].reindex(result.index).fillna(0) if goals_col in danger_agg.columns else 0
                result[f'{tier} Saves'] = result[f'{tier} Shots Against'] - result[f'{tier} Goals Against']
                result[f'{tier} xG Against'] = danger_xg_agg[xg_col].reindex(result.index).fillna(0) if xg_col in danger_xg_agg.columns else 0

            # GAA needs TOI
            toi = compute_goalie_toi(season, situation, stints_df=stints_df)
            toi_hours = toi.reindex(result.index).fillna(0.0) / 60.0
            result['GAA'] = np.where(toi_hours > 0, result['Goals_Against'] / toi_hours, np.nan)

            result = result.rename(columns={
                'Shots_Against': 'Shots Against', 'Goals_Against': 'Goals Against',
                'xG_Against': 'xG Against', 'Rebound_Attempts_Against': 'Rebound Attempts Against',
                'Rebound_xG_Against': 'Rebound xG Against',
            })
            result.index.name = 'Player ID'

            for col in cols:
                if col not in result.columns:
                    result[col] = 0
            result = result[cols]
    return result


def compute_goalie_game_gsax(season: str) -> pd.DataFrame:
    """
    Every goalie's GSAx (predicted xG Against minus actual Goals Against) per individual game, used by scoring to classify each start's quality.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: A DataFrame of per-game goalie GSAx, one row per (Player ID, Game ID)
    """
    cols = ['Player ID', 'Game ID', 'Shots Against', 'Goals Against', 'xG Against', 'GSAx']

    shots_df = data_io.load_shot_events_csv(season)

    shots_df = shots_df[shots_df['Event Type'].isin(constants.UNBLOCKED_SHOT_EVENTS)].copy()
    shots_df = shots_df.dropna(subset=['Goalie Player ID']).copy()
    if shots_df.empty:
        result = pd.DataFrame(columns=cols)
    else:
        bundle = xg.load_xg_model()
        shots_df['Goalie Player ID'] = shots_df['Goalie Player ID'].astype(int)
        shots_df = shots_df.reset_index(drop=True)
        shots_df['xG'] = xg.predict_xg(shots_df, season=season, bundle=bundle)
        shots_df['Goal'] = (shots_df['Event Type'] == 'goal').astype(int)
        shots_df['SOG'] = shots_df['Event Type'].isin(('goal', 'shot-on-goal')).astype(int)

        # Aggregate shots/goals/xG per goalie per individual game
        agg = shots_df.groupby(['Goalie Player ID', 'Game ID']).agg(
            **{
                'Shots Against': ('SOG', 'sum'),
                'Goals Against': ('Goal', 'sum'),
                'xG Against': ('xG', 'sum'),
            }
        ).reset_index().rename(columns={'Goalie Player ID': 'Player ID'})

        agg['GSAx'] = agg['xG Against'] - agg['Goals Against']
        result = agg[cols]
    return result


# ====================================================================================================
# ASSEMBLE ALL STATS
# ====================================================================================================

def compute_skater_stats(
    season: str, position: str, situation: str,
    stints_df: pd.DataFrame = None, player_stints_df: pd.DataFrame = None, ixg_df: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    Assemble one (season, position, situation) skater stats table, matching load_save.load_stats_csv's expected file shape.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str position ('F' or 'D') to build the table for
    :param situation: A str situation bucket key ('all', '5v5', '5v4', or '4v5')
    :param stints_df: An optional pre-built season stints DataFrame; built from scratch if not given
    :param player_stints_df: An optional pre-built per-skater expanded stints DataFrame; built from stints_df if not given
    :param ixg_df: An optional pre-computed individual xG DataFrame; computed from stints_df/bundle if not given
    :return: A DataFrame of skater stats, one row per Player ID
    """
    # Load once here so it's shared by the stint-building fallback below and by ixG further down
    bundle = xg.load_xg_model()

    # Build stints from scratch if not already provided by a shared bundle
    if stints_df is None:
        stints_df = rapm.build_season_stints(season)
        stints_df = rapm.attach_xg_to_stints(stints_df, season, bundle=bundle)
        stints_df = attach_sog_to_stints(stints_df, season)
        stints_df = rapm.attach_zone_start(stints_df, season)

    if player_stints_df is None:
        player_stints_df = expand_player_stints(stints_df)

    # Compute each stat component independently, then join them all together below
    gp = compute_skater_gp(season)
    toi = compute_skater_toi(player_stints_df, situation, season=season)
    onice = compute_skater_onice_stats(player_stints_df, situation)
    goals_assists = compute_skater_goals_assists(season, situation, stints_df)
    possession = compute_skater_possession_events(season, situation, stints_df)
    penalties = compute_skater_penalties(season, situation, stints_df)
    zone_starts = compute_skater_zone_starts(player_stints_df, situation)

    # ixG uses the 5v5-specific column for the 5v5 bucket, and the all-situations column otherwise
    if ixg_df is None:
        ixg_df = xg.compute_player_xg(season, bundle=bundle, stints_df=stints_df)
    ixg_col = 'ixG_5v5' if situation == '5v5' else 'ixG_all'
    ixg = ixg_df[ixg_col].rename('ixG') if ixg_col in ixg_df.columns else pd.Series(dtype=float, name='ixG')

    player_ids_df = data_io.load_player_ids_csv(season)

    # Anchor the result to every rostered player at this position, even those with zero of a stat
    roster = player_ids_df[player_ids_df['Position'] == position][['Player', 'Player ID', 'Team']].copy()
    roster = roster.drop_duplicates(subset='Player ID').set_index('Player ID')

    result = roster.join([gp.rename('GP'), toi.rename('TOI'), onice, goals_assists, possession,
                           penalties, zone_starts, ixg], how='left')

    # A missing component means the player recorded zero of that stat, not that it's unknown
    numeric_fill_zero = [
        'GP', 'TOI', 'Goals', 'Total Assists', 'First Assists', 'Second Assists', 'Total Points',
        'ixG', 'Hits', 'Hits Taken', 'Giveaways', 'Takeaways', 'Penalties Drawn', 'Total Penalties',
        'Off. Zone Starts', 'Neu. Zone Starts', 'Def. Zone Starts',
    ]
    for col in numeric_fill_zero:
        if col not in result.columns:
            result[col] = 0
        result[col] = result[col].fillna(0)

    # Rate stats stay NaN (rather than 0) when undefined, e.g. no shots on ice
    for col in ['GF%', 'xGF%', 'PDO']:
        if col not in result.columns:
            result[col] = np.nan

    result['Position'] = position
    result = result.reset_index()

    ordered_cols = [
        'Player ID', 'Player', 'Team', 'Position', 'GP', 'TOI', 'Goals', 'Total Assists',
        'First Assists', 'Second Assists', 'Total Points', 'ixG', 'Hits', 'Hits Taken', 'Giveaways',
        'Takeaways', 'Penalties Drawn', 'Total Penalties', 'Off. Zone Starts', 'Neu. Zone Starts',
        'Def. Zone Starts', 'GF%', 'xGF%', 'PDO',
    ]
    result = result[ordered_cols]
    return result


def compute_goalie_stats_table(season: str, situation: str, stints_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Assemble one (season, situation) goalie stats table, matching load_save.load_stats_csv's expected file shape.

    :param season: A str representing the season ('YYYY-YYYY')
    :param situation: A str situation bucket key ('all', '5v5', or '4v5')
    :param stints_df: An optional pre-built season stints DataFrame, used to strength-tag shots
    :return: A DataFrame of goalie stats, one row per Player ID
    """
    player_ids_df = data_io.load_player_ids_csv(season)

    # Restrict to known goalie IDs so a skater's row never leaks into the goalie table
    goalie_ids = set(player_ids_df.loc[player_ids_df['Position'] == 'G', 'Player ID'])

    gp = compute_goalie_gp(season, goalie_ids)
    toi = compute_goalie_toi(season, situation, stints_df=stints_df)
    shot_stats = compute_goalie_shot_stats(season, situation, stints_df=stints_df)

    # Anchor the result to every rostered goalie, even those with zero TOI
    roster = player_ids_df[player_ids_df['Position'] == 'G'][['Player', 'Player ID', 'Team']].copy()
    roster = roster.drop_duplicates(subset='Player ID').set_index('Player ID')

    result = roster.join([gp.rename('GP'), toi.rename('TOI'), shot_stats], how='left')

    # A missing component means the goalie recorded zero of that stat, not that it's unknown
    zero_fill_cols = [
        'GP', 'TOI', 'Shots Against', 'Saves', 'Goals Against',
        'HD Shots Against', 'HD Saves', 'HD Goals Against', 'HD xG Against',
        'MD Shots Against', 'MD Saves', 'MD Goals Against', 'MD xG Against',
        'LD Shots Against', 'LD Saves', 'LD Goals Against', 'LD xG Against',
        'Rebound Attempts Against', 'Rebound xG Against',
    ]
    for col in zero_fill_cols:
        if col not in result.columns:
            result[col] = 0
        result[col] = result[col].fillna(0)

    # Rate stats stay NaN (rather than 0) when undefined, e.g. no shots faced
    for col in ['SV%', 'GAA', 'xG Against']:
        if col not in result.columns:
            result[col] = np.nan

    result = result.reset_index()

    ordered_cols = [
        'Player ID', 'Player', 'Team', 'GP', 'TOI', 'Shots Against', 'Saves', 'Goals Against',
        'SV%', 'GAA', 'xG Against', 'HD Shots Against', 'HD Saves', 'HD Goals Against',
        'HD xG Against', 'MD Shots Against', 'MD Saves', 'MD Goals Against', 'MD xG Against',
        'LD Shots Against', 'LD Saves', 'LD Goals Against', 'LD xG Against',
        'Rebound Attempts Against', 'Rebound xG Against',
    ]
    result = result[ordered_cols]
    return result


def build_season_stint_bundle(season: str) -> dict:
    """
    Build every season-level (position/situation-independent) piece of derived stint data once, so all 11 (position, situation) calls per season can share it.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: A dict of {'stints_df', 'player_stints_df', 'ixg_df'} shared across (position, situation) calls
    """
    # Load once here so it isn't reloaded by every downstream call this bundle feeds
    bundle = xg.load_xg_model()

    # Build the season's stints and attach every season-level derived column once
    stints_df = rapm.build_season_stints(season)
    stints_df = rapm.attach_xg_to_stints(stints_df, season, bundle=bundle)
    stints_df = attach_sog_to_stints(stints_df, season)
    stints_df = rapm.attach_zone_start(stints_df, season)

    player_stints_df = expand_player_stints(stints_df)

    ixg_df = xg.compute_player_xg(season, bundle=bundle, stints_df=stints_df)

    stint_bundle = {'stints_df': stints_df, 'player_stints_df': player_stints_df, 'ixg_df': ixg_df}
    return stint_bundle


def make_and_save_stats(season: str, position: str, situation: str, stint_bundle: dict = None) -> None:
    """
    Compute and save one (season, position, situation) stats table to the path load_save.load_stats_csv reads from.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str position ('F', 'D', or 'G') to compute stats for
    :param situation: A str situation bucket key
    :param stint_bundle: An optional pre-built season stint bundle from build_season_stint_bundle
    :return: None
    """
    # Goalies and skaters go through different underlying compute functions
    if position == 'G':
        stints_df = stint_bundle['stints_df'] if stint_bundle is not None else None
        stats_df = compute_goalie_stats_table(season, situation, stints_df=stints_df)
    else:
        if stint_bundle is not None:
            stats_df = compute_skater_stats(
                season, position, situation,
                stints_df=stint_bundle['stints_df'], player_stints_df=stint_bundle['player_stints_df'],
                ixg_df=stint_bundle['ixg_df'],
            )
        else:
            stats_df = compute_skater_stats(season, position, situation)

    stats_file_name = f'{season}_{position}_{situation}_stats.csv'
    data_io.save_csv(stats_df, 'processed_data', 'stats', stats_file_name)


def make_and_save_all_stats(season: str) -> None:
    """
    Compute and save every (position, situation) stats table for one season, reusing one season-level stint bundle and xG model across all 11 calls.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: None
    """
    # Build once per season, then share it across every (position, situation) pair below
    stint_bundle = build_season_stint_bundle(season)

    for position in constants.POSITIONS:
        situations = constants.GOALIE_SITUATIONS if position == 'G' else constants.SKATER_SITUATIONS
        for situation in situations:
            make_and_save_stats(season, position, situation, stint_bundle=stint_bundle)
