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
    API_VERSION      = None

    API_KEY          = 'AIzaSyAqNEFzRIXBwDdO3PwZYKeoVBgkCOYBLOc'

    CLIENT_SECRETS   = os.path.join(os.path.dirname(__file__), 'client_secrets.json')
    CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), 'credential.json')

    _is_authorized = False
    
    def __init__(self, redirect_uri):
        self.apiclient = build(self.API_SERVICE_NAME, self.API_VERSION, developerKey = self.API_KEY)
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
    
    VIDEO_BASE_URL = 'https://www.youtube.com/watch?v='

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
        if not self.is_authorized() and user_name == None:
            return None

        favorites_playlist_id = self.channel()['playlists']['favorites']
        return self.playlist(favorites_playlist_id)

    def channel(self, user_name=None):
        if not self.is_authorized() and user_name == None:
            return None
        
        response_channel = self.apiclient.channels().list(
            part        = 'snippet,contentDetails',
            forUsername = user_name,
            mine        = True  if user_name == None else False,
        ).execute()['items'][0]
        
        related_playlists = response_channel['contentDetails']['relatedPlaylists']

        return {
            'title' : response_channel['snippet']['title'],
            'thumbnail': response_channel['snippet']['thumbnails']['default']['url'],
            'playlists': {
                'likes'     : related_playlists['likes']      if 'likes'      in related_playlists else None,
                'favorites' : related_playlists['favorites']  if 'favorites'  in related_playlists else None,
                'uploads'   : related_playlists['uploads']    if 'uploads'    in related_playlists else None,
                'watchLater': related_playlists['watchLater'] if 'watchLater' in related_playlists else None,
            },
        }

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
                'url':         self.VIDEO_BASE_URL + item['snippet']['resourceId']['videoId'],
                'title':       item['snippet']['title'],
                'description': item['snippet']['description'],
                'timestamp':   datetime.strptime(item['snippet']['publishedAt'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=pytz.utc),
                'thumbnail':   item['snippet']['thumbnails']['default']['url'] if 'thumbnails' in item['snippet'] else None
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
