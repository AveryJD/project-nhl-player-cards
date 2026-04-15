# ====================================================================================================
# FUNCTIONS FOR CLEANING DATA CSV FILES
# ====================================================================================================

# Imports
import pandas as pd
from player_card_project.utils import constants


def clean_player_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize player names for consistency.

    :param df: The DataFrame to be cleaned
    :return: The cleaned DataFrame
    """

    # Replace names with most commonly used names for consistency
    name_replacements = constants.FIX_NAMES
    df['Player'] = df['Player'].replace(name_replacements)

    return df

def clean_country_abreviations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize country abreviations for consistency.

    :param df: The DataFrame to be cleaned
    :return: The cleaned DataFrame
    """

    # Replace names with most commonly used names for consistency
    abreviation_replacements = {
        'Lat' : 'LVA',
        'Fin' : 'FIN',
    }
    df['Birth Country'] = df['Birth Country'].replace(abreviation_replacements)
    df['Nationality'] = df['Nationality'].replace(abreviation_replacements)

    return df


def clean_team_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize team abbreviations in the DataFrame.

    :param df: The DataFrame to be cleaned
    :return: The cleaned DataFrame
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

    :param df: The DataFrame to be cleaned
    :return: The cleaned DataFrame
    """

    # Make all forward positions (C, LW, RW) into 'F'
    if "Position" in df.columns:
        df.loc[~df['Position'].isin(['D', 'G']), 'Position'] = 'F'

    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean entire DataFrame with helper functions.

    :param df: The DataFrame to be cleaned
    :return: The cleaned DataFrame
    """
    
    # Drop empty or merge-related columns if present
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
    if 'Birth Country' in df.columns:
        df = clean_country_abreviations(df)

    # Sort by player names alphabetically
    df = df.sort_values(by="Player")

    return df