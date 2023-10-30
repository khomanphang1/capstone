const baseUrl = window.location.origin;

console.log('Loaded script')

const json = {
    name: "untitled",
    netlist: null,
    op_point_log: null,
    schematic: null
}

const form = document.getElementById('uploadForm');

// // add modal for tutorial steps
// document.addEventListener("DOMContentLoaded", function() {
//     console.log("DOM loaded");
//     const tutorialModal = document.getElementById("tutorial-modal");
//     const nextButton = document.getElementById("next-button");

//     let currentStep = 0;
//     const tutorialSteps = [
//         {
//             title: "Step 1: Circuit File Upload",
//             content: "Upload your circuit file here.",
//         },
//         // Add more steps as needed
//     ];

//     function showStep(stepIndex) {
//         if (stepIndex < tutorialSteps.length) {
//             const step = tutorialSteps[stepIndex];
//             const modalContent = tutorialModal.querySelector(".modal-content");
//             modalContent.innerHTML = `
//                 <h2>${step.title}</h2>
//                 <p>${step.content}</p>
//                 <button id="next-button">Next</button>
//             `;
//             tutorialModal.style.display = "block";
//         } else {
//             // All steps completed, you can hide the modal or perform another action.
//             tutorialModal.style.display = "none";
//             alert("Demo completed!");
//         }
//     }

//     nextButton.addEventListener("click", function() {
//         currentStep++;
//         showStep(currentStep);
//     });

//     // Show the first step initially
//     showStep(currentStep);
// });


// // Get the modal
// var modal = document.getElementById("myModal");
// console.log("modal", modal);
// // Get the button that opens the modal
// var btn = document.getElementById("myBtn");
// console.log
// // Get the <span> element that closes the modal
// var span = document.getElementsByClassName("close")[0];
// console.log("span", span);
// // When the user clicks on the button, open the modal
// btn.onclick = function() {
//   modal.style.display = "block";
//   console.log("btn clicked");
// }

// // When the user clicks on <span> (x), close the modal
// span.onclick = function() {
//   modal.style.display = "none";
// }

// // When the user clicks anywhere outside of the modal, close it
// window.onclick = function(event) {
//   if (event.target == modal) {
//     modal.style.display = "none";
//   }
// }



const tutorialModal = document.getElementById("tutorial-modal");
const openModalButton = document.getElementById("open-modal-button");

let currentStep = 0;
const tutorialSteps = [
    {
        title: "Step 1: Circuit File Upload",
        content: "Upload your circuit file here.",
    },
    {
        title: "Step 2: Schematic File Upload",
        content: "Upload your schematic file here.",
    },
    {
        title: "Step 3: Operating Point Log File Upload",
        content: "Upload your operating point log file here.",
    }
    // Add more steps as needed
];

function showStep(stepIndex) {
    if (stepIndex < tutorialSteps.length) {
        const step = tutorialSteps[stepIndex];
        const modalContent = tutorialModal.querySelector(".modal-content");
        modalContent.innerHTML = `
            <h2>${step.title}</h2>
            <p>${step.content}</p>
            <button id="next-button">Next</button>
        `;

        const nextButton = modalContent.querySelector("#next-button"); // Get the button inside the modal
        nextButton.addEventListener("click", function() {
            console.log("next button clicked");
            currentStep++;
            showStep(currentStep);
        });

        tutorialModal.style.display = "block";
    } else {
        tutorialModal.style.display = "none";
        alert("Demo completed!");
    }
}

openModalButton.addEventListener("click", function() {
    console.log("open modal button clicked");
    currentStep = 0;
    showStep(currentStep);
});



form.addEventListener('submit', async function(event) {
    event.preventDefault();
    console.log('Uploading circuit');
    console.log(json);

    try {
        const response = await fetch(`${baseUrl}/circuits`,
        {
            method: 'POST', // *GET, POST, PUT, DELETE, etc.
            mode: 'cors', // no-cors, *cors, same-origin
            cache: 'no-cache', // *default, no-cache, reload, force-cache, only-if-cached
            credentials: 'same-origin', // include, *same-origin, omit
            headers: {
            'Content-Type': 'application/json'
            // 'Content-Type': 'application/x-www-form-urlencoded',
            },
            redirect: 'follow', // manual, *follow, error
            referrerPolicy: 'no-referrer', // no-referrer, *no-referrer-when-downgrade, origin, origin-when-cross-origin, same-origin, strict-origin, strict-origin-when-cross-origin, unsafe-url
            body: JSON.stringify(json) // body data type must match "Content-Type" header
        });
        
        const obj = await response.json();
        console.log(obj);
        console.log(`Created circuit with id: ${obj.id}`);
        sessionStorage.setItem('circuitId', obj.id);
        window.location.replace('./demo.html');
    } catch {
        alert('Failed to upload circuit.')
    }
})



console.log('Initialized null json to be sent');
console.log(json);


const netlistFile = document.getElementById('formControlNetlistFile');
netlistFile.addEventListener('change', event => {
    const file = event.target.files[0];

    const reader = new FileReader();

    reader.readAsText(file, 'utf-8');

    reader.onerror = function(event) {
        alert("Failed to read file!\n\n" + reader.error);
        reader.abort(); // (...does this do anything useful in an onerror handler?)
      };

    reader.onload = () => {
        const ext = file.name.match(/\.[0-9a-z]+$/i)[0].toLowerCase();
        console.log(`Succesfully read ${ext} file`);

        json.netlist = reader.result;
       
    }
});

const schematicFile = document.getElementById('formControlSchematicFile');
schematicFile.addEventListener('change', event => {
    const file = event.target.files[0];

    const reader = new FileReader();

    reader.readAsText(file, 'utf-8');

    reader.onerror = function(event) {
        alert("Failed to read file!\n\n" + reader.error);
        reader.abort(); // (...does this do anything useful in an onerror handler?)
      };

    reader.onload = () => {
        const ext = file.name.match(/\.[0-9a-z]+$/i)[0].toLowerCase();
        console.log(`Succesfully read ${ext} file`);

        json.schematic = reader.result;
    }
});


const opPointLogFile = document.getElementById('formControlOpLogFile');
opPointLogFile.addEventListener('change', event => {
    const file = event.target.files[0];

    const reader = new FileReader();

    reader.readAsText(file, 'utf-8');

    reader.onerror = function(event) {
        alert("Failed to read file!\n\n" + reader.error);
        reader.abort(); // (...does this do anything useful in an onerror handler?)
      };

    reader.onload = () => {
        console.log(`Succesfully read op point log`);
        json.op_point_log = reader.result;
    }
});
    
