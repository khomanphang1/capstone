from mongoengine import *


connect('capstone')


class TransferFunction(EmbeddedDocument):
    input = StringField()
    output = StringField()
    symbolic = BinaryField()
    numeric = BinaryField()

    meta = {
        'indexes': [
            {
                'fields': ('input', 'output'),
                'unique': True
            }
        ]
    }


class Circuit(Document):
    name = StringField()
    svg = StringField()
    schematic = StringField()
    netlist = StringField()
    op_point_log = StringField()
    parameters = DictField()
    sfg = BinaryField()
    transfer_functions = EmbeddedDocumentListField(TransferFunction)




if __name__ == '__main__':
    connect('capstone')

    import dill
    import sympy as sp
    import networkx as nx

    import mason
    from mock_data import graph

    circuit = Circuit(
        name='2n3904_common_emitter',
        svg='<svg viewBox="0 0 300 100" xmlns="http://www.w3.org/2000/svg" stroke="red" fill="grey"></svg>',
        schematic='...',
        netlist='...',
        op_point_log='...',
        parameters = {
            'R_D': 1,
            'g_m': 2,
            'r_o': 3,
            'R_S': 4,
            'C_D': 5,
            'w': 100e3
        },
        sfg=dill.dumps(graph)
    )

    tf = mason.transfer_function(graph, 'v_i', 'v_o')
    tf_ = tf.subs({k: v for k, v in circuit.parameters.items() if k != 'w'})
    numeric_tf = sp.lambdify('w', tf_, 'numpy')

    circuit.transfer_functions.append(
        TransferFunction(
            input='v_gs',
            output='v_x',
            symbolic=dill.dumps(tf),
            numeric=dill.dumps(numeric_tf, recurse=True)
        )
    )

    circuit.save()

    print('Inserted one circuit.')