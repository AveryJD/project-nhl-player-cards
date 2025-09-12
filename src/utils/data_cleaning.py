# ====================================================================================================
# FUNCTIONS FOR CLEANING DATA CSV FILES
# ====================================================================================================

# Imports
import pandas as pd


def clean_player_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize player names for consistency.

    :param df: the DataFrame to be cleaned
    :return: the cleaned DataFrame
    """

    # Replace names with most commonly used names for consistency
    name_replacements = {
        'Alex Wennberg' : 'Alexander Wennberg',
        'Alexei Toropchenko' : 'Alexey Toropchenko',
        'Cameron Atkinson': 'Cam Atkinson',
        'Casey Desmith': 'Casey DeSmith',
        'Christopher Tanev': 'Chris Tanev',
        'Jani Hakanpaa': 'Jani Hakanpää',
        'Janis Moser': 'J.J. Moser',
        'Josh Brown': 'Joshua Brown',
        'Joshua Mahura': 'Josh Mahura',
        'Mat?j  Blümel': 'Matěj Blümel',
        'Matt Dumba': 'Mathew Dumba',
        'Mitchell Marner': 'Mitch Marner',
        'Nicholas Paul': 'Nick Paul',
        'Olli Maatta': 'Olli Määttä',
        'Oskar Back': 'Oskar Bäck',
        'Pat Maroon': 'Patrick Maroon',
    }
    df['Player'] = df['Player'].replace(name_replacements)

    return df


def clean_team_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize team abbreviations in the DataFrame.

    :param df: the DataFrame to be cleaned
    :return: the cleaned DataFrame
    """

    # Replace team abbreviations with most commonly used abbreviations for consistency
    team_replacements = {
        'L.A': 'LAK', 
        'S.J': 'SJS', 
        'N.J': 'NJD', 
        'T.B': 'TBL'
    }
    # Only replace specific abbreviations without breaking multi-team entries
    df['Team'] = df['Team'].apply(lambda x: ", ".join([team_replacements.get(team, team) for team in x.split(', ')]) if isinstance(x, str) else x)

    return df

def clean_positions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize positions in the DataFrame.

    :param df: the DataFrame to be cleaned
    :return: the cleaned DataFrame
    """

    # Make all forward positions (C, LW, RW) into 'F'
    if "Position" in df.columns:
        df.loc[~df['Position'].isin(['D', 'G']), 'Position'] = 'F'
    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean entire DataFrame with helper functions.

    :param df: the DataFrame to be cleaned
    :return: the cleaned DataFrame
    """
    
    # Drop unnecessary columns
    if '' in df.columns:
        df = df.drop(columns=[''])
    if '_x' in df.columns:
        df = df.drop(columns=['_x', '_y'])

    # Replace weird symbol in column headers
    df.columns = [col.strip().replace(" ", " ") for col in df.columns]
    
    # Use helper cleaning functions
    df = clean_player_names(df)
    df = clean_team_names(df)
    df = clean_positions(df)

    # Sort by player names alphabetically
    df = df.sort_values(by="Player")

    return df