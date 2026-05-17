# animations.py
from PyQt5.QtWidgets import QGraphicsPixmapItem, QFileDialog
from PyQt5.QtGui import QPixmap, QBrush, QPen
from PyQt5.QtCore import Qt, QTimer


class AnimationManager:
    def __init__(self, scene):
        self.scene = scene
        self.entity_animations = {}
        self.selected_item = None  # Entitatea selectată curent
        self.player_item = None    # Referință la jucător
        self.terrain_item = None
        self.terrain_image_path = None

    def set_selected_item(self, item):
        """Setează entitatea selectată curent"""
        self.selected_item = item
        
    def set_player_item(self, item):
        """Setează referința la jucător"""
        self.player_item = item

    def initialize_all_sprites(self):
        """Inițializează toate tipurile de sprite-uri pentru entitatea selectată"""
        if not self.selected_item:
            print("❌ Nicio entitate selectată")
            return
            
        print("🔧 Inițializare sprite-uri pentru entitatea selectată...")
        
        # Inițializează datele entității dacă nu există
        data = self.selected_item.data(0)
        if not isinstance(data, dict):
            data = {"sprites": {}, "facing": "down"}
            self.selected_item.setData(0, data)
        
        if "sprites" not in data:
            data["sprites"] = {}
            self.selected_item.setData(0, data)
        
        print("✅ Sprite-urile au fost inițializate")

    # === SPRITE LOADING FUNCTIONS ===
    
    def load_character_sprite(self):
        """Încarcă sprite-ul de caracter static"""
        self.setup_generic_sprite_or_animation(self.selected_item, "character")
    
    def load_movement_sprite(self):
        """Încarcă sprite-ul de mișcare (sprite sheet)"""
        if not self.selected_item:
            print("❌ Nicio entitate selectată")
            return
            
        files, _ = QFileDialog.getOpenFileNames(
            None, "Select Movement Sprite Sheet", "", "Images (*.png *.jpg *.bmp)")
        if not files:
            return
            
        sprite_path = files[0]
        self.setup_movement_animation(self.selected_item, sprite_path)
        
        # Salvează în datele entității
        data = self.selected_item.data(0)
        data["sprites"]["movement"] = files
        self.selected_item.setData(0, data)
    
    def load_attack_sprite(self):
        """Încarcă sprite-ul de atac generic"""
        self.load_attack_sprites("attack")
    
    def load_sword_attack_sprite(self):
        """Încarcă sprite-ul de atac cu sabia"""
        self.load_attack_sprites("sword")
    
    def load_bow_attack_sprite(self):
        """Încarcă sprite-ul de atac cu arcul"""
        self.load_attack_sprites("bow")
    
    def load_staff_attack_sprite(self):
        """Încarcă sprite-ul de atac cu toiagul"""
        self.load_attack_sprites("staff")
    
    def load_death_sprite(self):
        """Încarcă sprite-ul de moarte"""
        self.load_attack_sprites("death")

    # === SPRITE SWITCHING FUNCTIONS ===
    
    def switch_to_character_sprite(self):
        """Comută la sprite-ul de caracter"""
        if not self.selected_item:
            return
            
        data = self.selected_item.data(0)
        if not data or "sprites" not in data or "character" not in data["sprites"]:
            print("❌ Sprite-ul de caracter nu este încărcat")
            return
            
        # Oprește animațiile de mișcare
        if hasattr(self.selected_item, "movement_timer"):
            self.selected_item.movement_timer.stop()
            
        # Aplică sprite-ul de caracter
        sprite_path = data["sprites"]["character"][0]
        self.apply_static_sprite(self.selected_item, sprite_path)
        print("✅ Comutat la sprite-ul de caracter")
    
    def switch_to_movement_sprite(self):
        """Comută la sprite-ul de mișcare"""
        if not self.selected_item:
            return
            
        data = self.selected_item.data(0)
        if not data or "sprites" not in data or "movement" not in data["sprites"]:
            print("❌ Sprite-ul de mișcare nu este încărcat")
            return
            
        # Activează animația de mișcare
        if hasattr(self.selected_item, "movement_frames"):
            self.handle_movement_animation(self.selected_item, "down", True)
            print("✅ Comutat la sprite-ul de mișcare")
    
    def play_attack_animation(self, weapon_type="attack"):
        """Redă animația de atac"""
        if not self.selected_item:
            return
            
        data = self.selected_item.data(0)
        if not data or "sprites" not in data or weapon_type not in data["sprites"]:
            print(f"❌ Sprite-ul de {weapon_type} nu este încărcat")
            return
            
        self.play_attack_animation_with_sprite(weapon_type)
        print(f"✅ Redare animație {weapon_type}")
    
    def play_sword_attack(self):
        """Redă animația de atac cu sabia"""
        self.play_attack_animation("sword")
    
    def play_bow_attack(self):
        """Redă animația de atac cu arcul"""
        self.play_attack_animation("bow")
    
    def play_staff_attack(self):
        """Redă animația de atac cu toiagul"""
        self.play_attack_animation("staff")
    
    def play_death_animation_for_selected(self):
        """Redă animația de moarte pentru entitatea selectată"""
        if not self.selected_item:
            return
            
        self.play_death_animation(self.selected_item)

    # === UTILITY FUNCTIONS ===
    
    def apply_static_sprite(self, entity, sprite_path):
        """Aplică un sprite static pe entitate"""
        pixmap = QPixmap(sprite_path)
        if pixmap.isNull():
            print(f"❌ Sprite invalid: {sprite_path}")
            return
        
        # Elimină sprite-ul anterior
        if hasattr(entity, "sprite_item") and entity.sprite_item:
            self.scene.removeItem(entity.sprite_item)
        
        # Creează noul sprite
        sprite_item = QGraphicsPixmapItem()
        sprite_item.setZValue(2)
        self.scene.addItem(sprite_item)
        entity.sprite_item = sprite_item
        
        # Scalează și poziționează
        rect = entity.rect()
        scaled = pixmap.scaled(int(rect.width()), int(rect.height()), 
                              Qt.KeepAspectRatio, Qt.SmoothTransformation)
        sprite_item.setPixmap(scaled)
        self.center_sprite_on_entity(entity, sprite_item)
        
        # Ascunde entitatea originală
        entity.setBrush(QBrush(Qt.NoBrush))
        entity.setPen(QPen(Qt.NoPen))

    def get_sprite_status(self):
        """Returnează statusul sprite-urilor pentru entitatea selectată"""
        if not self.selected_item:
            return "Nicio entitate selectată"
        
        data = self.selected_item.data(0)
        if not data or "sprites" not in data:
            return "Niciun sprite încărcat"
        
        sprites = data["sprites"]
        loaded_sprites = list(sprites.keys())
        return f"Sprite-uri încărcate: {', '.join(loaded_sprites)}"

    # === ORIGINAL FUNCTIONS (îmbunătățite) ===
    
    def setup_generic_sprite_or_animation(self, entity, category="character"):
        if not entity:
            print("❌ Nicio entitate specificată")
            return
            
        files, _ = QFileDialog.getOpenFileNames(
            None, f"Select {category} Sprite(s)", "", "Images (*.png *.jpg *.bmp)")
        if not files:
            return

        sprite_path = files[0]
        pixmap = QPixmap(sprite_path)
        frame_w = 48

        is_sheet = pixmap.width() > frame_w and pixmap.width() % frame_w == 0

        if is_sheet:
            print(f"🟢 Sprite-sheet detectat pentru {category}, configurare animație de mișcare.")
            self.setup_movement_animation(entity, sprite_path)
        else:
            print(f"🟡 Imagine statică detectată pentru {category}, salvare ca sprite de caracter.")
            entity.character_sprite = pixmap
            self.apply_sprite_to_entity(entity, category, files)

    def center_sprite_on_entity(self, entity, sprite_item):
        rect = entity.rect()
        pixmap = sprite_item.pixmap()
        x = rect.x() + (rect.width() - pixmap.width()) / 2
        y = rect.y() + (rect.height() - pixmap.height()) / 2
        sprite_item.setPos(int(x), int(y))

    def setup_movement_animation(self, entity, sprite_path):
        pixmap = QPixmap(sprite_path)
        if pixmap.isNull():
            print(f"❌ Sprite de mișcare invalid: {sprite_path}")
            return

        frame_w, frame_h = 48, 48
        cols = pixmap.width() // frame_w
        rows = pixmap.height() // frame_h
        directions = ["down", "left", "right", "up"]
        frames = {d: [] for d in directions}

        if rows == 1:
            for c in range(cols):
                frame = pixmap.copy(c * frame_w, 0, frame_w, frame_h)
                for d in directions:
                    frames[d].append(frame)
        else:
            for r, d in enumerate(directions):
                if r >= rows:
                    break
                for c in range(cols):
                    frame = pixmap.copy(c * frame_w, r * frame_h, frame_w, frame_h)
                    frames[d].append(frame)

        # Elimină sprite-ul anterior
        if hasattr(entity, "sprite_item") and entity.sprite_item:
            self.scene.removeItem(entity.sprite_item)

        # Setup sprite_item
        sprite_item = QGraphicsPixmapItem()
        sprite_item.setZValue(2)
        self.scene.addItem(sprite_item)
        entity.sprite_item = sprite_item
        entity.setBrush(QBrush(Qt.NoBrush))
        entity.setPen(QPen(Qt.NoPen))

        rect = entity.rect()
        idle_pix = frames["down"][0]
        scaled = idle_pix.scaled(int(rect.width()), int(rect.height()), 
                                Qt.KeepAspectRatio, Qt.SmoothTransformation)
        sprite_item.setPixmap(scaled)
        self.center_sprite_on_entity(entity, sprite_item)

        # Salvează metadata
        entity.movement_frames = frames
        entity.movement_anim_idx = {d: 0 for d in directions}
        entity.current_direction = "down"
        entity.character_sprite = idle_pix

        # Timer pentru animație
        timer = QTimer()
        entity.movement_timer = timer

        def advance_frame():
            d = entity.current_direction
            idx = entity.movement_anim_idx[d]
            run_frames = frames[d][1:] if len(frames[d]) > 1 else frames[d]
            pix = run_frames[idx % len(run_frames)]
            entity.movement_anim_idx[d] = (idx + 1) % len(run_frames)
            scaled = pix.scaled(int(rect.width()), int(rect.height()), 
                               Qt.KeepAspectRatio, Qt.SmoothTransformation)
            sprite_item.setPixmap(scaled)
            self.center_sprite_on_entity(entity, sprite_item)

        timer.timeout.connect(advance_frame)
        timer.setInterval(90)

        print("✅ Animația de mișcare a fost configurată.")

    def apply_sprite_to_entity(self, entity, category, files):
        if not files or not entity:
            return

        data = entity.data(0)
        if not isinstance(data, dict):
            data = {"sprites": {}}

        if "sprites" not in data:
            data["sprites"] = {}
        data["sprites"][category] = files
        entity.setData(0, data)

        sprite_path = files[0]
        rect = entity.rect()

        frames = self.extract_frames_from_sheet(sprite_path, 48, 48)

        # Elimină sprite anterior
        if hasattr(entity, "sprite_item") and entity.sprite_item:
            self.scene.removeItem(entity.sprite_item)

        sprite_anim = QGraphicsPixmapItem()
        sprite_anim.setZValue(2)
        self.scene.addItem(sprite_anim)
        entity.sprite_item = sprite_anim
        entity.setBrush(QBrush(Qt.NoBrush))
        entity.setPen(QPen(Qt.NoPen))

        if len(frames) > 1:
            animation_index = [0]

            def update_frame():
                pixmap = frames[animation_index[0] % len(frames)]
                scaled = pixmap.scaledToHeight(int(rect.height()), Qt.SmoothTransformation)
                sprite_anim.setPixmap(scaled)
                pos_x = rect.x() + (rect.width() - scaled.width()) / 2
                pos_y = rect.y() + (rect.height() - scaled.height()) / 2
                sprite_anim.setPos(int(pos_x), int(pos_y))
                animation_index[0] += 1

            timer = QTimer()
            timer.timeout.connect(update_frame)
            timer.start(80)

            self.entity_animations[entity] = (sprite_anim, timer)
        else:
            scaled = frames[0].scaledToHeight(int(rect.height()), Qt.SmoothTransformation)
            sprite_anim.setPixmap(scaled)
            pos_x = rect.x() + (rect.width() - scaled.width()) / 2
            pos_y = rect.y() + (rect.height() - scaled.height()) / 2
            sprite_anim.setPos(int(pos_x), int(pos_y))

    def handle_movement_animation(self, entity, direction, moving=True):
        if not entity or not hasattr(entity, "movement_frames"):
            return

        frames = entity.movement_frames.get(direction)
        if not frames:
            return

        sprite_item = getattr(entity, "sprite_item", None)
        if not sprite_item or not isinstance(sprite_item, QGraphicsPixmapItem):
            sprite_item = QGraphicsPixmapItem()
            sprite_item.setZValue(2)
            self.scene.addItem(sprite_item)
            entity.sprite_item = sprite_item

        rect = entity.rect()

        if moving:
            timer = entity.movement_timer
            index = [1]

            def advance():
                frame = frames[index[0] % len(frames)]
                index[0] += 1
                scaled = frame.scaled(int(rect.width()), int(rect.height()), 
                                     Qt.KeepAspectRatio, Qt.SmoothTransformation)
                sprite_item.setPixmap(scaled)
                self.center_sprite_on_entity(entity, sprite_item)

            timer.stop()
            try:
                timer.timeout.disconnect()
            except:
                pass
            timer.timeout.connect(advance)
            timer.start(100)
            advance()
        else:
            if hasattr(entity, "movement_timer"):
                entity.movement_timer.stop()

            pix = getattr(entity, "character_sprite", frames[0])
            scaled = pix.scaled(int(rect.width()), int(rect.height()), 
                               Qt.KeepAspectRatio, Qt.SmoothTransformation)
            sprite_item.setPixmap(scaled)
            self.center_sprite_on_entity(entity, sprite_item)

    def load_attack_sprites(self, weapon_type):
        if not self.selected_item:
            print("❌ Nicio entitate selectată")
            return
            
        files, _ = QFileDialog.getOpenFileNames(
            None, f"Select {weapon_type} attack sprites", "", "Images (*.png *.jpg *.bmp)")
        if not files:
            return

        data = self.selected_item.data(0)
        if not isinstance(data, dict):
            data = {"sprites": {}}
            self.selected_item.setData(0, data)

        if "sprites" not in data:
            data["sprites"] = {}
        data["sprites"][weapon_type] = files
        self.selected_item.setData(0, data)
        print(f"✅ {weapon_type} attack sprite(s) setat:", files[0])

    def play_attack_animation_with_sprite(self, weapon_type):
        entity = self.selected_item or self.player_item
        if not entity:
            print("❌ Nicio entitate disponibilă pentru animația de atac")
            return

        data = entity.data(0)
        if not data:
            print("❌ Datele entității nu sunt disponibile")
            return
            
        facing = data.get("facing", "down")
        sprites = data.get("sprites", {})
        
        if weapon_type not in sprites:
            print(f"❌ Nu există sprite pentru atacul cu {weapon_type}")
            return

        sprite_path = sprites[weapon_type][0]
        frames = self.extract_frames_from_sheet(sprite_path, 48, 48)
        if not frames:
            print("❌ Nu s-au putut extrage frame-urile")
            return

        attack_sprite = QGraphicsPixmapItem()
        attack_sprite.setZValue(9)
        self.scene.addItem(attack_sprite)

        px, py = entity.rect().x(), entity.rect().y()
        size = entity.rect().width()
        dx = dy = 0

        if facing == "up": dy = -size
        elif facing == "down": dy = size
        elif facing == "left": dx = -size
        elif facing == "right": dx = size

        pos_x = px + dx
        pos_y = py + dy
        attack_sprite.setPos(pos_x, pos_y)

        index = [0]

        def update_frame():
            if index[0] >= len(frames):
                self.scene.removeItem(attack_sprite)
                timer.stop()
                return

            frame = frames[index[0]]
            scaled = frame.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            attack_sprite.setPixmap(scaled)
            index[0] += 1

        timer = QTimer()
        timer.timeout.connect(update_frame)
        timer.start(80)

    def play_death_animation(self, entity_item):
        if not entity_item:
            return

        data = entity_item.data(0)
        if not data:
            print("❌ Datele entității nu sunt disponibile")
            return
            
        sprites = data.get("sprites", {})
        if "death" not in sprites:
            print("❌ Nu există sprite de moarte pentru această entitate")
            return

        sprite_path = sprites["death"][0]
        frames = self.extract_frames_from_sheet(sprite_path, 48, 48)
        if not frames:
            print("❌ Nu s-au putut extrage frame-urile pentru animația de moarte")
            return

        death_sprite = QGraphicsPixmapItem()
        death_sprite.setZValue(20)
        self.scene.addItem(death_sprite)

        rect = entity_item.rect()
        size = rect.width()
        pos_x = rect.x()
        pos_y = rect.y()
        death_sprite.setPos(pos_x, pos_y)

        index = [0]

        def update_frame():
            if index[0] >= len(frames):
                self.scene.removeItem(death_sprite)
                timer.stop()
                return

            frame = frames[index[0]]
            scaled = frame.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            death_sprite.setPixmap(scaled)
            index[0] += 1

        timer = QTimer()
        timer.timeout.connect(update_frame)
        timer.start(100)

    def extract_frames_from_sheet(self, sprite_path, frame_width=48, frame_height=48):
        pixmap = QPixmap(sprite_path)
        frames = []

        if pixmap.width() > frame_width and pixmap.width() % frame_width == 0 and pixmap.height() == frame_height:
            cols = pixmap.width() // frame_width
            for col in range(cols):
                x = col * frame_width
                frame = pixmap.copy(x, 0, frame_width, frame_height)
                frames.append(frame)
        else:
            frames = [pixmap]

        return frames

    def sync_sprite_position(self, entity):
        sprite = getattr(entity, "sprite_item", None)
        if not sprite:
            return
        rect = entity.rect()
        pix = sprite.pixmap()
        pos_x = rect.x() + (rect.width() - pix.width()) / 2
        pos_y = rect.y() + (rect.height() - pix.height()) / 2
        sprite.setPos(int(pos_x), int(pos_y))

    # === TERRAIN FUNCTIONS ===
    
    def insert_terrain_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            None, "Select Terrain Image", "", "Images (*.png *.jpg *.bmp)")
        if not file_path:
            return
        self.insert_terrain_image_from_path(file_path)

    def insert_terrain_image_from_path(self, file_path):
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            print("❌ Calea imaginii de teren este invalidă")
            return

        width = int(self.scene.width())
        height = int(self.scene.height())
        scaled = pixmap.scaled(width, height, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        if hasattr(self, "terrain_item") and self.terrain_item and self.terrain_item.scene():
            self.scene.removeItem(self.terrain_item)

        self.terrain_item = QGraphicsPixmapItem(scaled)
        self.terrain_item.setZValue(-1)
        self.terrain_item.setPos(0, 0)
        self.scene.addItem(self.terrain_item)
        self.terrain_image_path = file_path
        print("✅ Imaginea de teren a fost restaurată")
    def rebuild_movement_animation(self, entity, sprite_path):
        """Reconstruiește animația de mișcare din sprite-sheet"""
        self.setup_movement_animation(entity, sprite_path)
