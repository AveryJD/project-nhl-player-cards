# ====================================================================================================
# EXPECTED GOALS (XG) MODEL
# ====================================================================================================

# Imports
import functools
import json
import os
import pickle
import re
import time
import numpy as np
import pandas as pd
import threadpoolctl
from joblib import Parallel, delayed
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold

from player_card_project import constants
from player_card_project import data_io
from player_card_project.process_data import rapm


DATA_DIR = constants.DATA_DIR

# Net location (NHL rink coordinates in feet)
NET_X = 89.0

# The shot features fed into the xG model, split by dtype since the model pipeline handles each differently
NUMERICAL_FEATURES = [
    'Distance', 'Angle', 'Behind Net', 'Prior Event Elapsed', 'Distance Change',
    'Shot Speed', 'Is Rebound', 'Is Rush', 'Crossed Royal Road', 'Period Number',
    'Same Team As Prior Event', 'Lateral Movement', 'Score State', 'Off Wing',
]
CATEGORICAL_FEATURES = ['Shot Type', 'Strength', 'Prior Event Type', 'Shooter Shoots', 'Goalie Catches']

# The shot event types
ALL_SHOT_EVENTS = ('goal', 'shot-on-goal', 'missed-shot', 'blocked-shot')
UNBLOCKED_SHOT_EVENTS = ('goal', 'shot-on-goal', 'missed-shot')


# ====================================================================================================
# FEATURE ENGINEERING
# ====================================================================================================

def time_to_seconds(time_str) -> float:
    """
    Convert a MM:SS clock string into total seconds, or NaN if not parseable.

    :param time_str: A clock value in MM:SS format
    :return: The float total number of seconds, or NaN if not parseable
    """
    # Nothing to parse
    if pd.isna(time_str):
        result = np.nan
    else:
        try:
            minutes, seconds = str(time_str).split(':')
            result = float(int(minutes) * 60 + int(seconds))
        # Malformed clock string
        except (ValueError, AttributeError):
            result = np.nan
    return result


def distance_angle(x: np.ndarray, y: np.ndarray) -> tuple:
    """
    Compute distance and angle-off-center to the nearer net for arrays of shot x/y coordinates.

    :param x: An array of shot x-coordinates
    :param y: An array of shot y-coordinates
    :return: A (distance, angle) tuple of arrays
    """
    # Mirror the target net to whichever end of the ice the shot was taken from
    mirrored_net_x = np.where(x >= 0, NET_X, -NET_X)
    dx = mirrored_net_x - x
    distance = np.sqrt(dx ** 2 + y ** 2)
    angle = np.degrees(np.arctan2(np.abs(y), np.abs(dx)))
    result = (distance, angle)
    return result


def engineer_features(shots_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add every derived numeric feature (see NUMERICAL_FEATURES) to a raw shot-events DataFrame; does not add 'Strength' or the handedness features.

    :param shots_df: A raw shot-events DataFrame
    :return: The DataFrame with every NUMERICAL_FEATURES column added
    """
    df = shots_df.copy()

    df['X'] = pd.to_numeric(df['X'], errors='coerce')
    df['Y'] = pd.to_numeric(df['Y'], errors='coerce')
    prior_x = pd.to_numeric(df.get('Prior Event X'), errors='coerce')
    prior_y = pd.to_numeric(df.get('Prior Event Y'), errors='coerce')

    # Core shot-location features
    distance, angle = distance_angle(df['X'].to_numpy(), df['Y'].to_numpy())
    df['Distance'] = distance
    df['Angle'] = angle
    df['Behind Net'] = (df['X'].abs() > NET_X).astype(int)

    cur_sec = df['Time'].apply(time_to_seconds)
    prior_sec = df.get('Prior Event Time', pd.Series(index=df.index, dtype=float)).apply(time_to_seconds)
    elapsed = (cur_sec - prior_sec).clip(lower=0)
    df['Prior Event Elapsed'] = elapsed

    # A shot only has a valid prior event if the prior location/timing is fully known
    has_prior = prior_x.notna() & prior_y.notna() & elapsed.notna()

    prior_distance, _ = distance_angle(prior_x.to_numpy(), prior_y.to_numpy())
    prior_distance = pd.Series(prior_distance, index=df.index)
    df['Distance Change'] = np.where(has_prior, df['Distance'] - prior_distance, np.nan)

    # Shot speed: distance traveled since the prior event, over the elapsed time, capped at a sane max
    travel = np.sqrt((df['X'] - prior_x) ** 2 + (df['Y'] - prior_y) ** 2)
    elapsed_safe = elapsed.replace(0, np.nan)
    shot_speed = travel / elapsed_safe
    df['Shot Speed'] = np.where(has_prior, shot_speed.clip(upper=50.0), np.nan)

    prior_type = df.get('Prior Event Type', pd.Series(index=df.index, dtype=object))
    df['Is Rebound'] = (
        has_prior & prior_type.isin(ALL_SHOT_EVENTS) & (elapsed <= constants.REBOUND_WINDOW_SECONDS)
    ).astype(int)
    df['Is Rush'] = (
        has_prior & (elapsed <= constants.RUSH_WINDOW_SECONDS) & (travel >= constants.RUSH_DISTANCE_THRESHOLD)
    ).astype(int)

    # Royal road / lateral movement features
    crossed = has_prior & (np.sign(df['Y']) != np.sign(prior_y)) & (df['Y'] != 0) & (prior_y != 0)
    df['Crossed Royal Road'] = crossed.astype(int)
    df['Lateral Movement'] = np.where(has_prior, (df['Y'] - prior_y).abs(), np.nan)

    prior_team = df.get('Prior Event Team', pd.Series(index=df.index, dtype=object))
    df['Same Team As Prior Event'] = (has_prior & (prior_team == df['Team'])).astype(int)

    # A shot failing the has_prior gate gets 'none' rather than a raw (often NaN) value, so it stays distinguishable from 'unknown'
    df['Prior Event Type'] = np.where(has_prior, prior_type.fillna('unknown'), 'none')

    df['Period Number'] = pd.to_numeric(df['Period'], errors='coerce').clip(upper=4)

    df['Shot Type'] = df.get('Shot Type', pd.Series(index=df.index, dtype=object)).fillna('unknown')

    if 'Event Type' in df.columns:
        df['Goal'] = (df['Event Type'] == 'goal').astype(int)

    return df


def attach_handedness_features(shots_df: pd.DataFrame, bios_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Join shooter/goalie shooting-catching hand onto a shot-events DataFrame and derive an 'Off Wing' flag from it.

    :param shots_df: A shot-events DataFrame
    :param bios_df: An optional pre-loaded player bios DataFrame; loaded from disk if not given
    :return: The DataFrame with 'Shooter Shoots', 'Goalie Catches', and 'Off Wing' columns added
    """
    df = shots_df.copy()

    if bios_df is None:
        bios_df = data_io.load_player_bios_csv()

    # Player ID -> shooting/catching hand lookup
    hand_map = (
        bios_df.dropna(subset=['Player ID'])
        .assign(**{'Player ID': lambda x: x['Player ID'].astype(int)})
        .drop_duplicates(subset='Player ID')
        .set_index('Player ID')['Shoots Catches']
    )

    shooter_ids = pd.to_numeric(df.get('Shooter Player ID'), errors='coerce')
    goalie_ids = pd.to_numeric(df.get('Goalie Player ID'), errors='coerce')

    df['Shooter Shoots'] = shooter_ids.map(hand_map).fillna('unknown')
    df['Goalie Catches'] = goalie_ids.map(hand_map).fillna('unknown')

    # Mirror Y onto the attacking direction so off wing is well-defined regardless of end of ice
    x = pd.to_numeric(df['X'], errors='coerce')
    y = pd.to_numeric(df['Y'], errors='coerce')
    attacking_direction = np.where(x >= 0, 1.0, -1.0)
    mirrored_y = y * attacking_direction

    is_off_wing = (
        ((df['Shooter Shoots'] == 'R') & (mirrored_y < 0)) |
        ((df['Shooter Shoots'] == 'L') & (mirrored_y > 0))
    )
    df['Off Wing'] = is_off_wing.astype(int)

    return df


def attach_strength_state_from_stints(shots_df: pd.DataFrame, stints_df: pd.DataFrame) -> pd.DataFrame:
    """
    The actual strength-state join against an already-built stints_df, from the shooting team's perspective ('5v5'/'5v4'/'4v5'/'EN_for'/'EN_against'/etc, 'unknown' if no matching stint).

    :param shots_df: A shot-events DataFrame
    :param stints_df: A season's stints DataFrame
    :return: The DataFrame with a 'Strength' column added
    """
    # 3-on-3 regular-season OT began 2015-2016; a pre-2015-16 '3v3' is a different (4-on-4-rules) situation and is
    # tagged '3v3_pre2015ot' so the two eras are never pooled together
    three_on_three_ot_first_season_start_year = 2015

    df = shots_df.copy()
    df['Strength'] = 'unknown'

    shot_sec = df['Time'].apply(time_to_seconds)

    strengths = np.full(len(df), 'unknown', dtype=object)
    df_reset = df.reset_index(drop=True)
    shot_sec = shot_sec.reset_index(drop=True)

    for (game_id, period), group in stints_df.groupby(['Game ID', 'Period']):
        row_mask = (df_reset['Game ID'] == game_id) & (df_reset['Period'] == period)
        row_idx = np.flatnonzero(row_mask.to_numpy())
        if len(row_idx) == 0:
            continue

        # Game ID's leading 4 digits are the season start year (YYYYTTNNNN format)
        is_pre_3v3_ot_era = int(str(game_id)[:4]) < three_on_three_ot_first_season_start_year

        starts = group['Start'].to_numpy()
        order = np.argsort(starts)
        group = group.iloc[order]
        starts = group['Start'].to_numpy()

        team_a = group['Team A'].iloc[0]
        team_b = group['Team B'].iloc[0]

        a_skaters = group['Team A Skaters'].apply(len).to_numpy()
        b_skaters = group['Team B Skaters'].apply(len).to_numpy()
        a_goalie = group['Team A Goalie On'].to_numpy()
        b_goalie = group['Team B Goalie On'].to_numpy()

        secs = shot_sec.to_numpy()[row_idx]
        teams = df_reset['Team'].to_numpy()[row_idx]

        # side='left': a shot on the exact stint boundary is attributed to the ending stint, matching build_season_stints' own goal-attribution fix
        stint_pos = np.searchsorted(starts, secs, side='left') - 1
        stint_pos = np.clip(stint_pos, 0, len(starts) - 1)

        for k, idx in enumerate(row_idx):
            pos = stint_pos[k]
            shooting_team = teams[k]

            if shooting_team == team_a:
                own_n, opp_n = a_skaters[pos], b_skaters[pos]
                own_goalie, opp_goalie = a_goalie[pos], b_goalie[pos]
            elif shooting_team == team_b:
                own_n, opp_n = b_skaters[pos], a_skaters[pos]
                own_goalie, opp_goalie = b_goalie[pos], a_goalie[pos]
            else:
                continue

            if not opp_goalie:
                strengths[idx] = 'EN_for'
            elif not own_goalie:
                strengths[idx] = 'EN_against'
            elif own_n == 3 and opp_n == 3 and is_pre_3v3_ot_era:
                strengths[idx] = '3v3_pre2015ot'
            else:
                strengths[idx] = f'{own_n}v{opp_n}'

    df['Strength'] = strengths
    return df


def attach_strength_state(shots_df: pd.DataFrame, season: str) -> pd.DataFrame:
    """
    Join each shot's on-ice strength state in from that season's stints, computing them fresh via rapm.build_season_stints.

    :param shots_df: A shot-events DataFrame
    :param season: A str representing the season ('YYYY-YYYY')
    :return: The DataFrame with a 'Strength' column added
    """

    stints_df = rapm.build_season_stints(season)
    strength_df = attach_strength_state_from_stints(shots_df, stints_df)
    return strength_df


def attach_score_state_to_shots(shots_df: pd.DataFrame) -> pd.DataFrame:
    """
    Attach the score state (own goals minus opponent goals, capped at +/-constants.SHOT_SCORE_STATE_CAP) at the moment of each shot, vectorized per-game.

    :param shots_df: A shot-events DataFrame
    :return: The DataFrame with a 'Score State' column added
    """
    df = shots_df.copy().reset_index(drop=True)
    if df.empty or 'Event Type' not in df.columns:
        df['Score State'] = 0.0
    else:
        period_num = pd.to_numeric(df['Period'], errors='coerce').fillna(1)
        shot_sec = df['Time'].apply(time_to_seconds).fillna(0)
        df['abs_sec'] = (period_num - 1) * 1200 + shot_sec

        score_state_arr = np.zeros(len(df), dtype=float)

        for game_id, game_df in df.groupby('Game ID'):
            goals = game_df[game_df['Event Type'] == 'goal'].sort_values('abs_sec')
            if goals.empty:
                continue

            teams = sorted(game_df['Team'].dropna().unique())
            if len(teams) != 2:
                continue
            team_a, team_b = teams[0], teams[1]

            goal_abs = goals['abs_sec'].to_numpy()
            a_cum = (goals['Team'] == team_a).to_numpy().cumsum()
            b_cum = (goals['Team'] == team_b).to_numpy().cumsum()

            game_idx = game_df.index.to_numpy()
            shot_abs = game_df['abs_sec'].to_numpy()
            shot_team = game_df['Team'].to_numpy()

            # searchsorted 'left': pos[i] = number of goals with abs_sec strictly before shot_abs[i]
            pos = np.searchsorted(goal_abs, shot_abs, side='left')
            idx_before = np.clip(pos - 1, 0, len(goal_abs) - 1)
            a_before = np.where(pos > 0, a_cum[idx_before], 0)
            b_before = np.where(pos > 0, b_cum[idx_before], 0)

            is_a = shot_team == team_a
            is_b = shot_team == team_b
            state = np.where(is_a, a_before - b_before, np.where(is_b, b_before - a_before, 0.0))
            score_state_arr[game_idx] = state

        df['Score State'] = np.clip(score_state_arr, -constants.SHOT_SCORE_STATE_CAP, constants.SHOT_SCORE_STATE_CAP).astype(float)
        df = df.drop(columns=['abs_sec'])
    return df


def build_training_table(seasons: list) -> pd.DataFrame:
    """
    Load, feature-engineer, and strength-tag shot events across multiple seasons into one combined training table.

    :param seasons: A list of str seasons ('YYYY-YYYY') to load shot events from
    :return: A combined DataFrame of feature-engineered, strength-tagged shots across every season
    """
    bios_df = data_io.load_player_bios_csv()

    chunks = []
    for season in seasons:
        shots_df = data_io.load_shot_events_csv(season)

        if shots_df.empty:
            continue

        shots_df = shots_df[shots_df['Event Type'].isin(UNBLOCKED_SHOT_EVENTS)].copy()
        if shots_df.empty:
            continue

        # Feature-engineer and tag this season's shots, then fold them into the combined table
        shots_df = engineer_features(shots_df)
        shots_df = attach_handedness_features(shots_df, bios_df=bios_df)
        shots_df = attach_score_state_to_shots(shots_df)
        shots_df = attach_strength_state(shots_df, season)
        shots_df['Season'] = season
        chunks.append(shots_df)

    if not chunks:
        feature_columns = NUMERICAL_FEATURES + CATEGORICAL_FEATURES
        result = pd.DataFrame(columns=feature_columns + ['Goal', 'Season'])
    else:
        result = pd.concat(chunks, ignore_index=True)
    return result


# ====================================================================================================
# TRAINING AND EVALUATION
# ====================================================================================================

def prep_categoricals(df: pd.DataFrame, categories: dict, cat_features: list = None) -> pd.DataFrame:
    """
    Coerce categorical feature columns to a fixed, shared 'category' dtype so encoding matches between train and predict time.

    :param df: A feature table DataFrame
    :param categories: A dict mapping column name to the fixed list of category values seen at train time
    :param cat_features: An optional list of categorical column names
    :return: The DataFrame with each categorical column coerced to the shared dtype
    """
    if cat_features is None:
        cat_features = CATEGORICAL_FEATURES
    df = df.copy()
    # Coerce every categorical column to the exact category set seen at train time
    for col in cat_features:
        cats = categories.get(col, [])
        df[col] = df[col].where(df[col].isin(cats), 'unknown')
        if 'unknown' not in cats:
            cats = cats + ['unknown']
        df[col] = pd.Categorical(df[col], categories=cats)
    return df


def max_in_season_calibration_error(seasons: np.ndarray, goals: np.ndarray, xg: np.ndarray) -> dict:
    """
    Compute, per season, |sum(predicted xG) - sum(actual goals)| / sum(actual goals), plus the max across seasons.

    :param seasons: An array of season labels, one per row
    :param goals: An array of actual goal outcomes (0/1), one per row
    :param xg: An array of predicted xG values, one per row
    :return: A dict of {'max_error': float, 'by_season': {season: error}}
    """
    by_season = {}
    for season in pd.unique(seasons):
        mask = seasons == season
        actual = goals[mask].sum()
        predicted = xg[mask].sum()
        if actual > 0:
            by_season[str(season)] = float(abs(predicted - actual) / actual)
        else:
            by_season[str(season)] = float('nan')

    valid = {s: e for s, e in by_season.items() if not np.isnan(e)}
    max_error = max(valid.values()) if valid else float('nan')
    result = {'max_error': max_error, 'by_season': by_season}
    return result


def fit_one_xg_candidate_fold(
    X: pd.DataFrame, y: np.ndarray, cat_features: list, params: dict,
    train_idx: np.ndarray, test_idx: np.ndarray, c_idx: int,
) -> tuple:
    """
    Fit one HistGradientBoostingClassifier on one (param_grid candidate, CV fold) combination and score the held-out fold.

    :param X: The full feature table
    :param y: An array of goal outcomes (0/1) aligned with X
    :param cat_features: A list of categorical feature column names
    :param params: A dict of HistGradientBoostingClassifier hyperparameters for this candidate
    :param train_idx: An array of row indices for this fold's training split
    :param test_idx: An array of row indices for this fold's held-out split
    :param c_idx: The int 1-based index of this candidate within the param grid, echoed back in the result so the caller can attribute this fold's predictions to it
    :return: A (c_idx, test_idx, predicted_probabilities) tuple
    """
    # Cap this fit to one thread
    with threadpoolctl.threadpool_limits(limits=1):
        model = HistGradientBoostingClassifier(
            categorical_features=cat_features, random_state=0, **params,
        )
        model.fit(X.iloc[train_idx], y[train_idx])
        pred = model.predict_proba(X.iloc[test_idx])[:, 1]

    result = (c_idx, test_idx, pred)
    return result


def train_single_xg_model(
    table: pd.DataFrame, feature_columns: list, cat_features: list,
    param_grid: list, n_splits: int, label: str = 'xG model',
) -> dict:
    """
    Train one HistGradientBoostingClassifier on table via GroupKFold-by-season CV grid search (parallelized across candidate x fold via joblib, one thread per fit), selecting by AUC and refitting on the full table.

    :param table: A feature-engineered training table
    :param feature_columns: A list of feature column names to train on
    :param cat_features: A list of categorical feature column names
    :param param_grid: A list of hyperparameter dicts to grid-search over
    :param n_splits: The int number of GroupKFold-by-season CV splits to use
    :param label: A short str description used in progress print messages
    :return: A dict bundle with the fitted model, categories, feature columns, best params, and CV metrics
    """

    # Lock in the fixed category set every fold/candidate will encode against
    categories = {col: sorted(table[col].dropna().unique().tolist()) for col in cat_features}
    table = prep_categoricals(table, categories, cat_features=cat_features)

    X = table[feature_columns]
    y = table['Goal'].to_numpy()
    groups = table['Season'].to_numpy()
    n_groups = len(np.unique(groups))
    effective_splits = max(2, min(n_splits, n_groups))

    best_auc = -np.inf
    best_params = param_grid[0]
    best_oof = None  # (oof_pred, valid_mask) for the winning candidate

    # Grid-search every (candidate, fold) pair in parallel, then pick the candidate with the best mean CV AUC
    if n_groups >= 2:
        gkf = GroupKFold(n_splits=effective_splits)
        # Pre-split fold indices once, reused across every param_grid candidate
        splits = list(gkf.split(X, y, groups=groups))
        n_candidates = len(param_grid)
        n_folds = len(splits)

        tasks = [
            (c_idx, params, train_idx, test_idx)
            for c_idx, params in enumerate(param_grid, start=1)
            for train_idx, test_idx in splits
        ]
        print(f'{label}: running {len(tasks)} candidate x fold fits in parallel '
              f'({n_candidates} candidates x {n_folds} folds)...')

        fit_results = Parallel(n_jobs=-1, backend='threading')(
            delayed(fit_one_xg_candidate_fold)(X, y, cat_features, params, train_idx, test_idx, c_idx)
            for c_idx, params, train_idx, test_idx in tasks
        )

        oof_by_candidate = {c_idx: np.full(len(table), np.nan) for c_idx in range(1, n_candidates + 1)}
        for c_idx, test_idx, pred in fit_results:
            oof_by_candidate[c_idx][test_idx] = pred

        for c_idx, params in enumerate(param_grid, start=1):
            oof_pred = oof_by_candidate[c_idx]
            valid = ~np.isnan(oof_pred)
            if not valid.any():
                continue
            auc = roc_auc_score(y[valid], oof_pred[valid])
            print(f'{label}: candidate {c_idx}/{n_candidates} {params} - CV AUC={auc:.5f}')
            if auc > best_auc:
                best_auc = auc
                best_params = params
                best_oof = (oof_pred, valid)

    if best_oof is not None:
        oof_pred, valid = best_oof
        calibration = max_in_season_calibration_error(groups[valid], y[valid], oof_pred[valid])
    else:
        calibration = {'max_error': float('nan'), 'by_season': {}}

    # Refit the winning candidate on the full table (not just its CV folds) for the model actually saved/used
    print(f'{label}: refitting best candidate {best_params} on the full table '
          f'({len(table)} rows)...')
    refit_start = time.time()
    final_model = HistGradientBoostingClassifier(
        categorical_features=cat_features, random_state=0, **best_params,
    )
    final_model.fit(X, y)
    print(f'{label}: final refit done - {time.time() - refit_start:.1f}s')

    result = {
        'model': final_model,
        'categories': categories,
        'feature_columns': feature_columns,
        'categorical_features': cat_features,
        'best_params': best_params,
        'cv_auc': float(best_auc) if best_auc != -np.inf else None,
        'cv_calibration': calibration,
        'n_rows': int(len(table)),
    }
    return result


def train_xg_model(
    seasons: list,
    param_grid: list = constants.PARAM_GRID,
    high_volume_param_grid: list = constants.PARAM_GRID_HIGH_VOLUME,
    high_volume_strengths: tuple = constants.HIGH_VOLUME_STRENGTHS,
    n_splits: int = constants.XG_CV_SPLITS,
) -> dict:
    """
    Train one xG model per distinct strength state actually present in the training data (with enough rows to clear constants.STRENGTH_MIN_ROWS), high-volume strengths get the deeper param grid, no combined fallback model.

    :param seasons: A list of str seasons ('YYYY-YYYY') to train on
    :param param_grid: The hyperparameter grid used for non-high-volume strength states
    :param high_volume_param_grid: The deeper hyperparameter grid used for high-volume strength states
    :param high_volume_strengths: A tuple of strength state strs that get the deeper param grid
    :param n_splits: The int number of GroupKFold-by-season CV splits to use
    :return: A dict of {'by_strength': {strength: model_bundle}, 'n_rows': int, 'seasons': list}
    """
    # Per-strength-state models drop 'Strength' as a feature (constant within each state); trained for every distinct
    # strength value with enough pooled volume, not just 5v5/5v4/4v5
    categorical_features_per_strength = ['Shot Type', 'Prior Event Type', 'Shooter Shoots', 'Goalie Catches']
    feature_columns_per_strength = NUMERICAL_FEATURES + categorical_features_per_strength

    table = build_training_table(seasons)

    strengths = sorted(s for s in table['Strength'].unique() if s != 'unknown')

    # Train one model per strength state with enough pooled volume
    by_strength = {}
    for strength in strengths:
        sub = table[table['Strength'] == strength].copy()
        if len(sub) < constants.STRENGTH_MIN_ROWS:
            print(f'xG {strength}: only {len(sub)} rows (< {constants.STRENGTH_MIN_ROWS}), skipping per-strength '
                  f'model (shots in this strength state will score as NaN)')
            continue
        strength_param_grid = high_volume_param_grid if strength in high_volume_strengths else param_grid
        print(f'xG {strength}: starting ({len(sub)} rows, '
              f'{"high-volume" if strength in high_volume_strengths else "default"} grid)...')
        result = train_single_xg_model(sub, feature_columns_per_strength,
                                         categorical_features_per_strength, strength_param_grid, n_splits,
                                         label=f'xG {strength}')
        by_strength[strength] = result
        print(f'xG {strength}: done - {result["n_rows"]} rows, CV AUC={result["cv_auc"]}')

    bundle = {
        'by_strength': by_strength,
        'n_rows': int(len(table)),
        'seasons': seasons,
    }
    return bundle


# ====================================================================================================
# PERSISTENCE AND SCORING
# ====================================================================================================

def save_xg_model(result: dict) -> None:
    """
    Save the trained xG model bundle (per-strength models only) and a JSON report.

    :param result: The dict returned by train_xg_model
    :return: None
    """
    save_dir = os.path.join(DATA_DIR, 'player_card_data', 'processed_data', 'xg_models')
    os.makedirs(save_dir, exist_ok=True)

    # Pickle just the pieces predict_xg_by_strength needs
    sub_bundles = {}
    for strength, sub_result in result.get('by_strength', {}).items():
        sub_bundles[strength] = {
            'model': sub_result['model'],
            'categories': sub_result['categories'],
            'feature_columns': sub_result['feature_columns'],
            'categorical_features': sub_result['categorical_features'],
        }

    bundle = {'by_strength': sub_bundles}
    with open(os.path.join(save_dir, 'xg_model.pkl'), 'wb') as f:
        pickle.dump(bundle, f)

    # Everything except the model object itself, for a human-readable JSON report
    sub_reports = {}
    for strength, sub_result in result.get('by_strength', {}).items():
        sub_report = {k: v for k, v in sub_result.items() if k != 'model'}
        sub_report['categories'] = {k: list(v) for k, v in sub_report['categories'].items()}
        sub_reports[strength] = sub_report

    report = {
        'n_rows': result['n_rows'],
        'seasons': result['seasons'],
        'by_strength': sub_reports,
    }
    with open(os.path.join(save_dir, 'xg_model_report.json'), 'w') as f:
        json.dump(report, f, indent=2)

    strength_keys = list(result.get('by_strength', {}).keys())
    print(f"Saved xG model - {result['n_rows']} rows, per-strength models: {strength_keys}")


@functools.lru_cache(maxsize=None)
def load_xg_model() -> dict:
    """
    Load the saved xG model bundle (see save_xg_model). Memoized since this is called repeatedly across a pipeline run; call load_xg_model.cache_clear() if the model is ever retrained mid-process.

    :return: The saved xG model bundle dict
    """
    path = os.path.join(DATA_DIR, 'player_card_data', 'processed_data', 'xg_models', 'xg_model.pkl')
    with open(path, 'rb') as f:
        model_bundle = pickle.load(f)
    return model_bundle


def nearest_trained_strength(strength: str, trained_strengths: set) -> str:
    """
    Map a raw Strength label to the closest strength state with its own trained xG model, for shots
    in a strength state too rare to clear constants.STRENGTH_MIN_ROWS on its own.

    :param strength: The raw str Strength label for one shot
    :param trained_strengths: The set of str strength labels with their own trained model
    :return: The str strength label to actually predict this shot with (a key in trained_strengths), or None if trained_strengths is empty
    """
    if not trained_strengths:
        return None
    if strength in trained_strengths:
        return strength

    match = re.match(r'^(\d+)v(\d+)', str(strength))
    if not match:
        return '5v5' if '5v5' in trained_strengths else next(iter(trained_strengths))

    own = min(max(int(match.group(1)), 3), 5)
    opp = min(max(int(match.group(2)), 3), 5)
    own_diff = own - opp

    best_strength, best_key = None, None
    for candidate in trained_strengths:
        cand_match = re.match(r'^(\d+)v(\d+)$', candidate)
        if not cand_match:
            continue
        cand_own, cand_opp = int(cand_match.group(1)), int(cand_match.group(2))
        key = (abs((cand_own - cand_opp) - own_diff), abs(cand_own - own) + abs(cand_opp - opp))
        if best_key is None or key < best_key:
            best_key, best_strength = key, candidate

    if best_strength is None:
        best_strength = '5v5' if '5v5' in trained_strengths else next(iter(trained_strengths))
    return best_strength


def predict_xg_by_strength(df: pd.DataFrame, bundle: dict) -> np.ndarray:
    """
    Route each shot to its per-strength model, falling back to the nearest trained strength state (see nearest_trained_strength) for a shot whose exact strength has no dedicated model, so every shot gets a real prediction.

    :param df: A feature-engineered, strength-tagged shot-events DataFrame
    :param bundle: The xG model bundle, with a 'by_strength' dict of per-strength sub-bundles
    :return: An array of predicted xG probabilities, one per row; NaN only if bundle has no trained strengths at all
    """
    result = np.full(len(df), np.nan)
    trained_strengths = set(bundle['by_strength'].keys())
    if not trained_strengths:
        return result

    # Every shot's actual Strength is mapped once to the strength model it'll be scored with, so an untrained/rare state doesn't fall through to NaN
    routed_strength = df['Strength'].map(lambda s: nearest_trained_strength(s, trained_strengths))

    for strength, sub_bundle in bundle['by_strength'].items():
        mask = (routed_strength == strength).to_numpy()
        if not mask.any():
            continue
        sub = df[mask].copy()
        sub = prep_categoricals(sub, sub_bundle['categories'],
                                  cat_features=sub_bundle['categorical_features'])
        X = sub[sub_bundle['feature_columns']]
        result[mask] = sub_bundle['model'].predict_proba(X)[:, 1]

    return result


def predict_xg(shots_df: pd.DataFrame, season: str = None, bundle: dict = None) -> np.ndarray:
    """
    Score shot events with the trained xG model, attaching Strength/Score State/handedness features first if not already present.

    :param shots_df: A shot-events DataFrame
    :param season: An optional str season ('YYYY-YYYY'), required to attach a 'Strength' column if not already present
    :param bundle: An optional pre-loaded xG model bundle; loaded from disk if not given
    :return: An array of predicted xG probabilities, one per row
    """
    if bundle is None:
        bundle = load_xg_model()

    # Attach whichever required features aren't already present
    df = engineer_features(shots_df)
    if 'Off Wing' not in df.columns:
        df = attach_handedness_features(df)
    if 'Strength' not in df.columns:
        df = attach_strength_state(df, season)
    if 'Score State' not in df.columns:
        df = attach_score_state_to_shots(df)

    df = df.reset_index(drop=True)
    xg_values = predict_xg_by_strength(df, bundle)
    return xg_values


# ====================================================================================================
# PLAYER/TEAM-LEVEL XG AGGREGATES
# ====================================================================================================

def compute_player_xg(season: str, bundle: dict = None, stints_df: pd.DataFrame = None) -> pd.DataFrame:
    """
    Every skater's own individual xG (ixG) for a season, both a season-total and a 5v5-only breakdown, from this project's own shot-event-based model.

    :param season: A str representing the season ('YYYY-YYYY')
    :param bundle: An optional pre-loaded xG model bundle; loaded from disk if not given
    :param stints_df: An optional pre-built season stints DataFrame, used to strength-tag shots
    :return: A DataFrame of 'ixG_all'/'ixG_5v5' indexed by Player ID
    """
    shots_df = data_io.load_shot_events_csv(season)

    shots_df = shots_df[shots_df['Event Type'].isin(UNBLOCKED_SHOT_EVENTS)].copy()
    shots_df = shots_df.dropna(subset=['Shooter Player ID'])
    if shots_df.empty:
        result = pd.DataFrame(columns=['ixG_all', 'ixG_5v5'])
    else:
        if stints_df is not None:
            shots_df = attach_strength_state_from_stints(shots_df, stints_df)
        else:
            shots_df = attach_strength_state(shots_df, season)

        if bundle is None:
            bundle = load_xg_model()
        shots_df['xG'] = predict_xg(shots_df, season=season, bundle=bundle)
        shots_df['Shooter Player ID'] = shots_df['Shooter Player ID'].astype(int)

        # Season-total ixG, plus a 5v5-only breakdown
        all_situations = shots_df.groupby('Shooter Player ID')['xG'].sum().rename('ixG_all')
        es_only = (
            shots_df[shots_df['Strength'] == '5v5']
            .groupby('Shooter Player ID')['xG'].sum().rename('ixG_5v5')
        )

        result = pd.concat([all_situations, es_only], axis=1)
        result['ixG_5v5'] = result['ixG_5v5'].fillna(0.0)
        result.index = result.index.rename('Player ID')
    return result


def make_and_save_xg_model(seasons: list = None) -> None:
    """
    Train and save the xG model in one call, mirroring rapm.make_and_save_rapm_scores' role for RAPM.

    :param seasons: An optional list of str seasons ('YYYY-YYYY') to train on; defaults to constants.DATA_SEASONS
    :return: None
    """

    if seasons is None:
        seasons = constants.DATA_SEASONS

    # Train then immediately persist
    result = train_xg_model(seasons)
    save_xg_model(result)
