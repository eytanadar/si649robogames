# load up the libraries
import panel as pn
import pandas as pd
import altair as alt
from altair_transform import extract_data
import Robogame as rg
import time,json
import networkx as nx
import traceback
from collections import defaultdict
import pprint

# we want to use bootstrap/template, tell Panel to load up what we need
pn.extension(design='bootstrap')
pn.extension('vega')

# load up the data
def getFrame():
    # load up the two datasets, one for Marvel and one for DC    
    return(pd.DataFrame())

default_username = "bob"
default_server = "127.0.0.1"
default_port = "5000"

username_input= pn.widgets.TextInput(name='Username:', placeholder=default_username)
servername_input= pn.widgets.TextInput(name='Server', placeholder='127.0.0.1')
port_input= pn.widgets.TextInput(name='Port', placeholder='5000')
go_button = pn.widgets.Button(name='Run', button_type='primary')
static_text = pn.widgets.StaticText(name='State', value='Hit go to start')

sidecol = pn.Column()
sidecol.append(static_text)
sidecol.append(username_input)
sidecol.append(servername_input)
sidecol.append(port_input)
sidecol.append(go_button)

network = None
tree = None
info = None
hints = None
predDict = None

game = None

predIdKey = "id"
predTimeKey = "time"
predValueKey = "value"

def update():
    try:
        global game, static_text, network_view, tree_view, info_view, hints_view, predDict, robo_time_chart, robo_expiry_sorted
        robo_expiry_sorted.object = getRoboSorted()
        gt = game.getGameTime()
        network_view.object = game.getNetwork()
        tree_view.object = game.getTree()
        info_view.object = game.getRobotInfo()
        hints_view.object = game.getHints()
        allPred = game.getAllPredictionHints()
        
        predDict = defaultdict(lambda: defaultdict(list))
        for pred in allPred:
            roboId = pred[predIdKey]
            predTime = pred[predTimeKey]
            value = pred[predValueKey]
            predDict[roboId][predTimeKey].append(predTime)
            predDict[roboId][predValueKey].append(value)
        
        hints_view.object = predDict
        robo_time_chart.object = getTimeChart()

        static_text.value = "Current time: " + str(100 - gt['unitsleft'])
    except:
        print(traceback.format_exc())

def go_clicked(event):
    try:
        global game, network, tree, info, hints, robo_expiry_sorted
        go_button.disabled = True
        uname = username_input.value
        if (uname == ""):
            uname = default_username
        server = servername_input.value
        if (server == ""):
            server = default_server
        port = port_input.value
        if (port == ""):
            port = default_port

        print(uname, server, port)
        game = rg.Robogame("bob",server=server,port=int(port))
        game.setReady()
        

        while(True):
            gametime = game.getGameTime()
            
            if ('Error' in gametime):
                static_text.value = "Error: "+str(gametime)
                break

            timetogo = gametime['gamestarttime_secs'] - gametime['servertime_secs']
            if (timetogo <= 0):
                static_text.value = "Let's go!"
                break
            static_text.value = "waiting to launch... game will start in " + str(int(timetogo))
            time.sleep(1) # sleep 1 second at a time, wait for the game to start

        # run a check every 5 seconds
        robo_expiry_sorted.object = getRoboSorted()
        cb = pn.state.add_periodic_callback(update, 5000, timeout=600000)
    except:
        #print(traceback.format_exc())
        return

go_button.on_click(go_clicked)

template = pn.template.BootstrapTemplate(
    title='Robogames Demo',
    sidebar=sidecol,
)

network_view = pn.pane.JSON({"message":"waiting for game to start"})
tree_view = pn.pane.JSON({"message":"waiting for game to start"})
info_view = pn.pane.DataFrame()
hints_view = pn.pane.JSON({"message":"waiting for game to start"})
robo_time_chart = pn.pane.Vega(None)
robo_expiry_sorted = pn.pane.Vega(None)
curr_selected_robot = 1

maincol = pn.Column()

def getTimeChart():
    global curr_selected_robot, predDict
    # print(f"\n\n\n textInput = {textInput} \n\n\n")
    
    # try:
    #     robotId = int(textInput)
    # except:
    #     return 'Please enter an integer'
    
    robotId = curr_selected_robot
        
    global predDict
    if predDict is None:
        return None
    if robotId not in predDict:
        return "No data found for this robot yet"

    print(predDict[robotId])
    
    robo_df = pd.DataFrame.from_dict(predDict[robotId])
    points = alt.Chart(robo_df).mark_circle(color="red").encode(
        x=alt.X('time:Q', scale=alt.Scale(domain=[0, 100])),
        y=alt.Y('value:Q', scale=alt.Scale(domain=[0, 100])),
        tooltip=['time', 'value']
    ).properties(
        title=f"Robot {robotId}'s data"
    )

    line = alt.Chart(robo_df).mark_line(interpolate="monotone").encode(
        x='time:Q',
        y='value:Q'
    )

    robotInfo = game.getRobotInfo()
    currRobot = robotInfo[robotInfo['id'] == robotId]
    expiry = currRobot["expires"].iloc[0]
    expiryLine = alt.Chart(pd.DataFrame({"x": [expiry]})).mark_rule().encode(
        x="x:Q"
    )

    return line + points + expiryLine

def updateCurrSelected(textInput):
    global curr_selected_robot, robo_time_chart
    try:
        curr_selected_robot = int(textInput)
        robo_time_chart.object = getTimeChart()
        return "Updated!"
    except:
        return "Please enter an integer"

def getFilteredRobotRecords(sortedRobotRecords, robotDegrees, currTime = 20, numCount = 20):
    filteredRobotRecords = []
    currRank = 1
    currCount = 0
    for robot in sortedRobotRecords:
        if robot["id"] >= 100:
            break
        if robot["expires"] < currTime:
            continue
        robot["rank"] = currRank
        robot["degree"] = robotDegrees[robot["id"]]
        currRank += 1
        filteredRobotRecords.append(robot)
        currCount += 1
        if currCount >= numCount:
            break
        
    return filteredRobotRecords

def getRoboSorted():
    global game
    if game is None:
        return None
    robots = game.getRobotInfo()
    network = game.getNetwork()
    socialnet = nx.node_link_graph(network)
    robotDegrees = {node:val for (node, val) in socialnet.degree()}
    robotRecords = robots.to_dict("records")
    sortedRobotRecords = sorted(robotRecords, key=lambda x:x["expires"])
    
    gt = game.getGameTime()
    currTime = 100 - gt['unitsleft']
    
    filteredRobotRecords = getFilteredRobotRecords(sortedRobotRecords, robotDegrees, currTime=currTime)
    
    robotDfWithRank = pd.DataFrame.from_records(filteredRobotRecords)
    return alt.Chart(robotDfWithRank).mark_circle(size=100).encode(
        alt.X('rank', axis=None),
        size="degree",
        tooltip=['name', 'expires', 'rank', "id", "degree"]
    ).properties(
        width=800
    )

robotIdInput = pn.widgets.TextInput(placeholder="Robot ID")

rowChart = pn.Row(pn.bind(updateCurrSelected, robotIdInput))


grid = pn.GridBox(ncols=2,nrows=3)
grid.append(network_view)
grid.append(tree_view)
grid.append(info_view)
grid.append(hints_view)

# timechart = getTimeChart(3)
maincol.append(robo_time_chart)
maincol.append(rowChart)
maincol.append(robotIdInput)
maincol.append("Upcoming robot and its popularity in the social network:")
maincol.append(robo_expiry_sorted)
maincol.append(grid)

template.main.append(maincol)



template.servable()