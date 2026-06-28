import time
import math

class EventBus:
    def __init__(self):
        self.listeners = {}
        
    def subscribe(self, event_name, callback):
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)
        
    def publish(self, event_name, *args, **kwargs):
        if event_name in self.listeners:
            for cb in self.listeners[event_name]:
                cb(*args, **kwargs)

class Behavior:
    def __init__(self, target_instance_id, pm, event_bus, config):
        self.target_id = target_instance_id
        self.pm = pm
        self.event_bus = event_bus
        self.config = config
        
    def start(self):
        pass
        
    def update(self, dt):
        pass
        
    def end(self):
        pass

class MoveLinearBehavior(Behavior):
    def update(self, dt):
        speed_x = self.config.get("speed_x", 10.0)
        speed_y = self.config.get("speed_y", 0.0)
        
        item = next((i for i in self.pm.scene_items if i.get("instance_id") == self.target_id), None)
        if item:
            item["x"] += speed_x * dt
            item["y"] += speed_y * dt

class MoveToBehavior(Behavior):
    def update(self, dt):
        target_x = self.config.get("target_x", 0.0)
        target_y = self.config.get("target_y", 0.0)
        speed = self.config.get("speed", 50.0)
        
        item = next((i for i in self.pm.scene_items if i.get("instance_id") == self.target_id), None)
        if item:
            dx = target_x - item["x"]
            dy = target_y - item["y"]
            dist = math.hypot(dx, dy)
            if dist > 0.5:
                move_dist = min(speed * dt, dist)
                item["x"] += (dx / dist) * move_dist
                item["y"] += (dy / dist) * move_dist

class GravityBehavior(Behavior):
    def __init__(self, target_instance_id, pm, event_bus, config):
        super().__init__(target_instance_id, pm, event_bus, config)
        self.velocity_y = 0.0
        
    def update(self, dt):
        gravity = self.config.get("gravity", 9.8 * 10)
        self.velocity_y += gravity * dt
        
        item = next((i for i in self.pm.scene_items if i.get("instance_id") == self.target_id), None)
        if item:
            item["y"] += self.velocity_y * dt
            # Basic floor collision (just for testing logic, ideally use CollisionBehavior)
            floor_y = self.pm.canvas_height - item.get("h", 0)
            if item["y"] >= floor_y:
                item["y"] = floor_y
                self.velocity_y = -self.velocity_y * self.config.get("bounciness", 0.5)

class CollisionBehavior(Behavior):
    def update(self, dt):
        item = next((i for i in self.pm.scene_items if i.get("instance_id") == self.target_id), None)
        if not item: return
        
        rect1 = (item["x"], item["y"], item.get("w", 0), item.get("h", 0))
        
        # O(N) collision detection
        for other in self.pm.scene_items:
            if other.get("instance_id") == self.target_id: continue
            rect2 = (other["x"], other["y"], other.get("w", 0), other.get("h", 0))
            
            # AABB intersection
            if (rect1[0] < rect2[0] + rect2[2] and rect1[0] + rect1[2] > rect2[0] and
                rect1[1] < rect2[1] + rect2[3] and rect1[1] + rect1[3] > rect2[1]):
                
                self.event_bus.publish("collision", self.target_id, other.get("instance_id"))
                
                # Resposta basica (trava)
                block = self.config.get("block", False)
                if block:
                    # simple push out based on center dist
                    cx1 = rect1[0] + rect1[2]/2
                    cx2 = rect2[0] + rect2[2]/2
                    if cx1 < cx2:
                        item["x"] = rect2[0] - rect1[2]
                    else:
                        item["x"] = rect2[0] + rect2[2]

# Registry to spawn behaviors
BEHAVIOR_REGISTRY = {
    "move_linear": MoveLinearBehavior,
    "move_to": MoveToBehavior,
    "gravity": GravityBehavior,
    "collision": CollisionBehavior
}
