from PyQt5.QtWidgets import QGraphicsRectItem, QListWidgetItem, QGraphicsPixmapItem,QInputDialog, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QColor, QPixmap, QFont
from PyQt5.QtCore import QRectF, Qt, pyqtSignal, QObject

ENTITY_TYPES = {
    # 🎮 Action RPG
    "PlayerRPG": {"color": "blue"},
    "Enemy": {"color": "red"},
    "NPC": {"color": "cyan"},
    "Collectible": {"color": "gold"},
    "Obstacle": {"color": "gray"},
    "Chest": {"color": "sienna"},
    "Door": {"color": "darkGreen"},
    "Projectile": {"color": "orange"},
    "TriggerZone": {"color": "purple"},

    # 🔫 Shooter
    "PlayerShooter": {"color": "green"},
    "Bullet": {"color": "orange"},
    "WeaponPickup": {"color": "darkBlue"},
    "AmmoPickup": {"color": "lightGray"},
    "Explosion": {"color": "red"},
    "SpawnPoint": {"color": "green"},

    # 🧩 Puzzle / Sokoban
    "PlayerPuzzle": {"color": "magenta"},
    "Box": {"color": "brown"},
    "TargetSpot": {"color": "lightGreen"},
    "Wall": {"color": "black"},
    "Switch": {"color": "magenta"},
    "Gate": {"color": "darkRed"},

    # 🏎 Racing
    "PlayerRacing": {"color": "cyan"},
    "PlayerCar": {"color": "blue"},
    "AICar": {"color": "darkRed"},
    "TrackBoundary": {"color": "black"},
    "Checkpoint": {"color": "lightBlue"},
    "Boost": {"color": "yellow"},
    "FinishLine": {"color": "white"},

    # 📖 Narrative Adventure
    "PlayerNarrative": {"color": "orange"},
    "DialogTrigger": {"color": "purple"},
    "Item": {"color": "gold"},
    "CutsceneTrigger": {"color": "pink"},
    "ChoicePoint": {"color": "orange"},

    # 🛡 Tower Defense
    "PathEnemy": {"color": "red"},
    "Tower": {"color": "navy"},
    "Waypoint": {"color": "teal"},
    "Base": {"color": "darkGray"},
    "UpgradeItem": {"color": "lime"}
}
PREDEFINED_ITEMS = {
    "Helmet": {"hp_bonus": 20},
    "Chest": {"hp_bonus": 40},
    "Legs": {"speed_bonus": 1},
    "Boots": {"speed_bonus": 1},
    "Shield": {"block_bonus": 10},
    "Sword": {"damage_bonus": 15},
    "Bow": {"damage_bonus": 10},
    "Staff": {"damage_bonus": 12},
    "HP Potion": {"restore_hp": 50},
    "Boost": {"speed_bonus": 3}
}

GRID_SIZE = 32

class DialogManager(QObject):
    dialog_finished = pyqtSignal()

    def __init__(self, scene,entity_manager):
        super().__init__()
        self.scene = scene
        self.entity_manager = entity_manager 
        self.dialog_lines = []
        self.current_line_index = 0
        self.text_item = None
        self.text_bg = None  # Fundal pentru text, opțional

    def start_dialog(self, npc_item, text):
        # Split dialogul pe slide-uri (paragrafe separate prin linie goală)
        self.dialog_lines = [s.strip() for s in text.split('\n\n') if s.strip()]
        self.current_line_index = 0
        self.current_dialog = npc_item

        # Creează text_item dacă nu există
        if not self.text_item:
            self.text_item = QGraphicsTextItem()
            self.text_item.setDefaultTextColor(Qt.black)  # Contrast pe fundal deschis
            self.text_item.setFont(QFont("Arial", 12, QFont.Bold))
            self.text_item.setZValue(100)
            self.scene.addItem(self.text_item)
        # Creează fundal pentru text dacă nu există (opțional, pentru claritate)
        if not self.text_bg:
            from PyQt5.QtWidgets import QGraphicsRectItem
            from PyQt5.QtGui import QColor
            self.text_bg = QGraphicsRectItem()
            self.text_bg.setBrush(QColor(255, 255, 224, 200))  # Galben deschis, semitransparent
            from PyQt5.QtGui import QPen
            self.text_bg.setPen(QPen(Qt.NoPen))
            self.text_bg.setZValue(99)
            self.scene.addItem(self.text_bg)

        print("Dialog STARTED:", self.dialog_lines)  # DEBUG
        self.show_current_line()

    def show_current_line(self):
        if self.current_dialog and self.current_line_index < len(self.dialog_lines):
            text = self.dialog_lines[self.current_line_index]
            self.text_item.setPlainText(text)

            npc_rect = self.current_dialog.rect()
            text_width = self.text_item.boundingRect().width()
            text_height = self.text_item.boundingRect().height()
            # Folosește npc_rect.x/y pentru poziția reală!
            pos_x = npc_rect.x() + (npc_rect.width() - text_width) / 2
            pos_y = max(0, npc_rect.y() - text_height - 10)

            self.text_item.setDefaultTextColor(Qt.black)
            self.text_item.setZValue(100)
            self.text_item.setPos(pos_x, pos_y)
            self.text_item.show()

            if self.text_bg:
                self.text_bg.setRect(pos_x - 6, pos_y - 3, text_width + 12, text_height + 6)
                self.text_bg.setZValue(99)
                self.text_bg.show()

            print(f"Dialog SHOW: '{text}' at ({pos_x}, {pos_y})")
        else:
            self.end_dialog()


    def advance_dialog(self):
        if self.current_dialog:
            self.current_line_index += 1
            if self.current_line_index >= len(self.dialog_lines):
                self.end_dialog()
            else:
                self.show_current_line()

    def end_dialog(self):
        if self.text_item:
            self.text_item.hide()
        if self.text_bg:
            self.text_bg.hide()

        # Drop item dacă NPC-ul are inventar
        if self.current_dialog:
            data = self.current_dialog.data(0)
            if isinstance(data, dict) and data.get("type") == "NPC":
                inventory = data.get("inventory", [])
                if inventory:
                    from entities import GRID_SIZE

                    item_name = inventory.pop(0)  # luăm primul item

                    # Creează un obiect colectabil la poziția NPC-ului
                    npc_x = int(self.current_dialog.rect().x())
                    npc_y = int(self.current_dialog.rect().y())
                    drop_data = {
                        "type": "Collectible",
                        "name": item_name
                    }

                    # Dacă NPC-ul avea bonusuri salvate (custom_items), le păstrăm
                    if "custom_items" in data and item_name in data["custom_items"]:
                        drop_data["custom_items"] = {item_name: data["custom_items"][item_name]}
                    if "item_types" in data and item_name in data["item_types"]:
                        drop_data["item_types"] = {item_name: data["item_types"][item_name]}
                    if "image" in data.get("custom_items", {}).get(item_name, {}):
                        drop_data["image"] = data["custom_items"][item_name]["image"]

                    self.current_dialog.setData(0, data)  # actualizează fără item
                    self.entity_manager.create_entity(npc_x, npc_y + GRID_SIZE, drop_data)
                    print(f"🎁 NPC dropped item: {item_name}")

        self.current_dialog = None
        self.dialog_lines = []
        self.current_line_index = 0
        self.dialog_finished.emit()




class EntityManager:
    def __init__(self, scene, list_widget):
        self.scene = scene
        self.list_widget = list_widget
        self.entity_counters = {key: 0 for key in ENTITY_TYPES.keys()}
        self.player_item = None
        self.dialog_manager = DialogManager(scene, self)  # 🔧 Trimite self ca entity_manager


    def create_entity(self, x, y, attributes):
        entity_type = attributes.get("type", "Unknown")
        color = ENTITY_TYPES.get(entity_type, {}).get("color", "black")
        size = attributes.get("size", attributes.get("width", 1))
        w = h = size
        rect_item = QGraphicsRectItem(x, y, w * GRID_SIZE, h * GRID_SIZE)

        rect_item.setFlags(QGraphicsRectItem.ItemIsSelectable | QGraphicsRectItem.ItemIsFocusable)


        # Aplicați atribute implicite în funcție de tipul de entitate
        if entity_type == "Enemy":
            attributes.setdefault("hp", 10)
            attributes.setdefault("speed", 1)
            attributes.setdefault("damage", 1)
            attributes.setdefault("range", 1)
            attributes.setdefault("trigger_range", 3)
            attributes.setdefault("resistance", 0)
            attributes.setdefault("inventory", [])
        elif entity_type.startswith("Player"):
            attributes.setdefault("hp", 100)
            attributes.setdefault("speed", 1)
            attributes.setdefault("damage", 1)
            attributes.setdefault("range", 1)
            attributes.setdefault("resistance", 0)
            attributes.setdefault("inventory", [])
        elif entity_type in ["NPC", "Chest"]:
            attributes.setdefault("inventory", [])

        # Dacă este un item din cele predefinite, adaugă bonusurile
        if entity_type == "Item" and "name" in attributes:
            item_name = attributes["name"]
            bonuses = PREDEFINED_ITEMS.get(item_name)
            if bonuses:
                attributes.update(bonuses)
                # Aplica și damage/range dacă e relevant
                if "damage_bonus" in bonuses:
                    attributes["damage"] = bonuses["damage_bonus"]
                    if item_name in ["Bow", "Staff"]:
                        attributes["range"] = 5
                    else:
                        attributes["range"] = 1
                if "block_bonus" in bonuses:
                    attributes["resistance"] = bonuses["block_bonus"]
                if "speed_bonus" in bonuses:
                    attributes["speed"] = bonuses["speed_bonus"]
                if "restore_hp" in bonuses:
                    attributes["heal"] = bonuses["restore_hp"]
                if "hp_bonus" in bonuses:
                    attributes["hp_bonus"] = bonuses["hp_bonus"]

        # Creează entitatea grafică
        rect_item = QGraphicsRectItem(QRectF(x, y, GRID_SIZE * w, GRID_SIZE * h))
        rect_item.setBrush(QBrush(QColor(color)))
        rect_item.setData(0, attributes)
        rect_item.setFlag(QGraphicsRectItem.ItemIsSelectable, True)
        rect_item.setFlag(QGraphicsRectItem.ItemIsMovable, False)

        # Numire entitate
        self.entity_counters[entity_type] += 1
        entity_name = f"{entity_type}{self.entity_counters[entity_type]}"
        attributes["name"] = entity_name

        # Adăugare în scenă
        self.scene.addItem(rect_item)

        # Adăugare în listă UI
        list_text = f"{entity_type} {self.entity_counters[entity_type]}"
        item_entry = QListWidgetItem(list_text)
        item_entry.setData(Qt.UserRole, rect_item)
        self.list_widget.addItem(item_entry)

        # Adaugă HP bar dacă e necesar
        if entity_type.startswith("Player") or entity_type == "Enemy":
            hp_width = GRID_SIZE * w
            hp_height = 5
            bar_x = x
            bar_y = y - hp_height - 2
            hp_rect = QGraphicsRectItem(QRectF(bar_x, bar_y, hp_width, hp_height))
            hp_rect.setBrush(QBrush(QColor("red")))
            hp_rect.setZValue(1)
            rect_item.setData(1, hp_rect)
            self.scene.addItem(hp_rect)

        # Setăm playerul curent
        if entity_type.startswith("Player"):
            self.player_item = rect_item

        # Inițializare dialog NPC
        if entity_type == "NPC":
            attributes["dialog_text"] = ""
        return rect_item

    def find_valid_position(self, width, height, preferred=None):
        if preferred:
            px, py = preferred
            test_rect = QRectF(px, py, width * GRID_SIZE, height * GRID_SIZE)
            if self.is_area_free(test_rect):
                return (px, py)

            max_distance = max(int(self.scene.height() // GRID_SIZE), int(self.scene.width() // GRID_SIZE))
            for distance in range(1, max_distance):
                for dx in range(-distance, distance + 1):
                    for dy in [-distance, distance]:
                        x = px + dx * GRID_SIZE
                        y = py + dy * GRID_SIZE
                        if 0 <= x <= self.scene.width() - width * GRID_SIZE and \
                        0 <= y <= self.scene.height() - height * GRID_SIZE:
                            test_rect = QRectF(x, y, width * GRID_SIZE, height * GRID_SIZE)
                            if self.is_area_free(test_rect):
                                return (x, y)

                for dy in range(-distance + 1, distance):
                    for dx in [-distance, distance]:
                        x = px + dx * GRID_SIZE
                        y = py + dy * GRID_SIZE
                        if 0 <= x <= self.scene.width() - width * GRID_SIZE and \
                        0 <= y <= self.scene.height() - height * GRID_SIZE:
                            test_rect = QRectF(x, y, width * GRID_SIZE, height * GRID_SIZE)
                            if self.is_area_free(test_rect):
                                return (x, y)

        for row in range(int(self.scene.height() // GRID_SIZE) - height + 1):
            for col in range(int(self.scene.width() // GRID_SIZE) - width + 1):
                x = col * GRID_SIZE
                y = row * GRID_SIZE
                candidate_rect = QRectF(x, y, width * GRID_SIZE, height * GRID_SIZE)
                if self.is_area_free(candidate_rect):
                    return (x, y)

        return None


    def is_area_free(self, rect_to_check):
        for item in self.scene.items():
            if isinstance(item, QGraphicsRectItem):
                if item.rect().intersects(rect_to_check):
                    data = item.data(0)
                    if data and data.get("type") not in ["SpawnPoint", "Collectible"]:
                        return False
        return True

    def get_player_item(self):
        return self.player_item

    def handle_interaction(self, player, key_event):
        if key_event.key() == Qt.Key_E:
            # Caută NPC apropiat pentru dialog
            player_pos = player.pos()
            for item in self.scene.items():
                if isinstance(item, QGraphicsRectItem):
                    data = item.data(0)
                    if data and data.get("type") == "NPC":
                        npc_pos = item.pos()
                        distance = ((player_pos.x() - npc_pos.x()) ** 2 +
                                    (player_pos.y() - npc_pos.y()) ** 2) ** 0.5
                        if distance < GRID_SIZE * 2:  # rază de dialog ~două pătrățele
                            self.show_npc_dialog(item)
                            return True
        elif key_event.key() == Qt.Key_Return:
            if self.dialog_manager.current_dialog:
                self.dialog_manager.advance_dialog()
                return True
        return False

    def show_npc_dialog(self, npc_item):
        data = npc_item.data(0)
        if data.get("dialog_text"):
            self.dialog_manager.start_dialog(npc_item, data["dialog_text"])

    def edit_npc_dialog(self, npc_item):
        data = npc_item.data(0)
        if data and data.get("type") == "NPC":
            text, ok = QInputDialog.getMultiLineText(
                None,
                "Edit NPC Dialog",
                "Enter dialog text (separate slides with new lines):",
                data.get("dialog_text", "")
            )
            if ok:
                data["dialog_text"] = text