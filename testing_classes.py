import requests
from bs4 import BeautifulSoup as bs
import numpy as np
import pandas as pd
import re
import traceback

class Player:
    '''
    class to capture player attributes

    Attributes:
        url - str
            url to player profile page on tournament software

    '''

    def __init__(self, url, name, tsid, player_ratings_df, df_tour_res):
        '''
        instantiates player object with profile url
        :param url: str - profile url from tournament software
                name: str - player name
                tsid: str - unique id of player
                player_ratings_df - DataFrame -
                df_tour_res - DataFrame - Schema
        '''
        self.url = url
        self.name = name
        self.tsid = tsid
        self.player_ratings_df = player_ratings_df
        self.df_tour_res = df_tour_res

    def get_df_tour_res(self):
        return self.df_tour_res

    def get_tournament_results(self,year):
        '''
        Get results for all tournament matches in given year
        :param year: int - year in format YYYY e.g 2019
        :return: pd.DataFrame - results of all matches within given year
        '''
        if self.url[-1] == '/':
            self.url = self.url[:-1]

        self.url += f'/tournaments/{year}'
        tour = TournamentResults(self.url, self.tsid, self.player_ratings_df, self.df_tour_res)
        if tour.check_if_results_exist():
            ply_tour_res = tour.collect_all_results()
            self.df_tour_res = tour.get_df_tour_res()
            return ply_tour_res
        else:
            print(f'No results for: {self.name} in {year}')
            return []


class Match:
    '''
    Class to represent a match
    TO DO - HANDLE FOR BYE'S OR MATCHES CALLED OFF
    '''
    def __init__(self, tag, tsid, player_ratings_df, df_tour_res):
        '''
        initialise a match object
        :param
            tag: bs4.tag - li class=match-group__item
            name: str - name of player searching for
            tsid; str - unique id of player searching on
        '''
        self.tag = tag
        self.tsid = tsid
        self.player_ratings_df = player_ratings_df
        self.df_tour_res = df_tour_res

    def check_for_no_match(self):
        '''
        Helper method to check if a match was played.
        :return: bool : True if no match, False if match played
        '''
        no_match = None
        try:
            no_match = self.tag.find('span', class_='tag--warning tag match__message').text.strip()
        except:
            pass

        if no_match:
            return True
        else:
            return False


    def get_match_duration(self):
        '''
        extract match duration if available, else return n/a
        :return: match_duration (str) - duration of match if available
        '''
        try:
            match_duration = self.tag.find('div', class_='match__header-aside').text.strip()
            #Remove Match stats text if included
            if re.search('(?i)Match stats', match_duration):
                match_duration = match_duration.split('Match stats')[-1].strip()
        except Exception as e:
            match_duration = 'n/a'
        return match_duration


    def get_match_id(self):
        '''
        extract match_id from href if available
        :return: match_id (str) - match_id if available
        '''
        try:
            match_id = self.tag.find('div', class_='match__header-aside').find('a')['href'].split('match=')[-1]
        except Exception as e:
            match_id = 'n/a'
        return match_id


    def get_match_scores_list(self,css_class_name):
        '''
        helper function to collect scores
        args:
           css_class_name  - str - Name of css class to select
        '''
        try:
            return [int(res.text.strip()) for res in self.tag.find(lambda tag: tag.name == 'div' and
                    tag['class'] == css_class_name.split()).find('div', class_='match__result')
                .find_all('li', class_='points__cell')]
        except Exception as e:
            return 'n/a'


    def get_match_date(self):
        try:
            match_date = self.tag.find('div', {'class': 'match__footer'}) \
                .find('svg', {'class': 'icon-clock nav-link__prefix'}).find_next_sibling().text
        except:
            match_date = self.tag.find('div', {'class': 'match__footer'}) \
                .find('span', {'class': 'nav-link__value'}).text
        return match_date


    def get_court(self):
        try:
            court = self.tag.find('div', {'class': 'match__footer'}) \
                .find_all('li', {'class': 'match__footer-list-item'})[-1].text.strip()
        except:
            court = 'n/a'
        return court


    def get_df_tour_res(self):
        '''
        Helper function to get DataFrame with tour results to map to players
        :return:
            df_tour_res - DataFrame
        '''
        return self.df_tour_res


    def get_match_stats(self):
        '''
        TO DO - HANDLE FOR BYE'S OR MATCHES CALLED OFF

        :return: match data/results - dict - key/values

        {'match_title': str,
        'match_id':str,
        'match_duration': str,
        'match_date':str,
        'match_court': match_court,
        'winning_team_p1': str,
        'winning_team_p2': str,
        'losing_team_p1': str,
        'losing_team_p2': str,
        'winning_team_scores': list,
        'losing_team_scores': list}

        '''
        match_title = self.tag.find('div', class_='match__header-title').text.strip()
        match_duration = self.get_match_duration()
        match_id = self.get_match_id()
        match_date = self.get_match_date()
        match_court = self.get_court()

        # Set empyt player dict
        match_data_dict = {
            'match_title': match_title,
            'match_id':match_id,
            'match_duration': match_duration,
            'match_date': match_date,
            'match_court': match_court,
            'winning_team_p1': np.nan,
            'winning_team_p1_tsid': np.nan,
            'winning_team_p2': np.nan,
            'winning_team_p2_tsid': np.nan,
            'losing_team_p1': np.nan,
            'losing_team_p1_tsid': np.nan,
            'losing_team_p2': np.nan,
            'losing_team_p2_tsid': np.nan,
            'winning_team_scores': np.nan,
            'losing_team_scores': np.nan
        }

        for num, player in enumerate(self.tag.find('div',class_='match__row has-won')
                                             .find('div','match__row-title').findChildren(recursive=False)):
            match_data_dict[f'winning_team_p{num + 1}'] = player.text.strip()
            # print(f'winning team p{num + 1}: {player.text.strip()}')
            #Getting TSID for player
            win_href = 'https://be.tournamentsoftware.com' + player.find('a')['href']
            tp_id = TourPlayerId(win_href, self.df_tour_res, self.player_ratings_df)
            match_data_dict[f'winning_team_p{num + 1}_tsid'] = tp_id.get_tsid()
            #Update tournament result dataframe - used to quickly allocate TSID to players
            self.df_tour_res = tp_id.get_tour_ref_df()

        for num, player in enumerate(self.tag.find(lambda tag: tag.name == 'div' and tag['class'] == 'match__row '.split())
                                             .find('div','match__row-title').findChildren(recursive=False)):
            match_data_dict[f'losing_team_p{num + 1}'] = player.text.strip()
            # print(f'losing team p{num + 1}: {player.text.strip()}')
            #Getting TSID for player
            win_href = 'https://be.tournamentsoftware.com' + player.find('a')['href']
            tp_id = TourPlayerId(win_href, self.df_tour_res, self.player_ratings_df)
            match_data_dict[f'losing_team_p{num + 1}_tsid'] = tp_id.get_tsid()
            #Update tournament result dataframe - used to quickly allocate TSID to players
            self.df_tour_res = tp_id.get_tour_ref_df()

        for lab, val in zip(['winning_team_scores','losing_team_scores'],['match__row has-won','match__row ']):
            match_data_dict[lab] = self.get_match_scores_list(val)

        return match_data_dict


class TournamentResults:
    def __init__(self, url, tsid, player_ratings_df, df_tour_res):
        '''
        instantiate TournamentResults class
        :param
            url: str - url for player tournament stats
            name: str - player which you are searching for tournament results for
            tsid: str - unique id code for player searching on
        '''
        self.cookies = {'ASP.NET_SessionId': 'samot0pr3nnbuav0vs3l1oop',
                       'st': 'l=2057&exp=44802.7753505324&c=1&cp=20',
                       'expires': 'Mon, 29-Aug-2022 16:36:30 GMT',
                       'path': '/'
                       }
        self.results = []
        self.url = url
        self.tsid = tsid
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
                            m1 = Match(match, self.tsid, self.player_ratings_df, self.df_tour_res)
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
    '''
    def __init__(self, url, df, player_ratings_df):
        '''
        instantiate TourPlayerId class
        :param url: str - url which links to player tournament stats
        :param df: - DataFrame - results table to look up previous values - schema :  tsid, tour_ref, tour_player_id
        :param player_ratings_df - DataFrame - DataFrame with player ranking stats
        '''
        self.url = url
        self.df = df
        self.player_ratings_df = player_ratings_df

    def _set_tour_player_ref(self):
        '''extract tournament_id and player_tournament_id from url'''
        self.tour_ref, self.tour_player_id = self.url.split('player.aspx?id=')[1].split('&player=')

    def get_tsid(self):
        '''get TSID for player: Either from df or by extracting it from html'''
        #set essential variables
        self._set_tour_player_ref()
        if len(self.df.loc[((self.df['tour_ref'] == self.tour_ref) &
                            (self.df['tour_player_id'] == self.tour_player_id)), 'tsid']) > 0:
            tsid = self.df.loc[((self.df['tour_ref'] == self.tour_ref) &
                                (self.df['tour_player_id'] == self.tour_player_id)), 'tsid'].values[0]
        else:

            tsid = self.scrape_tsid()
            self.update_tour_df(tsid)

        return tsid

    def update_tour_df(self,tsid):
        '''update DataFrame storing tournament ref and tsid mapping'''
        row = pd.DataFrame.from_dict({'tsid':[tsid],'tour_ref':[self.tour_ref],'tour_player_id':[self.tour_player_id]})
        self.df = self.df.append(row,ignore_index=True)

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
                print(traceback.format_exc())
                tsid = np.nan

        return tsid

    def get_tour_ref_df(self):
        '''Return the results df - table of tour_ref, player_ref, player_id'''
        return self.df


