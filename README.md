# Diagram Creator

A desktop application for creating and editing UML-like diagrams with visual blocks, tables, connectors, and real-time resizing.

## Features

- **Visual blocks** — simple rectangular shapes with custom titles and dimensions
- **Data tables** — blocks with unlimited fields that auto-resize based on content
- **Directional connectors** — arrows between elements with smart edge attachment
- **Resize handles** — visual corner and edge handles for intuitive dimension adjustment
- **Drag and drop** — move blocks and tables freely across the canvas
- **Project management** — save and load diagram projects for later editing
- **PNG export** — export final diagrams as high-quality PNG images
- **Real-time preview** — instant visual feedback for all changes
- **Duplicate connector prevention** — only one connection allowed between two elements

## Supported Platforms

Cross-platform compatibility verified on:

- Windows 10, Windows 11
- Windows Subsystem for Linux 2 (WSL2)
- macOS 10.14+
- Linux (Ubuntu 20.04+)

Requires Python 3.8 or higher.

## Requirements

- **Python** 3.8+
- **PyQt6** 6.7.0

## Installation

### From source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/diagram-creator.git
   cd diagram-creator
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python diagram_app.py
   ```

## Usage

### Create diagram
1. Launch the application
2. Click **"Add Block"** or **"Add Table"** to add elements
3. Click and drag elements to reposition them
4. Use corner/edge handles to resize elements

### Connect elements
1. Select a block or table
2. Click the green **"+"** button above the element
3. Click the target element to create a connection
4. Only one connection allowed between any two elements (old one replaces new)

### Edit elements
- **Double-click** any element or select and click **"Edit"** to modify
  - For blocks: change title, width, height
  - For tables: change title, width, and add/remove fields
- **Delete**: select element and press Delete or click **"Delete"**

### Save and manage
- **Save Diagram** — saves editable project as `.dgm` file for resuming later
- **Load Diagram** — restores previously saved project with all elements and connections
- **Export** — saves final diagram as PNG image file

### Keyboard shortcuts
- `Delete` — remove selected element
- `Ctrl+E` — edit selected element

## File Structure

```
diagram-creator/
├── diagram_app.py      — Main application
├── requirements.txt    — Python dependencies
├── README.md          — Documentation
└── RELEASE.md         — Release notes
```

## Technical Details

**GUI Framework:** PyQt6 — cross-platform desktop application framework

**Architecture:** Single-window application with canvas-based drawing system

**Data Format:** `.dgm` files store diagrams as JSON with element positions, dimensions, titles, and connection mappings

**Export:** QPainter-based rendering to PNG with automatic canvas sizing

## Known Limitations

- Canvas has unlimited size but scrolling not yet implemented
- Connector routing is direct line (no path optimization)
- Tables auto-adjust height based on field count; width must be set manually

## Building Executable

Using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed diagram_app.py
```

Compiled executable will be in `dist/diagram_app.exe`.

## License

[MIT](LICENSE)

---

*This project was developed with assistance from [Claude](https://claude.ai) (Anthropic).*
