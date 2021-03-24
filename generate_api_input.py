import json
import os

circuit_names = ('2N3904_common_emitter', '2N3904_cascode',
                  'ideal_common_source', 'transresistance')

root = 'test_data'

for name in circuit_names:

    files = {
        'schematic': os.path.join(root, f'{name}.asc'),
        'netlist': os.path.join(root, f'{name}.cir'),
        'op_point_log': os.path.join(root, f'{name}.log')
    }

    json_file = os.path.join(root, 'json', f'{name}.json')

    for key in files:
        try:
            with open(files[key], 'r') as f:
                files[key] = f.read()
        except FileNotFoundError:
            files[key] = None

    args = {k: v for k, v in files.items() if v}
    args['name'] = name

    with open(json_file, 'w') as f:
        f.write(json.dumps(args))


