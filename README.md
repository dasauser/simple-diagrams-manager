# Diagram Creator

Simple diagram editor for creating UML-like diagrams with blocks, tables, and connectors.

## Installation

1. Install Python 3.9+
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running

```bash
python diagram_app.py
```

## Features

### Core Elements

1. **Blocks** - Simple rectangular shapes with text labels
   - Add: Click "Add Block" button
   - Edit: Double-click block or select + click "Edit"
   - Move: Click and drag
   - Delete: Select + press Delete or click "Delete" button
   - Customize: Title, width, height

2. **Tables** - Blocks with fields that auto-resize
   - Add: Click "Add Table" button
   - Edit: Double-click or click "Edit"
   - Fields: Add/remove unlimited fields
   - Height auto-adjusts based on field count

3. **Connectors** - Directional arrows between elements
   - Add: Select source block, click "Add Connector", click target block
   - Delete: Select connector + press Delete
   - Auto-routing: Arrows attach to nearest edges

### Controls

- **Left Click**: Select element / Start dragging
- **Double Click**: Edit selected element
- **Delete Key**: Delete selected element
- **Ctrl+E**: Edit selected element
- **Drag**: Move blocks around canvas

### Saving

- Click "Save Diagram" button in top-right
- Choose location and filename
- Diagram exports as PNG image
- Automatically calculates optimal canvas size

### Starting Fresh

- Click "Create Diagram" to clear and start new diagram

## File Format

Diagram data structure (JSON format if you want to extend):
```json
{
  "blocks": [
    {
      "id": "block_0",
      "x": 100,
      "y": 100,
      "width": 120,
      "height": 60,
      "title": "Block Name"
    }
  ],
  "tables": [
    {
      "id": "table_0",
      "x": 300,
      "y": 100,
      "width": 150,
      "height": 110,
      "title": "Table Name",
      "fields": ["field1", "field2"]
    }
  ],
  "connectors": [
    {
      "id": "connector_0",
      "from_id": "block_0",
      "to_id": "table_0"
    }
  ]
}
```

## Keyboard Shortcuts

- `Delete`: Remove selected element
- `Ctrl+E`: Edit selected element

## Tips

- Connectors automatically route to the closest edge
- Table height adjusts automatically when fields are added/removed
- Use Edit dialog to precisely set dimensions and names
- Workspace has unlimited space - scroll as needed
