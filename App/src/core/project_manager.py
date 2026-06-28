import os
import json
import uuid
from pathlib import Path

class ProjectManager:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.is_loaded = False
        self.name = ""
        self.path = ""
        self.id = ""
        self.canvas_width = 1920
        self.canvas_height = 1080
        self.scene_items = []
        self.objects = {}
        self.history_stack = []
        self.history_index = -1
        self._is_undoing = False
        
    def create_project(self, name: str, base_path: str, width: int, height: int, create_folders: bool):
        # Se base_path for vazio, procura inteligentemente a pasta Documentos
        if not base_path.strip():
            home = Path.home()
            docs = home / "Documents"
            if not docs.exists():
                docs = home / "Documentos"
            # Checagem para usuários com OneDrive ativado
            if not docs.exists() and (home / "OneDrive" / "Documents").exists():
                docs = home / "OneDrive" / "Documents"
            elif not docs.exists() and (home / "OneDrive" / "Documentos").exists():
                docs = home / "OneDrive" / "Documentos"
            # Fallback final se nenhuma existir
            if not docs.exists():
                docs = home
            base_path = str(docs)
            
        self.reset()
        
        self.name = name if name.strip() else "Novo Projeto"
        self.path = os.path.join(base_path, self.name)
        self.canvas_width = width
        self.canvas_height = height
        self.id = str(uuid.uuid4())
        self.is_loaded = True
        
        # Cria a pasta física do projeto
        os.makedirs(self.path, exist_ok=True)
        os.makedirs(os.path.join(self.path, "Objects"), exist_ok=True)
        
        # Cria as pastas básicas se o checkbox foi marcado
        if create_folders:
            os.makedirs(os.path.join(self.path, "Images"), exist_ok=True)
            os.makedirs(os.path.join(self.path, "Audios"), exist_ok=True)
            
        # Cria arquivo de projeto básico
        self.save_project()
            
        return self.path

    def get_unique_instance_name(self, base_name):
        existing_names = [item.get("name") for item in self.scene_items if item.get("name")]
        if base_name not in existing_names:
            return base_name
        counter = 1
        while f"{base_name}_{counter}" in existing_names:
            counter += 1
        return f"{base_name}_{counter}"

    def get_or_create_object_for_asset(self, asset_ref: str, asset_type: str = "image"):
        # Busca se já existe um objeto para esse asset
        for obj_id, obj_data in self.objects.items():
            if obj_data.get("asset_ref") == asset_ref:
                return obj_id
                
        # Se não existe, cria um novo
        obj_id = str(uuid.uuid4())
        name = os.path.splitext(os.path.basename(asset_ref))[0]
        self.objects[obj_id] = {
            "id": obj_id,
            "name": name,
            "type": asset_type,
            "asset_ref": asset_ref,
            "base_properties": {},
            "instances": []
        }
        return obj_id

    def create_text_object(self, text_props):
        obj_id = str(uuid.uuid4())
        name = text_props.get("text", "Texto")[:15]
        self.objects[obj_id] = {
            "id": obj_id,
            "name": name,
            "type": "text",
            "base_properties": text_props,
            "instances": []
        }
        return obj_id
    def create_shape_object(self, shape_type, shape_props):
        obj_id = str(uuid.uuid4())
        
        # Traduz o tipo para um nome bonito
        names = {
            "rect": "Retângulo",
            "circle": "Círculo",
            "line": "Linha",
            "triangle": "Triângulo",
            "star": "Estrela"
        }
        name = names.get(shape_type, "Forma")
        
        self.objects[obj_id] = {
            "id": obj_id,
            "name": name,
            "type": "shape",
            "shape_type": shape_type,
            "base_properties": shape_props,
            "instances": []
        }
        return obj_id


    def save_project(self):
        if not self.is_loaded or not self.path:
            return
            
        import copy
        if not self._is_undoing:
            state = {
                "scene_items": copy.deepcopy(self.scene_items),
                "objects": copy.deepcopy(self.objects),
                "canvas_width": self.canvas_width,
                "canvas_height": self.canvas_height
            }
            # Remove anything after current index
            self.history_stack = self.history_stack[:self.history_index + 1]
            # Don't add if identical to current state (simple check based on str)
            if not self.history_stack or str(self.history_stack[-1]) != str(state):
                self.history_stack.append(state)
                self.history_index += 1
                if len(self.history_stack) > 30: # Limit history
                    self.history_stack.pop(0)
                    self.history_index -= 1
                    
        objects_dir = os.path.join(self.path, "Objects")
        os.makedirs(objects_dir, exist_ok=True)
        
        # 1. Agrupar scene_items por object_id
        # Limpa as instâncias antigas da memória dos objetos
        for obj in self.objects.values():
            obj["instances"] = []
            
        for item in self.scene_items:
            obj_id = item.get("object_id")
            if obj_id in self.objects:
                self.objects[obj_id]["instances"].append(item)
                
        # 2. Salvar cada objeto no seu JSON
        for obj_id, obj_data in self.objects.items():
            obj_file = os.path.join(objects_dir, f"{obj_id}.json")
            with open(obj_file, "w", encoding="utf-8") as f:
                json.dump(obj_data, f, indent=4)
                
        # 3. Salvar o project.json super leve
        data = {
            "id": self.id,
            "name": self.name,
            "canvases": [{"id": "default", "width": self.canvas_width, "height": self.canvas_height}],
            "objects_manifest": [f"{obj_id}.json" for obj_id in self.objects.keys()]
        }
        with open(os.path.join(self.path, "project.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def save_as(self, new_dir_path: str):
        if not self.is_loaded or not self.path:
            return False
            
        import shutil
        try:
            # Garante que as mudanças atuais estão salvas na pasta atual primeiro
            self.save_project()
            
            # Copia tudo para o novo diretório
            if os.path.exists(new_dir_path):
                # Se o diretório existe e não está vazio, pode ser um problema, mas o shutil.copytree falha se o destino existe.
                # Então, vamos criar um nome seguro ou usar dirs_exist_ok=True (Python 3.8+)
                shutil.copytree(self.path, new_dir_path, dirs_exist_ok=True)
            else:
                shutil.copytree(self.path, new_dir_path)
                
            self.path = new_dir_path
            self.name = os.path.basename(new_dir_path)
            
            # Atualiza o JSON no novo destino com o novo nome
            self.save_project()
            return True
        except Exception as e:
            print(f"Erro em save_as: {e}")
            return False

    def export_int(self, zip_filepath: str):
        if not self.is_loaded or not self.path:
            return False
        import shutil
        try:
            self.save_project()
            # shutil.make_archive cria zip, mas adiciona a extensão. 
            # zip_filepath já inclui '.int'. Vamos criar um zip com esse nome
            base_name = zip_filepath
            if base_name.endswith('.int'):
                base_name = base_name[:-4] # tira o .int para o make_archive, que vai por .zip
                
            out_zip = shutil.make_archive(base_name, 'zip', self.path)
            # Renomear de .zip para .int
            if os.path.exists(zip_filepath):
                os.remove(zip_filepath)
            os.rename(out_zip, zip_filepath)
            return True
        except Exception as e:
            print(f"Erro em export_int: {e}")
            return False

    def import_int(self, zip_filepath: str, extract_dir: str):
        import zipfile
        try:
            with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            self.load_project(extract_dir)
            return True
        except Exception as e:
            print(f"Erro em import_int: {e}")
            return False

    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self._apply_history_state()
            return True
        return False

    def redo(self):
        if self.history_index < len(self.history_stack) - 1:
            self.history_index += 1
            self._apply_history_state()
            return True
        return False

    def _apply_history_state(self):
        import copy
        state = self.history_stack[self.history_index]
        self.scene_items = copy.deepcopy(state["scene_items"])
        self.objects = copy.deepcopy(state["objects"])
        self.canvas_width = state["canvas_width"]
        self.canvas_height = state["canvas_height"]
        
        self._is_undoing = True
        self.save_project()
        self._is_undoing = False

    def load_project(self, path: str):
        proj_file = os.path.join(path, "project.json")
        if not os.path.exists(proj_file):
            return False
            
        try:
            with open(proj_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.id = data.get("id", str(uuid.uuid4()))
            self.name = data.get("name", os.path.basename(path))
            
            canvases = data.get("canvases", [])
            if canvases:
                self.canvas_width = canvases[0].get("width", 1920)
                self.canvas_height = canvases[0].get("height", 1080)
            else:
                self.canvas_width = data.get("canvas_width", 1920) # Fallback antigo
                self.canvas_height = data.get("canvas_height", 1080)
                
            self.path = path
            self.objects = {}
            self.scene_items = []
            
            # Carrega compatibilidade antiga
            old_scene_items = data.get("scene_items", [])
            
            objects_dir = os.path.join(path, "Objects")
            if os.path.exists(objects_dir):
                for manifest_file in data.get("objects_manifest", []):
                    obj_path = os.path.join(objects_dir, manifest_file)
                    if os.path.exists(obj_path):
                        with open(obj_path, "r", encoding="utf-8") as obj_f:
                            obj_data = json.load(obj_f)
                            self.objects[obj_data["id"]] = obj_data
                            self.scene_items.extend(obj_data.get("instances", []))
            
            # Migração automática de projetos antigos
            if old_scene_items and not self.scene_items:
                for item in old_scene_items:
                    # itens antigos tinham 'src', 'id', 'x', 'y'
                    obj_id = self.get_or_create_object_for_asset(item.get("src", ""))
                    new_instance = {
                        "instance_id": item.get("id"),
                        "object_id": obj_id,
                        "canvas_id": "default",
                        "x": item.get("x", 0),
                        "y": item.get("y", 0),
                        "z_index": len(self.scene_items),
                        "w": item.get("w"),
                        "h": item.get("h")
                    }
                    self.scene_items.append(new_instance)
                self.save_project() # Salva no novo formato
                
            # Ordenar scene_items por z_index
            self.scene_items.sort(key=lambda item: item.get("z_index", 0))
            
            # Garante que todos os objetos/items estão com o schema atualizado
            self._upgrade_project_schema()
            
            self.is_loaded = True
            return True
        except Exception as e:
            print(f"Erro ao carregar projeto: {e}")
            return False

    def _upgrade_project_schema(self):
        modified = False
        
        for obj_id, obj_data in self.objects.items():
            if "behaviors" not in obj_data:
                obj_data["behaviors"] = []
                modified = True
            
            if "base_properties" not in obj_data:
                obj_data["base_properties"] = {}
                modified = True
                
            if "type" not in obj_data:
                obj_data["type"] = "image"
                modified = True
                
        for idx, item in enumerate(self.scene_items):
            if "rotation" not in item:
                item["rotation"] = 0.0
                modified = True
            if "w" not in item:
                item["w"] = 100
                modified = True
            if "h" not in item:
                item["h"] = 100
                modified = True
            if "z_index" not in item:
                item["z_index"] = idx
                modified = True
            if "visible" not in item:
                item["visible"] = True
                modified = True
            if "name" not in item or not item["name"]:
                item["name"] = f"Objeto_{idx}"
                modified = True
                
        if modified:
            self.save_project()

    def handle_file_deleted(self, deleted_path: str):
        if not self.is_loaded: return False
        
        objects_to_delete = []
        try:
            rel_deleted_path = os.path.relpath(deleted_path, self.path)
            # Normaliza as barras para comparação
            rel_deleted_path = rel_deleted_path.replace('\\', '/')
            
            # 1. Verifica se o que foi deletado foi um objeto JSON ou se foi um asset (imagem)
            for obj_id, obj_data in self.objects.items():
                obj_file = f"Objects/{obj_id}.json"
                asset_ref = obj_data.get("asset_ref", "").replace('\\', '/')
                
                # Verifica se o arquivo ou a pasta pai foram deletados
                is_json_deleted = (rel_deleted_path == obj_file or obj_file.startswith(rel_deleted_path + '/'))
                is_asset_deleted = (rel_deleted_path == asset_ref or asset_ref.startswith(rel_deleted_path + '/'))
                
                if is_json_deleted or is_asset_deleted:
                    objects_to_delete.append(obj_id)
                    
            # 2. Deleta os objetos da RAM e suas instâncias
            if objects_to_delete:
                for obj_id in objects_to_delete:
                    if obj_id in self.objects:
                        del self.objects[obj_id]
                    
                    # Deleta arquivo físico do Objeto caso ele não tenha sido o alvo inicial da deleção
                    obj_file_path = os.path.join(self.path, "Objects", f"{obj_id}.json")
                    if os.path.exists(obj_file_path):
                        try:
                            os.remove(obj_file_path)
                        except:
                            pass
                            
                # Remove as instâncias do Canvas
                self.scene_items = [item for item in self.scene_items if item.get("object_id") not in objects_to_delete]
                
                # Salva o projeto
                self.save_project()
                return True # Retorna True se a cena foi alterada
        except Exception as e:
            print(f"Erro no handle_file_deleted: {e}")
            
        return False

    def export_int_package(self, output_dir=None):
        if not self.is_loaded or not self.path:
            return None
            
        self.save_project()
        
        import shutil
        if output_dir is None:
            output_dir = os.path.dirname(self.path)
            
        export_name = f"{self.name}.int"
        export_path = os.path.join(output_dir, export_name)
        
        temp_zip = shutil.make_archive(os.path.join(output_dir, self.name), 'zip', self.path)
        if os.path.exists(export_path):
            os.remove(export_path)
        os.rename(temp_zip, export_path)
        
        return export_path
