import pandas as pd
import numpy as np
import argparse
import uuid
import sys
import networkx as nx
import json
import time
from flask_cors import CORS
import traceback
import copy

# define Python user-defined exceptions
class ConfigError(Exception):
    pass


class Config():

	quantProps = ['Astrogation Buffer Length','InfoCore Size',
		'AutoTerrain Tread Count','Polarity Sinks',
		'Cranial Uplink Bandwidth','Repulsorlift Motor HP',
		'Sonoreceptors']
	nomProps = ['Arakyd Vocabulator Model','Axial Piston Model','Nanochip Model']
	allProps = quantProps + nomProps

	config = {'team1secret':str(uuid.uuid4()),
			  'team2secret':str(uuid.uuid4()),

			  # what robots are they interested in
			  'team1_int_bots':[],
			  'team2_int_bots':[],
			  'team1_int_parts':[],
			  'team2_int_parts':[],

			  'team1_hints_bots':[],
			  'team2_hints_bots':[],
			  'team1_hints_parts':[],
			  'team2_hints_parts':[],
			  # pick a start time when both teams are ready 
			  'starttime':-1,
			  # team ready
			  'team1_ready':False,
			  'team2_ready':False,
			  # team bets
			  'team1_bets':[],
			  'team2_bets':[],
			  # log of bets
			  'betlog':[],
			  'team2simulated':False,
			  # log of win reasons
			  'winreasons':[],
			  # last hint request time
			  'team1_lasthint':0,
			  'team2_lasthint':0,

			  # for simulation mode
			  'debug':False}


	socialnet = None
	genealogy = None

	robotdata = None

	def __init__(self,gameid,team1secret=None,team2secret=None,nolog=False,
					matchsave=None,directory=".",simulated=False):
		for i in np.arange(1,101):
			self.config['team1_bets'].append(-1)
			self.config['team2_bets'].append(-1)
			self.config['winreasons'].append({'winner':-2,'reason':-2})


		# create an empty array of what team was interested in what when
		# and what hints we gave them when
		for t in ['team1_hints_parts','team1_hints_bots','team2_hints_parts','team2_hints_bots',
				'team1_int_parts','team1_int_bots','team2_int_parts','team2_int_bots']:
				x = [[]]
				for i in np.arange(1,101):
					x.append(None)
				self.config[t] = x

		if (team1secret != None):
			self.config['team1secret'] = team1secret

		if (team2secret != None):
			self.config['team2secret'] = team2secret


		if (self.config['team1secret'] == self.config['team2secret']):
			raise ConfigError("Both teams have the same secret")

		if (simulated):
			self.simulatedSecondPlayer()

		self.config['gameid'] = gameid

		if (nolog):
			self.config['matchfile'] = None
		else:
			if (matchsave == None):
				self.config['matchfile'] = str(uuid.uuid4()) + "." + self.config['gameid'] + ".json"
			else: 
				self.config['matchfile'] = matchsave

		with open(directory + "/" + gameid+".socialnet.json") as json_file:
			data = json.load(json_file)
			self.socialnet = nx.node_link_graph(data)
			self.config['socialnet'] = data

		with open(directory + "/" + gameid+".tree.json") as json_file:
			data = json.load(json_file)	
			self.genealogy = nx.tree_graph(data)
			self.config['genealogy'] = data

		self.robotdata = pd.read_csv(directory + "/" + gameid+".robotdata.csv")
		self.robotdata['winner'] = -2

	def addToBetLog(self,curtime,team,beton,betval):
		self.config['betlog'].append({'time':curtime,'betby':team,'beton':beton,'value':betval})

	def setReady(self,team):
		if (team == 1):
			self.config['team1_ready'] = True
		else:
			self.config['team2_ready'] = True

		if ((self.config['team1_ready'] == True) and (self.config['team2_ready'] == True)):
			self.startGame()

	def getBets(self,team):
		if (team == 1):
			return(self.config['team1_bets'])
		else:
			return(self.config['team2_bets'])

	def getLastHintTime(self,team):
		if (team == 1):
			return(self.config['team1_lasthint'])
		else:
			return(self.config['team2_lasthint'])


	def setBets(self,team,bets):
		if (team == 1):
			self.config['team1_bets'] = bets
		else:
			self.config['team2_bets'] = bets

	def isSimulated(self):
		return(self.config['team2simulated'])

	def getGameID(self):
		return(self.config['gameid'])

	def getSecret(self,team):
		if (team == 1):
			return(self.config['team1secret'])
		else:
			return(self.config['team2secret'])

	def getBotInterest(self,team):
		if (team == 1):
			return(self.config['team1_int_bots'])
		else:
			return(self.config['team2_int_bots'])

	def setBotInterest(self,team,curtime,interest):
		if (team == 1):
			self.config['team1_int_bots'][curtime] = interest
		else:
			self.config['team2_int_bots'][curtime] = interest

	def setPartInterest(self,team,curtime,interest):
		if (team == 1):
			self.config['team1_int_parts'][curtime] = interest
		else:
			self.config['team2_int_parts'][curtime] = interest


	def getPartInterest(self,team):
		if (team == 1):
			return(self.config['team1_int_parts'])
		else:
			return(self.config['team2_int_parts'])



	def getBotHints(self,team,start=None,end=None):
		hintlist = None
		if (team == 1):
			hintlist = self.config['team1_hints_bots']
		else:
			hintlist = self.config['team2_hints_bots']
		if ((start == None) or (end == None)):
			return(hintlist)
		toret = []
		for i in np.arange(start,end+1):
			toret = toret + hintlist[i]
		return(toret)

	def getPartHints(self,team,start=None,end=None):
		hintlist = None
		if (team == 1):
			hintlist = self.config['team1_hints_parts']
		else:
			hintlist = self.config['team2_hints_parts']
		if ((start == None) or (end == None)):
			return(hintlist)
		toret = []
		for i in np.arange(start,end+1):
			toret = toret + hintlist[i]
		return(toret)


	def getRep(self):
		return(self.config)

	def getRobotData(self):
		return(robotdata)

	def getConfigKey(self,key):
		return(self.config[key])

	def getSocialnet(self):
		return(self.config['socialnet'])

	def getGenealogy(self):
		return(self.config['genealogy'])

	def isGameDone(self):
		if (('gameendtime' in self.config) and (time.time() > self.config['gameendtime'])):
			return(True)
		return(False)

	def getDebugMode(self):
		return(self.config['debug'])

	def hasGameStarted(self):
		if ('gamestarttime' in config):
			return(True)

		return(False)

	def startGame(self):
		start = time.time() + 10
		end = start + 600
		config['gamestarttime'] = start
		config['gameendtime'] = end
		self.config['starttime'] = start

	def getExpiration(self,rid):
		e = self.robotdata[self.robotdata.id == rid]['expires']
		return(e.values[0])

	def simulatedSecondPlayer(self):
		self.config['debug'] = True
		self.config['team2simulated'] = True
		self.config['team2_ready']= True
		bets = self.config['team2_bets']
		for i in np.arange(0,100):
			self.config['betlog'].append({'time':0,'betby':2,'beton':i,'value':50})
			bets[i] = 50
		self.config['team2_bets'] = bets
		if ((self.config['team1_ready'] == True) and (self.config['team2_ready'] == True)):
			self.startGame()

	def saveGameState(self):
		try:
			if (self.config['matchfile'] != None):
				tosave = copy.copy(self.config)
				del tosave['genealogy']
				del tosave['socialnet']
				del tosave['team1secret']
				del tosave['team2secret']
				with open(config['matchfile'], 'w') as outfile:
					json.dump(tosave, outfile, cls=NpEncoder)
				
		except:
			traceback.print_exc() 

	def getCurrentRuntime(self,roundint=False):
		if ('gamestarttime' not in self.config):
			return(-1)
		elif (roundint):
			return(round((time.time() - self.config['gamestarttime']) / 6))
		else:
			return(round((time.time() - self.config['gamestarttime']) / 6,2))


	def updateWinners(self):
		
		curtime = self.getCurrentRuntime()

		if (curtime < 0):
			# game hasn't started
			return

		if (curtime >= 100):
			# check if there are any bots left to determine
			if (len(self.robotdata[(self.robotdata.winner == -2)]) == 0):
				return


		self.robotdata['winner'] = self.robotdata['winner'].values

		t1bets = self.config['team1_bets']
		t2bets = self.config['team2_bets']

		# find undeclared robots that have expired
		todeclare = self.robotdata[(self.robotdata.winner == -2) & 
									(self.robotdata.expires <= curtime)].sort_values(['expires','id'])
		for row in todeclare.iterrows():
			#print(row)
			row = row[1]
			rid = row['id']
			expired = int(row['expires'])
			correct = int(row['t_'+str(int(expired))])

			self.robotdata.at[rid,'winner'] = -1

			#print(rid,"exp:",expired,"cor:",correct,"t1:",t1bets[rid],"t2:",t2bets[rid])
			
			if ((t1bets[rid] == -1) and (t2bets[rid] == -1)):
				# no one wants this robot
				#print("no team claims")
				self.config['winreasons'][rid] = {'winner':-1,'reason':-1}
				self.robotdata.at[rid,'winner'] = -1
				continue

			if (t1bets[rid] == -1):
				# team 1 doesn't want this robot, assign to team 2
				#print("team 1 wins by default")
				self.config['winreasons'][rid] = {'winner':2,'reason':-1}

				self.robotdata.at[rid,'winner'] = 2
				continue

			if (t2bets[rid] == -1):
				#print("team 2 wins by default")
				self.config['winreasons'][rid] = {'winner':1,'reason':-1}
				# team 2 doesn't want this robot, assign to team 1
				self.robotdata.at[rid,'winner'] = 1
				continue

			dist1 = abs(t1bets[rid] - correct)
			dist2 = abs(t2bets[rid] - correct)
			#print("\t",dist1,dist2)

			if ((dist1 == dist2) or ((dist1 < 10) and (dist2 < 10))):
				# do social net part
				neighbors = [n for n in self.socialnet.neighbors(rid)]

				# determine which neighbors have been declared
				neighrow = self.robotdata[robotdata['id'].isin(neighbors)][['id','winner']]

				neighrow = neighrow[neighrow.winner > -1]
				

				neighbors = neighrow['id'].values
				neighdec = neighrow['winner'].values
				neighpop = [self.socialnet.degree[n] for n in neighbors]
				tot = sum(neighpop)
				neighpop = [n/tot for n in neighpop]
				v1 = 0
				v2 = 0
				for i in np.arange(0,len(neighbors)):
					if (neighdec[i] == 1):
						v1 = v1 + neighpop[i]
					else:
						v2 = v2 + neighpop[i]

				#print(v1,v2)
				if (v1 > v2):
					#print("team 1 wins, by neighbors")
					self.config['winreasons'][rid] = {'winner':1,'reason':1}
					self.robotdata.at[rid,'winner'] = 1
					continue
				elif (v2 > v1):
					#print("team 2 wins, by neighbors")
					self.config['winreasons'][rid] = {'winner':2,'reason':1}
					self.robotdata.at[rid,'winner'] = 2
					continue
				else:
					w = np.random.choice([1,2], 1)[0]
					#print("tie on neighbors, random flip, goes to ",w)
					self.robotdata.at[rid,'winner'] = w
					self.config['winreasons'][rid] = {'winner':w,'reason':1.5}
					continue

			if (dist1 < dist2):
				# team 1 closer
				#print("team 1 wins, closer")
				self.config['winreasons'][rid] = {'winner':1,'reason':2}
				self.robotdata.at[rid,'winner'] = 1
				continue
			elif (dist2 < dist1):
				# team 2 closer
				#print("team 2 wins, closer")
				self.config['winreasons'][rid] = {'winner':2,'reason':2}
				self.robotdata.at[rid,'winner'] = 2
				continue
			else:
				# tie, just flip a coin
				w = np.random.choice([1,2], 1)[0]
				#print("tie on neighbors, random flip, goes to ",w)
				self.robotdata.at[rid,'winner'] = w
				self.config['winreasons'][rid] = {'winner':w,'reason':2.5}
				continue

			#print(rid,expired,correct)

		self.robotdata['winner'] = self.robotdata['winner'].values
		self.saveGameState()

	def populateInterestArrays(self,curtime):
		for a in ['team1_int_bots','team2_int_bots','team1_int_parts','team2_int_parts']:
			tempint = []
			for z in np.arange(1,curtime):
				if self.config[a][z] == None:
					# unpopulated, updated
					self.config[a][z] = tempint
				else:
					# populated, use as tempint
					tempint = self.config[a][z]

	def populateHintArrays(self,curtime):
		# populate the interests array up to and including the current time
		self.populateInterestArrays(curtime+1)

		for a in ['team1_hints_bots','team2_hints_bots']:
			# go through the hints we've already supposed to have given
			# and populate the array if we haven't done it
			for z in np.arange(1,curtime+1):
				if (self.config[a][z] == None):
					# haven't generated a hint for this time point yet
					roboHints = []
					if (a == 'team1_hints_bots'):
						# got hints for team 1
						self.config[a][z] = self.getBotHintSet(self.config['team1_int_bots'][z])
					else:
						self.config[a][z] = self.getBotHintSet(self.config['team1_int_bots'][z])

		for a in ['team1_hints_parts','team2_hints_parts']:
			# go through the hints we've already supposed to have given
			# and populate the array if we haven't done it
			for z in np.arange(1,curtime+1):
				if (config[a][z] == None):
					# haven't generated a hint for this time point yet
					roboHints = []
					if (a == 'team1_hints_parts'):
						# got hints for team 1
						self.config[a][z] = self.getPartHintSet(self.config['team1_int_parts'][z])
					else:
						self.config[a][z] = self.getPartHintSet(self.config['team1_int_parts'][z])


	def getPartHintSet(self,interests):
		toret = []

		possi = self.robotdata[robotdata.id < 100]

		if (len(interests) == 0):
			# user hasn't expressed interests,
			# all data is possible
			interests = self.allProps

		s = possi.sample(6)
		j = 1
		validcol = self.allProps
		selection = np.random.choice(validcol, 3)
		selection = np.append(selection,np.random.choice(interests, 3))
		for row in s.iterrows():
			row = row[1]
			rid = row['id']
			randcol = selection[j-1]
			randval = row[randcol]
			d = {'id':rid,'column':randcol,'value':randval}
			toret.append(d)
			j = j + 1				
			#print(toret)

		return(toret)

	def getBotHintSet(self,interests):
		toret = []
		# pick 5 rows at random
		s = self.robotdata.sample(5)
		j = 0
		randcols = np.random.choice(timecolumns, 5)
		for row in s.iterrows():
			row = row[1]
			rid = row['id']
			randcol = randcols[j].replace("t_","")
			randval = row[randcols[j]]
			d = {'id':rid,'time':int(randcol),'value':randval}
			toret.append(d)
			j = j + 1

		j = 0 
		s = self.robotdata
		if (len(interests) > 1):
			# if player expressed interest
			# pick those robots
			s = self.robotdata[self.robotdata['id'].isin(interests)]
		j = 0
		s = s.sample(5,replace=True)
		randcols = np.random.choice(timecolumns, 5)
		for row in s.iterrows():
			row = row[1]
			rid = row['id']
			randcol = randcols[j].replace("t_","")
			randval = row[randcols[j]]
			d = {'id':rid,'time':int(randcol),'value':randval}
			toret.append(d)
			j = j + 1
		return(toret)


	def getHints(self,team,hintlist,start,end):
		toret = []
		for i in np.arange(start,end+1):
			toret = toret + hintlist[i]
		return(toret)
	