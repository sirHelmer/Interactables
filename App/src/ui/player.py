import flet as ft
import os
import threading
import time
import copy
from core.behaviors import BEHAVIOR_REGISTRY, EventBus

class PlayerView(ft.Container):
    def __init__(self, pm, on_close):
        super().__init__()
        self.pm = pm
        self.on_close = on_close
        
        self.expand = True
        self.bgcolor = ft.Colors.BLACK
        
        self.running = False
        self.thread = None
        self.event_bus = EventBus()
        self.active_behaviors = []
        self.scene_state = []
        
        self.player_canvas = ft.Stack(
            width=self.pm.canvas_width,
            height=self.pm.canvas_height,
            clip_behavior=ft.ClipBehavior.HARD_EDGE
        )
        
        self.screen_container = ft.Container(
            content=self.player_canvas,
            width=self.pm.canvas_width,
            height=self.pm.canvas_height,
            bgcolor=ft.Colors.WHITE,
            alignment=ft.Alignment(0, 0)
        )
        
        self.is_playing = False
        
        self.play_btn = ft.IconButton(
            icon=ft.Icons.PLAY_ARROW,
            icon_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN_700,
            tooltip="Continuar",
            on_click=self.play,
            visible=True
        )
        self.pause_btn = ft.IconButton(
            icon=ft.Icons.PAUSE,
            icon_color=ft.Colors.WHITE,
            bgcolor=ft.Colors.ORANGE_700,
            tooltip="Pausar",
            on_click=self.pause,
            visible=False
        )
        
        top_bar = ft.Row([
            self.play_btn,
            self.pause_btn,
            ft.IconButton(
                icon=ft.Icons.CLOSE,
                icon_color=ft.Colors.WHITE,
                bgcolor=ft.Colors.RED_700,
                tooltip="Sair da Apresentação",
                on_click=self.stop
            )
        ], alignment=ft.MainAxisAlignment.CENTER)
        
        self.content = ft.Stack(
            controls=[
                ft.Container(
                    content=self.screen_container,
                    expand=True,
                    alignment=ft.Alignment(0, 0)
                ),
                ft.Container(
                    content=top_bar,
                    top=20,
                    left=0,
                    right=0
                )
            ],
            expand=True
        )

    def did_mount(self):
        self.page.on_resize = self.handle_resize
        self.handle_resize(None)
        self.page.pubsub.subscribe(self._on_pubsub)
        self.start()
        self.page.run_thread(self.game_loop)
        
    def _on_pubsub(self, msg):
        if msg == "update_scene":
            self.update()

    def will_unmount(self):
        self.page.on_resize = None
        try:
            self.page.pubsub.unsubscribe()
        except:
            pass
        self.running = False

    def start(self):
        self.running = True
        
        # Copia o estado inicial para não modificar o projeto original
        self.scene_state = copy.deepcopy(self.pm.scene_items)
        
        self.active_behaviors = []
        for item in self.scene_state:
            obj_data = self.pm.objects.get(item["object_id"])
            if obj_data:
                inst_props = item.get("instance_properties", {})
                behaviors = inst_props.get("behaviors", obj_data.get("behaviors", []))
                
                with open("player_debug.log", "a") as f:
                    f.write(f"Item {item.get('instance_id')} behaviors: {behaviors}\n")
                    
                for b_def in behaviors:
                    b_class = BEHAVIOR_REGISTRY.get(b_def["type"])
                    if b_class:
                        # Pass pm=self directly as we will stub scene_items property
                        beh = b_class(item["instance_id"], self, self.event_bus, b_def.get("config") or {})
                        self.active_behaviors.append(beh)
                        beh.start()
                        
        self._build_scene()

    def stop(self, e=None):
        self.running = False
        if self.on_close:
            self.on_close()

    def play(self, e=None):
        self.is_playing = True
        self.play_btn.visible = False
        self.pause_btn.visible = True
        if self.page: self.update()

    def pause(self, e=None):
        self.is_playing = False
        self.play_btn.visible = True
        self.pause_btn.visible = False
        if self.page: self.update()

    def game_loop(self):
        last_time = time.time()
        with open("player_debug.log", "w") as f:
            f.write(f"Game loop started. Active behaviors: {len(self.active_behaviors)}\n")
        
        frame_count = 0
        while self.running:
            current_time = time.time()
            dt = current_time - last_time
            last_time = current_time
            
            if self.is_playing:
                try:
                    for beh in self.active_behaviors:
                        beh.update(dt)
                        
                    self._update_scene()
                    
                    frame_count += 1
                    if frame_count % 60 == 0:
                        with open("player_debug.log", "a") as f:
                            pos_str = ", ".join([f"{i.get('instance_id')[:4]}: {i.get('y'):.1f}" for i in self.scene_state])
                            f.write(f"Frame {frame_count}, dt={dt:.3f}, Pos: {pos_str}\n")
                except Exception as e:
                    with open("player_debug.log", "a") as f:
                        f.write(f"Error in game loop: {e}\n")
            
            # FPS cap
            elapsed = time.time() - current_time
            sleep_time = max(0, (1.0/60.0) - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    @property
    def scene_items(self):
        return self.scene_state

    # Para comportamentos como gravidade que precisam saber o limite
    @property
    def canvas_height(self):
        return self.pm.canvas_height
        
    @property
    def canvas_width(self):
        return self.pm.canvas_width

    def _build_scene(self):
        self.player_canvas.controls.clear()
        
        for item in self.scene_state:
            object_id = item.get("object_id")
            obj_data = self.pm.objects.get(object_id)
            if not obj_data: continue
            
            base_props = obj_data.get("base_properties", {})
            inst_props = item.get("instance_properties", {})
            
            def get_p(k, d=None):
                if k in inst_props: return inst_props[k]
                return base_props.get(k, d)
                
            w = float(get_p("w", 100))
            h = float(get_p("h", 100))
            
            if obj_data.get("type") == "image":
                abs_path = os.path.join(self.pm.path, obj_data.get("asset_ref"))
                img = ft.Image(src=abs_path, fit=ft.BoxFit.FILL, width=w, height=h)
                blend_color = get_p("blend_color")
                if blend_color:
                    img.color = blend_color
                    img.color_blend_mode = ft.BlendMode.SRC_A_TOP
                content = img
            elif obj_data.get("type") == "text":
                content = ft.Container(
                    width=w, height=h,
                    content=ft.Text(
                        value=get_p("text", "Texto"),
                        font_family=get_p("font_family", "Arial"),
                        size=get_p("font_size", 24),
                        color=get_p("color", "#000000"),
                        weight=ft.FontWeight.BOLD if get_p("bold") else ft.FontWeight.NORMAL,
                        italic=get_p("italic", False)
                    )
                )
            elif obj_data.get("type") == "shape":
                import flet.canvas as cv
                import math
                shape_type = obj_data.get("shape_type", "rect")
                color = get_p("color", "#336699")
                
                if shape_type == "rect":
                    shape = cv.Canvas([cv.Path([cv.Path.MoveTo(0, 0), cv.Path.LineTo(w, 0), cv.Path.LineTo(w, h), cv.Path.LineTo(0, h), cv.Path.Close()], paint=ft.Paint(style=ft.PaintingStyle.FILL, color=color))])
                elif shape_type == "circle":
                    shape = cv.Canvas([cv.Circle(x=w/2, y=h/2, radius=min(w, h)/2, paint=ft.Paint(style=ft.PaintingStyle.FILL, color=color))])
                elif shape_type == "line":
                    shape = cv.Canvas([cv.Path([cv.Path.MoveTo(0, 0), cv.Path.LineTo(w, h)], paint=ft.Paint(style=ft.PaintingStyle.STROKE, color=color, stroke_width=get_p("border_width", 4)))])
                elif shape_type == "triangle":
                    shape = cv.Canvas([cv.Path([cv.Path.MoveTo(w/2, 0), cv.Path.LineTo(w, h), cv.Path.LineTo(0, h), cv.Path.Close()], paint=ft.Paint(style=ft.PaintingStyle.FILL, color=color))])
                elif shape_type == "star":
                    cx, cy = w/2, h/2; r_out, r_in = min(w, h)/2, min(w, h)/4; path_elements = []
                    for i in range(10):
                        angle = i * math.pi / 5 - math.pi / 2
                        r = r_out if i % 2 == 0 else r_in
                        x = cx + math.cos(angle) * r
                        y = cy + math.sin(angle) * r
                        if i == 0: path_elements.append(cv.Path.MoveTo(x, y))
                        else: path_elements.append(cv.Path.LineTo(x, y))
                    path_elements.append(cv.Path.Close())
                    shape = cv.Canvas([cv.Path(path_elements, paint=ft.Paint(style=ft.PaintingStyle.FILL, color=color))])
                else:
                    shape = ft.Container(bgcolor=color)
                content = ft.Container(content=shape, width=w, height=h)
            else:
                continue
                
            ctrl = ft.Container(
                data=item["instance_id"],
                left=item.get("x", 0),
                top=item.get("y", 0),
                content=content,
                rotate=ft.Rotate(angle=item.get("rotation", 0.0)),
                visible=item.get("visible", True)
            )
            self.player_canvas.controls.append(ctrl)
            
        if self.page: self.update()

    def _update_scene(self):
        # Update just the positions/rotations to be fast
        for ctrl in self.player_canvas.controls:
            iid = ctrl.data
            item = next((i for i in self.scene_state if i["instance_id"] == iid), None)
            if item:
                ctrl.left = float(item.get("x", 0))
                ctrl.top = float(item.get("y", 0))
                ctrl.rotate.angle = float(item.get("rotation", 0.0))
                ctrl.visible = bool(item.get("visible", True))
                
        if self.page:
            try:
                self.page.pubsub.send_all("update_scene")
            except: pass

    def handle_resize(self, e):
        if not self.page: return
        win_w = self.page.window_width if hasattr(self.page, "window_width") and self.page.window_width else self.page.width
        win_h = self.page.window_height if hasattr(self.page, "window_height") and self.page.window_height else self.page.height
        
        if not win_w or not win_h: return
        
        scale_x = (win_w * 0.9) / self.pm.canvas_width
        scale_y = (win_h * 0.9) / self.pm.canvas_height
        
        fit_scale = min(scale_x, scale_y)
        self.screen_container.scale = ft.Scale(scale=fit_scale)
        self.update()
