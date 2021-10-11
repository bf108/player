import requests
from bs4 import BeautifulSoup as bs
import numpy as np
import pandas as pd
import re
import traceback





class TournamentResults:
    def __init__(self, url, player_ratings_df, df_tour_res):
        '''
        instantiate TournamentResults class
        :param
            url: str - url for player tournament stats
            player_ratings_df: DataFrame - Collected by scraping ranking tables
            df_tour_res: DataFrame - Schema: tour_player_id, tour_ref, tsid
        '''
        self.cookies = {'ASP.NET_SessionId': 'samot0pr3nnbuav0vs3l1oop',
                       'st': 'l=2057&exp=44802.7753505324&c=1&cp=20',
                       'expires': 'Mon, 29-Aug-2022 16:36:30 GMT',
                       'path': '/'
                       }
        self.results = []
        self.url = url
        self.soup = bs(requests.get(self.url, cookies=self.cookies).content, 'html.parser')
        self.player_ratings_df = player_ratings_df
        self.df_tour_res = df_tour_res


    def check_if_results_exist(self):
        try:
            no_match_text = self.soup.find('div',class_='content').find('div',class_='page-content-start js-is-loading') \
            .find('div',class_='is-loading-element is-loading-element--blur') \
                .find('div',class_='wrapper wrapper--padding').find('div',class_='module js-is-loading') \
        .find('p',class_='text--center text--muted margin-bottom--small').text.strip()

        except Exception as e:
            no_match_text = 'n/a'

        if no_match_text == 'No matches found.':
            return False
        else:
            return True


    def find_all_tournaments(self):
        '''
        method to list all tournaments
        return:
            list (bs4.element)
        '''
        return self.soup.find('div', class_='content').find('div', class_='page-content-start js-is-loading') \
                           .find('div', class_='is-loading-element is-loading-element--blur') \
                           .find('div', class_='is-loading-element is-loading-element--blur') \
                           .find_all(recursive=False)


    def get_tournament_meta(self, tournament):
        '''
        Extract tournament heading details
        Get Tournament name, location, date

        :param
            tournament - BS4 div element
        :return:
            tour_meta - dict - {'tournament': name,'location': loc, 'tour_dates': date}
        '''
        meta = tournament.find('li', class_='list__item').find_all(recursive=False)[0]
        name = meta.find('h4', class_='media__title media__title--medium').text.strip()
        id = meta.find('h4', class_='media__title media__title--medium').find('a')['href'].split('tournament?id=')[-1]
        loc = meta.find('small', class_='media__subheading').text.strip().split('|')[1].strip()
        date = meta.find('small', class_='media__subheading media__subheading--muted').text.strip()

        tour_meta = {'tournament': name, 'tournament_id':id, 'location': loc, 'tour_dates': date}
        return tour_meta


    def split_events(self,tournament):
        '''
        splits tournament up into events
        :param tournament: bs.element (div class=module module--card)
        :return:
            list of list of bs.elements -
            Each sub list will be made up of:
                <h4> for event
                    <h5> for draws - Possible to have many draws under and event
                        <ol> for matches in draw
        '''
        # Don't include tournament meta which is first div element
        tour_li_items = tournament.find('li').find_all(recursive=False)[1:]
        idx_events = [idx for idx, li in enumerate(tour_li_items) if li.name == 'h4']

        events = []
        for i in range(len(idx_events)):
            if i + 1 < len(idx_events):
                events.append(tour_li_items[idx_events[i]:idx_events[i + 1]])
            else:
                events.append(tour_li_items[idx_events[i]:])
        return events


    def get_event_name(self, event):
        '''
        args:
            event - list - elements are bs4 objects - either h4, h5 or ol
        returns:
            dict - {'event_title':even_title}
        '''
        return {'event_title': event[0].text.strip().split('Event: ')[1]}


    def get_draw_tuples(self, event):
        '''
        partition the draws of each event. Provide the h5 tag (draw title) and ol tag (matches)
        :param event:
        :return: list tuples (bs5.h5, bs4.ol)
        '''
        draws = event[1:]
        draws_tuple_list = []
        for i in range(0,len(draws)-1,2):
            draws_tuple_list.append(draws[i:i+2])

        return draws_tuple_list


    def get_draw_title_id(self, tup):
        '''
        get name of sub event
        :param tup: (bs.h5, bs.ol)
        :return: draw_title_id_dict - dict
        '''
        draw_id, draw_title = tup[0].find('a')['href'].split('draw=')[-1], tup[0].find('a').text.strip()
        draw_title_id_dict = {'draw_title':draw_title, 'draw_id':draw_id}
        return draw_title_id_dict


    def get_match_list(self,tup):
        '''
        return list of match objects
        :param tup: (bs.h5, bs.ol)
        :return: list (bs4.li)
        '''
        return tup[1].find_all('li',class_='match-group__item')


    def collect_all_results(self):
        '''
        stores all tournament results for a player on a specific year
        :return: list of dict
        '''
        for tour in self.find_all_tournaments():
            tour_data_dict = self.get_tournament_meta(tour)
            for event in self.split_events(tour):
                event_dict = self.get_event_name(event)
                for tup in self.get_draw_tuples(event):
                    draw_title_id_dict = self.get_draw_title_id(tup)
                    for match in self.get_match_list(tup):
                        try:
                            m1 = Match(match, self.player_ratings_df, self.df_tour_res)
                            if m1.check_for_no_match():
                                pass
                            else:
                                m1_stats = m1.get_match_stats()
                                #Upate the tournament result df used to located TSID
                                self.df_tour_res = m1.get_df_tour_res()
                                #Combine all results and append to result list
                                comb = {**tour_data_dict, **event_dict,**draw_title_id_dict, **m1_stats}
                                self.results.append(comb)
                        except Exception as e:
                            pass
                            #Match stats not provided due to some issue with scrapping
                            # comb = {**tour_data_dict, **event_dict,**draw_title_id_dict}
                            # print(f'{comb}\n')
                            # print(traceback.format_exc())
        return self.results


    def get_df_tour_res(self):
        return self.df_tour_res


class TourPlayerId:
    '''
    class used to get player TSID from href on player name within match in tournament

    TODO - CONSIDER INCORPORATING LOGGING TO RECORD WHICH URLS FAILED TO PROVIDE TSID

    '''
    def __init__(self, url, player_ratings_df, df_tour_res):
        '''
        instantiate TourPlayerId class
        :param url: str - url which links to player tournament stats
        :param df: - DataFrame - results table to look up previous values - schema :  tsid, tour_ref, tour_player_id
        :param player_ratings_df - DataFrame - DataFrame with player ranking stats
        '''
        self.url = url
        self.player_ratings_df = player_ratings_df
        self.df_tour_res = df_tour_res


    def _set_tour_player_ref(self):
        '''extract tournament_id and player_tournament_id from url'''
        self.tour_ref, self.tour_player_id = self.url.split('player.aspx?id=')[1].split('&player=')


    def get_tsid(self):
        '''get TSID for player: Either from df or by extracting it from html'''
        #set essential variables
        self._set_tour_player_ref()
        if len(self.df_tour_res.loc[((self.df_tour_res['tour_ref'] == self.tour_ref) &
                            (self.df_tour_res['tour_player_id'] == self.tour_player_id)), 'tsid']) > 0:
            tsid = self.df_tour_res.loc[((self.df_tour_res['tour_ref'] == self.tour_ref) &
                                (self.df_tour_res['tour_player_id'] == self.tour_player_id)), 'tsid'].values[0]
        else:

            tsid = self.scrape_tsid()
            self.update_tour_df(tsid)

        return tsid


    def update_tour_df(self,tsid):
        '''update DataFrame storing tournament ref and tsid mapping'''
        row = pd.DataFrame.from_dict({'tsid':[tsid],'tour_ref':[self.tour_ref],'tour_player_id':[self.tour_player_id]})
        self.df_tour_res = self.df_tour_res.append(row,ignore_index=True)


    def scrape_tsid(self):
        '''if tsid isn't available in look up table, then collect via scraping'''
        self.cookies = {'ASP.NET_SessionId': 'samot0pr3nnbuav0vs3l1oop',
                       'st': 'l=2057&exp=44802.7753505324&c=1&cp=20',
                       'expires': 'Mon, 29-Aug-2022 16:36:30 GMT',
                       'path': '/'
                       }
        self.soup = bs(requests.get(self.url, cookies=self.cookies).content, 'html.parser')

        try:
            #Get TSID from player ranking df
            unique_player_ref = self.soup.find('div',class_='content').find('div',class_='wrapper--legacy') \
            .find('div',class_='subtitle').find('a',href=True)['href'].split('player-profile/')[-1]
            tsid = self.player_ratings_df.loc[self.player_ratings_df['Id'] == unique_player_ref, 'tsid'].values[0]
        except Exception as e:
            try:
                # Get TSID from player profile html - Slowest method - used as last attempt
                p_url = self.soup.find('div', class_='content').find('div', class_='wrapper--legacy') \
                    .find('div', class_='subtitle').find('a', href=True)['href']
                p_url = 'https://be.tournamentsoftware.com' + p_url
                soup = bs(requests.get(p_url, cookies=self.cookies).content, 'html.parser')
                tsid = soup.find('div', class_='page-head page-head--pattern wrapper wrapper--branding') \
                   .find('span',class_='media__title-aside').text[1:-1]
            except Exception as e2:
                #There are cases where the player doesn't have a profile on tournament software e.g
                'https://be.tournamentsoftware.com/sport/player.aspx?id=716287F7-461C-4818-B699-BCAE526CCB0D&player=2531'
                print(f'TSID not found for url: {self.url}')
                # print(traceback.format_exc())
                tsid = np.nan

        return tsid


    def get_tour_ref_df(self):
        '''Return the results df - table of tour_ref, player_ref, player_id'''
        return self.df_tour_res


