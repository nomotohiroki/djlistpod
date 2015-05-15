import os
import httplib2
import webbrowser
import pytz

from abc import ABCMeta, abstractmethod

from datetime import datetime

from apiclient.discovery import build
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file   import Storage

class Client(object):
    __metaclass__ = ABCMeta
    
    SCOPE = None
    API_SERVICE_NAME = None
    API_VERSION = None
    CLIENT_SECRETS   = os.path.join(os.path.dirname(__file__), 'client_secrets.json')
    CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credential.json')
    _is_authorized = False
    
    def __init__(self, redirect_uri):
        self.flow = flow_from_clientsecrets(
            self.CLIENT_SECRETS,
            scope = self.SCOPE,
            redirect_uri = redirect_uri,
        )
        
        storage = Storage(self.CREDENTIALS_FILE)
        credentials = storage.get()

        if credentials == None:
            auth_uri = self.flow.step1_get_authorize_url()
            webbrowser.open_new(auth_uri)
        else:
            self._authorize(credentials)

    def exchange(self, auth_code):
        credentials = self.flow.step2_exchange(auth_code)
        self._authorize(credentials)

    def _authorize(self, credentials):
        self.auth = credentials.authorize(httplib2.Http())
        self.apiclient = build(self.API_SERVICE_NAME, self.API_VERSION, http=self.auth)
        self._is_authorized = True
        storage = Storage(self.CREDENTIALS_FILE)
        storage.put(credentials)

    def is_authorized(self):
        return self._is_authorized



class Youtube(Client):
    SCOPE = "https://www.googleapis.com/auth/youtube"
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"
    _is_authorized = False


    def playlists(self, channel_id=None):
        response_playlists = self.apiclient.playlists().list(
            part       = 'snippet',
            channelId  = channel_id  if channel_id != None else None,
            mine       = True        if channel_id == None else False,
            maxResults = 50,
        ).execute()
        
        playlist_info = []
        
        for item in response_playlists['items']:
            playlist_info.append({
                'playlist_id': item['id'],
                'title':       item['snippet']['title'],
                'description': item['snippet']['description'],
                'thumbnail':   item['snippet']['thumbnails']['default']['url']
            })
        
        return playlist_info

    def favorites(self, user_name=None):
        if user_name:
            response_channel = self.apiclient.channels().list(
                part        = 'contentDetails',
                forUsername = user_name,
            ).execute()
        else:
            response_channel = self.apiclient.channels().list(
                part        = 'contentDetails',
                mine        = True,
            ).execute()
        
        favorites_playlist_id = response_channel['items'][0]['contentDetails']['relatedPlaylists']['favorites']
        return self.playlist(favorites_playlist_id)

    def subscriptions(self, user_name=None, nextPageToken=None):
        response_subscriptions = self.apiclient.subscriptions().list(
            part       = 'snippet,contentDetails',
            mine       = True,
            maxResults = 50,
            pageToken  = nextPageToken if nextPageToken else None,
        ).execute()
        
        subscription_info = []
        
        for item in response_subscriptions['items']:
            subscription_info.append({
                'channel_id':  item['snippet']['resourceId']['channelId'],
                'title':       item['snippet']['title'],
                'description': item['snippet']['description'],
                'thumbnail':   item['snippet']['thumbnails']['default']['url']
            })
        
        return subscription_info

    def playlist(self, playlist_id):
        playlist = self.playlist_info(playlist_id)
        playlist['videos'] = self.playlist_videos(playlist_id)
        
        return playlist

    def playlist_videos(self, playlist_id):
        response_playlistitems = self.apiclient.playlistItems().list(
            part       = 'snippet',
            playlistId = playlist_id,
            maxResults = 50,
        ).execute()
        
        playlist_videos = []

        for item in response_playlistitems['items']:
            playlist_videos.append({
                'video_id':    item['snippet']['resourceId']['videoId'],
                'title':       item['snippet']['title'],
                'description': item['snippet']['description'],
                'timestamp':   datetime.strptime(item['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc),
                'thumbnail':   item['snippet']['thumbnails']['default']['url']
            })
        return playlist_videos


    def playlist_info(self, playlist_id):
        response_playlist = self.apiclient.playlists().list(
            part = 'snippet',
            id   = playlist_id,
        ).execute()['items'][0]

        return {
            'title':       response_playlist['snippet']['title'],
            'description': response_playlist['snippet']['description'],
        }
