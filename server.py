from cgitb import text
from flask import Flask, request, abort, send_from_directory, Response, jsonify
from flask_cors import CORS
from distutils.util import strtobool

import db


app = Flask(__name__)
# app.config['DEBUG'] = False
CORS(app)


@app.route('/app/<path:path>')
def serve_webpage(path):
    return send_from_directory('public', path)


@app.route('/circuits/<circuit_id>', methods=['GET'])
def get_circuit(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description='Circuit not found')

    try:
        fields = request.args.get(
            'fields',
            type=lambda s: s and s.split(',') or None
        )

        return circuit.to_dict(fields)

    except Exception as e:
        abort(400, description=str(e))


@app.route('/circuits', methods=['POST'])
def create_circuit():
    name = request.json['name']
    netlist = request.json['netlist']

    schematic = request.json.get('schematic')
    op_point_log = request.json.get('op_point_log')

    try:
        circuit = db.Circuit.create(name, netlist, schematic, op_point_log)
    except Exception as e:
        abort(400, str(e))

    try:
        fields = request.args.get(
            'fields',
            type=lambda s: s and s.split(',') or None
        )

        return circuit.to_dict(fields)

    except Exception as e:
        abort(400, description=str(e))


@app.route('/circuits/<circuit_id>', methods=['PATCH'])
def patch_circuit(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()
    if not circuit:
        abort(404, description='Circuit not found')

    circuit.update_parameters(request.json)
    circuit.save()

    try:
        fields = request.args.get(
            'fields',
            type=lambda s: s and s.split(',') or None
        )

        return circuit.to_dict(fields)

    except Exception as e:
        abort(400, description=str(e))


@app.route('/circuits/<circuit_id>/transfer_function', methods=['GET'])
def get_transfer_function(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description='Circuit not found')

    input_node = request.args.get('input_node')
    output_node = request.args.get('output_node')
    latex = request.args.get('latex', default=True,
                             type=lambda s: bool(strtobool(s)))
    factor = request.args.get('factor', default=True,
                              type=lambda s: bool(strtobool(s)))
    numerical = request.args.get('numerical', default=False,
                                 type=lambda s: bool(strtobool(s)))

    try:
        transfer_function = circuit.compute_transfer_function(
            input_node,
            output_node,
            latex=latex,
            factor=factor,
            numerical=numerical,
            cache_result=False
        )

    except Exception as e:
        abort(400, description=str(e))

    circuit.save()

     # Return the loop gain as a JSON response with appropriate Cache-Control header
    response = jsonify({'transfer_function': transfer_function})

    # Disable caching for the response
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'  # HTTP 1.1
    response.headers['Pragma'] = 'no-cache'  # HTTP 1.0
    response.headers['Expires'] = '0'  # Proxies

    # print out the response
    print("response: " + str(response))
    # print("response get_data: " + response.get_data())
    # # print out the response with headers
    # print("response.headers: " + response.headers)

    return response

    # return {'transfer_function': transfer_function}


@app.route('/circuits/<circuit_id>/transfer_function/bode', methods=['GET'])
def get_transfer_function_bode(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description='Circuit not found')

    input_node = request.args.get('input_node')
    output_node = request.args.get('output_node')
    start_freq = request.args.get('start_freq_hz', type=float)
    end_freq = request.args.get('end_freq_hz', type=float)
    points_per_decade = request.args.get('points_per_decade', type=int)
    frequency_unit = request.args.get('frequency_unit', default='hz')
    gain_unit = request.args.get('gain_unit', default='db')
    phase_unit = request.args.get('phase_unit', default='deg')

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
            cache_result=True
        )

    except Exception as e:
        abort(400, description=str(e))

    circuit.save()

    return {
        'frequency': freq,
        'gain': gain,
        'phase': phase
    }


@app.route('/circuits/<circuit_id>/loop_gain', methods=['GET'])
def get_loop_gain(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description='Circuit not found')

    latex = request.args.get('latex', default=True,
                             type=lambda s: bool(strtobool(s)))
    factor = request.args.get('factor', default=True,
                              type=lambda s: bool(strtobool(s)))
    numerical = request.args.get('numerical', default=False,
                                 type=lambda s: bool(strtobool(s)))

    try:
        loop_gain = circuit.compute_loop_gain(
            latex=latex,
            factor=factor,
            numerical=numerical,
            cache_result=False
        )

    except Exception as e:
        abort(400, description=str(e))

    circuit.save()

    # # Return the loop gain as a JSON response
    # return jsonify({'loop_gain': loop_gain})
    # # return {'loop_gain': loop_gain}

    # Return the loop gain as a JSON response with appropriate Cache-Control header
    response = jsonify({'loop_gain': loop_gain})
    # response.headers['Cache-Control'] = 'no-store'  # Prevent caching

    # Disable caching for the response
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'  # HTTP 1.1
    response.headers['Pragma'] = 'no-cache'  # HTTP 1.0
    response.headers['Expires'] = '0'  # Proxies

    # print out the response
    print("response: " + str(response))
    # print("response get_data: " + response.get_data())
    # # print out the response with headers
    # print("response.headers: " + response.headers)

    return response


@app.route('/circuits/<circuit_id>/loop_gain/bode', methods=['GET'])
def get_loop_gain_bode(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description='Circuit not found')

    start_freq = request.args.get('start_freq_hz', type=float)
    end_freq = request.args.get('end_freq_hz', type=float)
    points_per_decade = request.args.get('points_per_decade', type=int)
    frequency_unit = request.args.get('frequency_unit', default='hz')
    gain_unit = request.args.get('gain_unit', default='db')
    phase_unit = request.args.get('phase_unit', default='deg')

    try:
        freq, gain, phase = circuit.eval_loop_gain(
            start_freq,
            end_freq,
            points_per_decade,
            frequency_unit,
            gain_unit,
            phase_unit,
            cache_result=True
        )

    except Exception as e:
        abort(400, description=str(e))

    circuit.save()

    return {
        'frequency': freq,
        'gain': gain,
        'phase': phase
    }

@app.route('/circuits/<circuit_id>/simplify', methods=['PATCH'])
def simplify_circuit(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description='Circuit not found')

    source = request.json.get('source')
    target = request.json.get('target')


    try:
        circuit.simplify_sfg(source, target)
        circuit.save()

        fields = request.args.get(
            'fields',
            type=lambda s: s and s.split(',') or None
        )

        return circuit.to_dict(fields)

    except Exception as e:
        abort(status=400, text=str(e))

@app.route('/circuits/<circuit_id>/undo', methods=['PATCH'])
def undo_sfg(circuit_id):
    circuit = db.Circuit.objects(id=circuit_id).first()

    if not circuit:
        abort(404, description='Circuit not found')

    circuit.undo_sfg()
    circuit.save()

    try:
        fields = request.args.get(
            'fields',
            type=lambda s: s and s.split(',') or None
        )

        return circuit.to_dict(fields)

    except Exception as e:
        abort(400, description=str(e))


if __name__ == '__main__':
    app.run(debug=True)
