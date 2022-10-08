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
import sqlite3
import numpy as np

con = sqlite3.connect('bfvstats.db')
cur = con.cursor()

def update_log(skip, cursor, connection):
    '''
    Adds the previous number of profiles skipped to the log table in the database
    Parameters: skip, number of profiles skipped in mostly completed iteration of scraping
                cursor, a cursor that allows for sending queries to a sql database
                connection, used to connect to a database and "commit" (i.e. make permanent) changes
    '''
    cursor.execute(f'INSERT INTO log (skip, time) VALUES ({skip}, CURRENT_TIMESTAMP);')
    connection.commit()
    
def retrieve_last_run(cursor):
    '''
    Retrieves the most recent number of profiles skipped from the database
    Parameter: cursor, a cursor that allows for sending queries to a sql database
    Returns: last_run, the number of profiles skipped on the last round of scraping
    '''
    # Sort runs in descending order and return the largest
    last_run = cursor.execute('SELECT skip FROM log ORDER BY skip DESC LIMIT 1;').fetchall()[0][0]
    return last_run

def read_categories(categories_to_scrape_file):
    '''
    Reads a list of categories to find in the JSON from a text file,
    separates them into general and class-related categories and returns
    each group as a list.
    Parameter: categories_to_scrape_file, filename of the file storing the categories
    Returns: history_categories, a list of general categories to collect from the JSON
             class_categories, a list of class-specific categories to collect from the JSON
    '''
    with open(categories_to_scrape_file, 'r') as f:
        categories = f.read().split('\n')
        history_categories = categories[0].split(' ')
        class_categories = categories[1].split(' ')
    return history_categories, class_categories

def parse_player(player_json):
    '''
    Retrives the players username and platform and returns their player_id and platform
    Parameters: player_json, the portion of a JSON string from the leaderboard API associated with a player.
    Returns: player_id, a combinattion of the player's platform and username, useful for inserting into URLs
             player_platform, the platform on which the player plays (i.e. xbl, psn, origin)
    '''
    player_username = player_json['id']
    player_platform = player_json['owner']['metadata']['platformSlug']
    player_id = f'{player_platform}/{player_username}'
    
    return player_id, player_platform

def parse_leaderboard(leaderboard_url, stat_dict):
    '''
    Retrives the player_id and player_platform for every play on a leaderboard page
    Parameters: leaderboard_url (url for the leaderboard API for a page)
                stat_dict, dictionary of profile info/platform info/stats for current batch from leaderboard API
    Returns: stat_dict with new player information inserted
    '''

    # Load the URL
    driver.get(leaderboard_url)
    leaderboard_content = driver.page_source.encode('utf-8').strip()
    soup = bs(leaderboard_content, features='lxml')
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

def parse_history_for_player(history_json, stat_dict, history_categories):
    '''
    Collects general (i.e. not class-specific) data for a single player
    Parameters: history_json, JSON containing general stats from profile API
                stat_dict, dictionary of profile info/platform info/stats for current batch from leaderboard API
                history_categories, a list of general categories to collect from the JSON
    Returns: stat_dict, with new general player stats entered
    '''
    available_stats = history_json.keys()
    for stat in history_categories:
        if stat in available_stats:
            stat_value = history_json[stat]['value']
            stat_percentile = history_json[stat]['percentile']
        else:
            stat_value = np.nan
            stat_percentile = np.nan
        
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

def parse_class_stats(class_json, stat_dict, class_categories):
    '''
    Retrieve class-specific stats for a specific player for a single class.
    Parameters: classes_json, JSON containing class-specific stats from the profile API
                stat_dict, dictionary of profile info/platform info/stats for current batch from leaderboard API
                class_categories, a list of class-specific categories to collect from the JSON
    Returns: stat_dict, with new player class information inserted
    '''
    class_name = class_json['metadata']['name']
    available_stats = list(class_json['stats'].keys())[1:]

    # Add class stats to stat_dict       
    for stat in class_categories: # The first entry is player rank, which we don't need
        # Check if the desired stat is present in the JSON
        if stat in available_stats:
            stat_percentile = class_json['stats'][stat]['percentile']
            stat_value = class_json['stats'][stat]['value']
        else:
            stat_percentile = np.nan
            stat_value = np.nan
        
        stat_name = f'{class_name}_{stat}' # ex Assault_kills
        
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

def parse_classes_for_player(classes_json, stat_dict, class_categories):
    '''
    Retrieve class-specific stats for a specific player for all classes.
    Parameters: classes_json, JSON containing class-specific stats from the profile API
                stat_dict, dictionary of profile info/platform info/stats for current batch from leaderboard API
                history_categories, a list of general categories to collect from the JSON
    Returns: stat_dict, with class information for all classes updated for a single player
    '''
    classes = ['medic', 'assault', 'support', 'recon', 'tanker', 'pilot']
    for class_json in classes_json:
        stat_dict = parse_class_stats(class_json, stat_dict, class_categories)
    
    # Check to see if class data was found for all classes for the player - some players do not have data for certain classes
    # First, identify class related features
    class_features = []
    for player_class in classes:
        for feature in stat_dict:
            if player_class in feature.lower():
                class_features.append(feature)
    
    # Check to see if all class related features are of same length, if not, fill short features with NaN      
    feature_lengths = [len(stat_dict[feature]) for feature in class_features]
    unique_feature_lengths = set(feature_lengths)
    if len(unique_feature_lengths) > 1:
        num_samples = max(unique_feature_lengths)
        for i, feature_length in enumerate(feature_lengths):
            if feature_length < num_samples:
                short_feature = class_features[i]
                stat_dict[short_feature].append(np.nan) # Since we do this for each player, should never need to add more than 1 NaN per player
                    
    return stat_dict


def parse_player_stats(stat_dict, history_categories, class_categories):
    '''
    Find general and class-specific information for every player in a batch retrieved from the leaderboard API
    Parameters: stat_dict, dictionary of profile info/platform info/stats for current batch from leaderboard API
                history_categories, a list of general categories to collect from the JSON
                class_categories, a list of class-specific categories to collect from the JSON
    Returns: stat_dict, with stats added for every player in current round of leaderboard scraping
    '''
    for player_id in tqdm(stat_dict['player_id']):
        
        # Get overall history for player
        api_url = f"https://api.tracker.gg/api/v2/bfv/standard/profile/{player_id}?"

        driver.get(api_url)
        history_content = driver.page_source.encode('utf-8').strip()
        soup = bs(history_content, features='lxml')
        history_json = json.loads(soup.body.pre.text)

        # Some data is simply unavailable for access
        if 'data' in history_json:
            history_json_data = history_json['data']['segments'][0]['stats']

            stat_dict = parse_history_for_player(history_json_data, stat_dict, history_categories)
               
        # Get class info for the user in question
        api_url = f"https://api.tracker.gg/api/v2/bfv/standard/profile/{player_id}/segments/class"

        driver.get(api_url)
        class_content = driver.page_source.encode('utf-8').strip()
        soup = bs(class_content, features='lxml')

        classes_json = json.loads(soup.body.pre.text)
        if 'data' in classes_json:
            classes_json_data = classes_json['data']
            
            stat_dict = parse_classes_for_player(classes_json_data, stat_dict, class_categories)

        # Drop player if no associated information
        if 'data' not in history_json and 'data' not in classes_json:
            stat_dict['player_id'] = stat_dict['player_id'][:-1]
            stat_dict['platform'] = stat_dict['platform'][:-1]
        
        time.sleep(2)
        
        
    return stat_dict        




def scrape_page(leaderboard_url, stat_dict, history_categories, class_categories):
    '''
    Scrapes player and platform information for a chunk of the leaderboard, then finds all of the
    player stats for each player found.
    Parameters: leaderboard_url, url to the leaderboard API
                stat_dict, dictionary of profile info/platform info/stats for current batch from leaderboard API
                history_categories, a list of general categories to collect from the JSON
                class_categories, a list of class-specific categories to collect from the JSON
    '''
    # Scrape the page
    stat_dict = parse_leaderboard(leaderboard_url, stat_dict)
    stat_dict = parse_player_stats(stat_dict, history_categories, class_categories)
    
    return stat_dict

def scrape_site(history_categories, class_categories, cur=cur, con=con):
    '''
    Collects data about all players.
    Parameters: history_categories, a list of general categories to collect from the JSON
                class_categories, a list of class-specific categories to collect from the JSON
    '''
    
    # determine how many profiles to skip
    skip = 0
    files = os.listdir('data')
    if len(files) > 0:
        skip = retrieve_last_run(cur) + 00
        print(f'Skipping first {skip} profiles.')

    while skip < 78800: # Max number of profiles, found manually
        leaderboard_url = f'https://api.tracker.gg/api/v1/bfv/standard/leaderboards?type=stats&platform=all&board=WINS&skip={skip}&take=100'
        
        # scrape page
        stat_dict = {}
        stat_dict = scrape_page(leaderboard_url, stat_dict, history_categories, class_categories)
        key_lens = [len(stat_dict[key]) for key in stat_dict]
        if len(list(set(key_lens))) > 1:
            for key in stat_dict:
                print(key, len(stat_dict[key]))


        # Load previous progess, if any
        current_iter = pd.DataFrame.from_dict(stat_dict)
        previous_file_name = f'bfvstats_skip{skip-100}.csv'
        
        # save the data
        if previous_file_name in files:
            previous_iter = pd.read_csv('data/'+previous_file_name, index_col=0)
            combined_df = pd.concat([previous_iter, current_iter]).reset_index(drop=True)
            combined_df = combined_df.drop_duplicates(subset=['player_id'])

            combined_df.to_csv(f'data/bfvstats_skip{skip}.csv')
            current_iter.to_sql('bfvstats', con=con, if_exists='append')
            update_log(skip, cur, con)     
            
        else:
            current_iter.to_csv(f'data/bfvstats_skip{skip}.csv')
            current_iter.to_sql('bfvstats', con=con, if_exists='append')

        skip += 100



options = Options()
options.add_argument("start-maximized")
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

history_categories, class_categories = read_categories('categories_to_scrape.txt')

scrape_site(history_categories, class_categories)

con.close()