import os
import sys
import configparser

class tvConfig:

	def __init__(self,configPath):
		self.vlc,self.rootdir,self.dbName,self.extractSubs = self.loadConfig(configPath)

	def loadConfig(self,configPath):

		if not os.path.isfile(configPath):
			print("ConfigFile not found, creating.")
			config = configparser.ConfigParser()
			config['PATHS'] =	{'db': '','videoDir': '','VLC': ''}
			config['SETTINGS'] = {'PLATFORM': ''}

			try:
				with open(configPath,'w') as configFile:
					config.write(configFile)
			except:
				print('Could not create config file')

		if os.path.isfile(configPath):
			try:
				config = configparser.ConfigParser()
				config.read(configPath)
				rootdir = config['PATHS']['videoDir']
				dbName = config['PATHS']['db']
				vlc = config['PATHS']['VLC']
				extractSubs = config['PATHS']['subExport']
			except:
				pass

		invalid = False
		if not os.path.isfile(dbName):
			print("database not found.")
			invalid = True
		if not os.path.isfile(vlc):
			print("VLC not found.")
			invalid = True
		if not os.path.isdir(rootdir):
			print("Invalid path for video folder.")
			invalid = True
		if invalid:
			print("Check your config! exiting...")
			#sys.exit(1)

		return vlc,rootdir,dbName,extractSubs

def sqlRun(conn,command,args = None):

	c = conn.cursor()
	if args == None:
		try:
			c.execute(command)
			return c
		except:
			print("Error:",command)
			return None
	else:
		try:
			c.execute(command,[].append(args))
			return c
		except:
			print("Error:",command)
			return None