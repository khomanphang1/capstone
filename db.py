from typing import Tuple, List, Union, Optional, Dict, Callable, Iterable
import os

from mongoengine import *
from datetime import datetime
import sympy
import mason
import math
import cmath
import numpy as np
import dill
import circuit_parser
from dpi import DPI_algorithm as DPI
import ltspice2svg
import networkx as nx


if 'DB_URI' in os.environ:
    # Connect to production database
    connection_str = os.environ['DB_URI']
    connect(host=connection_str)
else:
    # Connect to local development database
    connect('capstone')


class TransferFunction(EmbeddedDocument):
    input_node = StringField()
    output_node = StringField()
    sympy_expression = BinaryField()
    lambda_function = BinaryField()

    meta = {
        'indexes': [
            {
                'fields': ('input', 'output'),
                'unique': True
            }
        ]
    }


class LoopGainFunction(EmbeddedDocument):
    sympy_expression = BinaryField()
    lambda_function = BinaryField()


class Circuit(Document):
    name = StringField()
    svg = StringField()
    schematic = StringField()
    netlist = StringField()
    op_point_log = StringField()
    parameters = DictField()
    sfg = BinaryField()
    transfer_functions = EmbeddedDocumentListField(TransferFunction)
    loop_gain = EmbeddedDocumentField(LoopGainFunction)
    created = DateTimeField(default=datetime.utcnow)
    meta = {
        'indexes': [
            {'fields': ['created'], 'expireAfterSeconds': 86400}
        ]
    }

    def to_dict(self, fields: Optional[Iterable[str]] = None) -> Dict:
        """Returns a dictionary representation of the Circuit document.

        Args:
            fields: The fields to include. If fields is None or empty,
                the following are included by default:
                (id, name, parameters, and sfg).

        Returns:
            A dictionary.
        """
        fields = set(fields or ('id', 'name', 'parameters', 'sfg'))

        output = {
            'id': str(self.id),
            'name': self.name,
            'parameters': self.parameters.copy(),
            'svg': self.svg
        }

        # Because de-serializing and serializing the SFG is costly, only
        # do so when needed.
        if 'sfg' in fields:
            sfg = dill.loads(self.sfg)
            freq = 2j * math.pi * sympy.Symbol('f')

            for src, dst in sfg.edges:
                symbolic = sfg.edges[src, dst]['weight']

                if isinstance(symbolic, sympy.Expr):
                    numeric = symbolic.subs('s', freq).subs(self.parameters)
                else:
                    numeric = symbolic

                magnitude, phase = cmath.polar(numeric)

                sfg.edges[src, dst]['weight'] = {
                    'symbolic': str(symbolic),
                    'magnitude': magnitude,
                    'phase': phase
                }

            output['sfg'] = nx.cytoscape_data(sfg)

        # Some fields are invalid.
        if not fields <= output.keys():
            raise ValueError('Invalid fields.')

        return {k: v for k, v in output.items() if k in fields}

    @classmethod
    def create(
        cls,
        name: str,
        netlist: str,
        schematic: Optional[str] = None,
        op_point_log: Optional[str] = None
    ) -> 'Circuit':
        """Creates a new circuit.

        Args:
            name: The name of the circuit.
            netlist: The .net circuit netlist.
            schematic: The .asc circuit schematic. Defaults to None. Note that
                an svg circuit drawing will not be available if the schematic
                is not given.
            op_point_log: The operating point analysis log. If not given,
                the circuit is presumed to be in small-signal form. Defaults to
                None.
        """
        # Parse the circuit and enerate its small-signal representation.
        circuit = circuit_parser.Circuit.from_ltspice_netlist(netlist,
                                                              op_point_log)

        # Map components / parameter names to their numerical values.
        parameters = circuit.parameters()

        # Perform DPI analysis.
        sfg = DPI(circuit).graph

        # Generate an svg if the schematic is given.
        svg = None if schematic is None else ltspice2svg.asc_to_svg(schematic)

        # Note that loop gain and transfer functions are computed lazily. As
        # such, they are not constructed until they are accessed.

        # Initialize the underlying document.
        circuit = Circuit(
            name=name,
            netlist=netlist,
            schematic=schematic,
            svg=svg,
            op_point_log=op_point_log,
            parameters=parameters,
            sfg=dill.dumps(sfg)
        )

        circuit.save()

        return circuit

    def update_parameters(self, update_dict: Dict):
        """Update the circuit parameters.

        Args:
            update_dict: A dictionary containing the names and values to
                update.
        """
        if not update_dict.keys() <= self.parameters.keys():
            raise ValueError('Invalid parameters.')

        self.parameters.update(update_dict)

        self.transfer_functions.delete()
        self.loop_gain = None

    def _compute_transfer_function(
        self,
        input_node: str,
        output_node: str,
        cache_result: bool
    ) -> Tuple[sympy.Expr, Callable]:

        # Finds the transfer function sub-document by (input_node, output_node).
        transfer_function = self.transfer_functions. \
            filter(input_node=input_node, output_node=output_node).first()

        if transfer_function:
            # The transfer function was previously computed and cached.

            # De-serialize
            sympy_expression = dill.loads(transfer_function.sympy_expression)
            lambda_function = dill.loads(transfer_function.lambda_function)
            return sympy_expression, lambda_function

        # De-serialize the signal-flow graph.
        sfg = dill.loads(self.sfg)

        # Compute the transfer function.
        sympy_expression, _ = mason.transfer_function(
            sfg, input_node, output_node
        )

        # Substitute all terms for their numerical values except the frequency.
        lambda_function = sympy_expression.subs(
            {k: v for k, v in self.parameters.items() if k != 'f'}
        )

        # Compile symbolic expression into lambda function for numerical
        # computations.
        lambda_function = sympy.lambdify('s', lambda_function, 'numpy')

        if cache_result:
            # Cache the newly computed sympy expression and lambda function for
            # re-use.
            self.transfer_functions.append(
                TransferFunction(
                    input_node=input_node,
                    output_node=output_node,
                    # Serialize expression and function objects.
                    sympy_expression=dill.dumps(sympy_expression),
                    lambda_function=dill.dumps(lambda_function, recurse=True)
                )
            )

        return sympy_expression, lambda_function

    def compute_transfer_function(
        self,
        input_node: str,
        output_node: str,
        latex: bool = True,
        factor: bool = True,
        numerical: bool = False,
        cache_result: bool = False
    ) -> str:
        """Computes the transfer function between a pair of input and output nodes.

        Args:
            input_node: The name of the input node.
            output_node: The name of the output node.
            latex: If True, formats the transfer function in latex. Defaults to
                True.
            factor: If True, factors the expression. Defaults to True.
            numerical: If True, substitutes all symbols for numerical values,
                except 's'. Defaults to False.
            cache_result: If True, caches the computed transfer function;
                save() should be called to propagate changes to the cache.

        Returns:
            The transfer function.
        """
        sympy_expression, _ = self._compute_transfer_function(
            input_node,
            output_node,
            cache_result=cache_result
        )

        if numerical:
            sympy_expression = sympy_expression.subs(
                {k: v for k, v in self.parameters.items() if k != 'f'}
            )

        if factor:
            sympy_expression = sympy_expression.factor()

        return sympy.latex(sympy_expression) if latex \
            else str(sympy_expression)

    def eval_transfer_function(
        self,
        input_node: str,
        output_node: str,
        start_freq: float,
        end_freq: float,
        points_per_decade: int,
        frequency_unit: str = 'hz',
        gain_unit: Union[str, None] = 'db',
        phase_unit: str = 'deg',
        cache_result: bool = False
    ) -> Tuple[List[float], List[float], List[float]]:
        """Given a frequency range, evaluates the gain and phase of the
            transfer function over that range.

        Args:
            input_node: The name of the input node.
            output_node: The name of the output node.
            start_freq: The starting frequency.
            end_freq: The ending frequency.
            points_per_decade: The number of points to plot per decade.
            frequency_unit: The unit for the input frequency range. Can be 'hz'
                or 'rad/s'.
            gain_unit: The unit for the gain output. Can be None or
                '' for dimensionless, or 'db' for decibels.
            phase_unit: The unit for the phase output. Can be 'deg' for degrees,
                or 'rad' for radians.
            cache_result: If True, caches the computed transfer function;
                save() should be called to propagate changes to the cache.

        Returns:
            A (frequency_list, gain_list, phase_list) tuple.
        """
        _, lambda_function = self._compute_transfer_function(
            input_node,
            output_node,
            cache_result=cache_result
        )

        num_decades = math.log10(end_freq / start_freq)
        num_points = round(points_per_decade * num_decades)
        # Note that transfer function is expressed in terms of s.
        freq = np.logspace(math.log10(start_freq),
                           math.log10(end_freq),
                           num_points)

        if frequency_unit == 'hz':
            # Must scale by 2 * pi to get s.
            s = 1j * 2 * np.pi * freq
        elif frequency_unit == 'rad/s':
            s = 1j * freq
            pass
        else:
            raise ValueError('Invalid frequency unit.')

        output = lambda_function(s)

        # If the output is not the same length as the frequency array, then
        # it does not depend on the input, in which case we must pad it.
        if not isinstance(output, np.ndarray):
            output = np.repeat(output, len(freq))

        # Get the magnitude of complex output,
        # and convert to the correct units.
        if gain_unit in (None, ''):
            gain = np.abs(output)
        elif gain_unit == 'db':
            gain = 20 * np.log10(np.abs(output))
        else:
            raise ValueError('Invalid gain unit.')

        # Get the phase of complex output,
        # and convert to correct units.
        if phase_unit == 'rad':
            phase = np.angle(output, deg=False)
        elif phase_unit == 'deg':
            phase = np.angle(output, deg=True)
        else:
            raise ValueError('Invalid phase unit.')

        # Convert numpy arrays to plain python lists.
        return freq.tolist(), gain.tolist(), phase.tolist()

    def _compute_loop_gain(self, cache_result: bool) \
            -> Tuple[sympy.Expr, Callable]:

        if self.loop_gain:
            sympy_expression = dill.loads(self.loop_gain.sympy_expression)
            lambda_function = dill.loads(self.loop_gain.lambda_function)
            return sympy_expression, lambda_function

        # De-serialize the signal-flow graph.
        sfg = dill.loads(self.sfg)

        # Compute the loop gain function.
        sympy_expression = mason.loop_gain(sfg)

        # Substitute all terms for their numerical values except the frequency.
        lambda_function = sympy_expression.subs(
            {k: v for k, v in self.parameters.items() if k != 'f'}
        )

        # Compile symbolic expression into lambda function for numerical
        # computations.
        lambda_function = sympy.lambdify('s', lambda_function, 'numpy')

        if cache_result:
            self.loop_gain = LoopGainFunction(
                sympy_expression=dill.dumps(sympy_expression),
                lambda_function=dill.dumps(lambda_function, recurse=True)
            )

        return sympy_expression, lambda_function

    def compute_loop_gain(
        self,
        latex: bool = False,
        factor: bool = True,
        numerical: bool = False,
        cache_result: bool = False
    ):
        """Computes the loop gain function of a circuit.

        Args:
            latex: If True, formats the function in latex.
            factor: If True, factors the expression. Defaults to True.
            numerical: If True, substitutes all symbols for numerical values,
                except 's'. Defaults to False.
            cache_result: If True, caches the computed loop gain function;
                save() should be called to propagate changes to the cache.

        Returns:
            The loop gain function.
        """
        sympy_expression, _ = self._compute_loop_gain(cache_result=cache_result)

        if numerical:
            sympy_expression = sympy_expression.subs(
                {k: v for k, v in self.parameters.items() if k != 'f'}
            )

        if factor:
            sympy_expression = sympy_expression.factor()

        return sympy.latex(sympy_expression) if latex else str(sympy_expression)

    def eval_loop_gain(
            self,
            start_freq: float,
            end_freq: float,
            points_per_decade: int,
            frequency_unit: str = 'hz',
            gain_unit: Union[str, None] = 'db',
            phase_unit: str = 'deg',
            cache_result: bool = False
    ) -> Tuple[List[float], List[float], List[float]]:
        """Given a frequency range, evaluates the gain and phase of the
            loop gain function over that range.

        Args:
            start_freq: The starting frequency.
            end_freq: The ending frequency.
            points_per_decade: The number of points to plot per decade.
            frequency_unit: The unit for the input frequency range. Can be 'hz'
                or 'rad/s'.
            gain_unit: The unit for the gain output. Can be None or
                '' for dimensionless, or 'db' for decibels.
            phase_unit: The unit for the phase output. Can be 'deg' for degrees,
                or 'rad' for radians.
            cache_result: If True, caches the computed loop gain function;
                save() should be called to propagate changes to the cache.

        Returns:
            A (frequency_list, gain_list, phase_list) tuple.
        """
        _, lambda_function = self._compute_loop_gain(cache_result=cache_result)

        num_decades = math.log10(end_freq / start_freq)
        num_points = round(points_per_decade * num_decades)
        # Note that transfer function is expressed in terms of s.
        freq = np.logspace(math.log10(start_freq),
                           math.log10(end_freq),
                           num_points)

        if frequency_unit == 'hz':
            # Must scale by 2 * pi to get s.
            s = 1j * 2 * np.pi * freq
        elif frequency_unit == 'rad/s':
            s = 1j * freq
            pass
        else:
            raise ValueError('Invalid frequency unit.')

        output = lambda_function(s)

        # If the output is not the same length as the frequency array, then
        # it does not depend on the input, in which case we must pad it.
        if not isinstance(output, np.ndarray):
            output = np.repeat(output, len(freq))

        # Get the magnitude of complex output,
        # and convert to the correct units.
        if gain_unit in (None, ''):
            gain = np.abs(output)
        elif gain_unit == 'db':
            gain = 20 * np.log10(np.abs(output))
        else:
            raise ValueError('Invalid gain unit.')

        # Get the phase of complex output,
        # and convert to correct units.
        if phase_unit == 'rad':
            phase = np.angle(output, deg=False)
        elif phase_unit == 'deg':
            phase = np.angle(output, deg=True)
        else:
            raise ValueError('Invalid phase unit.')

        # Convert numpy arrays to plain python lists.
        return freq.tolist(), gain.tolist(), phase.tolist()
