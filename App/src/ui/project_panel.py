import flet as ft
import os

class ProjectPanel(ft.Container):
    def __init__(self, on_close=None, on_action_attempt=None, on_context_menu=None, on_move_item=None):
        super().__init__()
        self.on_action_attempt = on_action_attempt
        self.on_context_menu = on_context_menu
        self.on_move_item = on_move_item
        
        self.selected_items = []  # Changed to list to preserve order for Shift+Click
        self.last_selected_index = -1
        self.current_path = ""
        self.is_root = True
        self.project_root = ""
        
        self.multi_select_switch = ft.Switch(label="Seleção Múltipla", value=False, scale=0.55)
        
        self.height = 200
        self.bgcolor = ft.Colors.BLUE_GREY_100
        self.padding = 5
        self.title_text = ft.Text("PROJETO / ASSETS", weight=ft.FontWeight.W_600, size=11, color=ft.Colors.GREY_700)
        
        # Left Tree View
        self.tree_view = ft.Column(scroll=ft.ScrollMode.AUTO, expand=1, spacing=2)
        
        # Right Assets View
        self.assets_view = ft.Row(
            wrap=True,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        # Wrapped assets view for empty-area right-clicks
        self.assets_gesture = ft.GestureDetector(
            content=ft.Container(content=self.assets_view, expand=True, bgcolor=ft.Colors.TRANSPARENT),
            on_secondary_tap_down=lambda e: self._handle_right_click(e, None, is_folder=False),
            expand=4
        )
        
        self.main_content = ft.Row([
            self.tree_view,
            ft.VerticalDivider(width=1, color=ft.Colors.GREY_400),
            self.assets_gesture
        ], expand=True)
        
        self.content = ft.Column(
            controls=[
                ft.Container(
                    height=30,
                    content=ft.Row([
                        ft.Icon(ft.Icons.FOLDER, size=16, color=ft.Colors.GREY_700),
                        self.title_text,
                        ft.Container(expand=True),
                        ft.Container(content=self.multi_select_switch, alignment=ft.Alignment(0, 0), padding=ft.Padding(0, 0, 5, 0)),
                        ft.IconButton(icon=ft.Icons.CREATE_NEW_FOLDER, tooltip="Nova Pasta", icon_size=18, width=30, height=30, style=ft.ButtonStyle(padding=0), on_click=lambda _: self._trigger("new_folder")),
                        ft.IconButton(icon=ft.Icons.UPLOAD_FILE, tooltip="Importar Mídia", icon_size=18, width=30, height=30, style=ft.ButtonStyle(padding=0), on_click=lambda _: self._trigger("import")),
                        ft.IconButton(icon=ft.Icons.CLOSE, icon_size=18, width=30, height=30, style=ft.ButtonStyle(padding=0), on_click=lambda _: on_close() if on_close else None)
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.CENTER)
                ),
                ft.Divider(height=1),
                self.main_content
            ],
            spacing=5
        )

    def _trigger(self, action_name):
        if self.on_action_attempt:
            self.on_action_attempt(action_name)

    def _handle_right_click(self, e, item_path, is_folder):
        # Se clicou num item que não está selecionado, seleciona ele unicamente
        if item_path and item_path not in self.selected_items:
            self.selected_items = [item_path]
            self.load_path(self.current_path, self.is_root, self.project_root)
            
        if self.on_context_menu:
            # We pass the global coordinates to show the menu at mouse pos
            x = e.global_position.x if hasattr(e, 'global_position') and e.global_position else getattr(e, 'global_x', 0)
            y = e.global_position.y if hasattr(e, 'global_position') and e.global_position else getattr(e, 'global_y', 0)
            self.on_context_menu(x, y, item_path, is_folder)

    def _handle_tap(self, e, full_path, index):
        is_ctrl = getattr(e.page, "ctrl_pressed", False) or self.multi_select_switch.value
        is_shift = getattr(e.page, "shift_pressed", False)
        
        if is_shift and self.selected_items and self.last_selected_index != -1:
            # Seleção em Range (Shift + Click)
            start = min(self.last_selected_index, index)
            end = max(self.last_selected_index, index)
            
            # Limpa e seleciona o range
            if not is_ctrl:
                self.selected_items = []
                
            for i in range(start, end + 1):
                path_at_i = self.rendered_paths[i]
                if path_at_i not in self.selected_items:
                    self.selected_items.append(path_at_i)
        elif is_ctrl:
            # Toggle (Ctrl + Click)
            if full_path in self.selected_items:
                self.selected_items.remove(full_path)
            else:
                self.selected_items.append(full_path)
            self.last_selected_index = index
        else:
            # Seleção Simples
            if full_path in self.selected_items and len(self.selected_items) == 1:
                # Desmarca se clicar no único já selecionado
                self.selected_items = []
                self.last_selected_index = -1
            else:
                self.selected_items = [full_path]
                self.last_selected_index = index
                
        self.load_path(self.current_path, self.is_root, self.project_root)

    def _handle_drop(self, e: ft.DragTargetEvent, target_dir: str):
        src_path = e.src.data if getattr(e, 'src', None) else None
        if not src_path and hasattr(e, 'page'):
            try:
                src_path = e.page.get_control(e.src_id).data
            except Exception:
                pass
        
        if src_path and self.on_move_item:
            self.on_move_item(src_path, target_dir)

    def load_path(self, current_path, is_root=True, project_root=""):
        self.current_path = current_path
        self.is_root = is_root
        self.project_root = project_root
        self.rendered_paths = [] # Para manter rastreio dos indices para o Shift+Click
        
        self.title_text.value = f"PROJETO: {os.path.basename(current_path)}"
        self.assets_view.controls.clear()
        
        # Limpa seleções se mudar de pasta (opcional, mas evita bugs ao deletar coisas ocultas)
        # self.selected_items.clear()
        
        # Build Tree View (left)
        self.tree_view.controls.clear()
        if project_root and os.path.exists(project_root):
            self._build_tree(project_root, current_path, indent=0)
        
        # Build Back button (if not root)
        if not is_root:
            parent_dir = os.path.dirname(current_path)
            back_btn = ft.Container(
                content=ft.Column([ft.Icon(ft.Icons.ARROW_UPWARD, size=24, color=ft.Colors.BLACK_54), ft.Text("Voltar", size=10, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                width=70, height=70, bgcolor=ft.Colors.WHITE_70, border_radius=5,
                on_click=lambda _: self._trigger("navigate_up")
            )
            # Make Voltar a DragTarget
            dt_back = ft.DragTarget(
                group="assets",
                on_accept=lambda e: self._handle_drop(e, parent_dir),
                content=back_btn
            )
            self.assets_view.controls.append(dt_back)
            
        if not os.path.exists(current_path):
            self.update()
            return
            
        items = os.listdir(current_path)
        if not items and is_root:
            self.assets_view.controls.append(ft.Text("Nenhuma mídia importada.", italic=True, size=12, color=ft.Colors.GREY_700))
            self.update()
            return

        # Render folders
        for item in items:
            full_item = os.path.join(current_path, item)
            if os.path.isdir(full_item):
                self.rendered_paths.append(full_item)
                self.assets_view.controls.append(self._build_folder_icon(item, full_item, len(self.rendered_paths)-1))
                
        # Render files
        for item in items:
            full_item = os.path.join(current_path, item)
            if os.path.isfile(full_item):
                self.rendered_paths.append(full_item)
                self.assets_view.controls.append(self._build_file_icon(item, full_item, len(self.rendered_paths)-1))
                
        self.update()

    def _build_tree(self, node_path, current_view_path, indent=0):
        # Recursive tree builder
        name = os.path.basename(node_path)
        is_current = (node_path == current_view_path)
        
        row = ft.Row([
            ft.Container(width=indent*10),
            ft.Icon(ft.Icons.FOLDER_OPEN if is_current else ft.Icons.FOLDER, size=14, color=ft.Colors.AMBER_500),
            ft.Text(name, size=11, weight=ft.FontWeight.BOLD if is_current else ft.FontWeight.NORMAL, color=ft.Colors.BLACK_87)
        ], spacing=2)
        
        container = ft.Container(
            content=row,
            padding=2,
            bgcolor=ft.Colors.BLUE_GREY_200 if is_current else ft.Colors.TRANSPARENT,
            border_radius=3,
            on_click=lambda _: self._trigger(f"navigate_absolute|{node_path}")
        )
        
        # Make tree node a drag target!
        dt = ft.DragTarget(
            group="assets",
            on_accept=lambda e, p=node_path: self._handle_drop(e, p),
            content=container
        )
        self.tree_view.controls.append(dt)
        
        try:
            items = os.listdir(node_path)
            folders = [i for i in items if os.path.isdir(os.path.join(node_path, i))]
            for f in folders:
                self._build_tree(os.path.join(node_path, f), current_view_path, indent+1)
        except PermissionError:
            pass

    def _get_drag_data(self, full_path):
        import json
        if full_path in self.selected_items:
            return json.dumps(list(self.selected_items))
        return full_path

    def _build_folder_icon(self, name, full_path, index):
        is_selected = full_path in self.selected_items
        container = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.FOLDER, size=32, color=ft.Colors.AMBER_500),
                ft.Text(name, size=10, text_align=ft.TextAlign.CENTER, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=70, height=70, bgcolor=ft.Colors.BLUE_50 if is_selected else ft.Colors.WHITE, 
            border=ft.Border(
                top=ft.BorderSide(2, ft.Colors.BLUE),
                right=ft.BorderSide(2, ft.Colors.BLUE),
                bottom=ft.BorderSide(2, ft.Colors.BLUE),
                left=ft.BorderSide(2, ft.Colors.BLUE)
            ) if is_selected else None,
            border_radius=5,
            tooltip=name
        )
        
        # GestureDetector for Context Menu and Tap
        gd = ft.GestureDetector(
            content=container,
            on_tap=lambda e: self._handle_tap(e, full_path, index),
            on_secondary_tap_down=lambda e: self._handle_right_click(e, full_path, is_folder=True),
            on_double_tap=lambda e: self._trigger(f"navigate_down|{name}")
        )
        
        # Make it draggable AND a drag target
        draggable = ft.Draggable(group="assets", data=self._get_drag_data(full_path), content=gd)
        drag_target = ft.DragTarget(group="assets", on_accept=lambda e: self._handle_drop(e, full_path), content=draggable)
        
        return drag_target

    def _build_file_icon(self, name, full_path, index):
        ext = name.split('.')[-1].lower() if '.' in name else ''
        if ext in ['png', 'jpg', 'jpeg', 'webp', 'svg', 'gif']:
            icon_content = ft.Image(src=full_path, width=36, height=36, fit=ft.BoxFit.COVER)
        elif ext in ['mp3', 'wav', 'ogg']:
            icon_content = ft.Icon(ft.Icons.AUDIO_FILE, size=32, color=ft.Colors.CYAN_700)
        elif ext in ['mp4', 'avi', 'mov', 'webm']:
            icon_content = ft.Icon(ft.Icons.VIDEO_FILE, size=32, color=ft.Colors.PURPLE_600)
        elif ext in ['tbs', 'int', 'json']:
            icon_content = ft.Icon(ft.Icons.DATA_OBJECT, size=32, color=ft.Colors.DEEP_ORANGE_600)
        else:
            icon_content = ft.Icon(ft.Icons.INSERT_DRIVE_FILE, size=32, color=ft.Colors.GREY_600)

        is_selected = full_path in self.selected_items
        container = ft.Container(
            content=ft.Column([
                icon_content,
                ft.Text(name, size=10, text_align=ft.TextAlign.CENTER, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS)
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            width=70, height=70, bgcolor=ft.Colors.BLUE_50 if is_selected else ft.Colors.WHITE, 
            border=ft.Border(
                top=ft.BorderSide(2, ft.Colors.BLUE),
                right=ft.BorderSide(2, ft.Colors.BLUE),
                bottom=ft.BorderSide(2, ft.Colors.BLUE),
                left=ft.BorderSide(2, ft.Colors.BLUE)
            ) if is_selected else None,
            border_radius=5,
            tooltip=name
        )
        
        gd = ft.GestureDetector(
            content=container,
            on_tap=lambda e: self._handle_tap(e, full_path, index),
            on_secondary_tap_down=lambda e: self._handle_right_click(e, full_path, is_folder=False)
        )
        
        draggable = ft.Draggable(group="assets", data=self._get_drag_data(full_path), content=gd)
        return draggable
