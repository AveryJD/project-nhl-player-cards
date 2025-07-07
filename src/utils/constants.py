# ====================================================================================================
# DATA CONSTANTS
# ====================================================================================================

# Project file location
DATA_DIR = '/Users/averyjdoiron/GitHub/NHL-Player-Stat-Cards'

# Seasons to scrape stats and profile data for
SEASONS = ['2018-2019', '2019-2020', '2020-2021', '2021-2022', '2022-2023', '2023-2024', '2024-2025'] 

# Situations to get data for
PLAYER_SITUATIONS = ['all', '5v5', '5v4', '4v5']
GOALIE_SITUATIONS = ['all', '5v5', '4v5']

# Symbols to be replaced in player names
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

# Total games played in the season
SEASON_GAMES = 82

# The minimum games a skater has to play to qualify for rankings (at least 15% of games/13 games over a full 82 game season)
MIN_GP_SKATER = SEASON_GAMES * 0.15
# The minimum games a goalie has to play to qualify for rankings (at least 6% of games/5 games over a full 82 game season)
MIN_GP_GOALIE = SEASON_GAMES * 0.06

# ====================================================================================================
# NAMING CONSTANTS
# ====================================================================================================

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
    'TOR': 'Toronto Maple Leafs',   'VAN': 'Vancouver Canucks',     'UTA': 'Utah Hockey Club',
    'VGK': 'Vegas Golden Knights',  'WSH': 'Washington Capitals',   'WPG': 'Winnipeg Jets'
}

# Country abreviations with full names
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

# Attribute csv names with full names
ATRIBUTE_NAMES = {
    'off_rank' : 'Offense',
    'def_rank' : 'Defense',
    'evo_rank' : 'ES Offense',
    'evd_rank' : 'ES Defense',
    'ppl_rank' : 'Power Play',
    'pkl_rank' : 'Penalty Kill',
    'sht_rank' : 'Shooting',
    'plm_rank' : 'Playmaking',
    'phy_rank' : 'Physicality',
    'pen_rank' : 'Penalties',
    'fof_rank' : 'Faceoffs',
    #'spd_rank' : 'Speed',                      # Might be used in the future
    'all_rank' : 'Overall',
    'evs_rank' : 'Ev. Strength',
    'ldg_rank' : 'Low Danger',
    'mdg_rank' : 'Med. Danger',
    'hdg_rank' : 'High Danger',
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
    'VGK': (185, 151, 91),  'WSH': (4, 30, 66),     'WPG': (4, 30, 66)
}

# Team secondary colors
SECONDARY_COLORS = {
    'ANA': (185, 151, 91),  'ARI': (226,214,181),   'BOS': (17, 17, 17),
    'BUF': (255, 184, 28),  'CGY': (250, 175, 25),  'CAR': (0, 0, 0),
    'CHI': (0, 0, 0),       'COL': (35, 97, 146),   'CBJ': (206,17,38),
    'DAL': (143, 143, 140), 'DET': (0, 0, 0),       'EDM': (4, 30, 66),
    'FLA': (4,30,66),       'LAK': (17, 17, 17),    'MIN': (175, 35, 36),
    'MTL': (25, 33, 104),   'NSH': (4,30,66),       'NJD': (0, 0, 0),
    'NYI': (0,83,155),      'NYR': (206,17,38),     'OTT': (0, 0, 0),
    'PHI': (0, 0, 0),       'PIT': (0, 0, 0),       'SJS': (0, 0, 0),
    'SEA': (0, 22, 40),     'STL': (252, 181, 20),  'TBL': (0, 0, 0),
    'TOR': (0, 0, 0),       'VAN': (0, 132, 61),     'UTA': (0, 0, 0),
    'VGK': (51,63,72),      'WSH': (200, 16, 46),   'WPG': (172,22,44)
}

# Attribute colors for rank components
ATTRIBUTE_COLORS = {
    'Offense':          (0, 0, 0),
    'Defense':          (0, 0, 0),
    'ES Offense':       (255, 70, 70),
    'ES Defense':       (70, 70, 255),
    'Power Play':       (255, 150, 130),
    'Penalty Kill':     (130, 150, 255),
    'Shooting':         (0, 0, 0),
    'Playmaking':       (0, 0, 0),
    'Physicality':      (0, 0, 0),
    'Penalties':        (0, 0, 0),
    'Faceoffs':         (0, 0, 0),
    #'Speed':           (0, 0, 0),                 # Might be used in the future
    'Overall':          (255, 70, 70),
    'Ev. Strength':     (255, 150, 150),
    'Low Danger':       (0, 0, 0),
    'Med. Danger':      (0, 0, 0),
    'High Danger':      (0, 0, 0),
}

# Atribute colors for graph components
PLOT_ATTRIBUTE_COLORS = {
    'off_plot': (0/255, 0/255, 0/255),
    'def_plot': (0/255, 0/255, 0/255),
    'evo_plot': (255/255, 70/255, 70/255),
    'evd_plot': (70/255, 70/255, 255/255),
    'ppl_plot': (255/255, 150/255, 150/255),
    'pkl_plot': (150/255, 150/255, 255/255),
    'sht_plot': (0/255, 0/255, 0/255),
    'plm_plot': (0/255, 0/255, 0/255),
    'phy_plot': (0/255, 0/255, 0/255),
    'pen_plot': (0/255, 0/255, 0/255),
    'fof_plot': (0/255, 0/255, 0/255),
    #'spd_plot': (0/255, 0/255, 0/255),         # Might be used in the future
    'all_plot': (255/255, 70/255, 70/255),
    'evs_plot': (255/255, 150/255, 150/255),
    'ldg_plot': (0/255, 0/255, 0/255),
    'mdg_plot': (0/255, 0/255, 0/255),
    'hdg_plot': (0/255, 0/255, 0/255)
}



# ====================================================================================================
# PLAYER CARD CREATION CONSTANTS
# ====================================================================================================

# Players with unique attributes
UNIQUE_PLAYERS = ['James van Riemsdyk', # ADD MORE
]

# One forward per team (2024-2025 end of season rosters)
F_PLAYERS = ['Troy Terry', 'David Pastrnak', 'Tage Thompson', 'Nazem Kadri', 'Sebastian Aho',
            'Connor Bedard', 'Nathan MacKinnon', 'Sean Monahan', 'Jason Robertson', 'Dylan Larkin',
            'Connor McDavid', 'Aleksander Barkov', 'Anze Kopitar', 'Kirill Kaprizov', 'Cole Caufield',
            'Filip Forsberg', 'Jack Hughes', 'Mathew Barzal', 'Artemi Panarin', 'Brady Tkachuk',
            'Travis Konecny', 'Sidney Crosby', 'Macklin Celebrini', 'Jared McCann', 'Robert Thomas',
            'Nikita Kucherov', 'Auston Matthews', 'Clayton Keller', 'Elias Pettersson', 'Jack Eichel',
            'Alex Ovechkin', 'Kyle Connor'
]

# One defensemen per team (2024-2025 end of season rosters)
D_PLAYERS = ['Pavel Mintyukov', 'Charlie McAvoy', 'Rasmus Dahlin', 'MacKenzie Weegar', 'Jaccob Slavin',
            'Alec Martinez', 'Cale Makar', 'Zach Werenski', 'Miro Heiskanen', 'Moritz Seider',
            'Evan Bouchard', 'Gustav Forsling', 'Brandt Clarke', 'Brock Faber', 'Lane Hutson',
            'Roman Josi', 'Dougie Hamilton', 'Noah Dobson', 'Adam Fox', 'Jake Sanderson',
            'Travis Sanheim', 'Erik Karlsson', 'Marc-Edouard Vlasic', 'Vince Dunn', 'Colton Parayko',
            'Victor Hedman', 'Chris Tanev', 'Mikhail Sergachev', 'Quinn Hughes', 'Shea Theodore',
            'John Carlson', 'Josh Morrissey'
]

# One goalie per team (2024-2025 end of season rosters)
G_PLAYERS = ['John Gibson', 'Jeremey Swayman', 'Ukko-Pekka Luukkonen', 'Dustin Wolf', 'Frederik Andersen',
            'Arvid Soderblom', 'Mackenzie Blackwood', 'Elvis Merzļikins', 'Jake Oettinger', 'Cam Talbot',
            'Stuart Skinner', 'Sergei Bobrovsky', 'Darcy Kuemper', 'Filip Gustavsson', 'Sam Montembeault'
            'Juuse Saros', 'Jacob Markström', 'Ilya Sorokin', 'Ilya Shesterkin', 'Linus Ullmark',
            'Samuel Ersson', 'Tristan Jarry', 'Alexandar Georgiev', 'Joey Daccord', 'Jordan Binnington',
            'Andrei Vasilevskiy', 'Joseph Woll', 'Karel Vejmelka', 'Kevin Lankinen', 'Adin Hill',
            'Logan Thompson', 'Connor Hellebuyck'
]

