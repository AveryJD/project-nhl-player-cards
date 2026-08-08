# ====================================================================================================
# GET PROJECT FILE LOCATION
# ====================================================================================================

import os

def find_project_dir(start_dir: str) -> str:
    """
    Traverse upward until a directory containing 'data' is found.

    :param start_dir: Directory where the search starts
    :return: Project root directory
    """

    while True:
        potential_data_dir = os.path.join(start_dir, "data")

        if os.path.exists(potential_data_dir):
            return start_dir

        parent = os.path.dirname(start_dir)

        if parent == start_dir:
            raise FileNotFoundError('Could not find "data" folder')

        start_dir = parent


# Directory of the current file
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Root project directory
PROJECT_DIR = find_project_dir(CURRENT_DIR)

# Data directory
DATA_DIR = os.path.join(PROJECT_DIR, "data")



# ====================================================================================================
# DATA CONSTANTS
# ====================================================================================================

# Date card data was updated on
UPDATE_DATE = 'July 1, 2026'

# Positions to scrape stats for
POSITIONS = ['F', 'D', 'G']

# Position to data folder name
POSITION_FOLDERS = {'F': 'forwards', 'D': 'defensemen', 'G': 'goalies'}

# Situations to scrape stats for
SKATER_SITUATIONS = ['all', '5v5', '5v4', '4v5']
GOALIE_SITUATIONS = ['all', '5v5', '4v5']

# Seasons for to scraping data, building models, and making cards for
DATA_SEASONS = ['2009-2010', '2010-2011', '2011-2012', '2012-2013', '2013-2014',
                '2014-2015', '2015-2016', '2016-2017', '2017-2018', '2018-2019',
                '2019-2020', '2020-2021', '2021-2022', '2022-2023', '2023-2024',
                '2024-2025', '2025-2026']



# ====================================================================================================
# MODEL CONSTANTS
# ====================================================================================================

# Number of games per season
SEASON_GAMES = {
    '2026-2027': 0,     # Current season (max games any team has played)
    '2025-2026': 82,    
    '2024-2025': 82,
    '2023-2024': 82,
    '2022-2023': 82,
    '2021-2022': 82,
    '2020-2021': 56,    # Season shortened due to COVID
    '2019-2020': 71,    # Season paused due to COVID
    '2018-2019': 82,
    '2017-2018': 82,
    '2016-2017': 82,
    '2015-2016': 82,
    '2014-2015': 82,
    '2013-2014': 82,
    '2012-2013': 48,    # Season shortened due to lockout
    '2011-2012': 82,
    '2010-2011': 82,
    '2009-2010': 82,
}

# The minimum TOI per total games in the season that a player has to play to qualify for rankings (300 min / 82 games)
SKATER_MIN_TOI = 3.6585

# The minimum percentage of total games in the season that a player has to play to qualify for rankings (13 games / 82 total games)
GOALIE_MIN_GP = 0.15

# The minimum percentage of special teams time per game played that a player has to play to qualify for special teams rankings
SKATER_MIN_PP = 0.75
SKATER_MIN_PK = 0.75

# Weighting values for per weighted season skater rankings (found with fit_season_weights.py)
SKATER_THREE_SEASONS_WEIGHTS = [0.54, 0.34, 0.12]
SKATER_TWO_SEASONS_WEIGHTS = [0.56, 0.44, 0.00]
SKATER_TWO_SEASONS_WEIGHTS_GAP = [0.80, 0.00, 0.20]
SKATER_ONE_SEASON_WEIGHTS = [1.00, 0.00, 0.00]

# Weighting values for per weighted season goalie rankings (too variable, hand picked)
GOALIE_THREE_SEASONS_WEIGHTS = [0.50, 0.30, 0.20]
GOALIE_TWO_SEASONS_WEIGHTS = [0.60, 0.40, 0.00]
GOALIE_TWO_SEASONS_WEIGHTS_GAP = [0.80, 0.00, 0.20]
GOALIE_ONE_SEASON_WEIGHTS = [1.00, 0.00, 0.00]

# Goals to wins pythagorean exponent (found with fit_pythagorean_exponent.py)
PYTHAGOREAN_EXPONENT = 2.109

# Replacement-level TOI percentile for WAR (hand picked)
REPLACEMENT_TOI_PERCENTILE = 0.25

# Team-relative TOI rank cutoff defining replacement level (hand picked)
TEAM_TOI_RANK_THRESHOLDS = {
    '5v5': {'F': 13, 'D': 7},
    '5v4': {'F': 9, 'D': 4},
    '4v5': {'F': 8, 'D': 6},
}

# Cross-season RAPM prior stabilization TOI, per situation (hand picked)
PRIOR_STABILIZATION_TOI = {
    '5v5': 200.0,
    '5v4': 50.0,
    '4v5': 50.0
}

# Penalty xG per minute, per pre-penalty strength bucket (found with fit_penalty_xg_per_minute.py)
PENALTY_XG_PER_MINUTE = {
    '5v5': 0.09624,
    '5v4': 0.09624,
    '4v5': 0.24575
}

# GSAx thresholds for Great/Quality/Bad/Awful classification
GREAT_START_GSAX = 1.5
QUALITY_START_GSAX = 0.0
AWFUL_START_GSAX = -1.5



# ====================================================================================================
# NAMING CONSTANTS
# ====================================================================================================

# Position full names
POSITION_NAMES = {
    'F': 'Forward', 'D': 'Defense', 'G': 'Goalie'
}

# Specific position full names
SPECIFIC_POSITION_NAMES = {
    'C': 'Center', 'L': 'Left Wing', 'R': 'Right Wing', 'D': 'Defense', 'G': 'Goalie'
}

# Handedness full names
HANDEDNESS_NAMES = {
    'L': 'Left', 'R': 'Right',
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
    'ATL': 'Atlanta Thrashers',     'PHX': 'Phoenix Coyotes',
}

# Country abreviations with nationality names
NATIONALITIES = {
    'AUS': 'Australia',     'AUT': 'Austria',       'BLR': 'Belarus',       'CAN': 'Canada',
    'CZE': 'Czechia',       'DNK': 'Denmark',       'FIN': 'Finland',       'FRA': 'France',
    'DEU': 'Germany',       'HUN': 'Hungary',       'IRL': 'Ireland',       'ITA': 'Italy',
    'JAM': 'Jamaica',       'JPN': 'Japan',         'KAZ': 'Kazakhstan',    'KOR': 'South Korea',   
    'LVA': 'Latvia',        'LTU': 'Lithuania',     'NLD': 'Netherlands',   'NOR': 'Norway',
    'POL': 'Poland',        'RUS': 'Russia',        'SVK': 'Slovakia',      'SVN': 'Slovenia',
    'SWE': 'Sweden',        'SUI': 'Switzerland',   'CHE': 'Switzerland',   'UKR': 'Ukraine',
    'GBR': 'United Kingdom', 'USA': 'United States'
}

# Attribute abbreviations with full names
ATTRIBUTE_NAMES = {
    'ovr' : 'Overall WAR',
    # Skaters
    'evo' : '5v5 Offense',
    'evd' : '5v5 Defense',
    'ppl' : 'Power Play',
    'pkl' : 'Penalty Kill',
    'fin' : 'Finishing',
    'gol' : 'Goals',
    'xgl' : 'xGoals',
    'ast' : 'Assists',
    'pen' : 'Penalties',
    'hit' : 'Physicality',
    'pdo' : 'PDO (Luck)',
    'ozs' : 'O-Zone Starts',
    'cmp' : 'Competition',
    'tmt' : 'Teammates',
    # Goalies (also uses 'pkl' and 'ovr)
    'evs' : 'Even Strength',
    'ldg' : 'Low Danger',
    'mdg' : 'Med. Danger',
    'hdg' : 'High Danger',
    'rbd' : 'Rebounds',
    'tmd' : 'Team Defense',
    'gre' : 'Great Starts',
    'qal' : 'Quality Starts',
    'bad' : 'Bad Starts',
    'awf' : 'Awful Starts',
    'wrk' : 'Workload',
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

# Card color RGB values
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (180, 180, 180)
DARK = (39, 39, 39)
GRAPH_WHITE = (255/255, 255/255, 255/255)
GRAPH_BLACK = (0/255, 0/255, 0/255)
GRAPH_GRAY = (180/255, 180/255, 180/255)
GRAPH_DARK = (39/255, 39/255, 39/255)

# Team primary color RBG values
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
    'ATL': (4, 30, 66),     'PHX': (140, 38, 51),
}

# Team secondary color RGB values
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
    'ATL': (184, 97, 37),   'PHX': (21,71,52),
}

# Rank components RBG values
ATTRIBUTE_COLORS = {
    'Overall WAR':      (210, 110, 210),
    '5v5 Offense':      (255, 70, 70),
    '5v5 Defense':      (70, 70, 255),
    'Even Strength':    (255, 70, 70),
    'Penalty Kill':     (70, 70, 255),
}

# Graph component RBG values
PLOT_ATTRIBUTE_COLORS = {
    'ovr_plot': (210/255, 110/255, 210/255),
    'evo_plot': (255/255, 70/255, 70/255),
    'evd_plot': (70/255, 70/255, 255/255),
    'evs_plot': (255/255, 70/255, 70/255),
    'pkl_plot': (70/255, 70/255, 255/255),
}
