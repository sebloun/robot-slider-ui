import time
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

    def load_urdf(self, urdf_file):
        try:
            tree = ET.parse(urdf_file)
            root = tree.getroot()
            
            for joint in root.findall('joint'):
                joint_name = joint.get('name')
                if not joint_name or joint.get('type') != 'revolute':
                    continue

                # Parse joint limits
                limit = joint.find('limit')
                if limit is not None:
                    try:
                        self.limits[joint_name] = {
                            'min': float(limit.get('lower', '-180')),  # Default if missing
                            'max': float(limit.get('upper', '180'))    # Default if missing
                        }
                    except (TypeError, ValueError) as e:
                        self.limits[joint_name] = {'min': -180.0, 'max': 180.0}  # Fallback

                # Parse initial position (custom extension to URDF)
                initial_pos = joint.find('initial_position')
                if initial_pos is not None:
                    try:
                        self.positions[joint_name] = float(initial_pos.text)
                    except (TypeError, ValueError, AttributeError) as e:
                        self.positions[joint_name] = 0.0  # Default to zero position
                
                # Ensure joint exists in both dictionaries
                if joint_name not in self.positions:
                    self.positions[joint_name] = 0.0
                if joint_name not in self.limits:
                    self.limits[joint_name] = {'min': -180.0, 'max': 180.0}

        except ET.ParseError as e:
            raise ValueError(f"Invalid URDF file: {e}")
        except Exception as e:
            raise

    @staticmethod
    def quintic_interpolation(t, duration):
        """Quintic interpolation function for smooth motion"""
        t = max(0, min(t, duration))  # Clamp t between 0 and duration
        normalized_t = t / duration
        return 6 * normalized_t**5 - 15 * normalized_t**4 + 10 * normalized_t**3

    def calculate_interpolated_positions(self, target_pos, start_pos, elapsed, duration):
        """Calculate new positions based on interpolation"""
        interp_factor = self.quintic_interpolation(elapsed, duration)
        new_positions = {}
        
        for joint in target_pos:
            new_positions[joint] = round(
                start_pos[joint] + (target_pos[joint] - start_pos[joint]) * interp_factor,
                2
            )
        
        return new_positions

    def execute_movement(self, target_pos, duration, callback=None):
        """
        Execute movement and optionally call callback with new positions
        Args:
            target_pos: Dictionary of target positions
            duration: Movement duration in seconds
            callback: Optional callback function that receives new positions
        """
        try:
            start_time = time.time()
            start_pos = self.positions.copy()
            
            while True:
                elapsed = time.time() - start_time
                progress = min(elapsed / duration, 1.0)
                

                with self.lock:
                    new_positions = self.calculate_interpolated_positions(
                        target_pos, start_pos, elapsed, duration
                    )
                    self.positions.update(new_positions)
                    
                    if callback:
                        callback(new_positions)
                
                if progress >= 1.0:
                    break
                    
                time.sleep(0.02)
                
        except Exception as e:
            if callback:
                callback(None, e)
