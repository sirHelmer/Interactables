import flet as ft
import math
import colorsys
import platform
import os

def get_sys_fonts():
    # Retorna uma lista de fontes clássicas e seguras garantidas de rodar ou terem fallbacks nativos (Estilo Libre Office / Word)
    return sorted([
        "Arial", "Calibri", "Cambria", "Comic Sans MS", "Courier New", 
        "Georgia", "Helvetica", "Impact", "Lucida Console", "Roboto", 
        "Segoe UI", "Tahoma", "Times New Roman", "Trebuchet MS", "Verdana"
    ])

SYS_FONTS = get_sys_fonts()
COMMON_COLORS = [
    "#000000", "#FFFFFF", "#FF0000", "#00FF00", "#0000FF",
    "#FFFF00", "#FF00FF", "#00FFFF", "#808080", "#8B4513"
]

RECENT_COLORS = ["#FF0000", "#00FF00", "#0000FF", "#FFFFFF", "#000000"]

class ColorPickerModal(ft.AlertDialog):
    def __init__(self, initial_color="#000000", on_color_selected=None):
        super().__init__()
        self.on_color_selected = on_color_selected
        self.title = ft.Text("Seletor de Cor", size=14, weight=ft.FontWeight.BOLD)
        
        self.current_color = initial_color
        self.h = 0.0
        self.s = 0.0
        self.v = 1.0
        
        # Parse initial hex
        try:
            h = initial_color.lstrip('#')
            r, g, b = tuple(int(h[i:i+2], 16)/255.0 for i in (0, 2, 4))
            self.h, self.s, self.v = colorsys.rgb_to_hsv(r, g, b)
        except: pass

        self.wheel_size = 200
        self.center = self.wheel_size / 2
        
        self.cur_x = self.center
        self.cur_y = self.center
        self.cur_val_x = self.v * 200

        self.hue_indicator = ft.Container(
            width=12, height=12,
            border_radius=6,
            border=ft.Border(
                top=ft.BorderSide(2, ft.Colors.BLACK),
                right=ft.BorderSide(2, ft.Colors.BLACK),
                bottom=ft.BorderSide(2, ft.Colors.BLACK),
                left=ft.BorderSide(2, ft.Colors.BLACK)
            ),
            bgcolor=ft.Colors.TRANSPARENT,
            left=self.center - 6,
            top=self.center - 6
        )

        # Sweep gradient (Arco-íris)
        colors = [
            ft.Colors.RED,
            ft.Colors.YELLOW,
            ft.Colors.GREEN,
            ft.Colors.CYAN,
            ft.Colors.BLUE,
            ft.Colors.PURPLE,
            ft.Colors.RED
        ]
        
        self.wheel = ft.GestureDetector(
            on_pan_update=self._handle_wheel_pan,
            on_tap_down=self._handle_wheel_tap,
            content=ft.Container(
                width=self.wheel_size, height=self.wheel_size,
                border_radius=self.wheel_size / 2,
                gradient=ft.SweepGradient(colors=colors),
                content=ft.Container(
                    gradient=ft.RadialGradient(
                        colors=[ft.Colors.WHITE, ft.Colors.TRANSPARENT],
                        stops=[0.0, 1.0]
                    ),
                    content=ft.Stack([self.hue_indicator], width=self.wheel_size, height=self.wheel_size)
                )
            )
        )

        self.val_slider_width = 200
        self.val_indicator = ft.Container(
            width=6, height=20,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.BLACK),
                right=ft.BorderSide(1, ft.Colors.BLACK),
                bottom=ft.BorderSide(1, ft.Colors.BLACK),
                left=ft.BorderSide(1, ft.Colors.BLACK)
            ),
            left=self.val_slider_width - 3, top=0
        )
        
        self.val_bg = ft.Container(
            width=self.val_slider_width, height=20,
            border_radius=4,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.CENTER_LEFT,
                end=ft.Alignment.CENTER_RIGHT,
                colors=[ft.Colors.BLACK, ft.Colors.RED]
            ),
            content=ft.Stack([self.val_indicator])
        )

        self.val_slider = ft.GestureDetector(
            on_pan_update=self._handle_val_pan,
            on_tap_down=self._handle_val_tap,
            content=self.val_bg
        )

        self.recent_grid = ft.Row(wrap=True, width=200, spacing=5, run_spacing=5)
        self.update_recent_colors()

        self.preview = ft.Container(width=40, height=40, bgcolor=self.current_color, border_radius=4)
        
        self.content = ft.Column([
            self.wheel,
            ft.Text("Brilho", size=11),
            self.val_slider,
            ft.Row([
                self.preview,
                ft.Text(self.current_color, size=13, weight=ft.FontWeight.BOLD)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, width=200),
            ft.Divider(),
            ft.Text("Cores Recentes", size=11),
            self.recent_grid,
        ], width=200, height=400, spacing=10)

        self.actions = [
            ft.TextButton("Cancelar", on_click=self.cancel),
            ft.TextButton("Aplicar", on_click=self.apply)
        ]
        
        self._update_ui_from_hsv()

    def _rgb_to_hex(self, r, g, b):
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}".upper()

    def _update_ui_from_hsv(self):
        angle = self.h * 2 * math.pi
        radius = self.s * (self.wheel_size / 2)
        hx = self.center + math.cos(angle) * radius
        hy = self.center + math.sin(angle) * radius
        self.hue_indicator.left = max(0, min(self.wheel_size, hx)) - 6
        self.hue_indicator.top = max(0, min(self.wheel_size, hy)) - 6

        self.val_indicator.left = max(0, min(self.val_slider_width, (self.v * self.val_slider_width) - 3))

        r, g, b = colorsys.hsv_to_rgb(self.h, self.s, 1.0)
        pure_color = self._rgb_to_hex(r, g, b)
        self.val_bg.gradient.colors = [ft.Colors.BLACK, pure_color]

        r, g, b = colorsys.hsv_to_rgb(self.h, self.s, self.v)
        self.current_color = self._rgb_to_hex(r, g, b)
        self.preview.bgcolor = self.current_color
        
        if len(self.content.controls) > 3:
            row = self.content.controls[3]
            row.controls[1].value = self.current_color
            
        try:
            self.update()
        except: pass

    def _update_hsv_from_xy(self, x, y):
        dx = x - self.center
        dy = y - self.center
        
        angle = math.atan2(dy, dx)
        if angle < 0: angle += 2 * math.pi
        self.h = angle / (2 * math.pi)
        
        dist = math.hypot(dx, dy)
        self.s = min(1.0, dist / (self.wheel_size / 2))
        self._update_ui_from_hsv()

    def _handle_wheel_tap(self, e):
        if hasattr(e, 'local_x'):
            self.cur_x, self.cur_y = e.local_x, e.local_y
        elif hasattr(e, 'local_position'):
            self.cur_x, self.cur_y = e.local_position.x, e.local_position.y
        self._update_hsv_from_xy(self.cur_x, self.cur_y)

    def _handle_wheel_pan(self, e):
        if hasattr(e, 'local_delta'):
            dx = e.local_delta.x if hasattr(e.local_delta, 'x') else 0
            dy = e.local_delta.y if hasattr(e.local_delta, 'y') else 0
            self.cur_x += dx
            self.cur_y += dy
        elif hasattr(e, 'delta_x'):
            self.cur_x += e.delta_x
            self.cur_y += e.delta_y
        self._update_hsv_from_xy(self.cur_x, self.cur_y)

    def _update_v_from_x(self, x):
        x = max(0, min(self.val_slider_width, x))
        self.v = x / self.val_slider_width
        self._update_ui_from_hsv()

    def _handle_val_tap(self, e):
        if hasattr(e, 'local_x'):
            self.cur_val_x = e.local_x
        elif hasattr(e, 'local_position'):
            self.cur_val_x = e.local_position.x
        self._update_v_from_x(self.cur_val_x)

    def _handle_val_pan(self, e):
        if hasattr(e, 'local_delta'):
            dx = e.local_delta.x if hasattr(e.local_delta, 'x') else 0
            self.cur_val_x += dx
        elif hasattr(e, 'delta_x'):
            self.cur_val_x += e.delta_x
        self._update_v_from_x(self.cur_val_x)

    def update_recent_colors(self):
        self.recent_grid.controls.clear()
        for c in RECENT_COLORS:
            btn = ft.GestureDetector(
                on_tap=lambda e, col=c: self._load_hex(col),
                content=ft.Container(
                    width=25, height=25, bgcolor=c, border_radius=4,
                    border=ft.Border(
                        top=ft.BorderSide(1, ft.Colors.BLACK_12),
                        right=ft.BorderSide(1, ft.Colors.BLACK_12),
                        bottom=ft.BorderSide(1, ft.Colors.BLACK_12),
                        left=ft.BorderSide(1, ft.Colors.BLACK_12)
                    )
                )
            )
            self.recent_grid.controls.append(btn)

    def _load_hex(self, hstr):
        try:
            h = hstr.lstrip('#')
            r, g, b = tuple(int(h[i:i+2], 16)/255.0 for i in (0, 2, 4))
            self.h, self.s, self.v = colorsys.rgb_to_hsv(r, g, b)
            self._update_ui_from_hsv()
        except: pass

    def cancel(self, e):
        self.open = False
        self.page.update()

    def apply(self, e):
        if self.current_color not in RECENT_COLORS:
            RECENT_COLORS.insert(0, self.current_color)
            if len(RECENT_COLORS) > 10:
                RECENT_COLORS.pop()
        
        self.open = False
        self.page.update()
        if self.on_color_selected:
            self.on_color_selected(self.current_color)

class PropertiesPanel(ft.Container):
    def __init__(self, on_close=None):
        super().__init__()
        self.width = 300
        self.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
        self.padding = 5
        self.header = ft.Container(
            height=30,
            content=ft.Row([
                ft.Icon(ft.Icons.EDIT_NOTE, size=16, color=ft.Colors.GREY_700),
                ft.Text("PROPRIEDADES", weight=ft.FontWeight.W_600, size=11, color=ft.Colors.GREY_700),
                ft.Container(expand=True),
                ft.IconButton(icon=ft.Icons.CLOSE, icon_size=18, width=30, height=30, style=ft.ButtonStyle(padding=0), on_click=lambda _: on_close() if on_close else None)
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )
        
        self.props_container = ft.Column(
            controls=[ft.Text("Selecione um elemento para editar.", size=12)],
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        self.content = ft.Column(
            controls=[
                self.props_container
            ],
            spacing=5,
            expand=True
        )
        
        self.current_instance_id = None
        self.current_item_data = None
        self.current_obj_data = None
        self.pm = None
        self.on_change_cb = None

    def _create_field(self, label, value, on_change):
        return ft.Row([
            ft.Text(label, size=12, width=80),
            ft.TextField(value=str(value), text_size=12, height=30, content_padding=5, expand=True, on_change=on_change)
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _create_toggle(self, label, value, on_change):
        return ft.Row([
            ft.Text(label, size=12, width=80),
            ft.Switch(value=bool(value), on_change=on_change)
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)


    def clear(self):
        self.header.content.controls[1].value = "PROPRIEDADES"
        self.props_container.controls = [ft.Text("Selecione um elemento para editar.", size=12)]
        if self.page: self.update()

    def load_item(self, instance_id, item_data, obj_data, pm, on_change_cb):
        self.header.content.controls[1].value = "PROPRIEDADES"
        self.current_instance_id = instance_id
        self.current_item_data = item_data
        self.current_obj_data = obj_data
        self.pm = pm
        self.on_change_cb = on_change_cb
        
        if not instance_id or not item_data or not obj_data:
            self.clear()
            return
            
        self.build_property_grid()

    def build_property_grid(self):
        controls = []
        item = self.current_item_data
        obj = self.current_obj_data
        base_props = obj.get("base_properties", {})
        inst_props = item.setdefault("instance_properties", {})
        
        def update_val(key, val, is_item=False):
            if is_item:
                self.current_item_data[key] = val
            else:
                inst_props[key] = val
            if self.on_change_cb:
                self.on_change_cb()
                
        def get_prop(key, default_val=None):
            if key in inst_props: return inst_props[key]
            return base_props.get(key, default_val)

        # Generics
        controls.append(ft.Text("Geral", weight=ft.FontWeight.BOLD, size=13))
        controls.append(self._create_field("Nome", item.get("name", obj.get("name", "")), lambda e: update_val("name", e.control.value, True)))
        controls.append(self._create_toggle("Visível", item.get("visible", True), lambda e: update_val("visible", e.control.value, True)))
        
        controls.append(ft.Divider(height=1))
        controls.append(ft.Text("Transformação", weight=ft.FontWeight.BOLD, size=13))
        
        def safe_float_update(key, val_str, is_item=False):
            try:
                update_val(key, float(str(val_str).replace(',', '.')), is_item)
            except ValueError:
                pass

        def safe_rot_update(val_str):
            try:
                update_val("rotation", math.radians(float(str(val_str).replace(',', '.'))), True)
            except ValueError:
                pass

        controls.append(self._create_field("X", round(item.get("x", 0), 2), lambda e: safe_float_update("x", e.control.value, True)))
        controls.append(self._create_field("Y", round(item.get("y", 0), 2), lambda e: safe_float_update("y", e.control.value, True)))
        controls.append(self._create_field("Largura", round(item.get("w", 100), 2) if item.get("w") else "", lambda e: safe_float_update("w", e.control.value, True)))
        controls.append(self._create_field("Altura", round(item.get("h", 100), 2) if item.get("h") else "", lambda e: safe_float_update("h", e.control.value, True)))
        controls.append(self._create_field("Rotação", round(math.degrees(item.get("rotation", 0)), 2), lambda e: safe_rot_update(e.control.value)))
        
        def safe_z_update(val_str):
            try:
                val = int(val_str)
                update_val("z_index", val, True)
                # Re-sort scene_items by z_index
                if self.pm:
                    self.pm.scene_items.sort(key=lambda x: x.get("z_index", 0))
                    # O canvas render_canvas já é chamado via on_change_cb() no event handler
            except ValueError:
                pass
                
        controls.append(self._create_field("Z-Index", item.get("z_index", 0), lambda e: safe_z_update(e.control.value)))
        
        if obj.get("type") == "text":
            controls.append(ft.Divider(height=1))
            controls.append(ft.Text("Texto", weight=ft.FontWeight.BOLD, size=13))
            
            # Text multiline? Let's use a TextField with multiline
            txt_field = ft.TextField(value=get_prop("text", "Texto"), text_size=12, multiline=True, min_lines=2, max_lines=4, content_padding=5, on_change=lambda e: update_val("text", e.control.value))
            controls.append(ft.Column([ft.Text("Conteúdo", size=12), txt_field]))
            
            # Fonte
            font_opts = [ft.dropdown.Option(f) for f in SYS_FONTS]
            font_drop = ft.Dropdown(value=get_prop("font_family", "Arial"), options=font_opts, text_size=12, height=35, content_padding=5, expand=True, on_select=lambda e: update_val("font_family", e.control.value))
            controls.append(ft.Row([ft.Text("Fonte", size=12, width=80), font_drop], vertical_alignment=ft.CrossAxisAlignment.CENTER))
            
            # Tamanho com Botões
            def update_size(delta):
                val_str = size_field.value if size_field.value else str(get_prop("font_size", 24))
                curr = float(str(val_str).replace(',', '.'))
                new_size = max(1, curr + delta)
                size_field.value = str(new_size)
                self.update()
                update_val("font_size", new_size)
                
            size_field = ft.TextField(value=str(get_prop("font_size", 24)), text_size=12, height=30, content_padding=5, expand=True, on_change=lambda e: safe_float_update("font_size", e.control.value))
            controls.append(ft.Row([
                ft.Text("Tamanho", size=12, width=80),
                size_field,
                ft.IconButton(icon=ft.Icons.REMOVE, icon_size=14, width=30, height=30, on_click=lambda _: update_size(-1)),
                ft.IconButton(icon=ft.Icons.ADD, icon_size=14, width=30, height=30, on_click=lambda _: update_size(1))
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER))
            
            # Cor
            color_val = get_prop("color", "#000000")
            
            def on_color_picked(new_color):
                color_btn.content.bgcolor = new_color
                color_field.value = new_color
                self.update()
                update_val("color", new_color)
                
            def open_picker(e):
                picker = ColorPickerModal(initial_color=color_val, on_color_selected=on_color_picked)
                self.page.overlay.append(picker)
                picker.open = True
                self.page.update()
                
            color_btn = ft.GestureDetector(
                on_tap=open_picker,
                content=ft.Container(
                    width=35, height=35, bgcolor=color_val, border_radius=4,
                    border=ft.Border(
                        top=ft.BorderSide(1, ft.Colors.BLACK_12), right=ft.BorderSide(1, ft.Colors.BLACK_12),
                        bottom=ft.BorderSide(1, ft.Colors.BLACK_12), left=ft.BorderSide(1, ft.Colors.BLACK_12)
                    )
                )
            )
            color_field = ft.TextField(value=color_val, text_size=12, height=30, content_padding=5, expand=True, on_change=lambda e: update_val("color", e.control.value))
            
            controls.append(ft.Row([
                ft.Text("Cor", size=12, width=80),
                color_btn,
                color_field
            ], vertical_alignment=ft.CrossAxisAlignment.CENTER))
            controls.append(self._create_toggle("Negrito", get_prop("bold", False), lambda e: update_val("bold", e.control.value)))
            controls.append(self._create_toggle("Itálico", get_prop("italic", False), lambda e: update_val("italic", e.control.value)))

        # ----- Seção de Comportamentos -----
        controls.append(ft.Divider(height=1))
        controls.append(ft.Text("Comportamentos", weight=ft.FontWeight.BOLD, size=12))
        
        # Cópia profunda simplificada dos comportamentos para evitar vazar referência
        import copy
        if "behaviors" not in inst_props:
            inst_props["behaviors"] = copy.deepcopy(obj.get("behaviors", []))
            
        behaviors = inst_props.get("behaviors", [])
        
        if not behaviors:
            controls.append(ft.Text("Nenhum comportamento adicionado.", size=10, color=ft.Colors.GREY_500))
        else:
            for b_idx, b in enumerate(behaviors):
                def del_b(e, idx=b_idx):
                    inst_props["behaviors"].pop(idx)
                    self.on_change_cb()
                    self.load_item(self.current_instance_id, self.current_item_data, self.current_obj_data, self.pm, self.on_change_cb)
                
                b_type = b.get("type", "Unknown")
                b_name = b_type.replace("_", " ").title()
                controls.append(ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.Icons.EXTENSION, size=12, color=ft.Colors.BLUE),
                        ft.Text(b_name, size=11, expand=True, weight=ft.FontWeight.BOLD),
                        ft.IconButton(icon=ft.Icons.DELETE_OUTLINE, icon_size=14, width=24, height=24, icon_color=ft.Colors.RED_400, on_click=del_b)
                    ]),
                    padding=5, bgcolor=ft.Colors.WHITE, border_radius=4,
                    border=ft.Border(top=ft.BorderSide(1, ft.Colors.GREY_200), bottom=ft.BorderSide(1, ft.Colors.GREY_200), left=ft.BorderSide(1, ft.Colors.GREY_200), right=ft.BorderSide(1, ft.Colors.GREY_200))
                ))
                
                # Campos de configuração baseados no tipo
                b_config = b.get("config", {})
                def update_b_config(key, val, idx=b_idx):
                    inst_props["behaviors"][idx]["config"][key] = val
                    self.on_change_cb()
                    
                if b_type == "move_linear":
                    field_x = ft.TextField(value=str(b_config.get("speed_x", 10)), text_size=11, height=25, content_padding=3, expand=True, on_change=lambda e, k="speed_x", i=b_idx: safe_float_update_b(k, e.control.value, i))
                    field_y = ft.TextField(value=str(b_config.get("speed_y", 0)), text_size=11, height=25, content_padding=3, expand=True, on_change=lambda e, k="speed_y", i=b_idx: safe_float_update_b(k, e.control.value, i))
                    controls.append(ft.Row([ft.Text("Speed X:", size=11, width=50), field_x, ft.Text("Y:", size=11, width=20), field_y]))
                elif b_type == "gravity":
                    field_g = ft.TextField(value=str(b_config.get("gravity", 98)), text_size=11, height=25, content_padding=3, expand=True, on_change=lambda e, k="gravity", i=b_idx: safe_float_update_b(k, e.control.value, i))
                    field_b = ft.TextField(value=str(b_config.get("bounciness", 0.5)), text_size=11, height=25, content_padding=3, expand=True, on_change=lambda e, k="bounciness", i=b_idx: safe_float_update_b(k, e.control.value, i))
                    controls.append(ft.Row([ft.Text("Gravity:", size=11, width=50), field_g, ft.Text("Bounce:", size=11, width=40), field_b]))
                    
        def safe_float_update_b(key, val_str, idx):
            try:
                val = float(str(val_str).replace(',', '.'))
                inst_props["behaviors"][idx]["config"][key] = val
                self.on_change_cb()
            except ValueError:
                pass

        b_options = [
            ft.dropdown.Option("move_linear", "Mover (Linear)"),
            ft.dropdown.Option("gravity", "Gravidade"),
            ft.dropdown.Option("collision", "Colisão")
        ]
        b_dropdown = ft.Dropdown(options=b_options, text_size=12, height=35, content_padding=5, expand=True)
        
        def add_behavior(e):
            if not b_dropdown.value: return
            if "behaviors" not in inst_props: inst_props["behaviors"] = []
            
            new_b = {"type": b_dropdown.value, "config": {}}
            if b_dropdown.value == "move_linear": new_b["config"] = {"speed_x": 50.0, "speed_y": 0.0}
            if b_dropdown.value == "gravity": new_b["config"] = {"gravity": 98.0, "bounciness": 0.5}
            
            inst_props["behaviors"].append(new_b)
            self.on_change_cb()
            self.load_item(self.current_instance_id, self.current_item_data, self.current_obj_data, self.pm, self.on_change_cb)
            
        controls.append(ft.Row([
            b_dropdown,
            ft.IconButton(icon=ft.Icons.ADD_CIRCLE, icon_color=ft.Colors.BLUE, tooltip="Adicionar Comportamento", on_click=add_behavior)
        ]))

        self.props_container.controls = controls
        if self.page: self.update()

class Toolbar(ft.Container):
    def __init__(self, on_tool_change=None):
        super().__init__()
        self.on_tool_change = on_tool_change
        self.active_tool = "select"
        self.width = 60
        self.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
        self.padding = 5
        self.tools = [
            {"id": "pan", "icon": ft.Icons.PAN_TOOL, "tooltip": "Mover Cena"},
            {"id": "select", "icon": ft.Icons.HIGHLIGHT_ALT, "tooltip": "Selecionar"},
            {"id": "move", "icon": ft.Icons.OPEN_WITH, "tooltip": "Mover Objeto"},
            {"id": "rotate", "icon": ft.Icons.ROTATE_RIGHT, "tooltip": "Rotacionar"},
            {"id": "scale", "icon": ft.Icons.PHOTO_SIZE_SELECT_LARGE, "tooltip": "Escalonar"},
            {"id": "text", "icon": ft.Icons.TEXT_FIELDS, "tooltip": "Ferramenta de Texto"},
            {"id": "paint", "icon": ft.Icons.FORMAT_PAINT, "tooltip": "Balde de Tinta"},
            {"id": "rect", "icon": ft.Icons.CROP_SQUARE, "tooltip": "Retângulo"},
            {"id": "circle", "icon": ft.Icons.CIRCLE_OUTLINED, "tooltip": "Círculo"},
            {"id": "line", "icon": ft.Icons.SHOW_CHART, "tooltip": "Linha"},
            {"id": "triangle", "icon": ft.Icons.CHANGE_HISTORY, "tooltip": "Triângulo"},
            {"id": "star", "icon": ft.Icons.STAR_BORDER, "tooltip": "Estrela"},
        ]
        
        self.buttons = []
        for t in self.tools:
            btn = ft.IconButton(
                icon=t["icon"], 
                tooltip=t["tooltip"],
                data=t["id"],
                on_click=self._handle_tool_click,
                icon_color=ft.Colors.BLUE if t["id"] == self.active_tool else ft.Colors.GREY_800
            )
            self.buttons.append(btn)
            
        self.paint_color = "#336699"
        
        def on_color_picked(new_color):
            self.paint_color = new_color
            self.color_indicator.bgcolor = new_color
            self.update()
            
        def open_color_picker(e):
            picker = ColorPickerModal(initial_color=self.paint_color, on_color_selected=on_color_picked)
            self.page.overlay.append(picker)
            picker.open = True
            self.page.update()
            
        self.color_indicator = ft.Container(
            width=24, height=24, bgcolor=self.paint_color, border_radius=12,
            border=ft.Border(top=ft.BorderSide(2, ft.Colors.WHITE), right=ft.BorderSide(2, ft.Colors.WHITE), bottom=ft.BorderSide(2, ft.Colors.WHITE), left=ft.BorderSide(2, ft.Colors.WHITE)),
            on_click=open_color_picker,
            tooltip="Cor da Tinta/Formas"
        )
            
        self.content = ft.Column(
            controls=self.buttons + [ft.Divider(height=1), self.color_indicator],
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )

    def _handle_tool_click(self, e):
        self.active_tool = e.control.data
        for btn in self.buttons:
            btn.icon_color = ft.Colors.BLUE if btn.data == self.active_tool else ft.Colors.GREY_800
        self.update()
        if self.on_tool_change:
            self.on_tool_change(self.active_tool)
