# ====================================================================================================
# CLASSES FOR GENERATING SCORES FOR NHL PLAYERS BASED ON STATS
# ====================================================================================================

# Imports
import numpy as np
from utils import constants


class SkaterScorer:
    def __init__(self, weights: dict):
        self.weights = weights


    def adjust_score(self, score, row, season, toi_adjust=1):
        gp = row['GP']
        toi = row['TOI'] * toi_adjust

        # Adjust based on number of games in the season (default to 82)
        total_games = constants.SEASON_GAMES.get(season, 82)
        gp_factor = gp / total_games

        # Sigmoid weighting based on normalized GP
        if score >= 0:
            sigmoid = 0.3 + (1 / (1.43 + np.exp(-0.1 * (gp_factor * 82 - 25))))
        else:
            sigmoid = 0.3 + (1 / (1.43 + np.exp(0.1 * (gp_factor * 82 - 25))))

        adjusted_score = score * sigmoid
        adjusted_score = (adjusted_score / toi) * 60

        return adjusted_score


    def get_d_zone_percentage(self, row):
        off_starts, def_starts, neu_starts = row['Off. Zone Starts'], row['Def. Zone Starts'], row['Neu. Zone Starts']
        total_starts = off_starts + def_starts + neu_starts

        dzone_percent = def_starts / total_starts

        return dzone_percent if total_starts > 0 else 0.33


    def shooting_score(self, row, season):
        shots_on_net = row['Shots'] - row['Goals']
        shots_missed = row['iFF'] - row['Shots']
        shots_blocked = row['iCF'] - row['iFF']
        hd_chances = row['iHDCF'] - row['Goals']

        score = (
            self.weights['goals'] * row['Goals'] +
            self.weights['shots_on_net'] * shots_on_net +
            self.weights['shots_missed'] * shots_missed +
            self.weights['shots_were_blocked'] * shots_blocked +
            self.weights['high_danger_chances'] * hd_chances
        )

        return self.adjust_score(score, row, season)


    def playmaking_score(self, row, season):
        score = (
            self.weights['p_assists'] * row['First Assists'] +
            self.weights['s_assists'] * row['Second Assists'] +
            self.weights['rebounds_created'] * row['Rebounds Created'] +
            self.weights['rush_attempts'] * row['Rush Attempts']
        )

        return self.adjust_score(score, row, season)


    def offensive_score(self, row, season, oi_players=5):
        if row.empty:
            return -999999
        else:
            shots_on_net = row['Shots'] - row['Goals']
            shots_missed = row['iFF'] - row['Shots']
            shots_blocked = row['iCF'] - row['iFF']
            hd_chances = row['iHDCF'] - row['Goals']
            oi_lmdcf = row['iSCF'] - row['iHDCF'] - row['Goals']
            oi_hdcf = row['HDCF'] - row['iHDCF']
            oi_xgoals = row['xGF'] - row['ixG']

            score = (
                self.weights['goals'] * row['Goals'] +
                self.weights['shots_on_net'] * shots_on_net +
                self.weights['shots_missed'] * shots_missed +
                self.weights['shots_were_blocked'] * shots_blocked +
                self.weights['high_danger_chances'] * hd_chances +
                self.weights['p_assists'] * row['First Assists'] +
                self.weights['s_assists'] * row['Second Assists'] +
                self.weights['rebounds_created'] * row['Rebounds Created'] +
                self.weights['rush_attempts'] * row['Rush Attempts'] +
                
                (self.weights['oi_lmdsf'] * oi_lmdcf +
                self.weights['oi_hdsf'] * oi_hdcf +
                self.weights['oi_ldgf'] * row['LDGF'] +
                self.weights['oi_mdgf'] * row['MDGF'] +
                self.weights['oi_hdgf'] * row['HDGF'] +
                self.weights['oi_xgf'] * oi_xgoals) / oi_players
            )

            return self.adjust_score(score, row, season)


    def defensive_score(self, row, season, oi_players=5):
        if row.empty:
            return -999999
        else:
            d_zone_percent = self.get_d_zone_percentage(row)
            score = (
                self.weights['blocks'] * row['Shots Blocked'] +
                self.weights['takeaways'] * row['Takeaways'] +
                self.weights['giveaways'] * row['Giveaways'] +
                (self.weights['oi_ldsa'] * row['LDCA'] +
                self.weights['oi_mdsa'] * row['MDCA'] +
                self.weights['oi_hdsa'] * row['HDCA'] +
                self.weights['oi_ldga'] * row['LDGA'] +
                self.weights['oi_mdga'] * row['MDGA'] +
                self.weights['oi_hdga'] * row['HDGA'] +
                self.weights['oi_xga'] * row['xGA']) / oi_players
            )

            return self.adjust_score(score, row, season, toi_adjust=d_zone_percent,)


    def physicality_score(self, row, season):
        score = (
            self.weights['hits'] * row['Hits'] +
            self.weights['minors'] * row['Minor'] +
            self.weights['majors'] * row['Major'] +
            self.weights['misconducts'] * row['Misconduct']
        )

        return self.adjust_score(score, row, season)


    def penalties_score(self, row, season):
        score = (
            self.weights['penalty_min_taken'] * row['Total Penalties'] +
            self.weights['penalty_min_drawn'] * row['Penalties Drawn']
        )
    
        return self.adjust_score(score, row, season)


    def faceoff_score(self, row, season):
        total_fo = row['Faceoffs Won'] + row['Faceoffs Lost']
        if total_fo < row['GP'] * 3:
            return -999999
        score = (
            self.weights['faceoff_wins'] * row['Faceoffs Won'] +
            self.weights['faceoff_losses'] * row['Faceoffs Lost']
        )

        return self.adjust_score(score, row, season)



class GoalieScorer:
    def __init__(self, weights: dict):
        self.weights = weights


    def adjust_score(self, score, row, season=None):
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


    def total_score(self, row, season):
        score = (
            self.weights['hds'] * row['HD Saves'] +
            self.weights['hdga'] * row['HD Goals Against'] +
            self.weights['mds'] * row['MD Saves'] +
            self.weights['mdga'] * row['MD Goals Against'] +
            self.weights['lds'] * row['LD Saves'] +
            self.weights['ldga'] * row['LD Goals Against']
        )

        return self.adjust_score(score, row, season)


    def zone_score(self, row, season, zone):
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
        else:
            score = 0

        return self.adjust_score(score, row, season)

