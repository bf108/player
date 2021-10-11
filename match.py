import numpy as np
import re
from tournament_player_id import TourPlayerId


class Match:
    """
    Class to represent a match
    TO DO - HANDLE FOR BYE'S OR MATCHES CALLED OFF
    """

    def __init__(self, tag, player_ratings_df, df_tour_res):
        """
        initialise a match object
        :param
            tag: bs4.tag - li class=match-group__item
            player_ratings_df: DataFrame - Collected by scraping ranking tables
            df_tour_res: DataFrame - Schema: tour_player_id, tour_ref, tsid
        """
        self.tag = tag
        self.player_ratings_df = player_ratings_df
        self.df_tour_res = df_tour_res

    def check_for_no_match(self):
        """
        Helper method to check if a match was played.
        :return: bool : True if no match, False if match played
        """
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
        """
        extract match duration if available, else return n/a
        :return: match_duration (str) - duration of match if available
        """
        try:
            match_duration = self.tag.find('div', class_='match__header-aside').text.strip()
            # Remove Match stats text if included
            if re.search('(?i)Match stats', match_duration):
                match_duration = match_duration.split('Match stats')[-1].strip()
        except Exception as e:
            match_duration = 'n/a'
        return match_duration

    def get_match_id(self):
        """
        extract match_id from href if available
        :return: match_id (str) - match_id if available
        """
        try:
            match_id = self.tag.find('div', class_='match__header-aside').find('a')['href'].split('match=')[-1]
        except Exception as e:
            match_id = 'n/a'
        return match_id

    def get_match_scores_list(self, css_class_name):
        """
        helper function to collect scores
        args:
           css_class_name  - str - Name of css class to select
        """
        try:
            return [int(res.text.strip()) for res in self.tag.find(
                lambda tag: tag.name == 'div' and tag['class'] == css_class_name.split())
                .find('div', class_='match__result').find_all('li', class_='points__cell')]
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
        """
        Helper function to get DataFrame with tour results to map to players
        :return:
            df_tour_res - DataFrame
        """
        return self.df_tour_res

    def get_match_stats(self):
        """
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

        """
        match_title = self.tag.find('div', class_='match__header-title').text.strip()
        match_duration = self.get_match_duration()
        match_id = self.get_match_id()
        match_date = self.get_match_date()
        match_court = self.get_court()

        # Set empyt player dict
        match_data_dict = {
            'match_title': match_title,
            'match_id': match_id,
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

        for num, player in enumerate(self.tag.find('div', class_='match__row has-won')
                                             .find('div', 'match__row-title').findChildren(recursive=False)):
            match_data_dict[f'winning_team_p{num + 1}'] = player.text.strip()
            # print(f'winning team p{num + 1}: {player.text.strip()}')
            # Getting TSID for player
            win_href = 'https://be.tournamentsoftware.com' + player.find('a')['href']
            tp_id = TourPlayerId(win_href, self.player_ratings_df, self.df_tour_res)
            match_data_dict[f'winning_team_p{num + 1}_tsid'] = tp_id.get_tsid()
            # Update tournament result dataframe - used to quickly allocate TSID to players
            self.df_tour_res = tp_id.get_tour_ref_df()

        for num, player in enumerate(
                self.tag.find(lambda tag: tag.name == 'div' and tag['class'] == 'match__row '.split())
                        .find('div', 'match__row-title').findChildren(recursive=False)):
            match_data_dict[f'losing_team_p{num + 1}'] = player.text.strip()
            # print(f'losing team p{num + 1}: {player.text.strip()}')
            # Getting TSID for player
            win_href = 'https://be.tournamentsoftware.com' + player.find('a')['href']
            tp_id = TourPlayerId(win_href, self.player_ratings_df, self.df_tour_res)
            match_data_dict[f'losing_team_p{num + 1}_tsid'] = tp_id.get_tsid()
            # Update tournament result dataframe - used to quickly allocate TSID to players
            self.df_tour_res = tp_id.get_tour_ref_df()

        for lab, val in zip(['winning_team_scores', 'losing_team_scores'], ['match__row has-won', 'match__row ']):
            match_data_dict[lab] = self.get_match_scores_list(val)

        return match_data_dict
