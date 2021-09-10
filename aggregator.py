import pandas as pd
import numpy as np
import logging
import sys
import os

def set_logging(season):
    ts = datetime.datetime.today().strftime("%Y-%m-%d_%H%M%S")
    logging.basicConfig(
        level=logging.INFO,
        filename= f'logs/{season}_{ts}.log',
        filemode='w',
        format='%(levelname)s : %(asctime)s : %(message)s'
    )

def time_convert(x):
    mins = int(x.split(':')[0])
    secs = int(x.split(':')[1])
    return 60 * mins + secs

def main(season):
    # produce players.csv
    players = pd.read_csv(f'raw_data/{season}/list.csv')
    players['season'] = season
    players = players[['player', 'player_url', 'season', 'team', 'age', 'height', 'weight']]
    players.rename(columns={'player_url': 'slug', 'height': 'height_in', 'weight': 'weight_lb'}, inplace=True)
    print(players)
    print(len(players['player'].unique()), players['player'].count())

    # produce matchups.csv
    matchup_files = os.listdir(f'raw_data/{season}')
    matchup_files.remove('list.csv')
    matchups = pd.DataFrame()
    for m in matchup_files:
        temp = pd.read_csv(f'raw_data/{season}/{m}')
        temp['SECS'] = temp['MATCHUP MIN'].apply(time_convert)
        temp['2PM'] = temp['FGM'] - temp['3PM']
        temp['2PA'] = temp['FGA'] - temp['3PA']
        temp.rename(columns={'OFF_PLAYER': 'offense_player', 'DEF_PLAYER': 'defense_player', 'PARTIAL  POSS': 'POSS'}, inplace=True)
        temp = temp[['offense_player', 'defense_player', 'SEASON', 'SECS', 'POSS', '2PM', '2PA', '3PM', '3PA', 'FTM', 'FTA', 'AST', 'TOV']]
        matchups = matchups.append(temp, ignore_index=True)
    print(matchups)

    # produce stats.csv


    stats = players[['player', 'season']]
    offense_stats = pd.merge(stats, matchups.groupby('offense_player', as_index=False).sum(), left_on='player', right_on='offense_player')
    offense_stats['usg'] = (offense_stats['2PA'] + offense_stats['3PA'] + offense_stats['TOV'] + 0.44 * offense_stats['FTA']) / offense_stats['POSS']
    stats = pd.merge(stats, matchups.groupby('defense_player', as_index=False).agg({'POSS':'sum'}), left_on='player', right_on='defense_player')
    #stats = pd.merge(stats, )
    print(stats)
    print(offense_stats)

if __name__ == '__main__':
    main(sys.argv[1])
