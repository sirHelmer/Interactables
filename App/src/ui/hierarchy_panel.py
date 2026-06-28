import flet as ft

class HierarchyPanel(ft.Container):
    def __init__(self, pm, on_selection_change=None, on_reorder=None):
        super().__init__()
        self.pm = pm
        self.on_selection_change = on_selection_change
        self.on_reorder = on_reorder
        
        self.expand = True
        self.bgcolor = ft.Colors.SURFACE_CONTAINER_HIGHEST
        self.padding = 5
        
        self.list_view = ft.ListView(
            expand=True,
            spacing=2,
            padding=10
        )
        
        self.content = ft.Column(
            controls=[
                self.list_view
            ],
            spacing=0,
            expand=True
        )
        
        self.dragged_item_id = None
        self.selected_ids = []
        
    def set_selected(self, ids):
        self.selected_ids = ids
        self.refresh()
        
    def refresh(self):
        self.list_view.controls.clear()
        
        # In Flet, the item at index 0 is at the bottom of the Stack.
        # We want to display the hierarchy where the top visual item is at the top of the list,
        # just like Photoshop. So we iterate backwards.
        for idx in range(len(self.pm.scene_items) - 1, -1, -1):
            item = self.pm.scene_items[idx]
            try:
                row = self._create_item_row(item, idx)
                if row:
                    self.list_view.controls.append(row)
            except Exception as e:
                import traceback
                with open("hierarchy_error.log", "a") as f:
                    f.write(f"Erro ao criar row {idx}: {e}\n{traceback.format_exc()}\n")
            
        try:
            self.update()
        except:
            pass
            
        if hasattr(self, 'list_view'):
            count_info = ft.Container(
                content=ft.Row([
                    ft.Icon(ft.Icons.FORMAT_LIST_NUMBERED, size=16, color=ft.Colors.GREY_600),
                    ft.Text(f"{len(self.pm.scene_items)} elementos na cena", size=13, color=ft.Colors.GREY_600, italic=True)
                ], alignment=ft.MainAxisAlignment.CENTER),
                padding=5
            )
            self.list_view.controls.insert(0, count_info)
            try:
                self.update()
            except:
                pass

    def _create_item_row(self, item, current_idx):
        iid = item.get("instance_id")
        name = item.get("name", "Objeto")
        
        def handle_delete(e):
            self.pm.scene_items = [x for x in self.pm.scene_items if x.get("instance_id") != iid]
            if self.on_reorder:
                self.on_reorder()
            self.refresh()
            
        def handle_double_tap(e):
            # Envia pro topo (remove e adiciona no final)
            target = next((x for x in self.pm.scene_items if x.get("instance_id") == iid), None)
            if target:
                self.pm.scene_items.remove(target)
                self.pm.scene_items.append(target)
                
                # Centraliza
                # Usaremos um valor placeholder que o canvas.py pode interpretar, ou setamos 0,0 
                # (Idealmente canvas_width/2 mas o zoom complica, vamos setar o x, y depois no canvas)
                if self.on_selection_change:
                    self.on_selection_change([iid], double_click=True)
                
                if self.on_reorder:
                    self.on_reorder()
                self.refresh()
                
        def handle_tap(e):
            if self.on_selection_change:
                self.on_selection_change([iid])
                
        def drag_accept(e):
            src_id = e.page.get_control(e.src_id).data
            if src_id != iid:
                # Move src_id para a posicao deste item
                src_item = next((x for x in self.pm.scene_items if x.get("instance_id") == src_id), None)
                dst_item = next((x for x in self.pm.scene_items if x.get("instance_id") == iid), None)
                
                if src_item and dst_item:
                    src_idx = self.pm.scene_items.index(src_item)
                    dst_idx = self.pm.scene_items.index(dst_item)
                    
                    self.pm.scene_items.pop(src_idx)
                    self.pm.scene_items.insert(dst_idx, src_item)
                    
                    # Update all z_indices
                    for i, si in enumerate(self.pm.scene_items):
                        si["z_index"] = i
                        
                    self.pm.save_project()
                    
                    if self.on_reorder:
                        self.on_reorder()
                    self.refresh()

        obj_data = self.pm.objects.get(item.get("object_id"), {})
        obj_type = obj_data.get("type", "image")
        obj_name = obj_data.get("name", "Desconhecido")
        
        is_vis = item.get("visible", True)
        
        def handle_visibility(e):
            item["visible"] = not item.get("visible", True)
            self.pm.save_project()
            if self.on_reorder:
                self.on_reorder()
            self.refresh()
            
        type_icon = ft.Icons.IMAGE
        if obj_type == "text": type_icon = ft.Icons.TEXT_FIELDS
        elif obj_type == "shape": type_icon = ft.Icons.CATEGORY
        elif obj_type == "audio": type_icon = ft.Icons.AUDIOTRACK
        elif obj_type == "video": type_icon = ft.Icons.MOVIE
        
        display_text = f"{name} ({obj_name})"

        is_selected = iid in self.selected_ids
        
        row_content = ft.Container(
            bgcolor=ft.Colors.BLUE_50 if is_selected else ft.Colors.WHITE,
            border_radius=4,
            padding=5,
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.DRAG_INDICATOR, size=16, color=ft.Colors.GREY_400),
                    ft.IconButton(
                        icon=ft.Icons.VISIBILITY if is_vis else ft.Icons.VISIBILITY_OFF,
                        icon_size=16, width=24, height=24, padding=0,
                        icon_color=ft.Colors.BLACK_87 if is_vis else ft.Colors.GREY_400,
                        on_click=handle_visibility
                    ),
                    ft.Icon(type_icon, size=16, color=ft.Colors.BLACK_54),
                    ft.Text(display_text, size=12, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.IconButton(
                        icon=ft.Icons.DELETE_OUTLINE,
                        icon_color=ft.Colors.RED_400,
                        icon_size=16,
                        width=30, height=30,
                        on_click=handle_delete
                    )
                ]
            ),
            border=ft.Border(
                top=ft.BorderSide(1, ft.Colors.GREY_200),
                bottom=ft.BorderSide(1, ft.Colors.GREY_200),
                left=ft.BorderSide(1, ft.Colors.GREY_200),
                right=ft.BorderSide(1, ft.Colors.GREY_200)
            )
        )
        
        # GestureDetector for click and double click
        gesture = ft.GestureDetector(
            content=row_content,
            on_tap=handle_tap,
            on_double_tap_down=handle_double_tap
        )

        draggable = ft.Draggable(
            group="hierarchy",
            content=gesture,
            content_feedback=ft.Container(
                content=ft.Text(name, size=12, color=ft.Colors.WHITE),
                bgcolor=ft.Colors.BLUE_400,
                padding=5,
                border_radius=4
            ),
            data=str(iid) if iid is not None else "unknown"
        )

        target = ft.DragTarget(
            group="hierarchy",
            content=draggable,
            on_accept=drag_accept
        )

        return target
