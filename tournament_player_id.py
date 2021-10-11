import requests
from bs4 import BeautifulSoup as bs
import numpy as np
import pandas as pd


class TourPlayerId:
    """
    class used to get player TSID from href on player name within match in tournament

    TODO - CONSIDER INCORPORATING LOGGING TO RECORD WHICH URLS FAILED TO PROVIDE TSID

    """

    def __init__(self, url, player_ratings_df, df_tour_res):
        """
        instantiate TourPlayerId class
        :param url: str - url which links to player tournament stats
        :param player_ratings_df - DataFrame - DataFrame with player ranking stats
        :param df_tour_res: - DataFrame - res table to look up previous values - schema :tsid, tour_ref, tour_player_id
        """
        self.url = url
        self.player_ratings_df = player_ratings_df
        self.df_tour_res = df_tour_res
        self.cookies = {'ASP.NET_SessionId': 'samot0pr3nnbuav0vs3l1oop',
                        'st': 'l=2057&exp=44802.7753505324&c=1&cp=20',
                        'expires': 'Mon, 29-Aug-2022 16:36:30 GMT',
                        'path': '/'
                        }

    def _set_tour_player_ref(self):
        """extract tournament_id and player_tournament_id from url"""
        self.tour_ref, self.tour_player_id = self.url.split('player.aspx?id=')[1].split('&player=')

    def get_tsid(self):
        """get TSID for player: Either from df or by extracting it from html"""
        # set essential variables
        self._set_tour_player_ref()
        if len(self.df_tour_res.loc[((self.df_tour_res['tour_ref'] == self.tour_ref) &
                                     (self.df_tour_res['tour_player_id'] == self.tour_player_id)), 'tsid']) > 0:
            tsid = self.df_tour_res.loc[((self.df_tour_res['tour_ref'] == self.tour_ref) &
                                         (self.df_tour_res['tour_player_id'] == self.tour_player_id)), 'tsid'].values[0]
        else:

            tsid = self.scrape_tsid()
            self.update_tour_df(tsid)

        return tsid

    def update_tour_df(self, tsid):
        """update DataFrame storing tournament ref and tsid mapping"""
        row = pd.DataFrame.from_dict(
            {'tsid': [tsid], 'tour_ref': [self.tour_ref], 'tour_player_id': [self.tour_player_id]})
        self.df_tour_res = self.df_tour_res.append(row, ignore_index=True)

    def scrape_tsid(self):
        """if tsid isn't available in look up table, then collect via scraping"""
        self.soup = bs(requests.get(self.url, cookies=self.cookies).content, 'html.parser')

        try:
            # Get TSID from player ranking df
            unique_player_ref = self.soup.find('div', class_='content').find('div', class_='wrapper--legacy') \
                .find('div', class_='subtitle').find('a', href=True)['href'].split('player-profile/')[-1]
            tsid = self.player_ratings_df.loc[self.player_ratings_df['Id'] == unique_player_ref, 'tsid'].values[0]
        except Exception as e:
            try:
                # Get TSID from player profile html - Slowest method - used as last attempt
                p_url = self.soup.find('div', class_='content').find('div', class_='wrapper--legacy') \
                    .find('div', class_='subtitle').find('a', href=True)['href']
                p_url = 'https://be.tournamentsoftware.com' + p_url
                soup = bs(requests.get(p_url, cookies=self.cookies).content, 'html.parser')
                tsid = soup.find('div', class_='page-head page-head--pattern wrapper wrapper--branding') \
                           .find('span', class_='media__title-aside').text[1:-1]
            except Exception as e2:
                # There are cases where the player doesn't have a profile on tournament software e.g
                'https://be.tournamentsoftware.com/sport/player.aspx?id=716287F7-461C-4818-B699-BCAE526CCB0D&player=2531'
                print(f'TSID not found for url: {self.url}')
                # print(traceback.format_exc())
                tsid = np.nan

        return tsid

    def get_tour_ref_df(self):
        """Return the results df - table of tour_ref, player_ref, player_id"""
        return self.df_tour_res
