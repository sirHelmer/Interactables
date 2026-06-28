import json
import zipfile
import os
import tempfile
import shutil
from .models import Presentation

def pack_project(presentation: Presentation, source_assets_dir: str, target_file: str) -> bool:
    """
    Salva a apresentação (json) e seus assets dentro de um arquivo ZIP (.tbs ou .int).
    """
    try:
        # Cria um diretório temporário para montar o pacote
        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. Salvar o JSON
            json_path = os.path.join(temp_dir, 'data.json')
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write(presentation.model_dump_json(indent=4))
            
            # 2. Copiar assets, se houver
            temp_assets_dir = os.path.join(temp_dir, 'assets')
            if os.path.exists(source_assets_dir) and os.listdir(source_assets_dir):
                shutil.copytree(source_assets_dir, temp_assets_dir)
            else:
                os.makedirs(temp_assets_dir, exist_ok=True)
            
            # 3. Compactar no arquivo final
            with zipfile.ZipFile(target_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Calcula o caminho relativo dentro do zip
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
                        
        return True
    except Exception as e:
        print(f"Erro ao empacotar projeto: {e}")
        return False

def unpack_project(file_path: str, extract_dir: str) -> Presentation:
    """
    Descompacta um pacote (.tbs ou .int) para um diretório e retorna o modelo Presentation.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
    # Descompacta o arquivo
    with zipfile.ZipFile(file_path, 'r') as zipf:
        zipf.extractall(extract_dir)
        
    json_path = os.path.join(extract_dir, 'data.json')
    if not os.path.exists(json_path):
        raise ValueError("O pacote não contém um arquivo data.json válido.")
        
    # Lê e converte de volta para o objeto Pydantic
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    return Presentation(**data)

