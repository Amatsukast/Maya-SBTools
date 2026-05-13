# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-05-13
### Added
- **Triangles to Quads (Tris to Quads) plugin:**
  - Fast execution optimized for high-density polygon meshes (tens of thousands of polygons).
  - Topology Influence support inspired by Blender's BMesh implementation, enforcing clean grid-like quad flow even on curved surfaces (incorporating `rotate_to_plane` alignment).
  - Options to preserve UV boundaries, Material boundaries, and Sharp edges.
  - Interactive UI Options window for parameter adjustment.
  - Native Maya progress bar integration and unified undo chunk support.
  - Core O(E log E) optimization utilizing a lazy-deletion priority queue for scaling batch edge merging.
