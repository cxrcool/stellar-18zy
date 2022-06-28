import time
import bs4
import requests
import StellarPlayer
import re
import urllib.parse
import urllib.request
import math
import json
import urllib3
import os
import sys
import threading

class yszfplugin(StellarPlayer.IStellarPlayerPlugin):
    def __init__(self,player:StellarPlayer.IStellarPlayer):
        super().__init__(player)
        urllib3.disable_warnings()
        self.medias = []
        self.allmovidesdata = {}
        self.mediaclass = []
        self.pageindex = 0
        self.pagenumbers = 0
        self.apiurl = ''
        self.apitype = ''
        self.cur_page = ''
        self.max_page = ''
        self.nextpg = ''
        self.previouspg = ''
        self.firstpg = ''
        self.lastpg = ''
        self.pg = ''
        self.wd = ''
        self.ids = ''
        self.tid = ''
        self.spy = []
        self.searhStop = False
        self.li = []
        self.allSearchMedias = []
    
    def start(self):
        super().start()
        path = os.path.split(os.path.realpath(__file__))[0]
        for root, dirs, files in os.walk(path): 
            for file in files:
                filenames = os.path.splitext(file)
                if os.path.splitext(file)[1] == '.json':  # 想要保存的文件格式
                    self.resolveJson(path + os.path.sep + file)
        if len(self.spy) > 0:
            cat = self.spy[0]
            self.apiurl = cat['api']
            self.apitype = cat['datatype']
            self.getMediaType(False)
            self.pg = ''
            self.wd = ''
            self.tid = ''
            self.getMediaList(False)
        
        
    def resolveJson(self,file):
        file = open(file, "rb")
        fileJson = json.loads(file.read())
        for item in fileJson:
            self.spy.append(item)
        file.close()
    
    
    def show(self):
        controls = self.makeLayout()
        self.doModal('main',800,700,'',controls)        
    
    def makeLayout(self):
        zywz_layout = [
            {'type':'link','name':'title','@click':'onMainMenuClick'}
        ]
        secmenu_layout = [
            {'type':'link','name':'title','@click':'onSecMenuClick'}
        ]

        mediaclass_layout = [
            {'type':'link','name':'type_name','textColor':'#ff00ff', '@click':'on_class_click'}
        ]
        mediagrid_layout = [
            [
                {
                    'group': [
                        {'type':'image','name':'picture', '@click':'on_grid_click'},
                        {'type':'link','name':'title','textColor':'#ff7f00','fontSize':15,'height':0.15, '@click':'on_grid_click'}
                    ],
                    'dir':'vertical'
                }
            ]
        ]
        controls = [
            {'type':'space','height':5},
            {
                'group':[
                    {'type':'edit','name':'search_edit','label':'搜索','width':0.4},
                    {'type':'button','name':'搜索当前站','@click':'onSearch','width':100},
                    {'type':'button','name':'搜索所有站','@click':'onSearchAll','width':100},
                ],
                'width':1.0,
                'height':30
            },
            {'type':'space','height':10},
            {'type':'grid','name':'zygrid','itemlayout':zywz_layout,'value':self.spy,'itemheight':30,'itemwidth':80,'height':70},
            {'type':'space','height':5},
            {'type':'grid','name':'mediaclassgrid','itemlayout':mediaclass_layout,'value':self.mediaclass,'itemheight':30,'itemwidth':80,'height':80},
            {'type':'space','height':5},
            {'type':'grid','name':'mediagrid','itemlayout':mediagrid_layout,'value':self.medias,'separator':True,'itemheight':240,'itemwidth':150},
            {'group':
                [
                    {'type':'space'},
                    {'group':
                        [
                            {'type':'label','name':'cur_page',':value':'cur_page'},
                            {'type':'link','name':'首页','@click':'onClickFirstPage'},
                            {'type':'link','name':'上一页','@click':'onClickFormerPage'},
                            {'type':'link','name':'下一页','@click':'onClickNextPage'},
                            {'type':'link','name':'末页','@click':'onClickLastPage'},
                            {'type':'label','name':'max_page',':value':'max_page'},
                        ]
                        ,'width':0.7
                    },
                    {'type':'space'}
                ]
                ,'height':30
            },
            {'type':'space','height':5}
        ]
        return controls
    
    def onMainMenuClick(self, page, listControl, item, itemControl):
        self.searhStop = True
        self.allSearchMedias = []
        self.loading()
        self.player.updateControlValue('main','mediaclassgrid',[])
        self.player.updateControlValue('main','mediagrid',[])
        cat = self.spy[item]
        self.apiurl = cat['api']
        self.apitype = cat['datatype']
        self.getMediaType(True)
        self.pg = ''
        self.wd = ''
        self.tid = ''
        self.getMediaList(True)
        self.loading(True)
         
    def getMediaType(self,showerror):
        self.mediaclass = []
        self.player.updateControlValue('main','mediaclassgrid',self.mediaclass)
        url = self.apiurl + '?ac=list'
        try:
            res = requests.get(url,timeout = 5,verify=False)
            if res.status_code == 200:
                if self.apitype == 'json':
                    jsondata = json.loads(res.text, strict = False)
                    if jsondata:
                        self.mediaclass = jsondata['class']
                        self.getPageInfoJson(jsondata)
                else:
                    bs = bs4.BeautifulSoup(res.content.decode('UTF-8','ignore'),'html.parser')
                    selector = bs.select('rss > class >ty')
                    if selector:
                        for item in selector:
                            t_id = int(item.get('id'))
                            t_name = item.string
                            self.mediaclass.append({'type_id':t_id,'type_name':t_name})
                        self.getPageInfoXML(bs)
            else:
                if showerror:
                    self.player and self.player.toast('main','请求失败')
        except:
            if showerror:
                self.player and self.player.toast('main','请求失败')
        self.player.updateControlValue('main','mediaclassgrid',self.mediaclass)
        
    def getMediaList(self,showerror):
        self.medias = []
        self.player.updateControlValue('main','mediagrid',self.medias)
        if self.apiurl == '':
            return
        url = self.apiurl + '?ac=videolist'
        if self.wd != '':
            self.tid = ''
            url = url + '&wd=' +self.wd
        if self.tid != '':
            url = url + self.tid
        if self.pg != '':
            url = url + self.pg
        try:
            res = requests.get(url,timeout = 5,verify=False)
            if res.status_code == 200:
                if self.apitype == 'json':
                    jsondata = json.loads(res.text, strict = False)
                    if jsondata:
                        jsonlist = jsondata['list']
                        for item in jsonlist:
                            self.medias.append({'api':self.apiurl,'ids':item['vod_id'],'title':item['vod_name'],'picture':item['vod_pic'],'apitype':self.apitype})
                        self.getPageInfoJson(jsondata)
                else:
                    bs = bs4.BeautifulSoup(res.content.decode('UTF-8','ignore'),'html.parser')
                    selector = bs.select('rss > list > video')
                    if selector:
                        for item in selector:
                            nameinfo = item.select('name')
                            picinfo = item.select('pic')
                            idsinfo = item.select('id')
                            if nameinfo and picinfo and idsinfo:
                                name = nameinfo[0].string
                                pic = picinfo[0].string
                                ids = int(idsinfo[0].string)
                                self.medias.append({'api':self.apiurl,'ids':ids,'title':name,'picture':pic,'apitype':self.apitype})
                    self.getPageInfoXML(bs)
            else:
                if showerror:
                    self.player and self.player.toast('main','请求失败')
        except:
            if showerror:
                self.player and self.player.toast('main','请求失败')
        self.player.updateControlValue('main','mediagrid',self.medias)
    
    def on_class_click(self, page, listControl, item, itemControl):
        self.searhStop = True
        self.allSearchMedias = []
        if self.apiurl == '':
            return
        self.loading()
        typeid = self.mediaclass[item]['type_id']
        self.wd = ''
        self.pg = ''
        self.tid = '&t=' + str(typeid)
        self.getMediaList(True)
        self.loading(True)
    
    def getPageInfoJson(self,jsondata):
        self.pageindex = jsondata['page']
        self.pagenumbers = jsondata['pagecount']
        self.nextpg = '&pg=' + str(int(self.pageindex) + 1)
        if self.pageindex == 1:
            self.previouspg = '&pg=1'
        else:
            self.previouspg = '&pg=' + str(int(self.pageindex) - 1)
        self.firstpg = '&pg=1'
        self.lastpg = '&pg=' + str(self.pagenumbers)
        self.cur_page = '第' + str(self.pageindex) + '页'
        self.max_page = '共' + str(self.pagenumbers) + '页'    
    def getPageInfoXML(self,bs):
        self.nextpg = ''
        self.previouspg = ''
        self.firstpg = ''
        self.lastpg = ''
        selector = bs.select('rss > list')
        self.pagenumbers = 0
        self.pageindex = 0
        if selector:
            self.pageindex = int(selector[0].get('page'))
            self.pagenumbers = int(selector[0].get('pagecount'))
            if self.pageindex < self.pagenumbers:
                self.nextpg = '&pg=' + str(int(self.pageindex) + 1)
            else:
                self.nextpg = '&pg=' + str(self.pagenumbers)
            if self.pageindex == 1:
                self.previouspg = '&pg=1'
            else:
                self.previouspg = '&pg=' + str(int(self.pageindex) - 1)
            self.firstpg = '&pg=1'
            self.lastpg = '&pg=' + str(self.pagenumbers)
        self.cur_page = '第' + str(self.pageindex) + '页'
        self.max_page = '共' + str(self.pagenumbers) + '页'
    
    def onSearch(self, *args):
        self.pg = ''
        search_word = self.player.getControlValue('main','search_edit').strip()
        if search_word == '':
            self.player.toast("main","搜索条件不能为空")
            return   
        if self.apiurl == '':
            self.player.toast("main","请先选择资源站")
            return
        for cat in self.spy:
            if self.apiurl == cat['api']:
                if cat['search'] == False:
                    self.player.toast('main','该资源站不支持搜索')
                    return
        self.loading()
        self.wd = search_word
        self.getMediaList(True)
        self.loading(True)
    
    def onSearchAll(self,*args):
        search_word = self.player.getControlValue('main','search_edit').strip()
        if search_word == '':
            self.player.toast("main","搜索条件不能为空")
            return
        self.searhStop = True
        for t in self.li:
            t.join()
        self.li = []
        self.medias = []
        self.allSearchMedias = []
        self.player.updateControlValue('main','mediagrid',self.medias)
        self.searhStop = False
        for cat in self.spy:
            if cat['search']:
                searchurl = cat['api']
                apitype = cat['datatype']
                self.newSearchNode(searchurl,search_word,apitype,1)
        return

    def newSearchNode(self,searchurl,wd,apitype,pageindex):
        t = threading.Thread(target=self._SearchNoneThread,args=(searchurl,wd,apitype,pageindex))
        self.li.append(t)
        t.start()
        
    def _SearchNoneThread(self,searchurl,wd,apitype,pageindex):
        zyzapiurl = searchurl
        zyzapitype = apitype
        if self.searhStop:
            return
        url = zyzapiurl + '?ac=videolist&wd=' + wd + '&pg=' + str(pageindex)
        print(url)
        try:
            res = requests.get(url,timeout = 5,verify=False)
            if res.status_code == 200:
                if zyzapitype == "json":
                    jsondata = json.loads(res.text, strict = False)
                    if jsondata:
                        pageindex = int(jsondata['page'])
                        pagenumbers = int(jsondata['pagecount'])
                        if pageindex < pagenumbers and pagenumbers < 5:
                            self.newSearchNode(searchurl, wd, apitype,pageindex + 1)
                        if pagenumbers >= 5:
                            return
                        jsonlist = jsondata['list']
                        for item in jsonlist:
                            if self.searhStop == False:
                                self.allSearchMedias.append({'ids':item['vod_id'],'title':item['vod_name'],'picture':item['vod_pic'],'api':zyzapiurl,'apitype':zyzapitype})
                else:
                    bs = bs4.BeautifulSoup(res.content.decode('UTF-8','ignore'),'html.parser')
                    selector = bs.select('rss > list')
                    pagenumbers = 0
                    pageindex = 0
                    if selector:
                        pageindex = int(selector[0].get('page'))
                        pagenumbers = int(selector[0].get('pagecount'))
                    if pageindex < pagenumbers and pagenumbers < 5:
                        self.newSearchNode(searchurl, wd, apitype,pageindex + 1)
                    if pagenumbers >= 5:
                        return
                    selector = bs.select('rss > list > video')
                    if selector:
                        for item in selector:
                            nameinfo = item.select('name')
                            picinfo = item.select('pic')
                            idsinfo = item.select('id')
                            if nameinfo and picinfo and idsinfo:
                                name = nameinfo[0].string
                                pic = picinfo[0].string
                                ids = int(idsinfo[0].string)
                                if self.searhStop == False:
                                    self.allSearchMedias.append({'ids':ids,'title':name,'picture':pic,'api':zyzapiurl,'apitype':zyzapitype})
            else:
                return
        except:
            return
        if self.searhStop == False:
            if len(self.medias) < 20:
                num = 20
                if num > len(self.allSearchMedias):
                    num = len(self.allSearchMedias)
                for i in range(len(self.medias),num):
                    self.pageindex = 1
                    self.medias.append(self.allSearchMedias[i]);
                    self.cur_page = '第1页'
                    self.player.updateControlValue('main','mediagrid',self.medias)
            self.pagenumbers = len(self.allSearchMedias) // 20
            if self.pagenumbers * 20 < len(self.allSearchMedias):
                self.pagenumbers = self.pagenumbers + 1
            self.max_page = '共' + str(self.pagenumbers) + '页'
            self.player.updateControlValue('main','mediagrid',self.medias)
        
    def on_grid_click(self, page, listControl, item, itemControl):
        videoid = self.medias[item]['ids']
        apiurl = self.medias[item]['api']
        apitype = self.medias[item]['apitype']
        url = apiurl + '?ac=videolist&ids=' + str(videoid)
        self.onGetMediaPage(url,apitype)
        
    def onGetMediaPage(self,url,apitype):
        try:
            res = requests.get(url,timeout = 5,verify=False)
            if res.status_code == 200:
                if apitype == 'json':
                    jsondata = json.loads(res.text, strict = False)
                    if jsondata:
                        medialist = jsondata['list']
                        if len(medialist) > 0:
                            info = medialist[0]
                            playfrom = info["vod_play_from"]
                            playnote = '$$$'
                            playfromlist = playfrom.split(playnote)
                            playurl = info["vod_play_url"]
                            playurllist = playurl.split(playnote)
                            sourcelen = len(playfromlist)
                            sourcelist = []
                            for i in range(sourcelen):
                                if playfromlist[i].find('m3u8') >= 0:
                                    urllist = [] 
                                    urlstr = playurllist[i]
                                    jjlist = urlstr.split('#')
                                    for jj in jjlist:
                                        jjinfo = jj.split('$')
                                        urllist.append({'title':jjinfo[0],'url':jjinfo[1]})
                                    sourcelist.append({'flag':playfromlist[i],'medias':urllist})
                            mediainfo = {'medianame':info['vod_name'],'pic':info['vod_pic'],'actor':'演员:' + info['vod_actor'].strip(),'content':'简介:' + info['vod_content'].strip(),'source':sourcelist}
                            self.createMediaFrame(mediainfo)
                            return
                else:
                    bs = bs4.BeautifulSoup(res.content.decode('UTF-8','ignore'),'html.parser')
                    selector = bs.select('rss > list > video')
                    if len(selector) > 0:
                        info = selector[0]
                        nameinfo = info.select('name')[0]
                        name = nameinfo.text
                        picinfo = info.select('pic')[0]
                        pic = picinfo.text
                        actorinfo = info.select('actor')[0]
                        actor = '演员:' + actorinfo.text.strip()
                        desinfo = info.select('des')[0]
                        des = '简介:' + desinfo.text.strip()
                        dds = info.select('dl > dd')
                        sourcelist = []
                        for dd in dds:
                            ddflag = dd.get('flag')
                            ddinfo = dd.text
                            m3u8list = []
                            if ddflag.find('m3u8') >= 0:
                                urllist = ddinfo.split('#')
                                n = 1
                                for source in urllist:
                                    urlinfo = source.split('$')
                                    if len(urlinfo) == 1:
                                        m3u8list.append({'title':'第' + str(n) + '集','url':ddinfo})
                                    else:
                                        m3u8list.append({'title':urlinfo[0],'url':urlinfo[1]})
                                    n = n + 1
                                sourcelist.append({'flag':ddflag,'medias':m3u8list})
                        mediainfo = {'medianame':name,'pic':pic,'actor':actor,'content':des,'source':sourcelist}
                        self.createMediaFrame(mediainfo)
                        return
        except:
            self.player and self.player.toast('main','请求失败')
        self.player and self.player.toast('main','无法获取视频信息')
        return
        
    def createMediaFrame(self,mediainfo):
        if len(mediainfo['source']) == 0:
            self.player.toast('main','该视频没有可播放的视频源')
            return
        actmovies = []
        if len(mediainfo['source']) > 0:
            actmovies = mediainfo['source'][0]['medias']
        medianame = mediainfo['medianame']
        self.allmovidesdata[medianame] = {'allmovies':mediainfo['source'],'actmovies':actmovies}
        xl_list_layout = {'type':'link','name':'flag','textColor':'#ff0000','width':0.6,'@click':'on_xl_click'}
        movie_list_layout = {'type':'link','name':'title','@click':'on_movieurl_click'}
        controls = [
            {'type':'space','height':5},
            {'group':[
                    {'type':'image','name':'mediapicture', 'value':mediainfo['pic'],'width':0.25},
                    {'group':[
                            {'type':'label','name':'medianame','textColor':'#ff7f00','fontSize':15,'value':mediainfo['medianame'],'height':40},
                            {'type':'label','name':'actor','textColor':'#555500','value':mediainfo['actor'],'height':0.3},
                            {'type':'label','name':'info','textColor':'#005555','value':mediainfo['content'],'height':0.7}
                        ],
                        'dir':'vertical',
                        'width':0.75
                    }
                ],
                'width':1.0,
                'height':250
            },
            {'group':
                {'type':'grid','name':'xllist','itemlayout':xl_list_layout,'value':mediainfo['source'],'separator':True,'itemheight':30,'itemwidth':120},
                'height':40
            },
            {'type':'space','height':5},
            {'group':
                {'type':'grid','name':'movielist','itemlayout':movie_list_layout,'value':actmovies,'separator':True,'itemheight':30,'itemwidth':120},
                'height':200
            }
        ]
        result,control = self.doModal(mediainfo['medianame'],750,500,'',controls)

    def updateSearch(self,index):
        print(index)
        if index < 1:
            return
        self.medias = []
        self.player.updateControlValue('main','mediagrid',self.medias)
        self.pageindex = index
        self.cur_page = '第' + str(self.pageindex) + '页'
        if len(self.allSearchMedias) >= 20 * (index - 1):
            idxend = 20 * index
            idxstart = idxend - 20
            if idxend > len(self.allSearchMedias):
                idxend = len(self.allSearchMedias)
            for i in range(idxstart,idxend):
                self.medias.append(self.allSearchMedias[i])
            self.player.updateControlValue('main','mediagrid',self.medias)
        
    def onClickFirstPage(self, *args):
        if len(self.allSearchMedias) == 0:
            if self.firstpg == '':
                return
            self.pg = self.firstpg
            self.loading()
            self.getMediaList(True)
            self.loading(True)
        else:
            self.updateSearch(1)
        
    def onClickFormerPage(self, *args):
        if len(self.allSearchMedias) == 0:
            if self.previouspg == '':
                return
            self.pg = self.previouspg
            self.loading()
            self.getMediaList(True)
            self.loading(True)
        else:
            self.updateSearch(self.pageindex - 1)
    
    def onClickNextPage(self, *args):
        if len(self.allSearchMedias) == 0:
            if self.nextpg == '':
                return
            self.pg = self.nextpg
            self.loading()
            self.getMediaList(True)
            self.loading(True)
        else:
            self.updateSearch(self.pageindex + 1)
        
    def onClickLastPage(self, *args):
        if len(self.allSearchMedias) == 0:
            if self.lastpg == '':
                return
            self.pg = self.lastpg
            self.loading()
            self.getMediaList(True)
            self.loading(True)
        else:
            self.updateSearch(self.pagenumbers)
    
    def on_xl_click(self, page, listControl, item, itemControl):
        self.player.updateControlValue(page,'movielist',[])
        if len(self.allmovidesdata[page]['allmovies']) > item:
            self.allmovidesdata[page]['actmovies'] = self.allmovidesdata[page]['allmovies'][item]['medias']
        self.player.updateControlValue(page,'movielist',self.allmovidesdata[page]['actmovies'])
                
    def on_movieurl_click(self, page, listControl, item, itemControl):
        if len(self.allmovidesdata[page]['actmovies']) > item:
            playurl = self.allmovidesdata[page]['actmovies'][item]['url']
            playname = page + ' ' + self.allmovidesdata[page]['actmovies'][item]['title']
            try:
                self.player.play(playurl, caption=playname)
            except:
                self.player.play(playurl)  
            
    def playMovieUrl(self,playpageurl):
        return
        
    def loading(self, stopLoading = False):
        if hasattr(self.player,'loadingAnimation'):
            self.player.loadingAnimation('main', stop=stopLoading)
        
def newPlugin(player:StellarPlayer.IStellarPlayer,*arg):
    plugin = yszfplugin(player)
    return plugin

def destroyPlugin(plugin:StellarPlayer.IStellarPlayerPlugin):
    plugin.stop()
