# What is it


# Running the Application Locally
1. Install [LTspice](https://www.analog.com/en/design-center/design-tools-and-calculators/ltspice-simulator.html).
    * Under Tools -> Control Panel -> Netlist Options, check the *Convert 'µ' to 'u'* option - this forces LTspice to encode its output files as UTF-8. This application is only compatible with UTF-8-encoded files.
    
2. Install [Python 3](https://www.python.org/downloads/). This application was tested on Python 3.9.x.

3. Install [MongoDB](https://www.mongodb.com/try/download/community). 

4. Clone this project to your local workspace. Then, run `pip install -r requirements.txt` under the project root.

5. Start your local development MongoDB server using the `mongod` executable.

6. Run `server.py` to start your local development server.

7. Go to [localhost:5000/app/landing.html](localhost:5000/app/landing.html) for the landing page of the web app. To start 
using the web app, you must upload the following LTspice files:
    * .cir netlist file
    * (optional) .asc schematic file, if you wish to render the circuit schematic
    * (optional) .log operating point analysis log file - you won't need this if your circuit is already in 
        small-signal form

# Architecture

This application is divided into the following modules:

`circuit_parser.py`

Parses LTspice netlists and operating point analysis log files to create small-signal circuits - these are represented as
[NetworkX](https://networkx.org/documentation/stable/index.html) multigraphs. 

Currently, the parser supports only a small subset of LTspice component types and syntaxes. The module can be extended 
by subclassing `Component`, and overridng parsing methods for new component types. 

Note that the application only uses small-signal circuits as an intermediary step towards computing the signal-flow graph 
(SFG). For debugging and verification purposes, small-signal circuit multigraphs produced by this module can be 
visualized in one of two ways:

1. Render them on-screen using matplotlib (for more details, consult NetworkX library documentation)
2. Print the small-signal circuit to a netlist file using the `Circuit.netlist` property

`dpi.py`

Performs driving-point impedance analysis on a small-signal circuit, and outputs a signal-flow graph (SFG). 
*Todo: should add more details in this section* 

`mason.py`

Applies [Mason's gain formula](https://en.wikipedia.org/wiki/Mason%27s_gain_formula) to calculate the transfer function 
and loop gain of an SFG (the SFG is represented as a NetworkX digraph). The module uses NetworkX's implementation of 
[Johnson's algorithm](https://www.cs.tufts.edu/comp/150GA/homeworks/hw1/Johnson%2075.PDF) to find all simple cycles within 
the SFG (one of the main steps in the formula), and is therefore relatively efficient. 

`/ltspice2svg`

A thin wrapper around the [ltspice2svg](https://github.com/harshvinay752/ltspice2svg) package. It converts .asc schematic 
files to a web-friendly SVG format that can be displayed in the browser. The wrapper is needed because the original
package can only be run as __main__, and won't work correctly when imported. The wrapper solves this issue by invoking
it as a subprocess. 

`db.py`

Performs operations against a mongodb instance including:
    * creating and storing circuit documents 
    * serializing and de-serializing compiled transfer functions (these are used to compute bode plot point. They are
        expensive to compile so are cached in the database).
    * modifying circuit documents
    
    
This module should probably be re-factored because it embodies too much un-related logic. For example:
* the create circuit method also invokes the circuit parser, when it's better to pass in an already parsed circuit
* the module compiles symbolic transfer functions into faster numerical ones internally. This logic should probably be 
    separated out.
 
 
When deployed to Heroku, if the environment variable DB_URI is specified, the production MongoDB instance URI in the cloud. 

`server.py`

Runs a development server on port 5000. 
    * Front-end web pages are served from the static ./public directory.
    * An exhaustive list of API routes are available in api_specification.html. Some example functionalities provided are:
        * Update the component values in a circuit
        * Create a new circuit
        * Plot the gain and phase of a circuit's transfer function
        * Find the transfer function expression of a circuit
        
Note that when deployed to Heroku, the application uses Procfile to launch a production-quality waitress server instead of 
flasks's built-in development server.

