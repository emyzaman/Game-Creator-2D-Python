from tkinter import Scale
from PyQt5.QtWidgets import  QDialog, QVBoxLayout, QLabel, QComboBox, QGraphicsTextItem, QComboBox ,QSpinBox,QGraphicsPixmapItem, QListWidgetItem, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QListWidget, QGraphicsScene, QGraphicsView, QGraphicsRectItem, QFormLayout, QLabel, QLineEdit, QCheckBox, QFileDialog, QInputDialog
from PyQt5.QtCore import Qt, QRectF, QTimer, QEvent
from PyQt5.QtGui import QBrush, QColor, QPixmap, QTransform, QPen, QIcon
import json
import random
import heapq
from entities import EntityManager, ENTITY_TYPES, PREDEFINED_ITEMS
from animations import AnimationManager
from scenes import SceneManager
GRID_SIZE = 32
SCENE_WIDTH = 20
SCENE_HEIGHT = 15
class CreatedEntitiesList(QListWidget):
    def __init__(self):
        super().__init__()
        self.setSelectionMode(QListWidget.SingleSelection)

class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scale_factor = 1.0

    def wheelEvent(self, event):
        zoom_in = 1.1
        zoom_out = 1 / zoom_in

        if event.angleDelta().y() > 0 and self.scale_factor < 4.0:
            factor = zoom_in
        elif event.angleDelta().y() < 0 and self.scale_factor > 0.2:
            factor = zoom_out
        else:
            return

        self.scale_factor *= factor
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.scale(factor, factor)




class GameEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("No-Code 2D Game Editor")
        self.setGeometry(100, 100, 1000, 600)

        # --- Config grid/scenă ---
        self.inputs = {}
        self.grid_cols = 20
        self.grid_rows = 15
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, GRID_SIZE * self.grid_cols, GRID_SIZE * self.grid_rows)
        try:
            self.scene.selectionChanged.disconnect()
        except TypeError:
            pass

        self.view = ZoomableGraphicsView(self.scene)
        self.view.setMouseTracking(True)
        self.view.setFocusPolicy(Qt.StrongFocus)
        self.view.setFocus()

        # --- Managers ---
        self.animation_manager = AnimationManager(self.scene)
        self.entity_list_widget = CreatedEntitiesList()
        self.entity_manager = EntityManager(self.scene, self.entity_list_widget)
        self.scene_manager = SceneManager(self.scene, self.entity_manager, self.entity_list_widget, self.animation_manager)
        self.scene_manager.view = self.view

        # --- Butoane principale și controale grid ---
        self.save_button = QPushButton("Save Scene")
        self.save_button.clicked.connect(self.scene_manager.save_scene)
        self.load_button = QPushButton("Load Scene")
        self.load_button.clicked.connect(self.scene_manager.load_scene)
        self.selected_item = None
        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self.activate_delete_mode)
        self.copy_button = QPushButton("Copy")
        self.copy_button.clicked.connect(self.activate_copy_mode)
        self.marking_dead = False
        self.dead_tiles = []

        self.grid_toggle = QCheckBox("Show Grid")
        self.grid_toggle.setChecked(False)
        self.grid_toggle.stateChanged.connect(self.toggle_grid)

        self.mark_dead_button = QPushButton("Mark Dead Terrain")
        self.mark_dead_button.setCheckable(True)
        self.mark_dead_button.clicked.connect(self.toggle_dead_mode)

        self.grid_width_input = QSpinBox()
        self.grid_width_input.setMinimum(1)
        self.grid_width_input.setValue(20)
        self.grid_height_input = QSpinBox()
        self.grid_height_input.setMinimum(1)
        self.grid_height_input.setValue(15)
        self.grid_width_input.valueChanged.connect(self.update_grid_size)
        self.grid_height_input.valueChanged.connect(self.update_grid_size)
        self.selected_item = None
        self.grid_width_input.setEnabled(True)
        self.grid_height_input.setEnabled(True)

        # --- Top Buttons Layout ---
        top_buttons = QHBoxLayout()
        top_buttons.addWidget(self.mark_dead_button)
        top_buttons.addWidget(self.grid_toggle)
        top_buttons.addWidget(QLabel("Tile W:"))
        top_buttons.addWidget(self.grid_width_input)
        top_buttons.addWidget(QLabel("H:"))
        top_buttons.addWidget(self.grid_height_input)
        top_buttons.addWidget(self.delete_button)
        top_buttons.addWidget(self.copy_button)
        top_buttons.addWidget(self.save_button)
        top_buttons.addWidget(self.load_button)
         
        self.reset_button = QPushButton("Reset Grid")
        self.reset_button.clicked.connect(self.reset_grid)
        top_buttons.addWidget(self.reset_button)

        self.play_scene_checkbox = QCheckBox("Play Scene")
        self.play_scene_checkbox.setChecked(False)
        self.play_scene_checkbox.stateChanged.connect(self.toggle_play_mode)
        top_buttons.addWidget(self.play_scene_checkbox)

        self.stop_reset_button = QPushButton("Stop & Reset Scene")
        self.stop_reset_button.clicked.connect(self.reset_to_saved_scene)
        top_buttons.addWidget(self.stop_reset_button)

        self.export_button = QPushButton("Export")
        self.export_button.clicked.connect(self.export_game_to_exe)
        top_buttons.addWidget(self.export_button)

        self.current_entity = "Player"

        # --- Inițializări suplimentare ---
        self.entity_list_widget.setMaximumHeight(9999)
        self.entity_list_widget.itemClicked.connect(self.select_item)

        self.properties_form = QFormLayout()
        self.properties_widget = QWidget()
        self.properties_widget.setLayout(self.properties_form)

        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self.on_entity_selected)

        self.inventory_label = QLabel("Inventory:")
        self.inventory_display = QListWidget()
        self.inventory_display.itemClicked.connect(self.equip_or_swap_inventory_item)
        self.inventory_display.setContextMenuPolicy(Qt.CustomContextMenu)
        self.inventory_display.customContextMenuRequested.connect(self.handle_inventory_context_menu)

        self.inventory_box = QVBoxLayout()
        self.inventory_box.addWidget(self.inventory_label)
        self.inventory_box.addWidget(self.inventory_display)

        self.inventory_widget = QWidget()
        self.inventory_widget.setLayout(self.inventory_box)

        # --- Entity list & categories ---
        self.entity_list = QListWidget()
        self.entity_categories = {
            "🎮 Action RPG": ["PlayerRPG", "Enemy", "NPC", "Collectible", "Obstacle", "Chest", "Door"],
            "🔫 Shooter": ["PlayerShooter", "Bullet", "WeaponPickup", "AmmoPickup", "Explosion", "SpawnPoint"],
            "🧩 Puzzle": ["PlayerPuzzle", "Box", "TargetSpot", "Wall", "Switch", "Gate"],
            "🏎 Racing": ["PlayerRacing", "AICar", "TrackBoundary", "Checkpoint", "Boost", "FinishLine"],
            "📖 Narrative": ["PlayerNarrative", "DialogTrigger", "Item", "CutsceneTrigger", "ChoicePoint"],
            "🛡 Tower Defense": ["PathEnemy", "Tower", "Waypoint", "Base", "UpgradeItem"]
        }
        self.category_selector = QComboBox()
        self.category_selector.addItem("Toate")
        self.category_selector.addItems(self.entity_categories.keys())
        self.category_selector.currentTextChanged.connect(self.update_entity_list)
        self.category_selector.currentTextChanged.connect(self.sync_player_game_mode)
        self.entity_list.currentItemChanged.connect(self.handle_entity_item_changed)
        self.update_entity_list("Toate")
        self.delete_mode = False
        self.copy_mode = False
        self.copied_entity_data = None

        for category, entities in self.entity_categories.items():
            self.entity_list.addItem(category)
            for name in entities:
                self.entity_list.addItem(f"  {name}")

        self.entity_list.addItem("Insert Terrain")

        # --- Sidebar (stânga) ---
        sidebar = QVBoxLayout()
        sidebar.addWidget(self.category_selector)
        sidebar.addWidget(self.entity_list)
        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar)
        sidebar_widget.setFixedWidth(220)

        # --- Right Panel (dreapta) ---
        right_panel = QVBoxLayout()
        entities_label = QLabel("Entity List:")
        entities_label.setStyleSheet("font-weight: bold;")
        right_panel.addWidget(entities_label)
        self.entity_list_widget.setMaximumHeight(150)
        right_panel.addWidget(self.entity_list_widget)
        self.properties_widget.setVisible(False)
        right_panel.addWidget(self.properties_widget)
        self.inventory_widget.setVisible(False)
        right_panel.addWidget(self.inventory_widget)
        right_panel_widget = QWidget()
        right_panel_widget.setLayout(right_panel)
        right_panel_widget.setFixedWidth(280)

        # --- Layout principal ---
        layout = QHBoxLayout()
        layout.addWidget(sidebar_widget)
        layout.addWidget(self.view)
        layout.addWidget(right_panel_widget)
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_buttons)
        main_layout.addLayout(layout)
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # --- Restul inițializărilor specifice gameplay ---
        self.behavior_timer = QTimer()
        self.behavior_timer.timeout.connect(self.update_behaviors)
        self.behavior_timer.setInterval(100)
        # self.behavior_timer.start(100)  # dacă vrei să ruleze automat

        self.animation_manager.terrain_item = None
        self.animation_manager.terrain_image_path = None
        self.apply_sprite_to_entity = self.animation_manager.apply_sprite_to_entity
        self.play_attack_animation_with_sprite = self.animation_manager.play_attack_animation_with_sprite
        self.play_death_animation = self.animation_manager.play_death_animation
        self.load_attack_sprites = self.animation_manager.load_attack_sprites
        self.insert_terrain_image = self.animation_manager.insert_terrain_image
        self.insert_terrain_image_from_path = self.animation_manager.insert_terrain_image_from_path
        self.extract_frames_from_sheet = self.animation_manager.extract_frames_from_sheet

        self.entity_animations = {}
        self.player_item = self.entity_manager.get_player_item()
        self.view.mousePressEvent = self.place_entity

        self.setup_enemy_properties()
        self.behavior_types = ["idle", "hostile", "patrol"]
        self.dead_tiles = []
        self.dead_positions = set()
        self.view.viewport().installEventFilter(self)
        self._arrow_direction = None
        self.player_item = None


    def place_entity(self, event):
        pos = self.view.mapToScene(event.pos())
        if self.marking_dead:
            x = int(pos.x() // GRID_SIZE) * GRID_SIZE
            y = int(pos.y() // GRID_SIZE) * GRID_SIZE
            tile_pos = (x, y)

            if tile_pos in self.dead_positions:
                print("❌ Dead terrain already exists at this position.")
                return
           
            rect = QGraphicsRectItem(x, y, GRID_SIZE, GRID_SIZE)
            rect.setBrush(QBrush(QColor(80, 80, 80, 120)))  # semitransparent
            rect.setZValue(-5)
            rect.setData(0, {"type": "DeadTile"})  # ✅ tip logic
            rect.hide()  # 🔒 vizibil doar când butonul e apăsat
            self.scene.addItem(rect)
            self.dead_tiles.append(rect)
            self.dead_positions.add(tile_pos)
            print(f"✅ Marked dead terrain at {tile_pos}")
            return
        if self.delete_mode:
            items = self.scene.items(pos)
            for item in items:
                if isinstance(item, QGraphicsRectItem):
                    if item == self.player_item:
                        self.player_item = None
                        self.grid_width_input.setEnabled(True)
                        self.grid_height_input.setEnabled(True)
                        if hasattr(self, "facing_arrow") and self.facing_arrow:
                            self.scene.removeItem(self.facing_arrow)
                            self.facing_arrow = None

                    for idx in range(1, 3):
                        extra = item.data(idx)
                        if isinstance(extra, (QGraphicsRectItem, QGraphicsPixmapItem)):
                            self.scene.removeItem(extra)

                    self.scene.removeItem(item)
                    for i in range(self.entity_list_widget.count()):
                        if self.entity_list_widget.item(i).data(Qt.UserRole) == item:
                            self.entity_list_widget.takeItem(i)
                            break
                    self.delete_mode = False
                    self.delete_button.setStyleSheet("")
                    self.view.setCursor(Qt.ArrowCursor)
                    return

        if self.copy_mode and self.copied_entity_data:
            click_x = int(pos.x() // GRID_SIZE) * GRID_SIZE
            click_y = int(pos.y() // GRID_SIZE) * GRID_SIZE
            tile_pos = (click_x, click_y)
            if tile_pos in self.dead_positions:
                print("⛔ Cannot copy entity onto dead terrain.")
                return

            size = self.copied_entity_data.get("size", 1)
            placement_pos = self.entity_manager.find_valid_position(size, size, preferred=(click_x, click_y))


            if placement_pos:
                x, y = placement_pos
                new_entity = self.entity_manager.create_entity(x, y, dict(self.copied_entity_data))
                data = new_entity.data(0)
                if "sprites" in self.copied_entity_data:
                    data["sprites"] = dict(self.copied_entity_data["sprites"])
                    new_entity.setData(0, data)

                original_sprite = self.selected_item.data(2) if self.selected_item else None
                if original_sprite and isinstance(original_sprite, QGraphicsPixmapItem):
                    new_sprite = QGraphicsPixmapItem(original_sprite.pixmap())
                    new_sprite.setZValue(2)
                    self.scene.addItem(new_sprite)
                    new_entity.setData(2, new_sprite)
                    new_entity.setBrush(QBrush(Qt.NoBrush))
                    new_entity.setPen(QPen(Qt.NoPen))
                    rect = new_entity.rect()
                    new_sprite.setPos(
                        int(rect.x() + (rect.width() - new_sprite.pixmap().width()) / 2),
                        int(rect.y() + (rect.height() - new_sprite.pixmap().height()) / 2)
                    )
                print("✅ Entity copied successfully!")
            else:
                print("❌ No valid position found for copy placement!")
            return

        if not self.current_entity or self.current_entity not in ENTITY_TYPES:
            return

        size = self.get_entity_size(self.current_entity)
        click_x = int(pos.x() // GRID_SIZE) * GRID_SIZE
        click_y = int(pos.y() // GRID_SIZE) * GRID_SIZE
        tile_pos = (click_x, click_y)
        if tile_pos in self.dead_positions:
            print("⛔ Cannot copy entity onto dead terrain.")
            return

        placement_pos = self.entity_manager.find_valid_position(size, size, preferred=(click_x, click_y))
        if not placement_pos:
            print("❌ No valid space found!")
            return

        x, y = placement_pos
        data = {
            "type": self.current_entity,
            "size": size,
            "width": size,
            "height": size
        } 

        if self.current_entity.startswith("Player"):
            if self.player_item:
                print("⛔ Only one player is allowed.")
                self.player_item.setZValue(10)  
                sprite_item = self.player_item.data(2)
                if sprite_item:
                    sprite_item.setZValue(11)  # (opțional, sprite peste rect)
                return
            data.update({
                "game_mode": self.category_selector.currentText(),
                "hp": 100,
                "behavior": "idle",
                "inventory": [],
                "facing": "down",
                "damage": 25,
                 # cheile de mai jos sunt esențiale:
                "equipped_sword": "Wooden Sword",
                "equipped_weapon": "Wooden Sword",
                "custom_items": {
                    "Wooden Sword": {
                        "damage_bonus": 20
                    }
                },
                "item_types": {
                    "Wooden Sword": "sword"
                }
            })

        elif self.current_entity == "Enemy":
            data.update({
                "hp": 100,
                "behavior": random.choice(["idle", "patrol", "hostile"]),
                "inventory": random.sample(["key", "potion", "coin"], k=random.randint(1, 2)),
                "speed": 1,
                "damage": 25,
                "trigger_range": 5,
                "patrol_range": 5
            })

        elif self.current_entity == "Chest":
            data["inventory"] = []
            data["custom_items"] = {}
            data["item_types"] = {}

            # Alege câte iteme vrei (ex: 3)
            for i in range(3):
                dialog = QDialog(self)
                dialog.setWindowTitle("Setează statusurile itemului")
                layout = QFormLayout(dialog)
                combo = QComboBox()
                combo.addItems(PREDEFINED_ITEMS.keys())
                layout.addRow("Tip item:", combo)
                name_input = QLineEdit()
                layout.addRow("Nume item:", name_input)
                hp_input = QLineEdit("0")
                dmg_input = QLineEdit("0")
                res_input = QLineEdit("0")
                spd_input = QLineEdit("0")
                blk_input = QLineEdit("0")
                layout.addRow("HP Bonus:", hp_input)
                layout.addRow("Damage Bonus:", dmg_input)
                layout.addRow("Resistance:", res_input)
                layout.addRow("Speed Bonus:", spd_input)
                layout.addRow("Block Bonus:", blk_input)

                range_input = QLineEdit("3")
                layout.addRow("Range (bow/staff):", range_input)
                range_input.setVisible(False)  # implicit ascuns

                def update_range_visibility():
                    t = combo.currentText().lower()
                    show = t in ("bow", "staff")
                    range_input.setVisible(show)
                    layout.labelForField(range_input).setVisible(show)
                combo.currentTextChanged.connect(update_range_visibility)
                update_range_visibility()

                img_path = [""]
                img_btn = QPushButton("Alege imagine...")
                img_label = QLabel("Fără imagine")
                def select_img():
                    file, _ = QFileDialog.getOpenFileName(self, "Imagine", "", "Images (*.png *.jpg *.bmp)")
                    if file:
                        img_path[0] = file
                        img_label.setText(file.split("/")[-1])
                img_btn.clicked.connect(select_img)
                layout.addRow(img_btn, img_label)

                add_btn = QPushButton("OK")
                add_btn.clicked.connect(dialog.accept)
                layout.addWidget(add_btn)
                dialog.setLayout(layout)
                if dialog.exec_() != QDialog.Accepted:
                    return

                item_type = combo.currentText()
                item_name = name_input.text() or item_type
                bonus = {
                    "hp_bonus": int(hp_input.text()),
                    "damage_bonus": int(dmg_input.text()),
                    "resistance": int(res_input.text()),
                    "speed_bonus": int(spd_input.text()),
                    "block_bonus": int(blk_input.text()),
                }
                if item_type.lower() in ("bow", "staff"):
                    bonus["range"] = int(range_input.text())
                if img_path[0]:
                    bonus["image"] = img_path[0]

                # Salvezi în structura cufărului
                data["inventory"].append(item_name)
                data["custom_items"][item_name] = bonus
                data["item_types"][item_name] = item_type




        elif self.current_entity == "Collectible":
            dialog = QDialog(self)
            dialog.setWindowTitle("Setează statusurile itemului")
            layout = QFormLayout(dialog)
            combo = QComboBox()
            combo.addItems(PREDEFINED_ITEMS.keys())
            layout.addRow("Tip item:", combo)
            name_input = QLineEdit()
            layout.addRow("Nume item:", name_input)
            hp_input = QLineEdit("0")
            dmg_input = QLineEdit("0")
            res_input = QLineEdit("0")
            spd_input = QLineEdit("0")
            blk_input = QLineEdit("0")
            layout.addRow("HP Bonus:", hp_input)
            layout.addRow("Damage Bonus:", dmg_input)
            layout.addRow("Resistance:", res_input)
            layout.addRow("Speed Bonus:", spd_input)
            layout.addRow("Block Bonus:", blk_input)

            range_input = QLineEdit("3")
            layout.addRow("Range (bow/staff):", range_input)    
            range_input.setVisible(False)  # implicit ascuns

            def update_range_visibility():
                t = combo.currentText().lower()
                show = t in ("bow", "staff")
                range_input.setVisible(show)
                layout.labelForField(range_input).setVisible(show)
            combo.currentTextChanged.connect(update_range_visibility)
            update_range_visibility()

            img_path = [""]
            img_btn = QPushButton("Alege imagine...")
            img_label = QLabel("Fără imagine")
            def select_img():
                file, _ = QFileDialog.getOpenFileName(self, "Imagine", "", "Images (*.png *.jpg *.bmp)")
                if file:
                    img_path[0] = file
                    img_label.setText(file.split("/")[-1])
            img_btn.clicked.connect(select_img)
            layout.addRow(img_btn, img_label)

            add_btn = QPushButton("OK")
            add_btn.clicked.connect(dialog.accept)
            layout.addWidget(add_btn)
            dialog.setLayout(layout)
            if dialog.exec_() != QDialog.Accepted:
                return

            item_type = combo.currentText()
            item_name = name_input.text() or item_type
            bonus = {
                "hp_bonus": int(hp_input.text()),
                "damage_bonus": int(dmg_input.text()),
                "resistance": int(res_input.text()),
                "speed_bonus": int(spd_input.text()),
                "block_bonus": int(blk_input.text()),
            }
            if item_type.lower() in ("bow", "staff"):
                bonus["range"] = int(range_input.text())
            if img_path[0]:
                bonus["image"] = img_path[0]


            data["name"] = item_name
            data["custom_items"] = {item_name: bonus}
            data["item_types"] = {item_name: item_type}
            if img_path[0]:
                data["image"] = img_path[0]
        elif self.current_entity == "Door":
            # Dialog simplu: selectează fișierul scenei destinație
            file_name, _ = QFileDialog.getOpenFileName(self, "Select Scene to Load on Door", "", "JSON Files (*.json)")
            if not file_name:
                return
            data["target_scene"] = file_name


        new_entity = self.entity_manager.create_entity(x, y, data)
        self.current_entity = None  
        self.entity_list.setCurrentItem(None)  # Deselect in entity list
    
    def select_item(self, list_item):
        if not list_item:
            return

        entity = list_item.data(Qt.UserRole)
        if not entity:
            return
        self.scene.clearSelection()  # ADDED

        # Clear previous selection
        if self.selected_item and hasattr(self.selected_item, 'setSelected'):
            self.selected_item.setSelected(False)

        self.selected_item = entity
        entity.setSelected(True)
        self.entity_list.setCurrentItem(None)

        data = entity.data(0).copy() if isinstance(entity.data(0), dict) else {}

        # Șterge widgeturile vechi din formular
        while self.properties_form.count():
            child = self.properties_form.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        self.inputs = {}

        data.setdefault("size", data.get("width", 1))

        for key, value in data.items():
            if key in ["inventory", "width", "height", "sprites", "custom_items", "item_types", "range", "speed", "damage", "hp", "trigger_range", "behavior", "patrol_range","equipped_sword", "equipped_bow", "equipped_staff", "equipped_shield", "equipped_helmet", "equipped_chest", "equipped_legs", "equipped_boots", "equipped_hp potion", "equipped_boost"]:
                continue
            if data.get("type", "").startswith("Player") and key == "behavior":
                continue

            if key == "game_mode":
                combo = QComboBox()
                combo.addItems([
                    "Toate", "🎮 Action RPG", "🔫 Shooter", "🧩 Puzzle",
                    "🏎 Racing", "📖 Narrative", "🛡 Tower Defense"
                ])
                combo.setCurrentText(str(value))
                self.inputs[key] = combo
                self.properties_form.addRow(QLabel(f"{key}:"), combo)
                continue

            field = QLineEdit(str(value))
            if key in ["type", "name"]:
                field.setReadOnly(True)
            self.inputs[key] = field
            self.properties_form.addRow(QLabel(f"{key}:"), field)

        if data.get("type") in ["PlayerRPG", "Enemy"]:
            for attr in ["speed", "damage", "hp", "range"]:
                val = str(data.get(attr, 1 if attr == "speed" else 10))
                input_field = QLineEdit(val)
                self.inputs[attr] = input_field
                self.properties_form.addRow(QLabel(attr.capitalize() + ":"), input_field)
        if data.get("type") == "Enemy":
            behavior_combo = QComboBox()
            trigger_val = str(data.get("trigger_range", 5))
            tr = QLineEdit(trigger_val)
            self.inputs["trigger_range"] = tr
            self.properties_form.addRow(QLabel("Trigger Range:"), tr)
            behavior_combo.addItems(["idle", "hostile", "patrol"])
            behavior_combo.setCurrentText(data.get("behavior", "idle"))
            self.inputs["behavior"] = behavior_combo
            self.properties_form.addRow(QLabel("Behavior:"), behavior_combo)

            if data.get("behavior") == "hostile":
                tr = QLineEdit(str(data.get("trigger_range", 5)))
                self.inputs["trigger_range"] = tr
                self.properties_form.addRow(QLabel("Trigger Range (hostile):"), tr)

            elif data.get("behavior") == "patrol":
                pr = QLineEdit(str(data.get("patrol_range", 5)))
                tr = QLineEdit(str(data.get("trigger_range", 5)))
                self.inputs["patrol_range"] = pr
                self.inputs["trigger_range"] = tr
                self.properties_form.addRow(QLabel("Patrol Range:"), pr)
                self.properties_form.addRow(QLabel("Trigger Range (to hostile):"), tr)

                checkpoint_btn = QPushButton("➕ Add Checkpoint")
                checkpoint_btn.clicked.connect(lambda: self.start_inserting_waypoints(entity, mode="checkpoint"))
                self.properties_form.addRow(checkpoint_btn)

                finish_btn = QPushButton("🏁 Set Finish Point")
                finish_btn.clicked.connect(lambda: self.start_inserting_waypoints(entity, mode="finish"))
                self.properties_form.addRow(finish_btn)

        # Echipament curent vizualizat
        for eq in ["equipped_sword", "equipped_bow", "equipped_staff", "equipped_shield",
                "equipped_helmet", "equipped_chest", "equipped_legs", "equipped_boots",
                "equipped_hp potion", "equipped_boost"]:
            if eq in data:
                self.properties_form.addRow(QLabel(eq.replace("equipped_", "").capitalize() + ":"), QLabel(str(data[eq])))

        # Player = keybind btn
        if data.get("type", "").startswith("Player"):
            self.player_item = entity
            keybind_btn = QPushButton("Key Bindings")
            keybind_btn.clicked.connect(self.open_key_bindings_popup)
            self.properties_form.addRow(keybind_btn)

        # Butoane globale
        save_btn = QPushButton("Apply Changes")
        save_btn.clicked.connect(self.apply_changes)
        self.properties_form.addRow(save_btn)

        design_btn = QPushButton("Insert Design")
        design_btn.clicked.connect(self.open_design_menu)
        self.properties_form.addRow(design_btn)

        # NPC = dialog
        if data.get("type") == "NPC":
            edit_btn = QPushButton("Edit Dialog")
            edit_btn.clicked.connect(self.edit_selected_npc_dialog)
            self.properties_form.addRow(edit_btn)

            insert_btn = QPushButton("Insert Dialog")
            insert_btn.clicked.connect(self.insert_dialog_for_npc)
            self.properties_form.addRow(insert_btn)

        # INVENTAR
        for i in reversed(range(self.inventory_box.count())):
            widget = self.inventory_box.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.setParent(None)

        self.inventory_display.clear()

        if not self.properties_widget.isVisible():
            self.properties_widget.setVisible(True)

        excluded_types = ["Collectible", "Obstacle", "Projectile", "Door"]
        show_inventory = data.get("type") not in excluded_types
        self.inventory_widget.setVisible(show_inventory)
        self.entity_list_widget.setMaximumHeight(150)

        if show_inventory:
            inventory = data.get("inventory", [])
            equipped_items = [v for k, v in data.items() if k.startswith("equipped_")]
            all_items = inventory + [i for i in equipped_items if i and i not in inventory]

            for obj in all_items:
                item_widget = QListWidgetItem(obj)
                if obj in equipped_items:
                    item_widget.setBackground(QColor("yellow"))
                    item_widget.setText(f"{obj} (echipat)")
                self.inventory_display.addItem(item_widget)

            self.add_item_btn = QPushButton("➕ Adaugă item")
            self.remove_item_btn = QPushButton("➖ Șterge item selectat")
            self.add_item_btn.clicked.connect(self.open_add_item_dialog)
            self.remove_item_btn.clicked.connect(self.remove_inventory_item)
            self.inventory_box.addWidget(self.add_item_btn)
            self.inventory_box.addWidget(self.remove_item_btn)
    def apply_changes(self):
        if not hasattr(self, "selected_item") or self.selected_item is None:
            return

        old_data = self.selected_item.data(0)
        if not isinstance(old_data, dict):
            return

        new_data = {}

        for key, field in self.inputs.items():
            val = field.currentText() if isinstance(field, QComboBox) else field.text()
            try:
                val = int(val)
            except ValueError:
                try:
                    val = float(val)
                except ValueError:
                    pass
            new_data[key] = val

        # Sincronizăm size, width, height
        new_size = int(new_data.get("size", 1))
        new_data["width"] = new_data["height"] = new_size

        # Păstrăm inventarul și atributele speciale
        for key in ["inventory", "custom_items", "item_types", "sprites", "facing"]:
            if key in old_data:
                new_data[key] = old_data[key]

        # Păstrăm echipamentul echipat
        for key in old_data:
            if key.startswith("equipped_"):
                new_data[key] = old_data[key]

        # Update pe entitate
        self.selected_item.setData(0, new_data)

        # Reaplicare comportament UI dacă este Enemy
        if new_data.get("type") == "Enemy" and "behavior" in new_data:
            self.refresh_behavior_ui(self.selected_item)

        # Obținem poziția și verificăm dacă trebuie mutată
        rect = self.selected_item.rect()
        old_size = int(old_data.get("size", old_data.get("width", 1)))
        initial_pos = (int(rect.x()), int(rect.y()))

        if new_size != old_size:
            new_pos = self.entity_manager.find_valid_position(new_size, new_size, preferred=initial_pos)
            if new_pos:
                x, y = new_pos
            else:
                print("❌ No valid position for resized entity")
                return
        else:
            x, y = initial_pos

        # Aplicăm noul dreptunghi
        self.selected_item.setRect(x, y, GRID_SIZE * new_size, GRID_SIZE * new_size)

        # Redimensionăm și HP bar dacă e cazul
        hp_bar = self.selected_item.data(1)
        if hp_bar and isinstance(hp_bar, QGraphicsRectItem):
            hp_bar.setRect(x, y - 7, GRID_SIZE * new_size, 5)

        print(f"✅ Changes applied to {new_data.get('name', 'entity')}")
    def update_behaviors(self):
        from PyQt5.QtCore import QTime

        if not hasattr(self, "behavior_counters"):
            self.behavior_counters = {}
        if not hasattr(self, "last_enemy_attack"):
            self.last_enemy_attack = {}

        player = self.player_item
        if not player:
            return
        
        player_pos = player.rect().x(), player.rect().y()
        px_tile, py_tile = int(player_pos[0] // GRID_SIZE), int(player_pos[1] // GRID_SIZE)
        player_data = player.data(0)
        bonus_stats = self.compute_player_stats()
        player_resistance = bonus_stats.get("resistance", 0)
        if getattr(self, "blocking", False):
            player_resistance += bonus_stats.get("block_bonus", 0)

        for item in list(self.scene.items()):
            if not isinstance(item, QGraphicsRectItem):
                continue

            data = item.data(0)
            if not isinstance(data, dict) or data.get("type") != "Enemy":
                continue
            if "original_position" not in data:
                rect = item.rect()
                data["original_position"] = (int(rect.x() // GRID_SIZE), int(rect.y() // GRID_SIZE))
                item.setData(0, data)
            if data.get("behavior") == "idle" and data.get("was_attacked") and data.get("change_behavior_on_damage"):
                data["behavior"] = "hostile"
                item.setData(0, data)

            speed = data.get("speed", 1)
            interval = int(10 / speed)

            if item not in self.behavior_counters:
                self.behavior_counters[item] = 0
            self.behavior_counters[item] += 1
            if self.behavior_counters[item] < interval:
                continue
            self.behavior_counters[item] = 0

            behavior = data.get("behavior", "idle")
            ex, ey = item.rect().x(), item.rect().y()
            width, height = item.rect().width(), item.rect().height()

            ex_tile, ey_tile = int(ex // GRID_SIZE), int(ey // GRID_SIZE)
            px_tile, py_tile = int(player.rect().x() // GRID_SIZE), int(player.rect().y() // GRID_SIZE)
            distance_to_player = ((ex_tile - px_tile) ** 2 + (ey_tile - py_tile) ** 2) ** 0.5
            if data.get("hp", 100) <= 0:
                print(f"💀 Enemy at ({ex_tile}, {ey_tile}) defeated")
                self.remove_entity(item)
                continue

            hp_bar = item.data(1)
            if hp_bar and isinstance(hp_bar, QGraphicsRectItem):
                hp = data.get("hp", 100)
                bar_width = width * (hp / 100)
                hp_bar.setRect(ex, ey - 7, bar_width, 5)

            if data.get("behavior") == "patrol":
                if "waypoints" not in data or not data["waypoints"]:
                    if "start_point" in data and "final_point" in data:
                        if "checkpoints" in data and data["checkpoints"]:
                            forward = [data["start_point"]] + data["checkpoints"] + [data["final_point"]]
                            backward = list(reversed(data["checkpoints"])) + [data["start_point"]]
                        else:
                            forward = [data["start_point"], data["final_point"]]
                            backward = [data["start_point"]]

                        data["waypoints"] = forward + backward
                        data["patrol_index"] = 0
                        item.setData(0, data)



                waypoints = data.get("waypoints", [])
                trigger_range = data.get("trigger_range", 5)
                patrol_range = data.get("patrol_range", 10)

                # Dacă playerul este în raza de detectare
                if distance_to_player <= patrol_range:
                    data["behavior"] = "hostile"
                    item.setData(0, data)
                    continue  # acest frame nu continuă patrularea

                if waypoints:
                    idx = data.get("patrol_index", 0)
                    target = waypoints[idx % len(waypoints)]
                    enemy_size = data.get("size", 1)
                    path = self.calculate_path((ex_tile, ey_tile), target, size=enemy_size)


                    if path:
                        nx, ny = path[0]
                        item.setRect(nx * GRID_SIZE, ny * GRID_SIZE, width, height)

                        # Actualizează HP bar la noua poziție
                        hp_bar = item.data(1)
                        if hp_bar and isinstance(hp_bar, QGraphicsRectItem):
                            hp = data.get("hp", 100)
                            bar_width = width * (hp / 100)
                            hp_bar.setRect(nx * GRID_SIZE, ny * GRID_SIZE - 7, bar_width, 5)

                        # Dacă a ajuns la punctul țintă, avansează indexul
                        if (nx, ny) == target:
                            data["patrol_index"] = (idx + 1) % len(waypoints)
                            item.setData(0, data)



            if behavior == "hostile":
                trigger_range = data.get("trigger_range", 5)
                attack_range = data.get("range", 0)
                enemy_size = data.get("size", 1)

                if "original_position" not in data:
                    data["original_position"] = (ex_tile, ey_tile)
                    item.setData(0, data)

                # Dacă jucătorul a ieșit din raza de trigger → revenire
                if distance_to_player > trigger_range:
                    ox, oy = data.get("original_position", (ex_tile, ey_tile))
                    path = self.calculate_path((ex_tile, ey_tile), (ox, oy), size=enemy_size)
                    if path and len(path) > 1:
                        nx, ny = path[0]
                        item.setRect(nx * GRID_SIZE, ny * GRID_SIZE, width, height)

                        hp_bar = item.data(1)
                        if hp_bar and isinstance(hp_bar, QGraphicsRectItem):
                            hp = data.get("hp", 100)
                            hp_bar.setRect(nx * GRID_SIZE, ny * GRID_SIZE - 7, width * (hp / 100), 5)
                    return

                # 🔫 ATAC dacă playerul este în range (inclusiv fără contact fizic)
                if distance_to_player <= attack_range:
                    current_time = QTime.currentTime().msecsSinceStartOfDay()
                    last_attack = self.last_enemy_attack.get(item, 0)
                    if current_time - last_attack >= 1000:
                        enemy_damage = data.get("damage", 25)
                        player_data["hp"] = max(0, player_data.get("hp", 100) - max(0, enemy_damage - player_resistance))
                        player.setData(0, player_data)
                        player_hp_bar = player.data(1)
                        if player_hp_bar:
                            player_rect = player.rect()  # Inițializăm player_rect aici
                            hp_percent = player_data["hp"] / 100
                            player_hp_bar.setRect(
                                player_rect.x(),
                                player_rect.y() - 7,
                                player_rect.width() * hp_percent,
                                5
                            )

                        self.last_enemy_attack[item] = current_time
                        print(f"🗡 Enemy attacked player (range={attack_range})! Player HP: {player_data['hp']}")

                        if player_data["hp"] <= 0:
                            self.remove_entity(player)
                            self.player_item = None
                            print("💀 Player died!")
                            return

                # 🧭 Dacă nu e în range → deplasare către player
                elif distance_to_player > attack_range:
                    path = self.calculate_path((ex_tile, ey_tile), (px_tile, py_tile), size=enemy_size)
                    if path and len(path) > 1:
                        nx, ny = path[0]
                        target_rect = QRectF(nx * GRID_SIZE, ny * GRID_SIZE, width, height)
                        blocked = any(
                            other.rect().intersects(target_rect)
                            for other in self.scene.items()
                            if other != item and isinstance(other, QGraphicsRectItem) and
                            other.data(0) and other.data(0).get("type") in ["NPC", "Chest", "Obstacle", "Enemy", "PlayerRPG"]
                        )
                        if not blocked:
                            item.setRect(nx * GRID_SIZE, ny * GRID_SIZE, width, height)
                            hp_bar = item.data(1)
                            if hp_bar and isinstance(hp_bar, QGraphicsRectItem):
                                current_hp = data.get("hp", 100)
                                hp_bar.setRect(nx * GRID_SIZE, ny * GRID_SIZE - 7, width * (current_hp / 100), 5)


        if player_data["hp"] <= 0:
            self.remove_entity(player)
            self.player_item = None
            print("💀 Player died!")
            return
    def select_entity_from_list(self, list_item):
        if not list_item:
            # Deselectează tot dacă ai dat click pe spațiu gol în listă
            self.selected_item = None
            for item in self.scene.items():
                if isinstance(item, QGraphicsRectItem):
                    item.setSelected(False)
            return

        item = list_item.data(Qt.UserRole)
        if item:
            self.select_item(item)

            # If in copy mode, store the entity data
            if self.copy_mode:
                data = item.data(0)
                if isinstance(data, dict):
                    if data.get("type", "").startswith("Player"):
                        print("❌ Cannot copy Player entities!")
                        return
                    self.copied_entity_data = dict(data)
                    print("✅ Entity selected for copying. Click on the grid to place the copy.")

            # Clear current_entity when selecting from list to prevent continuous insertion
            self.current_entity = None
            self.entity_list.setCurrentItem(None)
    def get_entity_size(self, entity_type=None):
        entity_type = entity_type or self.current_entity

        action_rpg_sizes = {
            "PlayerRPG": 1,
            "Enemy": 1,
            "NPC": 1,
            "Collectible": 1,
            "Obstacle": 2,
            "Chest": 1,
            "Door": 1,
            "Projectile": 1,
            "TriggerZone": 1
        }

        return action_rpg_sizes.get(entity_type, 1)
    def update_entity(self, entity):
        if not isinstance(entity, QGraphicsRectItem):
            return

        data = entity.data(0)
        if not isinstance(data, dict):
            return

        old_hp = data.get("hp", 100)
        new_hp = max(0, old_hp - 1)  # Exemplu: scade 1 HP (poți înlocui cu damage calculat)
        data["hp"] = new_hp
        entity.setData(0, data)

        # Actualizează bara de HP dacă există
        hp_bar = entity.data(1)
        if hp_bar and isinstance(hp_bar, QGraphicsRectItem):
            bar_width = entity.rect().width() * (new_hp / 100)
            hp_bar.setRect(entity.rect().x(), entity.rect().y() - 7, bar_width, 5)

        # Transformă în hostile dacă e cazul
        if data.get("behavior") == "idle" and data.get("type") == "Enemy":
            if data.get("change_behavior_on_damage", True):  # implicit True
                data["behavior"] = "hostile"
                entity.setData(0, data)
                self.refresh_behavior_ui(entity)
                print(f"☠️ Enemy behavior changed to hostile! HP: {new_hp}")
    def sync_player_game_mode(self, selected_mode):
        # Când schimbi categoria, setează game_mode pentru playerul selectat (dacă există)
        if not self.selected_item:
            return
        data = self.selected_item.data(0)
        if not isinstance(data, dict) or not data.get("type", "").startswith("Player"):
            return

        # Trebuie să găsim QComboBox-ul de game_mode din self.inputs!
        if "game_mode" in self.inputs:
            widget = self.inputs["game_mode"]
            if isinstance(widget, QComboBox):
                # Dacă e "Toate", nu modificăm
                if selected_mode != "Toate":
                    widget.setCurrentText(selected_mode)
                    data["game_mode"] = selected_mode
                    self.selected_item.setData(0, data)
    def setup_enemy_properties(self):
        # Adăugăm checkbox pentru change behavior on damage
        self.change_behavior_checkbox = QCheckBox("Change to hostile when damaged")
        self.change_behavior_checkbox.stateChanged.connect(self.on_change_behavior_toggle)
        self.properties_form.addRow(self.change_behavior_checkbox)

    def on_change_behavior_toggle(self, state):
        if self.selected_item:
            data = self.selected_item.data(0)
            if isinstance(data, dict):
                data["change_behavior_on_damage"] = bool(state)
                self.selected_item.setData(0, data)


    def handle_entity_item_changed(self, current, previous):
        if current:
            name = current.text().strip()
            # Sari peste titluri de categorie sau spații goale
            if name in self.entity_categories or not name or name == "Insert Terrain":
                if name == "Insert Terrain":
                    self.insert_terrain_image()
                    self.entity_list.setCurrentItem(None)
                return
            # Setează entitatea curentă doar dacă este validă
            if name in ENTITY_TYPES:
                self.current_entity = name
            else:
                self.current_entity = None

    def edit_selected_npc_dialog(self):
        selected_items = self.entity_list_widget.selectedItems()

        if selected_items:
            item = selected_items[0].data(Qt.UserRole)
            if item and item.data(0).get("type") == "NPC":
                self.entity_manager.edit_npc_dialog(item)

    def insert_dialog_for_npc(self):
        # Selectează entitatea NPC selectată din lista de entități
        selected_items = self.entity_list_widget.selectedItems()
        if not selected_items:
            return
        item = selected_items[0].data(Qt.UserRole)
        if not item or item.data(0).get("type") != "NPC":
            return

        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Select Dialog Text File", "", "Text Files (*.txt)", options=options)
        if not filename:
            return

        with open(filename, 'r', encoding='utf-8') as f:
            raw = f.read()

        # Split pe secvențe: grupuri de linii separate de cel puțin o linie goală
        paragraphs = []
        current = []
        for line in raw.splitlines():
            if line.strip() == "":
                if current:
                    paragraphs.append('\n'.join(current).strip())
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append('\n'.join(current).strip())

        # Pune tot dialogul într-un singur string, delimitat de \n\n (folosit de DialogManager)
        dialog_text = "\n\n".join(paragraphs)

        # Actualizează dialog_text la NPC
        data = item.data(0)
        data["dialog_text"] = dialog_text
        item.setData(0, data)
        print("✅ Dialog importat cu succes!")

        # Pornește dialogul imediat ca demo (opțional):
        # self.entity_manager.dialog_manager.start_dialog(item, dialog_text)    
    def toggle_grid(self):
        for item in getattr(self, "grid_lines", []):
            self.scene.removeItem(item)

        if self.grid_toggle.isChecked():
            self.grid_lines = []
            for x in range(0, GRID_SIZE * self.grid_cols, GRID_SIZE):
                line = self.scene.addLine(x, 0, x, GRID_SIZE * self.grid_rows, QColor(180, 180, 180, 120))
                self.grid_lines.append(line)
            for y in range(0, GRID_SIZE * self.grid_rows, GRID_SIZE):
                line = self.scene.addLine(0, y, GRID_SIZE * self.grid_cols, y, QColor(180, 180, 180, 120))
                self.grid_lines.append(line)
        else:
            self.grid_lines = []
    def update_grid_size(self):
        self.grid_cols = max(1, self.grid_width_input.value())
        self.grid_rows = max(1, self.grid_height_input.value())
        self.scene.setSceneRect(0, 0, GRID_SIZE * self.grid_cols, GRID_SIZE * self.grid_rows)
        if self.grid_toggle.isChecked():
            self.toggle_grid()
    def select_and_setup_movement_animation(self):
        if not self.selected_item:
            return
        files, _ = QFileDialog.getOpenFileNames(self, "Select movement sprite-sheet", "", "Images (*.png *.jpg *.bmp)")
        if files:
            self.animation_manager.setup_movement_animation(self.selected_item, files[0])

    def open_design_menu(self):
        if not self.selected_item:
            print("❌ Nicio entitate selectată.")
            return

        self.animation_manager.set_selected_item(self.selected_item)
        self.animation_manager.initialize_all_sprites()

        design_window = QWidget()
        design_window.setWindowTitle("Sprite Manager")
        layout = QVBoxLayout()

        # === Încărcare sprite-uri ===
        char_btn = QPushButton("🧍 Load Character Sprite")
        char_btn.clicked.connect(lambda: self.animation_manager.load_character_sprite())
        layout.addWidget(char_btn)

        move_btn = QPushButton("🏃 Load Movement Sprite")
        move_btn.clicked.connect(lambda: self.animation_manager.load_movement_sprite())
        layout.addWidget(move_btn)

        attack_btn = QPushButton("⚔️ Load Attack Sprite")
        attack_btn.clicked.connect(lambda: self.animation_manager.load_attack_sprite())
        layout.addWidget(attack_btn)

        death_btn = QPushButton("💀 Load Death Sprite")
        death_btn.clicked.connect(lambda: self.animation_manager.load_death_sprite())
        layout.addWidget(death_btn)

        # === Testare sprite-uri ===
        test_char_btn = QPushButton("👤 Test Character")
        test_char_btn.clicked.connect(self.animation_manager.switch_to_character_sprite)
        layout.addWidget(test_char_btn)

        test_move_btn = QPushButton("🏃 Test Movement")
        test_move_btn.clicked.connect(self.animation_manager.switch_to_movement_sprite)
        layout.addWidget(test_move_btn)

        test_attack_btn = QPushButton("⚔️ Test Attack")
        test_attack_btn.clicked.connect(self.animation_manager.play_attack_animation)
        layout.addWidget(test_attack_btn)

        test_death_btn = QPushButton("💀 Test Death")
        test_death_btn.clicked.connect(self.animation_manager.play_death_animation_for_selected)
        layout.addWidget(test_death_btn)

        # Închidere
        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(design_window.close)
        layout.addWidget(close_btn)

        design_window.setLayout(layout)
        design_window.setFixedSize(240, 400)
        design_window.show()
        self.design_window = design_window


    def activate_delete_mode(self):
        self.delete_mode = not self.delete_mode  # Toggle delete mode
        if self.delete_mode:
            self.copy_mode = False
            self.copy_button.setStyleSheet("")
            self.delete_button.setStyleSheet("background-color: #ff8888")
            self.view.setCursor(Qt.CrossCursor)
        else:
            self.delete_button.setStyleSheet("")
            self.view.setCursor(Qt.ArrowCursor)

    def activate_copy_mode(self):
        self.copy_mode = not self.copy_mode
        if self.copy_mode:
            self.delete_mode = False
            self.copy_button.setStyleSheet("background-color: #8f8")
            self.delete_button.setStyleSheet("")
            self.copied_entity_data = None
            self.statusBar().showMessage("Select an entity (not Player) from the list to copy.")
        else:
            self.copy_button.setStyleSheet("")
            self.copied_entity_data = None


    

    def reset_grid(self):
        # 1. Debifează Show Grid (și ascunde gridul)
        self.grid_toggle.setChecked(False)
        self.show_grid = False  # dacă ai flag pentru grid
        self.properties_widget.setVisible(False)
        self.inventory_widget.setVisible(False)

        # 2. Resetează Tile W și H la valorile default
        self.grid_width_input.setValue(20)
        self.grid_height_input.setValue(15)
        self.grid_cols = 20
        self.grid_rows = 15
        self.grid_width_input.setEnabled(True)
        self.grid_height_input.setEnabled(True)

        # 3. Șterge tot din scenă
        self.scene.clear()
        self.facing_arrow = None

        # 4. Șterge toate referințele la entități
        self.selected_item = None
        self.current_entity = None
        self.entity_manager.player_item = None
        self.player_item = None
        self.entity_manager.entity_counters = {key: 0 for key in self.entity_manager.entity_counters.keys()}
        self.entity_list_widget.clear()  # dacă ai un QListWidget cu entitățile din scenă


        self.inventory_display.clear()
        # Resetează și proprietățile UI
        while self.properties_form.count():
            child = self.properties_form.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # 5. Re-generează gridul dacă vrei ca tiles-urile să apară iar
        self.update_grid_size()

      
    def update_entity_list(self, selected_category):
        # Save existing entity items before clearing
        existing_items = []
        for i in range(self.entity_list.count()):
            item = self.entity_list.item(i)
            if item.data(Qt.UserRole):  # This is an actual entity, not a category
                existing_items.append(item)

        self.entity_list.clear()

        # First add categories and their entities
        if selected_category == "Toate":
            for category, entities in self.entity_categories.items():
                self.entity_list.addItem(category)
                for name in entities:
                    self.entity_list.addItem(f"  {name}")
        else:
            self.entity_list.addItem(selected_category)
            for name in self.entity_categories.get(selected_category, []):
                self.entity_list.addItem(f"  {name}")

        # Add "Insert Terrain" option
        self.entity_list.addItem("Insert Terrain")

        # Add back the existing entity items
        for item in existing_items:
            self.entity_list.addItem(item)

    def open_key_bindings_popup(self):
        if not self.selected_item:
            return

        data = self.selected_item.data(0)
        if not isinstance(data, dict):
            return

        key_bindings = data.get("key_bindings", {
            "move_up": "W",
            "move_down": "S",
            "move_left": "A",
            "move_right": "D",
            "attack": "J",
            "interact": "E",
            "inventory": "I",
            "switch_weapon": "Q",
            "sprint": "Shift",
            "dodge": "Space",
            "block": "B"
        })

        from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QPushButton, QMessageBox
        popup = QDialog(self)
        popup.setWindowTitle("Configure Key Bindings")
        layout = QFormLayout()

        inputs = {}
        for action, key in key_bindings.items():
            field = QLineEdit(key)
            inputs[action] = field
            layout.addRow(f"{action.replace('_', ' ').capitalize()}:", field)

        save_btn = QPushButton("Save Bindings")
        layout.addWidget(save_btn)
        popup.setLayout(layout)

        def save_and_close():
            new_bindings = {action: field.text().upper() for action, field in inputs.items()}
            data["key_bindings"] = new_bindings
            self.selected_item.setData(0, data)
            QMessageBox.information(popup, "Saved", "Key bindings updated.")
            popup.accept()

        save_btn.clicked.connect(save_and_close)
        popup.exec_()
    
    def refresh_behavior_ui(self, selected_item):
        """Actualizează UI-ul pentru comportamentul inamicului selectat."""
        if isinstance(selected_item, QGraphicsRectItem):
            data = selected_item.data(0)
            if isinstance(data, dict) and "behavior" in data:
                current_behavior = data["behavior"]
                if hasattr(self, "inputs") and "behavior" in self.inputs:
                    behavior_combo = self.inputs["behavior"]
                    if isinstance(behavior_combo, QComboBox):
                        index = self.behavior_types.index(current_behavior)
                        behavior_combo.setCurrentIndex(index)

    def update_inventory_bar_position(self):
        if not hasattr(self, "inventory_bar") or not self.player_item:
            return

        base_size = int(self.player_item.rect().width())
        slot_size = base_size * 0.8  # ✅ fără împărțire la scale


        spacing = 2
        columns = 4
        rows = 5

        player_rect = self.player_item.rect()
        base_x = player_rect.x()
        base_y = player_rect.y() + player_rect.height() + spacing

        index = 0
        for col in range(columns):
            for row in range(rows):
                slot_x = base_x + col * (slot_size + spacing)
                slot_y = base_y + row * (slot_size + spacing)

                if index < len(self.inventory_bar):
                    item = self.inventory_bar[index]
                    if isinstance(item, QGraphicsRectItem):
                        item.setRect(slot_x, slot_y, slot_size, slot_size)
                    elif isinstance(item, QGraphicsTextItem):
                        item.setPos(slot_x + 2, slot_y + 2)
                        item.setScale(0.5)

                index += 1
    def show_chest_inventory(self, chest_item):
        # curățăm dacă era deja deschis alt inventar
        self.hide_chest_inventory()

        data = chest_item.data(0)
        inventory = data.get("inventory", [])
        self.chest_inventory_ui = []
        self.current_chest_entity = chest_item  # 🟢 salvezi referința la cufăr
        slot_size = GRID_SIZE
        spacing = 4
        num_slots = 5

        base_x = chest_item.rect().x()
        base_y = chest_item.rect().y() - slot_size - spacing

        for i in range(num_slots):
            slot_x = base_x + i * (slot_size + spacing)
            slot_y = base_y
            rect = QGraphicsRectItem(slot_x, slot_y, slot_size, slot_size)
            rect.setBrush(QBrush(QColor("#fffccc")))
            rect.setZValue(5)
            self.scene.addItem(rect)
            self.chest_inventory_ui.append(rect)
            rect.setAcceptedMouseButtons(Qt.RightButton)

            if i < len(inventory):
                label = QGraphicsTextItem(inventory[i])
                label.setDefaultTextColor(Qt.black)
                label.setScale(0.5)
                label.setZValue(6)
                label.setPos(slot_x + 4, slot_y + 4)
                self.scene.addItem(label)
                self.chest_inventory_ui.append(label)

            # Set up scene event handling
            rect.mousePressEvent = lambda event, rect=rect, i=i: self.handle_chest_slot_click(event, rect, i, inventory)

    def hide_chest_inventory(self):
        if hasattr(self, "chest_inventory_ui"):
            for item in self.chest_inventory_ui:
                self.scene.removeItem(item)
            del self.chest_inventory_ui
    def eventFilter(self, obj, event):
        # Click dreapta pe slot cufăr
        if event.type() == QEvent.GraphicsSceneMousePress:
            if event.button() == Qt.RightButton:
                if hasattr(self, "chest_inventory_ui") and obj in self.chest_inventory_ui:
                    idx = self.chest_inventory_ui.index(obj)
                    if idx % 2 == 0 and idx + 1 < len(self.chest_inventory_ui):
                        label_item = self.chest_inventory_ui[idx + 1]
                        item_name = label_item.toPlainText()
                        self.take_item_from_chest(obj, item_name)
                        return True
        # --- CLICK pe NPC pentru dialog ---
        if event.type() == QEvent.GraphicsSceneMousePress:
            if event.button() == Qt.LeftButton:
                # Caută dacă ai dat click pe un NPC
                for item in self.scene.items():
                    if isinstance(item, QGraphicsRectItem):
                        mouse_pos = self.view.mapToScene(event.pos())
                        if item.rect().contains(mouse_pos):
                            data = item.data(0)
                            if isinstance(data, dict) and data.get("type") == "NPC":
                                # Verifică dacă player-ul e lângă și cu fața spre el
                                if self.player_item:
                                    player_data = self.player_item.data(0)
                                    px, py = int(self.player_item.rect().x()), int(self.player_item.rect().y())
                                    nx, ny = int(item.rect().x()), int(item.rect().y())
                                    facing = player_data.get("facing", "down")
                                    fx, fy = px, py
                                    if facing == "up": fy -= GRID_SIZE
                                    elif facing == "down": fy += GRID_SIZE
                                    elif facing == "left": fx -= GRID_SIZE
                                    elif facing == "right": fx += GRID_SIZE
                                    if nx == fx and ny == fy:
                                        if self.entity_manager.handle_interaction(self.player_item, event):
                                            event.accept()
                                            return True
        return False

        
    

    def show_facing_arrow(self):
        if hasattr(self, "facing_arrow") and self.facing_arrow:
            self.scene.removeItem(self.facing_arrow)

        pix = QPixmap("arrow.png")
        if pix.isNull():
            print("❌ ERROR: Arrow image not found or invalid.")
            return

        arrow = QGraphicsPixmapItem(pix.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        arrow.setTransformOriginPoint(arrow.boundingRect().center())
        arrow.setZValue(5)
        self.scene.addItem(arrow)
        self.facing_arrow = arrow
        self.update_facing_arrow_position()

    def update_facing_arrow_position(self):
        if not self.player_item or not hasattr(self, "facing_arrow") or self.facing_arrow is None:
            return

        arrow = self.facing_arrow
        if arrow is None or arrow.scene() is None:
            # Obiectul a fost șters — nu mai încercăm să-l folosim
            self.facing_arrow = None
            return


        data = self.player_item.data(0)
        facing = data.get("facing", "down")
        rect = self.player_item.rect()
        size = rect.width()
        arrow = self.facing_arrow

        center_x = rect.x() + size / 2
        center_y = rect.y() + size / 2

        offset = size / 2 + 2  # mică distanță față de margine
        if facing == "up":
            angle = 0
            arrow.setPos(center_x - 8, rect.y() - offset)
            arrow.setRotation(angle)
        elif facing == "down":
            angle = 180
            arrow.setPos(center_x - 8, rect.y() + size + 2)
            arrow.setRotation(angle)
        elif facing == "left":
            angle = 270
            arrow.setPos(rect.x() - offset, center_y - 8)
            arrow.setRotation(angle)
        elif facing == "right":
            angle = 90
            arrow.setPos(rect.x() + size + 2, center_y - 8)
            arrow.setRotation(angle)
    

    def handle_inventory_context_menu(self, pos):
        item = self.inventory_display.itemAt(pos)
        if not item or not self.player_item:
            return

        from PyQt5.QtWidgets import QMenu
        menu = QMenu()
        drop_action = menu.addAction("🗑 Aruncă item")

        action = menu.exec_(self.inventory_display.mapToGlobal(pos))
        if action == drop_action:
            item_name = item.text().replace(" (echipat)", "")
            data = self.player_item.data(0)
            inventory = data.get("inventory", [])
            was_equipped = "(echipat)" in item.text()

            # Dacă era echipat, scoate-l din slotul respectiv!
            for slot in [
                "equipped_helmet", "equipped_chest", "equipped_legs", "equipped_boots", 
                "equipped_shield", "equipped_sword", "equipped_bow", "equipped_staff",
                "equipped_hp potion", "equipped_boost"
            ]:
                if data.get(slot) == item_name:
                    data[slot] = None  # Dezactivează slotul

            if data.get("equipped_weapon") == item_name:
                data["equipped_weapon"] = None

            if item_name in inventory:
                inventory.remove(item_name)

            self.player_item.setData(0, data)
            self.inventory_display.takeItem(self.inventory_display.row(item))
            # Creează item colectabil pe hartă la poziția playerului
            x, y = int(self.player_item.rect().x()), int(self.player_item.rect().y())
            drop_data = {"type": "Collectible", "name": item_name}
            self.entity_manager.create_entity(x, y, drop_data)
            print(f"🗑 Ai aruncat: {item_name}")


    

    def handle_scene_events(self, watched, event):
        if event.type() == event.GraphicsSceneMousePress:
            if event.button() == Qt.RightButton:
                if hasattr(self, "chest_inventory_ui") and watched in self.chest_inventory_ui:
                    idx = self.chest_inventory_ui.index(watched)
                    if idx % 2 == 0 and idx + 1 < len(self.chest_inventory_ui):
                        label_item = self.chest_inventory_ui[idx + 1]
                        item_name = label_item.toPlainText()
                        self.take_item_from_chest(watched, item_name)
                        return True
        return False

    def handle_chest_slot_click(self, event, rect, idx, inventory):
        if event.button() == Qt.RightButton and idx < len(inventory):
            item_name = inventory[idx]
            self.take_item_from_chest(self.current_chest_entity, item_name)
    def remove_entity(self, entity):
        # Șterge orice QGraphicsItem asociat (ex: sprite, HP bar, etc.)
        for i in range(1, 3):  # dacă ai date suplimentare la index 1, 2
            extra = entity.data(i)
            if isinstance(extra, (QGraphicsRectItem, QGraphicsPixmapItem)):
                self.scene.removeItem(extra)
        self.scene.removeItem(entity)
        # Scoate și din entity list
        for i in range(self.entity_list_widget.count()):
            if self.entity_list_widget.item(i).data(Qt.UserRole) == entity:
                self.entity_list_widget.takeItem(i)
                break
        
    

    def compute_player_stats(self):
        if not self.player_item:
            return {}

        data = self.player_item.data(0)
        total = {
            "hp_bonus": 0,
            "resistance": 0,
            "damage_bonus": 0,
            "speed_bonus": 0,
            "block_bonus": 0
            
        }

        for slot in ["helmet", "chest", "legs", "boots", "shield", "sword"]:
            equipped = data.get(f"equipped_{slot}")
            bonus = {}

            if equipped in PREDEFINED_ITEMS:
                bonus = PREDEFINED_ITEMS[equipped]
            elif "custom_items" in data and equipped in data["custom_items"]:
                bonus = data["custom_items"][equipped]

            for stat, value in bonus.items():
                if stat in total:
                    total[stat] += value

        return total

    # === A* PATHFINDING UTILS ===
    def build_grid_map(self):
        cols = self.grid_cols
        rows = self.grid_rows
        grid = [[0 for _ in range(cols)] for _ in range(rows)]

        for item in self.scene.items():
            if isinstance(item, QGraphicsRectItem):
                data = item.data(0)
                if not isinstance(data, dict):
                    continue
                if data.get("type") in ["Obstacle", "Enemy"]:
                    x = int(item.rect().x()) // GRID_SIZE
                    y = int(item.rect().y()) // GRID_SIZE
                    if 0 <= x < cols and 0 <= y < rows:
                        grid[y][x] = 1
        return grid

    def calculate_path(self, start, goal, size=1):
        cols, rows = self.grid_cols, self.grid_rows
        grid = self.build_grid_map()
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}

        def heuristic(a, b):
            return abs(int(a[0]) - int(b[0])) + abs(int(a[1]) - int(b[1]))


        while open_set:
            _, current = heapq.heappop(open_set)
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return path[::-1]  # invers pentru ordine corectă

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                x, y = neighbor
                enemy_size = 1

                is_valid = True
                for dx2 in range(enemy_size):
                    for dy2 in range(enemy_size):
                        xx = x + dx2
                        yy = y + dy2
                        if not (0 <= xx < cols and 0 <= yy < rows and grid[yy][xx] == 0):
                            is_valid = False
                            break
                    if not is_valid:
                        break

                if is_valid:
                    # restul codului (tentative etc.)

                    tentative = g_score[current] + 1
                    if neighbor not in g_score or tentative < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative
                        f = tentative + heuristic(goal, neighbor)
                        heapq.heappush(open_set, (f, neighbor))
        return []  # fără drum
    def start_inserting_waypoints(self, entity, mode):
        self.inserting_waypoints = True
        self.insert_mode = mode
        self.inserting_entity = entity

        if mode == "checkpoint":
            data = entity.data(0)

            if "final_point" in data:
                print("⚠️ Finish point already set. Cannot add checkpoints anymore.")
                return

            if "checkpoints" not in data:
                data["checkpoints"] = []

            if "start_point" not in data:
                x = int(entity.rect().x() // GRID_SIZE)
                y = int(entity.rect().y() // GRID_SIZE)
                data["start_point"] = (x, y)
            entity.setData(0, data)
            if "start_point" not in data:
                x = int(entity.rect().x() // GRID_SIZE)
                y = int(entity.rect().y() // GRID_SIZE)
                data["start_point"] = (x, y)
            entity.setData(0, data)
            

        self.view.setCursor(Qt.CrossCursor)

        def scene_click(event):
            if not self.inserting_waypoints:
                return

            pos = self.view.mapToScene(event.pos())
            x = int(pos.x() // GRID_SIZE)
            y = int(pos.y() // GRID_SIZE)

            # Ajustăm tile-ul pentru centrul entității (în funcție de dimensiune)
            size = self.inserting_entity.data(0).get("size", 1)
            tile = (x, y)

            rect = QGraphicsRectItem(
                x * GRID_SIZE,
                y * GRID_SIZE,
                GRID_SIZE * size,
                GRID_SIZE * size
            )

            pen = QPen()

            data = self.inserting_entity.data(0)
            self.normalize_waypoints(data)
            if mode == "checkpoint":
                data["checkpoints"].append(tile)
                pen.setColor(Qt.yellow)
            elif mode == "finish":
                data["final_point"] = tile
                pen.setColor(Qt.green)

                # Inițializează imediat patrularea
                if "start_point" in data:
                    if "checkpoints" in data and data["checkpoints"]:
                        forward = [data["start_point"]] + data["checkpoints"] + [data["final_point"]]
                        backward = list(reversed(data["checkpoints"])) + [data["start_point"]]
                    else:
                        forward = [data["start_point"], data["final_point"]]
                        backward = [data["start_point"]]

                    data["waypoints"] = forward + backward
                    data["patrol_index"] = 0

                self.inserting_waypoints = False
                self.view.setCursor(Qt.ArrowCursor)
                self.view.mousePressEvent = self.place_entity
            rect.setPen(pen)
            rect.setBrush(QBrush(Qt.NoBrush))
            rect.setZValue(10)
            self.scene.addItem(rect)

            self.inserting_entity.setData(0, data)

        self.view.mousePressEvent = scene_click

    def update_entity_properties(self, entity_item):
        if not entity_item:
            return
            
        data = entity_item.data(0)
        if not data:
            return
            
        # Actualizare câmpuri UI
        self.type_combo.setCurrentText(data.get("type", ""))
        self.facing_combo.setCurrentText(data.get("facing", "down"))
        self.size_spin.setValue(data.get("size", 1))
        self.speed_spin.setValue(data.get("speed", 1))
        self.damage_spin.setValue(data.get("damage", 0))
        self.hp_spin.setValue(data.get("hp", 100))
        
    def on_entity_selected(self):
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            entity_item = selected_items[0].data(Qt.UserRole)
            self.update_entity_properties(entity_item)

    def handle_enemy_damage(self, enemy):
        if enemy and enemy.behavior == 'idle':
            enemy.behavior = 'hostile'
            self.refresh_behavior_ui(enemy)
            print("Enemy behavior changed to hostile after taking damage!")
    

    def toggle_play_mode(self, state):
        if state == Qt.Checked:
            self.save_current_scene_state()
            self.behavior_timer.start(100)
            self.player_item = self.entity_manager.get_player_item()

            if self.player_item:
                self.setFocusProxy(self.view)
                self.view.setFocus()
                self.setFocus()

            print("▶ Simulare pornită")
        else:
            self.behavior_timer.stop()
            print("⏸ Simulare oprită")
    def save_current_scene_state(self):
        self.saved_scene_data = []
        for item in self.scene.items():
            if not isinstance(item, QGraphicsRectItem):
                continue
            entity_data = item.data(0)
            if not isinstance(entity_data, dict):
                continue
            rect = item.rect()
            self.saved_scene_data.append({
                "x": int(rect.x()),
                "y": int(rect.y()),
                "attributes": dict(entity_data)
            })
        print(f"💾 Scenă salvată intern: {len(self.saved_scene_data)} entități")
    def reset_to_saved_scene(self):
        if not hasattr(self, "saved_scene_data"):
            print("⚠ Nicio scenă salvată anterior.")
            return

        # Debifează Play Scene
        self.play_scene_checkbox.setChecked(False)

        # Debifează și Show Grid și ascunde grila
        self.grid_toggle.setChecked(False)
        self.toggle_grid()  # forțăm redesenarea grilei

        self.scene.clear()
        self.entity_list_widget.clear()

        for obj in self.saved_scene_data:
            x = obj.get("x", 0)
            y = obj.get("y", 0)
            attributes = obj.get("attributes", {})
            self.entity_manager.create_entity(x, y, attributes)

        self.player_item = self.entity_manager.get_player_item()
        if self.player_item:
            self.setFocusProxy(self.view)
            self.view.setFocus()
            self.setFocus()
        self.view.mousePressEvent = self.place_entity

        print("⏹ Scena a fost resetată la versiunea salvată.")
    def toggle_dead_mode(self):
        self.marking_dead = self.mark_dead_button.isChecked()

        if self.marking_dead:
            self.mark_dead_button.setStyleSheet("background-color: orange")
            self.view.setCursor(Qt.CrossCursor)
            for tile in self.dead_tiles:
                tile.show()
        else:
            self.mark_dead_button.setStyleSheet("")
            self.view.setCursor(Qt.ArrowCursor)
            for tile in self.dead_tiles:
                tile.hide()
    def normalize_waypoints(self, data):
        if "start_point" in data:
            x, y = data["start_point"]
            data["start_point"] = (int(x), int(y))

        if "final_point" in data:
            x, y = data["final_point"]
            data["final_point"] = (int(x), int(y))

        if "checkpoints" in data:
            data["checkpoints"] = [ (int(x), int(y)) for (x, y) in data["checkpoints"] ]

        if "waypoints" in data:
            data["waypoints"] = [ (int(x), int(y)) for (x, y) in data["waypoints"] ]
    def on_scene_selection_changed(self):
        selected = self.scene.selectedItems()
        if selected:
            entity = selected[0]
            # Caută în entity_list_widget itemul asociat
            for i in range(self.entity_list_widget.count()):
                list_item = self.entity_list_widget.item(i)
                if list_item.data(Qt.UserRole) == entity:
                    self.entity_list_widget.setCurrentItem(list_item)
                    self.select_item(list_item)
                    break
        else:
            self.selected_item = None

    def keyPressEvent(self, event):
        player = self.player_item
        if not player:
            return

        data = player.data(0)
        if not isinstance(data, dict) or not data.get("type", "").startswith("Player"):
            return

        game_mode = data.get("game_mode", "🎮 Action RPG")
        if game_mode == "🎮 Action RPG":
            self.handle_action_rpg_keys(event, player, data)

    def handle_action_rpg_keys(self, event, player_item, data):
        keymap = data.get("key_bindings", {
            "move_up": "W", "move_down": "S", "move_left": "A", "move_right": "D",
            "attack": "J", "interact": "E", "inventory": "I",
            "switch_weapon": "Q", "sprint": "Shift", "dodge": "Space", "block": "B"
        })

        pressed = event.text().upper()
        rect= player_item.rect() 
        x, y = rect.x(), rect.y()
        width, height = rect.width(), rect.height()
        new_x, new_y = x, y
        moved = False
        facing = data.get("facing", "down")
        speed = data.get("speed", 1)
        movement_delay = int(1000 / speed)
        from PyQt5.QtCore import QTime

        current_time = QTime.currentTime().msecsSinceStartOfDay()

        if hasattr(self, "_last_move_time"):
            elapsed = current_time - self._last_move_time
            if elapsed < movement_delay:
                return

        self._last_move_time = current_time

        if pressed == keymap.get("move_up", "W"):
            new_y -= GRID_SIZE
            facing = "up"
            direction = "up"
            self.hide_chest_inventory()
            moved = True
            if hasattr(self, "inventory_bar"):
                self.toggle_inventory_bar()
            self.animation_manager.handle_movement_animation(player_item, direction, moving=True)


        elif pressed == keymap.get("move_down", "S"):
            new_y += GRID_SIZE
            facing = "down"
            direction = "down"
            self.hide_chest_inventory()
            moved = True
            if hasattr(self, "inventory_bar"):
                self.toggle_inventory_bar()
            self.animation_manager.handle_movement_animation(player_item, direction, moving=True)

        elif pressed == keymap.get("move_left", "A"):
            new_x -= GRID_SIZE
            facing = "left"
            direction = "left"
            self.hide_chest_inventory()
            moved = True
            if hasattr(self, "inventory_bar"):
                self.toggle_inventory_bar()
            self.animation_manager.handle_movement_animation(player_item, direction, moving=True)


        elif pressed == keymap.get("move_right", "D"):
            new_x += GRID_SIZE
            facing = "right"
            direction = "right"
            self.hide_chest_inventory()
            moved = True
            if hasattr(self, "inventory_bar"):
                self.toggle_inventory_bar()
                self.animation_manager.handle_movement_animation(player_item, direction, moving=True)


        if not moved:
            self.animation_manager.handle_movement_animation(player_item, facing, moving=False)

        data["facing"] = facing
        if self.selected_item:
            self.selected_item.setData(0, data)
        elif player_item:
            player_item.setData(0, data)

        self.update_facing_arrow_position()

        if pressed == keymap.get("attack", "J"):
            weapon = data.get("equipped_weapon", "sword")
            self.play_attack_animation_with_sprite(weapon)
            self.player_attack(facing)
            self.hide_chest_inventory()
            return
        elif pressed == keymap.get("interact", "E"):
            interacted = False
            fx, fy = x, y
            if facing == "up": fy -= GRID_SIZE
            elif facing == "down": fy += GRID_SIZE
            elif facing == "left": fx -= GRID_SIZE
            elif facing == "right": fx += GRID_SIZE

            for item in self.scene.items():
                if isinstance(item, QGraphicsRectItem):
                    idata = item.data(0)
                    if not isinstance(idata, dict):
                        continue
                    if idata.get("type") == "Chest":
                        if int(item.rect().x()) == int(fx) and int(item.rect().y()) == int(fy):
                            self.show_chest_inventory(item)
                            interacted = True
                            break
            if not interacted:
                self.hide_chest_inventory()

        elif pressed == keymap.get("inventory", "I"):
            self.toggle_inventory_bar()
        elif pressed == keymap.get("switch_weapon", "Q"):
            inventory = data.get("inventory", [])
            item_types = data.get("item_types", {})

            # Arme din inventar
            weapons = [item for item in inventory if item_types.get(item, "").lower() in ["sword", "bow", "staff"]]

            # Arme echipate pe sloturi
            equipped_candidates = []
            for slot in ["equipped_sword", "equipped_bow", "equipped_staff"]:
                val = data.get(slot)
                if val and val not in weapons:
                    equipped_candidates.append(val)

            # Lista completă (fără duplicate)
            all_weapons = weapons + [w for w in equipped_candidates if w not in weapons]
            if not all_weapons:
                print("❌ No weapons to switch.")
                return

            # Arma actuală: cea din equipped_weapon (sau fallback pe sloturi dedicate)
            current = data.get("equipped_weapon", None)
            if not current:
                for slot in ["equipped_sword", "equipped_bow", "equipped_staff"]:
                    val = data.get(slot)
                    if val:
                        current = val
                        break

            # Switch pe lista de arme
            if current not in all_weapons:
                next_weapon = all_weapons[0]
            else:
                idx = all_weapons.index(current)
                next_weapon = all_weapons[(idx + 1) % len(all_weapons)]

            data["equipped_weapon"] = next_weapon
            print(f"🗡 Equipped: {next_weapon}")
            player_item.setData(0, data)
            self.toggle_inventory_bar()
        elif pressed == keymap.get("dodge", "SPACE"):
            print("🌀 Dodge roll!")
            self.toggle_inventory_bar()
        elif pressed == keymap.get("block", "B"):
            print("🛡 Blocking")
            self.toggle_inventory_bar()

        # verificare coliziuni
        for item in self.scene.items():
            if isinstance(item, QGraphicsRectItem) and item is not self.player_item:
                idata = item.data(0)
                if not isinstance(idata, dict):
                    continue
                if idata.get("type") in ["Obstacle", "Enemy", "Player", "NPC","Chest","Door","DeadTile"]:
                    new_rect = QRectF(new_x, new_y, width, height)
                    if item.rect().intersects(new_rect):
                        moved = False
                        break

        if moved and 0 <= new_x < self.scene.width() and 0 <= new_y < self.scene.height():
            self.selected_item.setRect(new_x, new_y, width, height)

            sprite_item = self.selected_item.data(2)
            if sprite_item and isinstance(sprite_item, QGraphicsPixmapItem):
                sprite_x = new_x + (width - sprite_item.pixmap().width()) / 2
                sprite_y = new_y + (height - sprite_item.pixmap().height()) / 2
                sprite_item.setPos(sprite_x, sprite_y)

            hp_bar = self.selected_item.data(1)
            if hp_bar and isinstance(hp_bar, QGraphicsRectItem):
                hp_bar.setRect(new_x, new_y - 7, width, 5)

            self.update_inventory_bar_position()
            self.update_facing_arrow_position()
                # -- DEBLOCARE colectare pentru itemele abia aruncate --
            for item in self.scene.items():
                if isinstance(item, QGraphicsRectItem):
                    idata = item.data(0)
                    if isinstance(idata, dict) and idata.get("type") == "Collectible":
                        rect = item.rect()
                        if not (int(rect.x()) == int(player_item.rect().x()) and int(rect.y()) == int(player_item.rect().y())):
                            if idata.get("_just_dropped"):
                                idata["_just_dropped"] = False

        for other in self.scene.items():
            if isinstance(other, QGraphicsRectItem) and other is not self.player_item:
                orect = other.rect()
                odata = other.data(0)
                if not isinstance(odata, dict):
                    continue

                if odata.get("type") == "Collectible":
                    if int(orect.x()) == int(new_x) and int(orect.y()) == int(new_y):
                        if odata.get("_just_dropped", False):
                            continue
                        name = odata.get("name", "Unknown")
                        player_data = self.player_item.data(0)
                        player_data.setdefault("inventory", []).append(name)
                        self.player_item.setData(0, player_data)

                        if self.selected_item == self.player_item:
                            self.inventory_display.addItem(name)

                        self.scene.removeItem(other)
                        print(f"Collected: {name}")

                elif odata.get("type") == "DialogTrigger":
                    if int(orect.x()) == int(new_x) and int(orect.y()) == int(new_y):
                        print("📜 Dialog declanșat: 'Ai intrat într-o zonă misterioasă...'")


        if event.key() in [Qt.Key_E, Qt.Key_Return]:
            player = self.player_item
            if not player:
                return

            pdata = player.data(0)
            if not isinstance(pdata, dict):
                return

            facing = pdata.get("facing", "down")
            px, py = int(player.rect().x()), int(player.rect().y())

            # Calculăm tile-ul din față
            fx, fy = px, py
            if facing == "up":
                fy -= GRID_SIZE
            elif facing == "down":
                fy += GRID_SIZE
            elif facing == "left":
                fx -= GRID_SIZE
            elif facing == "right":
                fx += GRID_SIZE
            # Verificăm dacă există o ușă fix în față
            for item in self.scene.items():
                if not isinstance(item, QGraphicsRectItem):
                    continue
                data = item.data(0)
                if not isinstance(data, dict):
                    continue
                if data.get("type") == "Door":
                    rx, ry = int(item.rect().x()), int(item.rect().y())
                    if rx == fx and ry == fy:
                        scene_file = data.get("target_scene")
                        if scene_file:
                            from PyQt5.QtWidgets import QMessageBox
                            confirm = QMessageBox.question(self, "Load Scene", f"Vrei să intri în scenă?\n{scene_file}")
                            if confirm == QMessageBox.Yes:
                                continue

                            
                        return  # prevenim să continue și cu alte interacțiuni

            # Verificăm dacă există NPC fix în față
            for item in self.scene.items():
                if not isinstance(item, QGraphicsRectItem):
                    continue
                data = item.data(0)
                if not isinstance(data, dict):
                    continue
                if data.get("type") == "NPC":
                    rx, ry = int(item.rect().x()), int(item.rect().y())
                    if rx == fx and ry == fy:
                        if self.entity_manager.handle_interaction(player, event):
                            event.accept()
                        return  # interacționăm doar cu un singur NPC
    def player_attack(self, facing):
        if not self.player_item:
            return

        player_data = self.player_item.data(0)
        custom_items = player_data.get("custom_items", {})
        equipped_weapon = player_data.get("equipped_weapon", "")
        weapon_stats = custom_items.get(equipped_weapon, {})

        weapon_type = player_data.get("item_types", {}).get(equipped_weapon, "").lower()
        base_damage = player_data.get("damage", 10)
        bonus_damage = weapon_stats.get("damage_bonus", 0)
        range_limit = weapon_stats.get("range", 1 if weapon_type == "sword" else 3)

        total_damage = base_damage + bonus_damage
        if range_limit <= 0:
            range_limit = 1

        # Poziția playerului (tile-uri)
        start_x = int(self.player_item.rect().x() // GRID_SIZE)
        start_y = int(self.player_item.rect().y() // GRID_SIZE)

        # Direcție
        dx, dy = 0, 0
        if facing == "up":
            dy = -1
        elif facing == "down":
            dy = 1
        elif facing == "left":
            dx = -1
        elif facing == "right":
            dx = 1

        for step in range(1, range_limit + 1):
            tx = start_x + dx * step
            ty = start_y + dy * step
            target_rect = QRectF(tx * GRID_SIZE, ty * GRID_SIZE, GRID_SIZE, GRID_SIZE)

            for item in self.scene.items():
                if item == self.player_item or not isinstance(item, QGraphicsRectItem):
                    continue

                data = item.data(0)
                if not isinstance(data, dict):
                    continue

                if item.rect().intersects(target_rect):
                    if data.get("type") == "Enemy":
                        # Aplica damage
                        enemy_hp = data.get("hp", 100)
                        data["hp"] = max(0, enemy_hp - total_damage)
                        item.setData(0, data)

                        # Schimbă comportament dacă era idle
                        if data.get("behavior") == "idle":
                            data["behavior"] = "hostile"
                            item.setData(0, data)
                            print("⚠️ Enemy became hostile!")

                        print(f"💥 Player attacked enemy with {equipped_weapon}! Damage: {total_damage}, HP left: {data['hp']}")

                        # Update HP bar
                        hp_bar = item.data(1)
                        if hp_bar and isinstance(hp_bar, QGraphicsRectItem):
                            full_width = item.rect().width()
                            new_width = max(0, int((data["hp"] / 100) * full_width))
                            hp_bar.setRect(item.rect().x(), item.rect().y() - 7, new_width, 5)

                        # Drop loot dacă moare
                        if data["hp"] <= 0:
                            loot = data.get("inventory", [])
                            for i, obj_name in enumerate(loot):
                                drop_x = tx * GRID_SIZE + (i % 2) * GRID_SIZE
                                drop_y = ty * GRID_SIZE + (i // 2) * GRID_SIZE
                                drop_data = {"type": "Collectible", "name": obj_name}
                                self.entity_manager.create_entity(drop_x, drop_y, drop_data)

                            if hp_bar:
                                self.scene.removeItem(hp_bar)
                            self.scene.removeItem(item)
                        return

                    elif data.get("type") in ["Obstacle", "Chest", "NPC", "Door"]:
                        print(f"🔸 Attack stopped by {data.get('type')} at ({tx},{ty})")
                        return

        print("🎯 No enemy hit in range.")
    # === UTILS INVENTAR ===
    def create_item_entity(self, owner_entity, item_name, data):
        """
        Creează o entitate invizibilă pentru un item de inventar.
        Poziționată suprapus pe owner.
        """
        if not owner_entity:
            return

        owner_rect = owner_entity.rect()
        x, y = int(owner_rect.x()), int(owner_rect.y())

        drop_data = {
            "type": "Collectible",
            "name": item_name,
            "visible": False,  # invizibil în inventar
            "owner": owner_entity,  # referință logică
            "_inventory_bound": True  # marcare internă
        }

        if "custom_items" in data and item_name in data["custom_items"]:
            drop_data["custom_items"] = {item_name: data["custom_items"][item_name]}
        if "item_types" in data and item_name in data["item_types"]:
            drop_data["item_types"] = {item_name: data["item_types"][item_name]}
        if "image" in data.get("custom_items", {}).get(item_name, {}):
            drop_data["image"] = data["custom_items"][item_name]["image"]

        item_entity = self.entity_manager.create_entity(x, y, drop_data)
        item_entity.setVisible(False)
        item_entity.setZValue(-1)
        return item_entity


    def drop_inventory_item(self):
        item = self.inventory_display.currentItem()
        if not item or not self.player_item:
            return

        data = self.player_item.data(0)
        inventory = data.get("inventory", [])
        item_name = item.text().replace(" (echipat)", "")

        # elimină itemul din inventar
        if item_name not in inventory:
            return

        inventory.remove(item_name)
        self.player_item.setData(0, data)
        self.inventory_display.takeItem(self.inventory_display.row(item))

        # Găsește entitatea itemului în scenă
        for entity in self.scene.items():
            if not isinstance(entity, QGraphicsRectItem):
                continue
            edata = entity.data(0)
            if not isinstance(edata, dict):
                continue
            if edata.get("name") == item_name and edata.get("_inventory_bound"):
                # poziționează în fața playerului
                px, py = self.player_item.rect().x(), self.player_item.rect().y()
                facing = data.get("facing", "down")
                dx, dy = 0, 0
                if facing == "up": dy = -1
                elif facing == "down": dy = 1
                elif facing == "left": dx = -1
                elif facing == "right": dx = 1

                drop_x = px + dx * GRID_SIZE
                drop_y = py + dy * GRID_SIZE
                entity.setRect(drop_x, drop_y, GRID_SIZE, GRID_SIZE)
                entity.setVisible(True)
                edata.pop("owner", None)
                edata.pop("_inventory_bound", None)
                entity.setData(0, edata)
                entity.setZValue(1)
                return


    def equip_or_swap_inventory_item(self, item):
        if not self.player_item:
            return

        data = self.player_item.data(0)
        item_name = item.text().replace(" (echipat)", "")
        inventory = data.get("inventory", [])
        item_type = data.get("item_types", {}).get(item_name, "").lower()

        slot_map = {
            "helmet": "equipped_helmet",
            "chest": "equipped_chest",
            "legs": "equipped_legs",
            "boots": "equipped_boots",
            "shield": "equipped_shield",
            "sword": "equipped_sword",
            "bow": "equipped_bow",
            "staff": "equipped_staff",
            "hp potion": "equipped_hp potion",
            "boost": "equipped_boost"
        }

        if item_type in slot_map:
            slot_key = slot_map[item_type]
            current_equipped = data.get(slot_key)

            # Scoate itemul din inventar
            if item_name in inventory:
                inventory.remove(item_name)

            # Pune itemul nou pe slotul echipat și pe cel vechi înapoi în inventar
            if current_equipped:
                inventory.append(current_equipped)
            data[slot_key] = item_name
            self.player_item.setData(0, data)

            # Setează arma echipată global dacă e tip ofensiv
            if item_type in ["sword", "bow", "staff"]:
                data["equipped_weapon"] = item_name

            # Resetare statusuri de bază
            data["hp"] = 100
            data["damage"] = 10
            data["speed"] = 1
            data["block"] = 0
            data["resistance"] = 0
            data["range"] = 1

            # Aplică bonusurile din toate sloturile echipate
            for key in slot_map.values():
                eq_item = data.get(key)
                if eq_item:
                    bonuses = data.get("custom_items", {}).get(eq_item, {})
                    for bkey, bval in bonuses.items():
                        if bkey == "hp_bonus": data["hp"] += bval
                        elif bkey == "damage_bonus": data["damage"] += bval
                        elif bkey == "speed_bonus": data["speed"] += bval
                        elif bkey == "block_bonus": data["block"] += bval
                        elif bkey == "resistance": data["resistance"] += bval
                        elif bkey == "range": data["range"] = max(data.get("range", 1), bval)

            self.player_item.setData(0, data)
            self.update_inventory_display(inventory)
            self.toggle_inventory_bar()
            self.inventory_display.clear()
            for itm in inventory:
                self.inventory_display.addItem(itm)

            print(f"✅ {item_name} echipat pe slotul {slot_key}.")
    def recalc_player_stats(self):
        if not self.player_item:
            return

        data = self.player_item.data(0)

        # Resetăm la valorile de bază
        data["hp"] = 100
        data["damage"] = 10
        data["speed"] = 1
        data["block"] = 0
        data["resistance"] = 0
        data["range"] = 1

        for slot in [
            "equipped_helmet", "equipped_chest", "equipped_legs", "equipped_boots",
            "equipped_shield", "equipped_sword", "equipped_bow", "equipped_staff",
            "equipped_hp potion", "equipped_boost"
        ]:
            item_name = data.get(slot)
            if not item_name:
                continue
            bonuses = data.get("custom_items", {}).get(item_name, {})
            for key, value in bonuses.items():
                if key == "hp_bonus":
                    data["hp"] += value
                elif key == "damage_bonus":
                    data["damage"] += value
                elif key == "speed_bonus":
                    data["speed"] += value
                elif key == "block_bonus":
                    data["block"] += value
                elif key == "resistance":
                    data["resistance"] += value
                elif key == "range":
                    data["range"] = max(data["range"], value)

        self.player_item.setData(0, data)
    
    def update_inventory_entities_position(self):
        """
        Sincronizează poziția entităților invizibile din inventar cu owner-ul lor.
        """
        for item in self.scene.items():
            if not isinstance(item, QGraphicsRectItem):
                continue
            data = item.data(0)
            if not isinstance(data, dict):
                continue
            if not data.get("_inventory_bound"):
                continue
            owner = data.get("owner")
            if not owner:
                continue
            owner_rect = owner.rect()
            item.setRect(owner_rect.x(), owner_rect.y(), GRID_SIZE, GRID_SIZE)
    def toggle_inventory_bar(self):
        self.update_inventory_entities_position()  # sincronizează itemele invizibile

        if hasattr(self, "inventory_bar"):
            for item in self.inventory_bar:
                self.scene.removeItem(item)
            del self.inventory_bar
            return

        if not self.player_item:
            return

        data = self.player_item.data(0)
        inventory = data.get("inventory", [])

        self.inventory_bar = []
        slot_size = int(self.player_item.rect().width()) * 0.8
        spacing = 2
        columns = 4
        rows = 5

        player_rect = self.player_item.rect()
        base_x = player_rect.x()
        base_y = player_rect.y() + player_rect.height() + spacing

        index = 0
        labels = [
            "Helmet", "Chest", "Legs", "Boots", "Shield",
            "Sword", "Bow", "Staff", "HP Potion", "Boost",
        ]

        equipped_items = []
        slot_map = {
            "Helmet": "equipped_helmet",
            "Chest": "equipped_chest",
            "Legs": "equipped_legs",
            "Boots": "equipped_boots",
            "Shield": "equipped_shield",
            "Sword": "equipped_sword",
            "Bow": "equipped_bow",
            "Staff": "equipped_staff",
            "HP Potion": "equipped_hp potion",
            "Boost": "equipped_boost"
        }

        for col in range(columns):
            for row in range(rows):
                slot_index = col * rows + row
                slot_x = base_x + col * (slot_size + spacing)
                slot_y = base_y + row * (slot_size + spacing)
                rect = QGraphicsRectItem(slot_x, slot_y, slot_size, slot_size)
                rect.setBrush(QBrush(QColor("#eeeeee")))
                rect.setPen(QColor("black"))
                rect.setZValue(3)
                self.scene.addItem(rect)
                self.inventory_bar.append(rect)

                if slot_index < len(labels):
                    slot_name = labels[slot_index]
                    label = QGraphicsTextItem(slot_name)
                    label.setDefaultTextColor(Qt.black)
                    label.setScale(0.5)
                    label.setZValue(4)
                    label.setPos(slot_x + 2, slot_y + 2)
                    self.scene.addItem(label)
                    self.inventory_bar.append(label)

                    equip_key = slot_map[slot_name]
                    eq_item = data.get(equip_key, None)
                    if eq_item:
                        eq_label = QGraphicsTextItem(str(eq_item))
                        eq_label.setDefaultTextColor(Qt.darkGreen)
                        eq_label.setScale(0.5)
                        eq_label.setZValue(5)
                        eq_label.setPos(slot_x + 2, slot_y + 18)
                        self.scene.addItem(eq_label)
                        self.inventory_bar.append(eq_label)

                        img_path = ""
                        if "custom_items" in data and eq_item in data["custom_items"]:
                            img_path = data["custom_items"][eq_item].get("image", "")
                        if img_path:
                            pixmap = QPixmap(img_path)
                            if not pixmap.isNull():
                                img_item = QGraphicsPixmapItem(
                                    pixmap.scaled(
                                        int(slot_size - 12),
                                        int(slot_size - 12),
                                        Qt.KeepAspectRatio,
                                        Qt.SmoothTransformation
                                    )
                                )
                                img_item.setPos(slot_x + 6, slot_y + 6)
                                img_item.setZValue(6)
                                self.scene.addItem(img_item)
                                self.inventory_bar.append(img_item)

                else:
                    storage_index = slot_index - len(labels)
                    storage_items = [item for item in inventory if item not in equipped_items]
                    if storage_index < len(storage_items):
                        item_name = storage_items[storage_index]
                        label = QGraphicsTextItem(item_name)
                        label.setDefaultTextColor(Qt.darkBlue)
                        label.setScale(0.5)
                        label.setZValue(4)
                        label.setPos(slot_x + 2, slot_y + 2)
                        self.scene.addItem(label)
                        self.inventory_bar.append(label)

                        img_path = ""
                        if "custom_items" in data and item_name in data["custom_items"]:
                            img_path = data["custom_items"][item_name].get("image", "")
                        if img_path:
                            pixmap = QPixmap(img_path)
                            if not pixmap.isNull():
                                img_item = QGraphicsPixmapItem(pixmap.scaled(int(slot_size - 12), int(slot_size - 12), Qt.KeepAspectRatio, Qt.SmoothTransformation))
                                img_item.setPos(slot_x + 6, slot_y + 6)
                                img_item.setZValue(6)
                                self.scene.addItem(img_item)
                                self.inventory_bar.append(img_item)

                        rect.mousePressEvent = lambda event, idx=storage_index: self.handle_inventory_storage_click(idx)

                index += 1
    def add_inventory_item(self, item_name, item_type, bonuses, image_path=""):
        if not self.selected_item:
            return

        data = self.selected_item.data(0)
        inventory = data.get("inventory", [])
        inventory.append(item_name)
        data["inventory"] = inventory

        if "custom_items" not in data:
            data["custom_items"] = {}
        data["custom_items"][item_name] = bonuses.copy()

        if "item_types" not in data:
            data["item_types"] = {}
        data["item_types"][item_name] = item_type

        if image_path:
            data["custom_items"][item_name]["image"] = image_path

        self.selected_item.setData(0, data)

        # Creează entitatea invizibilă în scenă pentru acest item
        self.create_item_entity(self.selected_item, item_name, data)

        print(f"🎒 {item_name} a fost adăugat în inventar ca entitate invizibilă.")
    def open_add_item_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Adaugă Item în Inventar")
        layout = QFormLayout(dialog)

        name_input = QLineEdit()
        layout.addRow("Nume item:", name_input)

        combo = QComboBox()
        combo.addItems(PREDEFINED_ITEMS.keys())
        layout.addRow("Tip item:", combo)

        hp_input = QLineEdit("0")
        dmg_input = QLineEdit("0")
        res_input = QLineEdit("0")
        spd_input = QLineEdit("0")
        blk_input = QLineEdit("0")
        layout.addRow("HP Bonus:", hp_input)
        layout.addRow("Damage Bonus:", dmg_input)
        layout.addRow("Resistance:", res_input)
        layout.addRow("Speed Bonus:", spd_input)
        layout.addRow("Block Bonus:", blk_input)

        range_input = QLineEdit("3")
        layout.addRow("Range (pentru arc/staff):", range_input)

        # Ascunde implicit câmpul pentru range
        range_input.setVisible(False)
        layout.labelForField(range_input).setVisible(False)

        def toggle_range_visibility(item_type):
            show = item_type.lower() in ["bow", "staff"]
            range_input.setVisible(show)
            layout.labelForField(range_input).setVisible(show)

        combo.currentTextChanged.connect(toggle_range_visibility)
        toggle_range_visibility(combo.currentText())  # inițial

        img_path = [""]

        img_btn = QPushButton("Alege imagine")
        img_label = QLabel("Fără imagine")
        layout.addRow(img_btn, img_label)

        def pick_img():
            path, _ = QFileDialog.getOpenFileName(self, "Alege imagine", "", "Images (*.png *.jpg *.bmp)")
            if path:
                img_path[0] = path
                img_label.setText(path.split("/")[-1])

        img_btn.clicked.connect(pick_img)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(dialog.accept)
        layout.addWidget(ok_btn)

        dialog.setLayout(layout)
        if dialog.exec_() != QDialog.Accepted:
            return

        item_name = name_input.text().strip() or combo.currentText()
        item_type = combo.currentText()
        bonuses = {
            "hp_bonus": int(hp_input.text()),
            "damage_bonus": int(dmg_input.text()),
            "resistance": int(res_input.text()),
            "speed_bonus": int(spd_input.text()),
            "block_bonus": int(blk_input.text())
        }

        if item_type.lower() in ["bow", "staff"]:
            bonuses["range"] = int(range_input.text())

        self.add_inventory_item(item_name, item_type, bonuses, img_path[0])


    def take_item_from_chest(self, chest_entity, item_name):
        if not self.player_item:
            return

        chest_data = chest_entity.data(0)
        chest_inventory = chest_data.get("inventory", [])
        if item_name not in chest_inventory:
            print(f"❌ {item_name} nu este în cufăr.")
            return

        # Eliminăm din cufăr
        chest_inventory.remove(item_name)
        chest_data["inventory"] = chest_inventory
        chest_custom_items = chest_data.get("custom_items", {})
        chest_item_types = chest_data.get("item_types", {})
        chest_entity.setData(0, chest_data)

        # Adaugăm în player
        data = self.player_item.data(0)
        inventory = data.get("inventory", [])
        inventory.append(item_name)
        data["inventory"] = inventory

        if "custom_items" not in data:
            data["custom_items"] = {}
        if "item_types" not in data:
            data["item_types"] = {}

        if item_name in chest_custom_items:
            data["custom_items"][item_name] = dict(chest_custom_items[item_name])
        if item_name in chest_item_types:
            data["item_types"][item_name] = chest_item_types[item_name]

        self.player_item.setData(0, data)

        # Mutăm entitatea itemului (dacă există deja în scenă) și o facem invizibilă
        for entity in self.scene.items():
            if not isinstance(entity, QGraphicsRectItem):
                continue
            edata = entity.data(0)
            if isinstance(edata, dict) and edata.get("name") == item_name and edata.get("owner") == chest_entity:
                edata["owner"] = self.player_item
                entity.setData(0, edata)
                entity.setVisible(False)
                entity.setZValue(-1)
                return

        # Dacă nu există deja, creează-l
        self.create_item_entity(self.player_item, item_name, data)
        self.update_inventory_display(data.get("inventory", []))
        
        print(f"✅ {item_name} a fost mutat din cufăr în inventarul playerului.")

    def handle_inventory_storage_click(self, idx):
        data = self.player_item.data(0)
        inventory = data.get("inventory", [])

        if idx >= len(inventory):
            return  # slot gol

        item_name = inventory[idx]
        item_type = data.get("item_types", {}).get(item_name, "").lower()

        slot_map = {
            "helmet": "equipped_helmet",
            "chest": "equipped_chest",
            "legs": "equipped_legs",
            "boots": "equipped_boots",
            "shield": "equipped_shield",
            "sword": "equipped_sword",
            "bow": "equipped_bow",
            "staff": "equipped_staff"
        }

        if item_type not in slot_map:
            return

        slot_key = slot_map[item_type]
        current_equipped = data.get(slot_key)

        # 1. Scoate itemul din inventory
        del inventory[idx]

        # 2. Pune înapoi cel curent (dacă e diferit)
        if current_equipped and current_equipped not in inventory:
            inventory.append(current_equipped)

        # 3. Echipare
        data[slot_key] = item_name
        if item_type in ["sword", "bow", "staff"]:
            data["equipped_weapon"] = item_name
        self.recalc_player_stats()
        # 4. Reset + bonusuri
        data["hp"] = 100
        data["damage"] = 10
        data["speed"] = 1
        data["block"] = 0
        data["resistance"] = 0
        data["range"] = 1

        for eq_key in slot_map.values():
            eq_item = data.get(eq_key)
            if eq_item:
                bonuses = data.get("custom_items", {}).get(eq_item, {})
                for b_key, b_val in bonuses.items():
                    if b_key == "hp_bonus":
                        data["hp"] += b_val
                    elif b_key == "damage_bonus":
                        data["damage"] += b_val
                    elif b_key == "speed_bonus":
                        data["speed"] += b_val
                    elif b_key == "block_bonus":
                        data["block"] += b_val
                    elif b_key == "resistance":
                        data["resistance"] += b_val
                    elif b_key == "range":
                        data["range"] = max(data.get("range", 1), b_val)

        self.player_item.setData(0, data)
        self.update_inventory_display(inventory)
        self.toggle_inventory_bar()
        self.inventory_display.clear()
        for item in inventory:
            self.inventory_display.addItem(item)

        print(f"✅ {item_name} echipat pe slotul {slot_key}")

    def update_inventory_display(self, inventory, equipped=None):
        if not self.player_item:
            return

        data = self.player_item.data(0)
        equipped_items = [
            data.get("equipped_helmet"),
            data.get("equipped_chest"),
            data.get("equipped_legs"),
            data.get("equipped_boots"),
            data.get("equipped_shield"),
            data.get("equipped_sword"),
            data.get("equipped_bow"),
            data.get("equipped_staff"),
            data.get("equipped_hp potion"),
            data.get("equipped_boost"),
        ]
        equipped_items = [item for item in equipped_items if item]

        self.inventory_display.clear()
        for name in inventory:
            if name not in equipped_items:
                img_path = ""
                if "custom_items" in data and name in data["custom_items"]:
                    img_path = data["custom_items"][name].get("image", "")
                item = QListWidgetItem(name)
                if img_path:
                    item.setIcon(QIcon(img_path))
                self.inventory_display.addItem(item)

        # Evidențiere vizuală pentru itemul echipat (dacă e cazul)
        if equipped:
            for i in range(self.inventory_display.count()):
                item = self.inventory_display.item(i)
                if item.text() == equipped:
                    item.setBackground(QColor("yellow"))
    def select_predefined_item(self, slot_name):
        from PyQt5.QtWidgets import QInputDialog, QMessageBox

        options = list(PREDEFINED_ITEMS.keys())
        item, ok = QInputDialog.getItem(self, f"Selectează item pentru {slot_name}", "Item:", options, editable=False)
        if not ok or not item:
            return

        valid_map = {
            "Helmet": ["helmet"],
            "Chest": ["chest"],
            "Legs": ["legs"],
            "Boots": ["boots"],
            "Shield": ["shield"],
            "Sword": ["sword"],
            "Bow": ["bow"],
            "Staff": ["staff"]
        }

        item_type = item.lower()
        expected = valid_map.get(slot_name, [])
        if not any(t in item_type for t in expected):
            QMessageBox.warning(self, "Item Invalid", f"❌ Itemul „{item}” nu este compatibil cu slotul „{slot_name}”.")
            return

        data = self.player_item.data(0)
        bonuses = {}
        if "custom_items" in data and item in data["custom_items"]:
            bonuses = data["custom_items"][item]
        elif item in PREDEFINED_ITEMS:
            bonuses = PREDEFINED_ITEMS[item]

        data[f"equipped_{slot_name.lower()}"] = item

        # Reset + aplicare bonusuri
        data["hp"] = 100
        data["damage"] = 10
        data["speed"] = 1
        data["block"] = 0
        data["resistance"] = 0
        data["range"] = 1

        for key, value in bonuses.items():
            if key == "hp_bonus":
                data["hp"] += value
            elif key == "damage_bonus":
                data["damage"] += value
            elif key == "speed_bonus":
                data["speed"] += value
            elif key == "block_bonus":
                data["block"] += value
            elif key == "resistance":
                data["resistance"] += value
            elif key == "range":
                data["range"] = max(data.get("range", 1), value)

        self.player_item.setData(0, data)
        print(f"🎒 {slot_name} echipat cu {item}. Bonusuri aplicate: {bonuses}")

    def remove_inventory_item(self):
        if not self.selected_item:
            return

        current = self.inventory_display.currentItem()
        if not current:
            return

        item_name = current.text().replace(" (echipat)", "")
        data = self.selected_item.data(0)
        inventory = data.get("inventory", [])

        if item_name in inventory:
            inventory.remove(item_name)
            data["inventory"] = inventory
            self.selected_item.setData(0, data)
            self.inventory_display.takeItem(self.inventory_display.row(current))

            # Șterge entitatea invizibilă asociată cu acest item (dacă există)
            for entity in self.scene.items():
                if not isinstance(entity, QGraphicsRectItem):
                    continue
                edata = entity.data(0)
                if not isinstance(edata, dict):
                    continue
                if edata.get("name") == item_name and edata.get("owner") == self.selected_item:
                    self.scene.removeItem(entity)
                    print(f"🗑 Entitatea itemului „{item_name}” a fost ștearsă din scenă.")
                    break


    def export_game_to_exe(self):
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        import shutil
        import os
        import json
        import subprocess

        # 1. Selectează scenele în ordine
        scene_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Scenes for Export", "", "JSON Files (*.json)")

        if not scene_paths:
            return

        # 2. Selectează folderul destinație
        export_dir = QFileDialog.getExistingDirectory(self, "Select Export Folder")
        if not export_dir:
            return

        # 3. Copiază fișierele de scenă
        scene_order = []
        scenes_export_path = os.path.join(export_dir, "scenes")
        os.makedirs(scenes_export_path, exist_ok=True)
        for i, path in enumerate(scene_paths):
            basename = os.path.basename(path)
            new_name = f"scene_{i+1:02}.json"
            shutil.copy(path, os.path.join(scenes_export_path, new_name))
            scene_order.append(new_name)

        # 4. Creează config de ordine scene
        with open(os.path.join(scenes_export_path, "order.json"), "w") as f:
            json.dump(scene_order, f, indent=2)

        # 5. Creează fișier `game_launcher.py`
                # 5. Creează fișier `game_launcher.py` -- FOLOSEȘTE GamePlayerWindow, nu GameEditor!
        launcher_code = f"""
import json
import os
from PyQt5.QtWidgets import QApplication
from editor import GamePlayerWindow

def launch_game():
    app = QApplication([])
    with open(os.path.join("scenes", "order.json")) as f:
        order = json.load(f)
    if order:
        first_scene = os.path.join("scenes", order[0])
        window = GamePlayerWindow(first_scene)
        window.show()
        app.exec_()

if __name__ == "__main__":
    launch_game()
"""
        with open(os.path.join(export_dir, "game_launcher.py"), "w") as f:
            f.write(launcher_code)

        with open(os.path.join(export_dir, "game_launcher.py"), "w") as f:
            f.write(launcher_code)

        # 6. (Opțional) Export EXE cu pyinstaller
        try:
            subprocess.run([
                "pyinstaller",
                "--noconfirm",
                "--onefile",
                "--add-data", "scenes;scenes",
                "--hidden-import", "PyQt5.sip",
                os.path.join(export_dir, "game_launcher.py")
            ], check=True)
            QMessageBox.information(self, "Export", "✅ Export completat cu succes!\nGăsești fișierul EXE în folderul /dist")
        except Exception as e:
            QMessageBox.warning(self, "Eroare export", f"❌ Eroare la export: {e}")


from PyQt5.QtWidgets import QGraphicsScene, QGraphicsView, QMainWindow
from PyQt5.QtCore import Qt

class GamePlayerWindow(QMainWindow):
    def __init__(self, scene_file):
        super().__init__()
        self.setWindowTitle("2D Game - Play Mode")
        self.setGeometry(100, 100, 1000, 600)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.view.setFocusPolicy(Qt.StrongFocus)
        self.setCentralWidget(self.view)

        # Managers only for logic
        from entities import EntityManager
        from animations import AnimationManager
        from scenes import SceneManager

        self.entity_manager = EntityManager(self.scene, None)
        self.animation_manager = AnimationManager(self.scene)
        self.scene_manager = SceneManager(self.scene, self.entity_manager, None, self.animation_manager)
        self.scene_manager.view = self.view

        # Load the exported scene (everything gets restored: terrain, dead tiles, design, NPC, etc.)
        self.scene_manager.load_scene_from_path(scene_file)
        self.player_item = self.entity_manager.get_player_item()

        # Disable selection/move on all entities
        for item in self.scene.items():
            if hasattr(item, "setFlag"):
                item.setFlag(item.ItemIsSelectable, False)
                item.setFlag(item.ItemIsFocusable, False)
        if self.player_item:
            self.player_item.setFlag(self.player_item.ItemIsSelectable, False)
            self.player_item.setFlag(self.player_item.ItemIsFocusable, False)

        self.view.setFocus()
        self.setFocus()

    def keyPressEvent(self, event):
        # Doar playerul reacționează la taste!
        if not self.player_item:
            return
        data = self.player_item.data(0)
        if not isinstance(data, dict):
            return
        from editor import GameEditor
        GameEditor.handle_action_rpg_keys(self, event, self.player_item, data)