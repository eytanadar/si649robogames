import flask
from flask import request, jsonify
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
import threading

mutex = threading.Lock()
mutex.acquire()

app = flask.Flask(__name__)
app.config["DEBUG"] = True
CORS(app)

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
		  'team1_ready':-1,
		  'team2_ready':-1,
		  # team bets
		  'team1_bets':[],
		  'team2_bets':[],
		  # log of bets
		  'betlog':[],

		  # log of win reasons
		  'winreasons':[],
		  # last hint request time
		  'team1_lasthint':0,
		  'team2_lasthint':0,

		  # for simulation mode
		  'debug':False}



socialnet = None
genealogy = None

robotadata = None

quantProps = ['Astrogation Buffer Length','InfoCore Size',
	'AutoTerrain Tread Count','Polarity Sinks',
	'Cranial Uplink Bandwidth','Repulsorlift Motor HP',
	'Sonoreceptors']
nomProps = ['Arakyd Vocabulator Model','Axial Piston Model','Nanochip Model']
allProps = quantProps + nomProps

timecolumns = []
for i in np.arange(1,101):
	timecolumns.append("t_"+str(i))
	config['team1_bets'].append(-1)
	config['team2_bets'].append(-1)
	config['winreasons'].append({'winner':-2,'reason':-2})

# create an empty array of what team was interested in what when
# and what hints we gave them when
for t in ['team1_hints_parts','team1_hints_bots','team2_hints_parts','team2_hints_bots',
		'team1_int_parts','team1_int_bots','team2_int_parts','team2_int_bots']:
		x = [[]]
		for i in np.arange(1,101):
			x.append(None)
		config[t] = x

mutex.release()

def saveGameState():
	try:
		if (config['matchfile'] != None):
			tosave = copy.copy(config)
			del tosave['genealogy']
			del tosave['socialnet']
			del tosave['team1secret']
			del tosave['team2secret']
			with open(config['matchfile'], 'w') as outfile:
				json.dump(tosave, outfile, cls=NpEncoder)
			
	except:
		traceback.print_exc() 

def updateWinners(curtime=None):
	if (curtime == None):
		curtime = getCurrentRuntime()

	if (curtime <= 0):
		# game hasn't started
		return

	if (curtime >= 100):
		# check if there are any bots left to determine
		if (len(robotdata[(robotdata.winner == -2)]) == 0):
			return


	robotdata['winner'] = robotdata['winner'].values

	t1bets = config['team1_bets']
	t2bets = config['team2_bets']

	# find undeclared robots that have expired
	todeclare = robotdata[(robotdata.winner == -2) & (robotdata.expires <= curtime)].sort_values(['expires','id'])
	for row in todeclare.iterrows():
		#print(row)
		row = row[1]
		rid = row['id']
		expired = int(row['expires'])
		correct = int(row['t_'+str(int(expired))])

		robotdata.at[rid,'winner'] = -1

		#print(rid,"exp:",expired,"cor:",correct,"t1:",t1bets[rid],"t2:",t2bets[rid])
		
		if ((t1bets[rid] == -1) and (t2bets[rid] == -1)):
			# no one wants this robot
			#print("no team claims")
			config['winreasons'][rid] = {'winner':-1,'reason':-1}
			robotdata.at[rid,'winner'] = -1
			continue

		if (t1bets[rid] == -1):
			# team 1 doesn't want this robot, assign to team 2
			#print("team 1 wins by default")
			config['winreasons'][rid] = {'winner':2,'reason':-1}

			robotdata.at[rid,'winner'] = 2
			continue

		if (t2bets[rid] == -1):
			#print("team 2 wins by default")
			config['winreasons'][rid] = {'winner':1,'reason':-1}
			# team 2 doesn't want this robot, assign to team 1
			robotdata.at[rid,'winner'] = 1
			continue

		dist1 = abs(t1bets[rid] - correct)
		dist2 = abs(t2bets[rid] - correct)
		#print("\t",dist1,dist2)

		if ((dist1 == dist2) or ((dist1 < 10) and (dist2 < 10))):
			# do social net part
			neighbors = [n for n in socialnet.neighbors(rid)]

			# determine which neighbors have been declared
			neighrow = robotdata[robotdata['id'].isin(neighbors)][['id','winner']]

			neighrow = neighrow[neighrow.winner > -1]
			

			neighbors = neighrow['id'].values
			neighdec = neighrow['winner'].values
			neighpop = [socialnet.degree[n] for n in neighbors]
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
				config['winreasons'][rid] = {'winner':1,'reason':1}
				robotdata.at[rid,'winner'] = 1
				continue
			elif (v2 > v1):
				#print("team 2 wins, by neighbors")
				config['winreasons'][rid] = {'winner':2,'reason':1}
				robotdata.at[rid,'winner'] = 2
				continue
			else:
				w = np.random.choice([1,2], 1)[0]
				#print("tie on neighbors, random flip, goes to ",w)
				robotdata.at[rid,'winner'] = w
				config['winreasons'][rid] = {'winner':w,'reason':1.5}
				continue

		if (dist1 < dist2):
			# team 1 closer
			#print("team 1 wins, closer")
			config['winreasons'][rid] = {'winner':1,'reason':2}
			robotdata.at[rid,'winner'] = 1
			continue
		elif (dist2 < dist1):
			# team 2 closer
			#print("team 2 wins, closer")
			config['winreasons'][rid] = {'winner':2,'reason':2}
			robotdata.at[rid,'winner'] = 2
			continue
		else:
			# tie, just flip a coin
			w = np.random.choice([1,2], 1)[0]
			#print("tie on neighbors, random flip, goes to ",w)
			robotdata.at[rid,'winner'] = w
			config['winreasons'][rid] = {'winner':w,'reason':2.5}
			continue

		#print(rid,expired,correct)

	robotdata['winner'] = robotdata['winner'].values

	robotdata.loc[robotdata['winner'] == 1, 'winningTeam'] = config['team1name']
	robotdata.loc[robotdata['winner'] == 2, 'winningTeam'] = config['team2name']
	robotdata.loc[robotdata['winner'] == -1, 'winningTeam'] = 'Undeclared'

	saveGameState()
	#print(robotdata[robotdata.winner != -2])



@app.route('/', methods=['GET'])
def home():
    return "<h1>Robogame Server</h1>"

@app.route('/api/v1/resources/network', methods=['POST'])
def api_network():
	try:
		mutex.acquire()
		updateWinners()
		mutex.release()
		
		if (('gameendtime' in config) and (time.time() > config['gameendtime'])):
			return(jsonify({"Error":"Game completed"}))

		return(config['socialnet'])
	except:
		e = sys.exc_info()[0]
		traceback.print_exc()
		if mutex.locked():
			mutex.release()
		return(jsonify({"Error":str(e)}))

class NpEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, np.integer):
			return int(obj)
		elif isinstance(obj, np.floating):
			return float(obj)
		elif isinstance(obj, np.ndarray):
			return obj.tolist()
		else:
			return super(NpEncoder, self).default(obj)

@app.route('/api/v1/resources/gamedebug', methods=['POST'])
def api_gamedebug():
	try:
		mutex.acquire()
		print("got debug request")
		if (config['debug']):
			updateWinners()
			reqtime = getCurrentRuntime(roundint=True)
			populateHintArrays(reqtime)
			#print(config['betlog'])
			mutex.release()
			return(json.dumps(config, cls=NpEncoder))
			#return({})
		else:
			return({})
	except:
		e = sys.exc_info()[0]
		traceback.print_exc()
		if mutex.locked():
			mutex.release()
		return(jsonify({"Error":str(e)}))


@app.route('/api/v1/resources/tree', methods=['POST'])
def api_tree():
	try:
		mutex.acquire()
		updateWinners()
		mutex.release()
		

		if (('gameendtime' in config) and (time.time() > config['gameendtime'])):
			return(jsonify({"Error":"Game completed"}))
		
		return(config['genealogy'])
	except:
		e = sys.exc_info()[0]
		traceback.print_exc()
		if mutex.locked():
			mutex.release()
		return(jsonify({"Error":str(e)}))

def getCurrentRuntime(roundint=False):
	if ('gamestarttime' not in config):
		return(-1)
	elif (roundint):
		return(round((time.time() - config['gamestarttime']) / 6))
	else:
		return(round((time.time() - config['gamestarttime']) / 6,2))

@app.route('/api/v1/resources/gametime', methods=['POST'])
def api_gametime():
	try:
		mutex.acquire()
		updateWinners()
		mutex.release()
		

		if (not 'gamestarttime' in config):
			return(jsonify({"Error":"Game not started",
							"team1name":config["team1name"],
							"team2name":config["team2name"]}))
		if (('gameendtime' in config) and (time.time() > config['gameendtime'])):
			return(jsonify({"Error":"Game completed",
							"team1name":config["team1name"],
							"team2name":config["team2name"]}))
		else:
			ft = getCurrentRuntime()
			fl= 100-ft
			if (ft < 0):
				ft = 0
				fl = 100
			if ('gamestarttime' in config):
				w = {"servertime_secs":time.time(),"gamestarttime_secs":config['gamestarttime'],
					"gameendtime_secs":config['gameendtime'],"unitsleft":fl,"curtime":ft,
					"team1name":config["team1name"],
					"team2name":config["team2name"]}
			return(jsonify(w))
	except:
		#print(e.exc_info())
		e = sys.exc_info()[0]
		traceback.print_exc()
		if mutex.locked():
			mutex.release()
		return(jsonify({"Error":str(e)}))

@app.route('/api/v1/resources/robotinfo', methods=['POST'])
def api_robotinfo():
	try:
		mutex.acquire()
		updateWinners()
		mutex.release()

		req_data = request.get_json()
		req_data = getTeam(req_data)
		toret = robotdata[['id','name','expires','winner','Productivity','winningTeam']]
		if ('Error' not in req_data):
			# we have a team, let's give them their current bets
			toret['bets'] = -1
			bets = []
			if (req_data['Team'] == 1):
				bets =config['team1_bets']
			elif (req_data['Team'] == 2):
				bets =config['team2_bets']

			for id in np.arange(0,100):
				toret.at[id,'bets'] = bets[id]

		ft = getCurrentRuntime()
		toret.loc[(toret.expires >= ft),'Productivity'] = np.NaN
		#print(toret)
		return(toret.to_json(orient="records"))
	except:
		e = sys.exc_info()[0]
		traceback.print_exc()
		if mutex.locked():
			mutex.release()
		return(jsonify({"Error":str(e)}))
	#return(jsonify({"Result":"OK"}))

def getExpiration(rid):
	e = robotdata[robotdata.id == rid]['expires']
	return(e.values[0])

def getTeam(_r):
	_r['Validated'] = 'False'
	if 'secret' in _r:
		secret = str(_r['secret'])
		if (secret == config['team1secret']):
			_r['Team'] = 1
			_r['Validated'] = 'True'
		elif (secret == config['team2secret']):
			_r['Team'] = 2
			_r['Validated'] = 'True'
		else:
			_r['Error'] = "Team secret doesn't match any team"
	else:
		_r['Error'] = "No team secret"
	return(_r) 

def populateInterestArrays(curtime):
	for a in ['team1_int_bots','team2_int_bots','team1_int_parts','team2_int_parts']:
		tempint = []
		for z in np.arange(1,curtime):
			if config[a][z] == None:
				# unpopulated, updated
				config[a][z] = tempint
			else:
				# populated, use as tempint
				tempint = config[a][z]

@app.route('/api/v1/resources/setinterestbots', methods=['POST'])
def api_setinterestbots():
	try:

		mutex.acquire()
		updateWinners()
		

		req_data = request.get_json()
		req_data = getTeam(req_data)
		if ('Error' in req_data):
			mutex.release()			
			return(jsonify({"Error":req_data['Error']}))

		
		if (('gameendtime' in config) and (time.time() > config['gameendtime'])):
			mutex.release()
			return(jsonify({"Error":"Game completed"}))

		interest = []
		curtime = getCurrentRuntime(roundint=True)
		if 'Bots' in req_data:
			for b in req_data['Bots']:
				interest.append(int(b))

		if (req_data['Team'] == 1):
			# set the current time's interest
			config['team1_int_bots'][curtime] = interest

		elif (req_data['Team'] == 2):
			# set the current time's interest
			config['team2_int_bots'][curtime] = interest

		populateInterestArrays(curtime)

		mutex.release()

		return(jsonify({"Result":"OK"}))
	except:
		e = sys.exc_info()[0]
		traceback.print_exc()
		if mutex.locked():
			mutex.release()
		return(jsonify({"Error":str(e)}))

@app.route('/api/v1/resources/setinterestparts', methods=['POST'])
def api_setinterestparts():
	try:

		mutex.acquire()
		updateWinners()

		req_data = request.get_json()
		req_data = getTeam(req_data)
		if ('Error' in req_data):
			mutex.release()
			return(jsonify({"Error":req_data['Error']}))

		
		if (('gameendtime' in config) and (time.time() > config['gameendtime'])):
			mutex.release()
			return(jsonify({"Error":"Game completed"}))
		

		interest = []
		curtime = getCurrentRuntime(roundint=True)
		if 'Parts' in req_data:
			for b in req_data['Parts']:
				interest.append(b)


		if (req_data['Team'] == 1):
			# set the current time's interest
			config['team1_int_parts'][curtime] = interest

		elif (req_data['Team'] == 2):
			# set the current time's interest
			config['team2_int_parts'][curtime] = interest

		#print(config['team1_int_parts'])
		populateInterestArrays(curtime)
		mutex.release()
		return(jsonify({"Result":"OK"}))
	except:
		e = sys.exc_info()[0]
		traceback.print_exc()
		if mutex.locked():
			mutex.release()
		return(jsonify({"Error":str(e)}))

@app.route('/api/v1/resources/setbets', methods=['POST'])
def api_setbets():
	try:
		mutex.acquire()
		updateWinners()

		req_data = request.get_json()
		req_data = getTeam(req_data)
		if ('Error' in req_data):
			mutex.release()
			return(jsonify({"Error":req_data['Error']}))

		
		if (('gameendtime' in config) and (time.time() > config['gameendtime'])):
			mutex.release()
			return(jsonify({"Error":"Game completed"}))

		bets = None
		if (req_data['Team'] == 1):
			bets = config['team1_bets']
		elif (req_data['Team'] == 2):
			bets = config['team2_bets']
		newbets = req_data['Bets']
		curtime = getCurrentRuntime()
		#print(req_data)
		for b in newbets.keys():
			if (int(b) <= len(bets)):
				expires = getExpiration(int(b))
				#print(b,newbets[b],expires)
				if (expires <= curtime):
					# robot already expired
					continue
				if ((newbets[b] >= -1) and (newbets[b] <= 100)):
					if (bets[int(b)] != int(newbets[b])):
						bets[int(b)] = int(newbets[b])
						#print("update",int(b),newbets[b])
						config['betlog'].append({'time':curtime,'betby':req_data['Team'],'beton':int(b),'value':newbets[b]})
		if (req_data['Team'] == 1):
			config['team1_bets'] = bets
		elif (req_data['Team'] == 2):
			config['team2_bets'] = bets
		mutex.release()
		return(jsonify({"Result":"OK"}))
	except:
		e = sys.exc_info()[0]
		traceback.print_exc() 
		#print(str(e))
		if mutex.locked():
			mutex.release()
		return(jsonify({"Error":str(e)}))


def populateHintArrays(curtime):
	# populate the interests array up to and including the current time
	populateInterestArrays(curtime+1)

	for a in ['team1_hints_bots','team2_hints_bots']:
		# go through the hints we've already supposed to have given
		# and populate the array if we haven't done it
		for z in np.arange(1,curtime+1):
			if (config[a][z] == None):
				# haven't generated a hint for this time point yet
				roboHints = []
				if (a == 'team1_hints_bots'):
					# got hints for team 1
					config[a][z] = getBotHintSet(config['team1_int_bots'][z])
				else:
					config[a][z] = getBotHintSet(config['team2_int_bots'][z])

	for a in ['team1_hints_parts','team2_hints_parts']:
		# go through the hints we've already supposed to have given
		# and populate the array if we haven't done it
		for z in np.arange(1,curtime+1):
			if (config[a][z] == None):
				# haven't generated a hint for this time point yet
				roboHints = []
				if (a == 'team1_hints_parts'):
					# got hints for team 1
					config[a][z] = getPartHintSet(config['team1_int_parts'][z])
				else:
					config[a][z] = getPartHintSet(config['team2_int_parts'][z])


def getPartHintSet(interests):
	toret = []

	possi = robotdata[robotdata.id < 100]

	if (len(interests) == 0):
		# user hasn't expressed interests,
		# all data is possible
		interests = allProps

	s = possi.sample(6)
	j = 1
	validcol = allProps
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

def getBotHintSet(interests):
	toret = []
	# pick 5 rows at random
	s = robotdata.sample(5)
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
	s = robotdata
	if (len(interests) > 0):
		# if player expressed interest
		# pick those robots
		s = robotdata[robotdata['id'].isin(interests)]
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


def getHints(hintlist,start,end):
	toret = []
	for i in np.arange(start,end+1):
		toret = toret + hintlist[i]
	return(toret)

@app.route('/api/v1/resources/gethints', methods=['POST'])
def api_gethints():
	try:
		mutex.acquire()
		updateWinners()

		req_data = request.get_json()
		req_data = getTeam(req_data)
		if ('Error' in req_data):
			mutex.release()
			return(jsonify({"Error":req_data['Error']}))

		if (('gameendtime' in config) and (time.time() > config['gameendtime'])):
			mutex.release()
			return(jsonify({"Error":"Game completed"}))

		reqtime = getCurrentRuntime(roundint=True)
		# populate the hints array
		populateHintArrays(reqtime)

		team = 0

		if (req_data['Team'] == 1):
			team = 1
			hintstart = config['team1_lasthint']
		else:
			team = 2
			hintstart = config['team2_lasthint']

		if ('hintstart' in req_data):
			if (int(req_data['hintstart']) != -1):
				hintstart = int(req_data['hintstart'])

		if (hintstart > reqtime):
			hintstart = reqtime

		# half of samples should be random, half from interest list
		p = []
		r = []

		if (team == 1):
			p = getHints(config['team1_hints_bots'],hintstart,reqtime)
			r = getHints(config['team1_hints_parts'],hintstart,reqtime)
			config['team1_lasthint'] = reqtime
		else:
			p = getHints(config['team2_hints_bots'],hintstart,reqtime)
			r = getHints(config['team2_hints_parts'],hintstart,reqtime)
			config['team2_lasthint'] = reqtime

		mutex.release()
		return(jsonify({"parts":r,"predictions":p,"hintstart":hintstart,"hintend":reqtime}))

	except:
		e = sys.exc_info()[0]
		traceback.print_exc()
		if mutex.locked():
			mutex.release()
		return(jsonify({"Error":str(e)}))

@app.route('/api/v1/resources/setready', methods=['POST'])
def api_setready():
	try:
		mutex.acquire()
		updateWinners()

		req_data = request.get_json()
		req_data = getTeam(req_data)
		if ('Error' in req_data):
			mutex.release()
			return(jsonify({"Error":req_data['Error']}))

		
		if (('gameendtime' in config) and (time.time() > config['gameendtime'])):
			mutex.release()
			return(jsonify({"Error":"Game completed"}))

		if ('gamestarttime' in config):
			mutex.release()
			return(jsonify({"Error":"Game already started"}))
		

		if (req_data['Team'] == 1):
			config['team1_ready'] = 1
		if (req_data['Team'] == 2):
			config['team2_ready']= 1

		print(req_data)
		print(config['team1_ready'],config['team2_ready'])
		if ((config['team1_ready'] == 1) and (config['team2_ready'] == 1)):
			startGame()
		mutex.release()
		return(jsonify({"Result":"OK"}))
	except:
		e = sys.exc_info()[0]
		traceback.print_exc()
		if mutex.locked():
			mutex.release()
		return(jsonify({"Error":str(e)}))

def startGame():
	start = time.time() + 10
	end = start + 600
	config['gamestarttime'] = start
	config['gameendtime'] = end
	return(start)

def simulatedSecondPlayer():
	config['debug'] = True
	config['team2_ready']= 1
	bets = config['team2_bets']
	for i in np.arange(0,100):
		config['betlog'].append({'time':0,'betby':2,'beton':i,'value':50})
		bets[i] = 50
	config['team2_bets'] = bets
	if ((config['team1_ready'] == 1) and (config['team2_ready'] == 1)):
		config['starttime'] = startGame()

def init_argparse() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		usage="%(prog)s [OPTION] [gameid]...",
		description="run th server"
	)
	
	parser.add_argument('gameid')
	parser.add_argument("-s", "--simulated", help="play a simulated player two", 
		action='store_true')
	parser.add_argument("-t1n", "--team1name", help="team 1's name, default is 'Team 1'")
	parser.add_argument("-t2n", "--team2name", help="team 2's name, default is 'Team 2'")
	parser.add_argument("-t1s", "--team1secret", help="secret for team 1, default is random")
	parser.add_argument("-t2s", "--team2secret", help="secret for team 2, default is random")
	parser.add_argument("-d", "--directory", help="directory for game files, default is cwd", 
		default="./")
	parser.add_argument("-m", "--matchsave", help="filename for the log of the game, default is a random uuid")
	parser.add_argument("-nl","--nolog", help="don't save a log for this match",action='store_true')
	return parser

mutex.acquire()
parser = init_argparse()
args = parser.parse_args()




if (args.team1secret != None):
	config['team1secret'] = args.team1secret

if (args.team2secret != None):
	config['team2secret'] = args.team2secret

if (args.team1name != None):
	config['team1name'] = args.team1name
else:
	config['team1name'] = "Team 1"

if (args.team2name != None):
	config['team2name'] = args.team2name
else:
	config['team2name'] = "Team 2"

if (config['team1secret'] == config['team2secret']):
	print("Error! Team 1 and Team 2 secrets must be different")
	sys.exit(0)


print("Team 1 Secret: " + config['team1secret'])


if (args.simulated):
	print("Team 2 will be simulated")
	config['team2name'] = "Simulated"
	simulatedSecondPlayer()
else:
	print("Team 2 Secret: " + config['team2secret'])

config['gameid'] = args.gameid

if (args.nolog):
	print("No log will be saved for this match")
	config['matchfile'] = None
else:
	if (args.matchsave == None):
		config['matchfile'] = str(uuid.uuid4()) + "." + config['gameid'] + ".json"
	else: 
		config['matchfile'] = args.matchsave

with open(args.directory + "/" + args.gameid+".socialnet.json") as json_file:
	data = json.load(json_file)
	socialnet = nx.node_link_graph(data)
	config['socialnet'] = data

with open(args.directory + "/" + args.gameid+".tree.json") as json_file:
	data = json.load(json_file)	
	genealogy = nx.tree_graph(data)
	config['genealogy'] = data

robotdata = pd.read_csv(args.directory + "/" + args.gameid+".robotdata.csv")
robotdata['winner'] = -2
robotdata['winningTeam'] = "Unassigned"

outf = open(args.directory + "/" + args.gameid+"",'w')

mutex.release()

app.run(host='0.0.0.0')
