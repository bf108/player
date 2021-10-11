# Player App Data Collection

## Objective
- Collect Badminton Player Ranking and Meta Data for 2019-2020.
- Collect Badminton Tournament Match results for group of players listed within firestore db.
- This data is collected from [tournamentsoftware](https://be.tournamentsoftware.com/ranking/ranking.aspx?rid=87)

## Player Rankings Data
Ranking data collected from 1st week in 2019 for the following groups:


|Group| Accronym |	Unique Players Count |
|---|---|---|
|Mens singles	| MS	    |1679 |
|womens singles |	WS	  |806 |
|Mens Doubles	| MD	    |1804 |
|Women Doubles|	WD	    |1001 |
|Mens Mixed Doubles |	Mens XDs |	892 |
|Womens Mixed Doubles |	Womens XDs	| 796 |

Schema for Rank Table

| Rank | Change | non_break_space | Player | Profile_url | Year of birth | Points | Total points | County | Tournaments | tsid | Region |
| ---|---|---|---|---|---|---|---|---|---|---|---|

This table was generated using the `scrapper.py` script using python packages: BeautifulSoup, requests, pandas

## Player Tournament Results 2019
Given the player urls and tsids available in the `player_ranking_table`,  I was then able to collect all tournament results from 2019 for each of these players again using BeautifulSoup and requests. 

In total this eqautes to data on over **35,000** unique matches. 

On some players we have data on over 250 matches. e.g [Indhumathi Coodalingam](https://be.tournamentsoftware.com/player-profile/5b29148a-2411-4796-bd60-63e2fe7a4415)

Average number of matches per player is 20.

I generated a set of Classes to help facilitate this process:

### Class Player
`player.py`

This Class is used to collect all tournament result data for a given player in a particular year. This is required since players can play many tournaments within one calendar year/season.

### Class TournamentResults
The Player Class calls upon TournamentResults class which segregates the various tournaments within a particular year.

Each tournament can have a range of Events: Singles, Doubles, Mixed Doubles. Each event has various stages.

### Class Match
The Match Class is used to collect data from an individual match within a tournament e.g:

- 'draw_id',
- 'draw_title',
- 'event_title',
- 'location',
- 'losing_team_p1',
- 'losing_team_p1_tsid',
- 'losing_team_p2',
- 'losing_team_p2_tsid',
- 'losing_team_scores',
- 'match_court',
- 'match_date',
- 'match_duration'**,
- 'match_id',
- 'match_title',
- 'tour_dates',
- 'tournament',
- 'tournament_id',
- 'winning_team_p1',
- 'winning_team_p1_tsid',*
- 'winning_team_p2',
- 'winning_team_p2_tsid',*
- 'winning_team_scores'

\*: This was sometimes not available when none UK players were playing. Unique Ids for players will be essential when moving to the ranking section (Stage 2 of the project)
\**: On occasion some of the data was missing e.g duration.

Where matches are called off or byes are awarded no results were recorded.

### Scrapping all the tournament results
This task utilises the helper Classes defined above Player, TournamentResults, Match, TournamentPlayerId to iterate through the player rankings table and collect all tournment results from 2019.

The script to perform this is `collect_match_data.py`

## Uploading to Firestore DB
This is performed with `access_firebase_db.py`

Access to the db is gained by accessing credentials saved in json file and initializing app. The results are uploaded in batches of 500.

- Collection (Table) for Rankings is **Player_Rankings**
- Collection (Table) for Tournament Results is **Player_Tournament_Results**

