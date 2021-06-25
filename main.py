from threading import Thread
import requests
import re
import pprint 
import random
import time
from queue import Queue


def workableTimeRegistration( function ):
	def wrapped(*args):
		start_time = time.clock()
		res = function(*args)
		print('Time of function')
		print(str(time.clock() - start_time))
		return res
	return wrapped


class objValidation():
	# Checking for some exeptions

	def unsigned_int(self, verifiable):
		if (type(verifiable) is not int) | (verifiable < 0):
			raise Exception('The input must be an unsigned integer')
		

class objTreadImgsUrlsManager(Thread):
	# That class needed to manage parsing urls and correctable writing to queues
	def __init__(self, UrlsQueue, DownloadingQueue, Path):
		Thread.__init__(self)
		self.urls_queue = UrlsQueue
		self.downloading_queue = DownloadingQueue
		self.path = Path


	def run(self):
		while True:
			self.__getImgsUrlsComponents(self.urls_queue.get())
			self.urls_queue.task_done()


	def __getImgsUrlsComponents(self, SiteUrl : str ):

		html = requests.get(SiteUrl).content.decode()

		imgs_names_list = re.findall(r'u\"\:\"([\S]*?\.png)', re.search(r'window.__pg = ([\[\]\{\}\"\w\,\.\:0-9]*)', html).group(1))

		info_dict = re.search(r'window.__info = ([\\\/\?\=\-\[\]\{\}\"\w\,\.\:0-9]*)', html)

		chapter_imgs_url = re.search(r'\"url\"\:\"([\/\\\-\w]*)\"', info_dict.group(1)).group(1).replace('\\','')
		chapter_imgs_servers = [correct_chapter_img_servers.replace('\\','') for correct_chapter_img_servers in re.findall(r'[\w]+\:[\w\\\/\.]+',re.search(r'\"servers\"\:\{([\w\"\:\\\/\.\,]*)\}',info_dict.group(1)).group(1))]

		[self.downloading_queue.put({
									'ChapterImgsServers': chapter_imgs_servers,
									'ChapterImgsUrl': chapter_imgs_url,
									'ImgName': imgs_names_list[img_index],
									'Dir': self.path,
									'FileName': img_index
									}) for img_index in range(len(imgs_names_list))]


class objTreadDownload(Thread):
	def __init__(self, downloading_queue, writing_queue):
		Thread.__init__(self)
		self.downloading_queue = downloading_queue
		self.writing_queue = writing_queue


	def run(self):
		while True:
			self.downloading(self.downloading_queue.get(), self.writing_queue)
			self.downloading_queue.task_done()		


	def downloading(self, queueDict: dict, writing_queue: dict):
		#ChapteImgsServers : list, ChapterImgsUrl : str, ImgName : str , Dir: str

		while True:

			res = requests.get(queueDict['ChapterImgsServers'][random.randint(0,3)] + queueDict['ChapterImgsUrl'] + queueDict['ImgName'])
			
			if res.status_code == 200:

				writing_queue.put({
									'Data': res.content,
									'Dir': queueDict['Dir'],
									'FileName': str(queueDict['FileName'])
					})
					
				print('Download done : ', queueDict['Dir'] + str(queueDict['FileName']))

				break
			else:
				print('Download error: ', queueDict['Dir'] + str(queueDict['FileName']), '\nRetrying...')


class objTreadWrite(Thread):
	def __init__(self, writing_queue):
		Thread.__init__(self)
		self.writing_queue = writing_queue


	def run(self):
		while True:
			self.writing(self.writing_queue.get())
			self.writing_queue.task_done()


	def writing(self, queueDict: dict):
		
		with open(queueDict['Dir'] + str(queueDict['FileName']) + '.png', 'wb+') as image:
					
			image.write(queueDict['Data'])
					
			print('Write done : ', queueDict['Dir'] + str(queueDict['FileName']) + '.png')


class Parser():
	# Using for writing parser for mangalib
	def __init__(self, MainPath, UrlsManagingTreadCount = 1, DownloadingTreadCount = 1, WritingTreadCount = 1):

		self.validation = objValidation()

		self.validation.unsigned_int(DownloadingTreadCount)
		self.validation.unsigned_int(WritingTreadCount)
		self.validation.unsigned_int(UrlsManagingTreadCount)

		self.main_path = MainPath

		self.downloading_tread_count = DownloadingTreadCount
		self.writing_tread_count = WritingTreadCount
		self.urls_managing_tread_count = UrlsManagingTreadCount

		self.titles_urls_queue = Queue()
		self.chapter_urls_queue = Queue()
		self.downloading_queue = Queue()
		self.writing_queue = Queue()

		self.__CreatingTreads()


	def __CreatingTreads(self):

		for i in range(self.urls_managing_tread_count):
			my_imgs_urls_managin_tread = objTreadImgsUrlsManager(self.chapter_urls_queue, self.downloading_queue, self.main_path)
			my_imgs_urls_managin_tread.setDaemon(True)
			my_imgs_urls_managin_tread.start()

		for i in range(self.downloading_tread_count):
			my_downloading_tread = objTreadDownload(self.downloading_queue, self.writing_queue)
			my_downloading_tread.setDaemon(True)
			my_downloading_tread.start()

		for i in range(self.writing_tread_count):
			my_writing_tread = objTreadWrite(self.writing_queue)
			my_writing_tread.setDaemon(True)
			my_writing_tread.start()
	

	def push_urls(self, Url: str):
		self.chapter_urls_queue.put(Url)


	def __del__(self):

		self.titles_urls_queue.join()
		self.chapter_urls_queue.join()
		self.downloading_queue.join()
		self.writing_queue.join()












def getImgsUrlsComponents( SiteUrl : str ) -> list:

	html = requests.get(SiteUrl).content.decode()

	imgs_names_list = re.findall(r'u\"\:\"([\S]*?\.png)', re.search(r'window.__pg = ([\[\]\{\}\"\w\,\.\:0-9]*)', html).group(1))

	info_dict = re.search(r'window.__info = ([\\\/\?\=\-\[\]\{\}\"\w\,\.\:0-9]*)', html)

	chapter_imgs_url = re.search(r'\"url\"\:\"([\/\\\-\w]*)\"', info_dict.group(1)).group(1).replace('\\','')
	chapter_imgs_servers = [correct_chapter_img_servers.replace('\\','') for correct_chapter_img_servers in re.findall(r'[\w]+\:[\w\\\/\.]+',re.search(r'\"servers\"\:\{([\w\"\:\\\/\.\,]*)\}',info_dict.group(1)).group(1))]

	return [{
									'ChapterImgsServers': chapter_imgs_servers,
									'ChapterImgsUrl': chapter_imgs_url,
									'ImgName': imgs_names_list[img_index],
									'Dir':  'Manga/',
									'FileName': img_index
									} for img_index in range(len(imgs_names_list))]


@workableTimeRegistration
def downloadImgs( ChapterUrl: str) -> bool:
	#'https://mangalib.me/bleach/v1/c0?page=1'
	chapter_imgs_servers, chapter_imgs_url, imgs_names_list = getImgsUrlsComponents(ChapterUrl)

	path = 'Manga/'

	imgs_info = [ {
			'ChapterImgsServers': chapter_imgs_servers,
			'ChapterImgsUrl': chapter_imgs_url,
			'ImgName': imgs_names_list[img_index],
			'Dir': path,
			'FileName': img_index
			} for img_index in range(len(imgs_names_list))]

	downloading_queue = Queue()
	writing_queue = Queue()

	for i in range(5):
		mytread = objTreadDownload(downloading_queue, writing_queue)
		mytread.setDaemon(True)
		mytread.start()

	for i in range(5):
		mytread = objTreadWrite(writing_queue)
		mytread.setDaemon(True)
		mytread.start()

	for img_info in imgs_info:
		downloading_queue.put(img_info)

	downloading_queue.join()
	writing_queue.join()

	return True

@workableTimeRegistration
def main():

	# chapter_imgs_servers, chapter_imgs_url, imgs_names_list = getImgsUrlsComponents('https://mangalib.me/death-march-kara-hajimaru-isekai-kyousoukyoku/v10/c61/bloki?page=1')

	# downloadImgs(chapter_imgs_servers, chapter_imgs_url, imgs_names_list)
	# print(len(imgs_names_list))


	res = requests.get('https://mangalib.me/bleach').content.decode()
	chapters_blocks = re.findall('<a class=\"link-default\" title=\"[\s\S]+?<\/a>', res)
	titles = [re.search('title=\"([\s\S]*?)\"', chapter_block).group(1) for chapter_block in chapters_blocks]
	hrefs = [re.search('href=\"([\s\S]*?)\"',chapter_block).group(1) for chapter_block in chapters_blocks]
	toms = [re.search('Том\\n[\'\s]*([\0-9]+?)\.',chapter_block).group(1) for chapter_block in chapters_blocks]
	chapters = [re.search('Глава ([\0-9]+?)\\n',chapter_block).group(1) for chapter_block in chapters_blocks]

	pprint.pprint(titles)
	pprint.pprint(hrefs)
	pprint.pprint(toms)
	pprint.pprint(chapters)
	print(len(chapters))
	print(len(toms))
	print(len(hrefs))
	print(len(titles))
	print(len(chapters_blocks))


# @workableTimeRegistration
def test():

	prox = '46.4.96.137:8080'

	proxy_dict = {
				'http': 'http://' + prox
	}

	data = {'task_id': 9, 'text': "Вычислить корень из 144"}

	# print(requests.post('https://find-it.fut.ru/contests/1/segment-task', proxies=proxy_dict).content.decode())

	# Make the HTTP request through the session.
	r = requests.post('https://find-it.fut.ru/test/answer', proxies = proxy_dict, data = data)

	print(r.status_code)
	print(r.content.decode())

if __name__ == '__main__':
	# main()
	# Parser(MainPath, UrlsManagingTreadCount = 1, DownloadingTreadCount = 1, WritingTreadCount = 1)
	downloadImgs('https://mangalib.me/bleach/v1/c0?page=1')

	# test()

