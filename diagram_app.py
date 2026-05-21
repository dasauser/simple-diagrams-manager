import sys
import json
import math
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Optional, List, Tuple
from enum import Enum

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QMessageBox, QLabel, QLineEdit, QDialog,
    QDialogButtonBox, QSpinBox, QListWidget, QListWidgetItem
)
from PyQt6.QtCore import Qt, QPoint, QRect, QTimer, pyqtSignal, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QImage, QBrush,
    QMouseEvent, QKeyEvent, QCursor, QPolygonF
)


class ElementType(Enum):
    BLOCK = "block"
    TABLE = "table"
    CONNECTOR = "connector"


@dataclass
class Point:
    x: float
    y: float

    def distance_to(self, other: 'Point') -> float:
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def to_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)


@dataclass
class Block:
    id: str
    x: float
    y: float
    width: float
    height: float
    title: str
    selected: bool = False

    def contains(self, point: Point) -> bool:
        return (self.x <= point.x <= self.x + self.width and
                self.y <= point.y <= self.y + self.height)

    def get_center(self) -> Point:
        return Point(self.x + self.width / 2, self.y + self.height / 2)

    def get_connection_point(self, target: 'Block') -> Point:
        """Get the point on this block's edge closest to target"""
        cx, cy = self.get_center().to_tuple()
        tx, ty = target.get_center().to_tuple()

        # Determine which edge to use
        dx = tx - cx
        dy = ty - cy

        if abs(dx) > abs(dy):  # Use left or right edge
            x = self.x if dx < 0 else self.x + self.width
            y = cy
        else:  # Use top or bottom edge
            x = cx
            y = self.y if dy < 0 else self.y + self.height

        # Clamp to block bounds
        x = max(self.x, min(x, self.x + self.width))
        y = max(self.y, min(y, self.y + self.height))

        return Point(x, y)


@dataclass
class Table(Block):
    fields: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.update_height()

    def update_height(self):
        """Recalculate height based on number of fields"""
        self.height = max(60, 40 + len(self.fields) * 25)

    def add_field(self, name: str):
        self.fields.append(name)
        self.update_height()

    def remove_field(self, index: int):
        if 0 <= index < len(self.fields):
            self.fields.pop(index)
            self.update_height()


@dataclass
class Connector:
    id: str
    from_id: str
    to_id: str
    selected: bool = False


class EditBlockDialog(QDialog):
    def __init__(self, block: Block, parent=None):
        super().__init__(parent)
        self.block = block
        self.setWindowTitle("Edit Block")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Title:"))
        self.title_input = QLineEdit(self.block.title)
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(50, 500)
        self.width_spin.setValue(int(self.block.width))
        layout.addWidget(self.width_spin)

        layout.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(50, 500)
        self.height_spin.setValue(int(self.block.height))
        layout.addWidget(self.height_spin)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def get_values(self):
        return {
            'title': self.title_input.text(),
            'width': self.width_spin.value(),
            'height': self.height_spin.value()
        }


class EditTableDialog(QDialog):
    def __init__(self, table: Table, parent=None):
        super().__init__(parent)
        self.table = table
        self.setWindowTitle("Edit Table")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Table Name:"))
        self.title_input = QLineEdit(self.table.title)
        layout.addWidget(self.title_input)

        layout.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(100, 500)
        self.width_spin.setValue(int(self.table.width))
        layout.addWidget(self.width_spin)

        layout.addWidget(QLabel("Fields:"))
        self.fields_list = QListWidget()
        for field in self.table.fields:
            self.fields_list.addItem(field)
        layout.addWidget(self.fields_list)

        fields_layout = QHBoxLayout()
        self.field_input = QLineEdit()
        self.field_input.setPlaceholderText("Field name")
        add_btn = QPushButton("Add Field")
        add_btn.clicked.connect(self.add_field)
        remove_btn = QPushButton("Remove Field")
        remove_btn.clicked.connect(self.remove_field)

        fields_layout.addWidget(self.field_input)
        fields_layout.addWidget(add_btn)
        fields_layout.addWidget(remove_btn)
        layout.addLayout(fields_layout)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def add_field(self):
        text = self.field_input.text().strip()
        if text:
            self.fields_list.addItem(text)
            self.field_input.clear()

    def remove_field(self):
        row = self.fields_list.currentRow()
        if row >= 0:
            self.fields_list.takeItem(row)

    def get_values(self):
        fields = [self.fields_list.item(i).text() for i in range(self.fields_list.count())]
        return {
            'title': self.title_input.text(),
            'width': self.width_spin.value(),
            'fields': fields
        }


class DiagramCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.blocks: List[Block] = []
        self.tables: List[Table] = []
        self.connectors: List[Connector] = []

        self.selected_element: Optional[Block | Connector] = None
        self.dragging = False
        self.drag_offset = Point(0, 0)
        self.creating_connector = False
        self.connector_start: Optional[str] = None

        self.element_counter = 0
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def get_all_blocks(self) -> List[Block]:
        return self.blocks + self.tables

    def add_block(self):
        block_id = f"block_{self.element_counter}"
        self.element_counter += 1
        block = Block(block_id, 100, 100, 120, 60, "New Block")
        self.blocks.append(block)
        self.update()

    def add_table(self):
        table_id = f"table_{self.element_counter}"
        self.element_counter += 1
        table = Table(table_id, 100, 100, 150, 60, "New Table")
        table.add_field("field1")
        self.tables.append(table)
        self.update()

    def add_connector(self):
        if self.selected_element and isinstance(self.selected_element, Block):
            self.creating_connector = True
            self.connector_start = self.selected_element.id

    def delete_selected(self):
        if isinstance(self.selected_element, Block):
            if self.selected_element in self.blocks:
                self.blocks.remove(self.selected_element)
            elif self.selected_element in self.tables:
                self.tables.remove(self.selected_element)
            # Remove associated connectors
            self.connectors = [
                c for c in self.connectors
                if c.from_id != self.selected_element.id and c.to_id != self.selected_element.id
            ]
        elif isinstance(self.selected_element, Connector):
            self.connectors.remove(self.selected_element)

        self.selected_element = None
        self.update()

    def edit_selected(self):
        if not isinstance(self.selected_element, Block):
            return

        if isinstance(self.selected_element, Table):
            dialog = EditTableDialog(self.selected_element, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                values = dialog.get_values()
                self.selected_element.title = values['title']
                self.selected_element.width = values['width']
                self.selected_element.fields = values['fields']
                self.selected_element.update_height()
        else:
            dialog = EditBlockDialog(self.selected_element, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                values = dialog.get_values()
                self.selected_element.title = values['title']
                self.selected_element.width = values['width']
                self.selected_element.height = values['height']

        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        pos = Point(event.position().x(), event.position().y())

        if self.creating_connector:
            # Try to connect to a block
            for block in self.get_all_blocks():
                if block.contains(pos) and block.id != self.connector_start:
                    connector_id = f"connector_{self.element_counter}"
                    self.element_counter += 1
                    self.connectors.append(Connector(connector_id, self.connector_start, block.id))
                    self.creating_connector = False
                    self.connector_start = None
                    self.update()
                    return

            self.creating_connector = False
            self.connector_start = None
            return

        # Deselect all
        for block in self.get_all_blocks():
            block.selected = False
        for connector in self.connectors:
            connector.selected = False

        # Check if clicking on a block
        for block in self.get_all_blocks():
            if block.contains(pos):
                block.selected = True
                self.selected_element = block
                self.dragging = True
                self.drag_offset = Point(pos.x - block.x, pos.y - block.y)
                self.update()
                return

        # Check if clicking on a connector
        for connector in self.connectors:
            if self.is_near_connector(pos, connector):
                connector.selected = True
                self.selected_element = connector
                self.update()
                return

        self.selected_element = None
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = Point(event.position().x(), event.position().y())

        if self.dragging and isinstance(self.selected_element, Block):
            self.selected_element.x = pos.x - self.drag_offset.x
            self.selected_element.y = pos.y - self.drag_offset.y
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.edit_selected()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected()
        elif event.key() == Qt.Key.Key_E and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.edit_selected()

    def is_near_connector(self, pos: Point, connector: Connector, threshold: float = 10) -> bool:
        from_block = next((b for b in self.get_all_blocks() if b.id == connector.from_id), None)
        to_block = next((b for b in self.get_all_blocks() if b.id == connector.to_id), None)

        if not from_block or not to_block:
            return False

        p1 = from_block.get_connection_point(to_block)
        p2 = to_block.get_connection_point(from_block)

        # Distance from point to line
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        length = math.sqrt(dx * dx + dy * dy)

        if length < 0.1:
            return False

        t = max(0, min(1, ((pos.x - p1.x) * dx + (pos.y - p1.y) * dy) / (length * length)))
        closest_x = p1.x + t * dx
        closest_y = p1.y + t * dy

        distance = math.sqrt((pos.x - closest_x) ** 2 + (pos.y - closest_y) ** 2)
        return distance < threshold

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        painter.fillRect(self.rect(), QColor(240, 240, 240))

        # Draw connectors
        for connector in self.connectors:
            self.draw_connector(painter, connector)

        # Draw blocks
        for block in self.blocks:
            self.draw_block(painter, block)

        # Draw tables
        for table in self.tables:
            self.draw_table(painter, table)

        # Draw connector preview
        if self.creating_connector and self.connector_start:
            start_block = next((b for b in self.get_all_blocks() if b.id == self.connector_start), None)
            if start_block:
                cursor_pos = self.mapFromGlobal(QCursor.pos())
                painter.setPen(QPen(QColor(100, 100, 100), 2, Qt.PenStyle.DashLine))
                painter.drawLine(int(start_block.get_center().x), int(start_block.get_center().y),
                               cursor_pos.x(), cursor_pos.y())

    def draw_block(self, painter: QPainter, block: Block):
        color = QColor(100, 150, 255) if block.selected else QColor(200, 220, 255)
        painter.fillRect(int(block.x), int(block.y), int(block.width), int(block.height), color)

        border_color = QColor(0, 0, 0) if block.selected else QColor(100, 100, 100)
        border_width = 2 if block.selected else 1
        painter.setPen(QPen(border_color, border_width))
        painter.drawRect(int(block.x), int(block.y), int(block.width), int(block.height))

        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(
            int(block.x), int(block.y), int(block.width), int(block.height),
            Qt.AlignmentFlag.AlignCenter, block.title
        )

    def draw_table(self, painter: QPainter, table: Table):
        color = QColor(150, 200, 100) if table.selected else QColor(200, 240, 150)
        painter.fillRect(int(table.x), int(table.y), int(table.width), int(table.height), color)

        border_color = QColor(0, 0, 0) if table.selected else QColor(100, 100, 100)
        border_width = 2 if table.selected else 1
        painter.setPen(QPen(border_color, border_width))
        painter.drawRect(int(table.x), int(table.y), int(table.width), int(table.height))

        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.setPen(QPen(QColor(0, 0, 0)))

        # Draw title
        title_height = 25
        painter.drawText(
            int(table.x), int(table.y), int(table.width), title_height,
            Qt.AlignmentFlag.AlignCenter, table.title
        )

        # Draw separator
        painter.drawLine(int(table.x), int(table.y + title_height),
                        int(table.x + table.width), int(table.y + title_height))

        # Draw fields
        painter.setFont(QFont("Arial", 8))
        for i, field in enumerate(table.fields):
            y = table.y + title_height + i * 25
            painter.drawText(
                int(table.x + 5), int(y), int(table.width - 10), 25,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, field
            )

    def draw_connector(self, painter: QPainter, connector: Connector):
        from_block = next((b for b in self.get_all_blocks() if b.id == connector.from_id), None)
        to_block = next((b for b in self.get_all_blocks() if b.id == connector.to_id), None)

        if not from_block or not to_block:
            return

        p1 = from_block.get_connection_point(to_block)
        p2 = to_block.get_connection_point(from_block)

        color = QColor(200, 0, 0) if connector.selected else QColor(100, 100, 100)
        pen_width = 2 if connector.selected else 1
        painter.setPen(QPen(color, pen_width))

        painter.drawLine(int(p1.x), int(p1.y), int(p2.x), int(p2.y))

        # Draw arrowhead
        angle = math.atan2(p2.y - p1.y, p2.x - p1.x)
        arrow_size = 10

        p_left = Point(
            p2.x - arrow_size * math.cos(angle - math.pi / 6),
            p2.y - arrow_size * math.sin(angle - math.pi / 6)
        )
        p_right = Point(
            p2.x - arrow_size * math.cos(angle + math.pi / 6),
            p2.y - arrow_size * math.sin(angle + math.pi / 6)
        )

        painter.setBrush(QBrush(color))
        arrow = QPolygonF([
            QPointF(p2.x, p2.y),
            QPointF(p_left.x, p_left.y),
            QPointF(p_right.x, p_right.y)
        ])
        painter.drawPolygon(arrow)

    def save_as_image(self, filepath: str):
        """Save diagram as PNG image"""
        # Calculate bounding box
        all_elements = self.get_all_blocks() + self.connectors
        if not all_elements:
            return

        min_x = min([b.x for b in self.get_all_blocks()], default=0)
        min_y = min([b.y for b in self.get_all_blocks()], default=0)
        max_x = max([b.x + b.width for b in self.get_all_blocks()], default=800)
        max_y = max([b.y + b.height for b in self.get_all_blocks()], default=600)

        width = int(max_x - min_x + 40)
        height = int(max_y - min_y + 40)

        # Create image
        image = QImage(width, height, QImage.Format.Format_RGB32)
        image.fill(QColor(240, 240, 240))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(-int(min_x) + 20, -int(min_y) + 20)

        # Draw all elements
        for connector in self.connectors:
            self.draw_connector(painter, connector)

        for block in self.blocks:
            self.draw_block(painter, block)

        for table in self.tables:
            self.draw_table(painter, table)

        painter.end()
        image.save(filepath, "PNG")

    def get_data(self) -> dict:
        """Export diagram data"""
        return {
            'blocks': [asdict(b) for b in self.blocks],
            'tables': [asdict(t) for t in self.tables],
            'connectors': [asdict(c) for c in self.connectors]
        }

    def load_data(self, data: dict):
        """Import diagram data"""
        self.blocks = [Block(**b) for b in data.get('blocks', [])]
        self.tables = [Table(**t) for t in data.get('tables', [])]
        self.connectors = [Connector(**c) for c in data.get('connectors', [])]
        self.update()


class DiagramApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diagram Creator")
        self.setGeometry(100, 100, 1000, 700)

        self.canvas = DiagramCanvas()

        # Main layout
        main_widget = QWidget()
        layout = QVBoxLayout()

        # Top toolbar
        toolbar_layout = QHBoxLayout()
        
        create_btn = QPushButton("Create Diagram")
        create_btn.clicked.connect(self.new_diagram)
        
        block_btn = QPushButton("Add Block")
        block_btn.clicked.connect(self.canvas.add_block)
        
        table_btn = QPushButton("Add Table")
        table_btn.clicked.connect(self.canvas.add_table)
        
        connector_btn = QPushButton("Add Connector")
        connector_btn.clicked.connect(self.canvas.add_connector)
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.canvas.delete_selected)
        
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.canvas.edit_selected)

        toolbar_layout.addWidget(create_btn)
        toolbar_layout.addWidget(block_btn)
        toolbar_layout.addWidget(table_btn)
        toolbar_layout.addWidget(connector_btn)
        toolbar_layout.addWidget(edit_btn)
        toolbar_layout.addWidget(delete_btn)
        toolbar_layout.addStretch()

        save_btn = QPushButton("Save Diagram")
        save_btn.clicked.connect(self.save_diagram)
        toolbar_layout.addWidget(save_btn)

        layout.addLayout(toolbar_layout)
        layout.addWidget(self.canvas)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    def new_diagram(self):
        self.canvas.blocks.clear()
        self.canvas.tables.clear()
        self.canvas.connectors.clear()
        self.canvas.selected_element = None
        self.canvas.element_counter = 0
        self.canvas.update()

    def save_diagram(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save Diagram", "", "PNG Image (*.png)"
        )
        if filepath:
            try:
                self.canvas.save_as_image(filepath)
                QMessageBox.information(self, "Success", f"Diagram saved to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiagramApp()
    window.show()
    sys.exit(app.exec())