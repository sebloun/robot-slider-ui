from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/update_joints', methods=['POST'])
def update_joints():
    joint_values = request.json
    print(f"Received joint values: {joint_values}")
    # Here you would typically send these values to your robot controller
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True)
