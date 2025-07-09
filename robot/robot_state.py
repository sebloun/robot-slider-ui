import xml.etree.ElementTree as ET
from threading import Lock


class RobotState:
    def __init__(self, urdf_file: str) :
        self.lock = Lock()
        self.positions: dict[str, float] = {}
        self.limits: dict[str, dict[str, float]] = {}
        self.load_urdf(urdf_file)
        
        for joint in self.limits:
            if joint not in self.positions:
                self.positions[joint] = 0  # Default to zero position

    def load_urdf(self, urdf_file:str):
        try:
            tree = ET.parse(urdf_file)
            root = tree.getroot()
            
            for joint in root.findall('joint'):
                name = joint.get('name')
                if name and joint.get('type') == 'revolute':
                    limit = joint.find('limit')
                    if limit is not None:
                        self.limits[name] = {
                            'min': float(limit.get('lower')),
                            'max': float(limit.get('upper'))
                        }
                        
                        # Check for initial position in URDF (not standard, but can be added)
                        initial_pos = joint.find('initial_position')
                        if initial_pos is not None:
                            self.positions[name] = float(initial_pos.text)
            
            # Verify we found all expected joints
            expected_joints = ['joint1', 'joint2', 'joint3', 'joint4', 'joint5', 'joint6']
            for joint in expected_joints:
                if joint not in self.limits:
                    raise ValueError(f"Missing joint {joint} in URDF file")
                    
        except Exception as e:
            print(f"Error loading URDF: {e}")
            # Fallback to hardcoded values if URDF loading fails
            self.positions = {
                'joint1': 0, 'joint2': 0, 'joint3': 30,
                'joint4': 40, 'joint5': 30, 'joint6': 20
            }
            self.limits = {
                'joint1': {'min': -110, 'max': 20},
                'joint2': {'min': -180, 'max': 180},
                'joint3': {'min': -180, 'max': 180},
                'joint4': {'min': -130, 'max': 120},
                'joint5': {'min': -180, 'max': 180},
                'joint6': {'min': -180, 'max': 180}
            }
