import flet as ft
from ui.layout import AppLayout
from core.db import init_db

def main(page: ft.Page):
    # Configurações iniciais da janela
    page.title = "Interactables - Editor"
    
    # Inicializa banco de dados local
    init_db()
    
    # Responsividade e Tema
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    
    # Instanciando o layout principal
    editor_layout = AppLayout()
    
    # Em versões 0.85+ o FilePicker é um Service e não um overlay control!
    page.services.append(editor_layout.file_picker)
    
    # Evento Global de Teclado (Para capturar Ctrl e Shift)
    def handle_keyboard(e: ft.KeyboardEvent):
        e.page.ctrl_pressed = e.ctrl
        e.page.shift_pressed = e.shift
        
        if hasattr(editor_layout, 'handle_keyboard'):
            editor_layout.handle_keyboard(e)
            
    page.on_keyboard_event = handle_keyboard
    
    page.add(editor_layout)

if __name__ == "__main__":
    # Rodando o aplicativo
    ft.run(main)
