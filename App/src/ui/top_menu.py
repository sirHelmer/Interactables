import flet as ft

class TopMenu(ft.Container):
    def __init__(self, on_view_toggle=None, on_create_project_click=None, on_open_project_click=None, on_recent_click=None, on_save_project_click=None, on_close_project_click=None, on_test_presentation_click=None, on_zoom_in_click=None, on_zoom_out_click=None, on_zoom_fit_click=None, on_duplicate_click=None, on_resize_canvas_click=None, on_undo_click=None, on_redo_click=None, on_open_int_click=None, on_save_as_click=None, on_auto_save_toggle=None):
        super().__init__()
        self.on_view_toggle = on_view_toggle
        self.on_create_project_click = on_create_project_click
        self.on_open_project_click = on_open_project_click
        self.on_recent_click = on_recent_click
        self.on_save_project_click = on_save_project_click
        self.on_close_project_click = on_close_project_click
        self.on_test_presentation_click = on_test_presentation_click
        self.on_zoom_in_click = on_zoom_in_click
        self.on_zoom_out_click = on_zoom_out_click
        self.on_zoom_fit_click = on_zoom_fit_click
        self.on_duplicate_click = on_duplicate_click
        self.on_resize_canvas_click = on_resize_canvas_click
        self.on_undo_click = on_undo_click
        self.on_redo_click = on_redo_click
        self.on_open_int_click = on_open_int_click
        self.on_save_as_click = on_save_as_click
        self.on_auto_save_toggle = on_auto_save_toggle
        self.bgcolor = ft.Colors.BLUE_GREY_900
        self.padding = 10
        self.height = 50
        
        # Menu Principal (estilo Barra de Menus)
        self.auto_save_item = ft.PopupMenuItem(icon=ft.Icons.CHECK_BOX_OUTLINE_BLANK, content=ft.Text("Auto Save"), on_click=self._toggle_auto_save)
        
        self.file_menu = ft.PopupMenuButton(
            content=ft.Text("Arquivo", color=ft.Colors.WHITE),
            items=[
                ft.PopupMenuItem(icon=ft.Icons.ADD_BOX, content=ft.Text("Criar Projeto"), on_click=lambda _: self.on_create_project_click() if self.on_create_project_click else None),
                ft.PopupMenuItem(icon=ft.Icons.FOLDER_OPEN, content=ft.Text("Abrir Pasta..."), on_click=lambda _: self.on_open_project_click() if self.on_open_project_click else None),
                ft.PopupMenuItem(icon=ft.Icons.UNARCHIVE, content=ft.Text("Abrir Projeto (.int)"), on_click=lambda _: self.on_open_int_click() if self.on_open_int_click else None),
                ft.PopupMenuItem(icon=ft.Icons.SAVE, content=ft.Text("Salvar Projeto"), on_click=lambda _: self.on_save_project_click() if self.on_save_project_click else None),
                ft.PopupMenuItem(icon=ft.Icons.SAVE_AS, content=ft.Text("Salvar Como..."), on_click=lambda _: self.on_save_as_click() if self.on_save_as_click else None),
                ft.PopupMenuItem(icon=ft.Icons.PRESENT_TO_ALL, content=ft.Text("Testar Apresentação"), on_click=lambda _: self.on_test_presentation_click() if self.on_test_presentation_click else None),
                ft.PopupMenuItem(content=ft.Divider(height=1)),
                ft.PopupMenuItem(icon=ft.Icons.HISTORY, content=ft.Text("Projetos Recentes..."), on_click=lambda _: self.on_recent_click() if self.on_recent_click else None),
                ft.PopupMenuItem(icon=ft.Icons.CLOSE, content=ft.Text("Fechar Projeto"), on_click=lambda _: self.on_close_project_click() if self.on_close_project_click else None),
                ft.PopupMenuItem(content=ft.Divider(height=1)),
                self.auto_save_item,
                ft.PopupMenuItem(icon=ft.Icons.EXIT_TO_APP, content=ft.Text("Sair"), on_click=self._quit_app),
            ]
        )
        
        self.edit_menu = ft.PopupMenuButton(
            content=ft.Text("Editar", color=ft.Colors.WHITE),
            items=[
                ft.PopupMenuItem(icon=ft.Icons.UNDO, content=ft.Text("Desfazer"), on_click=lambda _: self.on_undo_click() if self.on_undo_click else None),
                ft.PopupMenuItem(icon=ft.Icons.REDO, content=ft.Text("Refazer"), on_click=lambda _: self.on_redo_click() if self.on_redo_click else None),
                ft.PopupMenuItem(content=ft.Divider(height=1)),
                ft.PopupMenuItem(icon=ft.Icons.CONTROL_POINT_DUPLICATE, content=ft.Text("Duplicar Objeto (Ctrl+D)"), on_click=lambda _: self.on_duplicate_click() if self.on_duplicate_click else None),
                ft.PopupMenuItem(content=ft.Divider(height=1)),
                ft.PopupMenuItem(icon=ft.Icons.ASPECT_RATIO, content=ft.Text("Redimensionar Canvas"), on_click=lambda _: self.on_resize_canvas_click() if self.on_resize_canvas_click else None),
            ]
        )

        # Itens do Menu View controláveis
        self.view_menu_items = {
            "properties": ft.PopupMenuItem(icon=ft.Icons.CHECK, content=ft.Text("Painel Propriedades/Objetos"), on_click=lambda _: self._toggle("properties")),
            "project": ft.PopupMenuItem(icon=ft.Icons.CHECK, content=ft.Text("Painel de Projeto"), on_click=lambda _: self._toggle("project")),
            "toolbar": ft.PopupMenuItem(icon=ft.Icons.CHECK, content=ft.Text("Toolbar Flutuante"), on_click=lambda _: self._toggle("toolbar"))
        }

        # Menu de Visualização (View)
        self.view_menu = ft.PopupMenuButton(
            content=ft.Text("Visualizar", color=ft.Colors.WHITE),
            items=[
                self.view_menu_items["properties"],
                self.view_menu_items["project"],
                self.view_menu_items["toolbar"],
                ft.PopupMenuItem(content=ft.Divider(height=1)),
                ft.PopupMenuItem(icon=ft.Icons.ZOOM_IN, content=ft.Text("Zoom In"), on_click=lambda _: self.on_zoom_in_click() if self.on_zoom_in_click else None),
                ft.PopupMenuItem(icon=ft.Icons.ZOOM_OUT, content=ft.Text("Zoom Out"), on_click=lambda _: self.on_zoom_out_click() if self.on_zoom_out_click else None),
                ft.PopupMenuItem(icon=ft.Icons.FIT_SCREEN, content=ft.Text("Resetar Zoom/Fit View"), on_click=lambda _: self.on_zoom_fit_click() if self.on_zoom_fit_click else None),
            ]
        )

        self.content = ft.Row(
            controls=[
                ft.Icon(ft.Icons.TOUCH_APP, color=ft.Colors.BLUE_400),
                ft.Text("Interactables", weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE, size=16),
                ft.VerticalDivider(width=20, color=ft.Colors.TRANSPARENT),
                self.file_menu,
                self.edit_menu,
                self.view_menu,
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )

    def _toggle(self, name):
        if self.on_view_toggle:
            self.on_view_toggle(name)

    def _toggle_auto_save(self, e):
        # Altera o icone para simular checkbox
        is_active = False
        if self.auto_save_item.icon == ft.Icons.CHECK_BOX_OUTLINE_BLANK:
            self.auto_save_item.icon = ft.Icons.CHECK_BOX
            is_active = True
        else:
            self.auto_save_item.icon = ft.Icons.CHECK_BOX_OUTLINE_BLANK
        self.update()
        if self.on_auto_save_toggle:
            self.on_auto_save_toggle(is_active)

    async def _quit_app(self, e):
        # O Flet moderno requer que comandos de janela sejam awaitados para fechar o client Socket
        await self.page.window.close()
