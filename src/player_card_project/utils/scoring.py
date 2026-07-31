# ====================================================================================================
# FUNCTIONS FOR SCORING PLAYER ATTRIBUTES
# ====================================================================================================

# Imports
import numpy as np
import pandas as pd
from player_card_project.utils import player_stats
from player_card_project.utils import constants
from player_card_project.utils import load_save as file



class SkaterScorer:

    def __init__(self, position: str, season: str):
        """
        :param position: A str representing the position ('F' or 'D')
        :param season: A str representing the season ('YYYY-YYYY')
        """
        self.position = position
        self.season = season
        self.war_by_player = self.build_war_lookup(position, season)


    def adjust_score(self, score: np.ndarray, toi: np.ndarray) -> np.ndarray:
        """
        Convert a raw score to a per-60-minute rate.

        :param score: The score to be rate adjusted
        :param toi: the time on ice
        :return: An array of per-60 rates
        """
        adjusted_score = np.full_like(score, np.nan, dtype=float)
        np.divide(score * 60, toi, out=adjusted_score, where=toi > 0)
        return adjusted_score


    def build_war_lookup(self, position: str, season: str) -> pd.DataFrame:
        """
        Build a player to WAR row lookup table for the position and season.

        :param position: A str representing the position ('F' or 'D')
        :param season: A str representing the season ('YYYY-YYYY')
        :return: A DataFrame indexed by Player name with WAR columns, restricted to this position
        """

        war_df = file.load_skater_war_scores_csv(season)
        player_ids_df = file.load_player_ids_csv(season)

        war_df = war_df[war_df['Position'] == position]
        id_map = player_ids_df[['Player', 'Player ID']].drop_duplicates(subset='Player ID')
        war_with_names = war_df.merge(id_map, on='Player ID', how='inner')

        war_lookup = war_with_names.drop_duplicates(subset='Player').set_index('Player')
        return war_lookup


    def lookup_war(self, df: pd.DataFrame, war_col: str) -> np.ndarray:
        """
        Look up war column for each player in df.

        :param df: A DataFrame indexed by a 'Player' level
        :param war_col: The war column to get the score for
        :return: An array of WAR values
        """
        players = df.index.get_level_values('Player')

        war_values = players.map(self.war_by_player[war_col]).to_numpy(dtype=float)
        return war_values


    def total_war_score(self, df: pd.DataFrame) -> np.ndarray:
        """
        Total score: this player's own total war for the season.

        :param df: A DataFrame containing the player's all-situations stats
        :return: An array of total WAR values
        """
        total_score = self.lookup_war(df, 'tot_war')
        return total_score


    def offensive_war_score(self, df: pd.DataFrame, is_ppl: bool = False) -> np.ndarray:
        """
        Offense score: this player's own WAR in this situation.

        :param df: A DataFrame containing the player's stats for one situation (5v5 or 5v4)
        :param is_ppl: Whether df is power play (5v4) stats (looks up ppl_war instead of evo_war)
        :return: An array of offense WAR values
        """
        offense_score = self.lookup_war(df, 'ppl_war' if is_ppl else 'evo_war')
        return offense_score


    def defensive_war_score(self, df: pd.DataFrame, is_pkl: bool = False) -> np.ndarray:
        """
        Defense score: this player's own WAR in this situation.

        :param df: A DataFrame containing the player's stats in all situations
        :param is_pkl: Whether df is penalty kill (4v5) stats (looks up pkl_war instead of evd_war)
        :return: An array of defense WAR values
        """
        defense_score = self.lookup_war(df, 'pkl_war' if is_pkl else 'evd_war')
        return defense_score


    def finishing_war_score(self, df: pd.DataFrame) -> np.ndarray:
        """
        Finishing score: this player's own finishing WAR (goals above xG).

        :param df: A DataFrame containing the player's stats in all situations
        :return: An array of finishing WAR values
        """
        finishing_score = self.lookup_war(df, 'fin_war')
        return finishing_score


    def penalty_war_score(self, df: pd.DataFrame) -> np.ndarray:
        """
        Penalty WAR score: this player's own penalties WAR (net penalty drawing/taking).

        :param df: A DataFrame containing the player's all-situations stats
        :return: An array of penalty WAR values
        """
        penalty_score = self.lookup_war(df, 'pen_war')
        return penalty_score


    def secondary_score(self, df: pd.DataFrame, stat_str: str, total: bool = False) -> np.ndarray:
        """
        Compute one of the card's secondary (non-WAR) stat scores.

        :param df: A DataFrame containing the player's stats for the relevant situation
        :param stat_str: One of 'ixG', 'Goals', 'Assists', 'Physicality', 'PDO', or 'O-Zone Starts'
        :param total: If True, return the raw season value instead of the per-60 rate
        :return: An array of secondary scores
        """
        if stat_str == 'Assists':
            score = df['First Assists'].to_numpy() * 0.8 + df['Second Assists'].to_numpy() * 0.2
        elif stat_str == 'Physicality':
            score = df['Hits'].to_numpy() + df['Hits Taken'].to_numpy() * 0.5
        elif stat_str == 'O-Zone Starts':
            off_starts = df['Off. Zone Starts'].to_numpy()
            total_starts = off_starts + df['Neu. Zone Starts'].to_numpy() + df['Def. Zone Starts'].to_numpy()
            score = off_starts / total_starts * 100
        else:   # Goals, ixG, PDO
            score = df[stat_str].to_numpy()

        if total:
            final_score = score
        else:
            final_score = self.adjust_score(score, df['TOI'].to_numpy())
        return final_score



class GoalieScorer:

    def __init__(self, season: str):
        """
        :param season: A str representing the season ('YYYY-YYYY')
        """
        self.season = season
        self.war_by_player = self.build_goalie_war_lookup(season)
        self.game_gsax = self.buildgame_gsax_lookup(season)


    def adjust_score(self, score: np.ndarray, toi: np.ndarray) -> np.ndarray:
        """
        Convert a raw score to a per-60-minute rate.

        :param score: The score to be rate adjusted
        :param toi: the time on ice
        :return: An array of per-60 rates
        """
        adjusted = np.full_like(score, np.nan, dtype=float)
        np.divide(score * 60, toi, out=adjusted, where=toi > 0)
        return adjusted


    def build_goalie_war_lookup(self, season: str):
        """
        Build a player to WAR row lookup table for the season.

        :param season: A str representing the season ('YYYY-YYYY')
        :return: A DataFrame with WAR values
        """
        war_df = file.load_goalie_war_scores_csv(season)
        player_ids_df = file.load_player_ids_csv(season)

        id_map = (player_ids_df[player_ids_df['Position'] == 'G'][['Player', 'Team', 'Player ID']].drop_duplicates(subset='Player ID'))
        war_with_names = war_df.merge(id_map, on='Player ID', how='inner')
        goalie_war_lookup = war_with_names.drop_duplicates(subset=['Player', 'Team']).set_index(['Player', 'Team'])
        return goalie_war_lookup


    def buildgame_gsax_lookup(self, season: str):
        """
        Build a per-game GSAx lookup table for the season.

        :param season: A str representing the season ('YYYY-YYYY')
        :return: A DataFrame with goalie stats
        """
        game_gsax_df = player_stats.compute_goalie_game_gsax(season)

        return game_gsax_df


    def lookup_goalie_war(self, df: pd.DataFrame, war_col: str) -> np.ndarray:
        """
        Look up war_col for each goalie row in df, gated on positive TOI.

        :param df: A DataFrame with a 'TOI' column
        :param war_col: One of 'evs_war', 'pkl_war', 'tot_war'
        :return: An array of WAR values
        """

        war_values = df.index.map(self.war_by_player[war_col]).to_numpy(dtype=float)
        return war_values


    def total_war_score(self, df: pd.DataFrame) -> np.ndarray:
        """
        Total score: this player's own total war for the season.

        :param df: A DataFrame containing the goalie's all-situations stats
        :return: An array of total WAR values
        """
        total_score = self.lookup_goalie_war(df, 'tot_war')
        return total_score


    def evs_war_score(self, df: pd.DataFrame) -> np.ndarray:
        """
        Total score: this player's own 5v5 war for the season.

        :param df: A DataFrame containing the goalie's 5v5 stats
        :return: An array of 5v5 WAR values
        """
        evs_score = self.lookup_goalie_war(df, 'evs_war')
        return evs_score


    def pkl_war_score(self, df: pd.DataFrame) -> np.ndarray:
        """
        Total score: this player's own 4v5 war for the season.

        :param df: A DataFrame containing the goalie's 4v5 stats
        :return: An array of penalty kill WAR values
        """
        pkl_score = self.lookup_goalie_war(df, 'pkl_war')
        return pkl_score


    def zone_score(self, df: pd.DataFrame, zone: str) -> np.ndarray:
        """
        xG Against minus Goals Against for a specific zone

        :param df: A DataFrame containing the goalie's stats
        :param zone: One of 'HD', 'MD', 'LD'
        :param total: If True, return the raw season total instead of the per-60 rate
        :return: An array of zone GSAx scores (per-60 unless total=True); NaN for zero TOI
        """
        score = df[f'{zone} xG Against'].to_numpy() - df[f'{zone} Goals Against'].to_numpy()
        adjusted_score = self.adjust_score(score, df['TOI'].to_numpy())
        return adjusted_score


    def start_score(self, all_df: pd.DataFrame, logs_df: pd.DataFrame, level: str) -> np.ndarray:
        """
        Rate of Great/Quality/Bad/Awful starts (qualifying starts / games played), by per-game GSAx.

        :param all_df: A DataFrame containing the goalie's all-situations stats
        :param logs_df: A DataFrame of goalie game logs
        :param level: One of 'Great', 'Quality', 'Bad', 'Awful'
        :return: An array of qualifying-start rates
        """

        if 'Player' not in logs_df.columns:
            logs_df = logs_df.reset_index()

        merged = logs_df.merge(self.game_gsax[['Player ID', 'Game ID', 'GSAx']],
                                on=['Player ID', 'Game ID'], how='left')

        if level == 'Great':
            merged['flag'] = (merged['GSAx'] >= constants.GREAT_START_GSAX).astype(float)
        elif level == 'Quality':
            merged['flag'] = (merged['GSAx'] >= constants.QUALITY_START_GSAX).astype(float)
        elif level == 'Bad':
            merged['flag'] = (merged['GSAx'] < constants.QUALITY_START_GSAX).astype(float)
        elif level == 'Awful':
            merged['flag'] = (merged['GSAx'] <= constants.AWFUL_START_GSAX).astype(float)

        merged.loc[merged['GSAx'].isna(), 'flag'] = np.nan

        score = merged.groupby(['Player', 'Team'])['flag'].sum()
        score = score.reindex(all_df.index)
        games_played = all_df['GP'].reindex(all_df.index)

        adjusted_score = score / games_played
        if level in ('Bad', 'Awful'):
            adjusted_score = -adjusted_score
        start_rate = adjusted_score.to_numpy()
        return start_rate


    def rebound_score(self, df: pd.DataFrame) -> np.ndarray:
        """
        Rebound danger allowed: negated 'Rebound xG Against'.

        :param df: A DataFrame containing the goalie's stats (must have 'Rebound xG Against', 'TOI')
        :return: An array of Rebound scores (-Rebound xG Against/60); NaN for zero TOI
        """
        score = -df['Rebound xG Against'].to_numpy()

        adjusted_score = self.adjust_score(score, df['TOI'].to_numpy())
        return adjusted_score


    def team_d_score(self, df: pd.DataFrame) -> np.ndarray:
        """
        Team Defense: negated 5v5 Team xG Against per 60 (shot quality allowed by the skaters).

        :param df: A DataFrame containing the goalie's 5v5 stats
        :return: An array of Team Defense scores
        """
        score = -df['xG Against'].to_numpy()

        adjusted_score = self.adjust_score(score, df['TOI'].to_numpy())
        return adjusted_score


    def workload_score(self, df: pd.DataFrame) -> np.ndarray:
        """
        Workload: total games played plus total TOI (in hours) this season.

        :param df: A DataFrame containing the goalie's all-situations stats
        :return: An array of durability scores
        """
        games_played = df['GP'].to_numpy(dtype=float)
        toi_hours = df['TOI'].to_numpy(dtype=float) / 60.0
        workload = games_played + toi_hours
        return workload



# Quality of teammates/competition scoring

def build_player_id_map(season: str, position: str) -> pd.DataFrame:
    """
    Build a Player to Player ID lookup for a season.

    :param season: A str representing the season ('YYYY-YYYY')
    :param position: A str representing the position ('F' or 'D')
    :return: A DataFrame with player information
    """
    player_ids_df = file.load_player_ids_csv(season)

    if position is not None:
        player_ids_df = player_ids_df[player_ids_df['Position'] == position]
        dedup_subset = ['Player']
    else:
        dedup_subset = ['Player', 'Position']

    player_id_map = player_ids_df[['Player', 'Position', 'Player ID']].drop_duplicates(subset=dedup_subset)
    return player_id_map


def compute_score_based_talent(scores_df: pd.DataFrame, id_map: pd.DataFrame, talent_col: str) -> pd.Series:
    """
    Build a talent proxy per Player ID from a player's own raw WAR score, used to weight QoT/QoC.

    :param scores_df: A DataFrame with WAR scores
    :param id_map: A DataFrame with player information
    :param talent_col: The WAR score column to use as the talent proxy
    :return: A Series of talent values
    """
    flat = scores_df[[talent_col, 'Position']].rename(columns={talent_col: 'Talent'}).reset_index()[['Player', 'Position', 'Talent']].copy()

    # Collapse a player with multiple team rows (ex. traded) to one talent value
    flat = flat.groupby(['Player', 'Position'], as_index=False)['Talent'].mean()

    merged = flat.merge(id_map, on=['Player', 'Position'], how='inner')
    talent_by_id = merged.set_index('Player ID')['Talent']
    talent_by_id = talent_by_id[~talent_by_id.index.duplicated(keep='first')]

    return talent_by_id


def weighted_quality(toi_df: pd.DataFrame, talent_by_id: pd.Series) -> pd.DataFrame:
    """
    Compute the shared-TOI-weighted average talent for every player from a long-format TOI table.

    :param toi_df: A DataFrame with players shared TOI with other players
    :param talent_by_id: A Series of talent values
    :return: A DataFrame with quality and sample
    """
    work = toi_df.copy()
    work['Talent'] = work['Other Player ID'].map(talent_by_id)
    work = work.dropna(subset=['Talent'])

    work['Weighted'] = work['Shared TOI'] * work['Talent']
    grouped = work.groupby('Player ID').agg(Weighted=('Weighted', 'sum'), Sample=('Shared TOI', 'sum'))

    result = pd.DataFrame(index=grouped.index)
    result['Quality'] = grouped['Weighted'] / grouped['Sample']
    result['Sample'] = grouped['Sample']

    return result


def compute_quality_metrics(season: str, scores_df: pd.DataFrame, situation: str, talent_col: str, position: str = None) -> pd.DataFrame:
    """
    Compute QoT and QoC for every player in a season, restricted to one strength situation.

    :param season: A str representing the season ('YYYY-YYYY')
    :param scores_df: A DataFrame with WAR scores
    :param situation: A str strength situation to restrict to one of 'ES', 'PP', 'PK'
    :param talent_col: The score column to use as the talent proxy
    :param position: A str representing the position ('F' or 'D'), or None
    :return: A DataFrame with QoT/QoC scores ans samples
    """

    id_map = build_player_id_map(season, position=None)
    teammate_toi_df = file.load_teammate_toi_csv(season)
    competition_toi_df = file.load_competition_toi_csv(season)

    if 'Situation' in teammate_toi_df.columns:
        teammate_toi_df = teammate_toi_df[teammate_toi_df['Situation'] == situation]
    if 'Situation' in competition_toi_df.columns:
        competition_toi_df = competition_toi_df[competition_toi_df['Situation'] == situation]

    talent_by_id = compute_score_based_talent(scores_df, id_map, talent_col=talent_col)

    qot_df = weighted_quality(teammate_toi_df, talent_by_id)
    qoc_df = weighted_quality(competition_toi_df, talent_by_id)

    name_map = id_map if position is None else id_map[id_map['Position'] == position]
    id_to_player = name_map.drop_duplicates('Player ID').set_index('Player ID')['Player']

    qot_df = qot_df.rename(columns={'Quality': 'qot_score', 'Sample': 'qot_sample'})
    qoc_df = qoc_df.rename(columns={'Quality': 'qoc_score', 'Sample': 'qoc_sample'})

    quality_df = qot_df.join(qoc_df, how='outer')
    quality_df.index = quality_df.index.map(id_to_player)
    quality_df.index.name = 'Player'
    quality_df = quality_df[quality_df.index.notna()]

    return quality_df


def attach_quality_to_scores(scores_df: pd.DataFrame, quality_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add qot_score/qot_sample/qoc_score/qoc_sample columns onto a scores DataFrame.

    :param scores_df: A DataFrame with player scores
    :param quality_df: A DataFrame with QoT/QoC information
    :return: The scores DataFrame with quality information added
    """
    result = scores_df.copy()
    players = result.index.get_level_values('Player')

    for col in ['qot_score', 'qot_sample', 'qoc_score', 'qoc_sample']:
        result[col] = players.map(quality_df[col])

    return result


def average_quality_metrics(quality_a: pd.DataFrame, quality_b: pd.DataFrame) -> pd.DataFrame:
    """
    Average two quality DataFrames' qot_score/qoc_score columns together.

    :param quality_a: A quality DataFrame
    :param quality_b: A second quality DataFrame to average against
    :return: A DataFrame with QoT/QoC information
    """
    index = quality_a.index.union(quality_b.index)
    averaged = pd.DataFrame(index=index)
    for col in ['qot_score', 'qoc_score']:
        a_col = quality_a[col].reindex(index) if col in quality_a.columns else pd.Series(pd.NA, index=index, dtype='float64')
        b_col = quality_b[col].reindex(index) if col in quality_b.columns else pd.Series(pd.NA, index=index, dtype='float64')
        averaged[col] = pd.concat([a_col, b_col], axis=1).mean(axis=1)
    return averaged