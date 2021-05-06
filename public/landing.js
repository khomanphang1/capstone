const baseUrl = window.location.origin;

console.log('Loaded script')

const json = {
    name: "untitled",
    netlist: null,
    op_point_log: null,
    schematic: null
}

const form = document.getElementById('uploadForm');

form.addEventListener('submit', async function(event) {
    event.preventDefault();
    console.log('Uploading circuit');
    console.log(json);

    try {
        const response = await fetch(`{$baseUrl}/circuits`,
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
    
