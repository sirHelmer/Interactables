import flet as ft

class ExactInputModal(ft.AlertDialog):
    def __init__(self, title, fields, on_confirm_callback):
        super().__init__()
        self.on_confirm_callback = on_confirm_callback
        self.title = ft.Text(title, size=16, weight=ft.FontWeight.W_600)
        self.modal = True
        
        self.text_fields = []
        for label, default_val in fields.items():
            tf = ft.TextField(label=label, value=str(default_val), width=150)
            self.text_fields.append(tf)
            
        self.content = ft.Column(
            controls=self.text_fields,
            width=200,
            height=65 * len(self.text_fields),
            spacing=10
        )
        
        self.actions = [
            ft.TextButton("Cancelar", on_click=self._cancel),
            ft.TextButton("Aplicar", on_click=self._confirm)
        ]
        self.actions_alignment = ft.MainAxisAlignment.END

    def _cancel(self, e):
        self.open = False
        self.page.update()

    def _confirm(self, e):
        values = [tf.value for tf in self.text_fields]
        self.open = False
        self.page.update()
        if self.on_confirm_callback:
            self.on_confirm_callback(values)
