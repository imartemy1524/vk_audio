from .audio_enum_index import AudioEnumIndex
import vk_api,io,random,string,sys
import json as json_parser
from lxml import html
class Audio(object):
    def __init__(self,vkaudio,owner_id,playlistsReorderHash=None,audiosReorderHash=None,newPlaylistHash=None,listenedHash=None,playlistCoverUploadOptions=None,audios_loaded=False):
        from .audio_list import AudioList
        self.owner_id=owner_id;
        self._audios:AudioList=AudioList(vkaudio);
        self.Playlists=[]
        self._newPlaylistHash=newPlaylistHash;
        self._audiosReorderHash=audiosReorderHash;
        self._playlistsReorderHash=playlistsReorderHash;
        self._listenedHash=listenedHash
        self._playlistCoverUploadOptions = playlistCoverUploadOptions
        self.vk_audio = vkaudio;
        self._audios_loaded=audios_loaded;
        return    
    def load_audios_from_html(self,html_code,vk_audio=None,reorder_hash=None):
        if(vk_audio is None):vk_audio=self.vk_audio
        obj = html.fromstring(html_code)        
        json_data = "[{}]".format(",".join(i.attrib['data-audio'] for i in obj.find_class("audio_item") if 'data-audio' in i.attrib))#генерируем json из html
        return Audio.load_audios_from_js(self,json_data,vk_audio,reorder_hash)
    def load_audios_from_js(self,json,vk_audio=None,reorder_hash=None):
        if(vk_audio is None):vk_audio=self.vk_audio
        if(reorder_hash is None and isinstance(self,Audio)):reorder_hash=self._audiosReorderHash
        if(isinstance(json,str)):json = json_parser.loads(json)
        q=self if(not isinstance(self,Audio)) else self._audios;
        from .audio_obj import AudioObj
        audios = [];
        for i in json:
            a=AudioObj.parse(i,vk_audio,audios,reorder_hash)
            q.append(a)
            audios.append(a);
            if(len(audios)>=vk_audio.c_u):audios=[]
        return q
    def load_playlists_from_js(self,json):
        from .playlist import Playlist
        self.Playlists+=[Playlist.from_js(j,self.vk_audio,self._playlistsReorderHash) for j in json if isinstance(j['id'],int)]
        return self;
    def load_playlists_from_html(self,html_code):
        from .playlist import Playlist
        if(isinstance(html_code,str)):html_code = html.fromstring(html_code);
        for i in html_code.find_class("audio_pl_item2"):
            self.Playlists.append(Playlist.from_html(i,self.vk_audio,None));
        return self.Playlists
    @property
    def Audios(self):
        if(not self._audios_loaded):self.load_audios();
        return self._audios;
    @property 
    def Count(self):
        return len(self.Audios);
    def load_audios(self,offset=None,playlist_id=-1,access_hash='',owner_id=None):    
        from .audio_list import AudioList

        from .vk_audio import VkAudio
        vk = self.vk_audio if isinstance(self,Audio) else self;
        if(offset is None):offset = len(self._audios);
        if(owner_id is None):owner_id = self.owner_id;
        else:offset = 30;
        from .audio_obj import AudioObj
        audios_json = VkAudio._action(vk,data={
            'access_hash': access_hash,
            'act': 'load_section',
            'al': 1,
            'claim': 0,
            'is_loading_all': 1,#
            'is_preload': 0,#
            'offset': offset,
            'owner_id': owner_id,
            'playlist_id': playlist_id,
            'track_type': 'default',
            'type': 'playlist'});
        if(not audios_json['payload'][1][0]):raise PermissionError("Undefined error")
        audios = audios_json['payload'][1][0]['list']
        return Audio.load_audios_from_js(self if isinstance(self,Audio) else AudioList(self._enum_p),audios,vk)
class ArtistAudio(Audio):
    def __init__(self,vk_audio,audios_html,albums_html,artist_nick,*args,**arrgs):
        super().__init__(vk_audio,-1)
        self.nick = artist_nick
        self._parse_albums_from_html(albums_html
            )._parse_audios_from_html(audios_html)
        next_audio_data = audios_html.find_class("CatalogBlock__content")[0]
        self._data_id = next_audio_data.attrib['data-id']
        self._data_next = 'data-next' in next_audio_data.attrib and next_audio_data.attrib['data-next']
        self.owner_id = self._audios[0].owner_id;
    def _parse_albums_from_html(self,albums_html):
        from .playlist import Playlist
        self.Playlists+=[Playlist.from_html(i,self.vk_audio,self._audiosReorderHash) for i in albums_html.find_class("audio_pl_item2")]
        return self;
    def _parse_audios_from_html(self,audios_html):
        self.load_audios_from_js(json_parser.loads(i.attrib['data-audio']) for i in audios_html.find_class("audio_row"))
        return self
    def load_audios(self):
        from .audio_obj import AudioObj
        while(self._data_next):
            resp = self.vk_audio._action(data={"act": "load_catalog_section",
                "al": 1,
                "section_id": self._data_id,
                "start_from": self._data_next
                });
            if(resp['payload'][0] and isinstance(resp['payload'][0][1][0],str)):
                h = html.fromstring(resp['payload'][0][1][0])
                cls = h.find_class("CatalogBlock__itemsContainer")[0]
                self._data_next = 'data-next' in cls.attrib and cls.attrib['data-next']
                self.load_audios_from_js(resp['payload'][0][1][1]['playlist']['list'])
            elif(resp['payload'][1][0] and resp['payload'][1][0][0] and isinstance(resp['payload'][1][0][0],str)):
                h = html.fromstring(resp['payload'][1][0][0])
                cls = h.find_class("CatalogBlock__itemsContainer")[0]
                self._data_next = 'data-next' in cls.attrib and cls.attrib['data-next']
                self.load_audios_from_js(resp['payload'][1][1]['playlist']['list'])
            else:raise ValueError("Undefined json struct. It changed.")
        self._audios_loaded=True;
class MyAudio(Audio):
    class FILE_OPEN(vk_api.upload.FilesOpener):
        def __init__(self,content_types,*arg,**args):
            if(not isinstance(content_types,(list,tuple))):
                self.content_types = (content_types,)
            return super().__init__(*arg,**args);
        def open_files(self):
            return [(item[0],item[1]+(ct,)) for item,ct in zip(super().open_files(),self.content_types)]
            #return [item for item,ct in zip(super().open_files(),self.content_types)]
    def upload_playlist_cover(self,photo,content_type='image/jpeg'):
        """
        Загрузить обложку для плейлиста.
        :param photo: путь к изображению или file-like объект
        :type photo: str or io.BytesIO or io.BufferedReader
        :type content_type: str
        """
        from .vk_audio import VkAudio

        with MyAudio.FILE_OPEN(content_type, photo, key_format='photo') as photo_:
            opt = self._playlistCoverUploadOptions
            if(not opt or 'url' not in opt or not opt['url'] or 'vars' not in opt or not opt['vars']):raise PermissionError("You do not have permission to upload photo.")
            url = opt['url']
            if('ajax' not in opt['vars']):opt['vars']['ajx']=1;
            self.vk_audio.vk.http.options(url,params=opt['vars'])
            resp = self.vk_audio._action(url,params=opt['vars'],files=photo_)
            if(not resp):raise ValueError("undefined error")
            if('error' in resp and resp['error']):raise ValueError(resp['error'])
            return resp;
    def create_playlist(self,title="название",description="описание",audios=[],photo=None):
        """Создать новый плейлист. 
        :param title: Название 
        :type title: str or NoneType
        :param description:Описание
        :type description: str or NoneType
        :param audios: Аудиозаписи, добавляемые в этот плейлист.
        :type audios: list
        :param photo: Обложка плейлиста ( Результат функции upload_playlist_cover )
        :type photo: list or NoneType
        """
        if(not self._newPlaylistHash):raise PermissionError("You do not have access to create playlists")
        from .audio_obj import AudioObj
        from .playlist import Playlist
        a = ",".join(i.hash if isinstance(i,AudioObj) else str(i) for i in audios)
        resp = self.vk_audio._action("https://vk.com/al_audio.php?act=save_playlist",{
            "Audios": a,
            "al": 1,
            'cover': 0 if photo is None else json_parser.dumps(photo),
            'description': description,
            'hash': self._newPlaylistHash,
            'owner_id': self.owner_id,
            'playlist_id': 0,
            'title': title
        });
        del resp['success'];
        if(resp['payload'][1][0]):
            p = Playlist.from_js(resp['payload'][1][0],self.vk_audio,self._playlistsReorderHash)
            self.Playlists.append(p)
            return p;
        return False;
                    
class AudioSearch(Audio):
    def __init__(self, vkaudio,html):
        self._html = html
        self._artists_info = None
        return super().__init__(vkaudio, vkaudio.uid)
    @property
    def artists_info(self):
        if(not self._artists_info):
            from .playlist import Playlist
            ans = []
            parser = html.fromstring(self._html);
            for i in parser.find_class("title_link"):
                if('/artist/' not in i.attrib['href']):continue
                photo_item = i.getparent().getparent().getparent().find_class("audio_block_small_item__img");
                data = {"name":i.text,"href":i.attrib['href'].split("?")[0]}
                if(photo_item and "style" in photo_item[0].attrib):
                    data['photo']=Playlist.grab_image_from_el(photo_item[0])
                ans.append(data)
            self._artists_info=ans
        return self._artists_info;
    def artist_music(self,index):
        artist = self.artists_info[index];
        return self.vk_audio.load_artist(artist['nick'])
    def zip_artist(self,index:int=0):
        """Метод, который возвращает хеш артиста. Пототм по этому хешу можно получить его музыку - методом vk_audio.load_artist с параметром artist_hash"""
        if("/artist/" in self.artists_info[index]['href']):
            return 'a'+ self.artists_info[index]['href'].lstrip("https://vk.com/").replace("artist",'').lstrip("/")
        return 's'+self.artists_info[index]['name']