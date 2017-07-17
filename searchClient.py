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
	
def VLC(vlc,path,timeIndex):

	try:
		os.chdir("/mnt/c/Users/Avery/")	
		videoPath = path.replace("/mnt/f","F:")
		videoPath = videoPath.replace("/",'''\\''')	
		command = '"' + vlc + '" "' + videoPath + '" --start-time=' + str(timeIndex)
		#print("final command:",command)
		subprocess.call(command,shell=True)
	except:
		print("Error launching VLC")
		print(command)


def main():

	signal.signal(signal.SIGINT, signal_handler)

	configPath = "clipFinderConfig.ini"
	myConfig = searchConfig.tvConfig(configPath)
	vlc = myConfig.vlc
	rootdir = myConfig.rootdir
	dbName = myConfig.dbName

	try:
		conn = sqlite3.connect(dbName)
	except:
		print("error connecting to db")
		conn = False

	while conn:

		try:
			nsearch = "SELECT epcode,srt,length,paths,offsets(searchable),showName FROM searchable WHERE searchable MATCH '"
			oterm = input("Enter a search term: ")
			term = oterm.split()
			count = 1
			for word in term:
				nsearch = nsearch + '' '"''' + word
				if count < len(term):
					nsearch = nsearch + '" NEAR/2 '
				count = count + 1

			nsearch = nsearch + '\"\''
			c = searchConfig.sqlRun(conn,nsearch)
			matches = c.fetchall()

			if matches:
				print("\nEpisodes Matches:\n-----")
				for i,hit in enumerate(matches):
					print(str(i)+") ",end="")

					print(hit[5],hit[0],end="")
					try:
						parse = re.search(r".+\/.+S\d{2}E\d{2}(.+)\.",hit[3])
						print(parse.group(1))
					except:
						print(hit[3])					

				print("-----")
				result = matches[0]
				epLength = int(result[2])
				path = result[3]
				pos = int(result[4].split()[2])
				t = result[1].replace("'","")
				total = len(t)

				if(len(matches)>1):
					choice = int(input("Type digit for desired episode and press enter: "))
					if(choice <= len(matches)):
						path = matches[choice][3]
						pos = int(matches[choice][4].split()[2])
						t = matches[choice][1].replace("'","")

				timeIndex = getSceneTime(t,pos,1)
				#print("Launching",path,"\n")
				VLC(vlc,path,int(timeIndex))
			else:
				print("No matches.\n")
			
		except SystemExit:
			conn.close()
			sys.exit(0)
		except:
			print("A vague error has occurred")

main()