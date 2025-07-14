# ====================================================================================================
# CLASSES FOR GENERATING SCORES FOR NHL PLAYERS BASED ON STATS
# ====================================================================================================

# Imports
import numpy as np


class SkaterScorer:
    def __init__(self, weights: dict):
        self.weights = weights


    def adjust_score(self, score, row, toi_adjust=1):
        gp = row['GP']
        toi = row['TOI'] * toi_adjust

        if score >= 0:
            sigmoid = 0.3 + (1 / (1.43 + np.exp(-0.1 * (gp - 25))))
        else:
            sigmoid = 0.3 + (1 / (1.43 + np.exp(0.1 * (gp - 25))))

        adjusted_score = score * sigmoid
        if toi > 0:
            adjusted_score = (adjusted_score / toi) * 60
        return adjusted_score


    def get_d_zone_percentage(self, row):
        off, defn, neu = row['Off. Zone Starts'], row['Def. Zone Starts'], row['Neu. Zone Starts']
        total = off + defn + neu
        return defn / total if total > 0 else 0.33


    def shooting_score(self, row):
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
        return self.adjust_score(score, row)


    def playmaking_score(self, row):
        score = (
            self.weights['p_assists'] * row['First Assists'] +
            self.weights['s_assists'] * row['Second Assists'] +
            self.weights['rebounds_created'] * row['Rebounds Created'] +
            self.weights['rush_attempts'] * row['Rush Attempts']
        )
        return self.adjust_score(score, row)


    def offensive_score(self, row, oi_players=5):
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
            return self.adjust_score(score, row)


    def defensive_score(self, row, oi_players=5):
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
            return self.adjust_score(score, row, toi_adjust=d_zone_percent)


    def physicality_score(self, row):
        score = (
            self.weights['hits'] * row['Hits'] +
            self.weights['minors'] * row['Minor'] +
            self.weights['majors'] * row['Major'] +
            self.weights['misconducts'] * row['Misconduct']
        )
        return self.adjust_score(score, row)


    def penalties_score(self, row):
        return (
            self.weights['penalty_min_taken'] * row['Total Penalties'] +
            self.weights['penalty_min_drawn'] * row['Penalties Drawn']
        ) / row['GP']


    def faceoff_score(self, row):
        total_fo = row['Faceoffs Won'] + row['Faceoffs Lost']
        if total_fo < row['GP'] * 3:
            return -999999
        score = (
            self.weights['faceoff_wins'] * row['Faceoffs Won'] +
            self.weights['faceoff_losses'] * row['Faceoffs Lost']
        )
        return self.adjust_score(score, row)


class GoalieScorer:
    def __init__(self, weights: dict):
        self.weights = weights


    def adjust_score(self, score, row):
        gp = row['GP']
        if score >= 0:
            sigmoid = 1 / (1 + np.exp(-0.2 * (gp - 30)))
        else:
            sigmoid = 1 / (1 + np.exp(0.2 * (gp - 30)))
        adjusted_score = score * sigmoid
        return adjusted_score / gp if gp > 0 else 0


    def total_score(self, row):
        score = (
            self.weights['hds'] * row['HD Saves'] +
            self.weights['hdga'] * row['HD Goals Against'] +
            self.weights['mds'] * row['MD Saves'] +
            self.weights['mdga'] * row['MD Goals Against'] +
            self.weights['lds'] * row['LD Saves'] +
            self.weights['ldga'] * row['LD Goals Against']
        )
        return self.adjust_score(score, row)


    def score_by_zone(self, row, zone):
        if zone == 'LD':
            score = self.weights['lds'] * row['LD Saves'] + self.weights['ldga'] * row['LD Goals Against']
        elif zone == 'MD':
            score = self.weights['mds'] * row['MD Saves'] + self.weights['mdga'] * row['MD Goals Against']
        elif zone == 'HD':
            score = self.weights['hds'] * row['HD Saves'] + self.weights['hdga'] * row['HD Goals Against']
        else:
            score = 0
        return self.adjust_score(score, row)
