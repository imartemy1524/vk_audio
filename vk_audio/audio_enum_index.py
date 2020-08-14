import re
class AudioEnumIndex(object):
    """Класс, который получает индексы для парсинга аудио из Json
    Если вы это читаете, то, наверное, задаетесь вопросом, мол, в чем прикол?
    Ответ прост - когда мы получаем аудио, то оно приходит в виде
    [124,123,"","title","artist",151,0,0,"",0,98,"","[]","791f182bde81154cd3//d47c16cfba85aea71b/2221debbe1acc02050//60bd0c34804839fe5b/79a28d5546b5a052ec","https://sun1-16.userapi.com/c852220/v852220854/1b3178/12OVBdy2xLo.jpg,https://sun1-94.userapi.com/c852220/v852220854/1b3175/_jXKlI44750.jpg",{"duration":165,"content_id":"123_123","puid22":14,"account_age_type":3,"_SITEID":276,"vk_id":123,"ver":251126},"",[{"id":"3526648680302109106","name":"Little Big"},{"id":"459074144901352199","name":"Tatarka"}],[{"id":"4331274677005519524","name":"Clean Bandit"}],[-123,123,"2317e9c8b9f054546a"],"87691530vlqeJ66gBvKGqDnL0N7PXgY",0,0,true,"",false]
    Неудобоно, да?
    Впринципе, можно напрямую в коде указать, что 0 индекс - owner_id, 1 - item_id и т.п., 
        но при малейшем изменении/добавлении какого-либо эллемента весь код пойдет на смарку.
    Теперь перейдем к сути этого класса - этот класс парсит как раз такие индексы из javascript.
    """
    def __init__(self,header_object,vk):
        self.__vk = vk;
        children = header_object.getchildren();
        for i in children:
            if(i.tag!="script" or 'src' not in i.attrib):continue
            src =i.attrib['src']
            if(re.search('common\.[a-z0-9]+?\.js',src)):
                self._get_script_from_url(src)
                break;
        else:
            raise ValueError("неизвестная ошибка - скипт common.js не найден")
    def _get_script_from_url(self,src:str):
        resp = self.__vk.http.get("https://vk.com"+src if src.startswith("/") else src);
        text = resp.text;
        match = re.search('\{(AUDIO_ITEM_INDEX_ID:.+?)\}',text).groups()[0]      
        for i in match.split(','):
            i=i.split(':')
            if(len(i)!=2):continue;
            val = i[1].lstrip(' ').rstrip(' ');
            if(not val.isdigit()):continue
            val = int(val)
            if(i[0]=='AUDIO_ITEM_INDEX_ID'):self.AUDIO_ITEM_INDEX_ID=val
            elif(i[0]=='AUDIO_ITEM_INDEX_OWNER_ID'):self.AUDIO_ITEM_INDEX_OWNER_ID=val
            elif(i[0]=='AUDIO_ITEM_INDEX_URL'):self.AUDIO_ITEM_INDEX_URL=val
            elif(i[0]=='AUDIO_ITEM_INDEX_PERFORMER'):self.AUDIO_ITEM_INDEX_ARTIST=val
            elif(i[0]=='AUDIO_ITEM_INDEX_TITLE'):self.AUDIO_ITEM_INDEX_TITLE=val
            elif(i[0]=='AUDIO_ITEM_INDEX_DURATION'):self.AUDIO_ITEM_INDEX_DURATION=val
            elif(i[0]=='AUDIO_ITEM_INDEX_ALBUM_ID'):self.AUDIO_ITEM_INDEX_ALBUM_ID=val
            elif(i[0]=='AUDIO_ITEM_INDEX_AUTHOR_LINK'):self.AUDIO_ITEM_INDEX_AUTHOR_LINK=val
            elif(i[0]=='AUDIO_ITEM_INDEX_LYRICS'):self.AUDIO_ITEM_INDEX_LYRICS=val
            elif(i[0]=='AUDIO_ITEM_INDEX_COVER_URL'):self.AUDIO_ITEM_INDEX_COVER_URL=val
            elif(i[0]=='AUDIO_ITEM_INDEX_MAIN_ARTISTS'):self.AUDIO_ITEM_INDEX_MAIN_ARTISTS=val
            elif(i[0]=='AUDIO_ITEM_INDEX_HASHES'):self.AUDIO_ITEM_INDEX_HASHES=val
            elif(i[0]=='AUDIO_ITEM_INDEX_TRACK_CODE'):self.AUDIO_ITEM_INDEX_TRACK_CODE=val;
            elif(i[0]=='AUDIO_ITEM_INDEX_ALBUM'):self.AUDIO_ITEM_INDEX_ALBUM=val;
        s =self._get_hash(text,'actionHash');g =s.groups()[0]if s else None;
        self.AUDIO_ACTION_HASH_INDEX=int(g) if g.isdigit() else 2;
        #чтобы поиск шёл быстрее, обрезаем строку 
        if(s):
            text = text[s.start()-1000:-1 if len(text)>s.start()+4000 else (s.start()+4000)]
        self.AUDIO_URL_HASH_INDEX=self._get_hash_key(text,'urlHash', 5);
        self.AUDIO_EDIT_HASH_INDEX=self._get_hash_key(text,'editHash', 1);
        self.AUDIO_RESTORE_HASH_INDEX=self._get_hash_key(text,'restoreHash', 6);
        self.AUDIO_DELETE_HASH_INDEX=self._get_hash_key(text,'deleteHash',3);
        self.AUDIO_ADD_HASH_INDEX = self._get_hash_key(text,'addHash',0);
    def _get_hash_key(self,text,string,default):
        s = self._get_hash(text,string);
        g = s.groups()[0] if s else None;
        return int(g) if g is not None and g.isdigit() else default;
    def _get_hash(self,where,title):
        return re.search(title+':[a-z]+?\[(\d+?)\]',where)