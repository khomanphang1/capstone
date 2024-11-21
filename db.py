from typing import Tuple, List, Union, Optional, Dict, Callable, Iterable
import os

from mongoengine import *
from datetime import datetime
import sympy
from sympy.parsing.latex import parse_latex
import mason
import math
import cmath
import numpy as np
import dill
import circuit_parser
from dpi import DPI_algorithm as DPI
from dpi import simplify
from dpi import removing_branch
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
    sfg_stack = []
    redo_stack = []

    def to_dict(self, fields: Optional[Iterable[str]] = None) -> Dict:
        """Returns a dictionary representation of the Circuit document.

        Args:
            fields: The fields to include. If fields is None or empty,
                the following are included by default:
                (id, name, parameters, and sfg).

        Returns:
            A dictionary.
        """
        print("to_dict called in db.py")
        
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
                # print the edge and its weights
                print("src:", src)
                print("dst:", dst)
                print("edge:", sfg.edges[src, dst])
                print("edge weight:", sfg.edges[src, dst]['weight'])
                symbolic = sfg.edges[src, dst]['weight']

                if isinstance(symbolic, sympy.Expr):
                    numeric = symbolic.subs('s', freq).subs(self.parameters)
                else:
                    numeric = symbolic

                magnitude, phase = cmath.polar(numeric)

                sfg.edges[src, dst]['weight'] = {
                    'symbolic': sympy.latex(symbolic) if isinstance(symbolic, sympy.Expr) else str(symbolic),
                    'magnitude': magnitude,
                    'phase': phase*(180/cmath.pi)
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
        op_point_log: Optional[str] = None,
        circuitId: Optional[str] = None
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
        # Parse the circuit and generate its small-signal representation.
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
        circuit = None
        if circuitId is not None:
            circuit = Circuit(
                id=circuitId,
                name=name,
                netlist=netlist,
                schematic=schematic,
                svg=svg,
                op_point_log=op_point_log,
                parameters=parameters,
                sfg=dill.dumps(sfg)
            )
        else:
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
    
    def remove_branch_sfg(self, source, target):
        """Remove a branch from the sfg.

        Args:
            source: node representing start of path
            target: node representing end of the path
        """
        #save current sfg
        self.sfg_stack.append(self.sfg)
        self.redo_stack.clear()
        if len(self.sfg_stack) > 5:
            self.sfg_stack = self.sfg_stack[-5:]

        # De-serialize sfg
        sfg = dill.loads(self.sfg)

        # check nodes exist
        if not sfg or not sfg.has_node(source) or not sfg.has_node(target):
            raise Exception('Node does not exist.') 

        sfg = removing_branch(sfg, source, target)
        if not sfg or sfg == "Path is too short":
            raise Exception('The selected branch does not exist')
        self.sfg = dill.dumps(sfg)

    def simplify_sfg(self, source, target ):
        """Simplify the sfg.

        Args:
            source: node representing start of path
            target: node representing end of the path
        """
        #save current sfg
        self.sfg_stack.append(self.sfg)
        self.redo_stack.clear()
        if len(self.sfg_stack) > 5:
            self.sfg_stack = self.sfg_stack[-5:]

        # De-serialize sfg
        sfg = dill.loads(self.sfg)

        # check nodes exist
        if not sfg or not sfg.has_node(source) or not sfg.has_node(target):
            raise Exception('Node does not exist.') 
            
        sfg = simplify(sfg, source, target)
        if not sfg or sfg == "Path is too short":
            raise Exception('The selected path is too short') 

        self.sfg = dill.dumps(sfg)

    def undo_sfg(self):
        if len(self.sfg_stack) > 0:
            self.redo_stack.append(self.sfg)
            self.sfg = self.sfg_stack.pop()

    def redo_sfg(self):
        if len(self.redo_stack) > 0:
            self.sfg_stack.append(self.sfg)
            self.sfg = self.redo_stack.pop()

    def get_current_sfg(self):
        return self.deserialize_sfg()

    def old_edit_edge(self, editSrc, editDst, editSymbolic):
        """Edit the SFG edge

        Args:
            editSrc: the source vertex of the edge
            editDst: the destination vertex of the edge
            editSymbolic: the new symbolic function of the edge.
        """
        print("edit_edge called in db.py")
        print("self:", self)
        print("editSrc:", editSrc)
        print("editDst:", editDst)
        print("editSymbolic:", editSymbolic)
        
        print("loading sfg")
        sfg = dill.loads(self.sfg)
        print("sfg loaded")
        print("sfg:", sfg)

        # print sfg info
        print("nodes:", sfg.nodes)
        print("edges:", sfg.edges)


        print("iterating through edges")
        for src, dst in sfg.edges:
            if src == editSrc and dst == editDst:
                print("found edge")
                print("edge:", sfg.edges)
                symbolic = sfg.edges[src, dst]['weight']
                print("old symbolic:", symbolic)
                print("edge data:", sfg.edges[src, dst])
                sfg.edges[src, dst]['weight'] = editSymbolic
                print("edge data after edit:", sfg.edges[src, dst])
                self.sfg = dill.dumps(sfg)
                # return sfg.edges[src, dst]['weight']
                break
        # self.sfg = dill.dumps(sfg)
        return sfg
        raise Exception('The selected edge does not exist!')
    
    def edit_edge(self, editSrc, editDst, editSymbolic):
        """Edit the SFG edge

        Args:
            editSrc: the source vertex of the edge
            editDst: the destination vertex of the edge
            editSymbolic: the new symbolic function of the edge.
        """
        print("edit_edge called in db.py")
        print("editSrc:", editSrc)
        print("editDst:", editDst)
        print("editSymbolic:", editSymbolic)
        
        try:
            # Convert the symbolic string to a SymPy expression
            print("trying to convert to SymPy expression")
            editSymbolic = sympy.sympify(editSymbolic)
            print("successfully converted to SymPy expression")
        except sympy.SympifyError:
            # print("failed to convert to SymPy expression")
            # raise ValueError(f"Invalid symbolic expression: {editSymbolic}")
            try:
                # Fallback to parsing as a LaTeX expression
                editSymbolic = parse_latex(editSymbolic)
                print("successfully parsed as LaTeX expression")
            except Exception as e:
                print("failed to parse as LaTeX expression")
                raise ValueError(f"Invalid symbolic expression: {editSymbolic}. Error: {e}")
        # Load the current state of the SFG
        try:
            print("Loading SFG...")
            sfg = dill.loads(self.sfg)
            print("SFG loaded successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to load SFG: {e}")

        # Iterate through edges and find the one to update
        edge_found = False
        print("Iterating through edges...")
        for src, dst in sfg.edges:
            if src == editSrc and dst == editDst:
                print(f"Found edge from {src} to {dst}. Updating symbolic weight.")
                # Update the symbolic weight for the found edge
                sfg.edges[src, dst]['weight'] = editSymbolic
                edge_found = True
                break

        # Handle the case where the edge wasn't found
        if not edge_found:
            raise ValueError(f"The edge from {editSrc} to {editDst} does not exist!")

        # Serialize the updated SFG back to the database field
        try:
            print("Serializing the updated SFG...")
            self.sfg = dill.dumps(sfg)
            print("SFG serialized and stored successfully.")
        except Exception as e:
            raise RuntimeError(f"Failed to serialize the updated SFG: {e}")

        # Return the updated SFG for further use or confirmation
        return sfg

                

    # SFG binary field --> graph (json object)
    def deserialize_sfg(self):
        output = {}
        sfg = dill.loads(self.sfg) # binary to obj (deserialization)
        freq = 2j * math.pi * sympy.Symbol('f')

        for src, dst in sfg.edges:
            symbolic = sfg.edges[src, dst]['weight']

            if isinstance(symbolic, sympy.Expr):
                numeric = symbolic.subs('s', freq).subs(self.parameters)
            else:
                numeric = symbolic

            magnitude, phase = cmath.polar(numeric)

            sfg.edges[src, dst]['weight'] = {
                'symbolic': sympy.latex(symbolic) if isinstance(symbolic, sympy.Expr) else str(symbolic),
                'magnitude': magnitude,
                'phase': phase*(180/cmath.pi)
            }

        output['sfg'] = nx.cytoscape_data(sfg)
        return output

    # def import_sfg(self, sfg_obj):
    #     # TODO make sfg_obj (dictionary obj) --> sfg graph obj

    #     # serialize sfg graph obj to binary field and set to self.sfg
    #     sfg_serialized = dill.dumps(sfg_graph_obj)
    #     self.sfg = sfg_serialized

    def import_circuit(self, new_circuit):
        print(self.id)
        print(new_circuit.id)
        # self.name = new_circuit.name
        self.svg = new_circuit.svg
        self.schematic = new_circuit.schematic
        self.netlist = new_circuit.netlist
        self.op_point_log = new_circuit.op_point_log
        self.parameters = new_circuit.parameters
        self.sfg = new_circuit.sfg
        self.transfer_functions = new_circuit.transfer_functions
        self.loop_gain = new_circuit.loop_gain
        self.created = new_circuit.created
        self.sfg_stack = new_circuit.sfg_stack
        self.redo_stack = new_circuit.redo_stack

    def compute_phase_margin(
            self,
            gain: List[float],
            phase: List[float]
    ) -> Optional[float]:
        
        # Find the index where the gain is closest to 0 dB
        zero_db_index = min(range(len(gain)), key=lambda i: abs(gain[i]))
        
        # Check if the gain at the closest index is within a reasonable threshold of 0 dB
        #if abs(gain[zero_db_index]) > 0.1:  # Adjust threshold as needed
        #    return None  # or raise an exception if preferred

        # Get the phase at this index
        phase_at_zero_db = phase[zero_db_index]
        
        # Calculate the phase margin
        phase_margin = 180 - abs(phase_at_zero_db)

        #print ("The phase margin is: "+phase_margin) # Temporarily adding print statement for BOL
        
        return phase_margin

    def sweep_params_for_phase_margin(
        self,
        input_node: str,
        output_node: str,
        param_name: str,  
        min_value: float,
        max_value: float,
        step: float
    ) -> Tuple[List[float], List[float]]:
        """Sweeps capacitance values and plots capacitance vs. phase margin.

        Args:
            param_name: Name of the capacitor parameter to update.
            min_value: Minimum capacitance value to test.
            max_value: Maximum capacitance value to test.
            step: Increment step for capacitance.
            freq, gain, phase: Frequency, gain, and phase lists to compute phase margin.

        Returns:
            A tuple of two lists: capacitances and their corresponding phase margins.
        """
        param_values = []
        phase_margins = []

        original_param = self.parameters[param_name]
        # Parameters for eval_loop_gain
        start_freq = 1e3
        end_freq = 1e12
        points_per_decade = 30

        # Sweep capacitance values
        current_value = min_value
        while current_value <= max_value:
            # Update the specified capacitance in the circuit
            self.update_parameters({param_name: current_value})
            freq_list, gain_list, phase_list= self.eval_transfer_function(input_node=input_node,
                                                                        output_node=output_node,
                                                                        start_freq=start_freq,
                                                                        end_freq=end_freq,
                                                                        points_per_decade=points_per_decade)

            # Compute the phase margin for the current capacitance
            phase_margin = self.compute_phase_margin(gain_list, phase_list)
            
            # Store results
            param_values.append(current_value)
            phase_margins.append(phase_margin)

            print("Testing: "+str(current_value)+" F")
            print("Phase margin: "+str(phase_margin)+" deg")
            
            # Increment capacitance
            current_value += step
            current_value = round(current_value,max(0, -int(math.floor(math.log10(abs(step))))))
        
        self.update_parameters({param_name: original_param})

        return param_values, phase_margins

    def calculate_bandwidth(
            self,
            frequencies: List[float],
            magnitudes: List[float]
    ) -> Optional[float]:
        """
        Calculate the bandwidth frequency where the gain is closest to max_gain - 3 dB.

        Args:
            frequencies: List of frequency values.
            magnitudes: List of corresponding gain values in dB.

        Returns:
            float: Frequency at the closest -3 dB point (bandwidth).
            None: If no such point is found.
        """
        # Determine the max gain and -3 dB threshold
        max_gain_db = np.max(magnitudes)
        threshold_db = max_gain_db - 3

        # Find the index of the peak gain
        max_index = np.argmax(magnitudes)

        # Extract the part of the frequency and magnitude arrays after the peak
        post_peak_frequencies = frequencies[max_index + 1:]
        post_peak_magnitudes = magnitudes[max_index + 1:]

        if not post_peak_frequencies:
            return None  # Return None if there are no points after the peak

        # Find the index of the magnitude closest to the threshold
        closest_index = np.argmin(np.abs(np.array(post_peak_magnitudes) - threshold_db))

        # Return the corresponding frequency
        return post_peak_frequencies[closest_index]
    
    def sweep_params_for_bandwidth(
        self,
        input_node: str,
        output_node: str,
        param_name: str,  
        min_val: float,
        max_val: float,
        step: float
    ) -> Tuple[List[float], List[float]]:
        """Sweeps inputted parameter values and plots inputted parameter vs. bandwidth.

        Args:
            input_node:
            output_node
            param_name: Name of the parameter to update.
            min_val: Minimum value to test.
            max_val: Maximum value to test.
            step: Increment step for capacitance.
            freq, gain, phase: Frequency, gain, and phase lists to compute phase margin.

        Returns:
            
        """
        param_values = []
        bandwidths = []

        original_param = self.parameters[param_name]
        # Parameters for eval_loop_gain
        start_freq = 1e3
        end_freq = 1e12
        points_per_decade = 30

        # Sweep capacitance values
        current_val = min_val
        while current_val <= max_val:
            # Update the specified capacitance in the circuit
            self.update_parameters({param_name: current_val})
            freq_list, gain_list, phase_list= self.eval_transfer_function(input_node=input_node,
                                                                        output_node=output_node,
                                                                        start_freq=start_freq,
                                                                        end_freq=end_freq,
                                                                        points_per_decade=points_per_decade)

            # Compute the phase margin for the current capacitance
            bandwidth = self.calculate_bandwidth(freq_list, gain_list)
            
            # Store results
            param_values.append(current_val)
            bandwidths.append(bandwidth)

            print("Testing: "+str(current_val))
            print("Bandwidth: "+str(bandwidth)+" hz")
            
            # Increment capacitance
            current_val += step
            current_val = round(current_val,max(0, -int(math.floor(math.log10(abs(step))))))
        
        self.update_parameters({param_name: original_param})

        return param_values, bandwidths