

# vk_audio
Модуль на python для работы с аудио вк
### Установка
Установить данный модуль можно через pypi:
```pip install vk_audio```
### Требования 
> python>=3.6
### Примеры:
<details> 
 <summary><b>Авторизация</b>:</summary>
  

 1. Через **логин** и **пароль**
	
	  ```
	  import vk_audio,vk_api
	  vk_session = vk_api.VkApi(login='mylogin',password='mypassword')
	  vk_session.auth()
	  vk = vk_audio.VkAudio(vk=vk_session)
	  ```
	  или<br>
    ```
    import vk_audio
    vk = vk_audio.VkAudio(login='mylogin',password='mypassword');
    ```
 2. Через **куки**
	 <br>**Обратите внимание**: куки надо получать **ТОЛЬКО** с того же ip, на котором будет запускаться данный скрипт. Иначе, может не сработать.
   <br>**remixsid_cookie** - Кука **remixsid**. P.S. Лучше получать **НЕ** из firefox - может не работать<br>
   **your_id** - **id** пользователя, чья это кука<br>
     ```
     import vk_audio
     vk = vk_audio.VkAudio(remixsid_cookie="кука",your_id=123)
     ```
</details> 
<details> 
 <summary><b>Получение аудио</b>:</summary>
  
  ```
  vk = vk_audio.VkAudio(vk=vk_session)# <- объект vk_audio, полученный после авторизации
  ```
  - ***Получение аудиозаписей/плейлитов по owner_id***
  
  Owner_id - id пользователя или группы ( для групп - отрицательные )
  ```
  owner = 12345#Если None - аудио будут браться из своей музыки
  data = vk.load(user_id)#получаем наши аудио 
  
  second_audio = data.Audios[1]#берем вторую аудиозапись
  format_string = "{title} - {artist} ({owner_id}_{id}) -> {url}"
  print("2.",format_string.format(
      title=second_audio.title, #так же можно second_audio['title']
      artist=second_audio.artist,
      owner_id = second_audio.owner_id,
      id=second_audio.id,
      url=second_audio.url
      ))
  print("1.",format_string.format(**data.Audios[0].toArray()))#более хитрый способ
  ```
  
- ***Получение ТОЛЬКО аудио*** 

  Если Вам нужен метод, чтобы получить только аудио, и, например, скачать их, то это - как раз то, что Вам нужно.
  
  **P.S.** При получении аудио этим способом их невозможно передвигать методом move 
  ```
  auds = vk_audio.get_only_audios(owner_id=-1134)
  audio = auds[0]
  audio_url = audio.url# и т.п.
  ```
  
- ***Поиск по аудиозаписям***

  ```
    data = vk.search("Query")
    audios = data.Audio
    playlists = data.PLaylists
    artists = data.artists_info
  ```
- ***Получение аудиозаписей по их id***

  ```
  audios = "100_456239018,100_456239017"#или ['100_456239018','100_456239017']
  audio_1,audio_2 = vk.get_by_id(audios)
  #Если какая-то аудиозапись не будет найдена - возвратится False
  ```
- ***Получение аудиозапией и плейлистов артиста***
  Получить аудио и плейлисты артиста. 
  **P.S.** Если вы берете артиста из музыки пользователя или из плейлиста, то лучше воспользоваться методом `artist_music`
  ```
  nickname = "imaginedragons"
  artist_id=None#ну или по id, если найдете
  audios = vk.load_artist(artist_nickname=nickname,artist_id=artist_id)
  ```
</details> 
<details> 
  <summary><b>Разные действия с аудиозаписью</b>:</summary>
  
```
audio = data.Audios[10] # переменная audio <- AudioObj
```
 - ***Редактирование***<br>
		 Редактирование аудиозаписи
	```
	if(audio.can_edit):
	    audio.edit(title=audio.title+" Отредактировано",text="Крутые слова, которые должны быть у аудио.",artist="Полностью новый артист")
	```
- ***Удаление***<br>
	    Удаление аудиозаписи 
	```
	if(audio.can_delete): audio.delete()
	```
- ***Восстановление/добавление***<br>
		Добавление новой аудиозаписи или восстановление удаленной 
	```
	audio.add()# для добавления в группу с id 123 - audio.add(123)
	```
	**P.S.** Если вы только что удалили аудиозапись, то можно вызвать метод `restore` для её восстановления напрямую , но мы вам советуем использовать `add`, ибо он автоматически определяет, нужно ли добалять или восстанавливать аудио.
- ***Изменение позиции аудио***	<br>
    Передвигает аудиозапись с 0 индекса на 2, сохраняя изменения в вк <br>
	```audio.Audios.move(0,2)```<br>
	Так же можно передвигать в плейлисте:<br>
	```audio.Playlists[0].Audios.move(0,1)```
</details>

<details> 
  <summary><b>Передача по сети / получение hash'a</b>:</summary>

Наверняка многим надо, чтобы можно было сохранить определенную аудиозапись, и потом ее восстановить. Первый вариант, который приходит на ум - сохранить ее <b>owner_id</b> и <b>item_id</b>, а потом восстановить методом get_by_id. Так, конечно, можно, но мы крайне не советуем вам так делать, если вы сохраняете больше одной аудиозаписи - т.к. каждая аудиозапись будет восстанавливаться отдельным запросом и отдельным парсингом данных из html. Вам это надо? Если нет, то следующий метод для вас.
```
audio_list = data.Audios #<- AudioList
audio = audio_list[0] #<- AudioObj
playlist = data.Playlists[1] #<- Playlist
```
- ***Сохранение и восстановление аудиозаписи по hash***<br>
		 Возвращает hash аудиозаписи, по которой ее можно восстановить.
     <b>P.S.</b>Так 
     ```
     hash = audio.zip()
     audio_restored_obj = vk_audio.AudioObj.unzip(hash,vk)[0]
     ```
     Если надо сохранить несколько аудио сразу - можно воспользоваться методом ```AudioList.zip```:
     ```
     hash = audio_list.zip(0,10);#получаем hash с 1 по 10 аудиозапись
     audios_restored_objects = vk_audio.AudioObj.unzip(hash,vk)
     ```
     Ручной способ:
     ```
     hash = ",".join(i.zip() for i in audio_list)
     ```
- ***Сохранение и восстановление артиста аудиозаписи***
  ```
  hashes = []
  for i,item in enumerate(audio.artists_info):
    hashes.append(i.zip_artist(i))
  for i in hashes:
    artist_music = vk.load_arist(artist_hash=i)
    if not isinstance(artist_music,vk_audio.AudioSearch):#Если артиста нет - возвратится поиск
      nickname = artist_music.nick;
      audios = artist_music.Audios
      #и тп.
  ```
  
- ***Сохранение и восстановление артиста плейдиста***
  К сожалению, для сохранения плейлиста нет такого же безупречного метода, как и для аудиозаписи. Метод `zip` будет возвращать строку, содержащую в себе json объект плейлиста. НО! Есть возможность получить **hash** от списка аудиозаписей.
  ```
  playlist_json_str = playlist.zip()
  playlist_unzipped = vk_audio.Playlist.unzip(playlist_json_str,vk)
  
  audios_hash = playlist.zip_audios()
  audios_list_unzipped = vk_audio.Playlist.unzip_audios(audios_hash,vk)
  
  ```
</details>
