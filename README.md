# 🎮 No-Code 2D Game Editor

This project is a simple visual tool for creating 2D games without writing code. It is built in Python using PyQt5 and was designed as a learning project to understand how game editors, scene systems, and basic game engines work.

The idea is to let users build small 2D games by placing objects on a grid, configuring them through a UI, and then running the game directly from the editor.

---

## 🚀 What the Project Does

This application lets you:
- Create 2D scenes visually (like a simple level editor)
- Drag and drop different types of game objects
- Configure entities (player, enemies, NPCs, items, etc.)
- Add simple behaviors and animations
- Save and load scenes using JSON
- Run the created scene as a playable game

---

## 🧱 Main Features

### 🧩 Scene Editor
- Grid-based editing system
- Place and move objects on a map
- Zoom in/out for better editing
- Enable/disable grid view
- Mark blocked or non-walkable tiles

---

### 🎮 Game Objects (Entities)
The editor supports different types of objects:
- Player character
- Enemy characters with simple AI
- NPCs with dialogues
- Items and collectibles
- Doors and triggers
- Static objects (walls, decorations)

Each object has editable properties (position, stats, behavior, etc.).

---

### 🎭 Animations
The project includes a basic animation system:
- Sprite sheet support
- Idle and movement animations
- Attack and death animations
- Automatic frame switching using a timer
- Scaling sprites to fit objects

---

### 🤖 Simple AI System
Enemies can:
- Stay idle
- Patrol around the map
- Follow the player when detected
- React to triggers and collisions

---

### 🎒 Inventory System
Players and objects can interact with items:
- Collect items on the map
- Equip weapons or armor
- Receive stat bonuses like:
  - Health
  - Damage
  - Speed
  - Range

---

### 💬 Dialogue System
NPCs can:
- Display multi-line dialogue
- Interact with the player
- Drop items after conversations

---

### 🗺 Scene Saving & Loading
Scenes are saved in JSON format. This includes:
- Object positions
- Grid settings
- Tile data
- Entity properties
- AI and behavior data

Saved scenes can be loaded back and fully reconstructed.

---

### 🎯 Game Runner
The project also includes a simple game launcher:
- Loads the first scene automatically
- Starts a playable version of the created level
- Runs everything inside a PyQt window

---

## 🏗 Project Structure
main.py -> starts the editor
editor.py -> main level editor UI
entities.py -> game objects + AI + dialogue
animations.py -> animation system
scenes.py -> save/load system
game_launcher.py -> runs the playable game

---

## 🧠 How It Works (Simple Explanation)

1. You create a scene by placing objects on a grid
2. Each object stores its own data (position, stats, type)
3. The editor draws everything using PyQt graphics
4. Animations are handled using a timer that changes frames
5. When saving, everything is converted into JSON
6. When loading, the scene is rebuilt from that JSON file
7. The game launcher reads the scene and runs it as a game

---

## 🧪 Technologies Used

- Python 3
- PyQt5 (for the interface and rendering)
- JSON (for saving scenes)
- QGraphicsScene (for 2D rendering)

---

## 🎮 Game Types You Can Build

This editor can be used for simple:
- RPG games
- Shooter games
- Puzzle games
- Tower defense games
- Story-based / narrative games

Each type uses the same base system but different object setups.

---

## 📦 How to Run the Project

```bash
git clone https://github.com/your-username/no-code-game-editor.git
cd no-code-game-editor
pip install PyQt5
python main.pypython game_launcher.py
```
💾 Scene Format

A saved scene contains:

Grid size and settings
All placed objects
Object properties (HP, speed, etc.)
Sprite paths
AI and behavior settings

Everything is stored in a structured JSON file.

🔮 Future Improvements

Some ideas for future versions:

Better pathfinding (A* algorithm)
Visual scripting system
Multiplayer support
More advanced tile editor
Sound system
Export as standalone .exe
