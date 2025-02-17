from flask import (
    Flask,
    request,
    abort,
    send_from_directory,
    Response,
    send_file,
    jsonify,
)
from flask_cors import CORS
from distutils.util import strtobool
import tempfile
import dill
import json
import sympy

import db


app = Flask(__name__)
# app.config['DEBUG'] = False
CORS(app)


@app.route("/favicon.ico")
def favicon():
    return send_file("favicon.ico", mimetype="image/vnd.microsoft.icon")


@app.route("/app/<path:path>")
def serve_webpage(path):
    return send_from_directory("public", path)


@app.route("/circuits/<circuit_id>", methods=["GET"])
def get_circuit(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description="Circuit not found")

    try:
        fields = request.args.get("fields", type=lambda s: s and s.split(",") or None)
        print("--------------------fields: " + str(fields))
        print(circuit.to_dict(fields))
        return circuit.to_dict(fields)

    except Exception as e:
        abort(400, description=str(e))


@app.route("/circuits", methods=["POST"])
def create_circuit():
    name = request.json["name"]
    netlist = request.json["netlist"]

    schematic = request.json.get("schematic")
    op_point_log = request.json.get("op_point_log")

    try:
        circuit = db.Circuit.create(name, netlist, schematic, op_point_log)
    except Exception as e:
        abort(400, str(e))

    try:
        fields = request.args.get("fields", type=lambda s: s and s.split(",") or None)
        return circuit.to_dict(fields)

    except Exception as e:
        abort(400, description=str(e))


@app.route("/circuits/<circuit_id>", methods=["PATCH"])
def patch_circuit(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()
    if not circuit:
        abort(404, description="Circuit not found")

    circuit.update_parameters(request.json)
    circuit.save()

    try:
        fields = request.args.get("fields", type=lambda s: s and s.split(",") or None)

        print("fields: " + str(fields))
        print(circuit.to_dict(fields))

        return circuit.to_dict(fields)

    except Exception as e:
        abort(400, description=str(e))


@app.route("/circuits/<circuit_id>/update_edge", methods=["PATCH"])
def update_edge(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()
    if not circuit:
        abort(404, description="Circuit not found")

    try:
        input_node = request.args.get("input_node")
        output_node = request.args.get("output_node")
        symbolic = request.args.get("symbolic")

        circuit.edit_edge(input_node, output_node, symbolic)
        circuit.save()

        fields = request.args.get("fields", type=lambda s: s and s.split(",") or None)

        return circuit.to_dict(fields)

    except Exception as e:
        abort(400, description=str(e))


@app.route("/circuits/<circuit_id>/update_edge_new", methods=["PATCH"])
def update_edge_new(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()
    if not circuit:
        abort(404, description="Circuit not found")

    print("Received data:", request.json)

    input_node = request.json.get("source")
    output_node = request.json.get("target")
    symbolic = request.json.get("symbolic")

    print("got the input_node, output_node, and symbolic")

    if not input_node or not output_node or not symbolic:
        abort(400, description="Missing source, target, or symbolic data")

    try:
        print("Attempting to edit edge with the following data:")
        print(f"Source: {input_node}, Target: {output_node}, Symbolic: {symbolic}")

        # Call the edit_edge function, print debug info before and after
        print("Calling circuit.edit_edge()...")
        circuit.edit_edge(input_node, output_node, symbolic)
        print("Successfully called circuit.edit_edge()")

        print("Saving circuit...")
        circuit.save()
        print("Circuit saved successfully")

        fields = request.args.get("fields", type=lambda s: s and s.split(",") or None)
        # print fields
        print("fields: " + str(fields))
        print(circuit.to_dict(fields))
        return circuit.to_dict(fields)

    except Exception as e:
        abort(400, description=str(e))


# @app.route('/circuits/<circuit_id>/edges', methods=['DELETE'])
# def remove_edge(circuit_id):
#     circuit = db.Circuit.objects(id=circuit_id).first()
#     if not circuit:
#         abort(404, description='Circuit not found')

#     try:
#         print("trying remove_edge server side")
#         print("request: " + str(request))
#         data = request.get_json()
#         source = data.get('source')
#         target = data.get('target')

#         # Validate the data
#         if not source or not target:
#             raise ValueError('Invalid parameters.')

#         # print all edges of circuit
#         print("circuit edges: " + str(circuit.edges))
#         # get edge from circuit
#         edge = circuit.get_edge(source, target)
#         print("edge: " + str(edge))

#         # # Deserialize the SFG
#         # sfg = dill.loads(circuit.sfg)

#         # # Remove the specified edge
#         # if sfg.has_edge(source, target):
#         #     sfg.remove_edge(source, target)
#         # else:
#         #     raise ValueError('Edge not found in the graph.')

#         # # Serialize the updated SFG back to the binary field
#         # circuit.sfg = dill.dumps(sfg)
#         # circuit.save()

#         # # Fetch the updated SFG elements
#         # updated_sfg_elements = {
#         #     'nodes': [{'data': {'id': node, 'name': node}} for node in sfg.nodes],
#         #     'edges': []
#         # }
#         # for src, dst in sfg.edges:
#         #     weight = sfg.edges[src, dst]['weight']
#         #     symbolic = weight['symbolic']
#         #     if isinstance(symbolic, sympy.Basic):
#         #         symbolic = sympy.latex(symbolic)
#         #     updated_sfg_elements['edges'].append({
#         #         'data': {
#         #             'id': f'{src}_{dst}',
#         #             'source': src,
#         #             'target': dst,
#         #             'weight': {
#         #                 'symbolic': symbolic,
#         #                 'magnitude': weight['magnitude'],
#         #                 'phase': weight['phase']
#         #             }
#         #         }
#         #     })

#         # # unimplemented edge removal logic
#         # # # Logic to remove the edge from the database
#         # # # Example: Circuit.objects.filter(id=circuit_id).update(pull__edges={'source': source, 'target': target})
#         # # Logic to remove the edge from the database
#         # # Assuming your edge structure is like {'source': 'node1', 'target': 'node2'}
#         # circuit.update(pull__edges={'source': source, 'target': target})

#         # # Fetch the updated circuit
#         # circuit.reload()

#         # # Extract the updated SFG elements
#         # updated_sfg_elements = {
#         #     'nodes': [{'data': node.to_dict()} for node in circuit.nodes],
#         #     'edges': [{'data': edge.to_dict()} for edge in circuit.edges]
#         # }

#         # # # Simulate the updated SFG elements to send back to the frontend
#         # # updated_sfg_elements = {
#         # #     'nodes': [],  # Add your updated nodes here
#         # #     'edges': []   # Add your updated edges here
#         # # }

#         # # # return jsonify({"message": "Edge removed successfully", "sfg": {"elements": updated_sfg_elements}}), 200


#         # existing response update logic
#         fields = request.args.get(
#             'fields',
#             type=lambda s: s and s.split(',') or None
#         )

#         # print fields
#         # print("fields: " + str(fields))
#         # print(circuit.to_dict(fields))

#         return circuit.to_dict(fields)
#         # return jsonify({
#         #     "message": "Edge removed successfully",
#         #     "sfg": {"elements": updated_sfg_elements}
#         # }), 200

#     except ValueError as e:
#         app.logger.error(f"ValueError: {e}")
#         return jsonify({"error": str(e)}), 400  # Return 400 Bad Request for client-side errors
#     except Exception as e:
#         app.logger.error(f"Error removing edge in circuit {circuit_id}: {e}")
#         return jsonify({"error": "Internal Server Error"}), 500


# note to self: remove_edge is old
# remove_branch is new and uses similar logic to simplify_circuit
# url for the server route, matching method
@app.route("/circuits/<circuit_id>/remove_branch", methods=["PATCH"])
def remove_branch(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description="Circuit not found")

    # ensure content has matching format, for example: source and target
    source = request.json.get("source")
    target = request.json.get("target")

    try:
        circuit.remove_branch_sfg(source, target)
        circuit.save()

        fields = request.args.get("fields", type=lambda s: s and s.split(",") or None)

        # print fields
        print("fields: " + str(fields))
        print(circuit.to_dict(fields))

        # response = circuit.to_dict(fields)
        # response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        # response.headers['Pragma'] = 'no-cache'
        # response.headers['Expires'] = '0'
        # return jsonify(response), 200
        return circuit.to_dict(fields)

    except Exception as e:
        abort(status=400, text=str(e))


@app.route("/circuits/<circuit_id>/get_edge_info", methods=["GET"])
# GET method must not have body but extracts information from the URL
def get_edge_info(circuit_id):
    try:
        print("trying get_edge_info server side")
        circuit = db.Circuit.objects(id=circuit_id).first()
        if not circuit:
            return jsonify(error="Circuit not found"), 404
        # GET method needs "request/args/get()" rather than "request/json/get()" used in PATCH
        source = request.args.get("source")
        target = request.args.get("target")
        print("got source and target")
        print("source: " + str(source))
        print("target: " + str(target))

        if not source or not target:
            print("source or target not provided")
            return jsonify(error="Source and target nodes must be provided"), 400

        fields = request.args.get("fields", type=lambda s: s and s.split(",") or None)

        print("fields: " + str(fields))
        print(circuit.to_dict(fields))

        # for edge in circuit.sfg.elements.edges:
        #     print("iterating edge", circuit.sfg.elements.edges[edge])
        # print("-----first edge", circuit.to_dict(fields))

        # print("before edge = next(..........)")
        # edge = "test"
        # Find the edge with the matching source and target
        # for e in circuit.sfg.elements['edges']:
        #     if e['data']['source'] == source and e['data']['target'] == target:
        #         edge = e
        #         break

        # print("edge:", edge)
        # edge = next(
        #     (edge for edge in circuit.sfg['elements']['edges']
        #      if edge['data']['source'] == source and edge['data']['target'] == target), None
        # )
        # edge = next((edge for edge in circuit.sfg['elements']['edges'] if edge['data']['source'] == source and edge['data']['target'] == target), None)
        # print("edge: " + str(edge))

        # if not edge:
        #     print("edge not found")
        #     return jsonify(error="Edge not found"), 404

        # weight = edge['data']['weight']
        # print("weight: " + str(weight))

        # Finally specify the application/JSON format for the response to prevent 400 Error Bad Request
        # response = jsonify(weight)

        circuit_data = circuit.to_dict(fields)

        # Extracting the list of edges
        edges = circuit_data["sfg"]["elements"]["edges"]

        # Iterate over the edges to extract the desired information
        for edge in edges:
            weight = edge["data"]["weight"]
            symbolic = weight["symbolic"]
            magnitude = weight["magnitude"]
            phase = weight["phase"]

            print(f"Edge from {edge['data']['source']} to {edge['data']['target']}:")
            print(f"  Symbolic: {symbolic}")
            print(f"  Magnitude: {magnitude}")
            print(f"  Phase: {phase}")

        # Find the edge with the matching source and target
        selected_edge = None
        for e in edges:
            if e["data"]["source"] == source and e["data"]["target"] == target:
                selected_edge = e
                print("selected_edge: " + str(selected_edge))
                break

        if not selected_edge:
            print("edge not found")
            return jsonify(error="Edge not found"), 404

        response = jsonify(selected_edge)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    except Exception as e:
        return jsonify(error=str(e)), 400


# @app.route('/circuits/<circuit_id>/get_edge_info', methods=['GET'])
def qget_edge_info(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()
    if not circuit:
        abort(404, description="Circuit not found")

    # try:
    #     source = request.args.get('source')
    #     target = request.args.get('target')
    #     edge = circuit.get_edge(source, target)

    #     print("edge: " + str(edge))
    #     print("edge.to_dict(): " + str(edge.to_dict()))
    #     return edge.to_dict()

    # except Exception as e:
    #     abort(400, description=str(e))

    source = request.args.get("source")
    target = request.args.get("target")

    if not source or not target:
        abort(400, description="Source and target nodes must be provided")

    # try:
    #     # edge = next((edge for edge in circuit.sfg['elements']['edges'] if edge['data']['source'] == source and edge['data']['target'] == target), None)

    #     # if not edge:
    #     #     abort(404, description='Edge not found')

    #     # weight = edge['data']['weight']
    #     # return jsonify(weight)

    #     fields = request.args.get(
    #         'fields',
    #         type=lambda s: s and s.split(',') or None
    #     )
    #     # print fields
    #     print("fields: " + str(fields))
    #     print(circuit.to_dict(fields))
    #     # return circuit.to_dict(fields)

    try:
        edge = next(
            (
                edge
                for edge in circuit.sfg["elements"]["edges"]
                if edge["data"]["source"] == source and edge["data"]["target"] == target
            ),
            None,
        )

        if not edge:
            abort(404, description="Edge not found")

        weight = edge["data"]["weight"]
        response = jsonify(weight)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    except Exception as e:
        abort(400, description=str(e))

    # circuit.save()
    # response = jsonify({circuit.to_dict(fields)})
    # response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    # response.headers['Pragma'] = 'no-cache'
    # response.headers['Expires'] = '0'
    # print ("response: " + str(response))
    # return response


@app.route("/circuits/<circuit_id>/transfer_function", methods=["GET"])
def get_transfer_function(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description="Circuit not found")

    input_node = request.args.get("input_node")
    output_node = request.args.get("output_node")
    latex = request.args.get("latex", default=True, type=lambda s: bool(strtobool(s)))
    factor = request.args.get("factor", default=True, type=lambda s: bool(strtobool(s)))
    numerical = request.args.get(
        "numerical", default=False, type=lambda s: bool(strtobool(s))
    )

    try:
        transfer_function = circuit.compute_transfer_function(
            input_node,
            output_node,
            latex=latex,
            factor=factor,
            numerical=numerical,
            cache_result=False,
        )

    except Exception as e:
        abort(400, description=str(e))

    circuit.save()

    # Return the loop gain as a JSON response with appropriate Cache-Control header
    response = jsonify({"transfer_function": transfer_function})

    # Disable caching for the response
    response.headers["Cache-Control"] = (
        "no-cache, no-store, must-revalidate"  # HTTP 1.1
    )
    response.headers["Pragma"] = "no-cache"  # HTTP 1.0
    response.headers["Expires"] = "0"  # Proxies

    # print out the response
    print("response: " + str(response))
    # print("response get_data: " + response.get_data())
    # # print out the response with headers
    # print("response.headers: " + response.headers)

    return response

    # return {'transfer_function': transfer_function}


@app.route("/circuits/<circuit_id>/transfer_function/bode", methods=["GET"])
def get_transfer_function_bode(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description="Circuit not found")

    input_node = request.args.get("input_node")
    output_node = request.args.get("output_node")
    start_freq = request.args.get("start_freq_hz", type=float)
    end_freq = request.args.get("end_freq_hz", type=float)
    points_per_decade = request.args.get("points_per_decade", type=int)
    frequency_unit = request.args.get("frequency_unit", default="hz")
    gain_unit = request.args.get("gain_unit", default="db")
    phase_unit = request.args.get("phase_unit", default="deg")

    try:
        freq, gain, phase = circuit.eval_transfer_function(
            input_node,
            output_node,
            start_freq,
            end_freq,
            points_per_decade,
            frequency_unit,
            gain_unit,
            phase_unit,
            cache_result=False,
        )

    except Exception as e:
        abort(400, description=str(e))

    circuit.save()

    # print response
    print("freq: " + str(freq))
    print("gain: " + str(gain))
    print("phase: " + str(phase))

    response = jsonify({"frequency": freq, "gain": gain, "phase": phase})

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    print("response: " + str(response))

    return response


@app.route("/circuits/<circuit_id>/loop_gain", methods=["GET"])
def get_loop_gain(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description="Circuit not found")

    latex = request.args.get("latex", default=True, type=lambda s: bool(strtobool(s)))
    factor = request.args.get("factor", default=True, type=lambda s: bool(strtobool(s)))
    numerical = request.args.get(
        "numerical", default=False, type=lambda s: bool(strtobool(s))
    )

    try:
        loop_gain = circuit.compute_loop_gain(
            latex=latex, factor=factor, numerical=numerical, cache_result=False
        )

    except Exception as e:
        abort(400, description=str(e))

    circuit.save()

    # # Return the loop gain as a JSON response
    # return jsonify({'loop_gain': loop_gain})
    # # return {'loop_gain': loop_gain}

    # Return the loop gain as a JSON response with appropriate Cache-Control header
    response = jsonify({"loop_gain": loop_gain})
    # response.headers['Cache-Control'] = 'no-store'  # Prevent caching

    # Disable caching for the response
    response.headers["Cache-Control"] = (
        "no-cache, no-store, must-revalidate"  # HTTP 1.1
    )
    response.headers["Pragma"] = "no-cache"  # HTTP 1.0
    response.headers["Expires"] = "0"  # Proxies

    # print out the response
    print("response: " + str(response))
    # print("response get_data: " + response.get_data())
    # # print out the response with headers
    # print("response.headers: " + response.headers)

    return response


@app.route("/circuits/<circuit_id>/loop_gain/bode", methods=["GET"])
def get_loop_gain_bode(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description="Circuit not found")

    start_freq = request.args.get("start_freq_hz", type=float)
    end_freq = request.args.get("end_freq_hz", type=float)
    points_per_decade = request.args.get("points_per_decade", type=int)
    frequency_unit = request.args.get("frequency_unit", default="hz")
    gain_unit = request.args.get("gain_unit", default="db")
    phase_unit = request.args.get("phase_unit", default="deg")

    try:
        freq, gain, phase = circuit.eval_loop_gain(
            start_freq,
            end_freq,
            points_per_decade,
            frequency_unit,
            gain_unit,
            phase_unit,
            cache_result=False,
        )

    except Exception as e:
        abort(400, description=str(e))

    circuit.save()

    # print response
    print("freq: " + str(freq))
    print("gain: " + str(gain))
    print("phase: " + str(phase))

    response = jsonify({"frequency": freq, "gain": gain, "phase": phase})

    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"

    print("response: " + str(response))

    return response


# CHECK HERE FOR SIMPLIFICATION OF THE CIRCUIT
@app.route("/circuits/<circuit_id>/simplify", methods=["PATCH"])
def simplify_circuit(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description="Circuit not found")

    source = request.json.get("source")
    target = request.json.get("target")

    try:
        circuit.simplify_sfg(source, target)
        circuit.save()

        fields = request.args.get("fields", type=lambda s: s and s.split(",") or None)

        # print fields
        print("fields: " + str(fields))
        print(circuit.to_dict(fields))

        return circuit.to_dict(fields)

    except Exception as e:
        abort(status=400, text=str(e))


# Simplifying the entire graph
@app.route("/circuits/<circuit_id>/simplification", methods=["PATCH"])
def simplification_automation_sfg(circuit_id):
    print("INSIDE SIMPLIFICAION FUNCTION...")

    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description="Circuit not found")

    circuit.simplify_entire_sfg()
    circuit.save()

    try:
        fields = request.args.get("fields", type=lambda s: s and s.split(",") or None)

        return circuit.to_dict(fields)

    except Exception as e:
        abort(400, description=str(e))


def find_source_and_target(graph):
    """
    Manually determine the source and target nodes of the graph.
    - Source: Node with no incoming edges.
    - Target: Node with no outgoing edges.
    """
    source = None
    target = None
    print("here")

    # Iterate through each node in the graph
    for node in graph.nodes:
        in_degree = graph.in_degree(node)
        out_degree = graph.out_degree(node)

        # Identify the source (no incoming edges)
        if in_degree == 0:
            if source is not None:
                raise ValueError("Graph has multiple source nodes.")
            source = node

        # Identify the target (no outgoing edges)
        if out_degree == 0:
            if target is not None:
                raise ValueError("Graph has multiple target nodes.")
            target = node

    if source is None or target is None:
        raise ValueError("Unable to find a valid source and target in the graph.")

    return source, target


@app.route("/circuits/<circuit_id>/simplificationgraph", methods=["PATCH"])
def simplification_automation_sfg_entire(circuit_id):
    """
    Endpoint to simplify the entire signal-flow graph (SFG) for a given circuit.
    """
    print("INSIDE SIMPLIFICATION FUNCTION TRIVIAL...")
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description="Circuit not found")

    circuit.simplify_whole_graph_trivial()
    circuit.save()

    try:
        fields = request.args.get("fields", type=lambda s: s and s.split(",") or None)

        return circuit.to_dict(fields)

    except Exception as e:
        abort(400, description=str(e))


@app.route("/circuits/<circuit_id>/undo", methods=["PATCH"])
def undo_sfg(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description="Circuit not found")

    circuit.undo_sfg()
    circuit.save()

    try:
        fields = request.args.get("fields", type=lambda s: s and s.split(",") or None)

        return circuit.to_dict(fields)

    except Exception as e:
        abort(400, description=str(e))


@app.route("/circuits/<circuit_id>/redo", methods=["PATCH"])
def redo_sfg(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description="Circuit not found")

    circuit.redo_sfg()
    circuit.save()

    try:
        fields = request.args.get("fields", type=lambda s: s and s.split(",") or None)

        return circuit.to_dict(fields)

    except Exception as e:
        abort(400, description=str(e))


# For SFG Export
@app.route("/circuits/<circuit_id>/export", methods=["GET"])
def get_sfg(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()
    if not circuit:
        abort(404, description="Circuit not found")

    with tempfile.NamedTemporaryFile() as temp:
        dill.dump(circuit, temp)

    tmp_file = tempfile.NamedTemporaryFile(delete=True)
    tmp_file.flush()
    dill.dump(circuit, tmp_file)
    tmp_file.seek(0)

    try:
        return send_file(tmp_file, mimetype="pkl")
    except Exception as e:
        abort(400, description=str(e))


# TODO import needs implementation
@app.route("/circuits/<circuit_id>/import", methods=["POST"])
def import_dill_sfg(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        loaded_sfg = dill.load(request.files["file"])
        circuit = db.Circuit.create(
            circuitId=circuit_id,
            name=loaded_sfg.name,
            netlist=loaded_sfg.netlist,
            schematic=loaded_sfg.schematic,
            op_point_log=loaded_sfg.op_point_log,
        )
        circuit.import_circuit(loaded_sfg)
        circuit.id = circuit_id
        circuit.save()
        fields = request.args.get("fields", type=lambda s: s and s.split(",") or None)
        return circuit.to_dict(fields)

    try:
        loaded_sfg = dill.load(request.files["file"])
        circuit.import_circuit(loaded_sfg)
        circuit.save()
        fields = request.args.get("fields", type=lambda s: s and s.split(",") or None)

        return circuit.to_dict(fields)

    except Exception as e:
        abort(400, description=str(e))

@app.route('/circuits/<circuit_id>/pm/plot', methods=['GET'])
def plot_phase_margin(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description='Circuit not found')

    #if  min_cap <= 0 or max_cap <= 0 or step_size <= 0 or not selected_cap:
    #    return jsonify({"error": "Invalid input parameters"}), 400
    
    # Step 1: Parse query parameters
    input_node = request.args.get('input_node', type=str)
    output_node = request.args.get('output_node', type=str)
    start_freq = request.args.get('start_freq', type=float)
    end_freq = request.args.get('end_freq', type=float)
    selected_device = request.args.get('selected_device', type=str)
    min_val = float(request.args.get('min_val', type=float))
    max_val = float(request.args.get('max_val', type=float))
    step_size = float(request.args.get('step_size', type=float))
    test_resistor = request.args.get('test_resistor', type=str)
    test_resistance = request.args.get('test_resistance', type=float)

    try:
        device_value, phase_margin = circuit.sweep_params_for_phase_margin(
            input_node=input_node,
            output_node=output_node,
            start_freq=start_freq,
            end_freq=end_freq,
            param_name=selected_device,
            min_value=min_val,
            max_value=max_val,
            step=step_size,
            test_resistor=test_resistor,
            test_resistance=test_resistance
        )

    except Exception as e:
        abort(400, description=str(e))

    circuit.save()
    
    # print response
    print("device value: " + str(device_value))
    print("phase margin: " + str(phase_margin))

    response = jsonify({'device_value': device_value, 'phase_margin': phase_margin})

    return response

@app.route('/circuits/<circuit_id>/bandwidth/plot', methods=['GET'])
def plot_bandwidth(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description='Circuit not found')

    #if  min_cap <= 0 or max_cap <= 0 or step_size <= 0 or not selected_cap:
    #    return jsonify({"error": "Invalid input parameters"}), 400
    
    # Step 1: Parse query parameters
    input_node = request.args.get('input_node', type=str)
    output_node = request.args.get('output_node', type=str)
    start_freq = request.args.get('start_freq', type=float)
    end_freq = request.args.get('end_freq', type=float)
    selected_device = request.args.get('selected_device', type=str)
    min_val = float(request.args.get('min_val', type=float))
    max_val = float(request.args.get('max_val', type=float))
    step_size = float(request.args.get('step_size', type=float))
    test_resistor = request.args.get('test_resistor', type=str)
    test_resistance = request.args.get('test_resistance', type=float)

    try:
        parameter_value, bandwidth = circuit.sweep_params_for_bandwidth(
            input_node=input_node,
            output_node=output_node,
            start_freq=start_freq,
            end_freq=end_freq,
            param_name=selected_device,
            min_val=min_val,
            max_val=max_val,
            step=step_size,
            test_resistor=test_resistor,
            test_resistance=test_resistance
        )

    except Exception as e:
        abort(400, description=str(e))

    circuit.save()
    
    # print response
    print("parameter value: " + str(parameter_value))
    print("bandwidth: " + str(bandwidth))

    response = jsonify({'parameter_value': parameter_value, 'bandwidth': bandwidth})

    return response

@app.route('/circuits/<circuit_id>/devices/check', methods=['GET'])
def check_device(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description='Circuit not found')

   # Get the device name from query parameters
    device_name = request.args.get('device_name')
    if not device_name:
        return jsonify({"error": "Device name is required"}), 400

    try:
        # Use the is_device_valid function to check if the device exists
        device_exists = circuit.is_device_valid(device_name)

        # Return appropriate JSON response
        return jsonify({"exists": device_exists})
    except Exception as e:
        # Handle unexpected errors gracefully
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)
