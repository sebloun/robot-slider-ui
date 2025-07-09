
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

def execute_movement(target_pos, duration):
    def position_callback(new_positions, error=None):
        if error:
            socketio.emit('error', {'message': str(error)})
        else:
            socketio.emit('position_update', new_positions)
    
    robot_state.execute_movement(target_pos, duration, position_callback)

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