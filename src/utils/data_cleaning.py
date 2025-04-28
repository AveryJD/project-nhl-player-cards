# ====================================================================================================
# FUNCTIONS FOR CLEANING DATA CSV FILES
# ====================================================================================================

# Imports
import pandas as pd
from src.utils import constants


def clean_symbols(df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace any unusual characters in player names with typical characters.
    """

    for original, replacement in constants.SYMBOLS_TO_REPLACE.items():
        df = df.map(lambda x: x.replace(original, replacement) if isinstance(x, str) else x)

    return df


def clean_player_names(df: pd.DataFrame):
    """
    Standardize player names for consistency.
    """
    name_replacements = {
        'Christopher Tanev': 'Chris Tanev',
        'Mitchell Marner': 'Mitch Marner'
        # FIND MORE
    }
    df['Player'] = df['Player'].replace(name_replacements)

    return df


def clean_team_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize team abbreviations in the DataFrame.
    """
    team_replacements = {
        'L.A': 'LAK', 
        'S.J': 'SJS', 
        'N.J': 'NJD', 
        'T.B': 'TBL'
    }

    # Only replace specific abbreviations without breaking multi-team entries
    df['Team'] = df['Team'].apply(lambda x: ", ".join([team_replacements.get(team, team) for team in x.split(', ')]) if isinstance(x, str) else x)

    return df


def clean_positions(df: pd.DataFrame):
    """
    Standardize positions in the DataFrame.
    """
    if 'Position' in df.columns:
        df['Position'] = df['Position'].apply(lambda x: x.replace('L', 'LW').replace('R', 'RW'))

    return df


def clean_dataframe(df: pd.DataFrame):
    """
    Clean entire dataframe
    """
    
    # Drop unnecessary columns
    if '' in df.columns:
        df = df.drop(columns=[''])
    if '_x' in df.columns:
        df = df.drop(columns=['_x', '_y'])

    # Replace weird symbol in column headers
    df.columns = [col.strip().replace(" ", " ") for col in df.columns]
    
    df = clean_symbols(df)
    df = clean_player_names(df)
    df = clean_team_names(df)
    df = clean_positions(df)

    # Sort by player names alphabetically
    df = df.sort_values(by="Player")

    return df