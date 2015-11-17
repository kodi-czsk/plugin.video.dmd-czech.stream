# -*- coding: utf-8 -*-
import urllib2,urllib,re,os
from stats import *
import xbmcplugin,xbmcgui,xbmcaddon
import simplejson as json
from hashlib import md5
from time import time

__baseurl__ = 'http://www.stream.cz/API'
_UserAgent_ = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.0.3) Gecko/2008092417 Firefox/3.0.3'
addon = xbmcaddon.Addon('plugin.video.dmd-czech.stream')
profile = xbmc.translatePath(addon.getAddonInfo('profile'))
__settings__ = xbmcaddon.Addon(id='plugin.video.dmd-czech.stream')
home = __settings__.getAddonInfo('path')
REV = os.path.join( profile, 'list_revision')
icon = xbmc.translatePath( os.path.join( home, 'icon.png' ) )
nexticon = xbmc.translatePath( os.path.join( home, 'nextpage.png' ) )
fanart = xbmc.translatePath( os.path.join( home, 'fanart.jpg' ) )
scriptname = addon.getAddonInfo('name')
quality_index = int(addon.getSetting('quality'))
quality_settings = ["ask", "240p", "360p", "480p", "720p", "1080p"]

MODE_LIST_SHOWS = 1
MODE_LIST_SEASON = 2
MODE_LIST_EPISODES = 3
MODE_VIDEOLINK = 10
MODE_RESOLVE_VIDEOLINK = 11
MODE_LIST_NEXT_EPISODES = 12

def replaceWords(text, word_dic):
    rc = re.compile('|'.join(map(re.escape, word_dic)))
    def translate(match):
        return word_dic[match.group(0)]
    return rc.sub(translate, text)

WORD_DIC = {
'\u00e1': 'á',
'\u00e9': 'é',
'\u00ed': 'í',
'\u00fd': 'ý',
'\u00f3': 'ó',
'\u00fa': 'ú',
'\u016f': 'ů',
'\u011b': 'ě',
'\u0161': 'š',
'\u0165': 'ť',
'\u010d': 'č',
'\u0159': 'ř',
'\u017e': 'ž',
'\u010f': 'ď',
'\u0148': 'ň',
'\u00C0': 'Á',
'\u00c9': 'É',
'\u00cd': 'Í',
'\u00d3': 'Ó',
'\u00da': 'Ú',
'\u016e': 'Ů',
'\u0115': 'Ě',
'\u0160': 'Š',
'\u010c': 'Č',
'\u0158': 'Ř',
'\u0164': 'Ť',
'\u017d': 'Ž',
'\u010e': 'Ď',
'\u0147': 'Ň',
'\\xc3\\xa1': 'á',
'\\xc4\\x97': 'é',
'\\xc3\\xad': 'í',
'\\xc3\\xbd': 'ý',
'\\xc5\\xaf': 'ů',
'\\xc4\\x9b': 'ě',
'\\xc5\\xa1': 'š',
'\\xc5\\xa4': 'ť',
'\\xc4\\x8d': 'č',
'\\xc5\\x99': 'ř',
'\\xc5\\xbe': 'ž',
'\\xc4\\x8f': 'ď',
'\\xc5\\x88': 'ň',
'\\xc5\\xae': 'Ů',
'\\xc4\\x94': 'Ě',
'\\xc5\\xa0': 'Š',
'\\xc4\\x8c': 'Č',
'\\xc5\\x98': 'Ř',
'\\xc5\\xa4': 'Ť',
'\\xc5\\xbd': 'Ž',
'\\xc4\\x8e': 'Ď',
'\\xc5\\x87': 'Ň',
}

def getLS(strid):
    return addon.getLocalizedString(strid)

def notify(msg, timeout = 7000):
    xbmc.executebuiltin('Notification(%s, %s, %d, %s)'%(scriptname, msg.encode('utf-8'), timeout, addon.getAddonInfo('icon')))
    log(msg, xbmc.LOGINFO)

def log(msg, level=xbmc.LOGDEBUG):
    if type(msg).__name__=='unicode':
        msg = msg.encode('utf-8')
    xbmc.log("[%s] %s"%(scriptname,msg.__str__()), level)

def logDbg(msg):
    log(msg,level=xbmc.LOGDEBUG)

def logErr(msg):
    log(msg,level=xbmc.LOGERROR)

def makeImageUrl(rawurl):
    return 'http:'+rawurl.replace('{width}/{height}','360/360')

def getJsonDataFromUrl(url):
    req = urllib2.Request(url)
    req.add_header('User-Agent', _UserAgent_)
    req.add_header('Api-Password', md5('fb5f58a820353bd7095de526253c14fd'+url.split(__baseurl__)[1]+str(int(round(int(time())/3600.0/24.0)))).hexdigest())
    response = urllib2.urlopen(req)
    httpdata = response.read()
    response.close()
    httpdata = replaceWords(httpdata, WORD_DIC)
    return json.loads(httpdata)

def listContent():
    addDir(u'Nejnovější videa',__baseurl__ + '/timeline/latest',MODE_LIST_EPISODES,icon)
    addDir(u'Všechny pořady',__baseurl__ + '/catalogue',MODE_LIST_SHOWS,icon)
    addDir(u'Pohádky',__baseurl__ + '/catalogue?channels=3',MODE_LIST_SHOWS,icon)

def listShows(url):
    data = getJsonDataFromUrl(url)
    for item in data[u'_embedded'][u'stream:show']:
        if u'stream:backward' in item[u'_links']:
            link = __baseurl__+item[u'_links'][u'stream:backward'][u'href']
        else:
            link = __baseurl__+item[u'_links'][u'self'][u'href']
        image = makeImageUrl(item[u'image'])
        name = item[u'name']
        addDir(name,link,MODE_LIST_SEASON,image)

    if 'next' in data[u'_links'].keys():
        listShows(__baseurl__ + data[u'_links'][u'next'][u'href'])
    xbmcplugin.addSortMethod( handle=addonHandle, sortMethod=xbmcplugin.SORT_METHOD_LABEL)

def listSeason(url):
    data = getJsonDataFromUrl(url)
    seasons = data[u'_embedded'][u'stream:season']
    if type(seasons) is dict:
        for item in seasons[u'_embedded'][u'stream:episode']:
            link = __baseurl__+item[u'_links'][u'self'][u'href']
            image = makeImageUrl(item[u'image'])
            name = item[u'name']
            listEpisode(name,link,image)
    elif type(seasons) is list:
        for season in seasons:
            try:
                for episode in season[u'_embedded'][u'stream:episode']:
                    link = __baseurl__+episode[u'_links'][u'self'][u'href']
                    image = makeImageUrl(episode[u'image'])
                    name = season[u'name'] +' | '+ episode[u'name']
                    listEpisode(name,link,image)
            except:
                continue
    try:
        link = __baseurl__+data[u'_links'][u'next'][u'href']
        addDir(u'[B][COLOR blue]'+getLS(30004)+u' >>[/COLOR][/B]',link,MODE_LIST_SEASON,nexticon)
    except:
        logDbg('Další epizody nenalezeny')

def listEpisodes(url):
    data = getJsonDataFromUrl(url)
    islatest='/timeline/latest' in url
    for item in data[u'_embedded'][u'stream:episode']:
        link = __baseurl__+item[u'_links'][u'self'][u'href']
        image = makeImageUrl(item[u'image'])
        name = item[u'_embedded'][u'stream:show'][u'name'] + ' | ' + item[u'name']
        listEpisode(name,link,image,islatest)
    try:
        link = __baseurl__+data[u'_links'][u'next'][u'href']
        addDir(u'[B][COLOR blue]'+getLS(30004)+u' >>[/COLOR][/B]',link,MODE_LIST_EPISODES,nexticon)
    except:
        logDbg('Další epizody nenalezeny')

def listEpisode(name, link, image, islatest=False):
    if quality_index == 0:
        addDir(name,link,MODE_VIDEOLINK,image)
    else:
        addUnresolvedLink(name,link,image,islatest)

def listNextEpisodes(url):
    data = getJsonDataFromUrl(url)
    try:
        link = __baseurl__+data[u'_embedded'][u'stream:show'][u'_links'][u'self'][u'href']
        listSeason(link)
    except:
        logDbg('Další epizody nenalezeny')

def videoLink(url,name):
    data = getJsonDataFromUrl(url)
    name = data[u'name']
    thumb = makeImageUrl(data[u'image'])
    popis = data[u'detail']
    logDbg(url)
    for item in data[u'video_qualities']:
        try:
            for fmt in item[u'formats']:
                if fmt[u'type'] == 'video/mp4':
                    stream_url = fmt[u'source']
                    quality = fmt[u'quality']
                    addLink(quality+' '+name,stream_url,thumb,popis)
        except:
            continue
    try:
        link = __baseurl__+data[u'_embedded'][u'stream:show'][u'_links'][u'self'][u'href']
        image = makeImageUrl(data[u'_embedded'][u'stream:show'][u'image'])
        name = data[u'_embedded'][u'stream:show'][u'name']
        addDir(u'[B][COLOR blue]'+getLS(30004)+u' >>[/COLOR][/B]',link,MODE_LIST_SEASON,image)
    except:
        logDbg('Další epizody nenalezeny')

def resolveVideoLink(url,name):
    data = getJsonDataFromUrl(url)
    name = data[u'name']
    thumb = makeImageUrl(data[u'image'])
    popis = data[u'detail']
    qa = []
    logDbg("Resolving video URL for quality " + quality_settings[quality_index] + " from: " + url)
    for item in data[u'video_qualities']:
        try:
            for fmt in item[u'formats']:
                if fmt[u'type'] == 'video/mp4':
                    stream_url = fmt[u'source']
                    quality = fmt[u'quality']
                    qa.append((quality, stream_url))
        except:
            continue
    if len(qa) == 0:
        # no video available...
        notify(getLS(30003))
        xbmcplugin.setResolvedUrl(handle=addonHandle, succeeded=False, listitem=xbmcgui.ListItem(label="video", path=""))
        return
    # sort available qualities according desired one
    quality_sorted = quality_settings[quality_index:0:-1]
    quality_sorted += quality_settings[quality_index+1:]
    
    stream_url = ""
    for qf in quality_sorted:
        match_quality = [q for q in qa if q[0] == qf]
        if len(match_quality):
            stream_url = match_quality[0][1]
            break
    
    if stream_url == "":
        logErr("No video stream found!")
        xbmcplugin.setResolvedUrl(handle=addonHandle, succeeded=False, listitem=xbmcgui.ListItem(label="video", path=""))
        return

    logDbg("Resolved URL: "+stream_url)
    if match_quality[0][0] != quality_settings[quality_index]:
            notify(getLS(30002) % (quality_settings[quality_index], match_quality[0][0]))
    
    liz = xbmcgui.ListItem(path=stream_url, iconImage="DefaultVideo.png")
    liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": popis} )
    liz.setProperty('IsPlayable', 'true')
    liz.setProperty( "icon", thumb )
    xbmcplugin.setResolvedUrl(handle=addonHandle, succeeded=True, listitem=liz)

def getParams():
        param=[]
        paramstring=sys.argv[2]
        if len(paramstring)>=2:
                params=sys.argv[2]
                cleanedparams=params.replace('?','')
                if (params[len(params)-1]=='/'):
                        params=params[0:len(params)-2]
                pairsofparams=cleanedparams.split('&')
                param={}
                for i in range(len(pairsofparams)):
                        splitparams={}
                        splitparams=pairsofparams[i].split('=')
                        if (len(splitparams))==2:
                                param[splitparams[0]]=splitparams[1]
        return param

def addLink(name,url,iconimage,popis):
        logDbg("addLink(): '"+name+"' url='"+url+ "' img='"+iconimage+"' popis='"+popis+"'")
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": popis} )
        liz.setProperty( "Fanart_Image", fanart )
        ok=xbmcplugin.addDirectoryItem(handle=addonHandle,url=url,listitem=liz)
        return ok

def composePluginUrl(url, mode, name):
    return sys.argv[0]+"?url="+urllib.quote_plus(url.encode('utf-8'))+"&mode="+str(mode)+"&name="+urllib.quote_plus(name.encode('utf-8'))

def addItem(name,url,mode,iconimage,isfolder,islatest=False):
        u=composePluginUrl(url,mode,name)
        ok=True
        liz=xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
        liz.setInfo( type="Video", infoLabels={ "Title": name } )
        liz.setProperty( "Fanart_Image", fanart )
        if not isfolder:
                liz.setProperty("IsPlayable", "true")
                if islatest:
                    next_url = composePluginUrl(url,MODE_LIST_NEXT_EPISODES,name)
                    menuitems = []
                    menuitems.append(( getLS(30004).encode('utf-8'), 'XBMC.Container.Update('+next_url+')' ))
                    liz.addContextMenuItems(menuitems)
        ok=xbmcplugin.addDirectoryItem(handle=addonHandle,url=u,listitem=liz,isFolder=isfolder)
        return ok

def addDir(name,url,mode,iconimage):
        logDbg("addDir(): '"+name+"' url='"+url+"' icon='"+iconimage+"' mode='"+str(mode)+"'")
        return addItem(name,url,mode,iconimage,True)

def addUnresolvedLink(name,url,iconimage,islatest=False):
        mode=MODE_RESOLVE_VIDEOLINK
        logDbg("addUnresolvedLink(): '"+name+"' url='"+url+"' icon='"+iconimage+"' mode='"+str(mode)+"'")
        return addItem(name,url,mode,iconimage,False,islatest)

addonHandle=int(sys.argv[1])
params=getParams()
url=None
name=None
thumb=None
mode=None

try:
        url=urllib.unquote_plus(params["url"])
except:
        pass
try:
        name=urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode=int(params["mode"])
except:
        pass

logDbg("Mode: "+str(mode))
logDbg("URL: "+str(url))
logDbg("Name: "+str(name))

if mode==None or url==None or len(url)<1:
        STATS("OBSAH", "Function")
        listContent()
       
elif mode==MODE_LIST_SHOWS:
        STATS("LIST_SHOWS", "Function")
        listShows(url)

elif mode==MODE_LIST_SEASON:
        STATS("LIST_SEASON", "Function")
        listSeason(url)

elif mode==MODE_LIST_EPISODES:
        STATS("LIST_EPISODES", "Function")
        listEpisodes(url)

elif mode==MODE_VIDEOLINK:
        STATS(name, "Item")
        videoLink(url,name)

elif mode==MODE_RESOLVE_VIDEOLINK:
        resolveVideoLink(url,name)
        STATS(name, "Item")
        sys.exit(0)

elif mode==MODE_LIST_NEXT_EPISODES:
        STATS("LIST_NEXT_EPISODES", "Function")
        listNextEpisodes(url)
        
xbmcplugin.endOfDirectory(int(sys.argv[1]))
