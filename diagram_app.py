import sys
import math
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QMessageBox, QLabel, QLineEdit, QDialog,
    QDialogButtonBox, QSpinBox, QListWidget
)
from PyQt6.QtCore import Qt, QPoint, QRect, QPointF
from PyQt6.QtGui import (
    QPainter, QPen, QColor, QFont, QImage, QBrush,
    QMouseEvent, QKeyEvent, QCursor, QPolygonF
)


@dataclass
class Point:
    x: float
    y: float

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
    
    HANDLE_SIZE = 8

    def contains(self, point: Point) -> bool:
        return (self.x <= point.x <= self.x + self.width and
                self.y <= point.y <= self.y + self.height)

    def get_center(self) -> Point:
        return Point(self.x + self.width / 2, self.y + self.height / 2)

    def get_connection_point(self, target: 'Block') -> Point:
        cx, cy = self.get_center().to_tuple()
        tx, ty = target.get_center().to_tuple()

        dx = tx - cx
        dy = ty - cy

        if abs(dx) > abs(dy):
            x = self.x if dx < 0 else self.x + self.width
            y = cy
        else:
            x = cx
            y = self.y if dy < 0 else self.y + self.height

        x = max(self.x, min(x, self.x + self.width))
        y = max(self.y, min(y, self.y + self.height))

        return Point(x, y)
    
    def get_resize_handle_at(self, point: Point) -> Optional[str]:
        """Check if point is on a resize handle. Returns handle position or None."""
        h = self.HANDLE_SIZE
        handles = {
            'top_left': (self.x - h/2, self.y - h/2),
            'top': (self.x + self.width/2 - h/2, self.y - h/2),
            'top_right': (self.x + self.width - h/2, self.y - h/2),
            'left': (self.x - h/2, self.y + self.height/2 - h/2),
            'right': (self.x + self.width - h/2, self.y + self.height/2 - h/2),
            'bottom_left': (self.x - h/2, self.y + self.height - h/2),
            'bottom': (self.x + self.width/2 - h/2, self.y + self.height - h/2),
            'bottom_right': (self.x + self.width - h/2, self.y + self.height - h/2),
        }
        
        for handle_name, (hx, hy) in handles.items():
            if (hx <= point.x <= hx + h and hy <= point.y <= hy + h):
                return handle_name
        return None


@dataclass
class Table(Block):
    fields: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.update_height()

    def update_height(self):
        self.height = max(60, 40 + len(self.fields) * 25)

    def add_field(self, name: str):
        self.fields.append(name)
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
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
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
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
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
        if self.fields_list.currentRow() >= 0:
            self.fields_list.takeItem(self.fields_list.currentRow())

    def get_values(self):
        fields = [self.fields_list.item(i).text() for i in range(self.fields_list.count())]
        return {'title': self.title_input.text(), 'width': self.width_spin.value(), 'fields': fields}


class DiagramCanvas(QWidget):
    def __init__(self):
        super().__init__()
        self.blocks: List[Block] = []
        self.tables: List[Table] = []
        self.connectors: List[Connector] = []
        
        self.selected_id: Optional[str] = None
        self.dragging = False
        self.drag_offset = Point(0, 0)
        self.resizing_handle: Optional[str] = None
        self.creating_connector = False
        self.connector_start: Optional[str] = None
        self.connector_button_rect = None
        self.element_counter = 0
        
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def get_all_blocks(self) -> List[Block]:
        return self.blocks + self.tables

    def get_block_by_id(self, block_id: str) -> Optional[Block]:
        for block in self.get_all_blocks():
            if block.id == block_id:
                return block
        return None

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

    def delete_selected(self):
        if not self.selected_id:
            return
        
        block = self.get_block_by_id(self.selected_id)
        if block:
            if block in self.blocks:
                self.blocks.remove(block)
            elif block in self.tables:
                self.tables.remove(block)
            self.connectors = [c for c in self.connectors 
                             if c.from_id != self.selected_id and c.to_id != self.selected_id]
        else:
            connector = next((c for c in self.connectors if c.id == self.selected_id), None)
            if connector:
                self.connectors.remove(connector)
        
        self.selected_id = None
        self.update()

    def edit_selected(self):
        if not self.selected_id:
            return
        
        block = self.get_block_by_id(self.selected_id)
        if not block:
            return

        if isinstance(block, Table):
            dialog = EditTableDialog(block, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                values = dialog.get_values()
                block.title = values['title']
                block.width = values['width']
                block.fields = values['fields']
                block.update_height()
        else:
            dialog = EditBlockDialog(block, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                values = dialog.get_values()
                block.title = values['title']
                block.width = values['width']
                block.height = values['height']

        self.update()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() != Qt.MouseButton.LeftButton:
            return

        pos = Point(event.position().x(), event.position().y())

        if self.creating_connector:
            for block in self.get_all_blocks():
                if block.contains(pos) and block.id != self.connector_start:
                    # Check if connection already exists
                    existing = next((c for c in self.connectors 
                                   if c.from_id == self.connector_start and c.to_id == block.id), None)
                    
                    if existing:
                        # Remove old connection and create new one
                        self.connectors.remove(existing)
                    
                    connector_id = f"connector_{self.element_counter}"
                    self.element_counter += 1
                    self.connectors.append(Connector(connector_id, self.connector_start, block.id))
                    self.creating_connector = False
                    self.connector_start = None
                    self.selected_id = None
                    self.update()
                    return
            
            self.creating_connector = False
            self.connector_start = None
            self.selected_id = None
            self.update()
            return

        if (self.connector_button_rect and 
            self.connector_button_rect.contains(int(pos.x), int(pos.y)) and
            self.selected_id):
            self.creating_connector = True
            self.connector_start = self.selected_id
            self.update()
            return

        # Check for resize handle
        selected_block = self.get_block_by_id(self.selected_id) if self.selected_id else None
        if selected_block:
            handle = selected_block.get_resize_handle_at(pos)
            if handle:
                self.resizing_handle = handle
                self.update()
                return

        for block in self.get_all_blocks():
            block.selected = False

        self.selected_id = None
        self.resizing_handle = None

        for block in self.get_all_blocks():
            if block.contains(pos):
                block.selected = True
                self.selected_id = block.id
                self.dragging = True
                self.drag_offset = Point(pos.x - block.x, pos.y - block.y)
                self.update()
                return

        for connector in self.connectors:
            if self.is_near_connector(pos, connector):
                connector.selected = True
                self.selected_id = connector.id
                self.update()
                return

        self.update()

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = Point(event.position().x(), event.position().y())
        
        if self.resizing_handle and self.selected_id:
            block = self.get_block_by_id(self.selected_id)
            if block:
                min_size = 50
                h = self.resizing_handle
                
                if 'left' in h:
                    block.width = max(min_size, block.width + (block.x - pos.x))
                    block.x = pos.x
                if 'right' in h:
                    block.width = max(min_size, pos.x - block.x)
                if 'top' in h:
                    block.height = max(min_size, block.height + (block.y - pos.y))
                    block.y = pos.y
                if 'bottom' in h:
                    block.height = max(min_size, pos.y - block.y)
                
                if isinstance(block, Table):
                    block.update_height()
                
                self.update()
            return
        
        if self.dragging and self.selected_id:
            block = self.get_block_by_id(self.selected_id)
            if block:
                block.x = pos.x - self.drag_offset.x
                block.y = pos.y - self.drag_offset.y
                self.update()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            self.resizing_handle = None

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        self.edit_selected()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Delete:
            self.delete_selected()
        elif event.key() == Qt.Key.Key_E and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.edit_selected()

    def is_near_connector(self, pos: Point, connector: Connector, threshold: float = 10) -> bool:
        from_block = self.get_block_by_id(connector.from_id)
        to_block = self.get_block_by_id(connector.to_id)

        if not from_block or not to_block:
            return False

        p1 = from_block.get_connection_point(to_block)
        p2 = to_block.get_connection_point(from_block)

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
        painter.fillRect(self.rect(), QColor(240, 240, 240))

        for connector in self.connectors:
            self.draw_connector(painter, connector)

        for block in self.blocks:
            self.draw_block(painter, block)

        for table in self.tables:
            self.draw_table(painter, table)

        if self.creating_connector and self.connector_start:
            start_block = self.get_block_by_id(self.connector_start)
            if start_block:
                cursor_pos = self.mapFromGlobal(QCursor.pos())
                painter.setPen(QPen(QColor(100, 100, 100), 2, Qt.PenStyle.DashLine))
                painter.drawLine(int(start_block.get_center().x), int(start_block.get_center().y),
                               cursor_pos.x(), cursor_pos.y())

    def draw_block(self, painter: QPainter, block: Block):
        if self.creating_connector:
            color = QColor(180, 180, 180)
            border_color = QColor(100, 100, 100)
        else:
            color = QColor(100, 150, 255) if block.selected else QColor(200, 220, 255)
            border_color = QColor(0, 0, 0) if block.selected else QColor(100, 100, 100)
        
        painter.fillRect(int(block.x), int(block.y), int(block.width), int(block.height), color)
        
        border_width = 1 if self.creating_connector else (2 if block.selected else 1)
        painter.setPen(QPen(border_color, border_width))
        painter.drawRect(int(block.x), int(block.y), int(block.width), int(block.height))

        painter.setPen(QPen(QColor(0, 0, 0)))
        painter.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        painter.drawText(int(block.x), int(block.y), int(block.width), int(block.height),
                        Qt.AlignmentFlag.AlignCenter, block.title)

        # Draw resize handles if selected
        if block.selected and not self.creating_connector:
            self.draw_resize_handles(painter, block)
            self.draw_connector_button(painter, block)

    def draw_resize_handles(self, painter: QPainter, block: Block):
        """Draw resize handles on block corners and edges"""
        h = int(Block.HANDLE_SIZE)
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        
        handles = [
            (block.x - h/2, block.y - h/2),  # top_left
            (block.x + block.width/2 - h/2, block.y - h/2),  # top
            (block.x + block.width - h/2, block.y - h/2),  # top_right
            (block.x - h/2, block.y + block.height/2 - h/2),  # left
            (block.x + block.width - h/2, block.y + block.height/2 - h/2),  # right
            (block.x - h/2, block.y + block.height - h/2),  # bottom_left
            (block.x + block.width/2 - h/2, block.y + block.height - h/2),  # bottom
            (block.x + block.width - h/2, block.y + block.height - h/2),  # bottom_right
        ]
        
        for hx, hy in handles:
            painter.drawRect(int(hx), int(hy), h, h)

    def draw_table(self, painter: QPainter, table: Table):
        if self.creating_connector:
            color = QColor(180, 180, 180)
            border_color = QColor(100, 100, 100)
        else:
            color = QColor(150, 200, 100) if table.selected else QColor(200, 240, 150)
            border_color = QColor(0, 0, 0) if table.selected else QColor(100, 100, 100)
        
        painter.fillRect(int(table.x), int(table.y), int(table.width), int(table.height), color)
        
        border_width = 1 if self.creating_connector else (2 if table.selected else 1)
        painter.setPen(QPen(border_color, border_width))
        painter.drawRect(int(table.x), int(table.y), int(table.width), int(table.height))

        painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        painter.setPen(QPen(QColor(0, 0, 0)))

        title_height = 25
        painter.drawText(int(table.x), int(table.y), int(table.width), title_height,
                        Qt.AlignmentFlag.AlignCenter, table.title)

        painter.drawLine(int(table.x), int(table.y + title_height),
                        int(table.x + table.width), int(table.y + title_height))

        painter.setFont(QFont("Arial", 8))
        for i, field in enumerate(table.fields):
            y = table.y + title_height + i * 25
            painter.drawText(int(table.x + 5), int(y), int(table.width - 10), 25,
                           Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, field)

        if table.selected and not self.creating_connector:
            self.draw_resize_handles(painter, table)
            self.draw_connector_button(painter, table)

    def draw_connector_button(self, painter: QPainter, block: Block):
        button_size = 20
        button_x = block.x + block.width / 2 - button_size / 2
        button_y = block.y - button_size - 5

        painter.fillRect(int(button_x), int(button_y), button_size, button_size, QColor(76, 175, 80))
        painter.setPen(QPen(QColor(0, 0, 0), 1))
        painter.drawRect(int(button_x), int(button_y), button_size, button_size)

        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        painter.drawText(int(button_x), int(button_y), button_size, button_size,
                        Qt.AlignmentFlag.AlignCenter, "+")

        self.connector_button_rect = QRect(int(button_x), int(button_y), button_size, button_size)

    def draw_connector(self, painter: QPainter, connector: Connector):
        from_block = self.get_block_by_id(connector.from_id)
        to_block = self.get_block_by_id(connector.to_id)

        if not from_block or not to_block:
            return

        p1 = from_block.get_connection_point(to_block)
        p2 = to_block.get_connection_point(from_block)

        color = QColor(200, 0, 0) if connector.selected else QColor(100, 100, 100)
        pen_width = 2 if connector.selected else 1
        painter.setPen(QPen(color, pen_width))
        painter.drawLine(int(p1.x), int(p1.y), int(p2.x), int(p2.y))

        angle = math.atan2(p2.y - p1.y, p2.x - p1.x)
        arrow_size = 10

        p_left = Point(p2.x - arrow_size * math.cos(angle - math.pi / 6),
                       p2.y - arrow_size * math.sin(angle - math.pi / 6))
        p_right = Point(p2.x - arrow_size * math.cos(angle + math.pi / 6),
                        p2.y - arrow_size * math.sin(angle + math.pi / 6))

        painter.setBrush(QBrush(color))
        arrow = QPolygonF([QPointF(p2.x, p2.y), QPointF(p_left.x, p_left.y), QPointF(p_right.x, p_right.y)])
        painter.drawPolygon(arrow)

    def save_as_image(self, filepath: str):
        all_blocks = self.get_all_blocks()
        if not all_blocks:
            return

        min_x = min([b.x for b in all_blocks], default=0)
        min_y = min([b.y for b in all_blocks], default=0)
        max_x = max([b.x + b.width for b in all_blocks], default=800)
        max_y = max([b.y + b.height for b in all_blocks], default=600)

        width = int(max_x - min_x + 40)
        height = int(max_y - min_y + 40)

        image = QImage(width, height, QImage.Format.Format_RGB32)
        image.fill(QColor(240, 240, 240))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(-int(min_x) + 20, -int(min_y) + 20)

        for connector in self.connectors:
            self.draw_connector(painter, connector)

        for block in self.blocks:
            self.draw_block(painter, block)

        for table in self.tables:
            self.draw_table(painter, table)

        painter.end()
        image.save(filepath, "PNG")


class DiagramApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diagram Creator")
        self.setGeometry(100, 100, 1000, 700)

        self.canvas = DiagramCanvas()
        self.active_button = None

        main_widget = QWidget()
        layout = QVBoxLayout()

        toolbar_layout = QHBoxLayout()
        
        create_btn = QPushButton("Create Diagram")
        create_btn.clicked.connect(self.new_diagram)
        
        block_btn = QPushButton("Add Block")
        block_btn.clicked.connect(lambda: self.on_tool_button(block_btn, self.canvas.add_block))
        
        table_btn = QPushButton("Add Table")
        table_btn.clicked.connect(lambda: self.on_tool_button(table_btn, self.canvas.add_table))
        
        delete_btn = QPushButton("Delete")
        delete_btn.clicked.connect(self.canvas.delete_selected)
        
        edit_btn = QPushButton("Edit")
        edit_btn.clicked.connect(self.canvas.edit_selected)

        toolbar_layout.addWidget(create_btn)
        toolbar_layout.addWidget(block_btn)
        toolbar_layout.addWidget(table_btn)
        toolbar_layout.addWidget(edit_btn)
        toolbar_layout.addWidget(delete_btn)
        toolbar_layout.addStretch()

        save_project_btn = QPushButton("Save Diagram")
        save_project_btn.clicked.connect(self.save_project)
        toolbar_layout.addWidget(save_project_btn)
        
        load_project_btn = QPushButton("Load Diagram")
        load_project_btn.clicked.connect(self.load_project)
        toolbar_layout.addWidget(load_project_btn)
        
        export_btn = QPushButton("Export")
        export_btn.clicked.connect(self.export_diagram)
        toolbar_layout.addWidget(export_btn)

        layout.addLayout(toolbar_layout)
        layout.addWidget(self.canvas)

        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)

    def on_tool_button(self, button: QPushButton, action):
        if self.active_button and self.active_button != button:
            self.active_button.setStyleSheet("")
        
        if self.active_button == button:
            button.setStyleSheet("")
            self.active_button = None
        else:
            button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            self.active_button = button
        
        action()

    def new_diagram(self):
        self.canvas.blocks.clear()
        self.canvas.tables.clear()
        self.canvas.connectors.clear()
        self.canvas.selected_id = None
        self.canvas.element_counter = 0
        self.canvas.creating_connector = False
        self.canvas.connector_start = None
        self.canvas.update()

    def save_project(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Save Diagram", "", "Diagram File (*.dgm)")
        if filepath:
            try:
                data = {
                    'blocks': [{'id': b.id, 'x': b.x, 'y': b.y, 'width': b.width, 'height': b.height, 'title': b.title} 
                              for b in self.canvas.blocks],
                    'tables': [{'id': t.id, 'x': t.x, 'y': t.y, 'width': t.width, 'height': t.height, 'title': t.title, 'fields': t.fields} 
                              for t in self.canvas.tables],
                    'connectors': [{'id': c.id, 'from_id': c.from_id, 'to_id': c.to_id} 
                                  for c in self.canvas.connectors]
                }
                import json
                with open(filepath, 'w') as f:
                    json.dump(data, f, indent=2)
                QMessageBox.information(self, "Success", f"Diagram saved to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save: {str(e)}")

    def load_project(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Load Diagram", "", "Diagram File (*.dgm)")
        if filepath:
            try:
                import json
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                self.canvas.blocks.clear()
                self.canvas.tables.clear()
                self.canvas.connectors.clear()
                
                for block_data in data.get('blocks', []):
                    block = Block(block_data['id'], block_data['x'], block_data['y'], 
                                 block_data['width'], block_data['height'], block_data['title'])
                    self.canvas.blocks.append(block)
                    self.canvas.element_counter = max(self.canvas.element_counter, 
                                                      int(block_data['id'].split('_')[1]) + 1)
                
                for table_data in data.get('tables', []):
                    table = Table(table_data['id'], table_data['x'], table_data['y'], 
                                 table_data['width'], table_data['height'], table_data['title'])
                    table.fields = table_data.get('fields', [])
                    table.update_height()
                    self.canvas.tables.append(table)
                    self.canvas.element_counter = max(self.canvas.element_counter, 
                                                      int(table_data['id'].split('_')[1]) + 1)
                
                for conn_data in data.get('connectors', []):
                    connector = Connector(conn_data['id'], conn_data['from_id'], conn_data['to_id'])
                    self.canvas.connectors.append(connector)
                    self.canvas.element_counter = max(self.canvas.element_counter, 
                                                      int(conn_data['id'].split('_')[1]) + 1)
                
                self.canvas.selected_id = None
                self.canvas.update()
                QMessageBox.information(self, "Success", f"Diagram loaded from {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load: {str(e)}")

    def export_diagram(self):
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Diagram", "", "PNG Image (*.png)")
        if filepath:
            try:
                self.canvas.save_as_image(filepath)
                QMessageBox.information(self, "Success", f"Diagram exported to {filepath}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DiagramApp()
    window.show()
    sys.exit(app.exec())