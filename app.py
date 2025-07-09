import time
import xml.etree.ElementTree as ET
from threading import Lock, Thread

from flask import Flask, render_template
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='threading')

class RobotState:
    def __init__(self, urdf_file='robot.urdf'):
        self.lock = Lock()
        self.positions = {}
        self.limits = {}
        self.load_urdf(urdf_file)
        
        # Verify all joints were loaded
        required_joints = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
        for joint in required_joints:
            if joint not in self.positions:
                raise ValueError(f"Missing initial position for {joint} in URDF")
            if joint not in self.limits:
                raise ValueError(f"Missing limits for {joint} in URDF")

    def load_urdf(self, urdf_file):
        try:
            tree = ET.parse(urdf_file)
            root = tree.getroot()
            
            for joint in root.findall('joint'):
                name = joint.get('name')
                if name and joint.get('type') == 'revolute':
                    # Load limits
                    limit = joint.find('limit')
                    if limit is not None:
                        self.limits[name] = {
                            'min': float(limit.get('lower')),
                            'max': float(limit.get('upper'))
                        }
                    
                    # Load initial position
                    init_pos = joint.find('initial_position')
                    if init_pos is not None:
                        self.positions[name] = float(init_pos.text)
                    else:
                        raise ValueError(f"Missing initial_position for {name}")
                        
        except Exception as e:
            print(f"Error loading URDF: {e}")
            raise  # Re-raise exception since we require valid URDF

robot_state = RobotState()


def quintic_interpolation(t, duration):
    """Calculate interpolation factor (0 to 1) using quintic polynomial"""
    normalized_time = t / duration
    if normalized_time >= 1:
        return 1.0
    return 10 * normalized_time**3 - 15 * normalized_time**4 + 6 * normalized_time**5

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    with robot_state.lock:
        # Send initial state
        socketio.emit('init_state', {
            'positions': robot_state.positions,
            'limits': robot_state.limits
        })

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def execute_movement(target_pos, duration):
    try:
        start_time = time.time()
        start_pos = robot_state.positions.copy()
        
        while True:
            elapsed = time.time() - start_time
            progress = min(elapsed / duration, 1.0)
            
            # Calculate new positions
            with robot_state.lock:
                for joint in target_pos:
                    robot_state.positions[joint] = round(
                        start_pos[joint] + (target_pos[joint] - start_pos[joint]) * progress,
                        2
                    )
                
                # Emit update
                socketio.emit('position_update', robot_state.positions)
            
            if progress >= 1.0:
                break
                
            time.sleep(0.02)
            
    except Exception as e:
        socketio.emit('error', {'message': str(e)})

@socketio.on('set_target_positions')
def handle_set_positions(data):
    try:
        duration = float(data.get('duration', 2.0))
        target_pos = data['positions']
        
        # Validate positions against limits
        with robot_state.lock:
            for joint, pos in target_pos.items():
                limits = robot_state.limits.get(joint, {})
                target_pos[joint] = max(limits.get('min', -180), 
                                      min(limits.get('max', 180), 
                                      float(pos)))
        
        # Start movement in background thread
        Thread(target=execute_movement, args=(target_pos, duration)).start()
        
    except Exception as e:
        socketio.emit('error', {'message': str(e)})


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)