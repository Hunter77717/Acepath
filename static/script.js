let recognition;
let webcamStream;

if ('webkitSpeechRecognition' in window) {
    recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
}

function fetchQuestion() {
    fetch('/get_question')
        .then(response => response.json())
        .then(data => {
            document.getElementById("aiOutput").innerText = data.question;
            document.getElementById("aiOutput").setAttribute("data-keywords", JSON.stringify(data.keywords));
        });
}

function startRecording() {
    if (!recognition) return;
    recognition.start();
    recognition.onresult = function(event) {
        const userInput = event.results[0][0].transcript;
        document.getElementById("aiOutput").innerText = "Processing feedback...";

        const keywords = JSON.parse(document.getElementById("aiOutput").getAttribute("data-keywords"));

        fetch('/feedback', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_input: userInput,
                keywords: keywords
            }),
        })
        .then(response => response.json())
        .then(data => {
            document.getElementById("aiOutput").innerText = data.feedback;
        });
    };

    recognition.onerror = function(event) {
        console.error("Speech recognition error detected: " + event.error);
        document.getElementById("aiOutput").innerText = "Speech recognition error. Try again.";
    };
}

function toggleWebcam() {
    const videoElement = document.getElementById('webcam');

    if (webcamStream) {
        // Stop webcam stream if it is active
        webcamStream.getTracks().forEach(track => track.stop());
        webcamStream = null;
        videoElement.srcObject = null;
    } else {
        // Access the webcam
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                webcamStream = stream;
                videoElement.srcObject = stream;
            })
            .catch(error => {
                console.error("Error accessing the webcam: ", error);
                alert("Unable to access the webcam. Please check your permissions.");
            });
    }
}
