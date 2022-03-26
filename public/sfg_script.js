const baseUrl = window.location.origin;

const circuitId = sessionStorage.getItem('circuitId');

let [simplify_mode, node1, node2] = [false, null, null];


if (!circuitId) {
    window.location.replace('./landing.html');
}

var symbolic_flag = false //feature toggle
let current_data = null //session data
let edge_symbolic_label;

// Function to convert float to exponential
function expo(x, f) {
  return Number.parseFloat(x).toExponential(f);
}

function edge_helper(sample_data, flag) {
    let sfg_elements = JSON.parse(JSON.stringify(sample_data.sfg.elements))
    let edge_length = sample_data.sfg.elements.edges.length
    let sfg_edges = []
    edge_symbolic_label = new Array(edge_length)

    if (flag) {
        return;
        // for (i = 0; i < edge_length; i++) {
        //     let new_edge = JSON.parse(JSON.stringify(sample_data.sfg.elements.edges[i]))
        //     new_edge.data.weight = new_edge.data.weight.symbolic
        //     sfg_edges.push(new_edge)
        // }
    } else {
        for (i = 0; i < edge_length; i++) {
            let new_edge = JSON.parse(JSON.stringify(sample_data.sfg.elements.edges[i]))
            edge_symbolic_label[i] = new_edge.data.weight.symbolic
            //new_edge.data.weight = new_edge.data.weight.magnitude.toFixed(2)
            let magnitude = expo((new_edge.data.weight.magnitude), 2).toString()
            let phase = new_edge.data.weight.phase.toFixed(2).toString()
            let result = magnitude.concat("∠", phase);
            //new_edge.data.weight = expo((new_edge.data.weight.magnitude), 2)
            new_edge.data.weight = result
            sfg_edges.push(new_edge)
        }
    }
    sfg_elements.edges = JSON.parse(JSON.stringify(sfg_edges))
    return sfg_elements
}

// log sfg module loading time
const time1 = new Date()

function make_sfg(elements) {
    var cy = window.cy = cytoscape({
        container: document.getElementById('cy'),

        layout: {
            name: 'dagre',
            nodeSep: 200,
            edgeSep: 200,
            rankSep: 100,
            rankDir: 'LR',
            fit: true,
            minLen: function( edge ){ return 2 } 
        },

        style: [
        {
            selector: 'node[name]',
            style: {
            'content': 'data(name)'
            }
        },

        {
            selector: 'node[Vin]',
            style: {
            'background-color': 'red',
            }
        },

        {
            selector: 'edge',
            style: {
            'curve-style': 'unbundled-bezier',
            'control-point-distance': '-40',
            //'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'content': 'data(weight)',
            'text-outline-width': '4',
            'text-outline-color': '#E8E8E8'
            }
        },

        {
            selector: '.eh-handle',
            style: {
            'background-color': 'red',
            'width': 12,
            'height': 12,
            'shape': 'ellipse',
            'overlay-opacity': 0,
            'border-width': 12, // makes the handle easier to hit
            'border-opacity': 0
            }
        },

        {
            selector: '.eh-hover',
            style: {
            'background-color': 'red'
            }
        },

        {
            selector: '.eh-source',
            style: {
            'border-width': 2,
            'border-color': 'red'
            }
        },

        {
            selector: '.eh-target',
            style: {
            'border-width': 2,
            'border-color': 'red'
            }
        },

        {
            selector: '.eh-preview, .eh-ghost-edge',
            style: {
            'background-color': 'red',
            'line-color': 'red',
            'target-arrow-color': 'red',
            'source-arrow-color': 'red'
            }
        },

        {
            selector: '.eh-ghost-edge.eh-preview-active',
            style: {
            'opacity': 0
            }
        },
        {
            selector: ':selected',
            style: {
                'background-color': '#0069d9'
            }
        }
        ],

        elements: elements
    });

    cy.edges().forEach((edge,idx) => {
        if((edge.sourceEndpoint().x === edge.targetEndpoint().x) || (edge.sourceEndpoint().y === edge.targetEndpoint().y)) {
            edge.css({'control-point-distance': '0'})
        }
    });


    cy.on('tap', 'node', function(evt){
        if(simplify_mode) {
            let node = evt.target;
            console.log( 'tapped ' + node.id() );
            if (node === node1) {
                cy.$('#'+node.id()).css({'background-color': ''})
                node1 = null;
            }
            else if(node === node2) {
                cy.$('#'+node.id()).css({'background-color': ''})
                node2 = null;
            }
            else if(node1 === null){
                cy.$('#'+node.id()).css({'background-color': '#03af03'})
                node1 = node;
            }
            else if(node2 === null){
                cy.$('#'+node.id()).css({'background-color': '#f8075a'})
                node2 = node;
            }
        }
    
    });
    
    const time2 = new Date();
    let time_elapse = (time2 - time1)/1000;
    console.log("elements:", elements);
    console.log("SFG loading time: " + time_elapse + " seconds");
}

function display_mag_sfg() {
    let cy = window.cy;

    let updates = new Array(cy.edges().length)
    let edges = new Array(cy.edges().length)

    cy.edges().forEach((edge,idx) => {
        
        edges[idx] = edge.popper({
            content: () => {
            let div = document.createElement('div');

            //div.classList.add('popper-div');
            div.id = 'edge-' + idx;
            div.style.cssText = `font-size:${cy.zoom()*16 + 'px'};font-weight:400;`
            
            div.classList.add('label')
        
            div.innerHTML = '$$' + edge_symbolic_label[idx] + '$$';
            //div.innerHTML = '$$\\frac{y}{2x} + C$$';


        
            //document.getElementById('magnitudes').appendChild(div);
            //document.body.appendChild(div);
            document.getElementsByClassName('sfg-section')[0].appendChild(div);
            return div;
            },
            popper: {
                modifiers: {
                    preventOverflow: {
                        enabled: true,
                        boundariesElement: document.getElementsByClassName('sfg-section')[0],
                        padding: 5
                    },
                    hide:  {
                        enabled: true,
                    }
            }
        }})

        updates[idx] = () => {
            edges[idx].update();
            document.querySelector(`#edge-${idx}`).style.fontSize = cy.zoom()*16 + 'px';
        }
          
        edge.connectedNodes().on('position', updates[idx]);
        
        cy.on('pan zoom resize', updates[idx]);
    
    });

    MathJax.typeset();
    
    cy.style().selector('edge').css({'content': ''}).update()
    const time2 = new Date()
    let time_elapse = (time2 - time1)/1000
    console.log("SFG loading time: " + time_elapse + " seconds")
}


// input: data.parameters
function make_parameter_panel(parameters) {
    // remove the previous form
    var old_pf = document.getElementById("input-form")
    if (old_pf != null) {
        old_pf.remove()
    }

    var pf = document.createElement("form");
    pf.id = "input-form"

    var br = document.createElement("br");

    for (let key in parameters) {
        var parameter = document.createElement("input")
        parameter.type = "number"
        parameter.name = key
        parameter.id = key
        parameter.placeholder = key + ": " + parameters[key].toExponential()
        parameter.step = 0.000000000000001
        
        pf.appendChild(parameter)
        pf.appendChild(br.cloneNode())
    }

    var s = document.createElement("input")
    s.setAttribute("type", "submit")
    s.setAttribute("value", "Submit Form")
    pf.appendChild(s)

    //add event listener
    pf.addEventListener("submit", async function (event) {
        event.preventDefault()

        let form_data = {}
        //making input
        for (let key in parameters) {
            let i = document.querySelector(`#${key}`).value
            if (i != "") {
                form_data[key] = parseFloat(i)
            }
        }
        sfg_patch_request(form_data)

    });

    document.getElementById("param-form").appendChild(pf);
}


function sfg_patch_request(params) {

    let fields = "id,name,parameters,sfg,svg"

    let url = new URL(`${baseUrl}/circuits/${circuitId}`)
    url.searchParams.append("fields", fields)

    fetch(url, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        }, 
        mode: 'cors',
        credentials: 'same-origin',
        body: JSON.stringify(params)
    })
    .then(response => response.json())
    .then(data => {
        update_frontend(data)
    })
    .catch(error => {
        console.log(error)
    })
}

// still need function to collect source and target nodes and send as param to 
// this function
function sfg_simplify_request(params) {

    let url = new URL(`${baseUrl}/circuits/${circuitId}/simplify`)

    fetch(url, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        }, 
        mode: 'cors',
        credentials: 'same-origin',
        body: JSON.stringify(params)
    })
    .then(response => response.json())
    .then(data => {
        update_frontend(data)
    })
    .catch(error => {
        console.log(error)
    })
}


function load_interface() {

    let fields = "id,name,parameters,sfg,svg"

    var url = new URL(`${baseUrl}/circuits/${circuitId}`)
    url.searchParams.append("fields", fields)

    fetch(url)
        .then(response => {
            return response.json()
        })
        .then(data => {
            render_frontend(data)
        })
        .catch(error => {
            console.log(error)
        })
}

//Initialize frontend DOM tree
function render_frontend(data) {
    let curr_elements = edge_helper(data, symbolic_flag)
    // load SFG panel
    make_sfg(curr_elements)
    // load parameter panel
    make_parameter_panel(data.parameters)
    // load schematic panel
    make_schematics(data)

    // load transfer function
    make_transfer_func_panel()

    // load loop gain
    make_loop_gain_panel()

    // load bode plot
    make_transfer_bode_panel()
    make_loop_gain_bode_panel()
}


// Update SFG and parameter panel
function update_frontend(data) {
    let curr_elements = edge_helper(data, symbolic_flag)
    // load SFG panel
    make_sfg(curr_elements)
    // load parameter panel
    make_parameter_panel(data.parameters)
}


document.addEventListener('DOMContentLoaded', load_interface);


async function sfg_toggle() {
    symbolic_flag = !symbolic_flag
    //document.getElementById("frequency-slider").disabled = !document.getElementById("frequency-slider").disabled
    try {
        // Disable frequency slider on symbolic
        if (!symbolic_flag) {
            document.getElementById("frequency-slider").disabled = false;
        }
        else {
            document.getElementById("frequency-slider").disabled = true;
        }

        // let url = new URL(`${baseUrl}/circuits/${circuitId}`)
        // const response = await fetch(url)
        // let data = await response.json()

        //remove existing magnitude labels

        const time1 = new Date()
    

        const symbolic_labels = document.querySelectorAll('.label');
        symbolic_labels.forEach(label => {
            label.remove();
        });

        if(symbolic_flag) {
            display_mag_sfg();
        }
        else {
            window.cy.style().selector('edge').css({'content': 'data(weight)'}).update();
        }

        const time2 = new Date()

        let time_elapse = (time2 - time1)/1000
        console.log("SFG loading time (symbolic and magnitude toggle): " + time_elapse + " seconds")
        
        
    } catch {
        alert("error when toggle sfg")
    }
}

let el = document.getElementById("feature-toggle");
if (el) {
    el.addEventListener('click', sfg_toggle)
}

let refresh_button = document.getElementById("refresh-button");
if (refresh_button) {
    refresh_button.addEventListener('click', () => {
        window.location.reload()
    })
}

let return_landing = document.getElementById("return-landing");
if (return_landing) {
    return_landing.addEventListener('click', () => {
        window.location.replace('./landing.html');
    })
}

let frequency_slider = document.getElementById("frequency-slider");
var output = document.getElementById("frequency-value");
output.innerHTML = frequency_slider.value;

frequency_slider.oninput = function() {
    output.innerHTML = this.value;
    let form_data = {}
    form_data['f'] = parseInt(this.value);
    sfg_patch_request(form_data);
}



//transfer function display helper - load MathJax script
function load_latex() {
    var old_latex = document.getElementById("MathJax-script")
    if (old_latex != null) {
        old_latex.remove()
        console.log("remove old script")
    }

    var head = document.getElementsByTagName("head")[0];
    var latex_script = document.createElement("script");
    latex_script.type = "text/javascript";
    latex_script.id="MathJax-script";
    latex_script.async = true;
    latex_script.src = "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js";
    head.appendChild(latex_script);
}


function make_transfer_func_panel() {
    var form = document.createElement("form")
    form.id = "trans-form"

    var br = document.createElement("br");

    var in_node = document.createElement("input")
    in_node.type = "text"
    in_node.name = "input_node"
    in_node.id = "input_node"
    in_node.placeholder = "input node"

    var out_node = document.createElement("input")
    out_node.type = "text"
    out_node.name = "output_node"
    out_node.id = "output_node"
    out_node.placeholder = "output node"

    form.appendChild(in_node)
    form.appendChild(br.cloneNode())
    form.appendChild(out_node)
    form.appendChild(br.cloneNode())

    var s = document.createElement("input")
    s.setAttribute("type", "submit")
    s.setAttribute("value", "Submit Form")
    form.appendChild(s)

    form.addEventListener("submit", event => {
        event.preventDefault()

        let input = document.querySelector('#input_node').value
        let output = document.querySelector('#output_node').value
        
        if (input && output){
            make_transfer_func(input, output)
        }
        else {
            alert("input field incomplete")
        }
    });

    document.getElementById("transfer-form").appendChild(form);
}

function make_transfer_func(input_node, output_node) {
    let latex_toggle = true
    let factor_toggle = true
    let numerical_toggle = true
    let params = {input_node: input_node, output_node: output_node, latex: latex_toggle,
        factor: factor_toggle, numerical: numerical_toggle}
    var url = new URL(`${baseUrl}/circuits/${circuitId}/transfer_function`)
    Object.keys(params).forEach(key => url.searchParams.append(key, params[key]))
    fetch(url)
    .then(response => response.json())
    .then(data => {
        var trans = document.getElementById("trans-funtion")
        let latex_trans = "\\(" + data.transfer_function + "\\)"
        trans.innerHTML = latex_trans
        //reset MathJax
        MathJax.typeset()
    })
}


function make_schematics(data) {
    if (data.svg == null) {
        console.log("no SVG available")
    }
    else {
        var svg_html = document.getElementById("circuit-svg")

        svg_html.innerHTML = data.svg
        const svg = document.querySelector("#circuit-svg > svg")
        
        // Get the bounding box of all sub-elements inside the <svg>.
        const bbox = svg.getBBox();
        // Set the viewBox attribute of the SVG such that it is slightly bigger than the bounding box.
        svg.setAttribute("viewBox", (bbox.x-10)+" "+(bbox.y-10)+" "+(bbox.width+20)+" "+(bbox.height+20));
        svg.setAttribute("width", (bbox.width+20)  + "px");
        svg.setAttribute("height",(bbox.height+20) + "px");
        // Add a black border to the SVG so it's easier to visualize it.
        svg.setAttribute("style", "border:1px solid black");
        svg.setAttribute("height", "600px");
        svg.setAttribute("width", "1200px");
    }
}


function make_transfer_bode_panel() {
    var form = document.createElement("form")
    form.id = "trans-bode-form"

    var br = document.createElement("br");

    let element_list = []
    let element_type_dict = {
        input_node_bode: "text",
        output_node_bode: "text",
        start_freq_hz: "number",
        end_freq_hz: "number",
        points_per_decade: "number",
        // frequency_unit: "text",
        // gain_unit: "text",
        // phase_unit: "text"
    }

    // create input form
    for (key in element_type_dict) {
        var form_child = document.createElement("input")
        form_child.type = element_type_dict[key]
        if (element_type_dict[key] == "number")
            form_child.step = 0.000000000000001
        form_child.name = key
        form_child.id = key
        let new_str = key.replace(/_/g, " ");
        form_child.placeholder = new_str
        element_list.push(form_child)
    }

    let i;
    for (i=0; i < element_list.length; i++) {
        form.appendChild(element_list[i])
        form.appendChild(br.cloneNode())
    }

    var s = document.createElement("input")
    s.setAttribute("type", "submit")
    s.setAttribute("value", "Submit Form")
    form.appendChild(s)

    form.addEventListener("submit", event => {
        event.preventDefault()

        // required fields ["input_node_bode", "output_node_bode", "start_freq", "end_freq", "points_per_decade"]
        let form_list = ["input_node_bode", "output_node_bode", "start_freq_hz", "end_freq_hz", "points_per_decade"]
        // let form_list = ["input_node_bode", "output_node_bode", "start_freq_hz", "end_freq_hz", "points_per_decade", "frequency_unit", "gain_unit", "phase_unit"]
        
        let form_params = {}

        //default values for optional fields
        // form_params["frequency_unit"] = "hz"
        // form_params["gain_unit"] = "db"
        // form_params["phase_unit"] = "deg"

        let i;
        for (i=0; i < form_list.length; i++) {
            let form_entry = form_list[i]
            let input = document.querySelector(`#${form_entry}`).value
            // append key-value pair into dic
            if (form_params[form_entry] && input == "") {
                continue
            }
            else {
                form_params[form_entry] = input
            }
        }

        //*** need to add a validness check on required fields and values - chech_form_param()
        if (form_params){
            fetch_transfer_bode_data(form_params)
        }
        else {
            alert("input field incomplete")
        }
    });

    document.getElementById("transfer-func-bode-form").appendChild(form);
}


function fetch_transfer_bode_data(input_params) {
    let new_params = input_params
    new_params["input_node"] = input_params["input_node_bode"]
    new_params["output_node"] = input_params["output_node_bode"]
    delete new_params["input_node_bode"]
    delete new_params["output_node_bode"]
    
    var url = new URL(`${baseUrl}/circuits/${circuitId}/transfer_function/bode`)
    Object.keys(new_params).forEach(key => url.searchParams.append(key, new_params[key]))

    fetch(url)
    .then(response => response.json())
    .then(data => {
        make_bode_plots(data, 'transfer-bode-plot')
    })
}


function make_bode_plots(data, dom_element) {
    let freq_points = []
    let gain_points = [];
    let phase_points = [];
    let frequency = data["frequency"]
    let gain = data["gain"]
    let phase = data["phase"]

    let i;
    for (i=0; i < frequency.length; i++) {
        freq_points.push(Number.parseFloat(frequency[i].toExponential(0)).toFixed(0))
 
        let gain_pair = {
            x: frequency[i],
            y: gain[i]
        }
        gain_points.push(gain_pair)

        let phase_pair = {
            x: frequency[i],
            y: phase[i]
        }
        phase_points.push(phase_pair)
    }  

    // console.log(freq_points)
    // console.log(gain_points)
    // console.log(phase_points)

    xs = freq_points

    var lineChartData = {
        labels: xs,
        datasets: [{
            label: 'Gain plot',
            borderColor: 'rgb(255, 0, 0)',
            backgroundColor: 'rgb(255, 0, 0)',
            fill: false,
            data: gain_points,
            yAxisID: 'y-axis-1',
        }, {
            label: 'Phase plot',
            borderColor: 'rgb(0, 102, 255)',
            backgroundColor: 'rgb(0, 102, 255)',
            fill: false,
            data: phase_points,
            yAxisID: 'y-axis-2'
        }]
    };

    let graph_label
    if (dom_element === 'transfer-bode-plot') {
        graph_label = 'Transfer Function Bode Plot'
    } 
    else if (dom_element === 'loop-gain-bode-plot') {
        graph_label = 'Loop Gain Bode Plot'
    }

    var ctx = document.getElementById(dom_element).getContext('2d');
    window.myLine = Chart.Line(ctx, {
        data: lineChartData,
        options: {
            responsive: true,
            hoverMode: 'index',
            stacked: false,
            title: {
                display: true,
                text: graph_label
            },
            scales: {
                xAxes: [{
      
                    afterTickToLabelConversion: function(data){
                        var xLabels = data.ticks;
                        
                        xLabels.forEach((labels, i) => {
                            if (i % 10 != 0) {
                                xLabels[i] = '';
                            }
                        });

                    },             
                    scaleLabel: {
                        display: true,
                        labelString: 'Hz'
                    }
                }],
                yAxes: [{
                    type: 'linear', 
                    display: true,
                    position: 'left',
                    id: 'y-axis-1',
                    scaleLabel: {
                        display: true,
                        labelString: 'db'
                    }
                }, {
                    type: 'linear', 
                    display: true,
                    position: 'right',
                    id: 'y-axis-2',
                    ticks: {
                        min: -180,
                        max: 180,
                    },
                    scaleLabel: {
                        display: true,
                        labelString: 'deg'
                    },
                    stepSize: 1
                }],
            }
        }
    });
}



function make_loop_gain() {
    var url = new URL(`${baseUrl}/circuits/${circuitId}/loop_gain`)
    fetch(url)
    .then(response => response.json())
    .then(data => {
        var loop_gain = document.getElementById("loop-gain")
        let latex_loop_gain = "\\(" + data.loop_gain + "\\)"
        loop_gain.innerHTML = latex_loop_gain
        //reset MathJax
        MathJax.typeset()
    })

}


function make_loop_gain_panel() {
    var form = document.createElement("form")
    form.id = "lg-form"

    var s = document.createElement("input")
    s.setAttribute("type", "submit")
    s.setAttribute("value", "Display loop gain")
    form.appendChild(s)

    form.addEventListener("submit", event => {
        event.preventDefault()

        make_loop_gain()
       
    });

    document.getElementById("loop-gain-form").appendChild(form);
}

function make_loop_gain_bode_panel() {
    let form = document.createElement("form")
    form.id = "lg-bode-form"

    var br = document.createElement("br");

    let element_list = []
    let element_type_dict = {
        start_freq_hz_lg: "number",
        end_freq_hz_lg: "number",
        points_per_decade_lg: "number",
        // frequency_unit_lg: "text",
        // gain_unit_lg: "text",
        // phase_unit_lg: "text"
    }

    for (key in element_type_dict) {
        var form_child = document.createElement("input")
        form_child.type = element_type_dict[key]
        if (element_type_dict[key] == "number")
            form_child.step = 0.000000000000001
        form_child.name = key
        form_child.id = key
        let new_str = key.replace(/_/g, " ");
        form_child.placeholder = new_str
        element_list.push(form_child)
    }

    let i;
    for (i=0; i < element_list.length; i++) {
        form.appendChild(element_list[i])
        form.appendChild(br.cloneNode())
    }

    var s = document.createElement("input")
    s.setAttribute("type", "submit")
    s.setAttribute("value", "Submit Form")
    form.appendChild(s)

    form.addEventListener("submit", event => {
        event.preventDefault()

        // required fields ["start_freq", "end_freq", "points_per_decade"]
        let form_list = ["start_freq_hz", "end_freq_hz", "points_per_decade"]
        // let form_list = ["start_freq", "end_freq", "points_per_decade", "frequency_unit", "gain_unit", "phase_unit"]
    
        let form_params = {}

        //default values for optional fields
        // form_params["frequency_unit"] = "hz"
        // form_params["gain_unit"] = "db"
        // form_params["phase_unit"] = "deg"

        let i;
        for (i=0; i < form_list.length; i++) {
            // lg stands for loop gain, subject to change
            let form_entry = form_list[i] + "_lg"
            let input = document.querySelector(`#${form_entry}`).value
            // append key-value pair into dic
            if (form_params[form_list[i]] && input == "") {
                continue
            }
            else {
                form_params[form_list[i]] = input
            }
        }

        //*** need to add a validness check on required fields and values - chech_form_param()
        if (form_params){
            fetch_loop_gain_bode_data(form_params)
        }
        else {
            alert("input field incomplete")
        }
    });

    document.getElementById("loop-gain-bode-form").appendChild(form);
}


function fetch_loop_gain_bode_data(input_params) {
    var url = new URL(`${baseUrl}/circuits/${circuitId}/loop_gain/bode`)
    Object.keys(input_params).forEach(key => url.searchParams.append(key, input_params[key]))

    fetch(url)
    .then(response => response.json())
    .then(data => {
        make_bode_plots(data, 'loop-gain-bode-plot')
    })
}

function simplify_mode_toggle() {
    simplify_mode = !simplify_mode;
    simplify_btn = document.getElementById('simplify-btn');

    if(!simplify_mode){
        
        if(node1){
            cy.$('#'+node1.id()).css({'background-color': ''});
            node1 = null;
        }
        if(node2){
            cy.$('#'+node2.id()).css({'background-color': ''});
            node2 = null;
        }
        cy.style().selector(':selected').css({'background-color': '#0069d9'}).update();
        simplify_btn.style.display = 'none';
        
    }
    else {
        cy.style().selector(':selected').css({'background-color': '#999999'}).update();
        simplify_btn.style.display = 'inline-block';
    }
}

function simplify(){
    if(node1 === null || node2 === null){
        alert('Please select 2 nodes');
        return;
    }

    let aStar = cy.elements().aStar({ root: '#'+node1.id(), goal: '#'+node2.id() , directed: true});

    // check if there is a path
    if(!aStar.path){
        alert('There is no path between the selected nodes');
    }
    else if(aStar.path.edges().length > 2){
        alert('Your path is too long. Pick a path with only 2 edges');
    }
    else if(aStar.path.edges().length < 2){
        alert('Your path is too short. Pick a path with only 2 edges');
    }
    else (
        alert('will make API call')
    )

    // body for API call
    let form_data = {}
    form_data.source = node1.id()
    form_data.target = node2.id()

    sfg_simplify_request(form_data)

}
