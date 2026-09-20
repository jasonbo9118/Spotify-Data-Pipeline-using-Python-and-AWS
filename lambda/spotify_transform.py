import json
import boto3
from datetime import datetime
from io import StringIO
import pandas as pd

def album(data):
    album_list = []
    for row in data['items']:
        album_id = row['item']['album']['id']
        album_name = row['item']['album']['name']
        album_release_date = row['item']['album']['release_date']
        album_total_tracks = row['item']['album']['total_tracks']
        album_url = row['item']['album']['external_urls']
        album_element = {'album_id' : album_id, 'album_name' : album_name, 'album_release_date' : album_release_date, 'album_total_tracks' : album_total_tracks, 'album_url' : album_url}
        album_list.append(album_element)

    return album_list

def artist(data):
    artist_list = []
    for row in data['items']:
        artist_id = row['item']['artists'][0]['id']
        artist_name = row['item']['artists'][0]['name']
        artist_url = row['item']['artists'][0]['external_urls']
        artist_element = {'artist_id' : artist_id, 'artist_name' : artist_name, 'artist_url' : artist_url}
        artist_list.append(artist_element)

    return artist_list

def song(data):
    song_list = []
    for row in data['items']:
        song_id = row['item']['id']
        song_name = row['item']['name']
        song_duration = row['item']['duration_ms']
        song_url = row['item']['external_urls']['spotify']
        song_added = row['added_at']
        album_id = row['item']['album']['id']
        artist_id = row['item']['artists'][0]['id']
        song_element = {'song_id' : song_id, 
                        'song_name' : song_name, 
                        'song_duration' : song_duration, 
                        'song_url' : song_url,
                    'song_added' : song_added,
                    'album_id' : album_id,
                    'artist_id' : artist_id}
        song_list.append(song_element)

    return song_list


def lambda_handler(event, context):
    s3 = boto3.client('s3')
    Bucket = 'spotify-etl-project-jt-1'
    Key = 'raw_data/to_processed/'

    spotify_data = []
    spotify_keys = []

    for file in s3.list_objects(Bucket = Bucket, Prefix = Key)['Contents']:
        file_key = file['Key']
        if file_key.split('.')[-1] == 'json':
            response = s3.get_object(Bucket = Bucket, Key = file_key)
            content = response['Body']
            jsonObject = json.loads(content.read())
            spotify_data.append(jsonObject)
            spotify_keys.append(file_key)

    for data in spotify_data:
        album_list = album(data)
        artist_list = artist(data)
        song_list = song(data)

        album_df = pd.DataFrame.from_dict(album_list)
        album_df = album_df.drop_duplicates(subset=['album_id'])

        artist_df = pd.DataFrame.from_dict(artist_list)
        artist_df = artist_df.drop_duplicates(subset=['artist_id'])


        song_df = pd.DataFrame.from_dict(song_list)

        album_df['album_release_date'] = pd.to_datetime(album_df['album_release_date'],format='mixed',errors='coerce')
        song_df['song_added'] = pd.to_datetime(song_df['song_added'])

        song_key = 'transformed_data/songs_data/song_transformed' + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
        song_buffer=StringIO()
        song_df.to_csv(song_buffer, index=False)
        song_content = song_buffer.getvalue()
        s3.put_object(Bucket=Bucket, Key=song_key, Body=song_content)

        album_key = 'transformed_data/album_data/album_transformed' + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
        album_buffer=StringIO()
        album_df.to_csv(album_buffer, index=False)
        album_content = album_buffer.getvalue()
        s3.put_object(Bucket=Bucket, Key=album_key, Body=album_content)
        
        artist_key = 'transformed_data/artist_data/artist_transformed' + datetime.now().strftime("%Y%m%d_%H%M%S") + ".csv"
        artist_buffer=StringIO()
        artist_df.to_csv(artist_buffer, index=False)
        artist_content = artist_buffer.getvalue()
        s3.put_object(Bucket=Bucket, Key=artist_key, Body=artist_content)

    s3_resource = boto3.resource('s3')
    for key in spotify_keys:
        copy_source = {
            'Bucket' : Bucket,
            'Key' : key
        }
        s3_resource.meta.client.copy(copy_source, Bucket, 'raw_data/processed/' + key.split('/')[-1])
        s3_resource.Object(Bucket, key).delete()