# ====================================================================================================
# WINS ABOVE REPLACEMENT (WAR)
# ====================================================================================================

# Imports
import numpy as np
import pandas as pd

from player_card_project import constants
from player_card_project import data_io
from player_card_project.process_data import xgoals as xg



# ====================================================================================================
# PLAYER ID / TOI HELPERS
# ====================================================================================================

def build_player_id_lookup(season: str, position: str = None) -> pd.Series:
    """
    Build a Player name -> Player ID lookup for a season, optionally restricted to one position.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: An optional str position ('F'/'D'/'G') to restrict the lookup to
    :return: A Series mapping Player name to Player ID
    """
    player_ids_df = data_io.load_player_ids_csv(season)
    if position is not None:
        player_ids_df = player_ids_df[player_ids_df['Position'] == position]
    # First occurrence per Player wins if a name isn't unique
    id_map = player_ids_df[['Player', 'Player ID']].drop_duplicates(subset='Player')
    id_map = id_map.set_index('Player')['Player ID']
    return id_map


def toi_by_id(stats_df: pd.DataFrame, id_lookup: pd.Series) -> pd.Series:
    """
    Collapse a position/situation stats table into total TOI (minutes) per Player ID.

    :param stats_df: A position/situation stats DataFrame
    :param id_lookup: A Series mapping Player name to Player ID
    :return: A Series of total TOI minutes indexed by Player ID
    """
    work = stats_df[['Player', 'TOI']].copy()
    work['Player ID'] = work['Player'].map(id_lookup)
    work = work.dropna(subset=['Player ID']).copy()
    work['Player ID'] = work['Player ID'].astype(int)
    work = work.groupby('Player ID')['TOI'].sum()
    return work


def gp_by_id(stats_df: pd.DataFrame, id_lookup: pd.Series) -> pd.Series:
    """
    Collapse a position/situation stats table into total games played per Player ID, used to prorate season-total WAR to a per-game rate.

    :param stats_df: A position/situation stats DataFrame
    :param id_lookup: A Series mapping Player name to Player ID
    :return: A Series of total games played indexed by Player ID
    """
    work = stats_df[['Player', 'GP']].copy()
    work['Player ID'] = work['Player'].map(id_lookup)
    work = work.dropna(subset=['Player ID']).copy()
    work['Player ID'] = work['Player ID'].astype(int)
    work = work.groupby('Player ID')['GP'].sum()
    return work


def total_toi_by_id(season: str, situation: str) -> pd.Series:
    """
    Total TOI (minutes) for every skater in one situation this season, forwards and defensemen pooled together.

    :param season: A str representing the season ('YYYY-YYYY')
    :param situation: A str strength situation (e.g. '5v5', '5v4')
    :return: A Series of total TOI minutes indexed by Player ID
    """
    # Forwards and defensemen are scraped/stored separately, so pool them into one Series
    pieces = []
    for position in ('F', 'D'):
        stats_df = data_io.load_stats_csv(season, position, situation)
        id_lookup = build_player_id_lookup(season, position)
        pieces.append(toi_by_id(stats_df, id_lookup))
    total_tois = pd.concat(pieces)
    return total_tois


# ====================================================================================================
# GOALS-TO-WINS CONVERSION
# ====================================================================================================

def goals_to_wins_factor(season: str) -> float:
    """
    This season's marginal win value per goal (or xG) at league-average scoring.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: The float goals-to-wins conversion factor
    """
    standings_df = data_io.load_team_standings_csv(season)
    total_goals = standings_df['Goals For'].sum()
    total_games = standings_df['GP'].sum()

    # Marginal win value per goal, via the Pythagorean-exponent win% formula's derivative at league-average scoring
    g_pg = total_goals / total_games
    g2w_factor = constants.PYTHAGOREAN_EXPONENT / (4 * g_pg)
    return g2w_factor


# ====================================================================================================
# REPLACEMENT LEVEL
# ====================================================================================================

def team_rank_replacement_rate(stats_df: pd.DataFrame, id_lookup: pd.Series, rapm_by_id: pd.Series, rank_threshold: int) -> float:
    """
    The TOI-weighted average RAPM rate among rows ranked below rank_threshold in TOI on their own team's roster.

    :param stats_df: A position/situation stats DataFrame
    :param id_lookup: A Series mapping Player name to Player ID
    :param rapm_by_id: A Series of RAPM rates indexed by Player ID
    :param rank_threshold: The int within-team TOI rank below which a player counts as replacement-level
    :return: The float TOI-weighted average RAPM rate among the below-threshold rows
    """
    work = stats_df[['Player', 'Team', 'TOI']].copy()
    work['Player ID'] = work['Player'].map(id_lookup)
    work = work.dropna(subset=['Player ID']).copy()
    work['Player ID'] = work['Player ID'].astype(int)
    work['Rate'] = work['Player ID'].map(rapm_by_id)
    work = work.dropna(subset=['Rate'])
    work = work[work['TOI'] > 0]

    # Below-threshold rows (by within-team TOI rank) define the replacement-level pool
    work['Rank'] = work.groupby('Team')['TOI'].rank(method='first', ascending=False)
    pool = work[work['Rank'] > rank_threshold]

    rate = float((pool['Rate'] * pool['TOI']).sum() / pool['TOI'].sum())
    return rate


def compute_replacement_levels(season: str, rapm_df: pd.DataFrame = None, rank_thresholds: dict = None) -> dict:
    """
    Compute the replacement-level RAPM rate for every (component, position) pair this season, via the team-relative TOI rank method (see team_rank_replacement_rate).

    :param season: A str representing the season ('YYYY-YYYY')
    :param rapm_df: An optional pre-loaded RAPM scores DataFrame; loaded from disk if not given
    :param rank_thresholds: An optional dict of {situation: {position: rank_threshold}} overrides (default constants.TEAM_TOI_RANK_THRESHOLDS)
    :return: A dict of {component: {position: replacement_rate}}
    """
    if rapm_df is None:
        rapm_df = data_io.load_rapm_scores_csv(season)
    rapm_indexed = rapm_df.set_index('Player ID')

    if rank_thresholds is None:
        rank_thresholds = constants.TEAM_TOI_RANK_THRESHOLDS

    # Position-specific lookups, built once per position rather than inside the component loop below
    id_lookup_by_position = {position: build_player_id_lookup(season, position) for position in ('F', 'D')}
    levels = {}

    # The four RAPM-derived WAR components, mapped to their stats-CSV situation / rapm_scores column
    components = ('evo', 'evd', 'ppl', 'pkl')

    situation_by_component = {'evo': '5v5', 'evd': '5v5', 'ppl': '5v4', 'pkl': '4v5'}
    rapm_column_by_component = {'evo': 'evo_rapm', 'evd': 'evd_rapm', 'ppl': 'ppl_rapm', 'pkl': 'pkl_rapm'}

    # One replacement-level rate per (component, position) pair
    for component in components:
        situation = situation_by_component[component]
        rapm_col = rapm_column_by_component[component]
        levels[component] = {}

        rapm_by_id = rapm_indexed[rapm_col].dropna()

        for position in ('F', 'D'):
            stats_df = data_io.load_stats_csv(season, position, situation)
            threshold = rank_thresholds[situation][position]
            levels[component][position] = team_rank_replacement_rate(
                stats_df, id_lookup_by_position[position], rapm_by_id, threshold,
            )

    return levels


# ====================================================================================================
# FINISHING IMPACT
# ====================================================================================================

def compute_finishing_impact(season: str, strength: str = None) -> pd.Series:
    """
    Season-total (actual goals - sum of predicted xG) for every player's own shots.

    :param season: A str representing the season ('YYYY-YYYY')
    :param strength: An optional str strength situation to restrict shots to (e.g. '5v5')
    :return: A Series of finishing impact (goals above expected) indexed by Player ID
    """
    bundle = xg.load_xg_model()

    # Restrict to one strength state if requested, otherwise pool across every situation
    shots_df = data_io.load_shot_events_csv(season)
    shots_df = shots_df[shots_df['Event Type'].isin(constants.UNBLOCKED_EVENT_TYPES)].copy()
    shots_df = shots_df.dropna(subset=['Shooter Player ID'])

    if strength is not None:
        shots_df = xg.attach_strength_state(shots_df, season)
        shots_df = shots_df[shots_df['Strength'] == strength]

    predicted_xg = xg.predict_xg(shots_df, season=season, bundle=bundle)

    work = shots_df[['Shooter Player ID', 'Event Type']].copy()
    work['Goal'] = (work['Event Type'] == 'goal').astype(int)
    work['xG'] = predicted_xg
    work['Shooter Player ID'] = work['Shooter Player ID'].astype(int)

    grouped = work.groupby('Shooter Player ID').agg(
        Goals=('Goal', 'sum'), xG=('xG', 'sum'),
    )
    fin_impact = grouped['Goals'] - grouped['xG']
    return fin_impact


# ====================================================================================================
# PER-COMPONENT AND SEASON-LEVEL WAR
# ====================================================================================================

def compute_penalty_impact(season: str, g2w: float = None, penalty_values: dict = None) -> dict:
    """
    Penalty drawing/taking WAR component, split into three buckets by the committing player's own pre-penalty Strength.

    :param season: A str representing the season ('YYYY-YYYY')
    :param g2w: An optional pre-computed goals-to-wins factor; computed if not given
    :param penalty_values: An optional dict of {strength_bucket: xG value per penalty minute} overrides
    :return: A dict of {strength_bucket: Series of penalty WAR indexed by Player ID}
    """
    buckets = ('5v5', '5v4', '4v5')

    if penalty_values is None:
        penalty_values = constants.PENALTY_XG_PER_MINUTE

    penalties_df = data_io.load_penalty_events_csv(season)

    penalties_df = xg.attach_strength_state(penalties_df, season)
    if g2w is None:
        g2w = goals_to_wins_factor(season)

    # Restrict to penalty types with an attributable individual player impact (2-, 4-, 5-min)
    attributable = penalties_df[penalties_df['Duration'].isin([2, 4, 5])].copy()

    result = {}
    for bucket in buckets:
        bucket_df = attributable[attributable['Strength'] == bucket]

        # Drawn penalties: credited to the player who drew the power play
        drawn = bucket_df.dropna(subset=['Drew Player ID']).assign(
            **{'Drew Player ID': lambda x: x['Drew Player ID'].astype(int)},
        ).groupby('Drew Player ID')['Duration'].sum().rename('drawn_min')

        # Taken penalties: charged to the player who committed the infraction
        taken = bucket_df.dropna(subset=['Penalty Player ID']).assign(
            **{'Penalty Player ID': lambda x: x['Penalty Player ID'].astype(int)},
        ).groupby('Penalty Player ID')['Duration'].sum().rename('taken_min')

        all_ids = drawn.index.union(taken.index)
        net_minutes = drawn.reindex(all_ids).fillna(0.0) - taken.reindex(all_ids).fillna(0.0)
        net_minutes.index.name = 'Player ID'

        result[bucket] = net_minutes * penalty_values[bucket] * g2w

    return result


def compute_component_war(
    season: str, position: str, component: str, rapm_df: pd.DataFrame = None,
    replacement_levels: dict = None, g2w: float = None,
) -> pd.Series:
    """
    One component's WAR (wins), indexed by Player ID, for one position's player pool this season.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str position ('F' or 'D') to compute this component for
    :param component: A str WAR component key ('evo', 'evd', 'ppl', or 'pkl')
    :param rapm_df: An optional pre-loaded RAPM scores DataFrame; loaded from disk if not given
    :param replacement_levels: An optional pre-computed dict of {component: {position: replacement_rate}}; computed if not given
    :param g2w: An optional pre-computed goals-to-wins factor; computed if not given
    :return: A Series of component WAR, prorated to a per-game rate, indexed by Player ID
    """
    if rapm_df is None:
        rapm_df = data_io.load_rapm_scores_csv(season)
    rapm_indexed = rapm_df.set_index('Player ID')

    situation_by_component = {'evo': '5v5', 'evd': '5v5', 'ppl': '5v4', 'pkl': '4v5'}
    rapm_column_by_component = {'evo': 'evo_rapm', 'evd': 'evd_rapm', 'ppl': 'ppl_rapm', 'pkl': 'pkl_rapm'}

    rapm_col = rapm_column_by_component[component]
    situation = situation_by_component[component]

    if replacement_levels is None:
        replacement_levels = compute_replacement_levels(season, rapm_df=rapm_df)
    if g2w is None:
        g2w = goals_to_wins_factor(season)

    id_lookup = build_player_id_lookup(season, position)
    stats_df = data_io.load_stats_csv(season, position, situation)
    toi_series = toi_by_id(stats_df, id_lookup)
    games_played = gp_by_id(stats_df, id_lookup)

    component_replacement_rate = replacement_levels.get(component, {}).get(position, 0.0)

    # A player with TOI but no RAPM coefficient falls back to exactly replacement rate (0 WAR)
    rate = rapm_indexed[rapm_col].reindex(toi_series.index).fillna(component_replacement_rate)

    toi_hours = toi_series / 60.0
    xgar = (rate - component_replacement_rate) * toi_hours
    wars = xgar * g2w

    # Prorate the season-total WAR to a per-game rate
    games_played = games_played.reindex(wars.index).replace(0, np.nan)
    wars = wars / games_played
    return wars


def compute_skater_war(season: str) -> pd.DataFrame:
    """
    Compute every skater's full WAR breakdown for a season, prorated to a per-game rate: the four RAPM-derived components plus finishing and penalty impact.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: A DataFrame of skater WAR components (per-game rates), one row per Player ID
    """
    rapm_df = data_io.load_rapm_scores_csv(season)
    replacement_levels = compute_replacement_levels(season, rapm_df=rapm_df)
    g2w = goals_to_wins_factor(season)

    fin_war_by_bucket = {}
    for bucket in ('5v5', '5v4', '4v5'):
        finishing_impact = compute_finishing_impact(season, strength=bucket)
        fin_war_by_bucket[bucket] = finishing_impact * g2w

    pen_war_by_bucket = compute_penalty_impact(season, g2w=g2w)

    # The four RAPM-derived WAR components, mapped to their stats-CSV situation / rapm_scores column
    components = ('evo', 'evd', 'ppl', 'pkl')

    position_frames = []
    gp_frames = []
    for position in ('F', 'D'):
        component_wars = {}
        toi_index = None
        for component in components:
            war_series = compute_component_war(
                season, position, component, rapm_df=rapm_df,
                replacement_levels=replacement_levels, g2w=g2w,
            )
            component_wars[f'{component}_war'] = war_series
            toi_index = war_series.index if toi_index is None else toi_index.union(war_series.index)

        pos_df = pd.DataFrame(component_wars, index=toi_index).fillna(0.0)
        pos_df.insert(0, 'Position', position)
        position_frames.append(pos_df)

        # This position's games played, used below to prorate finishing/penalty impact the same way
        id_lookup = build_player_id_lookup(season, position)
        all_stats_df = data_io.load_stats_csv(season, position, 'all')
        gp_frames.append(gp_by_id(all_stats_df, id_lookup))

    combined = pd.concat(position_frames)
    # A player showing up in both position pools shouldn't normally happen, so keep the first-seen row
    combined = combined[~combined.index.duplicated(keep='first')]

    games_played = pd.concat(gp_frames)
    games_played = games_played[~games_played.index.duplicated(keep='first')]
    gp_aligned = games_played.reindex(combined.index).replace(0, np.nan)

    for bucket in ('5v5', '5v4', '4v5'):
        combined[f'fin_war_{bucket}'] = fin_war_by_bucket[bucket].reindex(combined.index).fillna(0.0)
        combined[f'pen_war_{bucket}'] = pen_war_by_bucket[bucket].reindex(combined.index).fillna(0.0)

        # Prorate finishing/penalty impact to a per-game rate, matching the four RAPM-derived components
        combined[f'fin_war_{bucket}'] = combined[f'fin_war_{bucket}'] / gp_aligned
        combined[f'pen_war_{bucket}'] = combined[f'pen_war_{bucket}'] / gp_aligned

    combined['fin_war'] = combined['fin_war_5v5'] + combined['fin_war_5v4'] + combined['fin_war_4v5']
    combined['pen_war'] = combined['pen_war_5v5'] + combined['pen_war_5v4'] + combined['pen_war_4v5']
    combined['tot_war'] = (
        combined['evo_war'] + combined['evd_war'] + combined['ppl_war'] + combined['pkl_war']
        + combined['fin_war'] + combined['pen_war']
    )

    combined.index.name = 'Player ID'
    combined = combined.reset_index()

    # Column order: identity, tot_war, the four RAPM components, then the two aggregates and their situational pieces
    ordered_cols = [
        'Player ID', 'Position', 'tot_war', 'evo_war', 'evd_war', 'ppl_war', 'pkl_war',
        'fin_war', 'pen_war', 'fin_war_5v5', 'fin_war_5v4', 'fin_war_4v5',
        'pen_war_5v5', 'pen_war_5v4', 'pen_war_4v5',
    ]

    war_components = combined[ordered_cols]
    return war_components


def compute_goalie_war(season: str) -> pd.DataFrame:
    """
    Compute goalie WAR for a season, using GSAx (Goals Saved Above Expected) as the per-60 rate metric in place of RAPM, then prorated to a per-game rate.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: A DataFrame of goalie WAR components, one row per Player ID
    """
    bundle = xg.load_xg_model()

    g2w = goals_to_wins_factor(season)
    id_lookup = build_player_id_lookup(season, 'G')

    # Custom xG Against from shot events, keyed by (component, Player ID); falls back to the stats CSV's own xG Against if unavailable
    custom_gsax = {}  # component -> pd.Series(GSAx, index=Player ID)

    shots_df = data_io.load_shot_events_csv(season)
    shots_df = shots_df[shots_df['Event Type'].isin(constants.UNBLOCKED_EVENT_TYPES)].copy()
    shots_df = shots_df.dropna(subset=['Goalie Player ID']).copy()
    shots_df['Goalie Player ID'] = shots_df['Goalie Player ID'].astype(int)
    shots_df = xg.attach_strength_state(shots_df, season)
    shots_df = shots_df[shots_df['Strength'].isin(['5v5', '5v4'])].copy()

    if not shots_df.empty:
        shots_df['xG'] = xg.predict_xg(shots_df, season=season, bundle=bundle)
        shots_df['Goal'] = (shots_df['Event Type'] == 'goal').astype(int)

        for component, strength in [('evs', '5v5'), ('pkl', '5v4')]:
            subset = shots_df[shots_df['Strength'] == strength]
            agg = subset.groupby('Goalie Player ID').agg(
                xG_Against=('xG', 'sum'),
                Goals_Against=('Goal', 'sum'),
            )
            custom_gsax[component] = agg['xG_Against'] - agg['Goals_Against']

    war_series_list = []

    for component, situation in [('evs', '5v5'), ('pkl', '4v5')]:
        stats_df = data_io.load_stats_csv(season, 'G', situation)

        # TOI per Player ID (still needed for per-60 rate, even without volume weighting)
        toi_work = stats_df[['Player', 'TOI']].copy()
        toi_work['Player ID'] = toi_work['Player'].map(id_lookup)
        toi_work = toi_work.dropna(subset=['Player ID']).copy()
        toi_work['Player ID'] = toi_work['Player ID'].astype(int)
        agg_toi = toi_work.groupby('Player ID')['TOI'].sum()

        # GSAx: prefer custom xG model; fall back to the stats CSV's own xG Against
        if component in custom_gsax:
            gsax = custom_gsax[component].reindex(agg_toi.index).fillna(0.0)
        else:
            fb_work = stats_df[['Player', 'xG Against', 'Goals Against']].copy()
            fb_work['Player ID'] = fb_work['Player'].map(id_lookup)
            fb_work = fb_work.dropna(subset=['Player ID']).copy()
            fb_work['Player ID'] = fb_work['Player ID'].astype(int)
            fb_agg = fb_work.groupby('Player ID').agg(
                xG_Against=('xG Against', 'sum'),
                Goals_Against=('Goals Against', 'sum'),
            )
            gsax = (fb_agg['xG_Against'] - fb_agg['Goals_Against']).reindex(agg_toi.index).fillna(0.0)

        # GSAx/60 rate (positive = better than expected)
        gsax_per60 = pd.Series(
            np.where(agg_toi > 0, gsax * 60 / agg_toi, 0.0),
            index=agg_toi.index,
        )

        # Team-rank replacement level: every goalie ranked below the starter (by TOI) on their own team defines replacement level, matching the skater methodology
        goalie_replacement_rate = team_rank_replacement_rate(
            stats_df, id_lookup, gsax_per60, constants.GOALIE_TEAM_RANK_THRESHOLD,
        )

        toi_hours = agg_toi / 60.0
        war = (gsax_per60 - goalie_replacement_rate) * toi_hours * g2w

        # Prorate the season-total WAR to a per-game rate
        games_played = gp_by_id(stats_df, id_lookup).reindex(war.index).replace(0, np.nan)
        war = war / games_played

        war.name = f'{component}_war'
        war_series_list.append(war)

    if not war_series_list:
        war_components = pd.DataFrame(columns=['Player ID', 'evs_war', 'pkl_war', 'tot_war'])
    else:
        combined = pd.concat(war_series_list, axis=1).fillna(0.0)
        combined.index.name = 'Player ID'

        for col in ['evs_war', 'pkl_war']:
            if col not in combined.columns:
                combined[col] = 0.0

        combined['tot_war'] = combined['evs_war'] + combined['pkl_war']
        war_components = combined.reset_index()
    return war_components


def make_skater_war_scores(season: str) -> None:
    """
    Compute a season's skater WAR scores once, then save forwards and defensemen to separate files.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: None
    """
    war_df = compute_skater_war(season)
    war_df.insert(0, 'Season', season)

    # Save forwards and defensemen to separate files, matching load_save.load_stats_csv's per-position shape
    for position in ('F', 'D'):
        pos_df = war_df[war_df['Position'] == position]
        data_io.save_csv(pos_df, 'processed_data', 'war_scores', f'{season}_{position}_war_scores.csv')


def make_goalie_war_scores(season: str) -> None:
    """
    Compute and save goalie WAR scores for a season to processed_data/war_scores/{season}_G_war_scores.csv.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: None
    """
    war_df = compute_goalie_war(season)
    war_df.insert(0, 'Season', season)

    data_io.save_csv(war_df, 'processed_data', 'war_scores', f'{season}_G_war_scores.csv')


def make_war_scores(season: str) -> None:
    """
    Compute and save a season's WAR scores for skaters and goalies.

    :param season: A str representing the season ('YYYY-YYYY')
    :return: None
    """
    make_skater_war_scores(season)
    make_goalie_war_scores(season)
