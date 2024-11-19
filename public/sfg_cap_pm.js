// Input fields for capacitance vs. phase margin plot generation
function make_cap_vs_pm_plot_parameter_panel() {
    const form = document.createElement("form");
    form.id = "cap-form";

    // Text field for capacitor name
    const input1 = document.createElement("input");
    input1.type = "text";
    input1.placeholder = "Selected capacitor";
    input1.id = "selected-capacitor";
    form.appendChild(input1);

    // Text field for minimum capacitance
    const input2 = document.createElement("input");
    input2.type = "number";
    input2.placeholder = "Min cap (F)";
    input2.id = "min-capacitance";
    form.appendChild(input2);

    // Text field for maximum capacitance
    const input3 = document.createElement("input");
    input3.type = "number";
    input3.placeholder = "Max cap (F)";
    input3.id = "max-capacitance";
    form.appendChild(input3);

    // Text field for capacitance increment step size
    const input4 = document.createElement("input");
    input4.type = "number";
    input4.placeholder = "Step size (F)";
    input4.id = "step-size";
    form.appendChild(input4);

    // Submit button
    const submitButton = document.createElement("input");
    submitButton.type = "submit";
    submitButton.value = "Submit Form";
    form.appendChild(submitButton);

    // Append the form to the container
    const formContainer = document.getElementById("cap-pm-form");
    if (formContainer) {
        formContainer.appendChild(form);
    } else {
        console.error("Element with ID 'cap-pm-form' not found");
    }

    // event listener for the submit button
    submitButton.addEventListener("submit", event => {
        event.preventDefault();

        // Get the values from the form inputs
        let selectedCapacitor = input1.value;
        let minCapacitance = input2.value;
        let maxCapacitance = input3.value;
        let stepSize = input4.value;
    });

    document.getElementById("cap-pm-form").appendChild(form);

}

// Immediately call the function for testing
make_cap_vs_pm_plot_parameter_panel();
