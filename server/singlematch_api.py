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
import Config

app = flask.Flask(__name__)
app.config["DEBUG"] = True
CORS(app)

configs = {}

def getConfig(req_obj):
	return[configs.values()[0]]

@app.route('/', methods=['GET'])
def home():
    return "<h1>Robogame Server</h1>"

@app.route('/singlematch_api/v1/resources/network', methods=['POST'])
def api_network():
	try:
		config = getConfig(request.get_json())
		config.updateWinners()

		if (config.isGameDone()):
			return(jsonify({"Error":"Game completed"}))

		return(config.getSocialnet())
	except:
		e = sys.exc_info()[0]
		traceback.print_exc() 
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

@app.route('/singlematch_api/v1/resources/gamedebug', methods=['POST'])
def api_gamedebug():
	try:
		config = getConfig(request.get_json())
		print("got debug request")
		if (config.getDebugMode()):
			config.updateWinners()
			reqtime = config.getCurrentRuntime(roundint=True)
			config.populateHintArrays(reqtime)
			#print(config['betlog'])
			return(json.dumps(config.getRep(), cls=NpEncoder))
			#return({})
		else:
			return({})
	except:
		e = sys.exc_info()[0]
		traceback.print_exc() 
		return(jsonify({"Error":str(e)}))


@app.route('/singlematch_api/v1/resources/tree', methods=['POST'])
def api_tree():
	try:
		config = getConfig(request.get_json())
		config.updateWinners()

		if (config.isGameDone()):
			return(jsonify({"Error":"Game completed"}))
		
		return(config.getGenealogy())
	except:
		e = sys.exc_info()[0]
		traceback.print_exc() 
		return(jsonify({"Error":str(e)}))

@app.route('/singlematch_api/v1/resources/gametime', methods=['POST'])
def api_gametime():
	try:
		config = getConfig(request.get_json())
		config.updateWinners()

		if (not config.hasGameStated()):
			return(jsonify({"Error":"Game not started"}))

		if (config.isGameDone()):
			return(jsonify({"Error":"Game completed"}))

		else:
			ft = config.getCurrentRuntime()
			fl= 100-ft
			if (ft < 0):
				ft = 0
				fl = 100
			w = {"servertime_secs":time.time(),"gamestarttime_secs":config['gamestarttime'],
				"gameendtime_secs":config['gameendtime'],"unitsleft":fl,"curtime":ft}
			return(jsonify(w))
	except:
		#print(e.exc_info())
		e = sys.exc_info()[0]
		traceback.print_exc() 
		return(jsonify({"Error":str(e)}))

@app.route('/singlematch_api/v1/resources/robotinfo', methods=['POST'])
def api_robotinfo():
	try:
		config = getConfig(request.get_json())
		config.updateWinners()
		req_data = getTeam(request.get_json())
		
		robotdata = config.getRobotData()

		toret = robotdata[['id','name','expires','winner','Productivity']]

		if ('Error' not in req_data):
			# we have a team, let's give them their current bets
			toret['bets'] = -1
			bets = config.getBets(req_data['Team'])

			for id in np.arange(0,100):
				toret.at[id,'bets'] = bets[id]

		ft = config.getCurrentRuntime()
		toret.loc[(toret.expires >= ft),'Productivity'] = np.NaN
		#print(toret)
		return(toret.to_json(orient="records"))
	except:
		e = sys.exc_info()[0]
		traceback.print_exc() 
		return(jsonify({"Error":str(e)}))
	#return(jsonify({"Result":"OK"}))



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



@app.route('/singlematch_api/v1/resources/setinterestbots', methods=['POST'])
def api_setinterestbots():
	try:

		config = getConfig(request.get_json())
		config.updateWinners()

		req_data = getTeam(request.get_json())
		if ('Error' in req_data):
			return(jsonify({"Error":req_data['Error']}))

		
		if (config.isGameDone()):
			return(jsonify({"Error":"Game completed"}))

		interest = []
		curtime = config.getCurrentRuntime(roundint=True)
		if 'Bots' in req_data:
			for b in req_data['Bots']:
				interest.append(int(b))


		config.setBotInterest(req_data['Team'],curtime,interest)

		config.populateInterestArrays(curtime)

		
		return(jsonify({"Result":"OK"}))
	except:
		e = sys.exc_info()[0]
		traceback.print_exc() 
		return(jsonify({"Error":str(e)}))

@app.route('/singlematch_api/v1/resources/setinterestparts', methods=['POST'])
def api_setinterestparts():
	try:
		config = getConfig(request.get_json())
		config.updateWinners()

		req_data = getTeam(request.get_json())
		if ('Error' in req_data):
			return(jsonify({"Error":req_data['Error']}))

		
		if (config.isGameDone()):
			return(jsonify({"Error":"Game completed"}))
		

		interest = []
		curtime = config.getCurrentRuntime(roundint=True)
		if 'Parts' in req_data:
			for b in req_data['Parts']:
				interest.append(b)


		config.setPartInterest(req_data['Team'],curtime,interest)
		config.populateInterestArrays(curtime)
		
		return(jsonify({"Result":"OK"}))
	except:
		e = sys.exc_info()[0]
		traceback.print_exc() 
		return(jsonify({"Error":str(e)}))

@app.route('/singlematch_api/v1/resources/setbets', methods=['POST'])
def api_setbets():
	try:
		config = getConfig(request.get_json())
		config.updateWinners()

		req_data = getTeam(request.get_json())
		if ('Error' in req_data):
			return(jsonify({"Error":req_data['Error']}))

		
		if (config.isGameDone()):
			return(jsonify({"Error":"Game completed"}))

		bets = None
		if (req_data['Team'] == 1):
			bets = config['team1_bets']
		elif (req_data['Team'] == 2):
			bets = config['team2_bets']
		newbets = req_data['Bets']
		curtime = config.getCurrentRuntime()
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
						config.addToBetLog(curtime,req_data['Team'],int(b),newbets[b])

		config.setBets(req_data['Team'],bets)

		return(jsonify({"Result":"OK"}))
	except:
		e = sys.exc_info()[0]
		traceback.print_exc() 
		#print(str(e))
		return(jsonify({"Error":str(e)}))


@app.route('/singlematch_api/v1/resources/gethints', methods=['POST'])
def api_gethints():
	try:
		config = getConfig(request.get_json())
		config.updateWinners()

		req_data = getTeam(request.get_json())
		if ('Error' in req_data):
			return(jsonify({"Error":req_data['Error']}))

		if (config.isGameDone()):
			return(jsonify({"Error":"Game completed"}))

		reqtime = getCurrentRuntime(roundint=True)
		# populate the hints array
		config.populateHintArrays(reqtime)

		team = 0

		hintstart = config.getLastHintTime(req_data['Team'])

		if ('hintstart' in req_data):
			if (int(req_data['hintstart']) != -1):
				hintstart = int(req_data['hintstart'])

		if (hintstart > reqtime):
			hintstart = reqtime

		p = config.getBotHints(req_data['Team'],hintstart,reqtime)
		r = config.getPartHints(req_data['Team'],hintstart,reqtime)
		config.setLastHintTime(req_data['Team'],reqtime)

		return(jsonify({"parts":r,"predictions":p,"hintstart":hintstart,"hintend":reqtime}))

	except:
		e = sys.exc_info()[0]
		traceback.print_exc() 
		return(jsonify({"Error":str(e)}))

@app.route('/singlematch_api/v1/resources/setready', methods=['POST'])
def api_setready():
	try:
		config = getConfig(request.get_json())
		config.updateWinners()

		req_data = getTeam(request.get_json())
		if ('Error' in req_data):
			return(jsonify({"Error":req_data['Error']}))
	
		if (config.isGameDone()):
			return(jsonify({"Error":"Game completed"}))

		if (config.hasGameStated()):
			return(jsonify({"Error":"Game already started"}))
		
		config.setReady(req_data['Team'])

		return(jsonify({"Result":"OK"}))
	except:
		e = sys.exc_info()[0]
		traceback.print_exc() 
		return(jsonify({"Error":str(e)}))


def init_argparse() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		usage="%(prog)s [OPTION] [gameid]...",
		description="run th server"
	)
	
	parser.add_argument('gameid')
	parser.add_argument("-s", "--simulated", help="play a simulated player two", 
		action='store_true')
	parser.add_argument("-t1s", "--team1secret", help="secret for team 1, default is random")
	parser.add_argument("-t2s", "--team2secret", help="secret for team 2, default is random")
	parser.add_argument("-d", "--directory", help="directory for game files, default is cwd", 
		default="./")
	parser.add_argument("-m", "--matchsave", help="filename for the log of the game, default is a random uuid")
	parser.add_argument("-nl","--nolog", help="don't save a log for this match",action='store_true')
	return parser

parser = init_argparse()
args = parser.parse_args()

c = Config.Config(args.gameid,team1secret=args.team1secret,team2secret=args.team2secret,
	simulated=args.simulated,nolog=args.nolog,matchsave=args.matchsave,
	directory=args.directory)

configs[args.gameid] = c

print("Single playoff mode")
print("Game id:",c.getGameID())
print("Team 1 Secret:",c.getSecret(1))
print("Team 2 Secret:",c.getSecret(2), "Simulated: ",c.isSimulated())
app.run()
