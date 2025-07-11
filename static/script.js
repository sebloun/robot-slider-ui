// Initialize joint state
const jointState = {
    targetValues: {
        joint1: 0,
        joint2: 0,
        joint3: 0,
        joint4: 0,
        joint5: 0,
        joint6: 0
    },
    limits: {
        joint1: { min: -180, max: 180 },
        joint2: { min: -180, max: 180 },
        joint3: { min: -180, max: 180 },
        joint4: { min: -180, max: 180 },
        joint5: { min: -180, max: 180 },
        joint6: { min: -180, max: 180 }
    }
};

let scene, camera, renderer, robot;
const robotJoints = {};

function initThree() {
    // Scene setup
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xe0e0e0);

    // Camera setup
    camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    camera.position.z = 15;
    camera.position.y = 5;

    // Renderer setup
    const displayDiv = document.getElementById('robot-display');
    renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(displayDiv.clientWidth, displayDiv.clientHeight);
    displayDiv.appendChild(renderer.domElement);

    // Lighting
    const ambientLight = new THREE.AmbientLight(0x404040); // Soft white light
    scene.add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
    directionalLight.position.set(5, 5, 5);
    scene.add(directionalLight);

    // Create the robot
    createRobot();

    // Start the animation loop
    animate();

    // Handle window resizing
    window.addEventListener('resize', onWindowResize, false);
}

function onWindowResize() {
    const displayDiv = document.getElementById('robot-display');
    camera.aspect = displayDiv.clientWidth / displayDiv.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(displayDiv.clientWidth, displayDiv.clientHeight);
}

function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}
// Connect to WebSocket with robust configuration
const socket = io('http://localhost:5001', {
    transports: ['websocket'],
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionAttempts: Infinity
});

// DOM elements
const statusElement = document.getElementById('status-message');
const connectionStatus = document.getElementById('connection-status');

// Initialize sliders with limits
function initializeSliders() {
    for (const [jointId, limit] of Object.entries(jointState.limits)) {
        const targetSlider = document.getElementById(`${jointId}-target`);
        const currentSlider = document.getElementById(`${jointId}-current`);
        const limitsDisplay = document.getElementById(`${jointId}-limits`);

        if (targetSlider) {
            targetSlider.min = limit.min;
            targetSlider.max = limit.max;
            targetSlider.value = jointState.targetValues[jointId];
        }

        if (currentSlider) {
            currentSlider.min = limit.min;
            currentSlider.max = limit.max;
        }
        if (limitsDisplay) {
            limitsDisplay.innerHTML = `<span>${limit.min}°</span><span>${limit.max}°</span>`;
        }

    }
}

// Update joint display
function updateJointDisplay(jointId, value, isTarget = true) {
    const displayElement = document.getElementById(`${jointId}-${isTarget ? 'target' : 'current'}-value`);
    const sliderElement = document.getElementById(`${jointId}-${isTarget ? 'target' : 'current'}`);

    if (displayElement) {
        const displayValue = isTarget ? Math.round(value) : value.toFixed(2);
        displayElement.textContent = `${displayValue}°`;
    }

    if (sliderElement) {
        sliderElement.value = value;
    }

    if (isTarget) {
        jointState.targetValues[jointId] = value;
    }
}

// Initialize with fallback values
document.addEventListener('DOMContentLoaded', () => {
    initializeSliders();
    initThree(); // Initialize the 3D scene

    // Set up event listeners for all target sliders
    document.querySelectorAll('.slider[id$="-target"]').forEach(slider => {
        const jointId = slider.id.replace('-target', '');
        updateJointDisplay(jointId, slider.value, true);

        slider.addEventListener('input', function () {
            updateJointDisplay(jointId, this.value, true);
        });
    });
});

// Socket event handlers
socket.on('connect', () => {
    console.log('Connected to WebSocket server');
    connectionStatus.textContent = 'Connected';
    connectionStatus.className = 'connection-status connected';
});

socket.on('connect_error', (error) => {
    console.error('Connection Error:', error);
    connectionStatus.textContent = 'Connection Error';
    connectionStatus.className = 'connection-status error';
});

socket.on('disconnect', (reason) => {
    console.log('Disconnected:', reason);
    connectionStatus.textContent = 'Disconnected';
    connectionStatus.className = 'connection-status disconnected';
    if (reason === 'io server disconnect') {
        socket.connect();
    }
});


socket.on('init_state', (data) => {
    // Update limits if provided by server
    if (data.limits) {
        Object.assign(jointState.limits, data.limits);
        initializeSliders();
    }

    // Update current positions if provided
    if (data.positions) {
        Object.entries(data.positions).forEach(([jointId, value]) => {
            updateJointDisplay(jointId, value, false);
        });
    }
});

socket.on('position_update', (positions) => {
    Object.entries(positions).forEach(([jointId, value]) => {
        updateJointDisplay(jointId, value, false);
        if (robotJoints[jointId]) {
            const angleInRadians = THREE.MathUtils.degToRad(value);

            // Set the rotation based on the joint's axis of movement
            switch (jointId) {
                case 'joint1': // Base (Y-axis rotation)
                    robotJoints.joint1.rotation.y = angleInRadians;
                    break;
                case 'joint2': // Shoulder (X-axis rotation)
                    robotJoints.joint2.rotation.x = angleInRadians;
                    break;
                case 'joint3': // Elbow (X-axis rotation)
                    robotJoints.joint3.rotation.x = angleInRadians;
                    break;
                case 'joint4': // Wrist Roll (Y-axis rotation)
                    robotJoints.joint4.rotation.y = angleInRadians;
                    break;
                case 'joint5': // Wrist Pitch (X-axis rotation)
                    robotJoints.joint5.rotation.x = angleInRadians;
                    break;
                case 'joint6': // Wrist Yaw (Z-axis rotation)
                    robotJoints.joint6.rotation.z = angleInRadians;
                    break;
            }
        }
    });
});

socket.on('status_update', (data) => {
    statusElement.textContent = data.message;
    statusElement.className = `status ${data.type}`;
    statusElement.style.display = 'block';
    setTimeout(() => { statusElement.style.display = 'none'; }, 3000);
});

// Button event handlers
document.getElementById('send-command').addEventListener('click', () => {
    const durationInput = document.getElementById('movement-duration');
    const duration = parseFloat(durationInput.value);

    if (isNaN(duration) || duration <= 0) {
        statusElement.textContent = 'Please enter a valid duration (> 0)';
        statusElement.className = 'status error';
        statusElement.style.display = 'block';
        setTimeout(() => { statusElement.style.display = 'none'; }, 3000);
        return;
    }

    socket.emit('set_target_positions', {
        positions: jointState.targetValues,
        duration: duration
    });
});

document.getElementById('reset-position').addEventListener('click', () => {
    Object.keys(jointState.targetValues).forEach(jointId => {
        updateJointDisplay(jointId, 0, true);
    });
});

function createRobot() {
    const material = new THREE.MeshStandardMaterial({ color: 0x606060, metalness: 0.8, roughness: 0.5 });

    // --- Joint 1 (Base) ---
    const baseGeometry = new THREE.CylinderGeometry(2, 2, 1, 32);
    robotJoints.joint1 = new THREE.Object3D();
    const baseMesh = new THREE.Mesh(baseGeometry, material);
    robotJoints.joint1.add(baseMesh);
    scene.add(robotJoints.joint1);

    // --- Joint 2 (Shoulder) ---
    const shoulderGeometry = new THREE.BoxGeometry(1.5, 4, 1.5);
    shoulderGeometry.translate(0, 2, 0); // Pivot at the bottom
    robotJoints.joint2 = new THREE.Mesh(shoulderGeometry, material);
    robotJoints.joint2.position.y = 1; // Position on top of the base
    robotJoints.joint1.add(robotJoints.joint2);

    // --- Joint 3 (Elbow) ---
    const elbowGeometry = new THREE.BoxGeometry(1.5, 4, 1.5);
    elbowGeometry.translate(0, 2, 0);
    robotJoints.joint3 = new THREE.Mesh(elbowGeometry, material);
    robotJoints.joint3.position.y = 4; // Position at the end of the shoulder
    robotJoints.joint2.add(robotJoints.joint3);

    // --- Joint 4 (Wrist Roll) ---
    const wristRollGeometry = new THREE.CylinderGeometry(0.5, 0.5, 1, 32);
    robotJoints.joint4 = new THREE.Mesh(wristRollGeometry, material);
    robotJoints.joint4.position.y = 4; // Position at the end of the elbow
    robotJoints.joint3.add(robotJoints.joint4);

    // --- Joint 5 (Wrist Pitch) ---
    const wristPitchGeometry = new THREE.BoxGeometry(0.5, 2, 0.5);
    wristPitchGeometry.translate(0, 1, 0);
    robotJoints.joint5 = new THREE.Mesh(wristPitchGeometry, material);
    robotJoints.joint5.position.y = 0.5; // Position on the wrist roll
    robotJoints.joint4.add(robotJoints.joint5);

    // --- Joint 6 (Wrist Yaw) ---
    const wristYawGeometry = new THREE.BoxGeometry(1, 0.5, 0.5);
    robotJoints.joint6 = new THREE.Mesh(wristYawGeometry, material);
    robotJoints.joint6.position.y = 2; // Position at the end of the wrist pitch
    robotJoints.joint5.add(robotJoints.joint6);
}
