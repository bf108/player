from tournament_results import TournamentResults


class Player:
    '''Class to collect tournament results for a specific player'''

    def __init__(self, url, name, player_ratings_df, df_tour_res):
        '''
        instantiates player object with profile url
        :param url: str - profile url from tournament software
                name: str - Player name
                player_ratings_df: DataFrame - Collected by scraping ranking tables
                df_tour_res: DataFrame - Schema: tour_player_id, tour_ref, tsid
        '''
        if url[-1] == '/':
            url = url[:-1]
        url += f'/tournaments/'

        self.url = url
        self.name = name
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
        tour_url = self.url + str(year)
        tour = TournamentResults(tour_url, self.player_ratings_df, self.df_tour_res)
        if tour.check_if_results_exist():
            ply_tour_res = tour.collect_all_results()
            self.df_tour_res = tour.get_df_tour_res()
            return ply_tour_res
        else:
            print(f'No results for: {self.name} in {year}')
            return []