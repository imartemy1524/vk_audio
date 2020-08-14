from .audio_list import *
from .playlist import *
from .audio_obj import *
from .audio import *
from .audio_enum_index import *
import json as json_parser
import vk_api,re,json,os,time,requests,random
import vk_audio_C_FUNC as func_c

class VkAudio(object):
    @property
    def _enum_p(self):
        if(not self.__enum_p):self.__enum_p=AudioEnumIndex(html.fromstring(self.vk.http.get('https://vk.com/').text).head,self.vk)
        return self.__enum_p;
    def __init__(self,vk=None,login=None,password=None,count_audios_to_get_url=10,your_id=None):
        """Модуль аудио вк. 
            vk - vk_api.VkApi или login и пароль
            :param count_audios_to_get_url: У скольких аудио получать ссылки за раз. Чем меньше значение, тем быстрее будут получаться ссылки. Устанавливать значение в пределах 1-10
            :param your_id: Ваш id. Если не задан, то будет получен методом users.get. При указании неверного id могут получиться неиграбельные ссылки.
            """
        if login is not None and password is not None:
            self.vk=vk_api.VkApi(login,password);
            self.vk.http.verify=False
            self.vk.auth()
        elif vk is not None:
            self.vk=vk;
            self.vk.http.verify=False 
        else:raise ValueError("No auth data passed");
        self.uid = your_id if your_id is not None else self.vk.method("users.get")[0]["id"] 
        self.c_u = count_audios_to_get_url
        self.__enum_p=None
    def load(self,owner_id=None) -> Audio:
        """
        Получить музыку пользователя/группы вк.
        :param owner_id: id страницы, у которой хотите получить аудио. Для групп - отрицательный
        :type owner_id: int or NoneType
        :param count_audios_to_get_url: У скольких аудиозаписей получать ссылку за один раз
        :type count_audios_to_get_url: int
        """
        if(owner_id is None):owner_id=self.uid

        html_text = self.vk.http.get('https://vk.com/audios%i' % owner_id,allow_redirects=False).text;
        if(not html_text):return False
        tree = html.fromstring(html_text)

        if(not self.__enum_p):self.__enum_p=AudioEnumIndex(tree.head,self.vk)
        script_with_info = self._get_script_el(tree);
        if(script_with_info==False):return False;

        #получаем данные о плейлисте в json
        json = self._parse_json_from_js(script_with_info.text)
        audio_to_return = (MyAudio if bool(json['newPlaylistHash']) else Audio)(self,owner_id,json['reorderHash'],json['audiosReorderHash'],json['newPlaylistHash'],json['listenedHash'],json['playlistCoverUploadOptions'])
        audio_to_return.load_playlists_from_js(json['playlists']);
        if 'playlist' in json['sectionData']['all'] and json['sectionData']['all']['playlist'] and json['sectionData']['all']['playlist']['list']:
            audio_to_return.load_audios_from_js(json['sectionData']['all']['playlist']['list']);
        return audio_to_return
    def load_artist(self,artist_nickname=None,artist_id=None) -> Audio:
        """
        Получение музыки артиста. Возможно без авторизации
        :param artist_nickname: Никнейм артиста.
        :type artist_nickname: str or NoneType
        :param artist_id: Id артиста.
        :type artist_id: int or NoneType
        """
        artist_href = ""
        if(artist_nickname is not None): 
            if("/" not in artist_nickname):artist_href = "artist/"+artist_nickname
            else:artist_href=artist_nickname
        elif(artist_id is not None): artist_href = "artist/"+str(artist_id)
        else:raise ValueError("artist_nickname or artist_id should be not None");

        h = html.fromstring(self.vk.http.get("https://vk.com/al_artist.php",allow_redirects=False,params={
            "__query":artist_href+"/top_audios",
            "_ref":artist_href,
            "_rndVer":random.randint(0,100000),
            "al":-1,
            "al_id":self.uid
            }).text).head.getchildren();
        if(len(h)!=3):raise vk_api.AccessDenied("Artist not found")
        json_audios = self._parse_json_from_js(h[1].text);
        if(not json_audios):raise vk_api.AccessDenied("Artist not found")
        if(json_audios['payload'][1][0].startswith('"\/artist\/')):
            return self.load_artist(json_audios['payload'][1][0].strip('"\'').replace("\\","").lstrip("/"))
        audios_html = html.fromstring(json_audios['payload'][1][1]);
        h = html.fromstring(self.vk.http.get("https://vk.com/al_artist.php",allow_redirects=False,params={
            "__query":artist_href+"/albums",
            "_ref":artist_href,
            "_rndVer":random.randint(0,2147483647),
            "al":-1,
            "al_id":self.uid
            }).text).head.getchildren()
        albums_html = None
        if(len(h)==3):  
            json_albums = self._parse_json_from_js( h[1].text)
            albums_html = html.fromstring(json_albums['payload'][1][1]);
        return ArtistAudio(self,audios_html,albums_html,artist_nickname);
    def search(self,query="Imagine dragons"):
        resp = self.action(data= {
            'act': 'section',
            'al': 1,
            'claim': 0,
            'is_layer': 0,
            'owner_id': self.uid,
            'q': query,
            'section': 'search'
        });
        a = AudioSearch(self,resp['payload'][1][0])
        json = resp['payload'][1][1]
        a.load_playlists_from_js(json['playlists']);
        if 'playlist' in json and json['playlist']['list']:
            a.load_audios_from_js(json['playlist']['list'])
        return a;
    def get_only_audios(self,owner_id=None,offset=0,count=None,need_enum=False):
        if(not need_enum):
            return [i for i in self._get_only_audios_enum(owner_id,offset,count) if i!=None]
        else:
            return self._get_only_audios_enum(owner_id,offset,count)
    def get_by_id(self,audios):
        '''
        Получить аудиозапись по id
        :param audios: Аудиозаписи, которые надо получить перечисленные через запятую.
        :type audios: str or list
        '''
        if(isinstance(audios,str)):audios = audios.split(",")
        ans,auds = [],[]
        c = 0;
        for i in audios:
            url = 'https://m.vk.com/audio'+i;
            response = self.vk.http.post(url);
            h = html.fromstring(response.text).find_class("audio_item_"+i)
            if(not h):
                ans.append(False)
            else:
                o = AudioObj.parse(json_parser.loads(h[0].attrib['data-audio']),self,auds);
                ans.append(o)
                auds.append(o)
                c+=1
                if(c%10==9):
                    auds = []
        return ans;
    def _get_only_audios_enum(self,owner_id,offset,count):
        resp = self.action("https://m.vk.com/audios%i"%(owner_id if owner_id is not None else self.uid),
            data={
            '_ajax': 1,
            'offset': offset    
           });
        if(not resp['data'] or not resp['data'][0] or not resp['data'][1]):
            yield;
        else:
            for i in Audio.load_audios_from_js([],
                    (resp['data'][0][key][1] for key in resp['data'][0]),
                    self):
                yield i;
                if(count is not None):
                    count-=1
                    if(count==0):break;            
            if(count is None or count>0):
                for i in self._get_only_audios_enum(owner_id,offset+c+1,None if count is None else count-c):
                    if(i):
                        yield i 
    def _get_script_el(self,tree):
        for i in tree.body.getchildren()[::-1]:
            if(i.tag=='script'):
                return i
        return False
    def _parse_json_from_js(self,js):
        if(not isinstance(js,str)):raise TypeError("js have to be str")
        q = func_c.parse_json_from_js(js);
        return json_parser.loads(q);

    
    @staticmethod
    def json(resp):
        try:
            return json_parser.loads(resp.text.lstrip('<!--'))
        except json.decoder.JSONDecodeError:
            pass
    def action(self,url="https://vk.com/al_audio.php",data={},params={},method="post",**args):
        from .vk_audio import VkAudio
        r = self.vk.http if(isinstance(self,VkAudio)) else self.http if isinstance(self,vk_api.VkApi) else self
        r.headers['X-Requested-With']='XMLHttpRequest'
        f=(r.post if method=="post" else r.get)
        resp = f(url,data=data,params=params,**args)
        del r.headers['X-Requested-With'];

        json = VkAudio.json(resp);
        json["success"]=(json and 'payload' in json and len(json['payload'])>=2 and len(json['payload'][1])!=0)

        return json
