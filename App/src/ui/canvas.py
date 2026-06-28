import flet as ft
import os
import uuid
import struct
import math

def get_image_size(file_path):
    try:
        with open(file_path, 'rb') as f:
            head = f.read(24)
            if head.startswith(b'\x89PNG\r\n\x1a\n'):
                return struct.unpack('>ii', head[16:24])
            elif head[:2] == b'\xff\xd8':
                f.seek(0)
                size = 2
                ftype = 0
                while not 0xc0 <= ftype <= 0xcf or ftype in (0xc4, 0xc8, 0xcc):
                    f.seek(size, 1)
                    byte = f.read(1)
                    while ord(byte) == 0xff:
                        byte = f.read(1)
                    ftype = ord(byte)
                    size = struct.unpack('>H', f.read(2))[0] - 2
                f.seek(1, 1)
                h, w = struct.unpack('>HH', f.read(4))
                return w, h
    except: pass
    return 100, 100

class CanvasArea(ft.Container):
    def __init__(self):
        super().__init__()
        self.expand = True
        self.bgcolor = ft.Colors.BLUE_GREY_100
        self.pm = None
        self.pm = None
        self.selected_item_ids = []
        self.active_tool = "select"
        self.zoom_level = 1.0
        self.on_selection_change = None
        self.get_paint_color = None
        
        self.canvas_stack = ft.Stack()
        
        self.paper = ft.Container(
            bgcolor=ft.Colors.WHITE,
            content=self.canvas_stack,
            shadow=ft.BoxShadow(spread_radius=1, blur_radius=5, color=ft.Colors.BLACK_26),
            scale=ft.Scale(scale=self.zoom_level, alignment=ft.Alignment(-1, -1)),
            left=0, top=0
        )
        
        self.scale_wrapper = ft.Container(
            content=ft.Stack([self.paper]),
            alignment=ft.Alignment(-1, -1)
        )
        
        self.bg_gesture = ft.GestureDetector(
            content=self.scale_wrapper,
            on_tap=self.handle_bg_tap,
            on_pan_start=self.handle_bg_pan_start,
            on_pan_update=self.handle_bg_pan,
            on_pan_end=self.handle_bg_pan_end
        )
        self.drag_target = ft.DragTarget(
            group="assets",
            on_accept=self.handle_drop,
            content=self.bg_gesture
        )
        self.workspace_margin = ft.Container(
            content=self.drag_target,
            padding=100
        )
        
        self.scroll_row = ft.Row(
            controls=[self.workspace_margin],
            scroll=ft.ScrollMode.AUTO,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
        self.scroll_col = ft.Column(
            controls=[self.scroll_row],
            scroll=ft.ScrollMode.AUTO,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True
        )
        
        self.zoom_controls = ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ft.Icons.ZOOM_OUT, icon_size=18, tooltip="Zoom Out (-10%)", on_click=lambda _: self.change_zoom(-0.1)),
                ft.TextButton(content=ft.Text("100%", size=12, weight=ft.FontWeight.BOLD), tooltip="Reset Zoom", on_click=lambda _: self.set_zoom(1.0)),
                ft.IconButton(icon=ft.Icons.ZOOM_IN, icon_size=18, tooltip="Zoom In (+10%)", on_click=lambda _: self.change_zoom(0.1)),
            ], spacing=0, alignment=ft.MainAxisAlignment.CENTER),
            bgcolor=ft.Colors.WHITE_70,
            border_radius=20,
            padding=ft.Padding(5, 0, 5, 0),
            right=20, bottom=20
        )
        
        self.content = ft.Stack([
            self.scroll_col,
            self.zoom_controls
        ], expand=True)

    def change_zoom(self, delta):
        new_zoom = max(0.1, min(self.zoom_level + delta, 5.0))
        self.set_zoom(new_zoom)

    def set_zoom(self, level):
        self.zoom_level = level
        self.paper.scale = ft.Scale(scale=self.zoom_level, alignment=ft.Alignment(-1, -1))
        
        if self.pm and self.pm.is_loaded:
            self.scale_wrapper.width = self.pm.canvas_width * self.zoom_level
            self.scale_wrapper.height = self.pm.canvas_height * self.zoom_level
            
        self.zoom_controls.content.controls[1].content.value = f"{int(self.zoom_level*100)}%"
        
        if self.page:
            self.zoom_controls.update()
            self.paper.update()
            if hasattr(self, 'scale_wrapper'):
                self.scale_wrapper.update()
            self.update()

    def zoom_fit(self):
        if not self.pm or not self.pm.is_loaded or not self.page:
            return
            
        win_w = self.page.window_width if hasattr(self.page, "window_width") and self.page.window_width else self.page.width
        win_h = self.page.window_height if hasattr(self.page, "window_height") and self.page.window_height else self.page.height
        
        if not win_w or not win_h:
            return
            
        scale_x = (win_w * 0.8) / self.pm.canvas_width
        scale_y = (win_h * 0.8) / self.pm.canvas_height
        
        fit_scale = min(scale_x, scale_y)
        self.set_zoom(fit_scale)

    def handle_bg_tap(self, e: ft.TapEvent):
        if self.active_tool == "text":
            if self.pm and self.pm.is_loaded:
                text_props = {
                    "text": "Novo Texto",
                    "font_family": "Arial",
                    "font_size": 24,
                    "color": "#000000",
                    "bold": False,
                    "italic": False
                }
                
                start_x = 0
                start_y = 0
                if hasattr(e, "local_x"):
                    start_x = e.local_x
                    start_y = e.local_y
                elif hasattr(e, "local_position"):
                    start_x = e.local_position.x
                    start_y = e.local_position.y
                
                start_x = start_x / self.zoom_level
                start_y = start_y / self.zoom_level
                
                object_id = self.pm.create_text_object(text_props)
                base_name = "Texto"
                if self.pm.objects.get(object_id):
                    base_name = self.pm.objects[object_id].get("name", "Texto")
                
                instance_name = self.pm.get_unique_instance_name(base_name)
                instance_id = str(uuid.uuid4())
                
                self.pm.scene_items.append({
                    "instance_id": instance_id,
                    "object_id": object_id,
                    "name": instance_name,
                    "x": start_x,
                    "y": start_y,
                    "w": 150, # Default text bounding box
                    "h": 50,
                    "rotation": 0.0,
                    "z_index": len(self.pm.scene_items)
                })
                
                self.selected_item_ids = [instance_id]
                self.pm.save_project()
                
                # Desativa a ferramenta de texto e volta pro select
                self.set_active_tool("select")
                if hasattr(self, "on_hierarchy_change") and self.on_hierarchy_change:
                    self.on_hierarchy_change()
                # Avisa a Toolbar (opcional) ou simplesmente chama render
                self.render_canvas()
                
                # Opcionalmente, aqui avisaríamos o layout para atualizar o ToolOptionsBar,
                # mas o layout_tool_change ou a seleção faz isso
                if hasattr(self.page, "layout_instance") and hasattr(self.page.layout_instance, "toolbar"):
                    # Hackzinho para sincronizar o botão da barra lateral, caso necessário
                    self.page.layout_instance.toolbar._handle_tool_click(type('Event', (), {'control': type('Control', (), {'data': 'select'})})())
        elif self.active_tool in ["rect", "circle", "line", "triangle", "star"]:
            if self.pm and self.pm.is_loaded:
                shape_props = {
                    "color": "#336699",
                    "border_color": "#000000",
                    "border_width": 2
                }
                
                start_x = 0
                start_y = 0
                if hasattr(e, "local_x"):
                    start_x = e.local_x
                    start_y = e.local_y
                elif hasattr(e, "local_position"):
                    start_x = e.local_position.x
                    start_y = e.local_position.y
                
                start_x = start_x / self.zoom_level
                start_y = start_y / self.zoom_level
                
                object_id = self.pm.create_shape_object(self.active_tool, shape_props)
                base_name = self.pm.objects[object_id].get("name", "Forma")
                
                instance_name = self.pm.get_unique_instance_name(base_name)
                instance_id = str(uuid.uuid4())
                
                self.pm.scene_items.append({
                    "instance_id": instance_id,
                    "object_id": object_id,
                    "name": instance_name,
                    "x": start_x,
                    "y": start_y,
                    "w": 100,
                    "h": 100,
                    "rotation": 0.0,
                    "z_index": len(self.pm.scene_items)
                })
                
                self.selected_item_ids = [instance_id]
                self.pm.save_project()
                
                self.set_active_tool("select")
                if hasattr(self, "on_hierarchy_change") and self.on_hierarchy_change:
                    self.on_hierarchy_change()
                self.render_canvas()
                
                if hasattr(self.page, "layout_instance") and hasattr(self.page.layout_instance, "toolbar"):
                    self.page.layout_instance.toolbar._handle_tool_click(type('Event', (), {'control': type('Control', (), {'data': 'select'})})())
        else:
            self.clear_selection(e)

    def update_selected_text_properties(self, props):
        changed = False
        if not self.pm or not self.pm.is_loaded: return
        
        for item in self.pm.scene_items:
            if item.get("instance_id") in self.selected_item_ids:
                obj_data = self.pm.objects.get(item.get("object_id"))
                if obj_data and obj_data.get("type") == "text":
                    obj_data["base_properties"].update(props)
                    changed = True
                    
        if changed:
            self.pm.save_project()
            self.render_canvas()

    def clear_selection(self, e):
        self.selected_item_ids = []
        self.render_canvas()

    def handle_bg_pan_start(self, e: ft.DragStartEvent):
        if self.active_tool == "select":
            # Usar coordenadas aproximadas se Flet não fornecer
            start_x = 0
            start_y = 0
            import json
            try:
                if hasattr(e, "local_position") and e.local_position:
                    start_x = e.local_position.x
                    start_y = e.local_position.y
                elif hasattr(e, "local_x"): start_x = e.local_x; start_y = e.local_y
                elif hasattr(e, "data") and isinstance(e.data, str):
                    ld = json.loads(e.data)
                    start_x = float(ld.get("lx", 0))
                    start_y = float(ld.get("ly", 0))
            except: pass
            
            start_x = start_x / self.zoom_level
            start_y = start_y / self.zoom_level
            
            self.marquee_start = (start_x, start_y)
            self.marquee_current = [start_x, start_y]
            self.marquee_rect = ft.Container(
                left=start_x, top=start_y, width=0, height=0,
                border=ft.Border(
                    top=ft.BorderSide(1, ft.Colors.BLUE),
                    right=ft.BorderSide(1, ft.Colors.BLUE),
                    bottom=ft.BorderSide(1, ft.Colors.BLUE),
                    left=ft.BorderSide(1, ft.Colors.BLUE)
                ),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.BLUE)
            )
            self.canvas_stack.controls.append(self.marquee_rect)
            self.canvas_stack.update()

    def handle_bg_pan(self, e: ft.DragUpdateEvent):
        try:
            dx, dy = 0.0, 0.0
            if hasattr(e, 'local_delta') and e.local_delta is not None:
                if isinstance(e.local_delta, str):
                    import json
                    try:
                        ld = json.loads(e.local_delta)
                        dx = float(ld.get("x", 0.0))
                        dy = float(ld.get("y", 0.0))
                    except: pass
                elif hasattr(e.local_delta, 'x'):
                    dx = e.local_delta.x
                    dy = e.local_delta.y
            elif hasattr(e, 'delta_x'):
                dx = getattr(e, 'delta_x', 0.0)
                dy = getattr(e, 'delta_y', 0.0)
            
            if self.active_tool == "pan":
                if self.page:
                    self.page.run_task(self.scroll_row.scroll_to, delta=-dx, duration=0)
                    self.page.run_task(self.scroll_col.scroll_to, delta=-dy, duration=0)
            elif self.active_tool == "select" and hasattr(self, 'marquee_rect'):
                scaled_dx = dx / self.zoom_level
                scaled_dy = dy / self.zoom_level
                self.marquee_current[0] += scaled_dx
                self.marquee_current[1] += scaled_dy
                start_x, start_y = self.marquee_start
                curr_x, curr_y = self.marquee_current[0], self.marquee_current[1]
                
                self.marquee_rect.left = min(start_x, curr_x)
                self.marquee_rect.top = min(start_y, curr_y)
                self.marquee_rect.width = abs(curr_x - start_x)
                self.marquee_rect.height = abs(curr_y - start_y)
                self.marquee_rect.update()
        except Exception as ex:
            print("ERROR IN BG PAN:", ex)

    def handle_bg_pan_end(self, e: ft.DragEndEvent):
        if self.active_tool == "select" and hasattr(self, 'marquee_rect'):
            try: self.canvas_stack.controls.remove(self.marquee_rect)
            except: pass
            
            # Checar colisão
            m_left = self.marquee_rect.left
            m_top = self.marquee_rect.top
            m_right = m_left + self.marquee_rect.width
            m_bottom = m_top + self.marquee_rect.height
            
            new_selection = []
            if self.pm:
                for item in self.pm.scene_items:
                    # assumindo width padrão de 100x100 se não especificado
                    w = item.get("w") or 100
                    h = item.get("h") or 100
                    x = item.get("x", 0)
                    y = item.get("y", 0)
                    
                    # AABB collision
                    if x < m_right and (x + w) > m_left and y < m_bottom and (y + h) > m_top:
                        new_selection.append(item.get("instance_id"))
            
            if new_selection:
                self.selected_item_ids = new_selection
            
            del self.marquee_rect
            self.render_canvas()

    def set_active_tool(self, tool_name):
        self.active_tool = tool_name
        self.render_canvas()

    def set_project_manager(self, pm):
        self.pm = pm
        if self.pm and self.pm.is_loaded:
            self.paper.width = self.pm.canvas_width
            self.paper.height = self.pm.canvas_height
        self.render_canvas()

    def handle_drop(self, e: ft.DragTargetEvent):
        if not self.pm or not self.pm.is_loaded:
            return
            
        src_path = e.src.data if getattr(e, 'src', None) else None
        if not src_path and hasattr(e, 'page'):
            try:
                src_path = e.page.get_control(e.src_id).data
            except:
                pass
                
        if not src_path or not os.path.isfile(src_path):
            return
            
        ext = src_path.split('.')[-1].lower()
        if ext not in ['png', 'jpg', 'jpeg', 'webp', 'svg', 'gif']:
            return # Apenas imagens por enquanto
            
        # Calcula o caminho relativo para portabilidade
        rel_path = os.path.relpath(src_path, self.pm.path)
        
        pos_x = 0
        pos_y = 0
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            if hasattr(e, 'local_position') and e.local_position:
                pos_x = int(e.local_position.x / self.zoom_level)
                pos_y = int(e.local_position.y / self.zoom_level)
            elif hasattr(e, 'x'): pos_x = int(float(e.x) / self.zoom_level)
            
            if not pos_y:
                if hasattr(e, 'y'): pos_y = int(float(e.y) / self.zoom_level)

        object_id = self.pm.get_or_create_object_for_asset(rel_path, "image")
        
        orig_w, orig_h = get_image_size(src_path)
        base_name = "Imagem"
        if self.pm.objects.get(object_id):
            base_name = self.pm.objects[object_id].get("name", "Imagem")
            
        instance_name = self.pm.get_unique_instance_name(base_name)

        new_instance = {
            "instance_id": str(uuid.uuid4()),
            "object_id": object_id,
            "name": instance_name,
            "canvas_id": "default",
            "x": pos_x,
            "y": pos_y,
            "z_index": len(self.pm.scene_items),
            "rotation": 0,
            "opacity": 1.0,
            "w": orig_w,
            "h": orig_h
        }
        self.pm.scene_items.append(new_instance)
        self.selected_item_ids = [new_instance["instance_id"]]
        
        # Salva o projeto imediatamente para persistir o novo Objeto e Instância em disco
        self.pm.save_project()
        
        if hasattr(self, "on_hierarchy_change") and self.on_hierarchy_change:
            self.on_hierarchy_change()
            
        self.render_canvas()

    def handle_pan_start(self, e: ft.DragStartEvent, item_id: str):
        if self.active_tool in ["select", "move", "scale", "rotate"]:
            if item_id not in self.selected_item_ids:
                self.selected_item_ids = [item_id]
                self.notify_selection()
                self.render_canvas()

    def handle_item_tap(self, e, item_id: str):
        if self.active_tool in ["select", "move", "scale", "rotate"]:
            self.selected_item_ids = [item_id]
            self.notify_selection()
            self.render_canvas()
        elif self.active_tool == "paint":
            # Paint bucket implementation
            self.selected_item_ids = [item_id]
            
            latest_color = "#FF0000"
            try:
                if self.get_paint_color:
                    latest_color = str(self.get_paint_color())
            except Exception:
                pass
            
            item = next((x for x in self.pm.scene_items if x.get("instance_id") == item_id), None)
            if item:
                obj_data = self.pm.objects.get(item["object_id"])
                if obj_data:
                    if "instance_properties" not in item:
                        item["instance_properties"] = {}
                        
                    if obj_data["type"] == "text":
                        item["instance_properties"]["color"] = latest_color
                    elif obj_data["type"] == "shape":
                        item["instance_properties"]["color"] = latest_color
                    elif obj_data["type"] == "image":
                        item["instance_properties"]["blend_color"] = latest_color
                        
                    self.pm.save_project()
                    
                    self.notify_selection()
                    
                    if hasattr(self, "on_hierarchy_change") and self.on_hierarchy_change:
                        self.on_hierarchy_change()
                    
                    self.render_canvas()
                    
        elif self.active_tool == "delete":
            self.pm.scene_items = [i for i in self.pm.scene_items if i.get("instance_id") != item_id]
            self.selected_item_ids = [s for s in self.selected_item_ids if s != item_id]
            self.pm.save_project()
            self.notify_selection()
            self.render_canvas()

    def handle_pan_update(self, e: ft.DragUpdateEvent, item_id: str, axis: str = "xy"):
        with open("pan_debug.log", "a") as f:
            f.write(f"PAN UPDATE CALLED! item_id: {item_id}\n")
            f.write(f"Event dir: {dir(e)}\n")
            if hasattr(e, 'local_x'): f.write(f"local_x: {e.local_x}\n")
            if hasattr(e, 'delta_x'): f.write(f"delta_x: {e.delta_x}\n")
            if hasattr(e, 'local_delta'): f.write(f"local_delta: {e.local_delta}\n")
            f.write(f"Event data: {getattr(e, 'data', 'None')}\n")
        try:
            # Determinar os deltas de forma segura
            dx, dy = 0.0, 0.0
            import json
            if hasattr(e, 'local_delta') and e.local_delta is not None:
                if isinstance(e.local_delta, str):
                    try:
                        ld = json.loads(e.local_delta)
                        dx = float(ld.get("x", 0.0))
                        dy = float(ld.get("y", 0.0))
                    except: pass
                elif hasattr(e.local_delta, 'x'):
                    dx = e.local_delta.x
                    dy = e.local_delta.y
            elif hasattr(e, 'delta_x'):
                dx = getattr(e, 'delta_x', 0.0)
                dy = getattr(e, 'delta_y', 0.0)
            
            if dx == 0 and dy == 0:
                print("Deltas are 0!")
                
            # Pega a rotação do item sendo manipulado para converter deltas locais em globais
            dragged_item_rot = 0
            if self.pm:
                for it in self.pm.scene_items:
                    if it.get("instance_id") == item_id:
                        dragged_item_rot = it.get("rotation", 0)
                        break

            # Atualiza todos os itens selecionados
            for item in self.pm.scene_items:
                iid = item.get("instance_id")
                if iid in self.selected_item_ids or iid == item_id:
                    if self.active_tool == "move":
                        # converte delta local do gesto para movimento global no canvas
                        g_dx = dx * math.cos(dragged_item_rot) - dy * math.sin(dragged_item_rot)
                        g_dy = dx * math.sin(dragged_item_rot) + dy * math.cos(dragged_item_rot)
                        item["x"] += g_dx
                        item["y"] += g_dy
                    elif self.active_tool == "rotate":
                        current_rot = item.get("rotation", 0)
                        item["rotation"] = current_rot + (dx * 0.02)
                    elif self.active_tool == "scale":
                        obj_data = self.pm.objects.get(item["object_id"], {})
                        base_props = obj_data.get("base_properties", {})
                        inst_props = item.get("instance_properties", {})
                        
                        def get_p(k, d=None):
                            if k in inst_props: return inst_props[k]
                            return base_props.get(k, d)
                            
                        w = get_p("w", 100)
                        h = get_p("h", 100)
                        x = item.get("x", 0)
                        y = item.get("y", 0)
                        
                        rot = item.get("rotation", 0)
                        
                        if axis == "xy":
                            aspect = h / w if w != 0 else 1
                            new_w = max(10, w + dx)
                            new_h = new_w * aspect
                            dw = new_w - w
                            dh = new_h - h
                            item["w"] = new_w
                            item["h"] = new_h
                            item["x"] = x - dw / 2
                            item["y"] = y - dh / 2
                        elif axis == "right":
                            new_w = max(10, w + dx)
                            dw = new_w - w
                            item["w"] = new_w
                            item["x"] = x + (dw / 2) * (math.cos(rot) - 1)
                            item["y"] = y + (dw / 2) * math.sin(rot)
                        elif axis == "bottom":
                            new_h = max(10, h + dy)
                            dh = new_h - h
                            item["h"] = new_h
                            item["x"] = x - (dh / 2) * math.sin(rot)
                            item["y"] = y + (dh / 2) * (math.cos(rot) - 1)
                        elif axis == "left":
                            new_w = max(10, w - dx)
                            dw = new_w - w
                            item["w"] = new_w
                            item["x"] = x - (dw / 2) * (1 + math.cos(rot))
                            item["y"] = y - (dw / 2) * math.sin(rot)
                        elif axis == "top":
                            new_h = max(10, h - dy)
                            dh = new_h - h
                            item["h"] = new_h
                            item["x"] = x + (dh / 2) * math.sin(rot)
                            item["y"] = y - (dh / 2) * (1 + math.cos(rot))
                    
            # Atualiza apenas os controles específicos sem re-renderizar todo o canvas (o que cancela o drag)
            for ctrl in self.canvas_stack.controls:
                c_data = getattr(ctrl, "data", None)
                if c_data in self.selected_item_ids or c_data == item_id:
                    # Encontra o item correspondente para atualizar
                    for item in self.pm.scene_items:
                        if item.get("instance_id") == c_data:
                            ctrl.left = item["x"]
                            ctrl.top = item["y"]
                            ctrl.rotate = ft.Rotate(angle=item.get("rotation", 0.0))
                            
                            # O controle principal do stack (gd) precisa ter w e h atualizados
                            # O Stack em si não tem w/h, mas precisamos atualizar o width/height da imagem dentro
                            # Vamos dar update no control, o render_canvas é o lugar oficial.
                            # Mas pra não piscar, vamos atualizar o width/height da Imagem aqui.
                            if hasattr(ctrl, 'content') and hasattr(ctrl.content, 'controls'):
                                gd_ctrl = ctrl.content.controls[0]
                                if hasattr(gd_ctrl, 'content') and hasattr(gd_ctrl.content, 'content'):
                                    img_ctrl = gd_ctrl.content.content
                                    if item.get("w") is not None:
                                        img_ctrl.width = item["w"]
                                    if item.get("h") is not None:
                                        img_ctrl.height = item["h"]
                                    img_ctrl.update()
                            ctrl.update()
                            break
            self.canvas_stack.update()
            self.notify_selection()
        except Exception as ex:
            import traceback
            with open("pan_debug.log", "a") as f:
                f.write(f"ERROR: {ex}\n{traceback.format_exc()}\n")
            print("ERROR IN PAN UPDATE:", ex)

    def handle_pan_end(self, e: ft.DragEndEvent, item_id: str):
        if self.pm:
            self.pm.save_project()
        self.notify_selection()
        self.render_canvas()

    def render_canvas(self):
        self.canvas_stack.controls.clear()
        
        if not self.pm or not self.pm.is_loaded:
            # Não renderiza nada se não tiver projeto
            self.update()
            return

        self.paper.width = self.pm.canvas_width
        self.paper.height = self.pm.canvas_height
        self.scale_wrapper.width = self.pm.canvas_width * self.zoom_level
        self.scale_wrapper.height = self.pm.canvas_height * self.zoom_level

        for item in self.pm.scene_items:
            instance_id = item.get("instance_id")
            object_id = item.get("object_id")
            obj_data = self.pm.objects.get(object_id)
            
            if not obj_data: continue
            
            is_selected = (instance_id in self.selected_item_ids)
            is_visible = item.get("visible", True)
            
            base_props = obj_data.get("base_properties", {})
            inst_props = item.get("instance_properties", {})
            def get_prop(k, d=None):
                if k in inst_props: return inst_props[k]
                return base_props.get(k, d)
            
            if obj_data.get("type") == "image":
                abs_path = os.path.join(self.pm.path, obj_data.get("asset_ref"))
                blend_color = get_prop("blend_color", None)
                
                img_control = ft.Image(src=abs_path, fit=ft.BoxFit.FILL)
                if blend_color:
                    img_control.color = blend_color
                    img_control.color_blend_mode = ft.BlendMode.SRC_A_TOP
                
                if item.get("w"): img_control.width = item.get("w")
                if item.get("h"): img_control.height = item.get("h")
            elif obj_data.get("type") == "text":
                content_control = ft.Text(
                    value=get_prop("text", "Texto"),
                    font_family=get_prop("font_family", "Arial"),
                    size=get_prop("font_size", 24),
                    color=get_prop("color", "#000000"),
                    weight=ft.FontWeight.BOLD if get_prop("bold") else ft.FontWeight.NORMAL,
                    italic=get_prop("italic", False)
                )
                img_control = ft.Container(content=content_control)
                if item.get("w"): img_control.width = item.get("w")
                if item.get("h"): img_control.height = item.get("h")
            elif obj_data.get("type") == "shape":
                shape_type = obj_data.get("shape_type", "rect")
                color = get_prop("color", "#336699")
                w, h = float(item.get("w", 100)), float(item.get("h", 100))
                
                import flet.canvas as cv
                import math
                
                if shape_type == "rect":
                    shape = cv.Canvas([
                        cv.Path([
                            cv.Path.MoveTo(0, 0),
                            cv.Path.LineTo(w, 0),
                            cv.Path.LineTo(w, h),
                            cv.Path.LineTo(0, h),
                            cv.Path.Close()
                        ], paint=ft.Paint(style=ft.PaintingStyle.FILL, color=color))
                    ])
                elif shape_type == "circle":
                    shape = cv.Canvas([
                        cv.Circle(x=w/2, y=h/2, radius=min(w, h)/2, paint=ft.Paint(style=ft.PaintingStyle.FILL, color=color))
                    ])
                elif shape_type == "line":
                    shape = cv.Canvas([
                        cv.Path([
                            cv.Path.MoveTo(0, 0),
                            cv.Path.LineTo(w, h)
                        ], paint=ft.Paint(style=ft.PaintingStyle.STROKE, color=color, stroke_width=get_prop("border_width", 4)))
                    ])
                elif shape_type == "triangle":
                    shape = cv.Canvas([
                        cv.Path([
                            cv.Path.MoveTo(w/2, 0),
                            cv.Path.LineTo(w, h),
                            cv.Path.LineTo(0, h),
                            cv.Path.Close()
                        ], paint=ft.Paint(style=ft.PaintingStyle.FILL, color=color))
                    ])
                elif shape_type == "star":
                    cx, cy = w/2, h/2
                    r_out, r_in = min(w, h)/2, min(w, h)/4
                    path_elements = []
                    for i in range(10):
                        angle = i * math.pi / 5 - math.pi / 2
                        r = r_out if i % 2 == 0 else r_in
                        x = cx + math.cos(angle) * r
                        y = cy + math.sin(angle) * r
                        if i == 0:
                            path_elements.append(cv.Path.MoveTo(x, y))
                        else:
                            path_elements.append(cv.Path.LineTo(x, y))
                    path_elements.append(cv.Path.Close())
                    shape = cv.Canvas([
                        cv.Path(path_elements, paint=ft.Paint(style=ft.PaintingStyle.FILL, color=color))
                    ])
                else:
                    shape = ft.Container(bgcolor=color)
                
                img_control = ft.Container(content=shape, width=w, height=h)
            else:
                continue
                
            rot_val = item.get("rotation", 0.0)
            
            border = ft.Border(
                top=ft.BorderSide(2, ft.Colors.BLUE),
                right=ft.BorderSide(2, ft.Colors.BLUE),
                bottom=ft.BorderSide(2, ft.Colors.BLUE),
                left=ft.BorderSide(2, ft.Colors.BLUE)
            ) if is_selected else ft.Border(
                top=ft.BorderSide(1, ft.Colors.TRANSPARENT),
                right=ft.BorderSide(1, ft.Colors.TRANSPARENT),
                bottom=ft.BorderSide(1, ft.Colors.TRANSPARENT),
                left=ft.BorderSide(1, ft.Colors.TRANSPARENT)
            )
            
            op_val = 1.0 if is_visible else 0.3
            
            gd = ft.GestureDetector(
                mouse_cursor=ft.MouseCursor.CLICK,
                drag_interval=10,
                on_pan_start=lambda e, iid=instance_id: self.handle_pan_start(e, iid),
                on_pan_update=lambda e, iid=instance_id: self.handle_pan_update(e, iid),
                on_pan_end=lambda e, iid=instance_id: self.handle_pan_end(e, iid),
                on_tap=lambda e, iid=instance_id: self.handle_item_tap(e, iid),
                content=ft.Container(
                    content=img_control,
                    border=border,
                    on_hover=lambda e, sel=is_selected: self._handle_hover(e, sel)
                )
            )
            
            # Elemento base é o GestureDetector (a imagem com a borda)
            stack_controls = [gd]
            
            if is_selected:
                def make_grip():
                    return ft.Container(
                        width=10, height=10, bgcolor=ft.Colors.WHITE, 
                        border=ft.Border(
                            top=ft.BorderSide(1, ft.Colors.BLUE),
                            right=ft.BorderSide(1, ft.Colors.BLUE),
                            bottom=ft.BorderSide(1, ft.Colors.BLUE),
                            left=ft.BorderSide(1, ft.Colors.BLUE)
                        ), border_radius=5
                    )
                
                if self.active_tool == "scale":
                    # 4 center edge grips
                    stack_controls.extend([
                        # Top grip
                        ft.Container(top=-5, left=0, right=0, content=ft.Row([ft.GestureDetector(content=make_grip(), on_pan_update=lambda e, iid=instance_id: self.handle_pan_update(e, iid, "top"), on_pan_end=lambda e, iid=instance_id: self.handle_pan_end(e, iid))], alignment="center")),
                        # Bottom grip
                        ft.Container(bottom=-5, left=0, right=0, content=ft.Row([ft.GestureDetector(content=make_grip(), on_pan_update=lambda e, iid=instance_id: self.handle_pan_update(e, iid, "bottom"), on_pan_end=lambda e, iid=instance_id: self.handle_pan_end(e, iid))], alignment="center")),
                        # Left grip
                        ft.Container(left=-5, top=0, bottom=0, content=ft.Column([ft.GestureDetector(content=make_grip(), on_pan_update=lambda e, iid=instance_id: self.handle_pan_update(e, iid, "left"), on_pan_end=lambda e, iid=instance_id: self.handle_pan_end(e, iid))], alignment="center")),
                        # Right grip
                        ft.Container(right=-5, top=0, bottom=0, content=ft.Column([ft.GestureDetector(content=make_grip(), on_pan_update=lambda e, iid=instance_id: self.handle_pan_update(e, iid, "right"), on_pan_end=lambda e, iid=instance_id: self.handle_pan_end(e, iid))], alignment="center"))
                    ])
                elif self.active_tool == "rotate":
                    # 1 top rotation handle
                    rot_grip = ft.Container(
                        width=14, height=14, bgcolor=ft.Colors.WHITE, 
                        border=ft.Border(
                            top=ft.BorderSide(1, ft.Colors.BLUE),
                            right=ft.BorderSide(1, ft.Colors.BLUE),
                            bottom=ft.BorderSide(1, ft.Colors.BLUE),
                            left=ft.BorderSide(1, ft.Colors.BLUE)
                        ), border_radius=7,
                        content=ft.Icon(ft.Icons.REFRESH, size=10, color=ft.Colors.BLUE)
                    )
                    # Line connecting to the object
                    line = ft.Container(width=2, height=20, bgcolor=ft.Colors.BLUE)
                    
                    rot_handle = ft.Column([rot_grip, line], spacing=0, alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                    stack_controls.append(
                        ft.Container(top=-34, left=0, right=0, alignment=ft.Alignment(0, -1), content=ft.GestureDetector(content=rot_handle, on_pan_update=lambda e, iid=instance_id: self.handle_pan_update(e, iid), on_pan_end=lambda e, iid=instance_id: self.handle_pan_end(e, iid)))
                    )
            
            rot_val = item.get("rotation", 0.0)
            scale_val = item.get("scale", 1.0)
            
            is_visible = item.get("visible", True)
            
            # Se não está visível e não está selecionado, não renderiza no canvas
            if not is_visible and not is_selected:
                continue
                
            op_val = 1.0 if is_visible else 0.3
            
            self.canvas_stack.controls.append(
                ft.Container(
                    data=instance_id,
                    left=item["x"],
                    top=item["y"],
                    content=ft.Stack(stack_controls, clip_behavior=ft.ClipBehavior.NONE),
                    rotate=ft.Rotate(angle=rot_val),
                    opacity=op_val,
                    visible=True  # Sempre True aqui, pois os realmente invisíveis já sofreram `continue`
                )
            )
                
        self.update()
    def _handle_hover(self, e, is_selected):
        if is_selected: return
        # Borda azul fina no hover para feedback visual
        e.control.border = ft.Border(
            top=ft.BorderSide(1, ft.Colors.BLUE_400),
            right=ft.BorderSide(1, ft.Colors.BLUE_400),
            bottom=ft.BorderSide(1, ft.Colors.BLUE_400),
            left=ft.BorderSide(1, ft.Colors.BLUE_400)
        ) if e.data == "true" else ft.Border(
            top=ft.BorderSide(1, ft.Colors.TRANSPARENT),
            right=ft.BorderSide(1, ft.Colors.TRANSPARENT),
            bottom=ft.BorderSide(1, ft.Colors.TRANSPARENT),
            left=ft.BorderSide(1, ft.Colors.TRANSPARENT)
        )
        e.control.update()

    def notify_selection(self):
        if self.on_selection_change:
            if len(self.selected_item_ids) == 1:
                for item in self.pm.scene_items:
                    if item.get("instance_id") == self.selected_item_ids[0]:
                        obj_data = self.pm.objects.get(item.get("object_id"))
                        if obj_data:
                            self.on_selection_change(item.get("instance_id"), item, obj_data)
                            return
            self.on_selection_change(None, None, None)
