# ====================================================================================================
# FUNCTIONS FOR GENERATING SCORES FOR NHL PLAYERS BASED ON STATS
# ====================================================================================================

# Imports
import numpy as np
from utils import constants

DATA_DIR = constants.DATA_DIR

# ====================================================================================================
# WEIGHTINGS 
# ====================================================================================================

# All weight values
weights = {
    # Shooting Weights
    'goals': 1.000,
    'shots_on_net' : 0.104,
    'shots_missed': 0.052,
    'shots_were_blocked': 0.026,
    'high_danger_chances': 0.000,   # ADD ?

    # Playmaking Weights
    'p_assists': 0.780,
    's_assists': 0.019,             # ADJUST
    'rebounds_created': 0.104,
    'rush_attempts': 0.052,         # ADJUST

    # On Ice Offensive Weights
    'oi_ldsf': 0.043,
    'oi_mdsf': 0.119,
    'oi_hdsf': 0.190,
    'oi_ldgf': 0.000,
    'oi_mdgf': 0.000,
    'oi_hdgf': 0.000,
    'oi_xgf': 1.000,

    # Defensive Weights
    'blocks': 0.104,
    'takeaways': 0.104,             # ADJUST
    'giveaways': -0.104,            # ADJUST

    # On Ice Defensive Weights
    'oi_ldsa': -0.043,
    'oi_mdsa': -0.119,
    'oi_hdsa': -0.190,
    'oi_ldga': -0.000,
    'oi_mdga': -0.000,
    'oi_hdga': -0.000,
    'oi_xga': -1.000,

    # Physicality Weights
    'hits': 1.00,                   # ADJUST
    'minors': 0.50,                 # ADJUST
    'majors': 2.00,                 # ADJUST
    'misconducts': 3.00,            # ADJUST

    # Penalty Differential Weights
    'penalty_min_taken': -1.000,
    'penalty_min_drawn': 1.000,


    # Speed Weights                 Might be used in the future
    'spd_speed': 0.00,

    # Faceoff Weights               Might be used in the future
    'faceoff_wins': 1.000,
    'faceoff_losses': -1.000,


    # Goalie Weights                # ADJUST ?
    'hds': 0.190,
    'mds': 0.119,
    'lds': 0.043,
    'hdga': -1.00,
    'mdga': -1.00, 
    'ldga': -1.00,
}


"""
Weight Explanations - Team data over the past 3 seasons from NaturalStatTrick
=== Individual ===
Goal = 1.000                Base weight for offense
Primary assist = 0.780      Found in blog post - https://analyticswithavery.com/blog/1
Secondary assist = 0.000    Found in blog post - https://analyticswithavery.com/blog/1


Shot = 0.103                Chances the average shot goes in the net (SH%)
LD Shot = 0.043             Chances a MD shot goes in the net (LDSH%)
MD Shot = 0.119             Chances a LD shot goes in the net (MDSH%)
HD Shot = 0.190             Chances a HD shot goes in the net (HDSH%)

Rebound Created = 0.103     Created another shot attempt
Shot Missed = 0.052         Half the weight of a shot that hit
Shot was Blocked = 0.026    Quater the weight of a shot that hit

Block = 0.103               Preventing a shot

=== On Ice ===
Divide stat weights by amount of players on the ice in functions
ex. 5v5 on ice high danger shot against = 0.190 / 5 = 0.038


=== Physicality ===


=== Penalty Differential ===

"""


# ====================================================================================================
# SKATER SCORE FUNCTIONS
# ====================================================================================================

def adjust_skater_score(score, row, toi_adjust=1):
    gp = row['GP']
    toi = row['TOI'] * toi_adjust

    if score >= 0:
        sigmoid = 0.3 + (1 / (1.43 + np.exp(-0.1 * (gp - 25))))
    else:
        sigmoid = 0.3 + (1 / (1.43 + np.exp(0.1 * (gp - 25))))

    adjusted_score = score * sigmoid
    adjusted_score = (adjusted_score / toi) * 60
    return adjusted_score


def adjust_goalie_score(score, row):
    gp = row['GP']

    if score >= 0:
        sigmoid = 1 / (1 + np.exp(-0.2 * (gp - 30)))
    else:
        sigmoid = 1 / (1 + np.exp(0.2 * (gp - 30)))

    adjusted_score = score * sigmoid
    adjusted_score = adjusted_score / gp
    return adjusted_score


def get_d_zone_percentage(row):
    off_zone_starts = row['Off. Zone Starts']
    def_zone_starts = row['Def. Zone Starts']
    neu_zone_starts = row['Neu. Zone Starts']
    total_zone_starts = off_zone_starts + def_zone_starts + neu_zone_starts

    def_zone_percentage = def_zone_starts / total_zone_starts

    return def_zone_percentage


def shooting_score(row):
    #Avoid double counting
    shots_on_net = row['Shots']  - row['Goals']
    shots_missed = row['iFF'] - row['Shots']
    shots_were_blocked = row['iCF'] - row['iFF']
    hd_chances = row['iHDCF'] - row['Goals']

    tot_sht_score = (
        weights['goals'] * row['Goals'] +
        weights['shots_on_net'] * shots_on_net +
        weights['shots_missed'] * shots_missed +
        weights['shots_were_blocked'] * shots_were_blocked +
        weights['high_danger_chances'] * hd_chances
    )

    sht_score = adjust_skater_score(tot_sht_score, row)
    return sht_score


def playmaking_score(row):
    tot_plm_score = (
        weights['p_assists'] * row['First Assists'] +
        weights['s_assists'] * row['Second Assists'] +
        weights['rebounds_created'] * row['Rebounds Created'] +
        weights['rush_attempts'] * row['Rush Attempts']
    )

    plm_score = adjust_skater_score(tot_plm_score, row)
    return plm_score


def offensive_score(row, oi_players=5):

    #Avoid double counting
    shots_on_net = row['Shots']  - row['Goals']
    shots_missed = row['iFF'] - row['Shots']
    shots_were_blocked = row['iCF'] - row['iFF']
    hd_chances = row['iHDCF'] - row['Goals']

    tot_sht_score = (
        weights['goals'] * row['Goals'] +
        weights['shots_on_net'] * shots_on_net +
        weights['shots_missed'] * shots_missed +
        weights['shots_were_blocked'] * shots_were_blocked +
        weights['high_danger_chances'] * hd_chances
    )
    
    tot_plm_score = (
        weights['p_assists'] * row['First Assists'] +
        weights['s_assists'] * row['Second Assists'] +
        weights['rebounds_created'] * row['Rebounds Created'] +
        weights['rush_attempts'] * row['Rush Attempts']
    )

    tot_oi_off_score = (
        weights['oi_ldsf'] * row['LDCF'] +
        weights['oi_mdsf'] * row['MDCF'] +
        weights['oi_hdsf'] * row['HDCF'] +
        weights['oi_ldgf'] * row['LDGF'] +
        weights['oi_mdgf'] * row['MDGF'] +
        weights['oi_hdgf'] * row['HDGF'] +
        weights['oi_xgf'] * row['xGF']
    ) / oi_players

    tot_off_score = tot_sht_score + tot_plm_score + tot_oi_off_score
    
    off_score = adjust_skater_score(tot_off_score, row)
    return off_score


def defensive_score(row, oi_players=5):
    d_zone_percent = get_d_zone_percentage(row)

    tot_def_score = (
        weights['blocks'] * row['Shots Blocked'] +
        weights['takeaways'] * row['Takeaways'] +
        weights['giveaways'] * row['Giveaways'] +
        (weights['oi_ldsa'] * row['LDCA'] +
        weights['oi_mdsa'] * row['MDCA'] +
        weights['oi_hdsa'] * row['HDCA'] +
        weights['oi_ldga'] * row['LDGA'] +
        weights['oi_mdga'] * row['MDGA'] +
        weights['oi_hdga'] * row['HDGA'] +
        weights['oi_xga'] * row['xGA']) / oi_players
    )

    def_score = adjust_skater_score(tot_def_score, row, d_zone_percent)
    return def_score


def power_play_score(row):
    # Check if pp 'TOI' is in the Series and meets the requirement (0.5 minutes per game played)
    if 'TOI' not in row or row['TOI'] < 41:
        ppl_score = -999999
    else:
        ppl_score = offensive_score(row, oi_players=4)
    return ppl_score


def penalty_kill_score(row):
    # Check if pk 'TOI' is in the Series and meets the requirement (0.5 minutes per game played)
    if 'TOI' not in row or row['TOI'] < row['GP'] * 0.5:
        pkl_score = -999999
    else:
        pkl_score = defensive_score(row, oi_players=4)
    return pkl_score


def physicality_score(row):
    tot_phy_score = (
        weights['hits'] * row['Hits'] +
        weights['minors'] * row['Minor'] +
        weights['majors'] * row['Major'] +
        weights['misconducts'] * row['Misconduct']
    )

    phy_score = adjust_skater_score(tot_phy_score, row)
    return phy_score


def penalties_score(row):
    tot_pen_score = (
        weights['penalty_min_taken'] * row['Total Penalties'] +
        weights['penalty_min_drawn'] * row['Penalties Drawn']    
    )

    pen_score = tot_pen_score /row['GP']
    return pen_score


def faceoff_score(row):         # Might use int the future
    # Check to see if player meets faceoffs requirement (3 faceoffs taken per game played)
    if row['Faceoffs Won'] + row['Faceoffs Lost'] < row['GP'] * 3:
        fof_score = -999999
    else:
        tot_fof_score = (
            weights['faceoff_wins'] * row['Faceoffs Won'] +
            weights['faceoff_losses'] * row['Faceoffs Lost']  
        )

        fof_score = adjust_skater_score(tot_fof_score, row)
    return fof_score


def speed_score(row):         # Might use int the future
    tot_spd_score = (
        weights['spd_speed'] * 0
    )

    spd_score = adjust_skater_score(tot_spd_score, row)
    return spd_score


# ====================================================================================================
# Goalie SCORE FUNCTIONS
# ====================================================================================================

# Used for all, evs, ppl, and pkl
def goalie_all_score(row):
    tot_all_score = (
        weights['hds'] * row['HD Saves'] +
        weights['hdga'] * row['HD Goals Against'] +
        weights['mds'] * row['MD Saves'] +
        weights['mdga'] * row['MD Goals Against'] +
        weights['lds'] * row['LD Saves'] +
        weights['ldga'] * row['LD Goals Against']
    )

    all_score = adjust_goalie_score(tot_all_score, row)
    return all_score


def goalie_ldg_score(row):
    tot_ldg_score = (
        weights['lds'] * row['LD Saves'] +
        weights['ldga'] * row['LD Goals Against']
    )
    
    ldg_score = adjust_goalie_score(tot_ldg_score, row)

    return ldg_score

def goalie_mdg_score(row):

    tot_mdg_score = (
        weights['mds'] * row['MD Saves'] +
        weights['mdga'] * row['MD Goals Against']
    )
    
    mdg_score = adjust_goalie_score(tot_mdg_score, row)

    return mdg_score

def goalie_hdg_score(row):

    tot_hdg_score = (
        weights['hds'] * row['HD Saves'] +
        weights['hdga'] * row['HD Goals Against']
    )
    
    hdg_score = adjust_goalie_score(tot_hdg_score, row)

    return hdg_score
