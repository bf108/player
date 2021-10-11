import pandas as pd
import os

os.chdir('/home/cdsw/player_workspace')

from player import Player


def main():
    df_player_table = pd.read_csv('/home/cdsw/player_rankings_2019.csv')
    # player ref not available without generating
    df_player_table['Id'] = df_player_table.Profile_url.apply(lambda x: x.split('player-profile/')[-1])

    all_results = []

    total = df_player_table.shape[0]

    # df tour results
    df_tour_res = pd.DataFrame.from_dict({'tsid': [], 'tour_ref': [], 'tour_player_id': []})
    df_tour_res = df_tour_res.astype('object')
    for row in df_player_table.iterrows():
        print(f'Collecting Results for {row[1].Player}, player {row[0] + 1} of {total}')
        name, url = row[1].loc[['Player', 'Profile_url']]
        ply = Player(url, name, df_player_table, df_tour_res)
        # list of dictionaries
        ply_results = ply.get_tournament_results(2019)
        all_results += ply_results
        # Update tour results dataframe
        df_tour_res = ply.get_df_tour_res()
        df_tour_res.drop_duplicates(inplace=True)

    df_all_results = pd.DataFrame.from_dict(all_results)
    df_all_results.to_csv('/home/cdsw/player_tournament_results_2019_.csv', index=False)
    df_tour_res.to_csv('/home/cdsw/player_tournament_results_references_2019_.csv', index=False)


if __name__ == '__main__':
    main()
