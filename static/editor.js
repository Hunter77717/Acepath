
// Initialize the Monaco editor
require.config({ paths: { 'vs': 'https://unpkg.com/monaco-editor/min/vs' } });
require(['vs/editor/editor.main'], function () {
    window.editor = monaco.editor.create(document.getElementById('editor'), {
        value: '',
        language: 'python',
        theme: 'vs-dark'
    });
});

// Run button functionality
document.getElementById('run-btn').addEventListener('click', function() {
    const code = window.editor.getValue();
    const outputDiv = document.getElementById('output');
    const inputBox = document.getElementById('input-box');

    outputDiv.textContent = '';  // Clear previous output

    if (code.includes('input(')) {
        inputBox.style.display = 'block';
        inputBox.focus();
        inputBox.onkeypress = function(event) {
            if (event.key === 'Enter') {
                const userInput = inputBox.value;
                inputBox.style.display = 'none';
                inputBox.value = '';
                runCodeWithInput(code, userInput);
            }
        };
    } else {
        runCodeWithInput(code);
    }
});

// Reset button functionality (for the code editor)
document.getElementById('reset-btn').addEventListener('click', function() {
    window.editor.setValue('');  // Clear the code in the editor
    document.getElementById('output').textContent = '';  // Clear the output
    document.getElementById('input-box').style.display = 'none';  // Hide the input box
    document.getElementById('input-box').value = '';  // Clear the input box
});

// Send button for AI interaction
document.getElementById('send-btn').addEventListener('click', function() {
    const prompt = document.getElementById('prompt-input').value;
    if (prompt.trim()) {
        askAI(prompt);
    }
});

// Reset chat button functionality (for the AI response and input)
document.getElementById('reset-chat-btn').addEventListener('click', function() {
    document.getElementById('ai-response').textContent = 'AI Responses will appear here...';  // Clear AI response
    document.getElementById('prompt-input').value = '';  // Clear AI input
});

// Toggle Sidebar
const sidebar = document.getElementById('sidebar');
const toggleBtn = document.getElementById('sidebar-toggle');

toggleBtn.addEventListener('click', function() {
    if (sidebar.classList.contains('active')) {
        sidebar.classList.remove('active');
        toggleBtn.innerHTML = '→';  // Arrow points right when collapsed
    } else {
        sidebar.classList.add('active');
        toggleBtn.innerHTML = '←';  // Arrow points left when expanded
    }
});

// Function to run the Python code with or without user input
function runCodeWithInput(code, userInput = '') {
    fetch('/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: code, input: userInput })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('output').textContent = data.output;  // Display output
    })
    .catch(error => console.error('Error:', error));
}

// Function to send the prompt to the AI model and get the response
function askAI(prompt) {
    fetch('/ask-ai', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: prompt })
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById('ai-response').textContent = "AI Response: " + data.response;  // Display AI response
    })
    .catch(error => console.error('Error:', error));
}


