// Ensure that face-api.js is loaded correctly
if (typeof faceapi === 'undefined') {
    console.error('face-api.js is not loaded. Please include it first.');
}

// Function to load models from the /static/js/face-api.js-master/weights folder
async function loadModels() {
    try {
        console.log('Loading models...');

        // Load the models from the local /static/js/face-api.js-master/weights folder
        await faceapi.nets.ssdMobilenetv1.loadFromUri('/static/js/face-api.js-master/weights');
        await faceapi.nets.faceLandmark68Net.loadFromUri('/static/js/face-api.js-master/weights');
        await faceapi.nets.faceRecognitionNet.loadFromUri('/static/js/face-api.js-master/weights');
        await faceapi.nets.faceExpressionNet.loadFromUri('/static/js/face-api.js-master/weights');

        console.log('Models loaded successfully!');
    } catch (error) {
        console.error('Error loading models:', error);
    }
}

// Function to start face recognition using a video element
async function startFaceRecognition(videoElement) {
    if (!videoElement) {
        console.error('Video element not found.');
        return;
    }

    try {
        // Access the webcam to stream video
        const stream = await navigator.mediaDevices.getUserMedia({ video: {} });
        videoElement.srcObject = stream;

        // Process the video when it starts playing
        videoElement.onplay = async () => {
            console.log('Video is playing...');
            
            // Detect faces and facial expressions once
            const detections = await faceapi.detectSingleFace(videoElement)
                .withFaceLandmarks()
                .withFaceExpressions();

            if (!detections) {
                console.log("No face detected.");
                return;
            }

            // Log the detected expressions
            const expressions = detections.expressions;
            const highestMood = Object.keys(expressions).reduce((a, b) => expressions[a] > expressions[b] ? a : b);
            console.log('Detected mood:', highestMood);

            // Send the detected mood to the backend
            fetch('/detect_mood', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ mood: highestMood }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.redirect) {
                    window.location.href = data.redirect;  // Redirect to the player page with mood-based playlist
                }
            })
            .catch(error => {
                console.error('Error sending mood to backend:', error);
            });
        };
    } catch (err) {
        console.error("Error accessing webcam: ", err);
    }
}

// Wait for the 'Detect Mood' button to be clicked to start face recognition
document.getElementById('detectMoodBtn').addEventListener('click', async function(event) {
    event.preventDefault();
    const video = document.getElementById('video');
    video.style.display = 'block';  // Show the video element after button click
    await loadModels();  // Load models before starting face recognition
    startFaceRecognition(video);  // Start face recognition when the user clicks the button
});
