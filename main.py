#!/usr/bin/python3

import requests
import curses
import sys
import os
import time
import re
import threading
from bs4 import BeautifulSoup
import json

PATH = os.path.dirname(os.path.abspath(__file__))

class App:
	finished = False
	__url_processed = 0
	__response_code = 0
	__html = ""
	__banner = [" _____      _         _", "/  __ \\    | |       | |", "| /  \\/_ __| |_   ___| |__", "| |   | '__| __| / __| '_ \\ ", "| \\__/\\ |  | |_ _\\__ \\ | | |", " \\____/_|   \\__(_)___/_| |_|", "   Parser by xorgzz", "    to exit press CTRL-C"]
	def __init__(self, stdscr) -> None:
		os.makedirs(f"{PATH}/raw", exist_ok=True)
		os.makedirs(f"{PATH}/json", exist_ok=True)
		self.__stdsrc = stdscr
		self.__height, self.__width = stdscr.getmaxyx()

		if self.__height < 16 or self.__width < 64:
			print("Screen is not big enough !!")
			sys.exit(1)

		self.__start()

	def __start(self) -> None:
		url = ""
		url_valid = False
		while not url_valid:
			url = str(self.__get_url()).strip()
			if bool(self.__is_url(url)):
				url_valid = True
			else:
				self.__throw_error("Invalid URL !!")
			
		self.__process_url(url)
		self.__print_banner()
		self.__print(f"All data dumped to json/{url}.json", 9, 10)
		time.sleep(3)

		self.finished = True

	def __process_url(self, url) -> None:
		self.__print_banner()
		msg = f"Processing URL {url}"
		self.__print(msg, 9, 10)
		
		thread = threading.Thread(target=self.__thread_url, args=(url,))
		thread.start()

		while self.__url_processed == 0:
			self.__print_banner()
			self.__print(msg, 9, 10)
			for i in range(3):
				time.sleep(0.4)
				self.__print(".", 9, 10+i+len(msg))
			time.sleep(0.4)

		if int(self.__response_code) == 200:

			self.__print_banner()
			self.__print(f"Response Code: {str(self.__response_code)}", 9, 10)
			self.__print(f"Data is being saved, please wait", 10, 10)
			html = str(self.__html.lower().split("</head>")[1])

			with open(f"{PATH}/raw/{url}.raw.html", "w", encoding='utf-8') as fp:
				fp.write(html)
			
			soup = BeautifulSoup(html, "html.parser")
			tds = soup.find_all("td")[2:]

			self.__file_the_tds(tds, url)
		else:
			self.__throw_error(f"Response Code: {self.__response_code}")
			self.__get_url()

	def __file_the_tds(self, tds, url) -> None:
		records = []
		if len(tds)%7 != 0:
			self.__throw_error("Invalid amout of data received !!")
			curses.endwin()
			sys.exit(1)
		for i in range(int(len(tds)/7)):
			record = dict()
			record["crd_id"] = str(self.__strip_record(str(tds[i*7]), True))
			record["logg_data"] = str(self.__strip_record(str(tds[i*7+1])))
			record["not_before"] = str(self.__strip_record(str(tds[i*7+2])))
			record["not_after"] = str(self.__strip_record(str(tds[i*7+3])))
			record["cn"] = str(self.__strip_record(str(tds[i*7+4])))
			record["maching_ids"] = str(self.__strip_record(str(tds[i*7+5])))
			record["issuer_name"] = str(self.__strip_record(str(tds[i*7+6]), True))

			records.append(record)
			
			with open(f"{PATH}/json/{url}.json", "w") as fp:
				fp.write(json.dumps(records, indent=4))

	def __strip_record(self, record, has_a=False) -> str:
		record = record.strip()
		record = record.replace("<br>", ", ")
		record = record.replace("<br/>", ", ")
		record = str(record.split(">")[2 if has_a else 1])
		record = str(record.split("<")[0])
		return record

	def __thread_url(self, url) -> None:
		response = requests.get(f"https://crt.sh/?q={url}")
		if response.status_code == 200:
			self.__html = response.text

		self.__response_code = response.status_code
		self.__url_processed = True
		
	def __throw_error(self, msg):
		self.__print_banner()
		self.__print(msg, 9, 10)
		self.__print("Try again", 9+1, 10+1)
		for i in range(3):
			time.sleep(0.4)
			self.__print(".", 9+1, 10+1+len("Try again")+i)
		time.sleep(0.4)

	def __print_banner(self) -> None:
		self.__stdsrc.clear()
		i = 0
		for slice in self.__banner:
			self.__print(slice,i,4)
			i+=1

	def __print(self, message, y=0, x=0) -> None:
		self.__stdsrc.addstr(y, x, message)
		self.__stdsrc.refresh()
	
	def __insert_into_string(self, the_string, what, where) -> str:
		return the_string[:where] + what + the_string[where:]
	
	def __del_from_string(self, the_string, where, del_type=0) -> str:
		if del_type == 0:
			return the_string[:where-1] + the_string[where:]
		if del_type == 1:
			return the_string[:where] + the_string[where+1:]
	
	def __is_url(self, url) -> bool:
		if url == "":
			return False
		regex = re.compile("^((?!-)[A-Za-z0-9-]" + "{1,63}(?<!-)\\.)" +"+[A-Za-z]{2,6}", re.IGNORECASE)
		return re.search(regex, url)

	def __get_url(self) -> str:
		useless_keys = (259, 258, ord("#"), ord("$"), ord(","), ord("@"), ord("!"), ord("%"), ord("^"), ord("&"), ord("*"), ord("("), ord(")")) # you won't need then in url anyways
		x = 10
		y = 9
		ask_msg = "Url: "
		cursor_position = 0 + x + len(ask_msg)

		url = ""
		inpt_index = 0

		backspace = 8 if os.name == "nt" else 263 # depends on the os
		
		while True:
			self.__print_banner()
			self.__print(ask_msg, y, x)
			self.__print(url, y, x+len(ask_msg))
			self.__stdsrc.move(y, cursor_position)
			self.__stdsrc.refresh()

			try:
				key = self.__stdsrc.getch()
			except KeyboardInterrupt:
				curses.endwin()
				print("User Exited")
				sys.exit(0)

			if key == backspace: # backspace
				if len(url) > 0:
					url = str(self.__del_from_string(url, inpt_index))
					cursor_position -= 1
					inpt_index -= 1
			elif key == ord("\n"): # enter
				break
			elif key == 260: # arrow left
				if inpt_index > 0:
					inpt_index -= 1
					cursor_position -= 1
			elif key == 261: # arrow right
				if inpt_index < len(url):
					inpt_index += 1
					cursor_position += 1
			elif key == 330: # delete
				if len(url) > 0:
					url = str(self.__del_from_string(url, inpt_index, 1))
			elif key in useless_keys: # delete
				continue
			else: # any other key
				url = str(self.__insert_into_string(url, chr(key), inpt_index))
				cursor_position += 1
				inpt_index += 1

		return url

def main(stdscr) -> None:
	app = App(stdscr)
	if app.finished:
		curses.endwin()
		sys.exit(0)

if __name__ == "__main__":
	curses.wrapper(main)