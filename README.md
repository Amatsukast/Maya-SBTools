# Maya-SBTools

A collection of utility scripts and plugins for Autodesk Maya.

## Triangles to Quads (Tris to Quads)
A high-performance Maya plugin that converts triangulated meshes into clean quad topology. Based on the robust algorithms used in Blender, it features O(E log E) optimization, a priority queue for edge merging, and advanced Topology Influence logic to ensure grid-like quad flows, especially on curved surfaces.

### Features
- **Fast execution:** Optimized to handle high-density meshes (tens of thousands of polygons) in seconds.
- **Topology Influence:** Aggressively aligns new quads with existing geometry for natural grid flows.
- **Boundary preservation:** Options to keep UV boundaries, material boundaries, and sharp edges intact.
- **Maya native integration:** Complete with progress bar support and a single undo chunk.

## Installation
1. Copy the `modules` folder contents to your Maya modules directory.
2. Restart Maya.
3. Access the tool from the `SBTools` menu.

## License
MIT License
