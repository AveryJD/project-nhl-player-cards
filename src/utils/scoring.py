# ====================================================================================================
# CLASSES FOR GENERATING SCORES FOR NHL PLAYERS BASED ON STATS
# ====================================================================================================

# Imports
import numpy as np
import pandas as pd
from utils import constants


class SkaterScorer:
    def __init__(self):
        self.weights = constants.S_WEIGHTS


    def adjust_score(self, score: np.ndarray, toi: np.ndarray) -> np.ndarray:
        adjusted = np.full_like(score, -999999, dtype=float)
        np.divide(score * 60 + 1e-10, toi, out=adjusted, where=toi > 0)
        return adjusted


    def shooting_score(self, df: pd.DataFrame) -> np.ndarray:
        shots_on_net = df['Shots'].to_numpy()
        shots_missed = (df['iFF'] - df['Shots']).to_numpy()
        shots_blocked = (df['iCF'] - df['iFF']).to_numpy()

        score = (
            self.weights['shots_on_net'] * shots_on_net +
            self.weights['shots_missed'] * shots_missed +
            self.weights['shots_blocked'] * shots_blocked
        )

        adjusted_score = self.adjust_score(score, df['TOI'].to_numpy())
        return adjusted_score


    def scoring_score(self, df: pd.DataFrame) -> np.ndarray:
        goals = df['Goals'].to_numpy()
        x_goals = df['ixG'].to_numpy()

        score = (
            self.weights['goals'] * goals +
            self.weights['x_goals'] * x_goals
        )

        adjusted_score = self.adjust_score(score, df['TOI'].to_numpy())
        return adjusted_score


    def playmaking_score(self, df: pd.DataFrame) -> np.ndarray:
        score = (
            self.weights['p_assists'] * df['First Assists'].to_numpy() +
            self.weights['s_assists'] * df['Second Assists'].to_numpy() +
            self.weights['rebounds_created'] * df['Rebounds Created'].to_numpy() +
            self.weights['rush_attempts'] * df['Rush Attempts'].to_numpy()
        )

        adjusted_score = self.adjust_score(score, df['TOI'].to_numpy())
        return adjusted_score


    def oniceoffense_score(self, df: pd.DataFrame) -> np.ndarray:
        oi_ldsf = df['LDCF']
        oi_mdsf = df['MDCF']
        oi_hdsf = df['HDCF']
        oi_xgoals = df['xGF'] - df['ixG']

        score = (
            self.weights['oi_ldsf'] * oi_ldsf.to_numpy() +
            self.weights['oi_mdsf'] * oi_mdsf.to_numpy() +
            self.weights['oi_hdsf'] * oi_hdsf.to_numpy() +
            self.weights['oi_xgf'] * oi_xgoals.to_numpy()
        )

        adjusted_score = self.adjust_score(score, df['TOI'].to_numpy())
        return adjusted_score
    

    def ozonestarts_score(self, df: pd.DataFrame) -> np.ndarray:
        score = (
            self.weights['o_zone_starts'] * df['Off. Zone Starts'].to_numpy() +
            self.weights['n_zone_starts'] * df['Neu. Zone Starts'].to_numpy() +
            self.weights['d_zone_starts'] * df['Def. Zone Starts'].to_numpy()
        )

        adjusted_score = self.adjust_score(score, df['TOI'].to_numpy())
        return adjusted_score


    def offensive_score(self, df: pd.DataFrame) -> np.ndarray:
        score = (
            self.scoring_score(df) +
            self.shooting_score(df) +
            self.playmaking_score(df) +
            self.oniceoffense_score(df) * 0.2
        )

        return score


    def onicedefense_score(self, df: pd.DataFrame) -> np.ndarray:
        score = (
            self.weights['oi_ldsa'] * df['LDCA'].to_numpy() +
            self.weights['oi_mdsa'] * df['MDCA'].to_numpy() +
            self.weights['oi_hdsa'] * df['HDCA'].to_numpy() +
            self.weights['oi_xga'] * df['xGA'].to_numpy()
        )

        adjusted_score = self.adjust_score(score, df['TOI'].to_numpy())
        return adjusted_score


    def defensive_score(self, df: pd.DataFrame) -> np.ndarray:
        score = (
            self.weights['blocks'] * df['Shots Blocked'].to_numpy() +
            self.weights['takeaways'] * df['Takeaways'].to_numpy() +
            self.weights['giveaways'] * df['Giveaways'].to_numpy()
        )

        adjusted_score = self.adjust_score(score, df['TOI'].to_numpy()) + self.onicedefense_score(df) * 0.2
        return adjusted_score


    def physicality_score(self, df: pd.DataFrame) -> np.ndarray:
        score = (
            self.weights['hits'] * df['Hits'].to_numpy() +
            self.weights['minors'] * df['Minor'].to_numpy() +
            self.weights['majors'] * df['Major'].to_numpy() +
            self.weights['misconducts'] * df['Misconduct'].to_numpy()
        )

        adjusted_score = self.adjust_score(score, df['TOI'].to_numpy())
        return adjusted_score


    def penalties_score(self, df: pd.DataFrame) -> np.ndarray:
        score = (
            self.weights['penalties_taken'] * df['Total Penalties'].to_numpy() +
            self.weights['penalties_drawn'] * df['Penalties Drawn'].to_numpy()
        )

        adjusted_score = self.adjust_score(score, df['TOI'].to_numpy())
        return adjusted_score


    def faceoff_score(self, df: pd.DataFrame) -> np.ndarray:
        total_fo = df['Faceoffs Won'] + df['Faceoffs Lost']
        valid = total_fo >= df['GP'] * 3

        score = (
            self.weights['faceoff_wins'] * df['Faceoffs Won'].to_numpy() +
            self.weights['faceoff_losses'] * df['Faceoffs Lost'].to_numpy()
        )

        adjusted_score = self.adjust_score(score, df['TOI'].to_numpy())
        return np.where(valid, adjusted_score, -999999)
    

    def fantasy_score(self, all_df: pd.DataFrame, ppl_df: pd.DataFrame, pkl_df: pd.DataFrame) -> np.ndarray:
        score = (
            self.weights['fan_goals'] * all_df['Goals'].to_numpy() +
            self.weights['fan_assists'] * all_df['Total Assists'].to_numpy() +
            self.weights['fan_shots'] * all_df['Shots'].to_numpy() +
            self.weights['fan_blocks'] * all_df['Shots Blocked'].to_numpy() +
            self.weights['fan_pp_points'] * ppl_df['Total Points'].to_numpy() +
            self.weights['fan_pk_points'] * pkl_df['Total Points'].to_numpy() 
        )

        adjusted_score = score / all_df['GP'].to_numpy()

        return adjusted_score



class GoalieScorer:
    def __init__(self):
        self.weights = constants.G_WEIGHTS


    def adjust_score(self, score: np.ndarray, toi: np.ndarray) -> np.ndarray:
        adjusted = np.full_like(score, -999999, dtype=float)
        np.divide(score * 60 + 1e-10, toi, out=adjusted, where=toi > 0)
        return adjusted


    def total_score(self, df: pd.DataFrame) -> np.ndarray:
        gsax = df['xG Against'] - df['Goals Against']
        score = (
            self.weights['hds'] * df['HD Saves'].to_numpy() +
            self.weights['hdga'] * df['HD Goals Against'].to_numpy() +
            self.weights['mds'] * df['MD Saves'].to_numpy() +
            self.weights['mdga'] * df['MD Goals Against'].to_numpy() +
            self.weights['lds'] * df['LD Saves'].to_numpy() +
            self.weights['ldga'] * df['LD Goals Against'].to_numpy() +
            self.weights['gsax'] * gsax.to_numpy()
        )
        adjusted_score = self.adjust_score(score, df['TOI'].to_numpy())
        return adjusted_score


    def zone_score(self, df: pd.DataFrame, zone: str) -> np.ndarray:
        if zone == 'LD':
            score = (
                self.weights['lds'] * df['LD Saves'].to_numpy() +
                self.weights['ldga'] * df['LD Goals Against'].to_numpy()
            )
        elif zone == 'MD':
            score = (
                self.weights['mds'] * df['MD Saves'].to_numpy() +
                self.weights['mdga'] * df['MD Goals Against'].to_numpy()
            )
        elif zone == 'HD':
            score = (
                self.weights['hds'] * df['HD Saves'].to_numpy() +
                self.weights['hdga'] * df['HD Goals Against'].to_numpy()
            )

        adjusted_score = self.adjust_score(score, df['TOI'].to_numpy())
        return adjusted_score
