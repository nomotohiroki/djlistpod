import calendar
import logging
from email import utils

from django.shortcuts import redirect, render_to_response
from django.http      import HttpResponse
from django.template  import RequestContext
from django.template.defaultfilters import register

from youtube_dl           import YoutubeDL
from youtube_dl.extractor import YoutubeIE

from app.client           import Youtube


# global instanses
ydl = None
ie  = None
y   = None

logger = logging.getLogger('myapp')

@register.filter(name='rss_pubdate')
def rss_pubdate(datetime):
    return utils.formatdate(calendar.timegm(datetime.timetuple()))


def index(request):
    _init_ycl(request)
    playlist_info     = None
    subscription_info = None
    channel_info      = None
    if y.is_authorized():
        playlist_info     = y.playlists()
        subscription_info = y.subscriptions()
        channel_info      = y.channel()
    
    return render_to_response(
        "dashboard.html",
        {
            'authorized':    y.is_authorized(),
            'channel':       channel_info,
            'playlists':     playlist_info,
            'subscriptions': subscription_info,
        },
        context_instance=RequestContext(request)
    )

def playlist(request, playlist_id):
    _init_ycl(request)
    playlist = y.playlist(playlist_id)
    return _render_podcast(request, playlist)

def favorites(request, user_name=None):
    _init_ycl(request)
    playlist = y.favorites(user_name)
    return _render_podcast(request, playlist)

def video(request, video_id):
    _init_ycl(request)
    o = ie.extract(video_id)
    # selected_url = ydl.select_format('best', o['formats'])['url']
    format_selector = ydl.build_format_selector('best')
    selected_url = list(format_selector(o['formats']))[0]['url']
    return redirect(selected_url)

def oauth2callback(request):
    y.exchange(request.GET['code'])
    return redirect("/")


def _init_ycl(request):
    global ydl, ie, y
    if y == None:
        ydl = YoutubeDL()
        ie  = YoutubeIE(ydl)
        y = Youtube(request.scheme + "://" + request.get_host() + "/oauth2callback")


def _render_podcast(request, playlist):
    mode = request.GET['mode'] if 'mode' in request.GET else None
    response = render_to_response('feed.html' if mode == 'html' else 'podcast.rss',
                              {
                                  'request': request,
                                  'title':  playlist['title']  if playlist else None,
                                  'videos': playlist['videos'] if playlist else None,
                              },
                              content_type = 'text/html' if mode == 'html' else 'application/rss+xml',
                              context_instance=RequestContext(request))
    response['Content-Length'] = len(response.content)
    return response
