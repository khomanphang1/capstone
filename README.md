# What is it


# Running the Application Locally
1. Install [LTspice](https://www.analog.com/en/design-center/design-tools-and-calculators/ltspice-simulator.html)
    * Under Tools -> Control Panel -> Netlist Options, check the *Convert 'µ' to 'u'* option - this forces LTspice to encode its output as UTF-8.
    
2. Install [Python 3](https://www.python.org/downloads/). This application was only tested on Python 3.9.x.

3. Install [MongoDB](https://www.mongodb.com/try/download/community). 

4. Clone this project to your local development workspace. Then, under un `pip install -r requirements.txt` under the project root.

5. Start your local MongoDB server using the `mongod` executable.

6. Run `server.py` to start your development server.

7. Go to [localhost:5000/app/landing.html](localhost:5000/app/landing.html) for the landing page of the web app. To start the appliction, output the required circuits files from LTspice and upload them. 

# Architecture

This application is divided into the following modules:

`circuit_parser.py`

Parses LTspice netlists and operating point analysis logs to create small-signal circuit graphs. Currently, only a small subset of LTspice netlist component types and syntaxes are supported. Sub-class `circuit_parser.Component` to add parsing logic for additional component types. 

While ths small-signal circuit is only used an intermediary result in this application, you can visualize the graph object that represents the circuit using one of the two options:
 1. Draw them on-screen using `NetworkX` and `matplotlib`, or
 2. output the small-signal circuit as a netlist file using `Circuit.netlist`

`dpi.py`

Performs driving-point impedance analysis on a small-signal circuit, and outputs a signal-flow graph (SFG). 

`mason.py`

Applies Mason's gain formula to calculate the transfer function and loop gain of an SFG.

`/ltspice2svg`

A thin wrapper around the [ltspice2svg](https://github.com/harshvinay752/ltspice2svg) package. It converts .asc schematic files to a web-friendly SVG format.

`db.py`

Performs CRUD operations against a local mongodb instance, or if environment variable DB_URI is specified, the production MongoDB instance URI in the cloud. Responsible for serializing and de-serializing SFGs, gain expressions, etc.

`server.py`

Run a development server on port 5000. When in production, Heroku does not launch the development server, but runs the app in waitress instead (see Procfile).


