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
