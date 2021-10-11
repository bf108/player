import requests
from bs4 import BeautifulSoup as bs
from scrapper import generateSoup
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import numpy as np
import pandas as pd
import re


def find_first_tournament_elm(soup):
    '''
    Find first tournament div element on individual player tournament results page

    args:
        soup - bs4 object - beautiful soup 4 object

    returns:
        first_tour_elm - bs4 object - first tournament div element
    '''
    first_tour_elm = soup.find('div', class_='content').find('div', class_='page-content-start js-is-loading') \
        .find('div', class_='is-loading-element is-loading-element--blur') \
        .find('div', class_='is-loading-element is-loading-element--blur').findChild()
    return first_tour_elm


cookies = {'ASP.NET_SessionId': 'samot0pr3nnbuav0vs3l1oop',
           'st': 'l=2057&exp=44802.7753505324&c=1&cp=20',
           'expires': 'Mon, 29-Aug-2022 16:36:30 GMT',
           'path': '/'}


url = "https://be.tournamentsoftware.com/player-profile/437C70CF-9D42-4F39-958C-6792BF9513AF"
# url = 'https://be.tournamentsoftware.com/player-profile/437c70cf-9d42-4f39-958c-6792bf9513af/tournaments/2019'


class Player:
    '''
    class to capture player attributes

    Attributes:
        url - str
            url to player profile page on tournament software

    '''

    def __init__(self, url):
        '''
        instantiates player object with profile url
        :param url: str - profile url from tournament software
        '''
        self.url = url

    def get_tournament_results(self,year):
        '''
        Get results for all tournament matches in given year
        :param year: int - year in format YYYY e.g 2019
        :return: pd.DataFrame - results of all matches within given year
        '''
        if self.url[-1] == '/':
            self.url = self.url[:-1]

        self.url += f'/tournaments/{year}'

        return self.url


class TournamentResults:
    def __init__(self, url):
        self.cookies = {'ASP.NET_SessionId': 'samot0pr3nnbuav0vs3l1oop',
                       'st': 'l=2057&exp=44802.7753505324&c=1&cp=20',
                       'expires': 'Mon, 29-Aug-2022 16:36:30 GMT',
                       'path': '/'
                       }
        results = {
            'tournament': [],
            'location': [],
            'tour_dates': [],
            'event_title': [],
            'sub_event_title': [],
            'match': [],
            'match_id':[],
            'match_duration': [],
            'match_date':[],
            'winning_team_p1': [],
            'winning_team_p2': [],
            'losing_team_p1': [],
            'losing_team_p2': [],
            'winning_team_scores': [],
            'losing_team_scores': [],
            }
        self.df_results = pd.DataFrame.from_dict(results)
        self.url = url
        self.soup = bs(requests.get(self.url, cookies=self.cookies).content, 'html.parser')


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
            name, location, date - tuple (str)
        '''
        meta = tournament.find('li', class_='list__item').find_all(recursive=False)[0]
        name = meta.find('h4', class_='media__title media__title--medium').text.strip()
        loc = meta.find('small', class_='media__subheading').text.strip().split('|')[1].strip()
        date = meta.find('small', class_='media__subheading media__subheading--muted').text.strip()

        return name, loc, date


    def _split_events(self,tournament):
        '''
        splits tournament up into events
        :param tournament: bs.element (div class=module module--card)
        :return:
            list of list of bs.elements -
            Each sub list will be made up of:
                <h4> for event
                    <h5> for subevents - Possible to have many subevents under and event
                        <ol> for matches in subevent
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


    def _get_event_details(self, event):
        '''
        args:
            event - list - elements are bs4 objects - either h4, h5 or ol
        returns:
            event_title - str
        '''
        for el in event:
            if el.name == 'h4':
                event_name = el.text.strip().split('Event: ')[1]
                print(f'Event: {event_name}')
            elif el.name == 'h5':
                sub_event = item.text.strip()
                print('Sub Event:' {sub_event})
            elif el.name == 'ol':
                pass



    def _get_event_details(self, tournament):
        li_item = tournament.find('li', class_='list__item').find_all(recursive=False)[1:]

        for el in li_item:
            if el.name == 'h4':
                event = el.text.strip().split('Event: ')[1]
                print(f'Event: {event}')
            elif el.name == 'h5':
                sub_event = item.text.strip()
                print('Sub Event:' {sub_event})
            elif el.name == 'ol':
                pass


    def _get_match_duration(self, match):
        '''
        extract match duration if available, else return n/a
        :param match: bs4.element
        :return: match_duration (str) - duration of match if available
        '''
        try:
            match_duration = match.find('div', class_='match__header-aside').text.strip()
        except Exception as e:
            match_duration = 'n/a'

        return match_duration


    def _get_match_id(self, match):
        '''
        extract match_id from href if available
        :param match: bs4.element
        :return: match_id (str) - match_id if available
        '''
        try:
            match_id = match.find('div', class_='match__header-aside').find('a')['href'].split('match=')[-1]
        except Exception as e:
            match_id = 'n/a'


    def _get_match_stats(self, elm):
        '''

        :param elm:
        :return:
        '''
        for match in elm.find_all(recursive=False):
            match_title = match.find('div', class_='match__header-title').text.strip()
            match_duration = self._get_match_duration(match)
            match_id = self._get_match_id(match)

            # Set empyt player dict
            players_dict = {
                'team_1_p1': np.nan,
                'team_1_p2': np.nan,
                'team_2_p1': np.nan,
                'team_2_p2': np.nan,
                'team_1_scores': np.nan,
                'team_2_scores': np.nan
            }



            for team, row in enumerate(match.find('div', class_='match__row-wrapper').findChildren(recursive=False)):
                # Consider changing this to specific win/loss
                # Rather than iterating
                for num, player in enumerate(row.find('div', class_='match__row-title').findChildren(recursive=False)):
                    print(f'Team_{team + 1}_Player_{num + 1}: {player.text.strip()}')
                    players_dict[f'team_{team + 1}_p{num + 1}'] = player.text.strip()

                if row.attrs['class'][0] == 'match__row has-won':
                    try:
                        scores = [res.text.strip() for res in row.find('div', class_='match__result').find_all('li',
                                                                                                               class_='points__cell points__cell--won')]
                        players_dict[f'team_{team + 1}_scores'] = scores
                    except:
                        print('No score available - potential Walkover')
                else:
                    try:
                        scores = [res.text.strip() for res in
                                  row.find('div', class_='match__result').find_all('li', class_='points__cell')]
                        players_dict[f'team_{team + 1}_scores'] = scores
                    except:
                        print('No score available - potential Walkover')

            # Append Results to dict
            data = {
                'name': name,
                'loc': loc,
                'date': date,
                'event': event,
                'sub_event': sub_event,
                'match': match_title,
                'duration': match_duration
            }

            new_data = {**data, **players_dict}

            df_results = df_results.append(new_data, ignore_index=True)


    def _get_event_details(self, event):
        '''
        args:
            event - list - elements are bs4 objects - either h4, h5 or ol
        returns:
            event_title - str
        '''
        for el in event:
            if el.name == 'h4':
                event_name = el.text.strip().split('Event: ')[1]
                print(f'Event: {event_name}')
            elif el.name == 'h5':
                sub_event = item.text.strip()
                print('Sub Event:' {sub_event})
            elif el.name == 'ol':
                pass


    def populate_results(self):
        tournaments = self._find_all_tournaments()
        for tour in tournaments:
            name, loc, date = self._get_tournament_meta(tour)
            for event in self._split_events(tour):

            for event in tour.find('li').find_all('ol',recursive=False):
                event_title = self._get_event_details(event)




for item in tour_items:
    if '<h4 ' in str(item).split('\n')[0]:
        event = item.text.strip().split('Event: ')[1]
        print(event)
    elif '<h5 ' in str(item).split('\n')[0]:
        sub_event = item.text.strip()
        print(sub_event)
    else:
        for match in item.findChildren(recursive=False):
            match_title = match.find('div', class_='match__header-title').text.strip()
            try:
                match_duration = match.find('div', class_='match__header-aside').text.strip()
            except Exception as e:
                match_duration = 'n/a'

            print(f'{match_title}: {match_duration}')

            # Set empyt player dict
            players_dict = {
                'team_1_p1': np.nan,
                'team_1_p2': np.nan,
                'team_2_p1': np.nan,
                'team_2_p2': np.nan,
                'team_1_scores': np.nan,
                'team_2_scores': np.nan
            }

            for team, row in enumerate(match.find('div', class_='match__row-wrapper').findChildren(recursive=False)):
                # Consider changing this to specific win/loss
                # Rather than iterating
                for num, player in enumerate(row.find('div', class_='match__row-title').findChildren(recursive=False)):
                    print(f'Team_{team + 1}_Player_{num + 1}: {player.text.strip()}')
                    players_dict[f'team_{team + 1}_p{num + 1}'] = player.text.strip()

                if row.attrs['class'][0] == 'match__row has-won':
                    try:
                        scores = [res.text.strip() for res in row.find('div', class_='match__result').find_all('li',
                                                                                                               class_='points__cell points__cell--won')]
                        players_dict[f'team_{team + 1}_scores'] = scores
                    except:
                        print('No score available - potential Walkover')
                else:
                    try:
                        scores = [res.text.strip() for res in
                                  row.find('div', class_='match__result').find_all('li', class_='points__cell')]
                        players_dict[f'team_{team + 1}_scores'] = scores
                    except:
                        print('No score available - potential Walkover')

            # Append Results to dict
            data = {
                'name': name,
                'loc': loc,
                'date': date,
                'event': event,
                'sub_event': sub_event,
                'match': match_title,
                'duration': match_duration
            }

            new_data = {**data, **players_dict}

            df_results = df_results.append(new_data, ignore_index=True)


# Extract tournament heading details
# Get Tournament name, location, date

name = tour_heading_elm.find('h4', class_='media__title media__title--medium').text.strip()
loc = tour_heading_elm.find('small', class_='media__subheading').text.strip().split('|')[1].strip()
date = tour_heading_elm.find('small', class_='media__subheading media__subheading--muted').text.strip()

# Extract Details from tournamnent
tour_items = tour_heading_elm.find_next_siblings()

results = {
    'name': [],
    'loc': [],
    'date': [],
    'event': [],
    'sub_event': [],
    'match': [],
    'duration': [],
    'team_1_p1': [],
    'team_1_p2': [],
    'team_2_p1': [],
    'team_2_p2': [],
    'team_1_scores': [],
    'team_2_scores': [],
}

df_results = pd.DataFrame.from_dict(results)

df_results.head()

for item in tour_items:
    if '<h4 ' in str(item).split('\n')[0]:
        event = item.text.strip().split('Event: ')[1]
        print(event)
    elif '<h5 ' in str(item).split('\n')[0]:
        sub_event = item.text.strip()
        print(sub_event)
    else:
        for match in item.findChildren(recursive=False):
            match_title = match.find('div', class_='match__header-title').text.strip()
            try:
                match_duration = match.find('div', class_='match__header-aside').text.strip()
            except Exception as e:
                match_duration = 'n/a'

            print(f'{match_title}: {match_duration}')

            # Set empyt player dict
            players_dict = {
                'team_1_p1': np.nan,
                'team_1_p2': np.nan,
                'team_2_p1': np.nan,
                'team_2_p2': np.nan,
                'team_1_scores': np.nan,
                'team_2_scores': np.nan
            }

            for team, row in enumerate(match.find('div', class_='match__row-wrapper').findChildren(recursive=False)):
                # Consider changing this to specific win/loss
                # Rather than iterating
                for num, player in enumerate(row.find('div', class_='match__row-title').findChildren(recursive=False)):
                    print(f'Team_{team + 1}_Player_{num + 1}: {player.text.strip()}')
                    players_dict[f'team_{team + 1}_p{num + 1}'] = player.text.strip()

                if row.attrs['class'][0] == 'match__row has-won':
                    try:
                        scores = [res.text.strip() for res in row.find('div', class_='match__result').find_all('li',
                                                                                                               class_='points__cell points__cell--won')]
                        players_dict[f'team_{team + 1}_scores'] = scores
                    except:
                        print('No score available - potential Walkover')
                else:
                    try:
                        scores = [res.text.strip() for res in
                                  row.find('div', class_='match__result').find_all('li', class_='points__cell')]
                        players_dict[f'team_{team + 1}_scores'] = scores
                    except:
                        print('No score available - potential Walkover')

            # Append Results to dict
            data = {
                'name': name,
                'loc': loc,
                'date': date,
                'event': event,
                'sub_event': sub_event,
                'match': match_title,
                'duration': match_duration
            }

            new_data = {**data, **players_dict}

            df_results = df_results.append(new_data, ignore_index=True)