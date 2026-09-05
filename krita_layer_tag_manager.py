import krita
import json
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLineEdit, QComboBox, QTreeWidget,
                             QTreeWidgetItem, QMessageBox, QDockWidget)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QColor

class TagManager(QObject):
    def __init__(self):
        super().__init__()
        self.tags = {}
        self.load_presets()

    def _get_preset_path(self):
        # Use Krita's config directory if available, fallback to home
        try:
            config_dir = krita.configDir()
            if config_dir:
                return os.path.join(config_dir, "layer_tags.json")
        except Exception:
            pass
        return os.path.join(os.path.expanduser("~"), ".krita", "layer_tags.json")

    def load_presets(self):
        preset_path = self._get_preset_path()
        if os.path.exists(preset_path):
            try:
                with open(preset_path, 'r') as f:
                    self.tags = json.load(f)
            except Exception:
                self.tags = {}

    def save_presets(self):
        preset_path = self._get_preset_path()
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(preset_path), exist_ok=True)
            with open(preset_path, 'w') as f:
                json.dump(self.tags, f, indent=2)
        except Exception as e:
            print(f"Error saving presets: {e}")

    def add_tag(self, name, color_hex):
        self.tags[name] = color_hex
        self.save_presets()

    def remove_tag(self, name):
        if name in self.tags:
            del self.tags[name]
            self.save_presets()

    def get_tag_color(self, name):
        return self.tags.get(name, "#FFFFFF")

class LayerTagWidget(QWidget):
    def __init__(self, tag_manager):
        super().__init__()
        self.tag_manager = tag_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Search & Filter
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search layers...")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Visible", "Hidden", "Locked", "Unlocked"])
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.filter_combo)
        layout.addLayout(search_layout)

        # Layer Tree
        self.layer_tree = QTreeWidget()
        self.layer_tree.setHeaderLabels(["Layer", "Tags"])
        layout.addWidget(self.layer_tree)

        # Tag Management
        tag_layout = QHBoxLayout()
        self.tag_input = QLineEdit()
        self.tag_input.setPlaceholderText("New tag name")
        self.add_tag_btn = QPushButton("Add Tag")
        self.add_tag_btn.clicked.connect(self.add_tag)
        tag_layout.addWidget(self.tag_input)
        tag_layout.addWidget(self.add_tag_btn)
        layout.addLayout(tag_layout)

        # Batch Operations
        batch_layout = QHBoxLayout()
        self.batch_action = QComboBox()
        self.batch_action.addItems(["Show", "Hide", "Lock", "Unlock", "Group"])
        self.batch_btn = QPushButton("Apply to Selected")
        self.batch_btn.clicked.connect(self.apply_batch)
        batch_layout.addWidget(self.batch_action)
        batch_layout.addWidget(self.batch_btn)
        layout.addLayout(batch_layout)

        self.setLayout(layout)

    def add_tag(self):
        name = self.tag_input.text().strip()
        if name:
            self.tag_manager.add_tag(name, "#00FF00")
            self.tag_input.clear()
            self.refresh_tree()

    def apply_batch(self):
        doc = krita.instance().activeDocument()
        if not doc:
            return

        selected_items = self.layer_tree.selectedItems()
        if not selected_items:
            return

        action = self.batch_action.currentText()
        doc.beginTransaction("Batch Layer Operation")
        
        for item in selected_items:
            node = item.data(0, Qt.UserRole)
            if not node:
                continue
            
            if action == "Show":
                node.visible = True
            elif action == "Hide":
                node.visible = False
            elif action == "Lock":
                node.locked = True
            elif action == "Unlock":
                node.locked = False
            elif action == "Group":
                # Simplified grouping logic
                pass

        doc.endTransaction()
        self.refresh_tree()

    def refresh_tree(self):
        doc = krita.instance().activeDocument()
        if not doc:
            return

        self.layer_tree.clear()
        self.populate_tree(doc.rootNode(), self.layer_tree.invisibleRootItem())

    def populate_tree(self, node, parent_item):
        if not node:
            return

        item = QTreeWidgetItem(parent_item)
        item.setText(0, node.name)
        item.setData(0, Qt.UserRole, node)
        
        # Get tags from custom properties
        tags = []
        try:
            tag_str = node.getCustomProperty("tags")
            if tag_str:
                tags = json.loads(tag_str)
        except Exception:
            pass
        item.setText(1, ", ".join(tags))

        for child in node.children():
            self.populate_tree(child, item)

class LayerTagPlugin:
    def __init__(self, parent):
        self.parent = parent
        self.tag_manager = TagManager()
        self.dock = QDockWidget("Layer Tag Manager", parent)
        self.widget = LayerTagWidget(self.tag_manager)
        self.dock.setWidget(self.widget)
        parent.addDockWidget(Qt.RightDockWidgetArea, self.dock)
        
        # Connect document change signal
        krita.instance().documentChanged.connect(self.on_document_changed)

    def on_document_changed(self, doc):
        if doc:
            self.widget.refresh_tree()

def create_instance(parent):
    return LayerTagPlugin(parent)
