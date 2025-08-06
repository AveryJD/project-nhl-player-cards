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


    def adjust_score(self, score: float, row: pd.Series, season: str) -> float:
        if score == -999999:
            adjusted_score = -999999

        else:
            gp = row['GP']
            toi = row['TOI']

            rate_score = score / toi * 60
            
            total_games = constants.SEASON_GAMES.get(season, 82)
            effective_gp = total_games * 0.75

            # Sigmoid weighting based on normalized GP
            if score >= 0:
                gp_sigmoid = 0.6 + (1 / (2.5 + np.exp(-0.2 * (gp - effective_gp))))
            else:
                gp_sigmoid = 0.6 + (1 / (2.5 + np.exp(0.2 * (gp - effective_gp))))

            adjusted_score = (rate_score * gp_sigmoid)

        return adjusted_score



    def shooting_score(self, row: pd.Series, season: str) -> float:
        shots_on_net = row['Shots']
        shots_missed = row['iFF'] - row['Shots']
        shots_blocked = row['iCF'] - row['iFF']

        score = (
            self.weights['shots_on_net'] * shots_on_net +
            self.weights['shots_missed'] * shots_missed +
            self.weights['shots_were_blocked'] * shots_blocked
        )

        return self.adjust_score(score, row, season)
    

    def finishing_score(self, row: pd.Series, season: str) -> float:
        goals = row['Goals']
        xgoals = row['ixG']

        goals_above_expected = goals - xgoals

        score = (
            self.weights['goals'] * goals +
            self.weights['goals_above_expected'] * goals_above_expected
        )

        return self.adjust_score(score, row, season)


    def playmaking_score(self, row: pd.Series, season: str) -> float:
        score = (
            self.weights['p_assists'] * row['First Assists'] +
            self.weights['s_assists'] * row['Second Assists'] +
            self.weights['rebounds_created'] * row['Rebounds Created'] +
            self.weights['rush_attempts'] * row['Rush Attempts']
        )

        return self.adjust_score(score, row, season)
    

    def oniceoffense_score(self, row: pd.Series, season: str) -> float:
        oi_cf = (row['LDCF'] + row['MDCF']) - (row['iSCF'] - row['iHDCF'])
        oi_hdcf = row['HDCF'] - row['iHDCF']
        oi_xgoals = row['xGF'] - row['ixG']

        score = (
            self.weights['oi_sf'] * oi_cf +
            self.weights['oi_hdsf'] * oi_hdcf +
            self.weights['oi_xgf'] * oi_xgoals
        )

        return self.adjust_score(score, row, season)


    def offensive_score(self, row: pd.Series, season: str) -> float:
        if row.empty:
            return -999999
        else:
            score = (
                self.finishing_score(row, season) +
                self.shooting_score(row, season) * 0.5 +
                self.playmaking_score(row, season) +
                self.oniceoffense_score(row, season) * 0.15
            )

            return score


    def onicedefense_score(self, row: pd.Series, season: str) -> float:
        if row.empty:
            return -999999
        else:
            score = (
                self.weights['oi_ldsa'] * row['LDCA'] +
                self.weights['oi_mdsa'] * row['MDCA'] +
                self.weights['oi_hdsa'] * row['HDCA'] +
                self.weights['oi_xga'] * row['xGA']
            )

            return self.adjust_score(score, row, season)


    def defensive_score(self, row: pd.Series, season: str) -> float:
        if row.empty:
            return -999999
        else:
            score = (
                self.weights['blocks'] * row['Shots Blocked'] +
                self.weights['takeaways'] * row['Takeaways'] +
                self.weights['giveaways'] * row['Giveaways']
            )

            score = self.adjust_score(score, row, season) + self.onicedefense_score(row, season) * 0.50

            return score
        

    def physicality_score(self, row: pd.Series, season: str) -> float:
        score = (
            self.weights['hits'] * row['Hits'] +
            self.weights['minors'] * row['Minor'] +
            self.weights['majors'] * row['Major'] +
            self.weights['misconducts'] * row['Misconduct']
        )

        return self.adjust_score(score, row, season)


    def penalties_score(self, row: pd.Series, season: str) -> float:
        score = (
            self.weights['penalty_min_taken'] * row['Total Penalties'] +
            self.weights['penalty_min_drawn'] * row['Penalties Drawn']
        )
    
        return self.adjust_score(score, row, season)


    def faceoff_score(self, row: pd.Series, season: str) -> float:
        total_fo = row['Faceoffs Won'] + row['Faceoffs Lost']
        if total_fo < row['GP'] * 3:
            return -999999
        score = (
            self.weights['faceoff_wins'] * row['Faceoffs Won'] +
            self.weights['faceoff_losses'] * row['Faceoffs Lost']
        )

        return self.adjust_score(score, row, season)



class GoalieScorer:
    def __init__(self):
        self.weights = constants.G_WEIGHTS


    def adjust_score(self, score: float, row: pd.Series, season:str=None) -> float:
        gp = row['GP']

        # Adjust based on number of games in the season (default is 82)
        total_games = constants.SEASON_GAMES.get(season, 82)
        gp_factor = gp / total_games

        # Sigmoid weighting based on normalized GP
        if score >= 0:
            sigmoid = 1 / (1 + np.exp(-0.2 * (gp_factor * 82 - 30)))
        else:
            sigmoid = 1 / (1 + np.exp(0.2 * (gp_factor * 82 - 30)))

        adjusted_score = score * sigmoid

        return adjusted_score / gp if gp > 0 else 0


    def total_score(self, row: pd.Series, season: str) -> float:
        score = (
            self.weights['hds'] * row['HD Saves'] +
            self.weights['hdga'] * row['HD Goals Against'] +
            self.weights['mds'] * row['MD Saves'] +
            self.weights['mdga'] * row['MD Goals Against'] +
            self.weights['lds'] * row['LD Saves'] +
            self.weights['ldga'] * row['LD Goals Against']
        )

        return self.adjust_score(score, row, season)


    def zone_score(self, row: pd.Series, season: str, zone) -> float:
        if zone == 'LD':
            score = (
                self.weights['lds'] * row['LD Saves'] +
                self.weights['ldga'] * row['LD Goals Against']
            )
        elif zone == 'MD':
            score = (
                self.weights['mds'] * row['MD Saves'] +
                self.weights['mdga'] * row['MD Goals Against']
            )
        elif zone == 'HD':
            score = (
                self.weights['hds'] * row['HD Saves'] +
                self.weights['hdga'] * row['HD Goals Against']
            )

        return self.adjust_score(score, row, season)

