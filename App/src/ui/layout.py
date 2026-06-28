import flet as ft
from .panels import PropertiesPanel, Toolbar
from .canvas import CanvasArea
from .top_menu import TopMenu
from .project_panel import ProjectPanel
from .modals.create_project import CreateProjectModal
from .hierarchy_panel import HierarchyPanel
from .modals.element_modals import ExactInputModal
from .player import PlayerView
from core.project_manager import ProjectManager
import os
import shutil

class AppLayout(ft.Stack):
    def __init__(self):
        super().__init__()
        self.expand = True
        
        self.pm = ProjectManager()
        self.current_view_dir = ""
        self.clipboard_path = None
        
        self.file_picker = ft.FilePicker()
        
        self.create_project_modal = CreateProjectModal(
            on_create_callback=self.handle_create_project,
            on_cancel_callback=None,
            file_picker=self.file_picker
        )
        
        self.top_menu = TopMenu(
            on_view_toggle=self.toggle_panel,
            on_create_project_click=self.open_create_project_modal,
            on_open_project_click=self.open_project_folder,
            on_recent_click=self.open_recent_projects_modal,
            on_save_project_click=self.handle_save_project,
            on_close_project_click=self.close_project,
            on_test_presentation_click=self.handle_test_presentation,
            on_zoom_in_click=lambda: self.canvas.change_zoom(0.1),
            on_zoom_out_click=lambda: self.canvas.change_zoom(-0.1),
            on_zoom_fit_click=lambda: self.canvas.zoom_fit(),
            on_duplicate_click=self.handle_duplicate_items,
            on_resize_canvas_click=self.open_resize_canvas_modal,
            on_undo_click=self.handle_undo,
            on_redo_click=self.handle_redo,
            on_save_as_click=self.handle_save_as,
            on_open_int_click=self.handle_open_int,
            on_auto_save_toggle=self.toggle_auto_save
        )
        
        self.canvas = CanvasArea()
        self.canvas.on_selection_change = self.handle_selection_change
        
        self.properties = PropertiesPanel(on_close=lambda: self.toggle_panel("properties", False))
        
        # O HierarchyPanel reage às mudanças de Z-Index/ordem, chamando o canvas para re-renderizar
        self.hierarchy = HierarchyPanel(
            pm=self.pm, 
            on_selection_change=self.handle_selection_change_from_hierarchy,
            on_reorder=self.handle_hierarchy_reorder
        )
        
        self.canvas.on_hierarchy_change = self.hierarchy.refresh
        
        self.properties.visible = True
        self.hierarchy.visible = True
        
        def change_tab(index):
            if hasattr(self, 'right_tabs'):
                self.right_tabs.controls[2].visible = (index == 0)
                self.right_tabs.controls[3].visible = (index == 1)
            btn_props.style.color = ft.Colors.BLUE if index == 0 else ft.Colors.GREY
            btn_objs.style.color = ft.Colors.BLUE if index == 1 else ft.Colors.GREY
            if self.page:
                self.right_tabs.update()
                
        self.change_tab = change_tab

        btn_props = ft.TextButton(
            content=ft.Row([ft.Icon(ft.Icons.TUNE, size=14), ft.Text("Propriedades", size=12)], alignment=ft.MainAxisAlignment.CENTER),
            on_click=lambda _: self.change_tab(0), 
            style=ft.ButtonStyle(color=ft.Colors.BLUE, shape=ft.RoundedRectangleBorder(radius=0)), 
            expand=True
        )
        btn_objs = ft.TextButton(
            content=ft.Row([ft.Icon(ft.Icons.LAYERS, size=14), ft.Text("Objetos", size=12)], alignment=ft.MainAxisAlignment.CENTER),
            on_click=lambda _: self.change_tab(1), 
            style=ft.ButtonStyle(color=ft.Colors.GREY, shape=ft.RoundedRectangleBorder(radius=0)), 
            expand=True
        )
        
        self.right_tabs = ft.Column(
            expand=True,
            controls=[
                ft.Row([btn_props, btn_objs], spacing=0),
                ft.Divider(height=1),
                ft.Container(content=self.properties, expand=True, visible=True),
                ft.Container(content=self.hierarchy, expand=True, visible=False)
            ]
        )
        
        self.right_panel_container = ft.Container(
            content=self.right_tabs,
            width=300,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGHEST,
            border=ft.Border(left=ft.BorderSide(1, ft.Colors.GREY_300)),
            visible=True
        )
        
        self.project_panel = ProjectPanel(
            on_close=lambda: self.toggle_panel("project", False),
            on_action_attempt=self.check_project_action,
            on_context_menu=self.handle_context_menu,
            on_move_item=self.handle_move_item
        )
        self.project_panel.visible = True
        
        self.toolbar = Toolbar(on_tool_change=self.handle_tool_change)
        self.toolbar.visible = True
        self.canvas.get_paint_color = lambda: self.toolbar.paint_color
        
        self.prop_resizer = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
            content=ft.Container(width=4, bgcolor=ft.Colors.BLUE_GREY_200),
            on_pan_update=self.resize_properties
        )
        self.prop_resizer.visible = True
        
        self.proj_resizer = ft.GestureDetector(
            mouse_cursor=ft.MouseCursor.RESIZE_UP_DOWN,
            content=ft.Container(height=4, bgcolor=ft.Colors.BLUE_GREY_200),
            on_pan_update=self.resize_project
        )
        self.proj_resizer.visible = True

        self.canvas_and_props = ft.Row(
            controls=[
                ft.Container(content=self.canvas, expand=True, bgcolor=ft.Colors.GREY_300),
                self.prop_resizer,
                self.right_panel_container
            ],
            expand=True,
            spacing=0
        )
        
        self.workspace_col = ft.Column(
            controls=[
                self.canvas_and_props,
                self.proj_resizer,
                self.project_panel
            ],
            expand=True,
            spacing=0
        )

        self.middle_row = ft.Row(
            controls=[
                self.toolbar,
                self.workspace_col
            ],
            expand=True,
            spacing=0
        )
        
        self.main_column = ft.Column(
            controls=[
                self.top_menu,
                self.middle_row
            ],
            spacing=0,
            expand=True
        )
        
        self.main_container = ft.Container(
            content=self.main_column,
            expand=True,
            bgcolor=ft.Colors.BLUE_GREY_50,
            on_click=self.close_context_menu  # Clique fora fecha o menu
        )
        
        self.controls = [self.main_container]
        self.context_menu_container = None

    def update_view_menu(self):
        self.top_menu.view_menu_items["properties"].icon = ft.Icons.CHECK if getattr(self.right_panel_container, 'visible', True) else None
        self.top_menu.view_menu_items["project"].icon = ft.Icons.CHECK if getattr(self.project_panel, 'visible', True) else None
        self.top_menu.view_menu_items["toolbar"].icon = ft.Icons.CHECK if getattr(self.toolbar, 'visible', True) else None
        self.top_menu.update()

    def toggle_panel(self, panel_name: str, is_visible: bool = None):
        if panel_name == "properties":
            is_vis = is_visible if is_visible is not None else not self.right_panel_container.visible
            self.right_panel_container.visible = is_vis
            self.prop_resizer.visible = is_vis
            self.right_panel_container.update()
            self.prop_resizer.update()
        elif panel_name == "project":
            is_vis = is_visible if is_visible is not None else not getattr(self.project_panel, 'visible', True)
            self.project_panel.visible = is_vis
            self.proj_resizer.visible = is_vis
            self.project_panel.update()
            self.proj_resizer.update()
        elif panel_name == "toolbar":
            self.toolbar.visible = is_visible if is_visible is not None else not getattr(self.toolbar, 'visible', True)
            self.toolbar.update()
        
        self.update_view_menu()
        self.update()

    def resize_properties(self, e):
        new_width = max(200, min(500, self.right_panel_container.width - e.local_delta.x))
        self.right_panel_container.width = new_width
        self.right_panel_container.update()

    def resize_project(self, e):
        new_height = max(100, min(400, self.project_panel.height - e.local_delta.y))
        self.project_panel.height = new_height
        self.project_panel.update()

    def did_mount(self):
        self.page.overlay.append(self.create_project_modal)

    def handle_tool_change(self, tool_name: str):
        self.canvas.set_active_tool(tool_name)
        if tool_name == "paint" and hasattr(self, 'change_tab'):
            self.change_tab(0)

    def handle_selection_change(self, instance_id, item_data=None, object_data=None):
        if instance_id:
            self.properties.load_item(instance_id, item_data, object_data, self.pm, self.on_property_changed)
        else:
            self.properties.clear()
            
        if hasattr(self, 'hierarchy') and self.hierarchy:
            self.hierarchy.set_selected([instance_id] if instance_id else [])
            
    def handle_selection_change_from_hierarchy(self, instance_ids, double_click=False):
        # Comunica o canvas que a hierarquia mandou selecionar
        if len(instance_ids) > 0:
            iid = instance_ids[0]
            self.canvas.selected_item_ids = [iid]
            
            if double_click:
                # Centraliza
                target = next((x for x in self.pm.scene_items if x.get("instance_id") == iid), None)
                if target:
                    target["x"] = self.pm.canvas_width / 2
                    target["y"] = self.pm.canvas_height / 2
            
            item = next((x for x in self.pm.scene_items if x.get("instance_id") == iid), None)
            if item:
                obj_data = self.pm.objects.get(item["object_id"])
                self.handle_selection_change(iid, item, obj_data)
        else:
            self.canvas.selected_item_ids = []
            self.handle_selection_change(None)
            
        self.canvas.render_canvas()
        
    def handle_hierarchy_reorder(self):
        # Quando reordena, o canvas deve re-renderizar para atualizar o Z-Index do stack
        self.pm.save_project()
        self.canvas.render_canvas()
    def on_property_changed(self):
        self.pm.save_project()
        self.canvas.render_canvas()
        if hasattr(self, 'hierarchy') and self.hierarchy:
            self.hierarchy.refresh()

    def show_snackbar(self, message, is_error=True):
        color = ft.Colors.RED_700 if is_error else ft.Colors.GREEN_700
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=color,
            duration=3000
        )
        self.page.snack_bar.open = True
        self.page.update()
        
    def handle_keyboard(self, e):
        # We ONLY bind 'Delete' because global 'Backspace' or 'Enter' will trigger
        # while the user is typing in the PropertiesPanel, instantly deleting their object!
        if e.key == "Delete":
            if getattr(self.canvas, 'selected_item_ids', None):
                self.delete_selected_items()
        elif e.ctrl and e.key == "D":
            self.handle_duplicate_items()
        elif e.ctrl and e.key == "Z":
            self.handle_undo()
        elif e.ctrl and e.key == "Y":
            self.handle_redo()
                
    def delete_selected_items(self):
        if not getattr(self.canvas, 'selected_item_ids', None):
            return
            
        modified = False
        for iid in self.canvas.selected_item_ids:
            target = next((x for x in self.pm.scene_items if x.get("instance_id") == iid), None)
            if target:
                self.pm.scene_items.remove(target)
                modified = True
                
        if modified:
            self.canvas.selected_item_ids = []
            self.handle_selection_change(None)
            self.canvas.render_canvas()
            self.pm.save_project()
            if hasattr(self, 'hierarchy') and self.hierarchy:
                self.hierarchy.refresh()

    def show_conflict_modal(self, pending_action):
        def on_save_close(e):
            self.conflict_dialog.open = False
            self.pm.save_project()
            self._do_close_project(save=True)
            self.page.update()
            pending_action()

        def on_close_only(e):
            self.conflict_dialog.open = False
            self._do_close_project(save=False)
            self.page.update()
            pending_action()

        def on_cancel(e):
            self.conflict_dialog.open = False
            self.page.update()

        self.conflict_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Projeto em Andamento"),
            content=ft.Text("Um projeto já está aberto! Salve-o ou feche-o antes de abrir um novo."),
            actions=[
                ft.TextButton("Salvar atual e fechar", on_click=on_save_close),
                ft.TextButton("Fechar projeto atual", on_click=on_close_only, style=ft.ButtonStyle(color=ft.Colors.RED)),
                ft.TextButton("Cancelar", on_click=on_cancel),
            ],
        )
        self.page.overlay.append(self.conflict_dialog)
        self.conflict_dialog.open = True
        self.page.update()

    def handle_save_project(self):
        if not self.pm.is_loaded:
            self.show_snackbar("Nenhum projeto aberto para salvar.", is_error=True)
            return
        
        self.pm.save_project()
        self.show_snackbar("Projeto salvo com sucesso!", is_error=False)

    def handle_test_presentation(self):
        if not self.pm.is_loaded:
            self.show_snackbar("Abra um projeto para testar a apresentação.", is_error=True)
            return
            
        def close_player():
            if self.player_view in self.page.overlay:
                self.page.overlay.remove(self.player_view)
            self.page.update()
            
        self.player_view = PlayerView(pm=self.pm, on_close=close_player)
        self.page.overlay.append(self.player_view)
        self.page.update()

    def close_project(self, _=None):
        if not self.pm.is_loaded:
            return
            
        def on_yes(e):
            self.close_dialog.open = False
            self.pm.save_project()
            self._do_close_project(save=True)
            self.page.update()

        def on_no(e):
            self.close_dialog.open = False
            self._do_close_project(save=False)
            self.page.update()

        def on_cancel(e):
            self.close_dialog.open = False
            self.page.update()

        self.close_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Fechar Projeto"),
            content=ft.Text("Deseja salvar o projeto antes de fechá-lo?"),
            actions=[
                ft.TextButton("Salvar", on_click=on_yes),
                ft.TextButton("Não Salvar", on_click=on_no, style=ft.ButtonStyle(color=ft.Colors.RED)),
                ft.TextButton("Cancelar", on_click=on_cancel),
            ],
        )
        self.page.overlay.append(self.close_dialog)
        self.close_dialog.open = True
        self.page.update()

    def _do_close_project(self, save=False):
        self.pm.is_loaded = False
        self.pm.path = None
        self.pm.name = "Sem Projeto"
        self.current_view_dir = ""
        self.project_panel.load_path("", is_root=False)
        self.canvas.set_project_manager(self.pm)
        self.show_snackbar("Projeto fechado.", is_error=False)

    def get_recent_projects(self):
        from pathlib import Path
        import json
        recent_file = os.path.join(str(Path.home()), ".interactables_recent.json")
        try:
            if os.path.exists(recent_file):
                with open(recent_file, "r") as f:
                    return json.load(f)
        except:
            pass
        return []

    def save_recent_projects(self, recent):
        from pathlib import Path
        import json
        recent_file = os.path.join(str(Path.home()), ".interactables_recent.json")
        try:
            with open(recent_file, "w") as f:
                json.dump(recent, f)
        except Exception as e:
            print(f"Erro ao salvar recentes: {e}")

    def add_recent_project(self, path):
        recent = self.get_recent_projects()
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        recent = recent[:5]
        self.save_recent_projects(recent)

    def open_recent_projects_modal(self, _=None):
        if self.pm.is_loaded:
            self.show_conflict_modal(lambda: self._show_recent_modal_internal())
            return
        self._show_recent_modal_internal()

    def _show_recent_modal_internal(self):
        recent = self.get_recent_projects()
        if not recent:
            self.show_snackbar("Nenhum projeto recente encontrado.")
            return

        def on_select(path):
            self.recent_dialog.open = False
            self.page.update()
            self.page.run_task(self._do_open_project_folder, force_path=path)

        def on_cancel(e):
            self.recent_dialog.open = False
            self.page.update()

        items = [
            ft.ListTile(
                title=ft.Text(os.path.basename(p)),
                subtitle=ft.Text(p),
                leading=ft.Icon(ft.Icons.FOLDER),
                on_click=lambda e, path=p: on_select(path)
            ) for p in recent
        ]

        self.recent_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Projetos Recentes"),
            content=ft.Container(
                width=400,
                content=ft.Column(items, tight=True, scroll=ft.ScrollMode.AUTO)
            ),
            actions=[ft.TextButton("Cancelar", on_click=on_cancel)]
        )
        self.page.overlay.append(self.recent_dialog)
        self.recent_dialog.open = True
        self.page.update()

    def show_no_project_modal(self):
        def on_create(e):
            self.no_proj_dialog.open = False
            self.page.update()
            self.open_create_project_modal()

        def on_open(e):
            self.no_proj_dialog.open = False
            self.page.update()
            self.open_project_folder()

        def on_cancel(e):
            self.no_proj_dialog.open = False
            self.page.update()

        self.no_proj_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Nenhum Projeto Aberto"),
            content=ft.Text("Não é possível realizar esta ação sem um projeto aberto.\nDeseja criar um novo projeto ou abrir uma pasta?"),
            actions=[
                ft.TextButton("Criar Novo", on_click=on_create),
                ft.TextButton("Abrir Pasta/Projeto", on_click=on_open),
                ft.TextButton("Cancelar", on_click=on_cancel),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(self.no_proj_dialog)
        self.no_proj_dialog.open = True
        self.page.update()

    def open_create_project_modal(self, _=None):
        if self.pm.is_loaded:
            self.show_conflict_modal(lambda: self._open_create_project_modal_internal())
            return
        self._open_create_project_modal_internal()

    def _open_create_project_modal_internal(self):
        self.create_project_modal.open = True
        self.page.update()

    # --- DRAG AND DROP ---
    def handle_move_item(self, src_path, target_dir):
        if not src_path or not target_dir or not os.path.exists(target_dir): return
        
        import json
        paths = []
        try:
            # Tenta dar parse caso o drag venha como JSON array (multi-select)
            if src_path.startswith('[') and src_path.endswith(']'):
                paths = json.loads(src_path)
            else:
                paths = [src_path]
        except:
            paths = [src_path]
            
        moved_any = False
        for p in paths:
            if os.path.exists(p):
                if os.path.dirname(p) == target_dir:
                    continue # Já está na pasta
                try:
                    shutil.move(p, os.path.join(target_dir, os.path.basename(p)))
                    moved_any = True
                except Exception as e:
                    print(f"Erro ao mover arquivo {p}: {e}")
                    
        if moved_any:
            # Limpa a seleção do painel pois os itens mudaram de lugar
            self.project_panel.selected_items.clear()
            self._reload_project_panel()

    # --- CONTEXT MENU E OPÇÕES ---
    def close_context_menu(self, e=None):
        if self.context_menu_container in self.controls:
            self.controls.remove(self.context_menu_container)
            self.context_menu_container = None
            self.update()

    def handle_context_menu(self, x, y, item_path, is_folder):
        self.close_context_menu()
        
        has_item = item_path is not None
        can_paste = self.clipboard_path is not None and os.path.exists(self.clipboard_path)
        
        def action_wrapper(action):
            def wrapper(e):
                self.close_context_menu()
                self.execute_context_action(action, item_path, is_folder)
            return wrapper
            
        menu_items = [
            {"text": "Importar", "icon": ft.Icons.UPLOAD_FILE, "on_click": action_wrapper("import"), "disabled": False},
            {"text": "Nova Pasta", "icon": ft.Icons.CREATE_NEW_FOLDER, "on_click": action_wrapper("new_folder"), "disabled": False},
            None, # Divider
            {"text": "Copiar", "icon": ft.Icons.COPY, "on_click": action_wrapper("copy"), "disabled": not has_item},
            {"text": "Colar", "icon": ft.Icons.PASTE, "on_click": action_wrapper("paste"), "disabled": not can_paste},
            None, # Divider
            {"text": "Recortar", "icon": ft.Icons.CONTENT_CUT, "on_click": action_wrapper("cut"), "disabled": not has_item},
            {"text": "Renomear", "icon": ft.Icons.EDIT, "on_click": action_wrapper("rename"), "disabled": not has_item},
            {"text": "Excluir", "icon": ft.Icons.DELETE, "on_click": action_wrapper("delete"), "disabled": not has_item},
        ]
        
        # Como o ContextMenu nativo às vezes é restrito, criamos um painel flutuante customizado simulando ele.
        # Ajustamos x e y para compensar possível estouro de tela (ex: próximo da borda direita/inferior)
        self.context_menu_container = ft.Container(
            left=min(x, self.page.width - 200) if self.page.width else x, 
            top=min(y, self.page.height - 300) if self.page.height else y,
            bgcolor=ft.Colors.WHITE,
            border_radius=5,
            padding=5,
            shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK_26),
            content=ft.Column(
                [
                    ft.TextButton(item["text"], icon=item["icon"], disabled=item["disabled"], on_click=item["on_click"], width=150, style=ft.ButtonStyle(alignment=ft.Alignment.CENTER_LEFT, color=ft.Colors.RED_500 if item["text"] == "Excluir" else ft.Colors.BLACK_87))
                    if item else ft.Divider(height=1)
                    for item in menu_items
                ],
                spacing=0
            )
        )
        
        self.controls.append(self.context_menu_container)
        self.update()

    def execute_context_action(self, action, item_path, is_folder):
        if not self.pm.is_loaded:
            self.show_no_project_modal()
            return

        # target_dir é o current_view_dir, mas se clicou numa pasta específica, pode ser ela
        target_dir = item_path if (is_folder and action in ["import", "new_folder", "paste"]) else self.current_view_dir
            
        if action == "import":
            self.page.run_task(self._do_import, target_dir)
            
        elif action == "new_folder":
            self.new_folder_modal = ExactInputModal("Criar Nova Pasta", {"Nome da Pasta": "Nova Pasta"}, lambda vals: self._do_create_folder(vals, target_dir))
            self.page.overlay.append(self.new_folder_modal)
            self.new_folder_modal.open = True
            self.page.update()
            
        elif action == "copy":
            self.clipboard_paths = list(self.project_panel.selected_items)
            self.is_cut = False
            
        elif action == "cut":
            self.clipboard_paths = list(self.project_panel.selected_items)
            self.is_cut = True
            
        elif action == "paste":
            if getattr(self, 'clipboard_paths', None):
                for cp in self.clipboard_paths:
                    if not os.path.exists(cp): continue
                    dest = os.path.join(target_dir, os.path.basename(cp))
                    
                    # Se for a mesma pasta, ignora
                    if os.path.dirname(cp) == target_dir:
                        continue
                        
                    try:
                        if getattr(self, 'is_cut', False):
                            shutil.move(cp, dest)
                        else:
                            if os.path.isdir(cp):
                                shutil.copytree(cp, dest)
                            else:
                                shutil.copy2(cp, dest)
                    except Exception as e:
                        self.show_snackbar(f"Erro ao colar: {e}")
                
                if getattr(self, 'is_cut', False):
                    self.clipboard_paths = [] # Limpa após recortar
                    self.is_cut = False
                self._reload_project_panel()
        elif action == "rename":
            old_name = os.path.basename(item_path)
            self.rename_modal = ExactInputModal("Renomear Item", {"Novo Nome": old_name}, lambda vals: self._do_rename(item_path, vals[0]))
            self.page.overlay.append(self.rename_modal)
            self.rename_modal.open = True
            self.page.update()
            
        elif action == "delete":
            has_changes = False
            items_to_delete = list(self.project_panel.selected_items)
            for path in items_to_delete:
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    
                    # Sincroniza a deleção com o ProjectManager e atualiza o canvas se necessário
                    if self.pm.handle_file_deleted(path):
                        has_changes = True
                except Exception as e:
                    self.show_snackbar(f"Erro ao excluir {os.path.basename(path)}: {e}")
                    
            if has_changes:
                self.canvas.render_canvas()
                
            # Limpa seleção após deletar
            self.project_panel.selected_items.clear()
            self._reload_project_panel()

    # --- AÇÕES ANTIGAS (Botões Superiores) ---
    def check_project_action(self, action_string):
        if not self.pm.is_loaded:
            self.show_no_project_modal()
            return

        if action_string == "new_folder":
            self.execute_context_action("new_folder", None, False)
            
        elif action_string == "import":
            self.execute_context_action("import", None, False)
            
        elif action_string == "navigate_up":
            parent = os.path.dirname(self.current_view_dir)
            if parent.startswith(self.pm.path):
                self.current_view_dir = parent
                self._reload_project_panel()
                
        elif action_string.startswith("navigate_down|"):
            folder_name = action_string.split("|")[1]
            self.current_view_dir = os.path.join(self.current_view_dir, folder_name)
            self._reload_project_panel()
            
        elif action_string.startswith("navigate_absolute|"):
            self.current_view_dir = action_string.split("|")[1]
            self._reload_project_panel()

    def _reload_project_panel(self):
        self.project_panel.load_path(self.current_view_dir, is_root=(self.current_view_dir == self.pm.path), project_root=self.pm.path)
        self.canvas.set_project_manager(self.pm)
        if hasattr(self, 'hierarchy') and self.hierarchy:
            self.hierarchy.refresh()

    def _do_create_folder(self, values, target_dir):
        folder_name = values[0]
        if folder_name.strip():
            os.makedirs(os.path.join(target_dir, folder_name.strip()), exist_ok=True)
            self._reload_project_panel()

    def _do_rename(self, item_path, new_name):
        if new_name.strip():
            dir_path = os.path.dirname(item_path)
            os.rename(item_path, os.path.join(dir_path, new_name.strip()))
            self._reload_project_panel()

    async def _do_import(self, target_dir):
        files = await self.file_picker.pick_files(allow_multiple=True, dialog_title="Importar Mídias")
        if files:
            for f in files:
                if f.path: 
                    shutil.copy2(f.path, target_dir)
            self._reload_project_panel()

    def open_project_folder(self, _=None):
        self.page.run_task(self._do_open_project_folder)
        
    async def _do_open_project_folder(self, force_path=None):
        path = force_path
        if not path:
            path = await self.file_picker.get_directory_path(dialog_title="Abrir Pasta...")
            
        if path and os.path.exists(path):
            if self.pm.load_project(path):
                self.show_snackbar(f"Projeto carregado: {self.pm.name}", is_error=False)
                self.add_recent_project(self.pm.path)
                self.current_view_dir = self.pm.path
                self._reload_project_panel()
            else:
                self.prompt_project_conversion(path)

    def handle_save_as(self, _=None):
        if not self.pm.is_loaded:
            self.show_snackbar("Nenhum projeto aberto.", True)
            return
            
        def on_save_folder(e):
            dialog.open = False
            self.page.update()
            self.page.run_task(self._do_save_as)

        def on_save_int(e):
            dialog.open = False
            self.page.update()
            self.page.run_task(self._do_save_as_int)

        def on_cancel(e):
            dialog.open = False
            self.page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Opções de Salvamento"),
            content=ft.Text("Como deseja salvar o projeto?"),
            actions=[
                ft.TextButton("Salvar em Nova Pasta", on_click=on_save_folder),
                ft.TextButton("Exportar Arquivo (.int)", on_click=on_save_int),
                ft.TextButton("Cancelar", on_click=on_cancel),
            ]
        )
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    async def _do_save_as(self):
        path = await self.file_picker.get_directory_path(dialog_title="Salvar Como (Escolha a pasta destino vazia)...")
        if path:
            if self.pm.save_as(path):
                self.show_snackbar(f"Projeto salvo como: {self.pm.name}", is_error=False)
                self.add_recent_project(self.pm.path)
                self.current_view_dir = self.pm.path
                self._reload_project_panel()
            else:
                self.show_snackbar("Erro ao salvar projeto em novo local.", True)

    async def _do_save_as_int(self):
        path = await self.file_picker.save_file(
            dialog_title="Exportar Projeto", 
            file_name=f"{self.pm.name}.int", 
            allowed_extensions=["int"]
        )
        if path:
            if not path.endswith('.int'):
                path += '.int'
            if self.pm.export_int(path):
                self.show_snackbar(f"Projeto exportado como: {os.path.basename(path)}", is_error=False)
            else:
                self.show_snackbar("Erro ao exportar projeto (.int).", True)

    def handle_open_int(self, _=None):
        self.page.run_task(self._do_open_int)

    async def _do_open_int(self):
        files = await self.file_picker.pick_files(
            dialog_title="1. Selecione o arquivo .int",
            allowed_extensions=["int"]
        )
        if not files or not files[0].path:
            return
            
        zip_path = files[0].path
        
        extract_root = await self.file_picker.get_directory_path(dialog_title="2. Escolha a pasta raiz para extrair o projeto...")
        if not extract_root:
            return
            
        basename = os.path.basename(zip_path)
        folder_name = os.path.splitext(basename)[0]
        extract_dir = os.path.join(extract_root, folder_name)
        
        counter = 1
        original_dir = extract_dir
        while os.path.exists(extract_dir):
            extract_dir = f"{original_dir}_{counter}"
            counter += 1
            
        os.makedirs(extract_dir, exist_ok=True)
            
        if self.pm.import_int(zip_path, extract_dir):
            self.show_snackbar(f"Projeto importado: {self.pm.name}", is_error=False)
            self.add_recent_project(self.pm.path)
            self.current_view_dir = self.pm.path
            self._reload_project_panel()
        else:
            self.show_snackbar("Erro ao importar arquivo .int.", True)

    def toggle_auto_save(self, is_active):
        self.is_auto_save_active = is_active
        if is_active and not getattr(self, '_auto_save_running', False):
            self._auto_save_running = True
            self.page.run_task(self._auto_save_loop)
            
    async def _auto_save_loop(self):
        import asyncio
        while getattr(self, 'is_auto_save_active', False):
            await asyncio.sleep(60) # 1 minuto
            if getattr(self, 'is_auto_save_active', False) and self.pm.is_loaded:
                self.pm.save_project()
                print("Auto Save ativado.")
        self._auto_save_running = False

    def prompt_project_conversion(self, path):
        def on_yes(e):
            self.convert_dialog.open = False
            self.page.update()
            
            self.pm.path = path
            self.pm.name = os.path.basename(path)
            self.pm.is_loaded = True
            self.pm.save_project() # Cria o project.json pra transformar numa pasta de projeto
            self.show_snackbar(f"Pasta convertida em projeto: {self.pm.name}", is_error=False)
            self.add_recent_project(self.pm.path)
            
            self.current_view_dir = self.pm.path
            self._reload_project_panel()

        def on_no(e):
            self.convert_dialog.open = False
            self.page.update()
            self.open_project_folder() # Abre novamente o seletor

        def on_cancel(e):
            self.convert_dialog.open = False
            self.page.update()

        self.convert_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Converter Pasta?"),
            content=ft.Text("A pasta selecionada não é um projeto do Interactables. Deseja convertê-la em um projeto agora?"),
            actions=[
                ft.TextButton("Sim, Converter", on_click=on_yes),
                ft.TextButton("Não, Escolher Outra", on_click=on_no),
                ft.TextButton("Cancelar", on_click=on_cancel),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        self.page.overlay.append(self.convert_dialog)
        self.convert_dialog.open = True
        self.page.update()

    def handle_create_project(self, name, path, width, height, create_folders):
        # Primeiro verificamos se a pasta de destino JÁ possui um projeto.
        from pathlib import Path
        
        # Simula o caminho que o ProjectManager vai criar
        target_path = path if path.strip() else str(Path.home() / "Documents")
        final_dir = os.path.join(target_path, name if name.strip() else "Novo Projeto")
        
        # Verifica se final_dir já tem project.json
        proj_file = os.path.join(final_dir, "project.json")
        if os.path.exists(proj_file):
            self.show_snackbar("Pasta já contém um projeto! Abrindo projeto existente...", is_error=False)
            if self.pm.load_project(final_dir):
                self.add_recent_project(self.pm.path)
                self.current_view_dir = self.pm.path
                self._reload_project_panel()
                return

        actual_path = self.pm.create_project(name, path, width, height, create_folders)
        self.add_recent_project(actual_path)
        self.current_view_dir = actual_path
        self._reload_project_panel()
        self.show_snackbar(f"Projeto {name} configurado fisicamente em: {actual_path}", is_error=False)

    def handle_duplicate_items(self):
        if not self.pm.is_loaded or not getattr(self.canvas, 'selected_item_ids', None):
            return
        
        import copy, uuid
        new_selection = []
        for iid in self.canvas.selected_item_ids:
            item = next((x for x in self.pm.scene_items if x.get("instance_id") == iid), None)
            if item:
                new_item = copy.deepcopy(item)
                new_item["instance_id"] = str(uuid.uuid4())
                new_item["x"] += 20
                new_item["y"] += 20
                new_item["z_index"] = len(self.pm.scene_items)
                if "name" in new_item:
                    new_item["name"] += " (Cópia)"
                self.pm.scene_items.append(new_item)
                new_selection.append(new_item["instance_id"])
                
        if new_selection:
            self.pm.save_project()
            self.canvas.selected_item_ids = new_selection
            self.canvas.render_canvas()
            if hasattr(self, "hierarchy") and self.hierarchy:
                self.hierarchy.refresh()
            self.handle_selection_change_from_hierarchy(new_selection)
            self.show_snackbar("Objetos duplicados com sucesso!", is_error=False)

    def handle_undo(self):
        if self.pm.undo():
            self.canvas.selected_item_ids = []
            self.canvas.render_canvas()
            if hasattr(self, "hierarchy") and self.hierarchy:
                self.hierarchy.refresh()
            self.show_snackbar("Desfazer realizado.", is_error=False)
        else:
            self.show_snackbar("Nada para desfazer.", is_error=True)

    def handle_redo(self):
        if self.pm.redo():
            self.canvas.selected_item_ids = []
            self.canvas.render_canvas()
            if hasattr(self, "hierarchy") and self.hierarchy:
                self.hierarchy.refresh()
            self.show_snackbar("Refazer realizado.", is_error=False)
        else:
            self.show_snackbar("Nada para refazer.", is_error=True)

    def open_resize_canvas_modal(self):
        if not self.pm.is_loaded: return
        def do_resize(vals):
            try:
                w = float(vals[0] if len(vals) > 0 else self.pm.canvas_width)
                h = float(vals[1] if len(vals) > 1 else self.pm.canvas_height)
                self.pm.canvas_width = w
                self.pm.canvas_height = h
                self.pm.save_project()
                self.canvas.render_canvas()
                self.show_snackbar("Canvas redimensionado com sucesso!", is_error=False)
            except (ValueError, IndexError):
                self.show_snackbar("Valores inválidos.", is_error=True)
                
        modal = ExactInputModal("Redimensionar Canvas", {"Largura": str(self.pm.canvas_width), "Altura": str(self.pm.canvas_height)}, do_resize)
        self.page.overlay.append(modal)
        modal.open = True
        self.page.update()
