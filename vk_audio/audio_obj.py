import json as json_parser
from .playlist import Playlist
import vk_audio_C_FUNC as func_c
class AudioObj(object):
    def __init__(self,enum):
        self.__decoded = False;
        self._url=None;
        self.enum = enum;
    def as_object(self,json):
        self._json = json;
        self.id=json[self.enum.AUDIO_ITEM_INDEX_ID];
        self.owner_id=json[self.enum.AUDIO_ITEM_INDEX_OWNER_ID];
        self.title=json[self.enum.AUDIO_ITEM_INDEX_TITLE];
        self.artist=json[self.enum.AUDIO_ITEM_INDEX_ARTIST]
        self.duration=json[self.enum.AUDIO_ITEM_INDEX_DURATION]
        self.text=json[self.enum.AUDIO_ITEM_INDEX_LYRICS]
        self.image=json[self.enum.AUDIO_ITEM_INDEX_COVER_URL]
        self.image = self.image.split(",")[-1] if type(self.image)==str else None
        self.artists_info = json[self.enum.AUDIO_ITEM_INDEX_MAIN_ARTISTS]
        self._url = json[self.enum.AUDIO_ITEM_INDEX_URL]
        self._album = json[self.enum.AUDIO_ITEM_INDEX_ALBUM] if json[self.enum.AUDIO_ITEM_INDEX_ALBUM]!=-1 else False
        __hashes=json[self.enum.AUDIO_ITEM_INDEX_HASHES].split("/");

        self.hash ="{0}_{1}_{2}_{3}".format(self.owner_id,self.id,__hashes[self.enum.AUDIO_ACTION_HASH_INDEX],__hashes[self.enum.AUDIO_URL_HASH_INDEX]);

        self.__add_hash = __hashes[self.enum.AUDIO_ADD_HASH_INDEX];
        self.__edit_hash = __hashes[self.enum.AUDIO_EDIT_HASH_INDEX];
        self.__delete_hash=__hashes[self.enum.AUDIO_DELETE_HASH_INDEX];
        self.__restore_hash=__hashes[self.enum.AUDIO_RESTORE_HASH_INDEX];
        self.__track_code_hash=json[self.enum.AUDIO_ITEM_INDEX_TRACK_CODE];
        self.can_edit=True if self.__edit_hash else False
        self.can_delete = True if self.__delete_hash else False 
        self.can_restore=False;
        self.deleted=False;

        pass
    @staticmethod
    def parse(json,vk_audio,audios_to_send_with=None,audiosReorderHash=None):
        item = AudioObj(vk_audio._enum_p)
        if(audios_to_send_with is None):audios_to_send_with=[]  
        item._reorder_hash=audiosReorderHash;
        
        item._vk_audio=vk_audio;
        item.get_url_with=audios_to_send_with or [item];
        item.as_object(json)
        return item
    def __str__(self):
        return  str(self.toArray());
    def __getitem__(self,name:str):
        return self.toArray()[name];
    def __eq__(self, value):
        if(type(value) is not AudioObj):return False;
        return self.id==value.id and self.owner_id == value.owner_id
    def toArray(self):
        return { "owner_id":self.owner_id,
            "id":self.id,
            "title":self.title,
            "artist":self.artist,
            "duration":self.duration,
            "image":self.image,
            "url":self.url,
            "artists_info":self.artists_info 
        }
    @property
    def url(self):
        if not self._url:
            string=','.join(i.hash for i in self.get_url_with)
            json = AudioObj.get_json_from_ids(self._vk_audio.vk,string);
            for i,item in enumerate(json):
                if(len(item)<=self.enum.AUDIO_ITEM_INDEX_URL or not item[self.enum.AUDIO_ITEM_INDEX_URL]):continue
                self.get_url_with[i].as_object(item);
        if not self.__decoded and self._url:
            self.__decoded=True
            self._url=func_c.decode(self._url,self._vk_audio.uid)
        return self._url
    def artist_music(self,index=0):
        '''
        Получает музыку у артиста данной аудиозаписи ( Или если id артиса не задано выполняет поиск ).
        :param index: Индекс артиста( У какого по счета астиста искать музыку). Если 0 -> будет искать у артиста artists_info[0]
        :type index: int or NoneType
        '''
        if(bool(self.artists_info)):
            artist = self.artists_info[index];
            return self._vk_audio.load_artist(artist_id= artist['id'])
        return self._vk_audio.search(query=self.artist);
    @property
    def Album(self) -> Playlist:
        if(not self._album):return
        owner_id = self._album[0]
        id = self._album[1]
        access_hash = self._album[2]
        
        resp = self._vk_audio.action('https://vk.com/al_audio.php?act=load_section',{
            "access_hash": access_hash,
            "al": 1,
            "claim": 0,
            "context":"", 
            "from_id":self._vk_audio.uid,
            "is_loading_all": 1,
            "is_preload": 0,
            "offset": 0,
            "owner_id": owner_id,
            "playlist_id": id,
            "type": "playlist"
            })
        data = resp['payload'][1][0]
        if(not isinstance(data,dict)):return
        return Playlist.from_js(data,self._vk_audio)
    #region vk_methods
    def edit(self,title=None,artist=None,text=None):
        if(not self.can_edit):raise PermissionError("you can not edit self audio")
        if(text is None):text=self.text;
        if(artist is None):artist=self.artist;
        if(title is None):title=self.title;
        ans = self._vk_audio.action(data={'act': 'edit_audio',
            'aid': self.id,
            'oid': self.owner_id,
            'al': 1,
            'force_edit_hash':'', 
            #genre: 18
            'hash': self.__edit_hash,
            'title':title,
            'performer': artist,
            'privacy': 0,
            'text': text
        })
        if(ans["success"]):
            self.text=text;
            self.artist=artist;
            self.title=title;
            return True
        else:
            return ans;
    def delete(self):
        if(not self.can_delete):raise PermissionError("You can not delete self audio")
        elif(self.can_restore):raise PermissionError("self audio have alredy deleted")
        ans = self._vk_audio.action(data={
            'act': 'delete_audio',
            'aid': self.id,
            'al': 1,
            'hash': self.__delete_hash,
            'oid': self.owner_id,
            'restore': 1,
            'track_code': self.__track_code_hash
        });
        if(ans and 'payload' in ans and len(ans['payload'])>=2 and len(ans['payload'][1])!=0):
            self.can_delete=False
            self.can_restore=True;
            return True;
        return ans;
    def add(self,group_id=0):
        '''
            Добавляет аудио в свои аудиозаписи или аудиозаписи группы.
            group_id -> id группы, если 0, то добавляется в свои аудиозаписи.
        '''
        if(self.can_restore):return self.restore();
        ans = self._vk_audio.action('https://vk.com/al_audio.php?act=add',data={
                'al': 1,
                'audio_id': self.id,
                'audio_owner_id': self.owner_id,
                #from: user_list:owner_audios
                'group_id': group_id,
                'hash': self.__add_hash,
                'track_code': self.__track_code_hash
            });
        if(ans["success"]):
            item = ans["payload"][1][0]
            self.as_object(item);
            return True;
        return ans
    def restore(self):
        if(not self.can_restore):
            raise PermissionError("Your audio is not deleted yet");
        ans = self._vk_audio.action(data={
            'act': 'restore_audio',
            'aid': self.id,
            'al': 1,
            'hash': self.__restore_hash,
            'oid': self.owner_id,
            'track_code': self.__track_code_hash
        });
        if(ans and 'payload' in ans and len(ans['payload'])>=2 and len(ans['payload'][1])!=0):
            self.can_restore=False;
            return True;
        return ans
    def reorder(self,move_after_id):
        '''
        Передвигает аудио.
        move_after_id  -> id аудио или AudioObj ПОСЛЕ которого надо вставить данную аудиозапись
        '''
        if(not self._reorder_hash):raise PermissionError("you can not move this audio");
        if isinstance( move_after_id,AudioObj):
            if(move_after_id.owner_id!=self.owner_id):raise ValueError("{0}\nowner_id is not equals\n{1}\nowner_id".format(repr(self),repr(move_after_id)));
            move_after_id=move_after_id.id
        resp = self._vk_audio.action(data={
            'act': 'reorder_audios',
            'al': 1,
            'audio_id': self.id,
            'hash': self._reorder_hash,
            'next_audio_id':move_after_id,
            'owner_id': self.owner_id
            } )
        if(resp and 'payload' in resp and len(resp['payload'])>=2):
            return True;
        return resp
    def reorderInPlaylist(self,playlist:Playlist,move_after_id):
        audios = [];
        if(move_after_id==0):
            audios.append(self.hash);
        for i in playlist.Audios:
            if(i==self):
                continue
            audios.append(i.hash)
            if(i==move_after_id):
                audios.append(self.hash);
        resp = self._vk_audio.action("https://vk.com/al_audio.php?act=save_playlist",{
            "Audios":",".join(audios),
            "al":1,
            "description":playlist.description,
            "hash":playlist.edit_hash,
            "owner_id":playlist.owner_id,
            "playlist_id":playlist.id,
            "title":playlist.title});
        if(resp and 'payload' in resp and len(resp['payload'])>=2):
            return True
        
        return resp;
    #endregion
    @staticmethod
    def get_audio_from_hash(hash:str,vk_audio):
        json=AudioObj.get_json_from_ids(vk_audio,hash)
        answer = [];
        for i in json:
            answer.append(AudioObj(i,vk_audio));
        return answer
    @staticmethod 
    def get_json_from_ids(session,ids):
        from .vk_audio import VkAudio
        json =VkAudio.action(session,'https://vk.com/al_audio.php?act=reload_audio',{
            "al":1,
            "ids":ids
            })
        if('payload' in json and len(json['payload'])==2 and json['payload'][1][0]=='no_audios'):raise ValueError("audios hash is invalid!")
            
        return json['payload'][1][0]