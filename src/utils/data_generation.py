# ====================================================================================================
# FUNCTIONS FOR SCRAPING NHL PROFILES AND STATS FROM NATURALSTATTRICK
# ====================================================================================================

# Imports
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
from utils import data_cleaning as dc
from utils import constants

DATA_DIR = constants.DATA_DIR


def get_page(url: str):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Failed to fetch data: {e}")
        return None
    

def random_delay():
    """"
    Random delay between requests to prevent server overload
    """
    delay = random.uniform(10, 20)
    print(f"Waiting {delay:.2f} seconds before next request")
    time.sleep(delay)



def get_skater_profiles(season: str,):

    # Scrape skater profiles
    url_season = season.replace("-", "")
    url = f'https://www.naturalstattrick.com/playerteams.php?fromseason={url_season}&thruseason={url_season}&stype=2&sit=all&score=all&stdoi=bio&rate=n&team=ALL&pos=S&loc=B&toi=0&gpfilt=none&fd=&td=&tgp=410&lines=single&draftteam=ALL'
    
    page_content = get_page(url)
    if page_content is None:
        return
    
    soup = BeautifulSoup(page_content, 'html.parser')
    columns = [item.text for item in soup.find_all('th')]
    data = [e.text for e in soup.find_all('td')]
    table = []
    start = 0

    while start + len(columns) <= len(data):
        player = data[start:start + len(columns)]
        table.append(player)
        start += len(columns)

    df = pd.DataFrame(table, columns=columns)

    # Cleanup
    df = dc.clean_dataframe(df)

    # Save skater profiles as a CSV in the proper location
    save_dir = os.path.join(DATA_DIR, 'data', 'player_data', 'skater_profiles')
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f'{season}_skater_profiles.csv')
    df.to_csv(save_path, index=False)
    print(f"{season} skater profiles saved")

    random_delay()
    

def get_skater_stats(season: str, situation: str):

    url_season = season.replace("-", "")

    # Scrape skater individual stats
    std_url = f'https://www.naturalstattrick.com/playerteams.php?fromseason={url_season}&thruseason={url_season}&stype=2&sit={situation}&score=all&stdoi=std&rate=n&team=ALL&pos=S&loc=B&toi=0&gpfilt=none&fd=&td=&tgp=410&lines=single&draftteam=ALL'
    std_page_content = get_page(std_url)

    std_soup = BeautifulSoup(std_page_content, 'html.parser')
    std_columns = [item.text for item in std_soup.find_all('th')]
    std_data = [e.text for e in std_soup.find_all('td')]
    
    std_table = []
    start = 0
    while start + len(std_columns) <= len(std_data):
        player = std_data[start:start + len(std_columns)]
        std_table.append(player)
        start += len(std_columns)

    df_std = pd.DataFrame(std_table, columns=std_columns)

    # Scrape skater on-ice stats
    oi_url = f'https://www.naturalstattrick.com/playerteams.php?fromseason={url_season}&thruseason={url_season}&stype=2&sit={situation}&score=all&stdoi=oi&rate=n&team=ALL&pos=S&loc=B&toi=0&gpfilt=none&fd=&td=&tgp=410&lines=single&draftteam=ALL'
    oi_page_content = get_page(oi_url)

    oi_soup = BeautifulSoup(oi_page_content, 'html.parser')
    oi_columns = [item.text for item in oi_soup.find_all('th')]
    oi_data = [e.text for e in oi_soup.find_all('td')]
    
    oi_table = []
    start = 0
    while start + len(oi_columns) <= len(oi_data):
        player = oi_data[start:start + len(oi_columns)]
        oi_table.append(player)
        start += len(oi_columns)

    df_oi = pd.DataFrame(oi_table, columns=oi_columns)

    # Merge both DataFrames on 'Name' column
    df = pd.merge(df_std, df_oi, on=['Player', 'Team', 'Position', 'GP', 'TOI'], how='inner')

    # Cleanup 
    df = dc.clean_dataframe(df)

    # Save player stats as a CSV in the proper location
    save_dir = os.path.join(DATA_DIR, 'data', 'player_data', 'skater_stats')
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f'{season}_skater_{situation}_stats.csv')
    df.to_csv(save_path, index=False)
    print(f"{season} skater {situation} stats saved")

    random_delay()


def get_goalie_profiles(season: str,):

    # Scrape goalie profiles
    url_season = season.replace("-", "")
    url = f'https://www.naturalstattrick.com/playerteams.php?fromseason={url_season}&thruseason={url_season}&stype=2&sit=all&score=all&stdoi=bio&rate=n&team=ALL&pos=G&loc=B&toi=0&gpfilt=none&fd=&td=&tgp=410&lines=single&draftteam=ALL'
    
    page_content = get_page(url)
    if page_content is None:
        return
    
    soup = BeautifulSoup(page_content, 'html.parser')
    columns = [item.text for item in soup.find_all('th')]
    data = [e.text for e in soup.find_all('td')]
    table = []
    start = 0

    while start + len(columns) <= len(data):
        player = data[start:start + len(columns)]
        table.append(player)
        start += len(columns)

    df = pd.DataFrame(table, columns=columns)

    # Cleanup
    df = dc.clean_dataframe(df)

    # Save goalie profiles as a CSV in the proper location
    save_dir = os.path.join(DATA_DIR, 'data', 'player_data', 'goalie_profiles')
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f'{season}_goalie_profiles.csv')
    df.to_csv(save_path, index=False)
    print(f"{season} goalie profiles saved")

    random_delay()



def get_goalie_stats(season: str, situation: str):

    # Scrape goalie stats
    url_season = season.replace("-", "")
    url = f'https://www.naturalstattrick.com/playerteams.php?fromseason={url_season}&thruseason={url_season}&stype=2&sit={situation}&score=all&stdoi=g&rate=n&team=ALL&pos=S&loc=B&toi=0&gpfilt=none&fd=&td=&tgp=410&lines=single&draftteam=ALL'
    page_content = get_page(url)

    soup = BeautifulSoup(page_content, 'html.parser')
    columns = [item.text for item in soup.find_all('th')]
    data = [e.text for e in soup.find_all('td')]
    
    table = []
    start = 0
    while start + len(columns) <= len(data):
        player = data[start:start + len(columns)]
        table.append(player)
        start += len(columns)

    df = pd.DataFrame(table, columns=columns)

    # Cleanup 
    df = dc.clean_dataframe(df)

    # Save goalie stats as a CSV in the proper location
    save_dir = os.path.join(DATA_DIR, 'data', 'player_data', 'goalie_stats')
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, f'{season}_goalie_{situation}_stats.csv')
    df.to_csv(save_path, index=False)
    print(f"{season} goalie {situation} stats saved")

    random_delay()

