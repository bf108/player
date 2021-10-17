import pandas as pd
import firebase_admin
from firebase_admin import credentials, firestore

def upload_player_ranks(collection_name, path_csv, db):
    """
    Write table in csv format to Firestore

    :param collection_name: str - name of collection on Firestore to save to
    :param path_csv: str - local path to csv with rank data
    :param db: google.cloud.firestore_v1.client
    :return: None

    """
    df = pd.read_csv(path_csv)
    batch = db.batch()

    for row_id, row in df.iterrows():
        doc_name = f"{'_'.join(row.get('Player').lower().split(' '))}_{row.get('tsid')}_{row.get('Category')}"
        doc_ref = db.collection(collection_name).document(doc_name)
        batch.set(doc_ref, row.to_dict())
        if row_id > 0 and row_id % 499 == 0:
            batch.commit()
            batch = db.batch()
            print(f'Completed batch {row_id+1 - 499} --> {row_id+1}')


def upload_player_tournament_results(collection_name, path_csv, db):
    """
     Write table in csv format to Firestore

    :param collection_name: str - name of collection on Firestore to save to
    :param path_csv: str - local path to csv with tournament data
    :param db: google.cloud.firestore_v1.client
    :return: None
    """
    df = pd.read_csv(path_csv)
    df.drop_duplicates(inplace=True)
    df.reset_index(inplace=True)

    #Creates a WriteBatch Object - Maximum operations per batch is 500
    batch = db.batch()
    size_of_batch = 0

    for row_id, row in df.iterrows():
        if size_of_batch < 499:
            #Create an automated document ref
            doc_ref = db.collection(collection_name).document()
            #Add document (match results) to batch
            batch.set(doc_ref, row.to_dict())
            #Increment batch size
            size_of_batch += 1
        else:
            print(f"Batch size: {size_of_batch}")
            #Commit batch of 499 results
            batch.commit()
            print(f'Completed batch {row_id+1 - 499} --> {row_id+1}')
            print('-' * 90, '\n')
            #Create a new empty batch and restart counter
            batch = db.batch()
            size_of_batch = 0


def main():
    '''
    Google firebase_admin module Python SDK provides the
    :return:
    '''
    #Credentials for Player Firebase DB
    cred = credentials.Certificate("/home/cdsw/player_workspace/secret_key.json")
    #Initialize App
    app = firebase_admin.initialize_app(cred)
    #Create google.cloud.firestore_v1.client
    db = firestore.client(app)

    print('='*90, '\nUploading Rankings')
    upload_player_ranks('Player_Rankings','/home/cdsw/player_rankings_2019.csv', db)
    print('=' * 90, '\nUploading Tournament Results','\n','=' * 90)
    upload_player_tournament_results('Player_Tournament_Results',
                                     '/home/cdsw/player_tournament_results_2019_.csv', db)


if __name__=='__main__':
    main()
