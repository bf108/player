import requests
from bs4 import BeautifulSoup as bs
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import numpy as np
import pandas as pd
import re

# Cookies required to gain access to Badminton England
cookies = {'ASP.NET_SessionId': 'samot0pr3nnbuav0vs3l1oop',
           'st': 'l=2057&exp=44802.7753505324&c=1&cp=20',
           'expires': 'Mon, 29-Aug-2022 16:36:30 GMT',
           'path': '/'
           }

# Set up categories to iteraate through
categories_ = ['MS', 'WS', 'MD', 'WD', 'Men\'s XD', 'Woman\'s XD']
category_ids = [574, 575, 576, 577, 578, 579]

category_dict = {}
for cat, cat_id in zip(categories_, category_ids):
    category_dict[cat] = cat_id

# Id of Badminton England National Rankings for Jan 2019
last_entry_dec_2018 = '19633'
cat = category_dict['MS']
rows_per_page = '100'
pg = '1'

# Headings of the ranking tables are:
headings = ['Rank', 'Change', 'non_break_space', 'Player', 'Profile_url', 'Year of birth', 'Points', 'Total points',
            'County', 'Tournaments']


def create_url_ranking_table(rank_table_id, cat, pg, rows_per_page):
    '''
    helper function to generate url for ranking table

    args:
        rank_table_id - str - The id for the table to collect data from e.g "19633"
        cat - str - Category accronym e.g "WS" for Womans Single
        pg - str - page number e.g '2'
        rows_per_page - str - Number of results to display on one page. Min "1" and Max '100'

    returns:
        url - str - url for the requested table
    '''
    return f'https://be.tournamentsoftware.com/ranking/' \
           f'category.aspx?id={last_entry_dec_2018}&' \
           f'category={cat}&C574CS=0&C574FTYAF=0&C57' \
           f'4FTYAT=0&C574FOG_2_F512=&p={pg}&ps={rows_per_page}'


def generateSoup(url, cookies):
    '''
    Generate bs object from url and cookies

    args:
        url - str - url of ranking result tables
        cookies - dict - providing cookies to avoid data privacy pop up

    return:
        soup - bs object of page
    '''
    page = requests.get(url, cookies=cookies)
    return bs(page.content, 'html.parser')


def find_last_pg_pagination(soup):
    '''
    Results are paginated. Helper function to find last page of pagination.
    This will allow us to iterate through pages.

    Value returned is +1 of the max page to ensure we iterate through this page (inclusive)

    args:
        soup - BS object - soup of page 1 of national rankings

    return:
        last_page - int - page number of last page e.g 8 (max last page will actually be 7)
    '''
    last_page = re.search('1 of \d*', soup.find('div', class_='content') \
                          .find('div', class_='wrapper--legacy').find('table') \
                          .find_all('tr')[-1].text).group().split(' ')[-1]

    last_page = int(last_page) + 1
    return last_page


def checkTableHeadings(tbl_heading_row):
    '''
    Verify table is in known format

    args:
        tbl_heading_row - BS element - <tr></tr>

    returns:
        bool - True/False if aligned to expected headings
    '''

    expected_headings = ['Rank',
                         'Change',
                         'non_break_space',
                         'Player',
                         'Profile_url',
                         'Year of birth',
                         'Points',
                         'Total points',
                         'County',
                         'Tournaments']

    # Extract headings
    headings = [hd.text for hd in tbl_heading_row.find_all('th')]
    headings[1] = 'Change'
    headings[3] = 'Profile_url'

    headings = headings[:2] + ['non_break_space'] + headings[2:]

    return headings == expected_headings


def getTableRows(soup):
    '''
    Return all rows of table in Badminton England National Rankings Table (for one page)

    args:
        soup - BS object - soup of page of national rankings

    return:
        table_rows - list (bs.elements) - list of table row elements
    '''
    table_rows = soup.find('div', class_='content') \
        .find('div', class_='wrapper--legacy') \
        .find('table').find_all('tr')

    return table_rows


def extractRowData(soup, headings, result_dict):
    '''
    Extract data from each row of ranking table on page

    args:
        soup - BS object - soup of page of national rankings
        headings - list (str) - expected heading names for table schema
        results_dict - dict - Store results from table

    return:
        results_dic - dict - With new rows of data added
    '''
    table_rows = getTableRows(soup)

    # Check if table format as expected
    if checkTableHeadings(table_rows[1]):
        # Extract player details - avoid headings [0:1] and pagination details in last row [-1]
        for row in table_rows[2:-1]:
            for val, hd in zip(row.find_all('td'), headings):
                if hd != 'non_break_space':
                    if hd != 'Profile_url':
                        if val.text:
                            result_dict[hd].append(val.text)
                        else:
                            result_dict[hd].append(None)

                    else:
                        if val.find('a').get('href'):
                            url = 'https://be.tournamentsoftware.com' + val.find('a').get('href')
                            result_dict[hd].append(url)
                        else:
                            result_dict[hd].append(None)

    else:
        print('Table format not as expected!')

    return result_dict


def createEmptyResultsDict():
    # Create dictionary to store table content - This will be used to create DataFrame
    results_dict = {}
    for hd in headings:
        if hd != 'non_break_space':
            results_dict[hd] = []

    return results_dict


def appendResultsDF(df_results, cat_results):
    '''
    append results dict for a category to Results DataFrame

    args:
        df_results - DataFrame - DataFrame of all results
        cat_results - dict - Results from single category

    return:
        df_results - DataFrame - DataFrame of all result updated with cat_resulst
    '''
    # Convert dict to DF
    df_cat = pd.DataFrame.from_dict(cat_results)

    df_results = pd.concat([df_results, df_cat],
                           axis=0,
                           ignore_index=True)

    return df_results


def generateResultsDF(cookies, category_dict, rows_per_page):
    '''
    Top level function to generate results DataFrame

    args:
        cookies - dict - providing cookies to avoid data privacy pop up
        category_dict - dict - keys category accronyms, values category ids
        rows_per_page - str - number of results to display per page "100"

    return:
        df_results - DataFrame - ranking results
    '''

    # Generate empy result DF
    df_results = pd.DataFrame.from_dict(createEmptyResultsDict())
    # Iterate through all categories
    for cat, cat_id in category_dict.items():
        print(f"Working on {cat}")
        # Generate url
        url = create_url_ranking_table(last_entry_dec_2018, cat_id, '1', rows_per_page)
        # Create emtpy results dict
        results_dict = createEmptyResultsDict()
        # Convert page to soup
        soup = generateSoup(url, cookies)
        # Get last page of table
        last_page = find_last_pg_pagination(soup)
        # Iterate through pages
        for page in range(1, last_page):
            if page == 1 or page % 5 == 0 or page == (last_page - 1):
                print(f'Extracting results from page {page} of {last_page - 1}')
            url_ = create_url_ranking_table(last_entry_dec_2018, cat_id, str(page), rows_per_page)
            soup_ = generateSoup(url_, cookies)
            results_dict = extractRowData(soup_, headings, results_dict)

        # Create category column
        results_dict['Category'] = cat

        df_results = appendResultsDF(df_results, results_dict)

    return df_results


def getTSID(url, cookies):
    try:
        soup = generateSoup(url, cookies)
        tsid = soup.find('div', class_='page-head page-head--pattern wrapper wrapper--branding') \
                   .find('span',class_='media__title-aside').text[1:-1]
    except:
        tsid = 'N/A'
    return tsid


def getRegion(url, cookies):
    try:
        soup = generateSoup(url, cookies)
        region = soup.find('div', class_='page-head page-head--pattern wrapper wrapper--branding') \
            .find('div', class_='media__content-subinfo') \
            .find('small', class_='media__subheading') \
            .find('span', class_='nav-link__value').text
    except:
        region = 'N/A'
    return region

def main():
    print('Generating Basic Results Table...')
    df_rank_results = generateResultsDF(cookies, category_dict, rows_per_page)
    print('Collecting TSIDs')
    df_rank_results['tsid'] = df_rank_results['Profile_url'].apply(lambda x: getTSID(x, cookies))
    print('Collecting Region')
    df_rank_results['region'] = df_rank_results['Profile_url'].apply(lambda x: getRegion(x, cookies))
    print('Save Results')
    df_rank_results.to_csv('player_rankings_2019.csv',index=False)

if __name__=='__main__':
    main()