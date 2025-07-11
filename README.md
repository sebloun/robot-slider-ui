# Robot Slider UI
## Development
1. Install python packages
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2. Run the application
```bash
python app.py
```
3. Open the UI in your browser:
```
http://localhost:5001/
```

## Docker
1. Build the image from the repository root with
```bash
docker build -t robotsliderui .
```
2. Run the container with
```bash
docker run -p 5001:5001 robotsliderui
```
3. Open the UI in your browser:
```
http://localhost:5001/
```
