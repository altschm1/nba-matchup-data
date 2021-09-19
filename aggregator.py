import pandas as pd
import numpy as np
import logging
import sys
import os

# set up logging files
def set_logging(season):
    ts = datetime.datetime.today().strftime("%Y-%m-%d_%H%M%S")
    logging.basicConfig(
        level=logging.INFO,
        filename= f'logs/{season}_{ts}.log',
        filemode='w',
        format='%(levelname)s : %(asctime)s : %(message)s'
    )

# convert MM:SS to seconds
def time_convert(x):
    mins = int(x.split(':')[0])
    secs = int(x.split(':')[1])
    return 60 * mins + secs

def main(season):
    # create final_data dir if it doesn't exist
    try:
        os.mkdir(f'final_data/{season}')
    except Exception as e:
        print(e)

    # produce players.csv
    players = pd.read_csv(f'raw_data/{season}/list.csv')
    players['season'] = season
    players = players[['player', 'player_url', 'season', 'team', 'age', 'height', 'weight']]
    players.rename(columns={'player_url': 'slug', 'height': 'height_in', 'weight': 'weight_lb'}, inplace=True)
    players.to_csv(f'final_data/{season}/players.csv', index=False)

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
    matchups.to_csv(f'final_data/{season}/matchups.csv', index=False)

    # produce stats.csv
    defense_stats = players[['player', 'season']]

    offense_stats = pd.merge(defense_stats, matchups.groupby('offense_player', as_index=False).sum(), left_on='player', right_on='offense_player')
    #offense_stats['usg'] = (offense_stats['2PA'] + offense_stats['3PA'] + offense_stats['TOV'] + 0.44 * offense_stats['FTA']) / offense_stats['POSS']
    offense_stats['adj_usg'] = (offense_stats['2PA'] + offense_stats['3PA'] + offense_stats['TOV'] + 0.44 * offense_stats['FTA']) * (offense_stats['POSS']**-0.5)
    offense_stats = pd.merge(offense_stats, players[['player', 'height_in', 'weight_lb']], left_on='player', right_on='player')
    offense_stats = offense_stats.drop(columns=['offense_player'])

    # get possessions
    defense_stats = pd.merge(defense_stats, matchups.groupby('defense_player', as_index=False).agg({'POSS':'sum'}), left_on='player', right_on='defense_player')
    defense_stats = defense_stats.drop(columns=['defense_player'])

    matchups_augmented = pd.merge(matchups, offense_stats[['player', 'adj_usg', 'height_in', 'weight_lb']], left_on='offense_player', right_on='player')
    matchups_augmented = matchups_augmented[matchups_augmented['POSS'] > 0.0]

    # get usage score
    wm = lambda x: np.average(x, weights=matchups_augmented.loc[x.index, "POSS"])
    weighted_usg_stats = matchups_augmented.groupby('defense_player', as_index=False).agg(adj_usg=('adj_usg', wm), poss=('POSS', sum))
    weighted_usg_stats.loc[weighted_usg_stats['poss'] < 100.0, 'adj_usg'] = np.nan
    weighted_usg_stats['adj_usg_rank'] = weighted_usg_stats['adj_usg'].rank(pct=True)
    defense_stats = pd.merge(defense_stats, weighted_usg_stats[['defense_player', 'adj_usg_rank']], left_on='player', right_on='defense_player')
    defense_stats = defense_stats.drop(columns=['defense_player'])

    # get height versatility score
    versatility = pd.DataFrame()
    versatility = matchups_augmented.groupby('defense_player', as_index=False).apply(lambda x: pd.Series({'freq_gte82': x[x['height_in'] >= 82]['POSS'].sum() / x['POSS'].sum()}))
    versatility = pd.merge(versatility, matchups_augmented.groupby('defense_player', as_index=False).apply(lambda x: pd.Series({'freq_lte78': x[(x['height_in'] > 75) & (x['height_in'] <= 78)]['POSS'].sum() / x['POSS'].sum()})))
    versatility = pd.merge(versatility, matchups_augmented.groupby('defense_player', as_index=False).apply(lambda x: pd.Series({'freq_lte81': x[(x['height_in'] > 78) & (x['height_in'] <= 81)]['POSS'].sum() / x['POSS'].sum()})))
    versatility = pd.merge(versatility, matchups_augmented.groupby('defense_player', as_index=False).apply(lambda x: pd.Series({'freq_lte75': x[x['height_in'] <= 75]['POSS'].sum() / x['POSS'].sum()})))
    versatility = pd.merge(versatility, matchups_augmented.groupby('defense_player', as_index=False).apply(lambda x: pd.Series({'poss_lte78': x[(x['height_in'] > 75) & (x['height_in'] <= 78)]['POSS'].sum()})))
    versatility = pd.merge(versatility, matchups_augmented.groupby('defense_player', as_index=False).apply(lambda x: pd.Series({'poss_lte81': x[(x['height_in'] > 78) & (x['height_in'] <= 81)]['POSS'].sum()})))
    versatility = pd.merge(versatility, matchups_augmented.groupby('defense_player', as_index=False).apply(lambda x: pd.Series({'poss_lte75': x[x['height_in'] <= 75]['POSS'].sum()})))
    versatility = pd.merge(versatility, matchups_augmented.groupby('defense_player', as_index=False).apply(lambda x: pd.Series({'poss_gte82': x[x['height_in'] >= 82]['POSS'].sum()})))
    versatility = pd.merge(versatility, matchups_augmented.groupby('defense_player', as_index=False).apply(lambda x: pd.Series({'poss': x['POSS'].sum()})))
    versatility['score'] = -(versatility['freq_lte75']*np.log(versatility['freq_lte75'] + 0.0001) + versatility['freq_lte78']*np.log(versatility['freq_lte78'] + 0.0001) + versatility['freq_lte81']*np.log(versatility['freq_lte81'] + 0.0001) + versatility['freq_gte82']*np.log(versatility['freq_gte82'] + 0.0001))
    versatility.loc[versatility['poss'] < 100.0, 'score'] = np.nan
    versatility['versatility_score_rank'] = versatility['score'].rank(pct=True)
    defense_stats = pd.merge(defense_stats, versatility, left_on='player', right_on='defense_player')
    defense_stats = defense_stats.drop(columns=['defense_player', 'score'])

    # get average height
    wm = lambda x: np.average(x, weights=matchups_augmented.loc[x.index, "POSS"])
    weighted_height_stats = matchups_augmented.groupby('defense_player', as_index=False).agg(height=('height_in', wm))
    defense_stats = pd.merge(defense_stats, weighted_height_stats[['defense_player', 'height']], left_on='player', right_on='defense_player')
    defense_stats = defense_stats.drop(columns=['defense_player'])

    # get average weight
    wm = lambda x: np.average(x, weights=matchups_augmented.loc[x.index, "POSS"])
    weighted_weight_stats = matchups_augmented.groupby('defense_player', as_index=False).agg(weight=('weight_lb', wm))
    defense_stats = pd.merge(defense_stats, weighted_weight_stats[['defense_player', 'weight']], left_on='player', right_on='defense_player')
    defense_stats = defense_stats.drop(columns=['defense_player'])

    defense_stats.to_csv(f'final_data/{season}/stats.csv', index=False)

if __name__ == '__main__':
    main(sys.argv[1])
