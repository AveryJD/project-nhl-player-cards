# ====================================================================================================
# GET PROJECT FILE LOCATION
# ====================================================================================================
import os


def find_data_dir(start_dir: str) -> str:
    """
    Get the data directory for the project (the folder that contains the data_card folder).

    :param start_dir: The directory that this function is being called from
    :return: The directory that contains the data_card folder
    """
    # Traverse up until a folder containing 'card_data' is found
    while True:
        potential_data_dir = os.path.join(start_dir, 'data_card')
        if os.path.exists(potential_data_dir):
            return start_dir
        parent = os.path.dirname(start_dir)
        if parent == start_dir:
            raise FileNotFoundError("Could not find 'card_data' folder")
        start_dir = parent

# Start from the current file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# This is the folder directly above 'card_data' (for standalone card project and website purposes)
DATA_DIR = find_data_dir(CURRENT_DIR)



# ====================================================================================================
# DATA CONSTANTS
# ====================================================================================================

# Positions to scrape stats and bio data for
POSITIONS = ['F', 'D', 'G']

# Situations to scrape stats for
SKATER_SITUATIONS = ['all', '5v5', '5v4', '4v5']
GOALIE_SITUATIONS = ['all', '5v5', '4v5']

# Seasons to scrape stats and bio data for
DATA_SEASONS = ['2025-2026']

# Seasons to make single seasons rankings for
YEARLY_RANK_SEASONS = ['2025-2026', 
                       '2024-2025', '2023-2024', '2022-2023', '2021-2022', '2020-2021', '2019-2020',
                       '2018-2019', '2017-2018', '2016-2017', '2015-2016', '2014-2015', '2013-2014',
                       '2012-2013', '2011-2012', '2010-2011', '2009-2010', '2008-2009', '2007-2008']

# Seasons to make weighted rankings for
WEIGHTED_RANK_SEASONS = ['2025-2026',
                         '2024-2025', '2023-2024', '2022-2023', '2021-2022', '2020-2021', '2019-2020',
                         '2018-2019', '2017-2018', '2016-2017', '2015-2016', '2014-2015', '2013-2014',
                         '2012-2013', '2011-2012', '2010-2011', '2009-2010']

# Seasons to gather total card info for
CARD_INFO_SEASONS = ['2025-2026',
                     '2024-2025', '2023-2024', '2022-2023', '2021-2022', '2020-2021', '2019-2020',
                     '2018-2019', '2017-2018', '2016-2017', '2015-2016', '2014-2015', '2013-2014',
                     '2012-2013', '2011-2012', '2010-2011', '2009-2010']



# ====================================================================================================
# RANKING CONSTANTS
# ====================================================================================================

SKATER_MIN_GP = 25
GOALIE_MIN_GP = 10

SKATER_MIN_PP = 0.75
SKATER_MIN_PK = 0.75
SKATER_MIN_FO = 3

# All weight values
S_WEIGHTS = {
    # Shooting and Scoring Weights
    'goals':            0.100,
    'x_goals':          0.100,
    'shots_on_net' :    0.104,
    'shots_missed':     0.020,
    'shots_blocked':    0.005,

    # Playmaking Weights
    'p_assists':        0.780,
    's_assists':        0.025,
    'rebounds_created': 0.150,
    'rush_attempts':    0.100,

    # Zone Start Weights
    'o_zone_starts':    1.000,
    'n_zone_starts':    0.000,
    'd_zone_starts':   -1.000,

    # On Ice Offensive Weights
    'oi_ldsf':          0.043,
    'oi_mdsf':          0.119,
    'oi_hdsf':          0.190,
    'oi_ldgf':          0.000,
    'oi_mdgf':          0.000,
    'oi_hdgf':          0.000,
    'oi_xgf':           1.000,

    # Defensive Weights
    'blocks':           0.080,
    'takeaways':        0.050,
    'giveaways':       -0.050,

    # On Ice Defensive Weights
    'oi_ldsa':          -0.043,
    'oi_mdsa':          -0.119,
    'oi_hdsa':          -0.190,
    'oi_xga':           -1.000,

    # Penalty Differential Weights
    'penalties_drawn':  1.000,
    'penalties_taken': -1.000,

    # Physicality Weights
    'hits':             1.000,
    'minors':           0.250,
    'majors':           0.500,
    'misconducts':      1.000,

    # Faceoff Weights
    'faceoff_wins':     1.000,
    'faceoff_losses':  -1.000,

    # Fantasy Weights
    'fan_goals':        3.000,
    'fan_assists':      2.000,
    'fan_shots':        0.500,
    'fan_blocks':       0.500,
    'fan_pp_points':    0.500,
    'fan_pk_points':    0.500
}

G_WEIGHTS = {
    # Goalie Weights
    'goals_against':   -0.750,
    'x_goals_against': -0.250,
    'ld_shots':        -0.043,
    'md_shots':        -0.119,
    'hd_shots':        -0.190,
    'ld_saves':         0.043,
    'md_saves':         0.119,
    'hd_saves':         0.190,
    'ld_ga':           -1.000,
    'md_ga':           -1.000,
    'hd_ga':           -1.000,
    'rebounds_given':  -0.010
}



# ====================================================================================================
# NAMING CONSTANTS
# ====================================================================================================

# Position first letters with full names
POSITION_NAMES = {
    'F': 'Forward', 'D': 'Defense', 'G': 'Goalie'
}

# Team abreviations with full names
TEAM_NAMES = {
    'ANA': 'Anaheim Ducks',         'ARI': 'Arizona Coyotes',       'BOS': 'Boston Bruins',
    'BUF': 'Buffalo Sabres',        'CGY': 'Calgary Flames',        'CAR': 'Carolina Hurricanes',
    'CHI': 'Chicago Blackhawks',    'COL': 'Colorado Avalanche',    'CBJ': 'Columbus Blue Jackets',
    'DAL': 'Dallas Stars',          'DET': 'Detroit Red Wings',     'EDM': 'Edmonton Oilers',
    'FLA': 'Florida Panthers',      'LAK': 'Los Angeles Kings',     'MIN': 'Minnesota Wild',
    'MTL': 'Montreal Canadiens',    'NSH': 'Nashville Predators',   'NJD': 'New Jersey Devils',
    'NYI': 'New York Islanders',    'NYR': 'New York Rangers',      'OTT': 'Ottawa Senators',
    'PHI': 'Philadelphia Flyers',   'PIT': 'Pittsburgh Penguins',   'SJS': 'San Jose Sharks',
    'SEA': 'Seattle Kraken',        'STL': 'St. Louis Blues',       'TBL': 'Tampa Bay Lightning',
    'TOR': 'Toronto Maple Leafs',   'VAN': 'Vancouver Canucks',     'UTA': 'Utah Mammoth',
    'VGK': 'Vegas Golden Knights',  'WSH': 'Washington Capitals',   'WPG': 'Winnipeg Jets',
    'ATL': 'Atlanta Thrashers',     'PHX': 'Phoenix Coyotes'
}

# Country abreviations with nationality names
NATIONALITIES = {
    'AUS': 'Australia',     'AUT': 'Austria',       'BLR': 'Belarus',       'CAN': 'Canada',
    'CZE': 'Czechia',       'DNK': 'Denmark',       'FIN': 'Finland',       'FRA': 'France',
    'DEU': 'Germany',       'HUN': 'Hungary',       'IRL': 'Ireland',       'ITA': 'Italy',
    'JAM': 'Jamaica',       'JPN': 'Japan',         'KAZ': 'Kazakhstan',    'KOR': 'South Korea',   
    'LVA': 'Latvia',        'LTU': 'Lithuania',     'NLD': 'Netherlands',   'NOR': 'Norway',
    'POL': 'Poland',        'RUS': 'Russia',        'SVK': 'Slovakia',      'SVN': 'Slovenia',
    'SWE': 'Sweden',        'CHE': 'Switzerland',   'UKR': 'Ukraine',       'GBR': 'United Kingdom',
    'USA': 'United States'
}

# Attribute names with full names
ATTRIBUTE_NAMES = {
    'evo_rank' : '5v5 Offense',
    'evd_rank' : '5v5 Defense',
    'ppl_rank' : '5v4 Offense',
    'pkl_rank' : '4v5 Defense',
    'oio_rank' : 'On Ice Offense',
    'oid_rank' : 'On Ice Defense',
    'scr_rank' : 'Scoring',
    'sht_rank' : 'Shooting',
    'plm_rank' : 'Playmaking',
    'zon_rank' : 'O-Zone Starts',
    'pen_rank' : 'Penalties',
    'phy_rank' : 'Physicality',
    'fof_rank' : 'Faceoffs',
    'fan_rank' : 'Fantasy',
    'all_rank' : 'Overall',
    'evs_rank' : 'Even Strength',
    'gpk_rank' : 'Penalty Kill',
    'ldg_rank' : 'Low Danger',
    'mdg_rank' : 'Med. Danger',
    'hdg_rank' : 'High Danger',
    'rbd_rank' : 'Rebounds',
    'tmd_rank' : 'Team Defense',
    'sho_rank' : 'Shutouts',
    'gre_rank' : 'Great Starts',
    'qal_rank' : 'Quality Starts',
    'bad_rank' : 'Bad Starts',
    'awf_rank' : 'Awful Starts',
}

# Symbols to be replaced in player names for the header
SYMBOLS_TO_REPLACE = {
    'ä': 'a',
    'á': 'a',
    'à': 'a',
    'â': 'a',
    'é': 'e',
    'è': 'e',
    'ê': 'e',
    'ë': 'e',
    'ï': 'i',
    'í': 'i',
    'ì': 'i',
    'î': 'i',
    'ö': 'o',
    'ó': 'o',
    'ò': 'o',
    'ô': 'o',
    'ø': 'o',
    'ü': 'u',
    'ñ': 'n',
    'ç': 'c',
    'ý': 'y',
}



# ====================================================================================================
# COLOR CONSTANTS
# ====================================================================================================

# Team primary colors
PRIMARY_COLORS = {
    'ANA': (252, 76, 2),    'ARI': (140, 38, 51),   'BOS': (252, 181, 20),
    'BUF': (0, 48, 135),    'CGY': (210, 0, 28),    'CAR': (206, 17, 38),
    'CHI': (207, 10, 44),   'COL': (111, 38, 61),   'CBJ': (0, 38, 84),
    'DAL': (0, 104, 71),    'DET': (206, 17, 38),   'EDM': (252, 76, 0),
    'FLA': (200, 16, 46),   'LAK': (162,170,173),   'MIN': (2, 73, 48),
    'MTL': (175, 30, 45),   'NSH': (255, 184, 28),  'NJD': (206, 17, 38),
    'NYI': (244, 125, 48),  'NYR': (0, 56, 168),    'OTT': (218, 26, 50),
    'PHI': (247, 73, 2),    'PIT': (252, 181, 20),  'SJS': (0, 109, 117),
    'SEA': (153, 217, 217), 'STL': (0, 47, 135),    'TBL': (0, 40, 104),
    'TOR': (0, 32, 91),     'VAN': (0, 32, 91),     'UTA': (105, 179, 231),
    'VGK': (185, 151, 91),  'WSH': (4, 30, 66),     'WPG': (4, 30, 66),
    'ATL': (4, 30, 66),     'PHX': (140, 38, 51)
}

# Team secondary colors
SECONDARY_COLORS = {
    'ANA': (185, 151, 91),  'ARI': (21,71,52),      'BOS': (17, 17, 17),
    'BUF': (255, 184, 28),  'CGY': (250, 175, 25),  'CAR': (0, 0, 0),
    'CHI': (0, 0, 0),       'COL': (35, 97, 146),   'CBJ': (206,17,38),
    'DAL': (143, 143, 140), 'DET': (0, 0, 0),       'EDM': (4, 30, 66),
    'FLA': (4,30,66),       'LAK': (17, 17, 17),    'MIN': (175, 35, 36),
    'MTL': (25, 33, 104),   'NSH': (4,30,66),       'NJD': (0, 0, 0),
    'NYI': (0,83,155),      'NYR': (206,17,38),     'OTT': (0, 0, 0),
    'PHI': (0, 0, 0),       'PIT': (0, 0, 0),       'SJS': (0, 0, 0),
    'SEA': (0, 22, 40),     'STL': (252, 181, 20),  'TBL': (0, 0, 0),
    'TOR': (0, 0, 0),       'VAN': (0, 132, 61),    'UTA': (0, 0, 0),
    'VGK': (51,63,72),      'WSH': (200, 16, 46),   'WPG': (172,22,44),
    'ATL': (184, 97, 37),   'PHX': (21,71,52)
}

# Attribute colors for rank components
ATTRIBUTE_COLORS = {
    '5v5 Offense':      (255, 70, 70),
    '5v5 Defense':      (70, 70, 255),
    '5v4 Offense':      (255, 150, 130),
    '4v5 Defense':      (130, 150, 255),
    'On Ice Offense':   (0, 0, 0),
    'On Ice Defense':   (0, 0, 0),
    'Scoring':          (0, 0, 0),
    'Shooting':         (0, 0, 0),
    'Playmaking':       (0, 0, 0),
    'O-Zone Starts':    (0, 0, 0),
    'Penalties':        (0, 0, 0),
    'Physicality':      (0, 0, 0),
    'Faceoffs':         (0, 0, 0),
    'Fantasy':          (0, 0, 0),
    'Overall':          (255, 70, 70),
    'Even Strength':    (255, 150, 150),
    'Penalty Kill':     (130, 150, 255),
    'Low Danger':       (0, 0, 0),
    'Med. Danger':      (0, 0, 0),
    'High Danger':      (0, 0, 0)
}

# Attribute colors for graph components
PLOT_ATTRIBUTE_COLORS = {
    'evo_plot': (255/255, 70/255, 70/255),
    'evd_plot': (70/255, 70/255, 255/255),
    'ppl_plot': (255/255, 150/255, 150/255),
    'pkl_plot': (150/255, 150/255, 255/255),
    'oio_plot': (0/255, 0/255, 0/255),
    'oid_plot': (0/255, 0/255, 0/255),
    'scr_plot': (0/255, 0/255, 0/255),
    'sht_plot': (0/255, 0/255, 0/255),
    'plm_plot': (0/255, 0/255, 0/255),
    'zon_plot': (0/255, 0/255, 0/255),
    'pen_plot': (0/255, 0/255, 0/255),
    'phy_plot': (0/255, 0/255, 0/255),
    'fof_plot': (0/255, 0/255, 0/255),
    'fan_plot': (0/255, 0/255, 0/255),
    'all_plot': (255/255, 70/255, 70/255),
    'evs_plot': (255/255, 150/255, 150/255),
    'gpk_plot': (150/255, 150/255, 255/255),
    'ldg_plot': (0/255, 0/255, 0/255),
    'mdg_plot': (0/255, 0/255, 0/255),
    'hdg_plot': (0/255, 0/255, 0/255)
}
