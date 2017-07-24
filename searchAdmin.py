
# Avery VanKirk 2017
# tv show clip searcher

import requests
from bs4 import BeautifulSoup
import subtitle_downloader
import sqlite3
import os
import sys
import re
import tempfile
import subprocess
import signal

import searchConfig

def signal_handler(signal, frame):
	print('\nctrl+c detectd, exiting')
	sys.exit(0)

#runs multiple sql statements
def sqlbatch(conn,commands):

	c = conn.cursor()
	for statement in commands:
		try:
			c.execute(statement)
		except:
			print("Error:",statement)

#Updates database with subtitles from a folder
def subUpdateFromFile(conn,folderPath):

	walk = os.walk(folderPath)
	c = conn.cursor()

	for root, dirs, subs in walk:

		for sub in subs:
			name, extension = os.path.splitext(sub)
			if extension  == ".srt":
				parse = re.search(r"(.+) - (S\d{2}E\d{2})",name)
				if parse == None:
					print("Trying 2nd regex")
					parse = re.search(r"(.+).(S\d{2}E\d{2})",name)

				#Tries to rebuild epcode so as not to have to switch around main logic to support more parse group 3
				if parse == None:
					print("Trying 3rd regex")
					parse = re.search(r"(.+) - (\d{2})x(\d{2})",name)
					fixedName = parse.group(1) + " - S" + parse.group(2) + "E" + parse.group(3)
					parse = re.search(r"(.+) - (S\d{2}E\d{2})",fixedName)

				if parse:	
					showName = parse.group(1).replace("."," ")
					epcode = parse.group(2)
					
					try:
						f = open(folderPath+sub,'r')
						newSub = f.read()
						newSub = newSub.replace("'","")
						c.execute("update bigtable set srt = (?) where epcode = (?) and showname = (?)",[newSub,epcode,showName])
					except:
						print("failure:",epcode)
						f = open(folderPath+sub,'r',encoding='latin-1')
						newSub = f.read()
						newSub = newSub.replace("'","")
						c.execute("update bigtable set srt = (?) where epcode = (?) and showname = (?)",[newSub,epcode,showName])
					
				else:
					print("No regex match for",name)

	conn.commit()

#:sout=#transcode{vcodec=hevc,vb=500,venc=x264{profile=baseline},scale=0.5}:http{dst=:8082/go.mkv} :sout-all :sout-keep
class tvShow:

	def __init__(self,name,path,dbName):
		self.dbName = dbName
		self.pathBuilder(path)
		

	def pathBuilder(self,showFolder):

		absolutes = []		
		conn = sqlite3.connect(self.dbName)
		c = conn.cursor()

		srt = 'None'
		epcode = ''
		length = 0
		path = ''
		showName = ''
		walk = os.walk(showFolder)

		for root, dirs, files in walk:
			for video in files:
				name, extension = os.path.splitext(video)

				filepath = root + "/" + video
				#Following REGEX matches epcode as group 2 for both S01E01-E02 and S01E01 - S01E02
				try:
					parse = re.search(r"^.+\/(.+?) - (S\d{2}E\d{2}(-E\d{2}| - S\d{2}E\d{2}|)) - (.+)",filepath)
					showName = parse.group(1)
					epcode = parse.group(2)
					print("PROCESSING:",showName,epcode)
				except:
					print("Non episode detected")

				#First, Try to rip from mkv
				srt = 1
				if extension == ".mkv":
					srt = ripSub(filepath)
				#else, try subdownloader
				if srt == 1:
					srt = subtitle_downloader.sub_fetcher(filepath)	

				try:
					c.execute("INSERT INTO bigtable VALUES (?,?,?,?,?)",[srt,epcode,length,filepath,showName])
				except:
					print("Error inserting SRT into table. SRT already exists")

		conn.commit()
		conn.close()

#attempts to rip first sub track of supplied file. Returns 1 on failure.
def ripSub(filename):

	devnull = open(os.devnull, 'w')

	try:
		out = subprocess.check_call(["ffmpeg","-i",filename,"-map","0:s:0","tmp.srt","-y"],stdout=open(os.devnull,'w'),stderr=open(os.devnull,'w'))
		f = open("tmp.srt",'r',encoding='utf-8')
		newSub = f.read()
		newSub = newSub.replace("'","")
		print("Srt Extracted from",filename)
		return newSub

	except:
		print("srt extraction failed")
		return 1
	
def rebuildSearchTable(conn):

	sqlbatch(conn,[
			"DROP TABLE if exists searchable;",
			"CREATE VIRTUAL TABLE searchable USING fts4(srt,epcode,length,paths,showname);",
			"INSERT INTO searchable SELECT srt,epcode,length,paths,showname FROM bigtable;"
		])
	conn.commit()

def extractSubs(conn,dir,show,season = None):

	c = conn.cursor()
	c.execute(("SELECT paths,srt FROM bigtable WHERE showname = (?)"),[show])
	if c:
		results = c.fetchall()
		for path,srt in results:			
			parse = re.search(r".+\/(.+S\d{2}E\d{2}.+)\.",path)
			if parse:
				#some things are still being stored as binary instead plaintext in db
				try:
					title = parse.group(1)
					tmp = str(srt)
					if(tmp[0] == 'b'):
						with open(dir + title + ".srt", "wb") as sub:
							print("binary sub detected, converting..?")
							sub.write(srt)
					else:
						with open(dir + title + ".srt", "wb") as sub:
							sub.write(bytes(srt,"utf-8"))						
				except:
					pass

def printShows(conn):
	q = "SELECT distinct showName FROM searchable;"
	c = searchConfig.sqlRun(conn,q)
	matches = c.fetchall()
	print(matches)

def commandParse(arg,conn,paths):
	dbName = paths[0]
	print(arg)
	if arg[0] == 'display':
		printShows(conn)

	elif arg[0] == 'rebuild':
		rebuildSearchTable(conn)

	elif arg[0] == 'add':
		name = input("show name: ")
		path = input("path: ")
		temp = tvShow(name,path,dbName)

	elif arg[0] == 'import_srt':
		#name = input("show name: ")
		#path = input("subtitle path: ")
		temp = subUpdateFromFile(conn,paths[1])

	elif arg[0] == 'extract':
		name = input("show name: ")
		temp = extractSubs(conn,paths[1],name)


def main():

	signal.signal(signal.SIGINT, signal_handler)
	configPath = "clipFinderConfig.ini"

	try:
		myConfig = searchConfig.tvConfig(configPath)
	except:
		print("Cannot get configs?")


	rootdir = myConfig.rootdir
	dbName = myConfig.dbName
	extractSubs = myConfig.extractSubs

	try:
		conn = sqlite3.connect(dbName)
	except:
		print("error connecting to db")
		conn = False

	searchConfig.sqlRun(conn,'''CREATE TABLE if not exists bigtable (
	srt TEXT,
	epcode TEXT,
	length NUMBER,
	paths INTEGER,
	showname TEXT)''')

	#futurama = tvShow("futurama","/mnt/f/Videos/futurama",dbName)
	#rebuildSearchTable(conn)

	while conn:
		term = input("$-$> ")
		term = term.split()
		commandParse(term,conn,[dbName,extractSubs])


	#
	#subUpdateFromFile("/mnt/c/Users/Avery/Desktop/Futurama aux subs/")

	#rebuildSearchTable(conn)

	conn.close()

main()