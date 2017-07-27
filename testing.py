

#Separates timecodes from srts
def testsplit(srt):
	timecodes = []
	regex = r"(\d{1})\n(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})"

	try:
		result = re.finditer(regex,srt)
	except:
		return False

	for each in result:
		timecodes.append(each.group(2))
		
	srt = re.sub('(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})\n', '', srt)

	newgetSceneTime(srt,350,1,timecodes)

#modified to get timecodes from timeCodeList instead of within srts
def newgetSceneTime(srt, index, preamble,timeCodeList):
	# This regex matches reversed SRT lines
	regex = r"(?m)(^\d+)$"
	try:
		result = re.finditer(regex, srt[index::-1])
	except:
		return False

	for scene in range(preamble):
		try:
			timeCodeIndex = next(result)
		except:
			print("No more scenes to preamble")

	timeCodeIndex = timeCodeIndex.group(1)   
	#############################################
	regex = r"(\d{2}):(\d{2}):(\d{2}),(\d{3}) --> \d{2}:\d{2}:\d{2},\d{3}"

	try:
		timecode = re.finditer(regex,timeCodeList[int(timeCodeIndex) - 1])
	except:
		pass
	
	timecode = next(timecode)

	hours = int(timecode.group(1))
	minutes = int(timecode.group(2))
	seconds = int(timecode.group(3))
	milliseconds = int(timecode.group(4))

	print(timeCodeIndex)
	print(hours,minutes,seconds,milliseconds)
	return hours*3600 + minutes*60 + seconds - 0