import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup as bs
import pandas as pd
import numpy as np
from tqdm import tqdm
import json
import os


def parse_player(player_json):
    '''
    Retrives the players username and platform and returns their player_id and platform
    Parameters: player_json, the portion of a JSON string from the leaderboard API associated with a player.
    Returns: player_id, player_platform
    '''
    player_username = player_json['id']
    player_platform = player_json['owner']['metadata']['platformSlug']
    player_id = f'{player_platform}/{player_username}'

    return player_id, player_platform


def parse_leaderboard(leaderboard_url, stat_dict):
    '''
    Retrives the player_id and player_platform for every play on a leaderboard page
    Parameters: leaderboard_url (url for the leaderboard API for a page), stat_dict (dictionary of player performance metrics and other player information)
    '''

    # Load the URL
    driver.get(leaderboard_url)
    leaderboard_content = driver.page_source.encode('utf-8').strip()
    soup = bs(leaderboard_content)
    leaderboard_json = json.loads(soup.body.pre.text)

    if 'data' in leaderboard_json:
        leaderboard_data_json = leaderboard_json['data']['items']
        # Get names from leaderboard
        for player_json in leaderboard_data_json:
            player_id, player_platform = parse_player(player_json)
            # Add the player_id to the dictionary
            if 'player_id' in stat_dict:
                stat_dict['player_id'].append(player_id)
            else:
                stat_dict['player_id'] = [player_id]

            # Add the player platform to the dictionary
            if 'platform' in stat_dict:
                stat_dict['platform'].append(player_platform)
            else:
                stat_dict['platform'] = [player_platform]

    else:
        if 'player_id' not in stat_dict:
            stat_dict['player_id'] = []
            stat_dict['platform'] = []

    return stat_dict


def parse_history_for_player(history_json, stat_dict):

    for stat in history_json:
        stat_value = history_json[stat]['value']
        stat_percentile = history_json[stat]['percentile']

        # Add value to stat_dict
        if stat+'_value' in stat_dict:
            stat_dict[stat+'_value'].append(stat_value)
        else:
            stat_dict[stat+'_value'] = [stat_value]

        # Add percentile to stat_dict
        if stat+'_percentile' in stat_dict:
            stat_dict[stat+'_percentile'].append(stat_percentile)
        else:
            stat_dict[stat+'_percentile'] = [stat_percentile]

    return stat_dict


def parse_class_stats(class_json, stat_dict):
    '''
    Retrieve class-specific stats for a specific player for a single class.
    '''
    class_name = class_json['metadata']['name']

    # Add class name to stat_dict
    # The first entry is player rank, which we don't need
    for stat in list(class_json['stats'].keys())[1:]:
        stat_percentile = class_json['stats'][stat]['percentile']
        stat_value = class_json['stats'][stat]['value']

        stat_name = f'{class_name}_{stat}'  # ex Assault_kills

        # Add stat value to dictionary
        if stat_name+'_value' in stat_dict:
            stat_dict[stat_name+'_value'].append(stat_value)
        else:
            stat_dict[stat_name+'_value'] = [stat_value]

        # Add stat percentile to dictionary
        if stat_name+'_percentile' in stat_dict:
            stat_dict[stat_name+'_percentile'].append(stat_percentile)
        else:
            stat_dict[stat_name+'_percentile'] = [stat_percentile]

    return stat_dict


def parse_classes_for_player(classes_json, stat_dict):
    '''
    Retrieve class-specific stats for a specific player for all classes.
    '''
    for class_json in classes_json:
        stat_dict = parse_class_stats(class_json, stat_dict)

    return stat_dict


def parse_player_stats(stat_dict):
    for player_id in tqdm(stat_dict['player_id']):

        # Get overall history for player
        api_url = f"https://api.tracker.gg/api/v2/bfv/standard/profile/{player_id}?"

        driver.get(api_url)
        history_content = driver.page_source.encode('utf-8').strip()
        soup = bs(history_content)
        history_json = json.loads(soup.body.pre.text)

        # Some data is simply unavailable for access
        if 'data' in history_json:
            history_json_data = history_json['data']['segments'][0]['stats']

            stat_dict = parse_history_for_player(history_json_data, stat_dict)

        # Get class info for the user in question
        api_url = f"https://api.tracker.gg/api/v2/bfv/standard/profile/{player_id}/segments/class"

        driver.get(api_url)
        class_content = driver.page_source.encode('utf-8').strip()
        soup = bs(class_content)

        classes_json = json.loads(soup.body.pre.text)
        if 'data' in classes_json:
            classes_json_data = classes_json['data']

            stat_dict = parse_classes_for_player(classes_json_data, stat_dict)

        # Drop player if no associated information
        if 'data' not in history_json and 'data' not in classes_json:
            stat_dict['player_id'] = stat_dict['player_id'][:-1]
            stat_dict['platform'] = stat_dict['platform'][:-1]

        time.sleep(3)


def scrape_page(leaderboard_url, stat_dict):
    # Scrape the page
    stat_dict = parse_leaderboard(leaderboard_url, stat_dict)
    stat_dict = parse_player_stats(stat_dict)

    return stat_dict


def scrape_site(skip_init=0):

    skip = skip_init
    while skip < 78800:
        leaderboard_url = f'https://api.tracker.gg/api/v1/bfv/standard/leaderboards?type=stats&platform=all&board=WINS&skip={skip}&take=100'

        # scrape page
        stat_dict = {}
        stat_dict = scrape_page(leaderboard_url, stat_dict)
        key_lens = [len(stat_dict[key]) for key in stat_dict]
        if len(list(set(key_lens))) > 1:
            for key in stat_dict:
                print(key, len(stat_dict[key]))

        # Load previous progess, if any
        current_iter = pd.DataFrame.from_dict(stat_dict)
        files = os.listdir()
        previous_file_name = f'bfvstats_skip{skip-100}.csv'

        if previous_file_name in files:
            previous_iter = pd.read_csv(previous_file_name, index_col=0)
            combined_df = pd.concat(
                [previous_iter, current_iter]).reset_index(drop=True)

            os.remove(previous_file_name)
            combined_df.to_csv(f'bfvstats_skip{skip}.csv')

        else:
            current_iter.to_csv(f'bfvstats_skip{skip}.csv')
        skip += 100


options = Options()
options.add_argument("start-maximized")
driver = webdriver.Chrome(service=ChromeService(
    ChromeDriverManager().install()), options=options)

scrape_site()
