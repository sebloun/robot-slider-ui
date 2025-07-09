from flask import Flask, render_template, copy_current_request_context
from flask_socketio import SocketIO, emit
import time
from threading import Thread

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Simulated robot state
current_positions = {
    'joint1': 0,
    'joint2': 0,
    'joint3': 0,
    'joint4': 0,
    'joint5': 0,
    'joint6': 0
}

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
    print('Client connected')
    emit('position_update', current_positions)

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('set_target_positions')
def handle_set_positions(data):
    positions = data['positions']
    duration = float(data['duration'])
    print(f"Received target positions: {positions} with duration: {duration}s")
    
    # Use copy_current_request_context to preserve context for background thread
    @copy_current_request_context
    def execute_movement(target_pos, duration):
        start_pos = current_positions.copy()
        start_time = time.time()
        
        try:
            emit('status_update', {'message': f'Movement started (duration: {duration}s)', 'type': 'success'})
            
            while True:
                elapsed = time.time() - start_time
                progress = min(elapsed / duration, 1.0)
                interp_factor = quintic_interpolation(elapsed, duration)
                
                # Update each joint position with 2 decimal precision
                for joint in target_pos:
                    current_positions[joint] = round(
                        start_pos[joint] + (target_pos[joint] - start_pos[joint]) * interp_factor,
                        2
                    )
                
                # Use socketio.emit (not emit) in background thread
                socketio.emit('position_update', current_positions)
                
                if progress >= 1.0:
                    break
                    
                time.sleep(0.02)  # Update rate (~50Hz)
            
            socketio.emit('status_update', {'message': 'Movement completed', 'type': 'success'})
        except Exception as e:
            print(f"Error in movement thread: {e}")
            socketio.emit('status_update', {'message': f'Movement error: {str(e)}', 'type': 'error'})
    
    # Start the movement thread
    Thread(target=execute_movement, args=(positions, duration)).start()

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)