# Matchup

Created by: Michael Altschuler

Last Updated: 09/18/2021

## Purpose

The purpose of this application is to gather all the data from https://www.nba.com/stats/player/{player_id}/head-to-head/ and store some composite metrics from those matchup data.

There are two scripts to work together.

scaper.py goes through every player from a season, and generates a file called {player_id}.csv in the directory ./raw_data/{season} that has all the matchup data from https://www.nba.com/stats/player/{player_id}/head-to-head/

aggregator.py goes through all the {player_id}.csv files in ./raw_data/{season} and generates three aggregate files (players.csv, matchups.csv, and stats.csv) in the directory ./final_data/{season}.

The fields for players.csv are currently:

* player
* slug
* season
* team
* age
* height_in
* weight_lb

The fields for matchups.csv are currently:

* offense_player
* defense_player
* SEASON
* SECS
* POSS
* 2PM
* 2PA
* 3PM
* 3PA
* FTM
* FTA
* AST
* TOV

The fields for stats.csv are currently:

* player
* season
* POSS
* adj_usg_rank (percentile score for average opposing adjusted usage rank where adjusted usage rank is ``` (2PA + 3PA + 0.44 * FTA + TOV) * POSS^-0.5 ```)
* freq_gte82 (frequency of possessions vs players 6'10 and taller)
* freq_lte78 (frequency of possessions vs players 6'4 to 6'6)
* freq_lte81 (frequency of possessions vs players 6'7 to 6'9)
* freq_lte75 (frequency of possessions vs players 6'3 and shorter)
* poss_lte78 (possessions versus players 6'4 to 6'6)
* poss_lte81 (possessions versus players 6'7 to 6'9)
* poss_lte75 (possessions versus players 6'3 and shorter)
* poss_gte82 (possessions versus players 6'10 and taller)
* poss
* versatility_score_rank (percentile for Shannon entropy for freq_gte82, freq_lte81, freq_lte78, freq_lte75)
* height (average opposing height)
* weight (average opposing weight)

## How to Run

If you want to rewrite over all files in raw_data directory

```
python scraper.py {season} 1
```

If you want to note rewrite over any files in raw_data directory and simply process unprocessed player_ids

```
python scraper.py {season} 0
```


For example:
```
python scraper.py 2017-18 1
```

To run aggregator script:

```
python aggregator.py {season}
```

## Potential Issues

This application uses chromedriver selenium to scrape the javascript table from stats.nba.com.  Make sure you have Chrome installed and make sure you have have the correct version of chromedriver that matches your version of chrome (https://chromedriver.chromium.org/downloads) and have it located in the same directory as scraper.py

It is possible that due to taking too long to load the webpage, not all of the rows will be read.  This application built in a protection to re-run it it didn't collect at least 50 rows. If you do not intend for this behavior, comment out that infinite loop at the bottom of scraper.py or hit CTL + C  after final.csv is saved the first time.
