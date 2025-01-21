
"""
Functions to determine a player's score in the following aspects of the game:

Total Offense               (offensive_score)
Total Defence               (defensive_score)
Even Strength Offence       (ev_offence_score)
Even Strength Defence       (ev_defense_score)
Powerplay                   (power_play_score)
Penalty Kill                (penalty_kill_score)
Shooting                    (shooting_score)
Playmaking                  (playmaking_score)
Physicality                 (physicality_score)
Speed                       (speed_score)
"""

# For overall offensive score and even strength offensive score
def offensive_score(row):
    # Define weights for each metric
    off_weights = {
        'goals': 100,
        'p_assists' : 55,
        's_assists' : 15,
        'low_danger_shots' : 3,
        'med_danger_shots' : 5,
        'high_danger_shots' : 10,
        'blocked_shots' : -2,
        'missed_shots' : -1,
        'ld_shots_onice' : 1,
        'md_shots_onice' : 2,
        'hd_shots_onice' : 3,
        'ld_goals_onice' : 3,
        'md_goals_onice' : 4,
        'hd_goals_onice' : 5
    }

    # Compute total offensive score
    tot_off_score = (
        off_weights['goals'] * row['I_F_goals'] +
        off_weights['p_assists'] * row['I_F_primaryAssists'] +
        off_weights['s_assists'] * row['I_F_secondaryAssists'] +
        off_weights['low_danger_shots'] * row['I_F_lowDangerShots'] +
        off_weights['med_danger_shots'] * row['I_F_mediumDangerShots'] +
        off_weights['high_danger_shots'] * row['I_F_highDangerShots'] +
        off_weights['blocked_shots'] * row['I_F_blockedShotAttempts'] +
        off_weights['missed_shots'] * row['I_F_missedShots'] +
        off_weights['ld_shots_onice'] * row['OnIce_F_lowDangerShots'] +
        off_weights['md_shots_onice'] * row['OnIce_F_mediumDangerShots'] +
        off_weights['hd_shots_onice'] * row['OnIce_F_highDangerShots'] +
        off_weights['ld_goals_onice'] * row['OnIce_F_lowDangerGoals'] +
        off_weights['md_goals_onice'] * row['OnIce_F_mediumDangerGoals'] +
        off_weights['hd_goals_onice'] * row['OnIce_F_highDangerGoals']
    )

    off_score = tot_off_score / row['games_played']
    return off_score



# For overall defensive score and even strength defensive score
def defensive_score(row):
    # Define weights for each metric
    def_weights = {
        'blocks': 30,
        'takeaways' : 20,
        'giveaways' : -15,
        'd_zone_giveaways' : -20,
        'ld_shots_against' : -0.5,
        'md_shots_against' : -1,
        'hd_shots_against' : -2,
        'ld_goals_against' : -5,
        'md_goals_against' : -3,
        'hd_goals_against' : -1
    }

    # Compute total defensive score
    tot_def_score = (
        def_weights['blocks'] * row['shotsBlockedByPlayer'] +
        def_weights['takeaways'] * row['I_F_takeaways'] +
        def_weights['giveaways'] * row['I_F_giveaways'] +
        def_weights['d_zone_giveaways'] * row['I_F_dZoneGiveaways'] +
        def_weights['ld_shots_against'] * row['OnIce_A_lowDangerShots'] +
        def_weights['md_shots_against'] * row['OnIce_A_mediumDangerShots'] +
        def_weights['hd_shots_against'] * row['OnIce_A_highDangerShots'] +
        def_weights['ld_goals_against'] * row['OnIce_A_lowDangerGoals'] +
        def_weights['md_goals_against'] * row['OnIce_A_mediumDangerGoals'] +
        def_weights['hd_goals_against'] * row['OnIce_A_highDangerGoals']
    )

    def_score = tot_def_score / row['games_played']
    return def_score



def power_play_score(row):
    # Check to see if player meets power play toi requirement (60 sec * 41 games = 2460 sec)
    if row['pp_icetime'] < 2460:
        ppl_score = 'N/A'
    else:
        # Define weights for each metric
        ppl_weights = {
            'pp_goals': 100,
            'pp_p_assists' : 55,
            'pp_s_assists' : 15,
        }

        # Compute total power play score
        tot_ppl_score = (
            ppl_weights['pp_goals'] * row['I_F_goals'] +
            ppl_weights['pp_p_assists'] * row['I_F_primaryAssists'] +
            ppl_weights['pp_s_assists'] * row['I_F_secondaryAssists'] 
        )

        ppl_score = tot_ppl_score / row['games_played']
    return ppl_score


def penalty_kill_score(row):
    # Check to see if player meets penalty kill toi requirement (60 sec * 41 games = 2460 sec)
    if row['pk_icetime'] < 2460:
        pkl_score = 'N/A'
    else:
        # Define weights for each metric
        pkl_weights = {
            'blocks' : 30,
            'takeaways' : 20
        }

        # Compute total penalty kill score
        tot_pkl_score = (
            pkl_weights['blocks'] * row['shotsBlockedByPlayer'] +
            pkl_weights['takeaways'] * row['I_F_takeaways'] 
        )

        pkl_score = tot_pkl_score / row['games_played']
    return pkl_score


def shooting_score(row):
    # Define weights for each metric
    sht_weights = {
        'goals': 100,
        'low_danger_shots' : 3,
        'med_danger_shots' : 5,
        'high_danger_shots' : 10,
        'blocked_shots' : -2,
        'missed_shots' : -1,
        'rebounds_created' : 4
    }

    # Compute total shooting score
    tot_sht_score = (
        sht_weights['goals'] * row['I_F_goals'] +
        sht_weights['low_danger_shots'] * row['I_F_lowDangerShots'] +
        sht_weights['med_danger_shots'] * row['I_F_mediumDangerShots'] +
        sht_weights['high_danger_shots'] * row['I_F_highDangerShots'] +
        sht_weights['blocked_shots'] * row['shotsBlockedByPlayer'] +
        sht_weights['missed_shots'] * row['I_F_missedShots'] +
        sht_weights['rebounds_created'] * row['I_F_rebounds']
    )

    sht_score = tot_sht_score / row['games_played']
    return sht_score


def playmaking_score(row):
    # Define weights for each metric
    plm_weights = {
        'p_assists' : 55,
        's_assists' : 15,
        'ld_shots_onice' : 1,
        'md_shots_onice' : 2,
        'hd_shots_onice' : 3,
        'ld_goals_onice' : 3,
        'md_goals_onice' : 4,
        'hd_goals_onice' : 5
    }

    # Compute total playmaking score
    tot_plm_score = (
        plm_weights['p_assists'] * row['I_F_primaryAssists'] +
        plm_weights['s_assists'] * row['I_F_secondaryAssists'] +
        plm_weights['ld_shots_onice'] * row['OnIce_F_lowDangerShots'] +
        plm_weights['md_shots_onice'] * row['OnIce_F_mediumDangerShots'] +
        plm_weights['hd_shots_onice'] * row['OnIce_F_highDangerShots'] +
        plm_weights['ld_goals_onice'] * row['OnIce_F_lowDangerGoals'] +
        plm_weights['md_goals_onice'] * row['OnIce_F_mediumDangerGoals'] +
        plm_weights['hd_goals_onice'] * row['OnIce_F_highDangerGoals']
    )

    plm_score = tot_plm_score / row['games_played']
    return plm_score


def physicality_score(row):
    # Define weights for each metric
    phy_weights = {
        'hits' : 15,
        'pim' : 2,
        'pim_drawn' : 1
    }

    # Compute total physicality score
    tot_phy_score = (
        phy_weights['hits'] * row['I_F_hits'] +
        phy_weights['pim'] * row['penalityMinutes'] +
        phy_weights['pim_drawn'] * row['penaltiesDrawn']
    )

    phy_score = tot_phy_score / row['games_played']
    return phy_score


def speed_score(row):
    # Define weights for each metric
    spd_weights = {
        'speed' : 000
    }

    # Compute total speed score
    tot_spd_score = (
        spd_weights['speed'] * 000  
    )

    spd_score = tot_spd_score / row['games_played']
    return spd_score

