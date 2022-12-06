# si649robogames -- Server files

To run a game on your local machine, you'll need to run the server in this directory. There are also 3 sample "matches" that you can play.

## Install

Before you run this, you'll need to install some packages:

```conda install networkx flask flask-cors requests scipy```

## Run

To start a server do:

```python api.py [-d directoryforgame] [-s] [-t1s T1Secret] [-t1n T1name] [-t2s T2Secret] [-t2n T2name] [-m matchsavefile] gameid```

gameid is the the prefix of all the game files (the examples we gave you are examplematch1, examplematch2, examplematch3.

```
-d/--directory is an optional directory. For example, we put the examplematch1 files in the example1 directory
-s/--simulated tells us whether to simulate team 2
-t1s/--team1secret is Team 1's secret. If you don't specify this, the server will give you one
-t2s/--team1secret is Team 2's secret. This is ignored if you use -s. If you don't specify this, the server will give you one
-m/--matchasave is a log file to save the game in, a random log name will be used if you don't specify this
-nl/--nolog don't save a log file for this match (will override -m option if both are included)
-t1n/--team1name name for team 1 (default is 'team 1')
-t2n/--team2name name for team 2 (default is 'team 2')

```


## Example

```python api.py -d ./example1 -s -t1s bob -t1n bobsTeam examplematch1```

We're using the examplematch1 files in the example1 directory, simulating player 2 and team 1's secret is 'bob' (that's us and our team name is bobsTeam). Team 2 will just bet 50 for everything.

If you want to play against yourself, you can specify two secrets and just connect two clients. For example, you can create alice and bob to play example2:

```python api.py -d ./example2 -s -t1s bob -t1n bobsTeam -t2s alice -t2n alicesTeam examplematch2```

The game log will get saved automatically for you, but you can also specify where it goes (e.g., experiment.json):

```python api.py -d ./example2 -s -t1s bob -t2s alice -m experiment.json examplematch2```

## Example Directories

Each of example1-12 contains a few files:

* The json file for an example game (e.g., bobvalice.json)
* The csv file containing all the match details (in a real game you won't have this). But the columns are robot id, t_X where X is the time (so t_5 will be a column representing the output of the robots in the guessing game at time 5), expires (when the robot wants you to guess by), Productivity (robot's productivity), and then all the parts columns
* the socialnet (gexf and json format) the network file for the match (see the example clients for how to parse these)
* the tree (gexf and json format) the tree file for the match (see the example clients for how to parse these)



