# ====================================================================================================
# FUNCTIONS FOR GETTING ALL DATA USED IN PLAYER CARDS
# ====================================================================================================

# Imports
import pandas as pd
from utils import load_save as file


def get_player_role(player_row: pd.Series) -> str:
    """
    Return a str for a player's time on ice allocation based on their time on ice and games played.

    :param player_row: a Series containing player data
    :return: a str of the toi allocation
    """
    # Player roles for goalies
    if player_row['Position'] == 'G':
        games_played = player_row['GP']
        if games_played >= 50:
            role = 'Starter'
        elif games_played > 41:
            role = '1A'
        elif games_played > 32:
            role = '1B'
        elif games_played > 8:
            role = 'Backup'
        else:
            role = 'Fringe'

    # Player roles for defensemen
    elif player_row['Position'] == 'D':
        avg_toi = player_row['TOI'] / player_row['GP']
        if avg_toi >= 22.0:
            role = 'First Pair'
        elif avg_toi > 18.0:
            role = 'Second Pair'
        elif avg_toi > 13.0:
            role = 'Third Pair'
        else:
            role = 'Fringe'

    # Player roles for forwards
    else:
        avg_toi = player_row['TOI'] / player_row['GP']
        if avg_toi >= 18.0:
            role = 'First Line'
        elif avg_toi > 15.5:
            role = 'Second Line'
        elif avg_toi > 8.5:
            role = 'Bottom 6'
        else:
            role = 'Fringe'

    return role


def make_card_data(season, position) -> None:
    """
    Generate a CSV file of all the relevent card data from other CSV files
    
    :param season: a str of the season to make the card data for (YYYY-YYYY')
    :param position: a str of the player's position's first letter to make the card data for ('F', 'D', or 'G')
    :return: None
    """
    # Load data
    bios_df = file.load_bios_csv(season, position)
    #salaries_df = file.load_salaries_csv(season, position)
    stats_df = file.load_stats_csv(season, position, 'all')
    rankings_df = file.load_rankings_csv(season, position)

    # Select important columns
    bios_cols = bios_df[['Player', 'Team', 'Position', 'Age', 'Date of Birth', 'Birth Country', 
                         'Nationality', 'Height (in)', 'Weight (lbs)', 
                         'Draft Year', 'Draft Round', 'Round Pick', 'Overall Draft Position']]  

    #salaries_cols = salaries_df[['Player', 'Team', 'Position', 'Contract Years', 'Cap Hit']]

    if position != 'G':
        stats_cols = stats_df[['Player', 'Team', 'Position', 'GP', 'TOI', 'Goals', 'First Assists']]

        rankings_cols = rankings_df[['Season', 'Player', 'Team', 'Position', 'evo_rank', 'evd_rank',
                                     'ppl_rank', 'pkl_rank', 'oio_rank', 'oid_rank', 'sht_rank', 'scr_rank',
                                     'zon_rank', 'plm_rank', 'pen_rank', 'phy_rank', 'fof_rank', 'fan_rank']]
        
    else:
        stats_cols = stats_df[['Player', 'Team', 'GP', 'SV%', 'GAA', 'xG Against', 'Goals Against']].copy()
        stats_cols.loc[:, 'Position'] = 'G'

        rankings_cols = rankings_df[['Season', 'Player', 'Team', 'Position', 'all_rank', 'evs_rank',
                                     'gpk_rank', 'ldg_rank', 'mdg_rank', 'hdg_rank']]


    # Merge data
    card_info_df = (
        rankings_cols
        .merge(stats_cols, on=['Player', 'Team', 'Position'], how='left')
        .merge(bios_cols, on=['Player', 'Team', 'Position'], how='left')
        #.merge(salaries_cols, on=['Player', 'Team', 'Position'], how='left')
    )

    # Add player role column
    card_info_df['Role'] = card_info_df.apply(get_player_role, axis=1)
    cols = list(card_info_df.columns)
    cols.remove("Role")
    stats_start = cols.index("GP")
    cols = cols[:stats_start] + ["Role"] + cols[stats_start:]
    card_info_df = card_info_df[cols]

    # Save CSV file
    if position == 'F':
        pos_folder = 'forwards'
    elif position == 'D':
        pos_folder = 'defensemen'
    elif position == 'G':
        pos_folder = 'goalies'
    else:
        raise ValueError(f"Unknown position {position}")

    filename = f'{season}_{position}_card_data.csv'
    file.save_csv(card_info_df, 'card_data', pos_folder, filename)

