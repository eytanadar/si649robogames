# si649robogames -- Client files

There are a number of client files that you can use to get started. 

You can run as many clients simultaneously as you want. So if your team has different parts of the dashboard, that will work (e.g., one person is working on network data and the other works on the parts). You will have to decide how to synchronize your guesses if you do this (e.g., one person can submit them). You can also test your dashboards by having two people on your team connect as different teams (see the example in the server directory)

## Simple Guess Interface (HTML)

We've created a page through which you can submit your guesses and keep track of how your team is doing. To run this, load up a webserver (e.g., ```python -m http.server``` in your directory) and then point your browser to http://localhost:8000/gamepage.html (assuming your server is on port 8000). You will see a very simple interface that will allow you to enter your match details (server location, port, and your team secret). Once the game gets going you can enter your guesses. As soon as you type something in and leave the cell, your guess will be submitted. Clicking on column names will sort by that column.

## API Libraries

There are two API library files, one for Python (```Robogame.py```) and one for Javascript (```Robogame.js```). You can see them in use in ```Example.ipynb``` (or ```streamlit_test.py```) and ```example.html```.

## Example Dashboard (Jupyter)

Load up Example.ipynb in jupyter notebook for an example dashboard (covered in the video). 

Before you run this, you'll need to install some packages:

```conda install networkx flask flask-cors requests scipy```

## Example Dashboard (Streamlit)

Run ```streamlit run streamlit_test.py``` for an example dashboard in Streamlit. You can modify this file to do more. Right now it just keeps getting the hacker's data and visualizing it.

## Example Dashboard (HTML)

Run ```python -m http.server``` to get a local webserver running (probably on port 8000). Point your browser there (e.g., http://localhost:8000/example.html). This file shows how to build a dashboard using web components (e.g., D3)

## Example Simulation (Jupyter)

If you look at ```Simulation.ipynb``` you will see how to write a basic simulator to try different strategies. It's really dumb at the moment, but you can play with this.

## Example Communicative Vis (Jupyter)

In ```PostGameAnalysis.ipynb``` you will find an example of how to do an anlysis of the log data produces after a match has completed.

