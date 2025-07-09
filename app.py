import time
from threading import Thread

from flask import Flask, render_template
from flask_socketio import SocketIO

from robot.robot_state import RobotState

app = Flask(__name__)
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   async_mode='threading')


robot_state = RobotState(urdf_file="robot/robot.urdf")

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

def quintic_interpolation(t, duration):
    """Calculate interpolation factor (0 to 1) using quintic polynomial"""
    normalized_time = t / duration
    if normalized_time >= 1:
        return 1.0
    return 10 * normalized_time**3 - 15 * normalized_time**4 + 6 * normalized_time**5

def execute_movement(target_pos, duration):
    try:
        start_time = time.time()
        start_pos = robot_state.positions.copy()
        
        while True:
            elapsed = time.time() - start_time
            progress = min(elapsed / duration, 1.0)
            interp_factor = quintic_interpolation(elapsed, duration)

            with robot_state.lock:
                for joint in target_pos:
                    robot_state.positions[joint] = round(
                        start_pos[joint] + (target_pos[joint] - start_pos[joint]) * interp_factor,
                        2
                    )
                
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