const baseUrl = window.location.origin;

const circuitId = sessionStorage.getItem('circuitId');

let [simplify_mode, node1, node2] = [false, null, null];
let [highlight_mode, hlt_src, hlt_tgt] = [false, null, null];

let stack_len = 0
let redo_len = 0

if (!circuitId) {
    window.location.replace('./landing.html');
}

var symbolic_flag = false //feature toggle
var tf_flag = false //transfer function toggle
var lg_flag = false //loop gain toggle
var tf = {}
let current_data = null //session data
let edge_symbolic_label;
let transfer_bode_plot_history = [];
let loop_gain_bode_plot_history = [];

// Function to convert float to exponential
function expo(x, f) {
  return Number.parseFloat(x).toExponential(f);
}

// Status of undo button for simplification
function disable_undo_btn(status){
    document.getElementById("undo-btn").disabled = status;
}

// status of redo button for simplification
function disable_redo_btn(status){
    document.getElementById("redo-btn").disabled = status;
}

// Function that parses the graph sent as a JSON from the backend
// into a cytoscape graph
function edge_helper(sample_data, flag) {
    if (!sample_data || !sample_data.sfg || !sample_data.sfg.elements) {
        throw new Error('Invalid sample data');
    }
    
    let sfg_elements = JSON.parse(JSON.stringify(sample_data.sfg.elements))
    let edge_length = sample_data.sfg.elements.edges.length
    let sfg_edges = []
    edge_symbolic_label = new Array(edge_length)

    // TODO MARK
    for (i = 0; i < edge_length; i++) {
        let new_edge = JSON.parse(JSON.stringify(sample_data.sfg.elements.edges[i])) // make sample_data.sfg.elements.edges[i] get the new edited branch from edge_symbolic_label[i] ==> sdf_patch_request_without_rendering to see updates
        edge_symbolic_label[i] = new_edge.data.weight.symbolic
        // TODO MARK
        // call sfg_patch_request (with or without rerendering) to send to backend
        
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

    // log all nodes and edges of sfg
    console.log("nodes:", cy.nodes());
    // log node ids
    console.log("node ids:", cy.nodes().map(node => node.id()));
    console.log("edges:", cy.edges());

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
            else if(hlt_src === null){ // sets highlight source node to green
                cy.$('#'+node.id()).css({'background-color': '#03af03'})
                hlt_src = node;
            }
            else if(hlt_tgt === null){ // sets highlight target node to red
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


    // Initialize edge hover functionality
    initializeEdgeHover();
    
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





// function dum2_editBranch() {
//     console.log("editBranch is called");

//     let cy = window.cy;
//     // let updates = new Array(cy.edges().length)
//     // let edges = new Array(cy.edges().length)

//     console.log("printing all edges: ", cy.edges())
//     // console.log("print edges: ", edges)

//     // Event listener for right-click on edges
//     cy.edges().forEach((edge, idx) => {
//         edge.on('cxttap', function(evt) {
//             console.log("evt target: ", evt.target)
//             console.log("evt: ", evt)

//             // Retrieve the LaTeX code for the selected edge
//             let latexCode = edge_symbolic_label[idx];
//             console.log("LaTeX code for selected edge:", latexCode);
//             console.log("Idx:", idx);

//             // Display popup window for editing LaTeX code
//             let modifiedLatexCode = editLatexCode(latexCode, idx);

//             // Check if the user made any modifications
//             if (modifiedLatexCode !== null) {
//                 // Update the LaTeX content of the Edge
//                 console.log("Modified LaTeX code:", modifiedLatexCode);
//                 // updateEdgeLabel(edge, modifiedLatexCode, idx);
//             }
//         });
        
//     });

//     // MathJax.typeset();

//     cy.style().selector('edge').css({ 'content': '' }).update();
//     const time2 = new Date();
//     let time_elapse = (time2 - time1) / 1000;
//     console.log("editBranch SFG loading time: " + time_elapse + " seconds");
// }


// function dum_editBranch() {
//     console.log("editBranch is called");

//     let cy = window.cy;
//     let updates = new Array(cy.edges().length)
//     let edges = new Array(cy.edges().length)

//     console.log("printing all edges: ", cy.edges())
//     console.log("print edges: ", edges)

//     // Event listener for right-click on edges
//     cy.edges().forEach((edge, idx) => {
//         edge.on('cxttap', function(evt) {
//             console.log("evt target: ", evt.target)
//             console.log("evt: ", evt)

//             // Retrieve the LaTeX code for the selected edge
//             let latexCode = edge_symbolic_label[idx];
//             console.log("LaTeX code for selected edge:", latexCode);
//             console.log("Idx:", idx);

//             // Display popup window for editing LaTeX code
//             let modifiedLatexCode = editLatexCode(latexCode, idx);

//             // Check if the user made any modifications
//             if (modifiedLatexCode !== null) {
//                 // Update the LaTeX content of the Edge
//                 console.log("Modified LaTeX code:", modifiedLatexCode);
//                 updateEdgeLabel(edge, modifiedLatexCode, idx);
//             }
//         });
//     });

//     // Function to update the LaTeX content of the edge
//     function updateEdgeLabel(edge, latexCode) {
//         console.log("Updating edge label:", edge, latexCode);
        
//         // Find the index of the edge in the edges array
//         let index = edges.findIndex(item => item.edge === edge);

//         // If the edge is found in the edges array
//         if (index !== -1) {
//             // Destroy the existing popper
//             edges[index].popper.destroy();

//             // Create a new popper with the modified LaTeX code
//             let newPopper = edge.popper({
//                 content: () => {
//                     let div = document.createElement('div');
//                     div.classList.add('label');
//                     div.innerHTML = '$$' + latexCode + '$$';
//                     console.log("Inside edge.popper content:()");
//                     return div;
//                 },
//                 popper: {
//                     modifiers: {
//                         preventOverflow: {
//                             enabled: true,
//                             boundariesElement: document.getElementsByClassName('sfg-section')[0],
//                             padding: 5
//                         },
//                         hide: {
//                             enabled: true,
//                         }
//                     }
//                 }
//             });

//             // Update the popper reference in the edges array
//             edges[index].popper = newPopper;
//         } else {
//             // Create a new popper and add it to the edges array
//             let newPopper = edge.popper({
//                 content: () => {
//                     let div = document.createElement('div');
//                     div.classList.add('label');
//                     div.innerHTML = '$$' + latexCode + '$$';
//                     console.log("Inside edge.popper content:()");
//                     return div;
//                 },
//                 popper: {
//                     modifiers: {
//                         preventOverflow: {
//                             enabled: true,
//                             boundariesElement: document.getElementsByClassName('sfg-section')[0],
//                             padding: 5
//                         },
//                         hide: {
//                             enabled: true,
//                         }
//                     }
//                 }
//             });

//             edges.push({ edge: edge, popper: newPopper });
//         }
//     }

//     MathJax.typeset();

//     cy.style().selector('edge').css({ 'content': '' }).update();
//     const time2 = new Date();
//     let time_elapse = (time2 - time1) / 1000;
//     console.log("editBranch SFG loading time: " + time_elapse + " seconds");
// }


// ------------------------------------------------------------------------------------------------

// // Function to display popup window with LaTeX code for editing
// function editLatexCode(latexCode) {
//     // Open a popup window or modal dialog
//     let userInput = prompt("Edit LaTeX code:", latexCode);

//     // Return the modified LaTeX code entered by the user
//     return userInput;
// }

// // edit the selected branch on the SFG
// function editBranch() {
//     console.log("editBranch is called");

//     let cy = window.cy;

//     let updates = new Array(cy.edges().length)
//     let edges = new Array(cy.edges().length)



//     // Event listener for right-click on edges
//     cy.edges().forEach((edge, idx) => {
//         edge.on('cxttap', function(evt){
//             // Retrieve the LaTeX code for the selected edge
//             let latexCode = edge_symbolic_label[idx];
//             console.log("LaTeX code for selected edge:", latexCode);

//             // Display popup window for editing LaTeX code
//             let modifiedLatexCode = editLatexCode(latexCode);

//             // Check if the user made any modifications
//             if (modifiedLatexCode !== null) {
//                 // Send the modified LaTeX code back to the circuit
//                 // Replace this line with the appropriate code to send the modified LaTeX code back to the circuit
//                 console.log("Modified LaTeX code:", modifiedLatexCode);
//             }
//         });
        
//         edges[idx] = edge.popper({
//             content: () => {
//             let div = document.createElement('div');

//             //div.classList.add('popper-div');
//             div.id = 'edge-' + idx;
//             div.style.cssText = `font-size:${cy.zoom()*16 + 'px'};font-weight:400;`
            
//             div.classList.add('label')
        
//             div.innerHTML = '$$' + modifiedLatexCode + '$$';
//             //div.innerHTML = '$$\\frac{y}{2x} + C$$';


        
//             //document.getElementById('magnitudes').appendChild(div);
//             //document.body.appendChild(div);
//             document.getElementsByClassName('sfg-section')[0].appendChild(div);
//             return div;
//             },
//             popper: {
//                 modifiers: {
//                     preventOverflow: {
//                         enabled: true,
//                         boundariesElement: document.getElementsByClassName('sfg-section')[0],
//                         padding: 5
//                     },
//                     hide:  {
//                         enabled: true,
//                     }
//             }
//         }})

//         updates[idx] = () => {
//             edges[idx].update();
//             edge = document.querySelector(`#edge-${idx}`);
//             if (edge) {
//                 edge.style.fontSize = cy.zoom()*16 + 'px';
//             }
//         }
          
//         edge.connectedNodes().on('position', updates[idx]);
        
//         cy.on('pan zoom resize', updates[idx]);

//     });

//     MathJax.typeset();

//     cy.style().selector('edge').css({'content': ''}).update()
//     const time2 = new Date()
//     let time_elapse = (time2 - time1)/1000
//     console.log("editBranch SFG loading time: " + time_elapse + " seconds")
// }


    // --------------------------------------------------------------------------------------------------------------------


    // cy.on('cxttap', 'edge', function(evt) {
    //     var edge = evt.target;
    //     var edgeData = edge.data(); // Get edge data, which includes the value

    //     // print the edge
    //     console.log('editing Edge:', edge);
    //     // print the edge data
    //     console.log('editing Original Edge Data:', edgeData);
    //     // print the latex data
    //     console.log('editing Original Edge Latex:', edgeData.latex);

    //     // Create a custom HTML prompt
    //     // Create a multiline message for the prompt
    //     var message = `Original LaTeX:\n${edgeData.latex}\n\nEnter new LaTeX:`;

    //     // Display prompt with original LaTeX and input field for new LaTeX
    //     var newLatex = prompt(message);

    //     // Check if user entered a new LaTeX content
    //     if (newLatex !== null && newLatex.trim() !== '') {
    //         // Update edge's data with new LaTeX content
    //         edge.data('latex', newLatex);
    //         console.log('Edge LaTeX updated:', newLatex);
    //     }
    // });
// }

// Removes the selected branch from the diagram
function qremoveBranch() {
    console.log("removeBranch is called");

    // Define the event handler to handle tap events on edges
    function edgeTapHandler(evt) {
        let tappedEdge = evt.target; // Get the tapped edge
        console.log('Tapped Edge:', tappedEdge);

        // Remove the popper element associated with the tapped edge
        let edgePopper = tappedEdge.popper(destroy
            
        ); // Retrieve the popper element
        if (edgePopper) {
            edgePopper.destroy(); // Destroy the popper element
            console.log('Popper removed:', edgePopper);
            // Remove the tapped edge from the diagram
            tappedEdge.remove();
            console.log('Edge removed:', tappedEdge);
        }

        // Turn off the event handler after the first edge has been removed
        cy.off('tap', 'edge', edgeTapHandler);
    }

    // Attach the event handler to listen for tap events on edges
    cy.on('tap', 'edge', edgeTapHandler);

}

function removeLatexCode(latexCode, idx) {
    edge_symbolic_label[idx] = '';
}

// TODO MARK: Make sure branch removals are consistent with the editBranch() logic
// TODO MARK: make sure floating nodes are also removed
function tremoveBranch() {
    console.log("removeBranch is called");
    let cy = window.cy;

    function edgeTapHandler(evt) {
        let edge = evt.target;
        let idx = cy.edges().indexOf(edge);

        // Remove the label for the edge being removed
        edge_symbolic_label.splice(idx, 1);

        document.getElementById("rmv-branch-btn").disabled = false;

        console.log('edge removed:', edge);
        cy.off('tap', 'edge', edgeTapHandler);
        edge.remove(); 
        reset_mag_labels();
        console.log("edge_symbolic_label:", edge_symbolic_label);

        // Update the indices in edge_symbolic_label to match the new indices of the remaining edges
        updateIndicesInSymbolicLabels();
    }

    // Attach the event listener to edges for click
    cy.on('tap', 'edge', edgeTapHandler);
    document.getElementById("rmv-branch-btn").disabled = true;

    // Update cy style and log loading time
    cy.style().selector('edge').css({ 'content': '' }).update();
    const time2 = new Date();
    let time_elapse = (time2 - time1) / 1000;
    console.log("editBranch SFG loading time: " + time_elapse + " seconds");

    // Function to update the indices in edge_symbolic_label array
    function updateIndicesInSymbolicLabels() {
        cy.edges().forEach((edge, i) => {
            let label = edge_symbolic_label[i];
            if (label !== undefined) {
                edge_symbolic_label[i] = label;
            }
        });
    }
}

// Function to initialize event listeners for edges
function initializeEdgeHover() {
    console.log("********** initializeEdgeHover is called **********")
    let cy = window.cy; // Assuming `cy` is your Cytoscape instance

    // Ensure `cy` is initialized
    if (typeof cy === 'undefined' || cy === null) {
        console.error('Cytoscape instance is not initialized.');
        return;
    }

    // Attach mouseover event listener to edges
    cy.on('mouseover', 'edge', function(event) {
        let edge = event.target;
        let edge_id = edge.id();
        let edge_index = cy.edges().indexOf(edge);
        let edgeData = edge.data();

        // Display edge information in a designated HTML element
        displayEdgeInfo(edgeData, edge_id, edge_index);

        // Show the edge-info box
        // document.getElementById('edge-info').style.display = 'block';

        // Show the edge-info box
        let edgeInfoBox = document.getElementById('edge-info');
        edgeInfoBox.style.display = 'block';
    });

    // Attach mouseout event listener to clear the information
    cy.on('mouseout', 'edge', function(event) {
        clearEdgeInfo();

        // Hide the edge-info box
        // document.getElementById('edge-info').style.display = 'none';

        //  // Hide the edge-info box
        //  let edgeInfoBox = document.getElementById('edge-info');
        //  edgeInfoBox.style.display = 'none';
    });

    // Attach mousemove event listener to update position of edge-info box
    cy.on('mousemove', 'edge', function(event) {
        updateEdgeInfoPosition(event.originalEvent);
    });
}

// Function to display edge information in an HTML element
function displayEdgeInfo(edgeData, edge_id, edge_index) {
    // console.log("********** displayEdgeInfo is called **********")
    let edgeInfoElement = document.getElementById('edge-info');

    // // Clear any existing content and force repaint by removing and re-adding the element
    // edgeInfoElement.style.display = 'none'; // Hide element
    // edgeInfoElement.innerHTML = ''; // Clear content
    // void edgeInfoElement.offsetWidth; // Force repaint
    // edgeInfoElement.style.display = 'block'; // Show element again

    // Clear any existing content and force repaint by removing and re-adding the element
    edgeInfoElement.innerHTML = ''; // Clear content
    if (edgeInfoElement.parentNode) {
        edgeInfoElement.parentNode.removeChild(edgeInfoElement);
        document.body.appendChild(edgeInfoElement);
    }

    if (edgeInfoElement) {
        edgeInfoElement.innerHTML = `
            <strong>Source:</strong> ${edgeData.source} <br>
            <strong>Target:</strong> ${edgeData.target} <br>
            <strong>Weight:</strong> ${edgeData.weight || 'N/A'} <br>
            <strong>Edge Index:</strong> ${edge_index} <br>
            <strong>Edge ID:</strong> ${edge_id} <br>
        `;
    }
}

// Function to clear the edge information display
function clearEdgeInfo() {
    // console.log("********** clearEdgeInfo is called **********");
    let edgeInfoElement = document.getElementById('edge-info');
    // edgeInfoElement.style.display = 'none'; // Hide element
    edgeInfoElement.innerHTML = ''; // Clear content
    // void edgeInfoElement.offsetWidth; // Force repaint
    // edgeInfoElement.style.display = 'block'; // Show element again
    // Hide the edge-info box
    let edgeInfoBox = document.getElementById('edge-info');
    edgeInfoBox.style.display = 'none';
}

// Function to update the position of the edge-info element based on mouse event
function updateEdgeInfoPosition(event) {
    let edgeInfoElement = document.getElementById('edge-info');

    // Set the position of the edge-info element to follow the mouse cursor
    edgeInfoElement.style.left = (event.clientX + 15) + 'px'; // Offset to avoid cursor overlap
    edgeInfoElement.style.top = (event.clientY + 15) + 'px';  // Offset to avoid cursor overlap
}

function removeBranch() {
    console.log("removeBranch is called");
    let cy = window.cy;
    function edgeTapHandler(evt){
        let edge = evt.target;
        edge.style('display', 'none');
        // edge.remove();

        // let idx = cy.edges().indexOf(edge);
        // edgeToRemove = cy.getElementById(idx);
        // console.log('idx:', idx);
        // console.log("edgeToRemove:", edgeToRemove);
        // edgeToRemove.remove();
        // edge_symbolic_label[idx] = '';
        
        console.log("edge_symbolic_label array:", edge_symbolic_label);
        // edge_symbolic_label.splice(idx,1); // Remove the latex code for the edge
        
        // // Adjust indices for edges after the removed edge
        // for (let i = idx + 1; i < cy.edges().length; i++) {
        //     edge_symbolic_label[i - 1] = edge_symbolic_label[i];
        // }
        // edge_symbolic_label.pop(); // Remove the last element
        

        // Construct data for the DELETE request
        let data = {
            source: edge.data('source'), // Get source node ID
            target: edge.data('target')  // Get target node ID
        };

        console.log("edge id:", edge.id());
        console.log("edge data:", edge.data());

        // Remove the edge from Cytoscape
        edge.remove();

        // Update the backend with the removed branch
        remove_edge_request(data);

        document.getElementById("rmv-branch-btn").disabled = false;
        
        console.log('edge (edge id) removed:', edge.id());
        cy.off('tap', 'edge', edgeTapHandler);
        console.log("edge_symbolic_label:", edge_symbolic_label);
        reset_mag_labels();
    }

    // Attach the event listener to edges for click
    cy.on('tap', 'edge', edgeTapHandler);
    document.getElementById("rmv-branch-btn").disabled = true;

    // Update cy style and log loading time
    cy.style().selector('edge').css({ 'content': '' }).update();
    const time2 = new Date();
    let time_elapse = (time2 - time1) / 1000;
    console.log("editBranch SFG loading time: " + time_elapse + " seconds");
}

function remove_edge_request(data) {
    console.log('DELETE request payload:', data);  // Log the payload



    let url = `${baseUrl}/circuits/${circuitId}/edges`;
    console.log("sending DELETE request to:", url);
    fetch(url, {
        method: 'DELETE',
        headers: {
            'Content-Type': 'application/json'
        },
        mode: 'cors',
        credentials: 'same-origin',
        body: JSON.stringify(data)
    })
    .then(response => {
        console.log("received DELETE response from server");
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        removeHighlight();
        console.log("remove_edge_request received data: ", data);
        // update_frontend(data);
    })
    .catch(error => {
        console.error('Error during DELETE request:', error);
        alert('An error occurred while removing the edge. Please check the server logs.');
    });
}

function removeBranchLikeSimplify() {
    console.log("removeBranch is called");
    let cy = window.cy;
    function edgeTapHandler(evt){
        let edge = evt.target;
        edge.style('display', 'none');

        console.log("requesting branch removal")
        
        // ensure matching content format as in the server side
        // for example: source and target
        let form_data = {}
        form_data.source = edge.data('source'); // Get source node ID
        form_data.target = edge.data('target'); // Get target node ID

        console.log("edge id:", edge.id());
        console.log("edge data:", edge.data());
        console.log("form_data:", form_data);

        // Remove the edge from Cytoscape
        edge.remove();

        // Update the backend with the removed branch
        removeBranchLikeSimplify_request(form_data)

        document.getElementById("rmv-branch-btn").disabled = false;
        console.log('edge (edge id) removed:', edge.id());
        cy.off('tap', 'edge', edgeTapHandler);
        console.log("edge_symbolic_label:", edge_symbolic_label);
        reset_mag_labels();
    }

    // Attach the event listener to edges for click
    cy.on('tap', 'edge', edgeTapHandler);
    document.getElementById("rmv-branch-btn").disabled = true;

    // Update cy style and log loading time
    cy.style().selector('edge').css({ 'content': '' }).update();
    const time2 = new Date();
    let time_elapse = (time2 - time1) / 1000;
    console.log("editBranch SFG loading time: " + time_elapse + " seconds");
}

function removeBranchLikeSimplify_request(params) {
    // ensure url matches with the server route
    let url = new URL(`${baseUrl}/circuits/${circuitId}/remove_branch`)
    console.log("sending PATCH request to:", url);
    fetch(url, {
        // ensure meta instructions match with server
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        mode: 'cors',
        credentials: 'same-origin',
        body: JSON.stringify(params)
    })
    .then(response => {
        // ensure response is in readable JSON format
        console.log("received PATCH response from server");
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log("data" , data);
        // console.log("weight", data.sfg.elements.edges[0].data.weight);
        if(stack_len==0){
            disable_undo_btn(false);
        }
        if (redo_len > 0) {
            redo_len = 0;
            disable_redo_btn(true);
        }
        stack_len = stack_len < 5 ? stack_len + 1 : 5
        
        // removeHighlight();
        console.log("remove_edge_request received data: ", data);
        // from old code
        update_frontend(data);
        
        // additional: like the sfg_simplify_request() funciton
        simplify_mode_toggle()
        reset_mag_labels()
    })
    .catch(error => {
        console.log(error)
        // console.error('Error during DELETE request:', error);
        // alert('An error occurred while removing the edge. Please check the server logs.');
    });
}


function getEdgeInfo() {
    console.log("getEdgeInfo is called");
    let cy = window.cy;
    function edgeTapHandler(evt) {
        let edge = evt.target;
        console.log("requesting edge info")
        let form_data = {
            source: edge.data('source'),
            target: edge.data('target')
        };
        console.log("form_data:", form_data);
        getEdgeInfo_request(form_data);

        document.getElementById("edit-branch-btn").disabled = false;
        cy.off('tap', 'edge', edgeTapHandler);
        console.log("edge_symbolic_label:", edge_symbolic_label);
        reset_mag_labels();
    }
    // Attach the event listener to edges for click
    cy.on('tap', 'edge', edgeTapHandler);
    document.getElementById("edit-branch-btn").disabled = true;

    // Update cy style and log loading time
    cy.style().selector('edge').css({ 'content': '' }).update();
    const time2 = new Date();
    let time_elapse = (time2 - time1) / 1000;
    console.log("getEdgeInfo SFG loading time: " + time_elapse + " seconds");
}

function getEdgeInfo_request(params) {
    let url = new URL(`${baseUrl}/circuits/${circuitId}/get_edge_info`)
    url.search = new URLSearchParams(params).toString();
    console.log("sending GET request to:", url.toString());
    fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
        mode: 'cors',
        credentials: 'same-origin',
        // body: JSON.stringify(params)
    })
    .then(response => {
        console.log("received GET response from server");
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('server\'s response data:', data);
        openEditModal(data);
    })
    .catch(error => {
        console.error('Error during GET request:', error);
        // console.error('Error during DELETE request:', error);
        // alert('An error occurred while removing the edge. Please check the server logs.');
    });
}    

function openEditModal(data) {
    clearEdgeInfo();
    // Get the modal element
    var modal = document.getElementById("edge-edit-modal");

    // Get the form and input elements
    var form = document.getElementById("edge-edit-form");
    var symbolicInput = document.getElementById("symbolic");
    //// Not using the magnitude and phase inputs for now
    // var magnitudeInput = document.getElementById("magnitude");
    // var phaseInput = document.getElementById("phase");
    var magnitudeDisplay = document.getElementById("magnitude-value");
    var phaseDisplay = document.getElementById("phase-value");

    console.log('Data:', data);

    // Populate the input fields with data
    symbolicInput.value = data.data.weight.symbolic;
    // magnitudeInput.value = data.data.weight.magnitude;
    // phaseInput.value = data.data.weight.phase;
    magnitudeDisplay.textContent = data.data.weight.magnitude;
    phaseDisplay.textContent = data.data.weight.phase;

    // Show the modal
    modal.style.display = "block";

    // When the user clicks on <span> (x), close the modal
    var span = document.getElementsByClassName("close")[0];
    span.onclick = function() {
        modal.style.display = "none";
    }

    // When the user clicks anywhere outside of the modal, close it
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }

    // Handle form submission
    form.onsubmit = function(event) {
        event.preventDefault();
        // var updatedData = {
        //     symbolic: symbolicInput.value,
        //     magnitude: parseFloat(magnitudeInput.value),
        //     phase: parseFloat(phaseInput.value)
        // };
        // console.log('Updated data:', updatedData);

        data.data.weight.symbolic = symbolicInput.value;
        // data.data.weight.magnitude = parseFloat(magnitudeInput.value);
        // data.data.weight.phase = parseFloat(phaseInput.value);
        console.log('Updated data:', data);
        
        // Send updated data to the server or handle it
        // TODO
        console.log('----------Next Step: send src, tgt, and new symbolic data to server----------');
        console.log('src:', data.data.source);
        console.log('tgt:', data.data.target);
        console.log('symbolic:', data.data.weight.symbolic);

        new_editBranchLikeSimplify(data.data.source, data.data.target, data.data.weight.symbolic);

        modal.style.display = "none";
    };
}


// Function to validate user input against valid keys
function validateInput(userInput) {
    // console.log("keys: ", keys);
    // console.log("latex_keys: ", latex_keys);
    // userInput = userInput.toLowerCase();
    for (let latex_key of latex_keys) {
        // return false if userinput does not include a valid key or is not an integer
        if (userInput.includes(latex_key) || Number.isInteger(parseInt(userInput))) {
            return true;
        }
    }
    return false;
}

// Function to display popup window for editing LaTeX code
function editLatexCode(latexCode, idx) {
    // Open a prompt dialog with the current LaTeX code
    let userInput = prompt("Edit LaTeX code:", latexCode);
    console.log("Edited latex code:", userInput);
    // check if any element in global keys appear in userInput
    if (userInput === null) {
        console.log("editBranch prompt cancelled");
        return latexCode;
    } else if (validateInput(userInput) && userInput !== null && userInput !== '') {
        console.log('editBranch Input is valid');
        edge_symbolic_label[idx] = userInput;
        return userInput;
    } else {
        console.log('Input is invalid');
        alert('Input is invalid\nPlease enter a valid LaTeX code.\nRefer to the list of valid circuit parameters.');
        return latexCode;
    }
}

function editBranchLikeSimplify() {
    console.log("editBranch is called");
    let cy = window.cy;
    function edgeTapHandler(evt){
        let edge = evt.target;

        console.log("requesting branch edit")

        let form_data = {}
        form_data.source = edge.data('source');
        form_data.target = edge.data('target');
        form_data.symbolic = 1;
        console.log("edge id:", edge.id());
        console.log("edge data:", edge.data());
        console.log("form_data:", form_data);


        update_edge_new(form_data);

        document.getElementById("edit-branch-btn").disabled = false;
        console.log('edge (edge id) removed:', edge.id());
        cy.off('tap', 'edge', edgeTapHandler);
        console.log("edge_symbolic_label:", edge_symbolic_label);
        reset_mag_labels();
    }

    // Attach the event listener to edges for click
    cy.on('tap', 'edge', edgeTapHandler);
    document.getElementById("edit-branch-btn").disabled = true;

    // Update cy style and log loading time
    cy.style().selector('edge').css({ 'content': '' }).update();
    const time2 = new Date();
    let time_elapse = (time2 - time1) / 1000;
    console.log("editBranch SFG loading time: " + time_elapse + " seconds");
}

function new_editBranchLikeSimplify(source, target, symbolic) {
    console.log("---------- new_editBranchLikeSimplify is called");

    let form_data = {}
    form_data.source = source;
    form_data.target = target;
    form_data.symbolic = symbolic;
    console.log("form_data:", form_data);

    update_edge_new(form_data);

    // reset_mag_labels();

    // Update cy style and log loading time
    // cy.style().selector('edge').css({ 'content': '' }).update();
    const time2 = new Date();
    let time_elapse = (time2 - time1) / 1000;
    console.log("editBranch SFG loading time: " + time_elapse + " seconds");
}

// Function to edit the selected branch on the SFG
function editBranch() {
    console.log("editBranch is called");
    let cy = window.cy;
    function edgeTapHandler(evt) {
        // console.log("evt target: ", evt.target)
        // console.log("evt: ", evt)

        console.log("BEFORE EDIT: edge_symbolic_label: ", edge_symbolic_label);


        // Retrieve the LaTeX code for the selected edge
        let edge = evt.target;
        let idx = cy.edges().indexOf(edge);
        let latexCode = edge_symbolic_label[idx];
        console.log("LaTeX code for selected edge:", latexCode);
        console.log("Idx:", idx);

        // print edge input, output, and weight
        console.log("edge source: ", edge.data('source'));
        console.log("edge target: ", edge.data('target'));
        console.log("edge weight: ", edge.data('weight'));
        console.log("edge weight symbolic: ", edge.data('weight_symbolic'))
        console.log("edge id: ", edge.id());
        // print all edge data
        console.log("edge data: ", edge.data());

        // Display popup window for editing LaTeX code
        let modifiedLatexCode = editLatexCode(latexCode, idx);
        document.getElementById("edit-branch-btn").disabled = false;
        // print all edge_symbolic_label
        console.log("AFTER EDIT: edge_symbolic_label: ", edge_symbolic_label);

        // Update the keys on parameters based on the modifiedLatexCode
        

        // sfg_patch_request(idx, latexCode, edge.data('source'), edge.data('target'));

        // most recent edit
        // update_edge(edge.data('source'), edge.data('target'), modifiedLatexCode);

        // try using simplify() method
        let form_data = {}
        form_data.source = edge.data('source');
        form_data.target = edge.data('target');
        update_edge()


        // Check if the user made any modifications
        if (modifiedLatexCode !== null) {
            // Update the LaTeX content of the Edge
            console.log("Modified LaTeX code:", modifiedLatexCode);
            
            // // update the sfg frontend and rerender
            // edge.data('weight', modifiedLatexCode);
            // cy.style().selector('edge').css({ 'content': '' }).update();
            // window.cy.style().selector('edge').css({'content': 'data(weight)'}).update();
            // display_mag_sfg();
            reset_mag_labels();
        }

        // Remove the event listener after it's triggered once
        cy.off('tap', 'edge', edgeTapHandler);
    }

    // Attach the event listener to edges for click
    cy.on('tap', 'edge', edgeTapHandler);
    document.getElementById("edit-branch-btn").disabled = true;

    // Update cy style and log loading time
    cy.style().selector('edge').css({ 'content': '' }).update();
    const time2 = new Date();
    let time_elapse = (time2 - time1) / 1000;
    console.log("editBranch SFG loading time: " + time_elapse + " seconds");
}




// function qqremoveBranch() {
//     // Print that this function is called from
//     console.log("removeBranch is called");

//     let cy = window.cy;
//     let updates = new Array(cy.edges().length)
//     let edges = new Array(cy.edges().length)

//     cy.edges().forEach((edge,idx) => {
//         edge.on('tap', function(evt){
//             // Remove the edge from the diagram
//             edge.remove();
//             console.log('Edge removed:', edge);
//         });
//     });


//     // Define the event handler to handle tap events on edges
//     function edgeTapHandler(evt) {
//         let tappedEdge = evt.target; // Get the tapped edge
//         console.log('Tapped Edge:', tappedEdge);

//         // Remove the popper element associated with the tapped edge
//         let edgePopper = tappedEdge.scratch('_popper'); // Retrieve the popper element
//         if (edgePopper) {
//             // print edgepopper content
//             console.log('Edge Popper:', edgePopper);
//             edgePopper.destroy(); // Destroy the popper element
//             console.log('Popper removed:', edgePopper);
//         }

//         // Remove the tapped edge from the diagram
//         tappedEdge.remove();
//         console.log('Edge removed:', tappedEdge);

//         //re-render the SFG


//         // Turn off the event handler after the first edge has been removed
//         cy.off('tap', 'edge', edgeTapHandler);
//     }

//     // Attach the event handler to listen for tap events on edges
//     cy.on('tap', 'edge', edgeTapHandler);

//     // // Define the event handler to handle remove events on edges
//     // function edgeRemoveHandler(evt) {
//     //     let removedEdge = evt.target; // Get the removed edge
//     //     console.log('Removed Edge:', removedEdge);

//     //     // Remove the popper element associated with the removed edge
//     //     let edgePopper = removedEdge.scratch('_popper'); // Retrieve the popper element
//     //     if (edgePopper) {
//     //         edgePopper.destroy(); // Destroy the popper element
//     //         console.log('Popper removed:', edgePopper);
//     //     }
//     //     cy.off('remove', 'edge', edgeRemoveHandler);
//     // }

//     // // Attach the event handler to listen for remove events on edges
//     // cy.on('remove', 'edge', edgeRemoveHandler);
// }

// // Removes the selected branch from the diagram
// function primitiveremoveBranch() {
//     // Print that this function is called from
//     console.log("removeBranch is called");

//     // Get the edge that is clicked
//     // function edgeTapHandler(evt) {
//     //     cy.edges().forEach((edge, idx) => {
//     //         edge.on('tap', function(evt){
//     //             // Remove the edge from the diagram
//     //             edge.remove();
//     //             console.log('Edge removed:', edge);
//     //         });
//     //     });
//     //     // Turn off the event handler after the first edge has been removed
//     //     cy.off('tap', 'edge', edgeTapHandler);
//     // }
    

//     // Define the event handler to handle tap events on edges
//     function edgeTapHandler(evt) {
//         let tappedEdge = evt.target; // Get the tapped edge
//         console.log('Tapped Edge:', tappedEdge);

//         // Remove the tapped edge from the diagram
//         tappedEdge.remove();
//         reset_mag_labels();
//         console.log('Edge removed:', tappedEdge);
        
//         // // Remove the popper element associated with the tapped edge
//         // let edgePopper = tappedEdge.scratch('_popper');
//         //     if (edgePopper) {
//         //     edgePopper.destroy();
//         //     console.log('Popper removed:', edgePopper);
//         // }

//         // // Update the edges
//         // tappedEdge.update();


//         // Turn off the event handler after the first edge has been removed
//         cy.off('tap', 'edge', edgeTapHandler);
//     }

//     // Attach the event handler to listen for tap events on edges
//     cy.on('tap', 'edge', edgeTapHandler);
// }

function  display_mag_sfg() {
    let cy = window.cy;

    let updates = new Array(cy.edges().length)
    let edges = new Array(cy.edges().length)

    cy.edges().forEach((edge,idx) => {
        
        // print each edge
        // console.log('Edge:', edge);
        // console.log('Edges[idx]: ', edges[idx]);

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

// declare global array of keys
keys = []
latex_keys = []

function convertToLatex(sympyCharacters) {
    console.log("length of sympyCharacters: ", sympyCharacters.length)
    if(sympyCharacters.length == 2){
        // check if the first character is a char and the second is a number
        if(sympyCharacters[0].match(/[a-z]/i) && !isNaN(sympyCharacters[1])){
            // add underscore between the first and second character
            sympyCharacters = sympyCharacters[0] + '_{' + sympyCharacters[1] + '}';
        }
        return sympyCharacters;
    }
    
    
    // Regular expression to match underscores
    const underscoreRegex = /_/g;
    // Convert each sympy character to its LaTeX representation
    // const latexCharacters = sympyCharacters.map(char => char.replace(underscoreRegex, '_{'));
    const latexCharacters = sympyCharacters.replace(underscoreRegex, '_{');
    console.log("latexCharacters: ", latexCharacters);
    return latexCharacters;
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
        // console.log("key: " + key + " value: " + parameters[key])
        // keys.push(key)
        // latex_key = convertToLatex(key)
        // latex_keys.push(latex_key)
        // console.log("keys array: " + keys) // iterating
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
    console.log("keys: " + keys) // all final keys
    console.log("latex_keys: " + latex_keys)
    
    var s = document.createElement("input")
    s.setAttribute("type", "submit")
    s.setAttribute("value", "Submit Form")
    pf.appendChild(s)

    console.log("freq: " + freq)
    output.innerHTML = freq
    frequency_slider.value = freq

    //add event listener
    pf.addEventListener("submit", async function (event) {
        event.preventDefault()

        let form_data = {}
        //making input
        console.log("---------- parameters: ", parameters)
        for (let key in parameters) {
            let i = document.querySelector(`#${key}`).value
            console.log("---------- key: " + key + " value: " + i)
            if (i != "") {
                form_data[key] = parseFloat(i)
            }
        }
        console.log("form_data: ", form_data)
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
    .then(response => {
        if (!response.ok) {
            // Handle HTTP errors
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        removeHighlight()
        console.log(data)
        update_frontend(data)
    })
    .catch(error => {
        console.error('Error during PATCH request:', error);
        alert('An error occurred while updating the circuit. Please check the server logs.');
    });
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
        if (redo_len > 0) {
            redo_len = 0;
            disable_redo_btn(true);
        }
        stack_len = stack_len < 5 ? stack_len + 1 : 5
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
            document.getElementById("rmv-branch-btn").disabled = true;
            document.getElementById("edit-branch-btn").disabled = true;
        }
        else {
            document.getElementById("frequency-slider").disabled = true;
            document.getElementById("rmv-branch-btn").disabled = false;
            document.getElementById("edit-branch-btn").disabled = false;
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

// Auto-fills the transfer function panel when click on desired nodes
function click_node_make_transfer_func_panel() {
    // Track the selected nodes
    let selectedNodes = [];

    // Add click event listener to nodes
    cy.on('click', 'node', function(event) {
        let node = event.target;
        let nodeId = node.id();

        if (selectedNodes.length === 0) {
            // Set the input node
            document.getElementById('input_node').value = nodeId;
            document.getElementById('input_node_bode').value = nodeId;
            selectedNodes.push(nodeId);
        } else if (selectedNodes.length === 1) {
            // Set the output node
            document.getElementById('output_node').value = nodeId;
            document.getElementById('output_node_bode').value = nodeId;
            selectedNodes.push(nodeId);
        } else {
            // Reset the selection if both nodes are already selected
            document.getElementById('input_node').value = '';
            document.getElementById('output_node').value = '';
            document.getElementById('input_node_bode').value = '';
            document.getElementById('output_node_bode').value = '';
            selectedNodes = [];
        }
    });
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

    click_node_make_transfer_func_panel()

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

function update_edge_new(params) {
    console.log("********** running update_edge_new **********")
    var url = new URL(`${baseUrl}/circuits/${circuitId}/update_edge_new`);
    // var url = `${baseUrl}/circuits/${circuitId}/update_edge_new`;
    
    console.log("Final URL with parameters:", url.href);
    console.log("sending PATCH request to:", url);

    fetch(url, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        mode: 'cors',
        credentials: 'same-origin',
        body: JSON.stringify(params)
    })
    .then(response => {
        if (!response.ok) {
            // If response is not ok (i.e., in error status range), reject the promise
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        // If response is ok, return JSON promise
        return response.json();
    })
    .then(data => {
        console.log("success!");
        update_frontend(data);
        reset_mag_labels();
    })
    .catch(error => {
        console.error('update_edge error!:', error);
        console.log('update_edge Full response:', error.response);
    });
}

function update_edge(input_node, output_node, symbolic_value) {
    var url = new URL(`${baseUrl}/circuits/${circuitId}/update_edge`);
    params = {input_node: input_node, output_node: output_node, symbolic_value: symbolic_value}
    console.log("URL before appending parameters:", url.href);
    Object.keys(params).forEach(key => {
        const value = params[key].toString();
        url.searchParams.append(key, value);
    });
    console.log("Final URL with parameters:", url.href);

    fetch(url, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        mode: 'cors',
        credentials: 'same-origin',
        body: JSON.stringify(params)
    })
    .then(response => {
        if (!response.ok) {
            // If response is not ok (i.e., in error status range), reject the promise
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        // If response is ok, return JSON promise
        return response.json();
    })
    .then(data => {
        console.log("success!");
    })
    .catch(error => {
        console.error('update_edge error!:', error);
        console.log('update_edge Full response:', error.response);
    });
}

async function tf_toggle() {
    console.log("********** running tf_toggle **********")
    console.log("tf_flag: ", tf_flag)
    console.log("input_node: ", tf.input)
    console.log("output_node: ", tf.output)
    if (tf.input && tf.output){
        tf_flag = !tf_flag
        try{
            const time1 = new Date()
            // TODO Mark
            // copy make_transfer_func fetch logic
            let latex_toggle = true
            let factor_toggle = true
            let params = {input_node: tf.input, output_node: tf.output, latex: latex_toggle,
                factor: factor_toggle, numerical: tf_flag}
            var url = new URL(`${baseUrl}/circuits/${circuitId}/transfer_function`)
    
            // print the base url
            console.log('base url for make_transfer_func: ', baseUrl)
    
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
                console.log("make_transfer_func fetch response: ", response)
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
                // print trans.innerHTML
                console.log("trans.innerHTML: " + trans.innerHTML)
                // what does trans.innerHTML do?
    
    
                console.log(data)
                //reset MathJax
                MathJax.typeset()
            })
            .catch(error => {
                console.error('make_transfer_func error:', error);
                console.log('make_transfer_func Full response:', error.response);
            });
    
            const time2 = new Date()
            let time_elapse = (time2 - time1)/1000
            console.log("Transfer function tf_toggle time (numeric <-> symbolic): " + time_elapse + " seconds")
        } catch {
            alert("error when toggle transfer function numeric <-> symbolic")
        }
    } else {
        //  uncheck the checkbox
        let tf_toggle_button = document.getElementById("tf-toggle");
        tf_toggle_button.checked = false
        alert("input field incomplete")
    }
}

let tf_toggle_button = document.getElementById("tf-toggle");
if (tf_toggle_button) {
    tf_toggle_button.addEventListener('click', tf_toggle)
}
    
function make_transfer_func(input_node, output_node) {
    console.log("********** runnning make_transfer_func **********")
    let latex_toggle = true
    let factor_toggle = true
    let numerical_toggle = tf_flag
    let params = {input_node: input_node, output_node: output_node, latex: latex_toggle,
        factor: factor_toggle, numerical: numerical_toggle}
    var url = new URL(`${baseUrl}/circuits/${circuitId}/transfer_function`)
    
    tf.input = input_node
    tf.output = output_node
    console.log("tf.input: ", tf.input)
    console.log("tf.output: ", tf.output)

    // print the base url
    console.log('base url for make_transfer_func: ', baseUrl)

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
        console.log("make_transfer_func Fetch response: ", response)
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
        // print trans.innerHTML
        console.log("trans.innerHTML: " + trans.innerHTML)
        // what does trans.innerHTML do?


        console.log(data)
        //reset MathJax
        MathJax.typeset()
    })
    .catch(error => {
        console.error('make_transfer_func error:', error);
        console.log('make_transfer_func Full response:', error.response);
    });
}


function make_schematics(data) {
    if (data.svg == null) {
        console.log("no SVG available")
    }
    else {
        var svg_html = document.getElementById("circuit-svg")
        var svg_html_small = document.getElementById("circuit-svg-small")

        svg_html.innerHTML = data.svg
        svg_html_small.innerHTML = data.svg
        const svg = document.querySelector("#circuit-svg > svg")
        const svg_small = document.querySelector("#circuit-svg-small > svg")
        
        // Get the bounding box of all sub-elements inside the <svg>.
        const bbox = svg.getBBox();
        const bbox_small = svg_small.getBBox();
        // Set the viewBox attribute of the SVG such that it is slightly bigger than the bounding box.
        svg.setAttribute("viewBox", (bbox.x-10)+" "+(bbox.y-10)+" "+(bbox.width+20)+" "+(bbox.height+20));
        svg.setAttribute("width", (bbox.width+20)  + "px");
        svg.setAttribute("height",(bbox.height+20) + "px");
        svg_small.setAttribute("viewBox", (bbox_small.x-10)+" "+(bbox_small.y-10)+" "+(bbox_small.width+20)+" "+(bbox_small.height+20));
        svg_small.setAttribute("width", (bbox_small.width)  + "px");
        svg_small.setAttribute("height",(bbox_small.height) + "px");
        // Add a black border to the SVG so it's easier to visualize it.
        svg.setAttribute("style", "border:1px solid black");
        svg.setAttribute("height", "600px");
        svg.setAttribute("width", "1200px");
        // svg_small.setAttribute("style", "border:1px solid black");
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
                if ((form_entry != 'input_node_bode') && (form_entry != "output_node_bode")) {
                    form_params[form_entry] = parseFloat(input);
                }
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

    // fetch(url)
    // .then(response => response.json())
    // .then(data => {
    //     make_bode_plots(data, 'transfer-bode-plot')
    // })

    fetch(url)
    .then(response => {
        if (!response.ok) {
            // If response is not ok (i.e., in error status range), reject the promise
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        // If response is ok, return JSON promise
        console.log("fetch_transfer_bode_data fetch OK.")
        return response.json();
    })
    .then(data => {
        // for user: have a button to save bode plat ("data") ==> in an tuple array or stack somewhere
        // the user should be able to click save at any time (many versions of the bode plot "data")
        // also show a new updated bode plot from the most recent "data"
        make_bode_plots(data, 'transfer-bode-plot')
        createOverlayButtons('transfer-bode-plot', 'transfer-bode');
        console.log("trasfer bode plot data:");
        console.log(data);
    })
    .catch(error => {
        console.error('fetch_transfer_bode_data error:', error);
        console.log('fetch_transfer_bode_data Full response:', error.response);
    });



}

function make_bode_plots(data, dom_element, overlayData = null) {
    let freq_points = [];
    let gain_points = [];
    let phase_points = [];
    let frequency = data["frequency"];
    let gain = data["gain"];
    let phase = data["phase"];

    // Select the appropriate history array
    let historyArray = dom_element === 'transfer-bode-plot' ? transfer_bode_plot_history : loop_gain_bode_plot_history;

    // Check if the incoming data is different from the last entry in the history
    let isDifferent = true;
    if (historyArray.length > 0) {
        let lastData = historyArray[historyArray.length - 1];
        isDifferent = !(_.isEqual(lastData, data));  // Using lodash to compare objects
    }

    // Push data to history only if it's different and not an overlay
    if (isDifferent && overlayData === null) {
        historyArray.push(data);
        console.log(dom_element + " history:", historyArray);
    }

    for (let i = 0; i < frequency.length; i++) {
        freq_points.push(Number.parseFloat(frequency[i].toExponential(0)).toFixed(0));

        gain_points.push({
            x: frequency[i],
            y: gain[i]
        });

        phase_points.push({
            x: frequency[i],
            y: phase[i]
        });
    }

    let datasets = [{
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
    }];

    // Add overlay data if provided
    if (overlayData) {
        let overlay_gain_points = [];
        let overlay_phase_points = [];

        for (let i = 0; i < overlayData.frequency.length; i++) {
            overlay_gain_points.push({
                x: overlayData.frequency[i],
                y: overlayData.gain[i]
            });

            overlay_phase_points.push({
                x: overlayData.frequency[i],
                y: overlayData.phase[i]
            });
        }

        datasets.push({
            label: 'Gain overlay',
            borderColor: 'rgba(255, 0, 0, 0.5)',
            backgroundColor: 'rgba(255, 0, 0, 0.5)',
            fill: false,
            data: overlay_gain_points,
            yAxisID: 'y-axis-1',
            borderDash: [5, 5],  // Dotted line
        }, {
            label: 'Phase overlay',
            borderColor: 'rgba(0, 102, 255, 0.5)',
            backgroundColor: 'rgba(0, 102, 255, 0.5)',
            fill: false,
            data: overlay_phase_points,
            yAxisID: 'y-axis-2',
            borderDash: [5, 5],  // Dotted line
        });
    }

    let ctx = document.getElementById(dom_element).getContext('2d');
    window.myLine = new Chart(ctx, {
        type: 'line',
        data: {
            labels: freq_points,
            datasets: datasets
        },
        options: {
            responsive: true,
            hoverMode: 'index',
            stacked: false,
            title: {
                display: true,
                text: dom_element === 'transfer-bode-plot' ? 'Transfer Function Bode Plot' : 'Loop Gain Bode Plot'
            },
            scales: {
                xAxes: [{
                    afterTickToLabelConversion: function(data){
                        var xLabels = data.ticks;
                        xLabels.forEach((label, i) => {
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
                    }
                }]
            }
        }
    });
}


function mid_make_bode_plots(data, dom_element, overlayData = null) {
    let freq_points = []
    let gain_points = [];
    let phase_points = [];
    let frequency = data["frequency"]
    let gain = data["gain"]
    let phase = data["phase"]

    // save data to global variable to keep track of history
    if (dom_element === 'transfer-bode-plot') {
        transfer_bode_plot_history.push(data)
        console.log("transfer_bode_plot_history: ", transfer_bode_plot_history)
    } else if (dom_element === 'loop-gain-bode-plot') {
        loop_gain_bode_plot_history.push(data)
        console.log("loop_gain_bode_plot_history: ", loop_gain_bode_plot_history)
    }

    for (let i = 0; i < frequency.length; i++) {
        freq_points.push(Number.parseFloat(frequency[i].toExponential(0)).toFixed(0))

        gain_points.push({
            x: frequency[i],
            y: gain[i]
        });

        phase_points.push({
            x: frequency[i],
            y: phase[i]
        });
    }

    let datasets = [{
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
    }];

    // Add overlay data if provided
    if (overlayData) {
        console.log("********** overlayData **********")
        let overlay_freq_points = [];
        let overlay_gain_points = [];
        let overlay_phase_points = [];

        for (let i = 0; i < overlayData.frequency.length; i++) {
            overlay_freq_points.push(Number.parseFloat(overlayData.frequency[i].toExponential(0)).toFixed(0))

            overlay_gain_points.push({
                x: overlayData.frequency[i],
                y: overlayData.gain[i]
            });

            overlay_phase_points.push({
                x: overlayData.frequency[i],
                y: overlayData.phase[i]
            });
        }

        datasets.push({
            label: 'New Gain Overlay',
            borderColor: 'rgba(255, 0, 0, 0.5)',
            backgroundColor: 'rgba(255, 0, 0, 0.5)',
            fill: false,
            data: overlay_gain_points,
            yAxisID: 'y-axis-1',
            borderDash: [5, 5],  // Dotted line
        }, {
            label: 'New Phase Overlay',
            borderColor: 'rgba(0, 102, 255, 0.5)',
            backgroundColor: 'rgba(0, 102, 255, 0.5)',
            fill: false,
            data: overlay_phase_points,
            yAxisID: 'y-axis-2',
            borderDash: [5, 5],  // Dotted line
        });
    }

    let ctx = document.getElementById(dom_element).getContext('2d');
    window.myLine = new Chart(ctx, {
        type: 'line',
        data: {
            labels: freq_points,
            datasets: datasets
        },
        options: {
            responsive: true,
            hoverMode: 'index',
            stacked: false,
            title: {
                display: true,
                text: dom_element === 'transfer-bode-plot' ? 'Transfer Function Bode Plot' : 'Loop Gain Bode Plot'
            },
            scales: {
                xAxes: [{
                    afterTickToLabelConversion: function(data){
                        var xLabels = data.ticks;
                        xLabels.forEach((label, i) => {
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
                    }
                }]
            }
        }
    });
    // Call this function after the first plot is made
    // if (transfer_bode_plot_history.length > 1) {
    //     createOverlayButtons('transfer-bode-plot', 'transfer-bode');
    // }
    // if (loop_gain_bode_plot_history.length > 1) {
    //     createOverlayButtons('loop-gain-bode-plot', 'loop-gain-bode');
    // }
}

function createOverlayButtons(dom_element, targetDivId) {
    console.log("********** running createOverlayButtons **********");
    let historyArray = dom_element === 'transfer-bode-plot' ? transfer_bode_plot_history : loop_gain_bode_plot_history;
    console.log("historyArray: ", historyArray);

    // Check if the buttonContainer already exists
    let targetDiv = document.getElementById(targetDivId);
    let buttonContainer = document.getElementById(`${dom_element}-overlay-buttons`);
    let clear_button = document.createElement('button');
    clear_button.textContent = `Clear History`;
    clear_button.onclick = function() {
        historyArray.length = 0;
        let ctx = document.getElementById(dom_element).getContext('2d');
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        buttonContainer.innerHTML = '';  // Clear the button container
    }
    

    if (!buttonContainer) {
        // Create a new buttonContainer if it doesn't exist
        buttonContainer = document.createElement('div');
        buttonContainer.id = `${dom_element}-overlay-buttons`;

        if (targetDiv) {
            targetDiv.appendChild(buttonContainer);  // Append to the specified target div
        } else {
            console.error(`Target div with id ${targetDivId} not found.`);
            return;
        }
    }

    // Clear existing buttons to avoid duplicates
    buttonContainer.innerHTML = '';

    buttonContainer.appendChild(clear_button);
    
    // Add buttons for each plot in history
    historyArray.forEach((data, index) => {
        let button = document.createElement('button');
        button.textContent = `Overlay Plot ${index}`;
        button.onclick = function() {
            let overlayData = historyArray[index];
            make_bode_plots(historyArray[0], dom_element, overlayData);  // Overlay selected plot over the original (index 0)
        };
        buttonContainer.appendChild(button);
    });
}


function old_createOverlayButtons(dom_element, targetDivId) {
    console.log("********** running createOverlayButtons **********")
    let historyArray = dom_element === 'transfer-bode-plot' ? transfer_bode_plot_history : loop_gain_bode_plot_history;
    console.log("historyArray: ", historyArray)

    let buttonContainer = document.createElement('div');
    buttonContainer.id = `${dom_element}-overlay-buttons`;

    historyArray.forEach((data, index) => {
        let button = document.createElement('button');
        button.textContent = `Overlay Plot ${index}`;
        button.onclick = function() {
            let overlayData = historyArray[index];
            make_bode_plots(historyArray[0], dom_element, overlayData);  // Overlay selected plot over the original (index 0)
        };
        buttonContainer.appendChild(button);
    });

    // document.body.appendChild(buttonContainer);  // Add the button container to the body (or any other desired location)
    let targetDiv = document.getElementById(targetDivId);
    if (targetDiv) {
        targetDiv.appendChild(buttonContainer);  // Append buttons to the specified target div
    } else {
        console.error(`Target div with id ${targetDivId} not found.`);
    }
}


function old_make_bode_plots(data, dom_element) {
    let freq_points = []
    let gain_points = [];
    let phase_points = [];
    let frequency = data["frequency"]
    let gain = data["gain"]
    let phase = data["phase"]

    // save data to global variable to keep track of history
    if (dom_element === 'transfer-bode-plot') {
        transfer_bode_plot_history.push(data)
        console.log("transfer_bode_plot_history: ", transfer_bode_plot_history)
    } else if (dom_element === 'loop-gain-bode-plot') {
        loop_gain_bode_plot_history.push(data)
        console.log("loop_gain_bode_plot_history: ", loop_gain_bode_plot_history)
    }
    // bode_plot_history.push(data)
    // console.log("bode_plot_history: ", bode_plot_history)

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

async function lg_toggle() {
    console.log("********** running lg_toggle **********")
    lg_flag = !lg_flag
    console.log("lg_flag: ", lg_flag)
    try {
        const time1 = new Date()
        // TODO Mark
        // copy make_loop_gain fetch logic
        let latex_toggle = true
        let factor_toggle = true
        let params = {latex: latex_toggle, factor: factor_toggle, numerical: lg_flag}
        var url = new URL(`${baseUrl}/circuits/${circuitId}/loop_gain`)

        // print the base url
        console.log('base url for make_loop_gain: ', baseUrl)

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
            console.log("make_loop_gain fetch response: ", response)
            return response.json();
        })
        .then(data => {
            console.log("data");
            console.log(data);
            console.log("loop gain data:", data.loop_gain);
            var loop_gain = document.getElementById("loop-gain")
            let latex_loop_gain = "\\(" + data.loop_gain + "\\)"
            loop_gain.innerHTML = latex_loop_gain
            
            console.log(data)
            //reset MathJax
            MathJax.typeset()
        })
        .catch(error => {
            console.error('make_loop_gain Fetch error:', error);
            console.log('make_loop_gain Full response:', error.response);
        });

        const time2 = new Date()
        let time_elapse = (time2 - time1)/1000
        console.log("Loop gain lg_toggle time (numeric <-> symbolic): " + time_elapse + " seconds")
    } catch {
        alert("error when toggle loop gain numeric <-> symbolic")
    }
}

let lg_toggle_button = document.getElementById("lg-toggle");
if (lg_toggle_button) {
    lg_toggle_button.addEventListener('click', lg_toggle)
}

function make_loop_gain() {
    console.log("********** runnning make_loop_gain **********")
    let latex_toggle = true
    let factor_toggle = true
    let numerical_toggle = lg_flag
    let params = {latex: latex_toggle, factor: factor_toggle, numerical: numerical_toggle}
    var url = new URL(`${baseUrl}/circuits/${circuitId}/loop_gain`)

    // print the base url
    console.log("base url for make_loop_gain:", baseUrl);

    // print out the created url
    console.log("url:", url)
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
        console.log("make_loop_gain Fetch response:", response);
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
        console.log("loop_gain.innerHTML:", loop_gain.innerHTML)
        console.log(data)
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
    Object.keys(input_params).forEach(key => url.searchParams.append(key, parseFloat(input_params[key])))

    // fetch(url)
    // .then(response => response.json())
    // .then(data => {
    //     make_bode_plots(data, 'loop-gain-bode-plot')
    // })

    fetch(url)
    .then(response => {
        if (!response.ok) {
            // If response is not ok (i.e., in error status range), reject the promise
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        // If response is ok, return JSON promise
        console.log("fetch_loop_gain_bode_data OK.")
        return response.json();
    })
    .then(data => {
        make_bode_plots(data, 'loop-gain-bode-plot')
        createOverlayButtons('loop-gain-bode-plot', 'loop-gain-bode');
        console.log("loop gain bode plot data:");
        console.log(data);
    })
    // .catch(error => {
    //     console.error('fetch_loop_gain_bode_data error:', error);
    //     console.log('fetch_loop_gain_bode_data Full response:', error.response);
    // });
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

function simplify()
{
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

// This function simplifies the entire graph 
// Removing dead branches and removing unecessary branches if needed 
function sfg_simplification_entire_graph(params) {
    const url = new URL(`${baseUrl}/circuits/${circuitId}/simplification`);

    fetch(url, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        if (stack_len === 0) {
            disable_undo_btn(false);
        }
        if (redo_len > 0) {
            redo_len = 0;
            disable_redo_btn(true);
        }
        stack_len = Math.min(stack_len + 1, 5);
        update_frontend(data);
        simplify_mode_toggle();
        reset_mag_labels();
    })
    .catch(error => {
        console.error('Error during SFG simplification:', error);
        alert('There was an error simplifying the graph. Please try again.');
    });
}



function simplify_entire_graph() 
{
    console.log("Requesting entire graph simplification");
    
    // Optional: Set up any parameters you want to pass.
    let params = {}; // Add any needed parameters here
    
    // Call the simplification request function
    sfg_simplification_entire_graph(params);
}


// This function simplifies the entire graph 
// Removing dead branches and removing unecessary branches if needed 
function sfg_simplification_entire_graph_trivial(params) {
    const url = new URL(`${baseUrl}/circuits/${circuitId}/simplificationgraph`);

    fetch(url, {
        method: 'PATCH',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(params)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json();
    })
    .then(data => {
        if (stack_len === 0) {
            disable_undo_btn(false);
        }
        if (redo_len > 0) {
            redo_len = 0;
            disable_redo_btn(true);
        }
        stack_len = Math.min(stack_len + 1, 5);
        update_frontend(data);
        simplify_mode_toggle();
        reset_mag_labels();
    })
    .catch(error => {
        console.error('Error during SFG simplification:', error);
        alert('There was an error simplifying the graph. Please try again.');
    });
}



function simplify_entire_graph_trivial() 
{
    console.log("Requesting entire graph simplification");
    
    // Optional: Set up any parameters you want to pass.
    let params = {}; // Add any needed parameters here
    
    // Call the simplification request function
    sfg_simplification_entire_graph_trivial(params);
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
        redo_len++;
        if (stack_len === 0) {
            disable_undo_btn(true);
        }
        if (redo_len > 0) {
            disable_redo_btn(false);
        }
        update_frontend(data);
        reset_mag_labels();
        console.log(stack_len);
        console.log(redo_len);
    })
    .catch(error => {
        console.log(error)
    })
}

function sfg_redo_request(params) {

    let url = new URL(`${baseUrl}/circuits/${circuitId}/redo`)

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
        stack_len++;
        redo_len--;
        if (redo_len === 0) {
            disable_redo_btn(true);
        }
        if (stack_len > 0) {
            disable_undo_btn(false);
        }
        update_frontend(data);
        reset_mag_labels();
        console.log(stack_len);
        console.log(redo_len);
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

function sfg_redo(){
    if (redo_len > 0){
        sfg_redo_request();
    }
    else {
        disable_redo_btn(true);
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