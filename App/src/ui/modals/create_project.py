import flet as ft

class CreateProjectModal(ft.AlertDialog):
    def __init__(self, on_create_callback, on_cancel_callback, file_picker=None):
        super().__init__()
        self.on_create_callback = on_create_callback
        self.on_cancel_callback = on_cancel_callback
        self.file_picker = file_picker
        
        self.title = ft.Text("Criar Novo Projeto", size=18, weight=ft.FontWeight.BOLD)
        self.modal = True
        
        self.input_name = ft.TextField(label="Nome do Projeto", value="MeuProjeto", autofocus=True)
        self.input_path = ft.TextField(label="Pasta de Armazenamento (Vazio = Documentos)", hint_text="C:\\\\Users\\\\...", expand=True)
        self.btn_pick_folder = ft.IconButton(icon=ft.Icons.FOLDER_OPEN, tooltip="Procurar Pasta", on_click=self._open_picker)
        self.input_width = ft.TextField(label="Largura Canvas (X)", value="1920", width=130)
        self.input_height = ft.TextField(label="Altura Canvas (Y)", value="1080", width=130)
        self.check_folders = ft.Checkbox(label="Criar estrutura básica (Images, Audios)", value=True)
        
        self.content = ft.Column(
            width=350,
            height=250,
            controls=[
                self.input_name,
                ft.Row([self.input_path, self.btn_pick_folder]),
                ft.Row([self.input_width, ft.Text("x"), self.input_height], alignment=ft.MainAxisAlignment.START),
                self.check_folders
            ],
            spacing=10
        )
        
        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cancel),
            ft.TextButton("Criar", on_click=self._create)
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def _open_picker(self, e):
        if self.file_picker:
            self.page.run_task(self._do_pick_folder)
            
    async def _do_pick_folder(self):
        path = await self.file_picker.get_directory_path(dialog_title="Selecione a Pasta do Projeto")
        if path:
            self.input_path.value = path
            self.input_path.update()

    def _cancel(self, e):
        self.open = False
        self.page.update()
        if self.on_cancel_callback:
            self.on_cancel_callback()

    def _create(self, e):
        # Validação simples
        try:
            w = int(self.input_width.value)
            h = int(self.input_height.value)
        except ValueError:
            w = 1920
            h = 1080
            
        self.open = False
        self.page.update()
        
        if self.on_create_callback:
            self.on_create_callback(
                self.input_name.value,
                self.input_path.value,
                w,
                h,
                self.check_folders.value
            )
