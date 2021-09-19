import sys
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
import pandas as pd
import os
import logging
import datetime

# set up logging parameters
def set_logging(season):
    ts = datetime.datetime.today().strftime("%Y-%m-%d_%H%M%S")
    logging.basicConfig(
        level=logging.INFO,
        filename= f'logs/{season}_{ts}.log',
        filemode='w',
        format='%(levelname)s : %(asctime)s : %(message)s'
    )

# return all rows from stats.nba.com stable and not just first 50
def select_all(driver):
    select_options = driver.find_elements_by_xpath("//select")
    try:
        for s in select_options:
            select_test = Select(s)
            for option in select_test.options:
                if 'All' == option.text:
                    dropdown_menu = select_test
                    dropdown_menu.select_by_visible_text('All')
    except Excpetion as e:
        logger.error("Error selecting all...")
        logger.error(f"{err}")
        quit()

def main(season, from_scratch=True):
    # set logger
    set_logging(season)

    # make sure raw_data/season exists
    try:
        os.mkdir(f'raw_data/{season}')
        logging.info(f"Generated dir raw_data/{season}")
    except Exception as e:
        logging.info(f"Dir raw_data/{season} already exists")

    # get the url set for all the players
    driver = webdriver.Chrome('./chromedriver')
    driver.get(f'https://www.nba.com/stats/players/bio/?Season={season}&SeasonType=Regular%20Season')
    select_all(driver)

    # scrape the bio data with the url links
    soup = BeautifulSoup(driver.page_source, 'lxml')
    parsed_table = soup.find_all('table')
    data = []
    for row in parsed_table[0].find_all('tr'):
        row_data = []
        for td in row.find_all('td'):
            td_check = td.find('a')
            if td_check is not None:
                link = td.a['href']
                row_data.append(link)

            not_link = ' '.join(td.stripped_strings)
            not_link = not_link.strip()
            if not_link == '':
                not_link = None
            row_data.append(not_link)
        try:

            vals = {
                'player_url': row_data[0].split('/')[-2],
                'player' : row_data[1],
                'team' : row_data[3],
                'age' : int(row_data[5]),
                'height' : int(row_data[6].split('-')[0]) * 12 + int(row_data[6].split('-')[1]),
                'weight' : int(row_data[7])
            }

            data.append(vals)
        except Exception as e:
            pass

    df = pd.DataFrame(data)
    df.to_csv(f'raw_data/{season}/list.csv', index=False)
    logging.info(f"Bio = {df.shape}")
    driver.close()

    # scrape matchup data
    for index, row in df.iterrows():
        if from_scratch or f"{row['player_url']}.csv" not in os.listdir(f"raw_data/{season}"):
            try:
                os.remove(f"raw_data/{season}/{row['player_url']}.csv")
            except:
                pass

            for i in range(10):
                try:
                    driver = webdriver.Chrome('./chromedriver')
                    driver.get(f"https://www.nba.com/stats/player/{row['player_url']}/head-to-head/?Season={season}&SeasonType=Regular%20Season")
                    select_all(driver)
                    temp = pd.read_html(driver.page_source)[0]
                    driver.close()
                    temp['DEF_PLAYER'] = row['player']
                    temp.rename(columns={'MATCHUP': 'OFF_PLAYER'}, inplace=True)
                    temp['SEASON'] = season
                    temp.to_csv(f"raw_data/{season}/{row['player_url']}.csv", index=False)
                    logging.info(f"SUCCESS : {row['player']} = {temp.shape} = {row['player_url']}.csv")
                    break
                except Exception as e:
                    logging.error(f"{row['player']} = {e}")
                    logging.error("Trying again...")
                    driver.close()
                if i == 9:
                    logging.error(f"Unable to parse {row['player']}")
        else:
            logging.info(f"SUCCESS : {row['player']} - {row['player_url']}.csv already exists")

if __name__ == '__main__':
    main(sys.argv[1], bool(int(sys.argv[2])))
