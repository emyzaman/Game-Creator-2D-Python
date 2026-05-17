
import json
from PyQt5.QtWidgets import QFileDialog, QGraphicsRectItem, QGraphicsPixmapItem
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtCore import Qt

GRID_SIZE = 32

class SceneManager:
    def __init__(self, scene, entity_manager, entity_list_widget, animation_manager):
        self.scene = scene
        self.entity_manager = entity_manager
        self.entity_list_widget = entity_list_widget
        self.animation_manager = animation_manager
        self.dead_tiles = []
        self.dead_positions = set()
        self.terrain_image_path = None
        self.view = None

    def save_scene(self):
        filename, _ = QFileDialog.getSaveFileName(None, "Save Scene", "", "JSON Files (*.json)")
        if not filename:
            return

        # --- Metadata scenă ---
        scene_metadata = {
            "grid_size": GRID_SIZE,
            "grid_cols": getattr(self, "grid_cols", 20),
            "grid_rows": getattr(self, "grid_rows", 15),
            "dead_tiles": list(getattr(self, "dead_positions", set())),  # Listă de tuple (x, y)
            "terrain_image": self.terrain_image_path if self.terrain_image_path else None
            
        }

        # --- Entități ---
        scene_data = []
        for item in self.scene.items():
            if not isinstance(item, QGraphicsRectItem):
                continue

            rect = item.rect()
            x = int(rect.x())
            y = int(rect.y())
            w = int(rect.width())
            h = int(rect.height())

            data = item.data(0)
            if not isinstance(data, dict):
                continue

            attributes = dict(data)  # Copie pentru siguranță

            # Serializare specială pentru sprite-uri (salvează lista de fișiere/path-uri)
            if "sprites" in attributes:
                new_sprites = {}
                for k, v in attributes["sprites"].items():
                    if isinstance(v, list):
                        new_sprites[k] = v.copy()
                    elif isinstance(v, dict):
                        # Pentru movement sprite-sheet: {'path': ..., ...}
                        new_sprites[k] = dict(v)
                    else:
                        new_sprites[k] = v
                attributes["sprites"] = new_sprites

            # Serializare pentru coordonate complexe (waypoints, checkpoints, etc.)
            for key in ["waypoints", "checkpoints"]:
                if key in attributes:
                    attributes[key] = [(int(a), int(b)) for (a, b) in attributes[key]]
            for key in ["start_point", "final_point"]:
                if key in attributes and attributes[key] is not None:
                    attributes[key] = tuple(map(int, attributes[key]))

            # Custom items din inventar
            if "custom_items" in attributes:
                #  Asigurare că toate valorile din custom_items sunt serializabile
                attributes["custom_items"] = {
                    str(k): dict(v) if isinstance(v, dict) else v
                    for k, v in attributes["custom_items"].items()
                }
            # Echipament echipat
            for eq in [k for k in attributes if k.startswith("equipped_")]:
                attributes[eq] = attributes[eq]

            # Orice altceva (ex: dialog_text, inventory, item_types, etc.)
            # nu are nevoie de procesare specială

            scene_data.append({
                "x": x,
                "y": y,
                "width": w,
                "height": h,
                "attributes": attributes
            })
        for tile in self.dead_tiles:
            if not tile: continue
            rect = tile.rect()
            scene_data.append({
                "x": int(rect.x()),
                "y": int(rect.y()),
                "width": 1,
                "height": 1,
                "attributes": {"type": "DeadTile"}
            })
        #
        final_data = {
            "metadata": scene_metadata,
            "objects": scene_data
        }

        with open(filename, 'w') as f:
            json.dump(final_data, f, indent=4)

        print(f"✅ Scene saved to {filename}")


    def load_scene_from_path(self, path):
        try:
            with open(path, 'r') as f:
                raw = json.load(f)

            # --- 1. Citește metadata ---
            if isinstance(raw, dict):
                metadata = raw.get("metadata", {})
                scene_data = raw.get("objects", [])
            elif isinstance(raw, list):  # fallback compatibilitate veche
                metadata = {}
                scene_data = raw
            else:
                print(f"❌ Format fișier invalid: {type(raw)}")
                return

            # --- 2. Restore grid/dimensiuni/dead tiles/terrain ---
            grid_size = metadata.get("grid_size", GRID_SIZE)
            grid_cols = metadata.get("grid_cols", 20)
            grid_rows = metadata.get("grid_rows", 15)
            dead_tiles = metadata.get("dead_tiles", [])
            terrain_img = metadata.get("terrain_image", None)

            # Setează scena la dimensiunea corectă
            self.scene.setSceneRect(0, 0, grid_size * grid_cols, grid_size * grid_rows)
            if hasattr(self, "grid_cols"): self.grid_cols = grid_cols
            if hasattr(self, "grid_rows"): self.grid_rows = grid_rows

            # Resetare UI pentru tiles "moarte"
            if hasattr(self, "dead_tiles"): self.dead_tiles.clear()
            if hasattr(self, "dead_positions"): self.dead_positions.clear()
            # Șterge tot din scenă și liste UI
            self.scene.clear()
            self.entity_list_widget.clear()
            self.entity_manager.entity_counters = {key: 0 for key in self.entity_manager.entity_counters.keys()}
            self.entity_manager.player_item = None

            # --- 3. Replasează tiles moarte dacă există ---
            for pos in dead_tiles:
                x, y = pos if isinstance(pos, (list, tuple)) else (pos['x'], pos['y'])
                rect = QGraphicsRectItem(x, y, grid_size, grid_size)
                rect.setBrush(QBrush(QColor(80, 80, 80, 120)))  # semitransparent
                rect.setZValue(-5)
                rect.setData(0, {"type": "DeadTile"})  # ✅ obstacol logic
                rect.hide()  # 🔒 ascuns implicit
                self.scene.addItem(rect)
                self.dead_tiles.append(rect)
                self.dead_positions.add((x, y))

            # --- 4. Reîncarcă imagine teren dacă e cazul ---
            if terrain_img and hasattr(self.animation_manager, "insert_terrain_image_from_path"):
                self.animation_manager.insert_terrain_image_from_path(terrain_img)
                self.terrain_image_path = terrain_img

            # --- 5. Recreează fiecare entitate cu toate datele ei ---
            for obj in scene_data:
                if not isinstance(obj, dict):
                    continue
                x = obj.get("x", 0)
                y = obj.get("y", 0)
                attributes = obj.get("attributes", {})
                w = attributes.get("width", 1)
                h = attributes.get("height", 1)

                # Fix pentru sprite-uri: convertim orice dict cu path-uri
                if "sprites" in attributes:
                    new_sprites = {}
                    for k, v in attributes["sprites"].items():
                        if isinstance(v, list):
                            new_sprites[k] = v
                        elif isinstance(v, dict):
                            new_sprites[k] = dict(v)
                        else:
                            new_sprites[k] = v
                    attributes["sprites"] = new_sprites

                # Fix pentru waypoints/checkpoints
                for key in ["waypoints", "checkpoints"]:
                    if key in attributes and isinstance(attributes[key], list):
                        attributes[key] = [tuple(xy) for xy in attributes[key]]

                for key in ["start_point", "final_point"]:
                    if key in attributes and isinstance(attributes[key], (list, tuple)):
                        attributes[key] = tuple(attributes[key])

                # Creează entitatea în scenă cu toate datele
                entity = self.entity_manager.create_entity(x, y, attributes)
                # HP bar dacă e nevoie
                if attributes.get("type") in ["PlayerRPG", "Enemy"]:
                    hp = attributes.get("hp", 100)
                    hp_bar = QGraphicsRectItem(x, y - 7, grid_size * w, 5)
                    hp_bar.setBrush(QBrush(QColor("red")))
                    self.scene.addItem(hp_bar)
                    entity.setData(1, hp_bar)

                # Sprite-uri (se aplică la fiecare categorie, cu lista de path-uri)
                sprites = attributes.get("sprites", {})
                for category, sprite_data in sprites.items():
                    if category == "movement" and isinstance(sprite_data, (list, dict)):
                        # Sprite sheet — folosește primul path din listă sau "path" din dict
                        if isinstance(sprite_data, dict) and "path" in sprite_data:
                            self.animation_manager.setup_movement_animation(entity, sprite_data["path"])
                        elif isinstance(sprite_data, list) and sprite_data:
                            self.animation_manager.setup_movement_animation(entity, sprite_data[0])
                    elif isinstance(sprite_data, list) and sprite_data:
                        self.animation_manager.apply_sprite_to_entity(entity, category, sprite_data)

            self.animation_manager.player_item = self.entity_manager.get_player_item()
            print(f"✅ Scene loaded from {path}")

            # RESETARE SELECTIE
            self.selected_item = None
            self.entity_list_widget.clearSelection()

        except Exception as e:
            import traceback
            print(f"❌ Failed to load scene: {e}")
            traceback.print_exc()


    def load_scene(self):
        filename, _ = QFileDialog.getOpenFileName(None, "Load Scene", "", "JSON Files (*.json)")
        if not filename:
            return

        self.load_scene_from_path(filename)

        # Reset UI selection, focus, etc.
        self.selected_item = None
        if hasattr(self.entity_list_widget, "clearSelection"):
            self.entity_list_widget.clearSelection()

        # Reselectează orice entitate la click, ca la entitățile noi
        def on_entity_clicked(item):
            entity = item.data(Qt.UserRole)
            if entity:
                self.select_item(item)

        # (Optional) Reinițializează UI-ul pentru proprietăți/inventar ca să fie corect la primul click
        if hasattr(self, "properties_widget"):
            self.properties_widget.setVisible(False)
        if hasattr(self, "inventory_widget"):
            self.inventory_widget.setVisible(False)

        print("✅ Scene loaded, all entities are now editable.")
