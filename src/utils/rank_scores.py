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
    'goals': 90,
    'shots_on_net' : 5,
    'shots_missed': -3,
    'shots_were_blocked': -5,
    'high_danger_chances': 12,

    # Playmaking Weights
    'p_assists': 60,
    's_assists': 20,
    'rebounds_created': 4,
    'rush_attempts': 10,

    # Defensive Weights
    'blocks': 22,
    'takeaways': 20,
    'giveaways': -20,
    'oi_goal_differential': 5,
    'oi_shot_differential': 0.5,

    # Physicality Weights
    'hits': 15,
    'minors': 2,
    'majors': 10,
    'misconducts': 15,

    ###### ADD ######
    # Speed Weights 
    'spd_speed': 0,

    # Penalty Differential Weights
    'penalty_min_taken': -1,
    'penalty_min_drawn': 1,

    # Faceoff Weights
    'faceoff_wins': 1,
    'faceoff_losses': -1,

    # Goalie Weights
    'hds': 0.26,
    'mds': 0.13,
    'lds': 0.03,
    'hdga': -1,
    'mdga': -1, 
    'ldga': -0,
}


"""
Weight Explanations:
Goal for a team = 200
    Goal = 90
    Primary assist = 60
    Secondary assist = 20

Shot has ~11% chance of going in
    Block (preventing a shot) = 200 * 0.11 = 22
    Blocked shot (player's shot prevented) = -5
    Missed shot = -3

Low danger shot has ~3% chance of going in
    Low danger shot taken = 3
    Low danger shot against = -3 / 5 = -0.6
Medium danger shot has ~13 chance of going in
    Medium danger shot taken = 13
    Medium danger shot against = -13 / 5 = -2.6
High danger shot has ~26 % chance of going in
    High danger shot taken = 26
    High danger shot against = -26 / 5 = -5.2

    Takeaway = 20
    Giveaway = -20
    D-Zone giveaway = -5 (on top of -20)

    Rebound created
"""


# ====================================================================================================
# SKATER SCORE FUNCTIONS
# ====================================================================================================

def get_zone_start_percentages(row):
    total_starts = row['Off. Zone Starts'] + row['Neu. Zone Starts'] + row['Def. Zone Starts']
    
    # Default equal weighting if no data available
    if total_starts == 0:
        return 0.33, 0.33, 0.33 
    
    o_zone_start_percent = row['Off. Zone Starts'] / total_starts
    n_zone_start_percent = row['Neu. Zone Starts'] / total_starts
    d_zone_start_percent = row['Def. Zone Starts'] / total_starts
    
    return o_zone_start_percent, n_zone_start_percent, d_zone_start_percent



def adjust_scores(score, row):
    SEASON_GAMES = 82
    
    per_game_score = score / row['GP']
    
    # Apply sqrt scaling for better distribution
    base_score = np.sign(per_game_score) * np.sqrt(abs(per_game_score) + 1e-10)
    
    # Apply games played adjustment
    game_adjustment = np.sqrt(row['GP'] / SEASON_GAMES)
    adjusted_score = base_score * game_adjustment
    
    return adjusted_score

def adjust_goalie_score(score, row):

    k=82

    raw_per_60 = (score / row['TOI']) * 60

    # Weighting based on games played
    weight = row['GP'] / (row['GP'] + k)
    adjusted_score = (weight * raw_per_60)

    return adjusted_score


def shooting_score(row):
    shots_on_net = row['Shots']  - row['Goals']
    shots_missed = row['iFF'] - row['Shots']
    shots_were_blocked = row['iCF'] - row['iFF']


    tot_sht_score = (
        weights['goals'] * row['Goals'] +
        weights['shots_on_net'] * shots_on_net +
        weights['shots_missed'] * shots_missed +
        weights['shots_were_blocked'] * shots_were_blocked +
        weights['high_danger_chances'] * row['iHDCF']
    )

    sht_score = adjust_scores(tot_sht_score, row)
    return sht_score


def playmaking_score(row):
    tot_plm_score = (
        weights['p_assists'] * row['First Assists'] +
        weights['s_assists'] * row['Second Assists'] +
        weights['rebounds_created'] * row['Rebounds Created'] +
        weights['rush_attempts'] * row['Rush Attempts']
    )

    plm_score = adjust_scores(tot_plm_score, row)
    return plm_score


def defensive_score(row):
    oi_goal_differential = row['GF'] - row['GA']
    oi_shot_differential = row['SF'] - row['SA']

    base_def_score = (
        weights['blocks'] * row['Shots Blocked'] +
        weights['takeaways'] * row['Takeaways'] +
        weights['giveaways'] * row['Giveaways'] +
        weights['oi_goal_differential'] * oi_goal_differential +
        weights['oi_shot_differential'] * oi_shot_differential
    )

    oZS, _, dZS = get_zone_start_percentages(row)
    
    # Increase defensive score if player has more defensive responsibilities
    adjustment_factor = 1 + (dZS - oZS) * 0.15  # Boost by max 15%
    def_score = base_def_score * adjustment_factor

    return def_score


def offensive_score(row):
    base_off_score = shooting_score(row) + playmaking_score(row)
    
    oZS, _, dZS = get_zone_start_percentages(row)
    
    # Reduce offensive score if a player has an easier offensive workload
    # adjustment_factor = 1 - (oZS - dZS) * 0.1  # Reduce by max 10%
    off_score = base_off_score #* adjustment_factor
    
    return off_score


def power_play_score(row):
    # Check if 'TOI' is in the Series and is a valid number
    if 'TOI' not in row or row['TOI'] < 41:
        ppl_score = -999999
    else:
        ppl_score = offensive_score(row)
    return ppl_score


def penalty_kill_score(row):
    # Check if 'TOI' is in the Series and is a valid number
    if 'TOI' not in row or row['TOI'] < 41:
        pkl_score = -999999
    else:
        pkl_score = defensive_score(row)
    return pkl_score


def physicality_score(row):
    tot_phy_score = (
        weights['hits'] * row['Hits'] +
        weights['minors'] * row['Minor'] +
        weights['majors'] * row['Major'] +
        weights['misconducts'] * row['Misconduct']
    )

    phy_score = adjust_scores(tot_phy_score, row)
    return phy_score


##### ADD #####
def speed_score(row):
    tot_spd_score = (
        weights['spd_speed'] * 0
    )

    spd_score = adjust_scores(tot_spd_score, row)
    return spd_score


def penalties_score(row):
    tot_pen_score = (
        weights['penalty_min_taken'] * row['Total Penalties'] +
        weights['penalty_min_drawn'] * row['Penalties Drawn']    
    )

    pen_score = tot_pen_score /row['GP']
    return pen_score


def faceoff_score(row):
    # Check to see if player meets faceoffs requirement (3 faceoffs taken per game played)
    if row['Faceoffs Won'] + row['Faceoffs Lost'] < row['GP'] * 3:
        fof_score = -999999
    else:
        tot_fof_score = (
            weights['faceoff_wins'] * row['Faceoffs Won'] +
            weights['faceoff_losses'] * row['Faceoffs Lost']  
        )

        fof_score = adjust_scores(tot_fof_score, row)
    return fof_score


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
