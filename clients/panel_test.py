# load up the libraries
import panel as pn
import pandas as pd
import altair as alt
from altair_transform import extract_data
import Robogame as rg
import time,json
import networkx as nx
import traceback

# we want to use bootstrap/template, tell Panel to load up what we need
pn.extension(design='bootstrap')

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

game = None

def update():
    try:
        global game, static_text, network_view, tree_view, info_view, hints_view
        gt = game.getGameTime()
        network_view.object = game.getNetwork()
        tree_view.object = game.getTree()
        info_view.object = game.getRobotInfo()
        hints_view.object = game.getHints()

        static_text.value = "Time left: " + str(gt['unitsleft'])
    except:
        print(traceback.format_exc())

def go_clicked(event):
    try:
        global game, network, tree, info, hints
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
        game = rg.Robogame(uname,server=server,port=int(port))
        readResp = game.setReady()
        if ('Error' in readResp):
            static_text.value = "Error: "+str(readResp)
            go_button.disabled = False
            return
        

        while(True):
            gametime = game.getGameTime()
            
            if ('Error' in gametime):
                if (gametime['Error'] == 'Game not started'):
                    static_text.value = "Game not started yet, waiting"
                    time.sleep(1)
                    continue
                else:
                    static_text.value = "Error: "+str(gametime)
                    break

            timetogo = gametime['gamestarttime_secs'] - gametime['servertime_secs']
            if (timetogo <= 0):
                static_text.value = "Let's go!"
                break
            static_text.value = "waiting to launch... game will start in " + str(int(timetogo))
            time.sleep(1) # sleep 1 second at a time, wait for the game to start

        # run a check every 5 seconds
        cb = pn.state.add_periodic_callback(update, 5000, timeout=60000)
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

grid = pn.GridBox(ncols=2,nrows=2)
grid.append(network_view)
grid.append(tree_view)
grid.append(info_view)
grid.append(hints_view)

template.main.append(grid)



template.servable()