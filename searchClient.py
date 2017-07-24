
# Avery VanKirk 2017
# tv show clip searcher
import sqlite3
import os
import sys
import re
import subprocess
import signal

import searchConfig

def signal_handler(signal, frame):
	print('\nctrl+c detectd, exiting')
	sys.exit(0)
	
#takes a srt as string, searches for timecodes backward from supplied index position
#Set preamble to number of subtitle lines you want to play ahead of your search term
def getSceneTime(srt,index,preamble,secondsOffset = 0):
	#This regex matches reversed SRT lines
	regex = r"\d{3},\d{2}:\d{2}:\d{2} >-- (\d{3}),(\d{2}):(\d{2}):(\d{2})"
	try:
		result = re.finditer(regex,srt[index::-1])
	except:
		return False

	for scene in range(preamble):
		try:
			timecode = next(result)
		except:
			print("No more scenes to preamble")

	hours = int(timecode.group(4)[::-1])
	minutes = int(timecode.group(3)[::-1])
	seconds = int(timecode.group(2)[::-1])
	milliseconds = int(timecode.group(1)[::-1])

	return hours*3600 + minutes*60 + seconds - secondsOffset

	
def VLC(vlc,path,timeIndex,platform):

	try:
		#print("Launching",path,"\n")
		if platform == 'mixed':
			os.chdir("/mnt/c/Users") #chdir to suppress 'unable to translate working directory message'
			parse = re.search(r"(\/mnt\/(.))",path)
			driveLetter = parse.group(2)
			driveLetter = driveLetter.upper() + ":"						
			videoPath = path.replace(parse.group(1),driveLetter)
			#print(videoPath)
			videoPath = videoPath.replace("/",'''\\''')	
		command = '"' + vlc + '" "' + videoPath + '" --start-time=' + str(timeIndex)
		print("final command:",command)
		subprocess.call(command,shell=True)
	except:
		print("Error launching VLC")
		print(command)


class matches:

	def __init__(self,matchlist):
		self.matchlist = matchlist

	def __str__(self):
		return str(self.matchlist)

	def getChoice(self,choice):
		path = self.matchlist[choice][3]
		pos = int(self.matchlist[choice][4].split()[2])
		srt = self.matchlist[choice][1].replace("'","")
		timeIndex = getSceneTime(srt,pos,1)
		return path,timeIndex,srt

	def length(self):
		return len(self.matchlist)

	def print(self):
		print("\nEpisodes Matches:\n-----")
		for i,hit in enumerate(self.matchlist):
			print(str(i)+") ",end="")
			print(hit[5],hit[0],end="")
			try:
				parse = re.search(r".+\/.+S\d{2}E\d{2}(.+)\.",hit[3])
				print(parse.group(1))
			except:
				print(hit[3])
		print("-----")



def nearSearch(keywords,conn):

	nsearch = "SELECT epcode,srt,length,paths,offsets(searchable),showName FROM searchable WHERE searchable MATCH '"
	count = 1
	for word in keywords:
		nsearch = nsearch + '' '"''' + word
		if count < len(keywords):
			nsearch = nsearch + '" NEAR/2 '
		count = count + 1
	nsearch = nsearch + '\"\''
	c = searchConfig.sqlRun(conn,nsearch)
	tmatches = matches(c.fetchall())
	return tmatches

def main():

	signal.signal(signal.SIGINT, signal_handler)

	configPath = "clipFinderConfig.ini"
	myConfig = searchConfig.tvConfig(configPath)
	vlc = myConfig.vlc
	rootdir = myConfig.rootdir
	dbName = myConfig.dbName
	platform = myConfig.platform

	try:
		conn = sqlite3.connect(dbName)
	except:
		print("error connecting to db")
		conn = False

	while conn:

		try:			
			keywords = input("Enter a search term: ").split()
			matches = nearSearch(keywords,conn)

			if matches:
				matches.print()
				if(matches.length()>1):
					choice = int(input("Type digit for desired episode and press enter: "))
					if(choice <= matches.length()):
						path,timeIndex,srt = matches.getChoice(choice)
				else:
					path,timeIndex,srt = matches.getChoice(0)
				VLC(vlc,path,int(timeIndex),platform)
			else:
				print("No matches.\n")
			
		except SystemExit:
			conn.close()
			sys.exit(0)
		except:
			print("A vague error has occurred")

main()