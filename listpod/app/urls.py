from django.conf.urls import patterns, url
from app import views

urlpatterns = patterns('',
    url(r'^playlist/(?P<playlist_id>[\d\w-]+)$', views.playlist,       name='playlist'),
    url(r'^video/(?P<video_id>[\d\w-]+)\.mp4$',  views.video,          name='video'),
    url(r'^favorites/$',                         views.favorites,      name='myfavorites'),
    url(r'^favorites/(?P<user_name>[\d\w-]+)$',  views.favorites,      name='favorites'),
    url(r'^oauth2callback$',                     views.oauth2callback, name='oauth2callback'),
    url(r'^$',                                   views.index,          name='index'),
)
