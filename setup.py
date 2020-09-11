#!python
#cython: language_level=3
from setuptools import find_packages,setup,Extension

my_ex = Extension("vk_audio_C_FUNC",sources = ['src/C_FUNC/PyProg.cpp'],language="c++")
setup(
    name = "vk_audio",
    version = "7.3",
	packages=find_packages(),
    py_modules = ["vk_api",'datetime','lxml','click','curses-menu'],
    author = "Superbespalevniy chel",
    author_email = "imartemy1@gmail.com",
    url = "https://vk.com/fesh_dragoziy",
    description = "Модуль для вызова методов аудио вк.",
    ext_modules = [my_ex],
)  
