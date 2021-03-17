# API Reference
## **GET** /circuits/:id
Returns circuit-related data associated with the specified ID.

### Path Parameters
| Name             | Type   | Description                      |
|------------------|--------|----------------------------------|
| `id`<br>REQUIRED | string | The ID of the circuit to lookup. |

### Query Parameters
| Name                      | Type    | Description                                                                               |
|---------------------------|---------|-------------------------------------------------------------------------------------------|
| `fields`<br>OPTIONAL      | array   | The list of fields to include in the response.                                            |

### Response Fields
| Name                     | Type   | Description                                                             |
|--------------------------|--------|-------------------------------------------------------------------------|
| `id`<br>DEFAULT          | string | The ID of the circuit.                                                  |
| `name`<br>DEFAULT        | string | The name of the circuit.                                                |
| `parameters`<br>DEFAULT  | object | A mapping between component parameter names and their numerical values. |
| `sfg`<br>DEFAULT         | object | A signal-flow graph in Cytoscape format.                                |
| `svg`<br>OPTIONAL        | string | An HTML SVG element that contains a drawing of the circuit.             |

<br>

## **POST** /circuits
Creates a new circuit.

### Query Parameters
| Name                      | Type    | Description                                                                               |
|---------------------------|---------|-------------------------------------------------------------------------------------------|
| `fields`<br>OPTIONAL      | array   | The list of fields to include in the response.                                            |

### JSON Body Parameters
| Name                       | Type   | Description                                                                                                                                   |
|----------------------------|--------|-----------------------------------------------------------------------------------------------------------------------------------------------|
| `name`<br>REQUIRED         | string | The name of the circuit.                                                                                                                      |
| `netlist`<br>REQUIRED      | string | The content of a .net LTspice netlist file.                                                                                                   |
| `schematic`<br>OPTIONAL    | string | The content of a .asc LTspice schematic file. If not supplied, the circuit's `svg` field will be unavailable.                                 |
| `op_point_log`<br>OPTIONAL | string | The content of a .log LTspice operating point analysis log file. If not supplied, the circuit is presumed to be in small-signal form already. |

### Response Fields
| Name                     | Type   | Description                                                             |
|--------------------------|--------|-------------------------------------------------------------------------|
| `id`<br>DEFAULT          | string | The ID of the circuit.                                                  |
| `name`<br>DEFAULT        | string | The name of the circuit.                                                |
| `parameters`<br>DEFAULT  | object | A mapping between component parameter names and their numerical values. |
| `sfg`<br>DEFAULT         | object | A signal-flow graph in Cytoscape format.                                |
| `svg`<br>OPTIONAL        | string | An HTML SVG element that contains a drawing of the circuit.             |

<br>

## **PATCH** /circuits/:id
For a circuit with the specified ID, modifies the numerical values of a given set of circuit parameters.

### Path Parameters
| Name             | Type   | Description                      |
|------------------|--------|----------------------------------|
| `id`<br>REQUIRED | string | The ID of the circuit to lookup. |

### JSON Body Parameters
The body should be a flat object consisting of key-value pairs. For example, 
```json
{
    "f": 1e3,
    "C1": 1e-6
}
```
means circuit parameters "f" and "C1" will be updated to their new numerical values. The keys (i.e. parameter names) must be a subset of the keys found in the `parameters` field the circuit.

<br>

## **GET** /circuits/:id/transfer_function
For a circuit with the specified ID, returns the symbolic transfer function expression between a pair of input and output nodes.

### Path Parameters
| Name             | Type   | Description                      |
|------------------|--------|----------------------------------|
| `id`<br>REQUIRED | string | The ID of the circuit to lookup. |

### Query Parameters
| Name                      | Type    | Description                                                                               |
|---------------------------|---------|-------------------------------------------------------------------------------------------|
| `input_node`<br>REQUIRED  | string  | The input circuit node.                                                                   |
| `output_node`<br>REQUIRED | string  | The output circuit node.                                                                  |
| `latex`<br>OPTIONAL       | boolean | If True, formats the expression in latex. If False, returns the expression in plain text. |

### Response Fields
| Name                | Type   | Description                                |
|---------------------|--------|--------------------------------------------|
| `transfer_function` | string | The symbolic transfer function expression. |

<br>

## **GET** /circuits/:id/transfer_function/bode
For a circuit with the specified ID, and for the transfer function between a pair of input and output nodes, returns the gain and phase values over a frequency range.

### Path Parameters
| Name             | Type   | Description                      |
|------------------|--------|----------------------------------|
| `id`<br>REQUIRED | string | The ID of the circuit to lookup. |

### Query Parameters
| Name                            | Type    | Description                                                                                            |
|---------------------------------|---------|--------------------------------------------------------------------------------------------------------|
| `input_node`<br>REQUIRED        | string  | The input circuit node.                                                                                |
| `outut_node`<br>REQUIRED        | string  | The output circuit node.                                                                               |
| `start_freq`<br>REQUIRED        | float   | The starting frequency.                                                                                |
| `end_freq`<br>REQUIRED          | float   | The ending frequency.                                                                                  |
| `points_per_decade`<br>REQUIRED | integer | The number of points per decade of frequency.                                                          |
| `frequency_unit`<br>OPTIONAL    | string  | The frequency unit. Can be either "hz" for hertz, or "rad/s" for radians per second. Defaults to "hz". |
| `gain_unit`<br>OPTIONAL         | string  | The gain unit. Can be either "" for dimensionless, or "db" for decibels. Defaults to "db".             |
| `phase_unit`<br>OPTIONAL        | string  | The phase unit. Can be either "deg" for degrees, or "rad" for radians. Defaults to "deg".              |

### Response Fields
| Name                | Type   | Description                                            |
|---------------------|--------|--------------------------------------------------------|
| `frequency`<br>     | array  | A list of frequencies.                                 |
| `gain`<br>          | array  | A list of gain values over the input frequency range.  |
| `phase`<br>         | array  | A list of phase values over the input frequency range. |

<br>

## **GET** /circuits/:id/loop_gain
For a circuit with the specified ID, return its symbolic loop gain function expression.

### Path Parameters
| Name             | Type   | Description                      |
|------------------|--------|----------------------------------|
| `id`<br>REQUIRED | string | The ID of the circuit to lookup. |

### Query Parameters
| Name                      | Type    | Description                                                                               |
|---------------------------|---------|-------------------------------------------------------------------------------------------|
| `latex`<br>OPTIONAL       | boolean | If True, formats the expression in latex. If False, returns the expression in plain text. |

### Response Fields
| Name                | Type   | Description                                 |
|---------------------|--------|---------------------------------------------|
| `loop_gain`         | string | The symbolic loop gain function expression. |

<br>

## **GET** /circuits/:id/loop_gain/bode
For a circuit with the specified ID, for its loop gain function, returns the gain and phase values over a frequency range.

### Path Parameters
| Name             | Type   | Description                      |
|------------------|--------|----------------------------------|
| `id`<br>REQUIRED | string | The ID of the circuit to lookup. |

### Query Parameters
| Name                            | Type    | Description                                                                                            |
|---------------------------------|---------|--------------------------------------------------------------------------------------------------------|
| `start_freq`<br>REQUIRED        | float   | The starting frequency.                                                                                |
| `end_freq`<br>REQUIRED          | float   | The ending frequency.                                                                                  |
| `points_per_decade`<br>REQUIRED | integer | The number of points per decade of frequency.                                                          |
| `frequency_unit`<br>OPTIONAL    | string  | The frequency unit. Can be either "hz" for hertz, or "rad/s" for radians per second. Defaults to "hz". |
| `gain_unit`<br>OPTIONAL         | string  | The gain unit. Can be either "" for dimensionless, or "db" for decibels. Defaults to "db".             |
| `phase_unit`<br>OPTIONAL        | string  | The phase unit. Can be either "deg" for degrees, or "rad" for radians. Defaults to "deg".              |

### Response Fields
| Name                | Type   | Description                                            |
|---------------------|--------|--------------------------------------------------------|
| `frequency`<br>     | array  | A list of frequencies.                                 |
| `gain`<br>          | array  | A list of gain values over the input frequency range.  |
| `phase`<br>         | array  | A list of phase values over the input frequency range. |


<br><span style="background-color:DodgerBlue;padding:0.3rem;font-size:0.6rem;font-weight:bold;color:white;">REQUIRED</span>

<br><span style="background-color:DodgerBlue;padding:0.3rem;font-size:0.6rem;font-weight:bold;color:white;">DEFAULT</span>

<br><span style="background-color:white;border:solid 0.1rem;padding:0.2rem;font-size:0.6rem;font-weight:bold;color:DodgerBlue;border-color:DodgerBlue;">OPTIONAL</span>