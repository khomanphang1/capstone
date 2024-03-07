const baseUrl = window.location.origin;

const circuitId = sessionStorage.getItem('circuitId');

let [simplify_mode, node1, node2] = [false, null, null];
let [highlight_mode, hlt_src, hlt_tgt] = [false, null, null];

let stack_len = 0

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

// Status of undo button for simplification
function disable_undo_btn(status){
    document.getElementById("undo-btn").disabled = status;
}

// Function that parses the graph sent as a JSON from the backend
// into a cytoscape graph
function edge_helper(sample_data, flag) {
    let sfg_elements = JSON.parse(JSON.stringify(sample_data.sfg.elements))
    let edge_length = sample_data.sfg.elements.edges.length
    let sfg_edges = []
    edge_symbolic_label = new Array(edge_length)

    for (i = 0; i < edge_length; i++) {
        let new_edge = JSON.parse(JSON.stringify(sample_data.sfg.elements.edges[i]))
        edge_symbolic_label[i] = new_edge.data.weight.symbolic
        // Represent magnitude with 2 decimal points exponent
        let magnitude = expo((new_edge.data.weight.magnitude), 2).toString()
        let phase = new_edge.data.weight.phase.toFixed(2).toString()
        // Transmittance in polar form
        let result = magnitude.concat("∠", phase);
        new_edge.data.weight = result
        sfg_edges.push(new_edge)
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
        wheelSensitivity: 0.4,
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
        ,
        {   // Style for the most dominant path
            selector: '.highlighted',
              style: {
                'background-color': 'red',
                'line-color': 'red',
                'target-arrow-color': 'red',
                'transition-property': 'background-color, line-color, target-arrow-color',
                'transition-duration': '0.1s'
              }
        },

        {   // Style for cycles within the path
            selector: '.cycle',
              style: {
                'background-color': 'blue',
                'line-color': 'blue',
                'target-arrow-color': 'blue',
                'transition-property': 'background-color, line-color, target-arrow-color',
                'transition-duration': '0.1s'
              }
        },
        {   // Style for the weakest path
            selector: '.weak_path',
              style: {
                'background-color': 'yellow',
                'line-color': 'yellow',
                'target-arrow-color': 'yellow',
                'transition-property': 'background-color, line-color, target-arrow-color',
                'transition-duration': '0.1s'
              }
        },
        {   // Style for the common edges
            selector: '.common_edge',
              style: {
                'background-color': 'purple',
                'line-color': 'purple',
                'target-arrow-color': 'purple',
                'transition-property': 'background-color, line-color, target-arrow-color',
                'transition-duration': '0.1s'
              }
        },
        {   // Source Node for the Dominant path finder
            selector: '.pink',
              style: {
                'background-color': '#d90069',
                'line-color': '#d90069',
                'target-arrow-color': '#d90069',
                'transition-property': 'background-color, line-color, target-arrow-color',
                'transition-duration': '0.1s'
              }
        },
        {   // Target node for dominant path finder
            selector: '.green',
              style: {
                'background-color': '#2E8B57',
                'line-color': '#2E8B57',
                'target-arrow-color': '#2E8B57',
                'transition-property': 'background-color, line-color, target-arrow-color',
                'transition-duration': '0.1s'
              }
        }
        ],
        elements: elements
    });

    //make lines straight
    cy.edges().forEach((edge,idx) => {
        if((edge.sourceEndpoint().x === edge.targetEndpoint().x) || (edge.sourceEndpoint().y === edge.targetEndpoint().y) && edge.source().edgesWith(edge.target()).length === 1) {
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
        if(highlight_mode){
            let node = evt.target;
            console.log( 'tapped ' + node.id() );
            if (node === hlt_src) {
                cy.$('#'+node.id()).css({'background-color': ''})
                hlt_src = null;
            }
            else if(node === hlt_tgt) {
                cy.$('#'+node.id()).css({'background-color': ''})
                hlt_tgt = null;
            }
            else if(hlt_src === null){
                cy.$('#'+node.id()).css({'background-color': '#03af03'})
                hlt_src = node;
            }
            else if(hlt_tgt === null){
                cy.$('#'+node.id()).css({'background-color': '#f8075a'})
                hlt_tgt = node;
            }
            if(hlt_src != null & hlt_tgt != null){
                console.log("Time to highlight:)")
                HighlightPath()
            }else{
                removeHighlightPrevious()
            }
        }
    });
    
    const time2 = new Date();
    let time_elapse = (time2 - time1)/1000;
    console.log("elements:", elements);
    console.log("make_sfg SFG loading time: " + time_elapse + " seconds");
}

function HighlightPath(){
    var node = hlt_src;
    var target = hlt_tgt
    var paths_found = 0;
    var elementsToSearch = cy.elements;
    var searchedAlready = [];
    var MakesPath = [];
    paths = []
    cycle_edge_in_path = []
    actual_cycles = []
    removeHighlightPrevious()

    // source is a node
    // destination is a node
    const findPathsToTarget = function(source, destination, searchedAlready, path){
          let connected = source.outgoers().edges()
          searchedAlready.push(source.id())
          let new_path = [...path];
          var result = false;
          if(connected.length != 0){
            // find direct connections
            connected.forEach(this_edge => {
                if(this_edge.target().id() == destination.id()){
                    // concatenate edge
                    const found_path = new_path.concat([this_edge]);
                    paths_found = paths_found + 1
                    paths.push(found_path)
                    result = true
                }
                else{
                    // check if node already visited within path
                    visited = false
                    var edge_index = 0
                    // changed to source and checked if it came back to itself
                    new_path.forEach(e => {
                        if(e.source().id() == this_edge.target().id() || this_edge.target().id() == this_edge.source().id()){
                            visited = true;
                            let new_cycle = new_path.slice(edge_index)
                            new_cycle.push(this_edge)
                            actual_cycles.push(new_cycle)
                            console.log("In here!")
                            console.log(new_cycle)
                            cycle_edge_in_path.push(e)
                        }
                        edge_index = edge_index + 1
                    })

                    if(visited == false){
                        const explore_path = new_path.concat([this_edge]);
                        if(findPathsToTarget(this_edge.target(), destination, searchedAlready, explore_path)){
                            result = true;
                            MakesPath.push(this_edge.target().id())
                        }
                    }
                }
            });
          }
          if(result == true){
            return true;
          }else{
            return false;
          }
    };

    if(findPathsToTarget(node, target, searchedAlready, [])){
        MakesPath.push(node.id())
        let index = 0;
        let min_index = -1;
        let max_index = -1;
        let max_gain = 0;
        let min_gain = Infinity;
        console.log("Paths found = " + paths_found)
        gains = []
        paths.forEach(path => {
            let total_gain = 1.0
            path.forEach(gain=>{
                let weight = gain.data('weight')
                weight = weight.split('∠');
                total_gain = total_gain * Number(weight[0])
            })
            gains.push(total_gain)
            if(total_gain < min_gain){
                min_index = index;
                min_gain = total_gain;
            }
            if(total_gain > max_gain){
                max_index = index;
                max_gain = total_gain;
            }
            index = index + 1;
      })
        if(min_index != -1){
            paths[min_index].forEach(gain=>{
                gain.addClass('weak_path')
                if(gain.target().id() != target.id() & gain.target().id() != node.id()){
                    gain.target().addClass('weak_path')
                }
                if(gain.source().id() != node.id() & gain.source().id() != target.id()){
                    gain.source().addClass('weak_path')
                }
            })
        }
        if(max_index != -1){
            paths[max_index].forEach(gain=>{
                gain.addClass('highlighted')
                if(gain.target().id() != target.id() & gain.target().id() != node.id()){
                    gain.target().addClass('highlighted')
                }
                if(gain.source().id() != node.id() & gain.source().id() != target.id()){
                    gain.source().addClass('highlighted')
                }
          })
      }
        if(max_index != -1 & min_index != -1){
             const filteredArray = paths[max_index].filter(value => paths[min_index].includes(value));
             filteredArray.forEach(path=>{
                 path.addClass('common_edge')
                 if(path.target().id() != target.id())
                    path.target().addClass('common_edge')
                 if(path.source().id() != node.id())
                    path.source().addClass('common_edge')
             })
        }
        var cycle_index = 0
        cycle_edge_in_path.forEach(cycle=>{
            if(MakesPath.includes(cycle.target().id()) && MakesPath.includes(cycle.source().id())){
                console.log('Cycle found: ')
                console.log(actual_cycles[cycle_index])
                actual_cycles[cycle_index].forEach(cycle_edge=>{
                    cycle_edge.removeClass('weak_path')
                    cycle_edge.removeClass('common_edge')
                    cycle_edge.removeClass('highlighted')
                    cycle_edge.addClass('cycle')
                })
            }
            cycle_index = cycle_index + 1
        })
        console.log('Paths found: ')
        console.log(paths)
        console.log('Gains: ')
        console.log(gains)
        document.getElementById("dominant").textContent = expo(max_gain,2);
        document.getElementById("weak").textContent = expo(min_gain,2);
      }
}

function removeHighlightPrevious(){
    let cy = window.cy;
    document.getElementById("dominant").textContent = "N/A";
    document.getElementById("weak").textContent = "N/A";
    cy.elements().forEach((element,idx) => {
            element.removeClass('highlighted');
            element.removeClass('cycle');
            element.removeClass('weak_path');
            element.removeClass('pink');
            element.removeClass('green');
            element.removeClass('common_edge');
      })
}

function removeHighlight(){
    let cy = window.cy;
    document.getElementById("dominant").textContent = "N/A";
    document.getElementById("weak").textContent = "N/A";
    if(hlt_tgt){
        cy.$('#'+hlt_tgt.id()).css({'background-color': ''});
        hlt_tgt = null
    }
    if(hlt_src){
        cy.$('#'+hlt_src.id()).css({'background-color': ''});
        hlt_src = null
    }
    cy.elements().forEach((element,idx) => {
            element.removeClass('highlighted');
            element.removeClass('cycle');
            element.removeClass('weak_path');
            element.removeClass('pink');
            element.removeClass('green');
            element.removeClass('common_edge');
      })
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
            edge = document.querySelector(`#edge-${idx}`);
            if (edge) {
                edge.style.fontSize = cy.zoom()*16 + 'px';
            }
        }
          
        edge.connectedNodes().on('position', updates[idx]);
        
        cy.on('pan zoom resize', updates[idx]);
    
    });

    MathJax.typeset();
    
    cy.style().selector('edge').css({'content': ''}).update()
    const time2 = new Date()
    let time_elapse = (time2 - time1)/1000
    console.log("display_mag_sfg SFG loading time: " + time_elapse + " seconds")
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
    var freq = 0
    for (let key in parameters) {
        var parameter = document.createElement("input")
        parameter.type = "number"
        parameter.name = key
        parameter.id = key
        if(key == 'f')
            freq = parameters[key]
        parameter.placeholder = key + ": " + parameters[key].toExponential()
        parameter.step = 0.000000000000001
        
        pf.appendChild(parameter)
        pf.appendChild(br.cloneNode())
    }

    var s = document.createElement("input")
    s.setAttribute("type", "submit")
    s.setAttribute("value", "Submit Form")
    pf.appendChild(s)

    console.log(freq)
    output.innerHTML = freq
    frequency_slider.value = freq

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
        removeHighlight()
        console.log(data)
        update_frontend(data)
    })
    .catch(error => {
        console.log(error)
    })
}

// Sends a patch request to the backend and updates edge weights
// on the graph without re rendering the entire graph
// same as sfg_patch_request but without update_frontend
function sfg_patch_request_without_rerender(params) {

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
        removeHighlight()
        let cy = window.cy;
        let curr_elements = edge_helper(data, symbolic_flag).edges
        curr_elements.forEach(edge=>{
            let text = 'edge[source = "'
            text = text.concat(edge.data.source)
            text = text.concat('"]')
            text = text.concat('[target = "')
            text = text.concat(edge.data.target)
            text = text.concat('"]')
            value = edge.data.weight
            cy.elements(text).data('weight', value)
        })
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
        if(stack_len==0){
            disable_undo_btn(false);
        }
        stack_len = stack_len < 2 ? stack_len + 1 : 2
        update_frontend(data)
        simplify_mode_toggle()
        reset_mag_labels()
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

    // Frequency bounds form
    make_frequency_bounds()
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

// HTML Frequency slider element
let frequency_slider = document.getElementById("frequency-slider");

// HTML Element displaying current frequency from slider
var output = document.getElementById("frequency-value");

// Update the display of the frequency value with the current value from the slider
output.innerHTML = frequency_slider.value;

frequency_slider.oninput = function() {
    output.innerHTML = frequency_slider.value;
    let form_data = {}
    form_data['f'] = parseInt(this.value);  // populate form with frequency request
    sfg_patch_request_without_rerender(form_data);      // send patch request to backend,
                                                        // this function receives new values
                                                        // and updates sfg edges
    document.querySelector('input#f').placeholder = 'f' + ": " + expo(this.value,2)
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

    // print the base url
    console.log('base url: ', baseUrl)

    // print the created url
    console.log('url: ', url)
    console.log("URL before appending parameters:", url.href);
    Object.keys(params).forEach(key => {
        const value = params[key].toString();
        url.searchParams.append(key, value);
    });
    console.log("Final URL with parameters:", url.href);
    
    fetch(url)
    .then(response => {
        if (!response.ok) {
            // If response is not ok (i.e., in error status range), reject the promise
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        // If response is ok, return JSON promise
        return response.json();
    })
    .then(data => {
        console.log("data");
        console.log(data);
        console.log("transfer function data:", data.transfer_function);
        // Handle the JSON data
        var trans = document.getElementById("trans-funtion")
        let latex_trans = "\\(" + data.transfer_function + "\\)"
        trans.innerHTML = latex_trans
        console.log(data)
        //reset MathJax
        MathJax.typeset()
    })
    .catch(error => {
        console.error('make_transfer_func error:', error);
        console.log('make_transfer_func Full response:', error.response);
    });
    
    // fetch(url)
    // // .then(response => response.json())
    // .then(response => {
    //     console.log('Response Type:', response.type);
    //     return response.json();
    // })
    // .then(data => {
    //     var trans = document.getElementById("trans-funtion")
    //     let latex_trans = "\\(" + data.transfer_function + "\\)"
    //     trans.innerHTML = latex_trans
    //     console.log(data)
    //     //reset MathJax
    //     MathJax.typeset()
    // })
    // .catch(error => {
    //     console.error('Error:', error);
    // });
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

function make_frequency_bounds() {
    var form = document.createElement("form")
    form.id = "frequency-bounds-form"

    var min_range = document.getElementById("min-range")
    var max_range = document.getElementById("max-range")
    var update_range = document.getElementById("update-range")
    form.appendChild(min_range)
    form.appendChild(max_range)
    form.appendChild(update_range)

    form.addEventListener("submit", event => {
        event.preventDefault()

        let min = Number(document.querySelector('#min-range').value)
        let max = Number(document.querySelector('#max-range').value)

        if (min >= 0 && max >= 0 && min < max){
            document.getElementById("frequency-slider").min = min
            document.getElementById("frequency-slider").max = max
            document.getElementById('min-range').placeholder=expo(min,2).toString()
            document.getElementById('max-range').placeholder=expo(max,2).toString()
        }
        else {
            alert("input invalid")
        }
    });

    document.getElementById("frequency-form").appendChild(form)
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

    // print the base url
    console.log("base url:", baseUrl);

    // print out the created url
    console.log("url:", url.href)
    fetch(url)
    .then(response => {
        if (!response.ok) {
            // If response is not ok (i.e., in error status range), reject the promise
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        // If response is ok, return the JSON promise
        return response.json();
    })
    .then(data => {
        console.log("data");
        console.log(data);
        console.log("loop gain data:", data.loop_gain);
        var loop_gain = document.getElementById("loop-gain")
        let latex_loop_gain = "\\(" + data.loop_gain + "\\)"
        loop_gain.innerHTML = latex_loop_gain
        //reset MathJax
        MathJax.typeset()
    })
    .catch(error => {
        // Handle errors
        console.error('make_loop_gain Fetch error:', error);
        console.log('make_loop_gain Full response:', error.response);
    });

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

function path_highlight_toggle() {
    highlight_mode = !highlight_mode;
    if(!highlight_mode){
        removeHighlight()
        document.getElementById('simplification-toggle').checked = false;
        document.getElementById('simplification-toggle').disabled = false;
    }else{
        node1 = null
        node2 = null
        document.getElementById('simplification-toggle').disabled = true;
    }
}

function simplify_mode_toggle() {
    simplify_btn = document.getElementById('simplify-btn');
    simplify_mode = !simplify_mode;
    

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
        document.getElementById('simplification-toggle').checked = false;
        document.getElementById('path-highlight-toggle').disabled = false;
        document.getElementById('rmv-hlt-btn').disabled = false;
    }
    else {
        removeHighlight()
        document.getElementById('path-highlight-toggle').checked = false;
        document.getElementById('path-highlight-toggle').disabled = true;
        document.getElementById('rmv-hlt-btn').disabled = true;

        cy.style().selector(':selected').css({'background-color': '#999999'}).update();
        simplify_btn.style.display = 'inline-block';
        document.getElementById('simplification-toggle').checked = true;
    }
}

function simplify(){
    if(node1 === null || node2 === null){
        alert('Please select 2 nodes');
        return;
    }

    //find path between the selected nodes
    let aStar = cy.elements().aStar({ root: '#'+node1.id(), goal: '#'+node2.id() , directed: true});

    //check if a path exists
    if(!aStar.path){
        alert('There is no path between the selected nodes');
    }
    //check if the smallest possible path is larger than 2
    else if(aStar.path.edges().length > 2){
        alert('Your path is too long. Pick a path with only 2 edges');
    }
    else {
        console.log("requesting simplification")
        let form_data = {}
        form_data.source = node1.id()
        form_data.target = node2.id()
        sfg_simplify_request(form_data)
    }
}

function sfg_undo_request(params) {

    let url = new URL(`${baseUrl}/circuits/${circuitId}/undo`)

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
        stack_len--;
        if (stack_len === 0) {
            disable_undo_btn(true);
        }
        update_frontend(data)
        reset_mag_labels()
    })
    .catch(error => {
        console.log(error)
    })
}

function sfg_undo(){
    if (stack_len > 0){
        sfg_undo_request();
    }
    else {
        disable_undo_btn(true);
    }
}

function reset_mag_labels(){
    if(symbolic_flag) {
        const symbolic_labels = document.querySelectorAll('.label');
        symbolic_labels.forEach(label => {
            label.remove();
        });

        display_mag_sfg();
    }
}

function export_sfg(){
    export_sfg_request();
}

function export_sfg_request() {
    // get current deserialized (non binary) sfg, and export as json

    let url = new URL(`${baseUrl}/circuits/${circuitId}/export`)
    console.log(url)
    fetch(url, {
        method: "get",
        mode: "no-cors",

    })
        .then(response => {
            return response.blob();
        })
        .then(blob => {
            console.log("EXported json obj is: ", blob);
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${circuitId}-export.pkl`;
            a.click();
            URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.log('File Download Failed', error)
        })

}

// Function to download data to a file
function download(data, filename, type) {
    var file = new Blob([data], {type: type});
    if (window.navigator.msSaveOrOpenBlob) // IE10+
        window.navigator.msSaveOrOpenBlob(file, filename);
    else { // Others
        var a = document.createElement("a"),
                url = URL.createObjectURL(file);
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);   
        a.click();
        setTimeout(function() {
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);  
        }, 0); 
    }
}


function upload_sfg() {
    // TODO add error checking (i.e. is file in correct json format)
    var files = document.getElementById('upload_sfg').files;
    console.log(files);
    if (files.length <= 0) {
        return false;
    }

    var fr = new FileReader();
    var sfg_obj;
    fr.onload = function(e) { 
        console.log(e);
        sfg_obj = JSON.parse(e.target.result);
        // TODO alert() here
        //var res_str = JSON.stringify(result, null, 2);
        console.log("IMPORTED json obj is: ", sfg_obj)
        //console.log(JSON.parse(JSON.stringify(sfg_obj.sfg.elements)))
        // TODO connect to backend to convert sfg JSON to sfg graph and binary field
        import_sfg_request(sfg_obj)
        console.log(sessionStorage.getItem('circuitId'))
    }

    fr.readAsText(files.item(0));
}

function import_sfg_request(sfg_obj) {

    let url = new URL(`${baseUrl}/circuits/${circuitId}/import`)

    fetch(url, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        }, 
        mode: 'cors',
        credentials: 'same-origin',
        body: JSON.stringify(sfg_obj)
    })
    .then(response => response.json())
    .then(data => {
        update_frontend(sfg_obj, true);
    })
    .catch(error => {
        console.log(error)
    })
}

function upload_dill_sfg() {
    // TODO add error checking (i.e. is file in correct json format)
    var files = document.getElementById('upload_sfg').files;
    console.log(files);
    if (files.length <= 0) {
        return false;
    }
    var dill_sfg = files[0];
    console.log(dill_sfg);
    var fr = new FileReader();
    var sfg_obj;
    fr.onload = function(e) { 
        console.log("IMPORTED dill obj is: ", dill_sfg)
        //console.log(JSON.parse(JSON.stringify(sfg_obj.sfg.elements)))
        // TODO connect to backend to convert sfg JSON to sfg graph and binary field
        import_dill_sfg(dill_sfg)
    }

    fr.readAsText(files.item(0));
}

function import_dill_sfg(dill_sfg) {
    let url = new URL(`${baseUrl}/circuits/${circuitId}/import`)
    console.log(circuitId)
    var formData = new FormData();
    formData.append("file", dill_sfg);

    fetch(url, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // TODO update_frontend(data);
        //or update_frontend(sfg_obj, true); ?
       
        
        data_json = JSON.parse(JSON.stringify(data));
        // data_json.sfg = sfg_obj;
        
        console.log("modified data is: ");
        console.log(data_json);
        update_frontend(data_json); //buggy
        
    
        // update_frontend(sfg_obj, true);
    })
    .catch(error => {
        console.log(error)
    })}