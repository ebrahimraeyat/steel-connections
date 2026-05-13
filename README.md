# Steel Connection Designer

An interactive desktop application for the design and checking of **Bolted Flange Plate (BFP)** moment connections in structural steel frames.  
Supports both the **Iranian Code (PN-S 2800 / Instruction 360)** and **AISC 358-16 (USA)** design standards.

---

## Table of Contents

1. [Overview](#overview)
2. [Interface Layout](#interface-layout)
3. [Left Panel — Inputs](#left-panel--inputs)
4. [Centre Panel — 3-D Viewer & Log](#centre-panel--3-d-viewer--log)
5. [Right Panel — Design Results](#right-panel--design-results)
6. [File Menu](#file-menu)
7. [Exporting a Report](#exporting-a-report)
8. [Units](#units)
9. [Keyboard Shortcuts](#keyboard-shortcuts)

---

## Overview

Steel Connection Designer checks a BFP connection against the selected design code and displays the 3-D geometry in real time.  
Every time an input value changes, the calculation runs automatically and the results panel updates instantly.

---

## Interface Layout

![image](https://github.com/user-attachments/assets/41a7654f-861c-42f7-9309-30af7622d6ae)

The three panels can be resized by dragging the splitter handles.

---

## Left Panel — Inputs

The left panel is a scrollable form.  Each section contains an annotated 3-D sketch that shows exactly which dimension each input controls.

### Design Code
Select the design standard to apply:

| Option | Standard |
|--------|----------|
| Iranian Code (PN-S 2800 / Instruction 360) | Iranian national standard |
| AISC 358-16 (USA) | AISC Prequalified Connections |

Changing the design code reruns all checks immediately.

### Beam
Enter the cross-section dimensions of the connected beam.

| Label | Meaning |
|-------|---------|
| Bf | Flange width (cm) |
| D  | Total depth (cm) |
| tf | Flange thickness — select from standard list |
| tw | Web thickness — select from standard list |

The sketch shows a horizontal I-section extruded in 3-D with a faded column silhouette behind it.

### Column
Same fields as Beam.  
The sketch shows a vertical column extruded upward with a faded beam silhouette at the connection level.

### Flange Plate
The horizontal cover plates welded to the beam flanges and bolted to the column.

| Label | Meaning |
|-------|---------|
| b (←→) | Plate length along the beam axis (cm) |
| h (↑↓) | Plate width across the flange (cm) |
| t  | Plate thickness — select from standard list |

The sketch shows two bold green plates with a faded I-section underneath.

### Web Plate
The shear tab connecting the beam web to the column.

| Label | Meaning |
|-------|---------|
| b (←→) | Plate width (horizontal, across web) (cm) |
| h (↑↓) | Plate height (vertical, along beam depth) (cm) |
| t  | Plate thickness — select from standard list |

The sketch shows a bold green vertical plate with the web cross-section faded behind it.

### Flange Bolts
High-strength bolts connecting the flange plates to the column face.

| Field | Meaning |
|-------|---------|
| Diameter | Bolt shank diameter (cm): 2.4 / 2.7 / 3.0 |
| N (rows/Z) | Number of bolt rows along the beam axis |
| M (gauge/X) | Number of bolt columns across the plate width |

### Web Bolts
Bolts connecting the web plate to the beam web.

| Field | Meaning |
|-------|---------|
| Diameter | Bolt shank diameter (cm): 2.0 / 2.4 / 2.7 |
| Rows (Z) | Number of bolt rows (vertical) |
| Cols (X) | Number of bolt columns (horizontal) |

---

## Centre Panel — 3-D Viewer & Log

### 3-D Viewer
The connection geometry updates automatically after every input change (250 ms debounce).  
Use the toolbar buttons to control the view:

| Button | Action |
|--------|--------|
| Isometric | Standard isometric view |
| Front | Front elevation |
| Side | Side elevation |
| Top | Plan view |
| Fit All | Zoom to fit all geometry |
| Shaded | Solid shaded display |
| Wireframe | Wireframe display |

Mouse controls: **left-drag** to rotate, **middle-drag** to pan, **scroll** to zoom.

### Design Log
The log below the viewer shows timestamped messages after each calculation:

- **INFO** — design code name, warnings about geometry adjustments
- **✓ OK** — connection passes all checks (green)
- **⚠ Warning** — one or more checks failed (orange), with a description of each failure

---

## Right Panel — Design Results

### Connection Values

| Field | Meaning |
|-------|---------|
| M_pr (t·cm) | Probable flexural resistance of the beam |
| sh (cm) | Horizontal bolt pitch |
| lh (cm) | Horizontal edge distance |
| kl (cm) | Column clear height |
| s3 (cm) | Bolt row spacing |
| s5 (cm) | Edge distance |

### Bolt Group

Shows the selected bolt grade, total bolt count, and factored bolt resistance φRn (t).

### Design Checks

A table listing every code check with a **✓ OK** or **✗ NG** result.  
When a check fails, the row turns red and a description appears in the Design Log.

---

## File Menu

| Command | Shortcut | Description |
|---------|----------|-------------|
| New | Ctrl+N | Reset all inputs to defaults |
| Open… | Ctrl+O | Open a saved model file (`.scj`) |
| Save | Ctrl+S | Save the current model |
| Save As… | Ctrl+Shift+S | Save to a new file |
| Quit | Ctrl+Q | Exit the application |

When there are unsaved changes the title bar shows a **●** marker.  
Closing the window with unsaved changes prompts: **Save / Discard / Cancel**.

Model files use the `.scj` (Steel Connection JSON) format.

---

## Exporting a Report

Click **📄 Export Report** in the viewer toolbar.  
Choose a location — a Word (`.docx`) document is generated containing:

- Project header with design code name and date
- All input values
- Step-by-step calculations with clause references
- Check summary table (Check / Criterion / Code Reference / Result)
- Final adequacy verdict

After saving, a dialog asks whether to open the file immediately.

---

## Units

All inputs and outputs use the following consistent unit system:

| Quantity | Unit |
|----------|------|
| Length / Dimensions | cm |
| Force | kgf |
| Moment | kgf·cm |
| Stress | kgf/cm² |

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New model |
| Ctrl+O | Open model |
| Ctrl+S | Save |
| Ctrl+Shift+S | Save As |
| Ctrl+Q | Quit |

