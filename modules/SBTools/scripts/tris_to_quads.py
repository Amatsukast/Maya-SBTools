import maya.api.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel
import math
from heapq import heappush, heappop

# ============================================================================
# Progress Bar Helpers
# ============================================================================

_PROGRESS_BAR = None


def _progress_begin(total_steps, status="Triangles to Quads..."):
    """Start the Maya main progress bar (bottom-left)."""
    global _PROGRESS_BAR
    _PROGRESS_BAR = mel.eval("$tmp = $gMainProgressBar")
    cmds.progressBar(
        _PROGRESS_BAR,
        edit=True,
        beginProgress=True,
        isInterruptable=False,
        status=status,
        maxValue=max(total_steps, 1),
    )


def _progress_step(step=1, status=None):
    """Advance the progress bar by step."""
    if _PROGRESS_BAR is None:
        return
    kwargs = {"edit": True, "step": step}
    if status is not None:
        kwargs["status"] = status
    cmds.progressBar(_PROGRESS_BAR, **kwargs)


def _progress_end():
    """End the progress bar."""
    global _PROGRESS_BAR
    if _PROGRESS_BAR is not None:
        cmds.progressBar(_PROGRESS_BAR, edit=True, endProgress=True)
        _PROGRESS_BAR = None


# ============================================================================
# Math Helper Functions
# ============================================================================


def sub_v3_v3v3(a, b):
    """Vector subtraction: result = a - b"""
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def normalize_v3(n):
    """Normalize vector and return length"""
    length = math.sqrt(n[0] * n[0] + n[1] * n[1] + n[2] * n[2])
    if length > 0:
        return (n[0] / length, n[1] / length, n[2] / length), length
    return n, 0


def dot_v3v3(a, b):
    """Dot product"""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def angle_normalized_v3v3(v1, v2):
    """Angle between two normalized vectors"""
    dot = max(-1.0, min(1.0, dot_v3v3(v1, v2)))
    return math.acos(dot)


def compare_v3v3(v1, v2, limit):
    """Compare two vectors with tolerance"""
    return (
        abs(v1[0] - v2[0]) < limit
        and abs(v1[1] - v2[1]) < limit
        and abs(v1[2] - v2[2]) < limit
    )


def normal_tri_v3(v1, v2, v3):
    """Calculate triangle normal"""
    edge1 = sub_v3_v3v3(v2, v1)
    edge2 = sub_v3_v3v3(v3, v1)

    # Cross product
    nx = edge1[1] * edge2[2] - edge1[2] * edge2[1]
    ny = edge1[2] * edge2[0] - edge1[0] * edge2[2]
    nz = edge1[0] * edge2[1] - edge1[1] * edge2[0]

    normal, _ = normalize_v3((nx, ny, nz))
    return normal


def area_tri_v3(v1, v2, v3):
    """Calculate triangle area"""
    edge1 = sub_v3_v3v3(v2, v1)
    edge2 = sub_v3_v3v3(v3, v1)

    # Cross product magnitude
    cx = edge1[1] * edge2[2] - edge1[2] * edge2[1]
    cy = edge1[2] * edge2[0] - edge1[0] * edge2[2]
    cz = edge1[0] * edge2[1] - edge1[1] * edge2[0]

    return 0.5 * math.sqrt(cx * cx + cy * cy + cz * cz)


def quad_calc_error(v1, v2, v3, v4):
    """
    Computes error of a proposed merge quad.
    Lower error = better quad quality.
    """
    error = 0.0

    # 1. Normal difference: perfectly flat planar face adds zero
    n1 = normal_tri_v3(v1, v2, v3)
    n2 = normal_tri_v3(v1, v3, v4)
    angle_a = 0.0 if compare_v3v3(n1, n2, 1e-6) else angle_normalized_v3v3(n1, n2)

    n1 = normal_tri_v3(v2, v3, v4)
    n2 = normal_tri_v3(v4, v1, v2)
    angle_b = 0.0 if compare_v3v3(n1, n2, 1e-6) else angle_normalized_v3v3(n1, n2)

    diff = (angle_a + angle_b) / (math.pi * 2)
    error += diff

    # 2. Co-linearity: face with four right angle corners adds zero
    edge_vecs = [
        sub_v3_v3v3(v1, v2),
        sub_v3_v3v3(v2, v3),
        sub_v3_v3v3(v3, v4),
        sub_v3_v3v3(v4, v1),
    ]

    edge_vecs_normalized = []
    for vec in edge_vecs:
        normalized, _ = normalize_v3(vec)
        edge_vecs_normalized.append(normalized)

    diff = (
        abs(
            angle_normalized_v3v3(edge_vecs_normalized[0], edge_vecs_normalized[1])
            - math.pi / 2
        )
        + abs(
            angle_normalized_v3v3(edge_vecs_normalized[1], edge_vecs_normalized[2])
            - math.pi / 2
        )
        + abs(
            angle_normalized_v3v3(edge_vecs_normalized[2], edge_vecs_normalized[3])
            - math.pi / 2
        )
        + abs(
            angle_normalized_v3v3(edge_vecs_normalized[3], edge_vecs_normalized[0])
            - math.pi / 2
        )
    ) / (math.pi * 2)

    error += diff

    # 3. Concavity: face with no concavity adds zero
    area_a = area_tri_v3(v1, v2, v3) + area_tri_v3(v1, v3, v4)
    area_b = area_tri_v3(v2, v3, v4) + area_tri_v3(v4, v1, v2)

    area_min = min(area_a, area_b)
    area_max = max(area_a, area_b)

    diff = (1.0 - (area_min / area_max)) if area_max > 0 else 1.0
    error += diff

    return error


def compute_quad_edge_vecs(positions):
    """Compute 4 normalized edge vectors of a quad."""
    vecs = []
    for i in range(4):
        vec = sub_v3_v3v3(positions[i], positions[(i + 1) % 4])
        n, _ = normalize_v3(vec)
        vecs.append(n)
    return vecs


def cross_v3v3(a, b):
    """Cross product of two 3D vectors."""
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def rotate_v3_around_axis(v, axis, cos_a, sin_a):
    """Rotate vector v around unit axis using Rodrigues' formula."""
    dot = dot_v3v3(v, axis)
    cr = cross_v3v3(axis, v)
    k = dot * (1.0 - cos_a)
    return (
        v[0] * cos_a + cr[0] * sin_a + axis[0] * k,
        v[1] * cos_a + cr[1] * sin_a + axis[1] * k,
        v[2] * cos_a + cr[2] * sin_a + axis[2] * k,
    )


def normal_quad_v3(v1, v2, v3, v4):
    """Compute quad normal as average of two triangle normals."""
    n1 = normal_tri_v3(v1, v2, v3)
    n2 = normal_tri_v3(v1, v3, v4)
    avg = ((n1[0] + n2[0]) / 2, (n1[1] + n2[1]) / 2, (n1[2] + n2[2]) / 2)
    result, _ = normalize_v3(avg)
    return result


def rotate_quad_to_plane(quad_positions, shared_v0, shared_v1, plane_normal):
    """
    Rotate quad_b around the shared edge to be coplanar with quad_a.
    Based on Blender's rotate_to_plane from bmo_join_triangles.cc.

    Args:
        quad_positions: list of 4 (x,y,z) position tuples
        shared_v0, shared_v1: positions of the shared edge vertices (hinge)
        plane_normal: normal of the reference quad (quad_a)
    Returns: list of 4 rotated positions
    """
    axis_vec = sub_v3_v3v3(shared_v0, shared_v1)
    axis, axis_len = normalize_v3(axis_vec)
    if axis_len < 1e-8:
        return quad_positions

    quad_normal = normal_quad_v3(
        quad_positions[0],
        quad_positions[1],
        quad_positions[2],
        quad_positions[3],
    )

    # Signed angle from plane_normal to quad_normal around axis
    cr = cross_v3v3(plane_normal, quad_normal)
    sin_angle = dot_v3v3(cr, axis)
    cos_angle = dot_v3v3(plane_normal, quad_normal)
    angle = math.atan2(sin_angle, cos_angle)

    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    result = []
    for pos in quad_positions:
        # Check if this vertex is on the shared edge (hinge)
        if compare_v3v3(pos, shared_v0, 1e-6) or compare_v3v3(pos, shared_v1, 1e-6):
            result.append(pos)
        else:
            local = sub_v3_v3v3(pos, shared_v0)
            rotated = rotate_v3_around_axis(local, axis, cos_a, sin_a)
            result.append(
                (
                    rotated[0] + shared_v0[0],
                    rotated[1] + shared_v0[1],
                    rotated[2] + shared_v0[2],
                )
            )
    return result


def compute_alignment(
    quad_a_vecs, quad_b_positions, shared_v0=None, shared_v1=None, plane_normal=None
):
    """
    Compute alignment between two quads (0=misaligned, 1=perfect grid).
    Based on Blender's compute_alignment from bmo_join_triangles.cc.
    If shared edge and plane_normal are provided, rotates quad_b to be
    coplanar with quad_a first (important for curved surfaces).
    """
    if shared_v0 is not None and plane_normal is not None:
        quad_b_positions = rotate_quad_to_plane(
            quad_b_positions,
            shared_v0,
            shared_v1,
            plane_normal,
        )

    quad_b_vecs = compute_quad_edge_vecs(quad_b_positions)

    errors = [0.0, 0.0, 0.0, 0.0]
    for i in range(4):
        angle_a = abs(angle_normalized_v3v3(quad_a_vecs[i], quad_b_vecs[i]))
        angle_b = abs(angle_normalized_v3v3(quad_a_vecs[i], quad_b_vecs[(i + 1) % 4]))
        errors[0] += angle_a
        errors[1] += angle_b
        errors[2] += math.pi - angle_a
        errors[3] += math.pi - angle_b

    best_error = min(errors) / 4.0
    alignment = max(0.0, 1.0 - (best_error / (math.pi / 4.0)))
    return alignment


def is_quad_flip_v3(v1, v2, v3, v4):
    """
    Check if quad is flipped/concave.
    Returns True if the quad would be twisted or concave.
    """
    edge1 = sub_v3_v3v3(v2, v1)
    edge2 = sub_v3_v3v3(v3, v2)
    edge3 = sub_v3_v3v3(v4, v3)
    edge4 = sub_v3_v3v3(v1, v4)

    def cross(a, b):
        return (
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        )

    c1 = cross(edge1, edge2)
    c2 = cross(edge2, edge3)
    c3 = cross(edge3, edge4)
    c4 = cross(edge4, edge1)

    return dot_v3v3(c1, c2) < 0 or dot_v3v3(c2, c3) < 0 or dot_v3v3(c3, c4) < 0


# ============================================================================
# Selection Helpers
# ============================================================================


def get_selected_mesh():
    """
    Get the selected mesh as MFnMesh.
    Returns: (mesh_fn, dag_path) or (None, None)
    """
    selection = om.MGlobal.getActiveSelectionList()
    if selection.isEmpty():
        print("ERROR: No mesh selected")
        return None, None

    try:
        dag_path = selection.getDagPath(0)
        mesh_fn = om.MFnMesh(dag_path)
        return mesh_fn, dag_path
    except:
        print("ERROR: Selected object is not a mesh")
        return None, None


def get_selected_meshes():
    """
    Get all selected meshes as a list of (mesh_fn, dag_path).
    Non-mesh objects are silently skipped.
    """
    selection = om.MGlobal.getActiveSelectionList()
    if selection.isEmpty():
        return []

    meshes = []
    for i in range(selection.length()):
        try:
            dag_path = selection.getDagPath(i)
            mesh_fn = om.MFnMesh(dag_path)
            meshes.append((mesh_fn, dag_path))
        except Exception:
            continue
    return meshes


def get_mesh_by_name(mesh_name):
    """
    Get mesh by its name.
    Returns: (mesh_fn, dag_path) or (None, None)
    """
    try:
        sel = om.MSelectionList()
        sel.add(mesh_name)
        dag_path = sel.getDagPath(0)
        mesh_fn = om.MFnMesh(dag_path)
        return mesh_fn, dag_path
    except Exception:
        return None, None


# ============================================================================
# Mesh Data Pre-computation (single-pass topology scan)
# ============================================================================


def build_mesh_data(
    mesh_fn, dag_path, keep_uv_boundary, keep_sharp_edge, keep_material_boundary
):
    """
    Pre-compute all topology data needed for the algorithm in a single pass.
    Returns a dict with all lookup tables for O(1) access.
    """
    num_edges = mesh_fn.numEdges
    num_faces = mesh_fn.numPolygons
    num_verts = mesh_fn.numVertices

    # --- Edge data: single pass through MItMeshEdge ---
    edge_faces = {}  # edge_id -> (face_a, face_b) or None
    edge_verts = {}  # edge_id -> (v0, v1)
    edge_smooth = {}  # edge_id -> bool

    edge_iter = om.MItMeshEdge(mesh_fn.object())
    while not edge_iter.isDone():
        eid = edge_iter.index()
        faces = edge_iter.getConnectedFaces()
        edge_faces[eid] = tuple(faces) if len(faces) == 2 else None
        edge_verts[eid] = (edge_iter.vertexId(0), edge_iter.vertexId(1))
        if keep_sharp_edge:
            edge_smooth[eid] = edge_iter.isSmooth
        edge_iter.next()

    # --- Face data ---
    face_verts = {}
    for fid in range(num_faces):
        face_verts[fid] = list(mesh_fn.getPolygonVertices(fid))

    # --- Vertex positions ---
    points = mesh_fn.getPoints(om.MSpace.kWorld)
    vert_pos = {}
    for vid in range(num_verts):
        p = points[vid]
        vert_pos[vid] = (p.x, p.y, p.z)

    # --- Face normals ---
    face_normals = {}
    for fid in range(num_faces):
        n = mesh_fn.getPolygonNormal(fid, om.MSpace.kWorld)
        face_normals[fid] = (n.x, n.y, n.z)

    # --- Material data ---
    face_materials = []
    if keep_material_boundary:
        try:
            shaders, face_indices = mesh_fn.getConnectedShaders(
                dag_path.instanceNumber()
            )
            face_materials = list(face_indices)
        except Exception:
            pass

    # --- UV data: (face_id, global_vertex_id) -> uv_id ---
    face_vert_uvid = {}
    if keep_uv_boundary:
        try:
            for fid in range(num_faces):
                verts = face_verts[fid]
                for local_idx, vid in enumerate(verts):
                    face_vert_uvid[(fid, vid)] = mesh_fn.getPolygonUVid(fid, local_idx)
        except Exception:
            face_vert_uvid = {}

    # --- Face to edges mapping (for TI neighbor discovery) ---
    face_to_edges = {}
    for eid, ef in edge_faces.items():
        if ef is None:
            continue
        for fid in ef:
            if fid not in face_to_edges:
                face_to_edges[fid] = []
            face_to_edges[fid].append(eid)

    return {
        "edge_faces": edge_faces,
        "edge_verts": edge_verts,
        "edge_smooth": edge_smooth,
        "face_verts": face_verts,
        "vert_pos": vert_pos,
        "face_normals": face_normals,
        "face_materials": face_materials,
        "face_vert_uvid": face_vert_uvid,
        "face_to_edges": face_to_edges,
    }


# ============================================================================
# Fast Edge Evaluation (O(1) per edge using precomputed data)
# ============================================================================


def get_quad_verts_fast(edge_id, data):
    """Get the 4 vertices that would form a quad. O(1) using lookup tables."""
    faces = data["edge_faces"].get(edge_id)
    if faces is None:
        return None

    fa, fb = faces
    verts_a = data["face_verts"][fa]
    verts_b = data["face_verts"][fb]

    if len(verts_a) != 3 or len(verts_b) != 3:
        return None

    ev1, ev2 = data["edge_verts"][edge_id]

    opp_a = None
    for v in verts_a:
        if v != ev1 and v != ev2:
            opp_a = v
            break

    opp_b = None
    for v in verts_b:
        if v != ev1 and v != ev2:
            opp_b = v
            break

    if opp_a is None or opp_b is None:
        return None

    return [ev1, opp_a, ev2, opp_b]


def is_edge_delimit_fast(
    edge_id,
    data,
    angle_face_threshold,
    angle_shape_threshold,
    keep_uv_boundary,
    keep_sharp_edge,
    keep_material_boundary,
    delimit_count=None,
):
    """
    Check if an edge should be delimited (not merged).
    All lookups are O(1) using precomputed data.
    """
    faces = data["edge_faces"].get(edge_id)
    if faces is None:
        if delimit_count is not None:
            delimit_count["not_manifold"] += 1
        return True

    fa, fb = faces

    # Check material boundary
    if keep_material_boundary and data["face_materials"]:
        fm = data["face_materials"]
        if fa < len(fm) and fb < len(fm):
            if fm[fa] != fm[fb]:
                if delimit_count is not None:
                    delimit_count["material"] += 1
                return True

    # Check sharp edge
    if keep_sharp_edge and data["edge_smooth"]:
        if not data["edge_smooth"].get(edge_id, True):
            if delimit_count is not None:
                delimit_count["sharp"] += 1
            return True

    # Check UV boundary
    if keep_uv_boundary and data["face_vert_uvid"]:
        ev1, ev2 = data["edge_verts"][edge_id]
        uvid = data["face_vert_uvid"]

        uv_a1 = uvid.get((fa, ev1))
        uv_b1 = uvid.get((fb, ev1))
        if uv_a1 is not None and uv_b1 is not None and uv_a1 != uv_b1:
            if delimit_count is not None:
                delimit_count["uv"] += 1
            return True

        uv_a2 = uvid.get((fa, ev2))
        uv_b2 = uvid.get((fb, ev2))
        if uv_a2 is not None and uv_b2 is not None and uv_a2 != uv_b2:
            if delimit_count is not None:
                delimit_count["uv"] += 1
            return True

    # Check face normal angle
    if angle_face_threshold < math.radians(180):
        normal_a = data["face_normals"][fa]
        normal_b = data["face_normals"][fb]
        angle_face_cos = math.cos(angle_face_threshold)
        if dot_v3v3(normal_a, normal_b) < angle_face_cos:
            if delimit_count is not None:
                delimit_count["angle_face"] += 1
            return True

    # Check shape angle
    if angle_shape_threshold < math.radians(180):
        quad_verts = get_quad_verts_fast(edge_id, data)
        if quad_verts is None:
            if delimit_count is not None:
                delimit_count["quad_invalid"] += 1
            return True

        positions = [data["vert_pos"][v] for v in quad_verts]

        if is_quad_flip_v3(positions[0], positions[1], positions[2], positions[3]):
            if delimit_count is not None:
                delimit_count["angle_shape"] += 1
            return True

        edge_vecs = [
            sub_v3_v3v3(positions[0], positions[1]),
            sub_v3_v3v3(positions[1], positions[2]),
            sub_v3_v3v3(positions[2], positions[3]),
            sub_v3_v3v3(positions[3], positions[0]),
        ]

        edge_vecs_normalized = []
        for vec in edge_vecs:
            normalized, _ = normalize_v3(vec)
            edge_vecs_normalized.append(normalized)

        for i in range(4):
            next_i = (i + 1) % 4
            angle = angle_normalized_v3v3(
                edge_vecs_normalized[i], edge_vecs_normalized[next_i]
            )
            if abs(angle - math.pi / 2) > angle_shape_threshold:
                if delimit_count is not None:
                    delimit_count["angle_shape"] += 1
                return True

    return False


# ============================================================================
# Topology Influence
# ============================================================================

MAXIMUM_IMPROVEMENT = 0.99


def propagate_topology_influence(
    edge_id,
    data,
    topo_influence,
    consumed_faces,
    edge_version,
    edge_error,
    version_counter,
    edge_queue,
    queue_error,
    _debug_stats=None,
):
    """
    After virtually merging edge_id, improve nearby candidate edges
    based on alignment with the new quad. Core of Topology Influence.

    queue_error: the TI-adjusted error from the priority queue (NOT the
                 geometric error). This enables cascade amplification -
                 improved edges propagate their improved error to neighbors.
    """
    if _debug_stats is None:
        _debug_stats = {}

    faces = data["edge_faces"][edge_id]
    fa, fb = faces

    quad_verts = get_quad_verts_fast(edge_id, data)
    if quad_verts is None:
        _debug_stats["no_quad"] = _debug_stats.get("no_quad", 0) + 1
        return

    positions = [data["vert_pos"][v] for v in quad_verts]
    # Use queue_error (TI-adjusted) instead of recomputing from geometry.
    # This is the key to cascade amplification (matching Blender behavior).
    quad_error = queue_error
    quad_vecs = compute_quad_edge_vecs(positions)
    quad_normal = normal_quad_v3(positions[0], positions[1], positions[2], positions[3])

    # Find boundary edges of the virtual quad (all edges of fa/fb except the dissolved one)
    quad_boundary = set()
    for fid in (fa, fb):
        for eid in data["face_to_edges"].get(fid, []):
            if eid != edge_id:
                quad_boundary.add(eid)

    # Discover neighbor merge candidates (up to 8) with their shared boundary edge
    neighbor_candidates = {}  # c_eid -> b_eid (shared boundary edge)
    for b_eid in quad_boundary:
        b_faces = data["edge_faces"].get(b_eid)
        if b_faces is None:
            continue
        for nf in b_faces:
            if nf in (fa, fb) or nf in consumed_faces:
                continue
            if len(data["face_verts"][nf]) != 3:
                continue
            for c_eid in data["face_to_edges"].get(nf, []):
                if c_eid == b_eid:
                    continue
                if c_eid not in neighbor_candidates:
                    neighbor_candidates[c_eid] = b_eid

    _debug_stats["candidates_found"] = _debug_stats.get("candidates_found", 0) + len(
        neighbor_candidates
    )

    # Update priority of each valid neighbor candidate
    skipped_not_in_queue = 0
    skipped_worse = 0
    skipped_consumed = 0
    skipped_no_quad = 0
    improved = 0

    for c_eid, b_eid in neighbor_candidates.items():
        if c_eid not in edge_error:
            skipped_not_in_queue += 1
            continue

        current_err = edge_error[c_eid]

        if quad_error > current_err:
            skipped_worse += 1
            continue

        c_faces = data["edge_faces"].get(c_eid)
        if c_faces is None:
            continue
        cfa, cfb = c_faces
        if cfa in consumed_faces or cfb in consumed_faces:
            skipped_consumed += 1
            continue

        c_quad_verts = get_quad_verts_fast(c_eid, data)
        if c_quad_verts is None:
            skipped_no_quad += 1
            continue
        c_positions = [data["vert_pos"][v] for v in c_quad_verts]

        # Rotate quad_b to be coplanar with quad_a using the shared edge as hinge
        bv0, bv1 = data["edge_verts"][b_eid]
        alignment = compute_alignment(
            quad_vecs,
            c_positions,
            shared_v0=data["vert_pos"][bv0],
            shared_v1=data["vert_pos"][bv1],
            plane_normal=quad_normal,
        )

        improvement = quad_error - current_err
        multiplier = min(topo_influence * alignment, MAXIMUM_IMPROVEMENT)
        new_err = current_err + improvement * multiplier

        if new_err < current_err:
            improved += 1
            version_counter[0] += 1
            v = version_counter[0]
            edge_version[c_eid] = v
            edge_error[c_eid] = new_err
            heappush(edge_queue, (new_err, v, c_eid))

    _debug_stats["skipped_not_in_queue"] = (
        _debug_stats.get("skipped_not_in_queue", 0) + skipped_not_in_queue
    )
    _debug_stats["skipped_worse"] = _debug_stats.get("skipped_worse", 0) + skipped_worse
    _debug_stats["skipped_consumed"] = (
        _debug_stats.get("skipped_consumed", 0) + skipped_consumed
    )
    _debug_stats["improved"] = _debug_stats.get("improved", 0) + improved


# ============================================================================
# Main Algorithm (pre-compute + lazy-heap + TI + batch delete)
# ============================================================================


def triangles_to_quads(
    mesh_fn,
    dag_path,
    angle_face_threshold=math.radians(40),
    angle_shape_threshold=math.radians(40),
    keep_uv_boundary=True,
    keep_sharp_edge=True,
    keep_material_boundary=True,
    topo_influence=1.0,
):
    """
    Convert triangles to quads on a single mesh.

    Args:
        mesh_fn: MFnMesh object
        dag_path: MDagPath to the mesh
        angle_face_threshold: Maximum face normal angle difference (radians)
        angle_shape_threshold: Maximum corner angle deviation from 90 deg (radians)
        keep_uv_boundary: Preserve UV boundaries
        keep_sharp_edge: Preserve sharp edges
        keep_material_boundary: Preserve material boundaries
        topo_influence: Topology influence strength (0=off, 1=default, max 2)
    """
    mesh_name = dag_path.partialPathName()
    print(f"Processing mesh: {mesh_name}")
    print(f"Vertices: {mesh_fn.numVertices}")
    print(f"Edges: {mesh_fn.numEdges}")
    print(f"Polygons: {mesh_fn.numPolygons}")
    print(f"Topology Influence: {topo_influence:.1f}")

    # Count triangles
    tri_count = 0
    for i in range(mesh_fn.numPolygons):
        if mesh_fn.polygonVertexCount(i) == 3:
            tri_count += 1

    print(f"Triangular faces: {tri_count}")

    if tri_count == 0:
        print("No triangular faces to process")
        return

    # --- Phase 1: Pre-compute all topology data in one pass ---
    print("\nPre-computing mesh data...")
    _progress_step(status=f"{mesh_name}: Pre-computing mesh data...")
    data = build_mesh_data(
        mesh_fn, dag_path, keep_uv_boundary, keep_sharp_edge, keep_material_boundary
    )

    # --- Phase 2: Build priority queue (lazy-deletion heap) ---
    print("Building edge priority queue...")
    _progress_step(status=f"{mesh_name}: Building edge priority queue...")
    edge_queue = []
    edge_version = {}  # edge_id -> latest version
    edge_error = {}  # edge_id -> current error
    version_counter = [0]

    delimit_count = {
        "not_manifold": 0,
        "not_2_faces": 0,
        "material": 0,
        "sharp": 0,
        "uv": 0,
        "angle_face": 0,
        "quad_invalid": 0,
        "angle_shape": 0,
    }

    for edge_id in range(mesh_fn.numEdges):
        faces = data["edge_faces"].get(edge_id)
        if faces is None:
            continue

        fa, fb = faces
        if len(data["face_verts"][fa]) != 3 or len(data["face_verts"][fb]) != 3:
            continue

        if is_edge_delimit_fast(
            edge_id,
            data,
            angle_face_threshold,
            angle_shape_threshold,
            keep_uv_boundary,
            keep_sharp_edge,
            keep_material_boundary,
            delimit_count,
        ):
            continue

        quad_verts = get_quad_verts_fast(edge_id, data)
        if quad_verts is None:
            continue

        positions = [data["vert_pos"][v] for v in quad_verts]
        merge_error = quad_calc_error(
            positions[0], positions[1], positions[2], positions[3]
        )

        version_counter[0] += 1
        v = version_counter[0]
        edge_version[edge_id] = v
        edge_error[edge_id] = merge_error
        heappush(edge_queue, (merge_error, v, edge_id))

    print(f"Found {len(edge_version)} candidate edges for merging")
    print("Delimit reasons:")
    for reason, count in delimit_count.items():
        if count > 0:
            print(f"  - {reason}: {count}")

    if not edge_version:
        print("No edges to merge")
        return

    # --- Phase 2.5: Pre-existing quad influence (if TI enabled) ---
    if topo_influence > 0:
        for fid in range(mesh_fn.numPolygons):
            if len(data["face_verts"][fid]) != 4:
                continue
            fv = data["face_verts"][fid]
            fp = [data["vert_pos"][v] for v in fv]
            f_err = quad_calc_error(fp[0], fp[1], fp[2], fp[3])
            # Over-prioritize existing quads (same as Blender)
            f_err *= 2.0 - topo_influence * MAXIMUM_IMPROVEMENT
            f_vecs = compute_quad_edge_vecs(fp)
            # Find neighbor merge candidates around this quad
            for eid in data["face_to_edges"].get(fid, []):
                ef = data["edge_faces"].get(eid)
                if ef is None:
                    continue
                for nf in ef:
                    if nf == fid or len(data["face_verts"][nf]) != 3:
                        continue
                    for c_eid in data["face_to_edges"].get(nf, []):
                        if c_eid == eid or c_eid not in edge_error:
                            continue
                        curr = edge_error[c_eid]
                        if f_err > curr:
                            continue
                        c_qv = get_quad_verts_fast(c_eid, data)
                        if c_qv is None:
                            continue
                        c_pos = [data["vert_pos"][v] for v in c_qv]
                        al = compute_alignment(f_vecs, c_pos)
                        imp = f_err - curr
                        mult = min(topo_influence * al, MAXIMUM_IMPROVEMENT)
                        new_e = curr + imp * mult
                        if new_e < curr:
                            version_counter[0] += 1
                            vv = version_counter[0]
                            edge_version[c_eid] = vv
                            edge_error[c_eid] = new_e
                            heappush(edge_queue, (new_e, vv, c_eid))

    # --- Phase 3: Process queue with TI propagation + face conflict ---
    print("\nSelecting edges for merging...")
    _progress_step(status=f"{mesh_name}: Selecting best edges...")
    consumed_faces = set()
    edges_to_delete = []
    use_ti = topo_influence > 0
    ti_debug_stats = {}

    while edge_queue:
        err, ver, edge_id = heappop(edge_queue)

        # Lazy deletion: skip outdated entries
        if edge_version.get(edge_id) != ver:
            continue

        faces = data["edge_faces"].get(edge_id)
        if faces is None:
            continue

        fa, fb = faces
        if fa in consumed_faces or fb in consumed_faces:
            continue

        # Claim both faces
        consumed_faces.add(fa)
        consumed_faces.add(fb)
        edges_to_delete.append(edge_id)

        # Propagate topology influence to neighbors
        if use_ti:
            propagate_topology_influence(
                edge_id,
                data,
                topo_influence,
                consumed_faces,
                edge_version,
                edge_error,
                version_counter,
                edge_queue,
                err,  # pass the TI-adjusted queue error for cascade
                ti_debug_stats,
            )

    if use_ti:
        print("TI Debug Stats:")
        for k, v in ti_debug_stats.items():
            print(f"  {k}: {v}")

    print(f"Selected {len(edges_to_delete)} edges for batch deletion")

    # --- Phase 4: Batch delete all edges in one command ---
    _progress_step(status=f"{mesh_name}: Merging {len(edges_to_delete)} edges...")
    if edges_to_delete:
        print("Executing batch edge deletion...")
        edge_names = [f"{mesh_name}.e[{eid}]" for eid in edges_to_delete]
        cmds.polyDelEdge(*edge_names, cleanVertices=False)

    merge_count = len(edges_to_delete)
    print(f"Successfully merged {merge_count} edges into quads")

    # Final stats
    final_tri_count = 0
    final_quad_count = 0
    for i in range(cmds.polyEvaluate(mesh_name, face=True)):
        face_name = f"{mesh_name}.f[{i}]"
        if cmds.objExists(face_name):
            vert_info = cmds.polyInfo(face_name, faceToVertex=True)
            if vert_info:
                vert_count = len([int(x) for x in vert_info[0].split()[2:]])
                if vert_count == 3:
                    final_tri_count += 1
                elif vert_count == 4:
                    final_quad_count += 1

    print(f"\nFinal result:")
    print(f"  Triangles: {final_tri_count}")
    print(f"  Quads: {final_quad_count}")

    print("-" * 60)


# ============================================================================
# Run Entry Point (multiple object support + undo chunk)
# ============================================================================


def run(
    angle_face_threshold=math.radians(40),
    angle_shape_threshold=math.radians(40),
    keep_uv_boundary=True,
    keep_sharp_edge=True,
    keep_material_boundary=True,
    topo_influence=0.0,
):
    """
    Run Tris to Quads on all selected mesh objects.
    Non-mesh objects are silently skipped.
    The entire operation is wrapped in a single undo chunk.
    """
    print("=" * 60)
    print("Maya Triangles to Quads")
    print("=" * 60)

    meshes = get_selected_meshes()
    if not meshes:
        print("ERROR: No mesh objects selected")
        return

    print(f"Found {len(meshes)} mesh object(s) to process\n")

    # Progress bar: 4 steps per mesh (pre-compute, queue, select, delete)
    _progress_begin(
        total_steps=len(meshes) * 4,
        status="Triangles to Quads...",
    )
    cmds.undoInfo(openChunk=True, chunkName="Tris to Quads")
    try:
        for idx, (mesh_fn, dag_path) in enumerate(meshes):
            print(f"[{idx + 1}/{len(meshes)}] {dag_path.partialPathName()}")
            triangles_to_quads(
                mesh_fn,
                dag_path,
                angle_face_threshold,
                angle_shape_threshold,
                keep_uv_boundary,
                keep_sharp_edge,
                keep_material_boundary,
                topo_influence,
            )
    finally:
        cmds.undoInfo(closeChunk=True)
        _progress_end()

    print("=" * 60)
    print("All processing complete!")
    print("=" * 60)


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    run(
        angle_face_threshold=math.radians(40),
        angle_shape_threshold=math.radians(40),
        keep_uv_boundary=True,
        keep_sharp_edge=True,
        keep_material_boundary=True,
        topo_influence=1.0,
    )
