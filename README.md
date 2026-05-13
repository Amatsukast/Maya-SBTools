# Maya-SBTools

**Latest Version: v1.0.0**

A collection of utility scripts and plugins for Autodesk Maya.

## Triangles to Quads (Tris to Quads)

A high-performance Maya plugin that converts triangulated meshes into clean quad topology. Based on the robust algorithms used in Blender, it features O(E log E) optimization, a priority queue for edge merging, and advanced Topology Influence logic to ensure grid-like quad flows, especially on curved surfaces.

### Features

- **Fast execution:** Optimized to handle high-density meshes (tens of thousands of polygons) in seconds.
- **Topology Influence:** Aggressively aligns new quads with existing geometry for natural grid flows.
- **Boundary preservation:** Options to keep UV boundaries, material boundaries, and sharp edges intact.
- **Maya native integration:** Complete with progress bar support and a single undo chunk.

### Usage

1. Select the target polygon mesh in **Object Mode**.
2. Go to the `SBTools` menu and click **Triangles to Quads**.
3. (Optional) Open the option box (□) next to the menu item to adjust advanced settings like Topology Influence.

## Installation

1. Download `Maya-SBTools_v1.0.0.zip` from the Releases page.
2. Extract the downloaded ZIP file.
3. Copy the extracted `modules` folder into your Maya documents directory (e.g., `Documents\maya\`).
4. Restart Maya.

## License

This project is licensed under the **GNU General Public License v3.0**. See [LICENSE](LICENSE) for details.

## Changelog (Brief)

- **v1.0.0 (2026-05-13)**
  - Initial release.
  - Added Triangles to Quads plugin with Blender-style Topology Influence optimization.

For a full history of changes, see the [CHANGELOG](CHANGELOG.md).
