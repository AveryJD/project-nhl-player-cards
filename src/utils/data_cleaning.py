# ====================================================================================================
# FUNCTIONS FOR CLEANING DATA CSV FILES
# ====================================================================================================

# Imports
import pandas as pd
from . import constants


def clean_symbols(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace any unusual symbols in the DataFrame with typical characters.

    :param df: the DataFrame to be cleaned
    :return: the cleaned DataFrame
    """

    # Replace symbols in the DataFrame
    for original, replacement in constants.SYMBOLS_TO_REPLACE.items():
        df = df.map(lambda x: x.replace(original, replacement) if isinstance(x, str) else x)

    return df


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
        'Christopher Tanev': 'Chris Tanev',
        'Matt Dumba': 'Mathew Dumba',
        'Mitchell Marner': 'Mitch Marner',
        # FIND MORE
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
        'T.B': 'TBL',
        'PHX': 'ARI',
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
    df = clean_symbols(df)
    df = clean_player_names(df)
    df = clean_team_names(df)
    df = clean_positions(df)

    # Sort by player names alphabetically
    df = df.sort_values(by="Player")

    return df