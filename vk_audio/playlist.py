from lxml import html
from .audio import Audio;
import re
class Playlist(object):
    def __init__(self,r_h,vk_audio):
        self._audios=None
        self._reorder_hash=r_h
        self._vk_audio = vk_audio
    @staticmethod
    def from_js(js:dict,vk_audio,reorder_hash=None):
        p = Playlist(reorder_hash,vk_audio);
        p.owner_id=p.__parse(js,'owner_id','ownerId')
        p.id=js['id'];
        if(not isinstance(p.id,int)):raise ValueError("id is invalid")
        p.raw_id=p.__parse(js,'raw_id','rawId')
        p.title=js['title']
        p.description=js['description']

        author_line = p.__parse(js,'author_line','authorLine');
        auth=html.fromstring(author_line).find_class("audio_pl_snippet__artist_link") if author_line else ''
        
        p.author_info =[{"name":i.text,"href":i.attrib['href']} for i in auth] if auth else []

        p.listens = js['listens']
        p.has_image=bool(js['thumb']) if 'thumb' in js else False;
        p.audios_count=p.__parse(js,'size','totalCount')
        if(p.has_image):
            p.images=[js["thumb"]]
        else:
            p.images = []
            g_c = p.__parse(js,'grid_covers','gridCovers')
            if(g_c):
                ch =html.fromstring(g_c).getchildren()#[0].attrib['style']
                for i in ch:
                    for k in i.attrib['style'].split(";"):
                        key,value = k.split(":",1)
                        if "image" in key:
                            p.images.append(value.lstrip("url('\"").rstrip("\"')"))
        p.my_playlist=not p.__parse(js,"is_followed","isFollowed") and p._reorder_hash;
        p.edit_hash=p.__parse(js,"edit_hash","editHash")
        p.access_hash = p.__parse(js,"access_hash","accessHash")
        p.can_edit = bool(p.edit_hash)
        if('list' in js and bool(js['list'])):
            aud = Audio(vk_audio,p.owner_id)
            aud.load_audios_from_js(js['list'])
            aud._audios.playlist=p;
            p._audios = aud._audios;
        p.follow_hash = p.__parse(js,"follow_hash","followHash");
        return p
    @staticmethod
    def grab_image_from_el(el):
            for i in el.attrib['style'].split(";"):
                key,value = i.split(":",1)
                if(key=='background-image'):
                    return value.lstrip(' url("\'').rstrip("\"'); ")
            return False
    @staticmethod
    def from_html(html,vk_audio,reorder_hash=None):                
        p = Playlist(reorder_hash,vk_audio);
        p.owner_id,p.id= (int(i) for i in html.attrib['data-id'].split('_'))
        p.title= html.find_class("audio_item__title")[0].text
        p.audios_count = int(html.find_class("audio_pl__stats_count")[0].text)
        p.raw_id=html.attrib['data-raw-id'];
        p.description=""

        auth=html.find_class("audio_pl_snippet__artist_link")
        

        p.author_info =[{"name":i.text,"href":i.attrib['href']} for i in auth]

        p.my_playlist=False
        p.can_edit=False
        el_cover = html.find_class('audio_pl__cover')[0];

        href_splited = el_cover.attrib['href'].split("_")
        if(len(href_splited)>=3):
            p.access_hash=href_splited[-1]
        el_image =Playlist.grab_image_from_el(el_cover);
        if(el_image):p.images=[el_image];p.has_image=True
        else:
            p.images=[]
            for i in el_cover.find_class("audio_pl_grid_cover"):
                item = Playlist.grab_image_from_el(i);
                if(item!=False):
                    p.images.append(item)
        el_follow_hash =el_cover.find_class("audio_pl__actions_add")[0];
        p.follow_hash = re.findall('[\'|"]([a-z0-9]+?)[\'|"]',el_follow_hash.attrib['onclick'])[0]
        return p
    def __parse(self,json,*keys):
        for i in keys:
            if i in json:return json[i]
    def toJson(self):
        return {
            "owner_id":self.owner_id,
            "id":self.id,
            "title":self.title,
            "description":self.description,
            "author":self.author,
            "author_info":self.author_info,
            "listens":self.listens,
            "thumb":self.thumb,
            "audios_count":self.audios_count
        }
    def artist_music(self,index=0):
        '''
        Получает музыку у артиста данной аудиозаписи ( Или если id артиса не задано выполняет поиск ).
        :param index: Индекс артиста( У какого по счета астиста искать музыку). Если 0 -> будет искать у артиста artists_info[0]
        :type index: int
        '''
        if("/artist/" in self.author_info[index]['href']):
            artist = self.author_hrefs[index]['href'].lstrip("https://vk.com/");
            
            return self._vk_audio.load_artist(artist)
        return self._vk_audio.search(query=self.artist);
    @property
    def Audios(self):
        if(self._audios is None):
            audio:Audio = Audio(self._vk_audio,self.owner_id);
            self._audios = Audio.load_audios(self._vk_audio,0,self.id,self.access_hash,self.owner_id)
            self._audios.playlist=self;
        return self._audios;
    def edit(self,title=None,description=None,audios=None,photo=None):
        """Редактировать плейлист. 
        :param title: Название 
        :type title: str or NoneType
        :param description:Описание
        :type description: str or NoneType
        :param audios: Аудиозаписи, находящиеся в этом плейлисте. Если передано None - берутся из self.Audios
        :type audios: list or NoneType
        :param photo: Обложка плейлиста ( Результат функции Audio.upload_playlist_cover )
        :type photo: list or NoneType
        """
        from .vk_audio import VkAudio
        if(not self.can_edit):raise PermissionError("you do not have permission to do self")
        from .audio_obj import AudioObj
        enumerable = (
            (i.hash if type(i)==AudioObj else str(i)) 
                for i in 
                    (audios if audios is not None else self.Audios)
        )
        data = {"Audios":",".join(enumerable),
                "al":1,
                "description":self.description if description is None else description,
                "hash":self.edit_hash,
                "owner_id":self.owner_id,
                "playlist_id":self.id,
                "title":self.title if title is None else title}
        if(photo==False):data['cover']=-1;
        elif(photo is not None):data['cover']=photo;
        resp =self._vk_audio.action("https://vk.com/al_audio.php?act=save_playlist",data);
        if(resp and 'payload' in resp and len(resp['payload'])>=2):
            self.title=title
            self.description=description
            return True
        return resp;
    def delete(self):
        if(self.follow_hash):
            resp = self._vk_audio.action(data={
                'act': 'follow_playlist',
                'al': 1,
                'hash': self.follow_hash,
                'playlist_id': self.id,
                'playlist_owner_id': self.owner_id,
                'showcase':False
            });
        else:    
            resp = self._vk_audio.action("https://vk.com/al_audio.php?act=delete_playlist",data={
                'al': 1,
                'hash': self.edit_hash,
                'page_owner_id': self.owner_id,
                'playlist_id': self.id,
                'playlist_owner_id': self.owner_id
            })
    def add(self):
        if(not self.follow_hash):raise PermissionError("you do not have permission to do self")

        resp = self._vk_audio.action(data={
            'act': 'follow_playlist',
            'al': 1,
            'hash': self.follow_hash,
            'playlist_id': self.id,
            'playlist_owner_id': self.owner_id,
            'showcase': 0
        });
        if(not resp['payload'][1] or not resp['payload'][1][0] or isinstance(resp['payload'][1][0],str)):raise PermissionError(resp['payload'][1][0])
        return Playlist.from_js(resp['payload'][1][0],self._vk_audio)

