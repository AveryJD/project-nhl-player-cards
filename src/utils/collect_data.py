# ====================================================================================================
# FUNCTIONS FOR SCRAPING DATA FROM NATURALSTATTRICK
# ====================================================================================================

# Imports
import pandas as pd
from bs4 import BeautifulSoup
import requests
import time
import random
from utils import clean_data as clean
from utils import constants
from utils import load_save as file

DATA_DIR = constants.DATA_DIR


def make_nst_url(
    season: str,
    situation: str,
    stdoi: str,
    position: str,
    stype: int = 2,
    score: str = 'all',
    rate: str = 'n',
    team: str = 'ALL',
    loc: str = 'B',
    toi: int = 0,
    gpfilt: str = 'none',
    fd: str = '',
    td: str = '',
    tgp: int = 410,
    lines: str = 'single',
    draftteam: str = 'ALL'
) -> str:
    """
    Build a fully parameterized Natural Stat Trick URL for scraping.

    :param season: Season in 'YYYY-YYYY' format (e.g. '2020-2021')
    :param situation: Game situation (e.g. 'all', '5v5', 'pp', etc.)
    :param stdoi: Type of stats ('bio', 'std', 'oi', 'g')
    :param position: Player position ('S', 'F', 'D', 'G', etc.)
    :param stype: Season type (1 = preseason, 2 = regular, 3 = RTP, 4 = playoffs)
    :param score: Score situation (e.g., 'all', 'tied', 'u', 'd')
    :param rate: Stat rate type ('n' = counts, 'y' = rates, 'r' = relative)
    :param team: Team code ('ALL' or 3-letter team code)
    :param loc: Location ('B' = both, 'H' = home, 'A' = away)
    :param toi: Minimum TOI filter (int)
    :param gpfilt: Game range filter ('none', 'gpdate', 'gpteam')
    :param fd: From date (YYYY-MM-DD) if using gpdate
    :param td: To date (YYYY-MM-DD) if using gpdate
    :param tgp: Last X team games if using gpteam
    :param lines: Split lines ('single' or 'split')
    :param draftteam: Draft team ('ALL' or 3-letter team code)
    :return: Complete NST URL string
    """
    # Make the season string in the correct format for the URL
    url_season = season.replace("-", "")
    
    # Make the URL
    url = (f'https://www.naturalstattrick.com/playerteams.php?'
           f'fromseason={url_season}&thruseason={url_season}'
           f'&stype={stype}&sit={situation}&score={score}&stdoi={stdoi}&rate={rate}'
           f'&team={team}&pos={position}&loc={loc}&toi={toi}&gpfilt={gpfilt}'
           f'&fd={fd}&td={td}&tgp={tgp}&lines={lines}&draftteam={draftteam}')

    return url


def random_delay() -> None:
    """
    Introduce a random delay between web requests to reduce server load and avoid rate limiting.

    :return: None
    """
    # Make delay by a random time of 20-30 seconds
    delay = random.uniform(20, 30)
    print(f"Waiting {delay:.2f} seconds before next request")
    time.sleep(delay)


def get_page(url: str) -> str:
    """
    Fetch the HTML content of a given URL.

    :param url: The URL to fetch
    :return: The content of the fetched page, or None if the request fails
    """
    # Delay before fetching the page
    random_delay()

    # Fetch the page content
    response = requests.get(url)
    response.raise_for_status()

    return response.content


def merge_data(df_one: pd.DataFrame, df_two: pd.DataFrame, merge_keys: list) -> pd.DataFrame:
    """
    Merge two DataFrames on specified keys using an inner join.

    :param df_one: the first DataFrame
    :param df_two: the second DataFrame
    :param merge_keys: List of column names to merge on
    :return: Merged DataFrame
    """
    merged_df = pd.merge(df_one, df_two, on=merge_keys, how='inner')

    return merged_df


def scrape_data(url: str) -> pd.DataFrame:
    """
    Scrape table data from a given URL and return it as a DataFrame.

    :param url: The URL to scrape
    :return: DataFrame containing the scraped table data
    """
    # Fetch the page from the URL
    page_content = get_page(url)
    
    # Scrape page
    soup = BeautifulSoup(page_content, 'html.parser')
    columns = [item.text for item in soup.find_all('th')]
    data = [e.text for e in soup.find_all('td')]

    # Make DataFrame
    table = [data[i:i+len(columns)] for i in range(0, len(data), len(columns))]
    df = pd.DataFrame(table, columns=columns)
    
    return df


def scrape_and_save_bios(season: str, position: str) -> None:
    """
    Scrape player bios from NST and save using the standardized save function.

    :param season: Season in 'YYYY-YYYY' format (e.g. '2020-2021')
    :param position: Capitalized first letter of the position of player bios ('F', 'D', or 'G')
    :return: None
    """
    bios_url = make_nst_url(season=season, situation='all', stdoi='bio', position=position)
    bios_df = scrape_data(bios_url)
    bios_df = clean.clean_dataframe(bios_df)

    filename = f'{season}_{position}_bios.csv'
    file.save_csv(bios_df, main_folder='data_scraped', sub_folder='bios', filename=filename)


def scrape_and_save_stats(season: str, position: str, situation: str) -> None:
    """
    Scrape player stats from NST and save using the standardized save function.

    :param season: Season in 'YYYY-YYYY' format (e.g. '2020-2021')
    :param position: Capitalized first letter of the position of player stats ('F', 'D', or 'G')
    :return: None
    """

    if position != 'G':
        std_url = make_nst_url(season=season, situation=situation, stdoi='std', position=position)
        std_stats_df = scrape_data(std_url)

        oi_url = make_nst_url(season=season, situation=situation, stdoi='oi', position=position)
        oi_stats_df = scrape_data(oi_url)

        merge_keys = ['Player', 'Team', 'Position', 'GP', 'TOI']
        stats_df = merge_data(std_stats_df, oi_stats_df, merge_keys)
        stats_df = clean.clean_dataframe(stats_df)
    else:
        g_stats_url = make_nst_url(season=season, situation=situation, stdoi='g', position=position)
        g_stats_df = scrape_data(g_stats_url)
        stats_df = clean.clean_dataframe(g_stats_df)

    stats_filename = f'{season}_{position}_{situation}_stats.csv'
    file.save_csv(stats_df, 'data_scraped', 'stats', stats_filename)

