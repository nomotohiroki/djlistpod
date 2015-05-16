import calendar
from email import utils

from django.shortcuts import redirect, render_to_response
from django.http      import HttpResponse
from django.template  import RequestContext
from django.template.defaultfilters import register

from youtube_dl           import YoutubeDL
from youtube_dl.extractor import YoutubeIE

from app.client           import Youtube


# global instanses
ydl = YoutubeDL()
ie  = YoutubeIE(ydl)
y   = None


@register.filter(name='rss_pubdate')
def rss_pubdate(datetime):
    return utils.formatdate(calendar.timegm(datetime.timetuple()))


def index(request):
    _init_ycl(request)
    playlist_info     = None
    subscription_info = None
    channel_info      = None
    if y != None and y.is_authorized():
        playlist_info     = y.playlists()
        subscription_info = y.subscriptions()
        channel_info      = y.channel()
    
    return render_to_response('dashboard.html', { 'channel': channel_info, 'playlists': playlist_info, 'subscriptions': subscription_info }, context_instance=RequestContext(request))

def playlist(request, playlist_id):
    _init_ycl(request)
    if y == None or not y.is_authorized():
        return HttpResponse(u'Not Authorized.')
    playlist = y.playlist(playlist_id)
    return _render_podcast(request, playlist)

def favorites(request, user_name=None):
    _init_ycl(request)
    if y == None or not y.is_authorized():
        return HttpResponse(u'Not Authorized.')
    playlist = y.favorites(user_name)
    return _render_podcast(request, playlist)

def video(request, video_id):
    _init_ycl(request)
    if y == None or not y.is_authorized():
        return HttpResponse(u'Not Authorized.')
    o = ie.extract('https://www.youtube.com/watch?v=' + video_id)
    selected_url = ydl.select_format('best', o['formats'])['url']
    return redirect(selected_url)

def oauth2callback(request):
    y.exchange(request.GET['code'])
    return redirect("/favorites/")


def _init_ycl(request):
    global y
    if y == None:
        y = Youtube(request.scheme + "://" + request.get_host() + "/oauth2callback")


def _render_podcast(request, playlist):
    response = render_to_response('podcast.rss',
                              {
                                  'request': request,
                                  'title':  playlist['title'],
                                  'videos': playlist['videos'],
                              },
                              content_type = 'application/rss+xml',
                              context_instance=RequestContext(request))
    response['Content-Length'] = len(response.content)
    return response
