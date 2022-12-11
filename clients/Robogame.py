import requests as rq
import json
import pandas as pd

class Robogame:

	server = None
	port = None
	gameid = None
	secret = None
	network = None
	tree = None
	predictionHints = None
	partHints = None
	multiplayer = False

	def __init__(self,secret,server="127.0.0.1",port=5000,gameid='default',multiplayer=False):
		"""creates a new Robogame object. Requires your team secret (as defined by server). 
		server defaults to localhost and port to 5000"""
		self.server = server
		self.port = port
		self.secret = secret
		self.gameid = gameid
		self.predictionHints = []
		self.partHints = []
		self.multiplayer = multiplayer

	def getUrl(self,path):
		"""internal method to construct a url give a path"""
		return("http://"+self.server+":"+str(self.port)+path)

	def getDebug(self):
		"""returns a json format version of the social network"""
		payload = {'secret':self.secret,'gameid':self.gameid}
		r = rq.post(self.getUrl("/api/v1/resources/gamedebug"), json = payload)
		return(r.json())

	def getNetwork(self):
		"""returns a json format version of the social network"""
		if (self.network != None):
			return(self.network)
		payload = {'secret':self.secret,'gameid':self.gameid}
		r = rq.post(self.getUrl("/api/v1/resources/network"), json = payload)
		self.network = r.json()
		return(self.network)

	def getTree(self):
		"""returns a json format version of the genealogy"""
		if (self.tree != None):
			return(self.tree)
		payload = {'secret':self.secret,'gameid':self.gameid}
		r = rq.post(self.getUrl("/api/v1/resources/tree"), json = payload)
		self.tree = r.json()
		return(self.tree)

	def getGameTime(self):
		"""returns a game time object that includes the current time in planet X units, what the server 
		thinks the time is (in seconds), when the game starts and when it ends (all in seconds)"""
		payload = {'secret':self.secret,'gameid':self.gameid}
		r = rq.post(self.getUrl("/api/v1/resources/gametime"), json = payload)
		return(r.json())

	def getRobotInfo(self,js=False):
		"""returns the current game details as a dataframe with an option to get it as json with js=True.
		Data includes the id, name, expiration, productivity (for expired robots), team affiliation"""
		payload = {'secret':self.secret,'gameid':self.gameid}
		r = rq.post(self.getUrl("/api/v1/resources/robotinfo"), json = payload)
		#print(r.json())
		if js:
			return(r.json())
		else:
			return(pd.read_json(json.dumps(r.json()),orient='records'))

	def setRobotInterest(self,interest):
		"""accepts an array of robot ids to indicate an interest to the hacker, an empty list [] means interest in all"""
		payload = {'secret':self.secret,'Bots':interest,'gameid':self.gameid}
		r = rq.post(self.getUrl("/api/v1/resources/setinterestbots"), json = payload)
		return(r.json())

	def setPartInterest(self,interest):
		"""accepts an array of robot parts to indicate an interest to the hacker, an empty list [] means interest in all"""
		payload = {'secret':self.secret,'Parts':interest,'gameid':self.gameid}
		r = rq.post(self.getUrl("/api/v1/resources/setinterestparts"), json = payload)
		return(r.json())

	def setBets(self,bets):
		"""accepts the bets as a dictionary, {id1:bet1,id2:bet2,...}"""
		payload = {'secret':self.secret,'Bets':bets,'gameid':self.gameid}
		r = rq.post(self.getUrl("/api/v1/resources/setbets"), json = payload)
		return(r.json())

	def getHints(self,hintstart=-1):
		"""get the latest hints from the hacker"""
		if (self.multiplayer & (hintstart == -1)):
			hintstart = 0   # we want to force the retrieval of all hints from the start

		payload = {'secret':self.secret,'hintstart':int(hintstart),'gameid':self.gameid}
		r = rq.post(self.getUrl("/api/v1/resources/gethints"), json = payload)
		rjson = r.json()
		if 'predictions' in rjson:
			for hint in rjson['predictions']:
				if (hint not in self.predictionHints):
					self.predictionHints.append(hint)
		if 'parts' in rjson:
			for hint in rjson['parts']:
				if (hint not in self.partHints):
					self.partHints.append(hint)
		return(r.json())

	def getAllPredictionHints(self):
		"""get all the prediction hints since the start"""
		# update the hints
		return(self.predictionHints)

	def getAllPartHints(self):
		"""get all the part hints since the start"""
		return(self.partHints)

	def setReady(self):
		"""tell the server we're ready to go"""
		payload = {'secret':self.secret}
		r = rq.post(self.getUrl("/api/v1/resources/setready"), json = payload)
		return(r.json())

