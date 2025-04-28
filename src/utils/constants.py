# ====================================================================================================
# DATA CONSTANTS
# ====================================================================================================

# Seasons to scrape stats and profile data for
SEASONS = ['2020-2021', '2021-2022', '2022-2023', '2023-2024', '2024-2025'] 

SITUATIONS = ['all', 'ev', 'pp', 'pk']

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
# NAMING CONSTANTS
# ====================================================================================================

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
    'spd_rank' : 'Speed',
    'ova_rank' : 'Overall',
    'evs_rank' : 'Ev. Strength',
    'ldg_rank' : 'Low Danger',
    'mdg_rank' : 'Med. Danger',
    'hdg_rank' : 'High Danger',
}



# ====================================================================================================
# COLOR CONSTANTS
# ====================================================================================================

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

# SORT BETTER AND CHANGE COLORS
ATTRIBUTE_COLORS = {
    'Offense':      (255, 70, 70),
    'Defense':      (22, 115, 193),
    'Shooting':     (255, 200, 80),
    'Playmaking':   (180, 220, 120),
    'Physicality':  (143, 121, 193),
    'Penalties':    (221, 185, 218),
    'ES Offense':   (0, 0, 0),
    'Power Play':   (0, 0, 0),
    'ES Defense':   (0, 0, 0),
    'Penalty Kill': (0, 0, 0),
    'Faceoffs':     (0, 0, 0),
    'Speed':        (0, 0, 0),
    'Overall':      (255, 100, 0),
    'Ev. Strength': (0, 255, 255),
    'Low Danger':   (255, 0, 0),
    'Med. Danger':  (0, 255, 0),
    'High Danger':  (0, 0, 255)
}

PLOT_ATTRIBUTE_COLORS = {
    'off_plot': (255/255, 70/255, 70/255),
    'def_plot': (22/255, 115/255, 193/255),
    'sht_plot': (255/255, 200/255, 80/255),
    'plm_plot': (180/255, 220/255, 120/255),
    'phy_plot': (143/255, 121/255, 193/255),
    'pen_plot': (221/255, 185/255, 218/255),
    'eso_plot': (0/255, 0/255, 0/255),
    'ppl_plot': (0/255, 0/255, 0/255),
    'esd_plot': (0/255, 0/255, 0/255),
    'pkl_plot': (0/255, 0/255, 0/255),
    'fof_plot': (0/255, 0/255, 0/255),
    'spd_plot': (0/255, 0/255, 0/255),
    'ova_plot': (255/255, 100/255, 0/255),
    'evs_plot': (0/255, 255/255, 255/255),
    'ldg_plot': (255/255, 0/255, 0/255),
    'mdg_plot': (0/255, 255/255, 0/255),
    'hdg_plot': (0/255, 0/255, 255/255)
}




# ====================================================================================================
# PLAYER CONSTANTS
# ====================================================================================================

# Players with unique attributes
UNIQUE_PLAYERS = ['James van Riemsdyk', # ADD MORE
                          ]

# One forward per team
F_PLAYERS = ['Troy Terry', 'David Pastrnak', 'Tage Thompson', 'Nazem Kadri', 'Sebastian Aho',
            'Connor Bedard', 'Nathan MacKinnon', 'Sean Monahan', 'Jason Robertson', 'Dylan Larkin',
            'Connor McDavid', 'Aleksander Barkov', 'Anze Kopitar', 'Kirill Kaprizov', 'Cole Caufield',
            'Filip Forsberg', 'Jack Hughes', 'Mathew Barzal', 'Artemi Panarin', 'Brady Tkachuk',
            'Travis Konecny', 'Sidney Crosby', 'Macklin Celebrini', 'Jared McCann', 'Robert Thomas',
            'Nikita Kucherov', 'Auston Matthews', 'Clayton Keller', 'Elias Pettersson', 'Jack Eichel',
            'Alex Ovechkin', 'Kyle Connor'
]

# One defensemen per team
D_PLAYERS = ['Pavel Mintyukov', 'Charlie McAvoy', 'Rasmus Dahlin', 'MacKenzie Weegar', 'Jaccob Slavin',
            'Alec Martinez', 'Cale Makar', 'Zach Werenski', 'Miro Heiskanen', 'Moritz Seider',
            'Evan Bouchard', 'Gustav Forsling', 'Brandt Clarke', 'Brock Faber', 'Lane Hutson',
            'Roman Josi', 'Dougie Hamilton', 'Noah Dobson', 'Adam Fox', 'Jake Sanderson',
            'Travis Sanheim', 'Erik Karlsson', 'Marc-Edouard Vlasic', 'Vince Dunn', 'Colton Parayko',
            'Victor Hedman', 'Chris Tanev', 'Mikhail Sergachev', 'Quinn Hughes', 'Shea Theodore',
            'John Carlson', 'Josh Morrissey'
]

# One goalie per team
G_PLAYERS = ['John Gibson', 'Jeremey Swayman', 'Ukko-Pekka Luukkonen', 'Dustin Wolf', 'Frederik Andersen',
            'Arvid Soderblom', 'Mackenzie Blackwood', 'Elvis Merzļikins', 'Jake Oettinger', 'Cam Talbot',
            'Stuart Skinner', 'Sergei Bobrovsky', 'Darcy Kuemper', 'Filip Gustavsson', 'Sam Montembeault'
            'Juuse Saros', 'Jacob Markström', 'Ilya Sorokin', 'Ilya Shesterkin', 'Linus Ullmark',
            'Samuel Ersson', 'Tristan Jarry', 'Alexandar Georgiev', 'Joey Daccord', 'Jordan Binnington',
            'Andrei Vasilevskiy', 'Joseph Woll', 'Karel Vejmelka', 'Kevin Lankinen', 'Adin Hill',
            'Logan Thompson', 'Connor Hellebuyck'
]


