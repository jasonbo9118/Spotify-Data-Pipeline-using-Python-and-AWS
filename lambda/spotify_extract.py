import json
import os
import requests
from spotipy.oauth2 import SpotifyOAuth
import boto3
from datetime import datetime


def lambda_handler(event, context):

    print("Starting Spotify connection...")

    client_id = os.environ.get("client_id")
    client_secret = os.environ.get("client_secret")
    redirect_uri = os.environ.get("redirect_uri")
    refresh_token = os.environ.get("refresh_token")

    auth_manager = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope="playlist-read-private"
    )

    # Refresh the access token using the token obtained locally
    token_info = auth_manager.refresh_access_token(refresh_token)

    access_token = token_info["access_token"]

    print("Spotify authentication successful!")

    playlist_id = "3k4RaZjxSzRIRlrtUEaGka"

    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/items"

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=10
    )

    print("Spotify API status:", response.status_code)

    response.raise_for_status()
    
    data = response.json()
    
    client = boto3.client('s3')

    file_name = "spotify_raw_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"

    client.put_object(
        Bucket='spotify-etl-project-jt-1',
        Key='raw_data/to_processed/' + file_name,
        Body=json.dumps(data)
    )

    print("Spotify data successfully uploaded to S3")