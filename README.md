# Maya-SBTools

[English](README.md) | [日本語](README_JP.md)

**Latest Version: v1.0.0**

A collection of utility scripts and plugins for Autodesk Maya.

## Installation

1. Download `Maya-SBTools_v1.0.0.zip` from the Releases page.
2. Extract the downloaded ZIP file.
3. Copy the extracted `modules` folder into your Maya user documents directory (e.g., `Documents\maya\`).
4. Start (or restart) Maya.
5. You should now see an **[SBTools]** menu added to the main menu bar.

## Triangles to Quads

Triangles to Quads is a high-performance Maya plugin that converts triangulated meshes into clean quad topology while preserving the original structure. Compared to Maya's standard "Quadrangulate" feature, it utilizes an algorithm that accurately reads the topology flow, particularly on curved surfaces.

### Features & Benefits

- **High-Quality Grid Flow:** Takes into account the flow of adjacent polygons to generate natural topology with minimal distortion.
- **Fast Execution:** Optimized to process meshes with tens of thousands of polygons in seconds.
- **Boundary Preservation:** Prevents unintended merging across UV seams, material boundaries, and sharp edges.
- **Maya Native Integration:** Fully supports progress bars and a single undo chunk.

### Comparison with Maya Standard Quadrangulate

This tool is based on the highly acclaimed quadrangulation algorithm from Blender, offering significant advantages in "quad alignment," especially on curved surfaces.

|                         Angle                         |       Original Triangles       |         Maya Standard Quads          |              SBTools Quads              |
| :---------------------------------------------------: | :----------------------------: | :----------------------------------: | :-------------------------------------: |
| <span style="white-space: nowrap;">**Angle 1**</span> | <img src="images/tri_01.webp"> | <img src="images/quad_maya_01.webp"> | <img src="images/quad_sbtools_01.webp"> |
| <span style="white-space: nowrap;">**Angle 2**</span> | <img src="images/tri_02.webp"> | <img src="images/quad_maya_02.webp"> | <img src="images/quad_sbtools_02.webp"> |
| <span style="white-space: nowrap;">**Angle 3**</span> | <img src="images/tri_03.webp"> | <img src="images/quad_maya_03.webp"> | <img src="images/quad_sbtools_03.webp"> |

### Basic Usage

1. Select the target polygon mesh in **Object Mode** (multiple selections are supported).
2. Go to the `[SBTools] > [Triangles to Quads]` menu and execute it.

<img src="images/ui_Triangles to Quads.webp">

To adjust settings, click the **Option Box (□)** next to the menu item to open the settings window.

<img src="images/ui_Triangles to Quads_op.webp">

### Option Settings Details

In the options window, you can adjust the following parameters to control the conversion results.

#### Angle Thresholds

- **Face Normal Angle** (Default: 40.0): If the difference in normal angles between adjacent faces exceeds this value, the edge will not be merged.
- **Shape Angle** (Default: 40.0): Specifies how much the corners of the generated quads can deviate from 90 degrees.

#### Keep Boundary

- **Keep UV Boundary**: When enabled, prevents quadrangulation across UV seams.
- **Keep Material Boundary**: When enabled, prevents merging between faces assigned different materials.
- **Keep Sharp Edge**: When enabled, preserves hard edges (Sharp Edges).

#### Advanced Features

- **Topology Influence** (0.0 - 2.0): The core setting of this tool.
  - `0.0`: Evaluates based on shape flatness only.
  - `1.0`: Standard setting. Aligns with the surrounding flow.
  - `2.0`: Strongly prioritizes alignment with the surrounding grid flow.

### Technical Approach

Behind the scenes, this tool employs advanced computational geometry optimization.

- **Blender Algorithm Port:** Implements an optimized version of Blender's highly regarded `bmo_join_triangles` algorithm for the Maya Python API (OpenMaya).
- **Priority Queue with Lazy Evaluation:** Calculates the "quality (error value) when merged" for all edges and processes them in order of best quality. When one edge is merged, the scores of surrounding edges are updated (chained) in real-time.
- **O(1) Lookups:** By pre-calculating topology traversal, it ensures that computational complexity does not grow exponentially even for large meshes.
- **Batch Processing:** Minimizes API call overhead by passing all edge deletions to Maya commands (`polyDelEdge`) in a single batch.

## License

This project is licensed under the **GNU General Public License v3.0**. See [LICENSE](LICENSE) for details.

## Changelog (Brief)

- **v1.0.0 (2026-05-13)**
  - Initial release.
  - Added Triangles to Quads plugin with Blender-style Topology Influence optimization.

For a full history of changes, see the [CHANGELOG](CHANGELOG.md).
