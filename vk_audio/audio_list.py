from .audio_obj import *
from .audio_enum_index import *;
class AudioList(list):
	def __init__(self,vk,*params):
		self.vk_audio=vk;
		self.playlist=None;
		super().__init__(*params)
	def __str__(self):
		return str(self.toJsonArray())
	def toJsonArray(self):
		ans=[]
		for i in self:
			ans.append(i.toArray())
		return ans
	def move(self,from_index:int=None,to_index:int=None):
		before_index_id=to_index
		if(to_index==from_index):return;
		elif(to_index>from_index):
			before_index_id=self[to_index];
		else:
			if(before_index_id!=0): 
				before_index_id=self[before_index_id-1];
		if(self.playlist!=None):
			ans = self[from_index].reorderInPlaylist(self.playlist,before_index_id);
		else:
			ans = self[from_index].reorder(before_index_id);
		if(ans==True):
			self.insert(to_index, self.pop(from_index)) 
			
		return ans

