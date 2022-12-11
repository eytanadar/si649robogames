import streamlit as st
import numpy as np
import time
import altair as alt
import pandas as pd
import numpy as np
import Robogame as rg
import collections

@st.cache(allow_output_mutation=True)
def prepGame():
    status.write("prepping game...")
    print('prepping game')
    game = rg.Robogame("bob")
    game.setReady()
    return(game)

@st.cache(ttl=3)
def getHintData():
    game.getHints()
    toReturn = pd.DataFrame(game.getAllPredictionHints())
    status.write("Getting hints, we now have "+str(len(toReturn))+" hints")
    return(toReturn)

# a container to hold the robots we're interested in
def checkbox_container():
    with st.expander("Robots to track:"):
        for i in np.arange(0,10):
            cols = st.columns(10)
            for j in np.arange(1,11):
                foo = i*10+j
                with cols[j-1]:
                    st.checkbox(str(foo),key='dynamic_checkbox_' + str(foo))
            
        
# helper to get a list of what's clicked on        
def get_selected_checkboxes():
    return [i.replace('dynamic_checkbox_','') for i in st.session_state.keys() if i.startswith('dynamic_checkbox_') and st.session_state[i]]

# status bar
status = st.empty()

# wait for both players to be ready
game = prepGame()
while(True):    
    gametime = game.getGameTime()
    timetogo = gametime['gamestarttime_secs'] - gametime['servertime_secs']
    
    if ('Error' in gametime):
        status.write("Error"+str(gametime))
        break
    if (timetogo <= 0):
        status.write("Let's go!")
        break
    status.write("waiting to launch... game will start in " + str(int(timetogo)))
    time.sleep(1) # sleep 1 second at a time, wait for the game to start

checkbox_container()
chart_row = st.empty()

robotInterests = []

while(True):
    time.sleep(2)
    currentInterests = list(get_selected_checkboxes())
    if collections.Counter(currentInterests) != collections.Counter(robotInterests):
        # only update if things have changed
        game.setRobotInterest(currentInterests)
        robotInterests = currentInterests
        print(list(get_selected_checkboxes()))

  
    t = getHintData()
    chrt = alt.Chart(t).mark_circle().encode(
            alt.X('time:Q',scale=alt.Scale(domain=(0, 100))),
            alt.Y('value:Q',scale=alt.Scale(domain=(0, 100)))
        )

    chart_row.altair_chart(chrt)
