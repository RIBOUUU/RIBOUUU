"""Version haute qualite de la spirale, rendue avec Blender (Cycles).

Usage (avec le module bpy installe) :
  python3 blender_spirale.py <timeline.json> <dossier_sortie> [duree_s] [w] [h] [samples] [frame_unique]
Lit le calendrier des notes produit par build_audio.py et rend les images en PNG.
"""
import json, math, sys, os
import bpy
from mathutils import Vector

TLP = sys.argv[1]; OUT = sys.argv[2]
DUR = float(sys.argv[3]) if len(sys.argv) > 3 else 4.0
W = int(sys.argv[4]) if len(sys.argv) > 4 else 1080
H = int(sys.argv[5]) if len(sys.argv) > 5 else 1920
SAMPLES = int(sys.argv[6]) if len(sys.argv) > 6 else 64
ONLY = int(sys.argv[7]) if len(sys.argv) > 7 else None
FPS = 30

TL = json.load(open(TLP)); HITS = TL["hits"]
NB = min(len(HITS), 40)

# ---------------- trajectoire (meme principe que scene.html) ----------------
R, V, BR, G, SLOPE = 5.0, 5.5, 0.28, 39.0, 1.3
land = [(0.0, 0.0)]                 # (angle, hauteur du centre de la bille au contact)
hops = []
for i in range(NB):
    T = HITS[i]["dur"]
    dy = -SLOPE * T
    vy = (dy + G * T * T / 2) / T
    vmax = math.sqrt(2 * G * 2.2)
    g = G
    if vy > vmax:                     # note longue : la bille flotte au lieu de plonger
        lo, hi = 0.5, G
        for _ in range(40):
            gm = (lo + hi) / 2; v = (dy + gm * T * T / 2) / T
            if v > 0 and v * v / (2 * gm) > 2.2: hi = gm
            else: lo = gm
        g = lo; vy = (dy + g * T * T / 2) / T
    a0, z0 = land[-1]
    land.append((a0 - V * T / R, z0 + dy)); hops.append((T, g, vy))

def ball_pos(t):
    if t < HITS[0]["t"]:
        a, z = land[0]; d = HITS[0]["t"] - t
        return Vector((R * math.cos(a), R * math.sin(a), z + 9 * d * d + 2.4 * d))
    for i in range(NB):
        T, g, vy = hops[i]
        if t < HITS[i]["t"] + T or i == NB - 1:
            s = min(t - HITS[i]["t"], T); k = s / T
            a = land[i][0] + (land[i + 1][0] - land[i][0]) * k
            z = land[i][1] + vy * s - g * s * s / 2
            return Vector((R * math.cos(a), R * math.sin(a), z))

def smooth_ball(t, win=0.45, n=13):
    v = Vector((0, 0, 0))
    for k in range(n): v += ball_pos(t + (k / (n - 1) - 0.5) * 2 * win)
    return v / n

# ---------------- scene ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = SAMPLES; sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
sc.cycles.max_bounces = 4; sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.fps = FPS
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.45
sc.frame_start = 0; sc.frame_end = int(DUR * FPS) - 1
for vt, lk in (('AgX', 'AgX - Punchy'), ('AgX', 'Punchy'), ('Filmic', 'Medium High Contrast')):
    try:
        sc.view_settings.view_transform = vt
        try: sc.view_settings.look = lk
        except Exception: pass
        break
    except Exception: continue
sc.render.image_settings.file_format = 'PNG'

def mat(name, base=(0.02, 0.02, 0.022), rough=0.4, metal=0.0, emis=None, strength=0.0, coat=0.0, trans=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*base, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    for key in ("Coat Weight", "Clearcoat"):
        if key in p.inputs: p.inputs[key].default_value = coat; break
    for key in ("Transmission Weight", "Transmission"):
        if key in p.inputs: p.inputs[key].default_value = trans; break
    if emis is not None:
        p.inputs["Emission Color"].default_value = (*emis, 1)
        p.inputs["Emission Strength"].default_value = strength
    return m

# monde : degrade crepuscule (rose-orange a l'horizon, lavande en haut)
world = bpy.data.worlds.new("ciel"); sc.world = world; world.use_nodes = True
nt = world.node_tree; nt.nodes.clear()
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
ramp = nt.nodes.new("ShaderNodeValToRGB"); bg = nt.nodes.new("ShaderNodeBackground"); out = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs[0])
nt.links.new(ramp.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], out.inputs[0])
cr = ramp.color_ramp
cr.elements[0].position = 0.30; cr.elements[0].color = (0.22, 0.20, 0.36, 1)
cr.elements[1].position = 0.9; cr.elements[1].color = (0.78, 0.76, 0.92, 1)
e = cr.elements.new(0.50); e.color = (1.0, 0.62, 0.48, 1)
bg.inputs[1].default_value = 0.9

sun_d = bpy.data.lights.new("soleil", 'SUN'); sun_d.energy = 3.2; sun_d.color = (1.0, 0.78, 0.62); sun_d.angle = math.radians(4)
sun = bpy.data.objects.new("soleil", sun_d); sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), 0, math.radians(35))

# sol tres loin en dessous (ombres douces, profondeur)
bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, -14))
bpy.context.object.data.materials.append(mat("sol", base=(0.85, 0.72, 0.78), rough=0.9))

# ---------------- blocs ----------------
SEGS = {0: 'abcdef', 1: 'bc', 2: 'abged', 3: 'abgcd', 4: 'fgbc', 5: 'afgcd', 6: 'afgedc', 7: 'abc', 8: 'abcdefg', 9: 'abcfgd'}
m_body = mat("bloc", base=(0.018, 0.018, 0.02), rough=0.32, coat=0.6)
m_off = mat("segment_eteint", base=(0.06, 0.06, 0.065), rough=0.5)
m_wire = mat("fil", base=(0.3, 0.3, 0.32), rough=0.3, metal=1.0)
m_screw = mat("vis", base=(0.8, 0.8, 0.82), rough=0.25, metal=1.0)
YEL = (1.0, 0.42, 0.0)          # orange-jaune sature (AgX desature les tres fortes emissions)

def add_box(name, size, loc, parent, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bm = o.modifiers.new("biseau", 'BEVEL'); bm.width = bevel; bm.segments = 3
    o.data.materials.append(m); o.parent = parent
    return o

def seg_rects(d, cx, cz, w, h, t):
    m = {'a': (cx, cz + h / 2 - t / 2, w - 2 * t, t), 'd': (cx, cz - h / 2 + t / 2, w - 2 * t, t), 'g': (cx, cz, w - 2 * t, t),
         'f': (cx - w / 2 + t / 2, cz + h / 4, t, h / 2 - t * 1.4), 'b': (cx + w / 2 - t / 2, cz + h / 4, t, h / 2 - t * 1.4),
         'e': (cx - w / 2 + t / 2, cz - h / 4, t, h / 2 - t * 1.4), 'c': (cx + w / 2 - t / 2, cz - h / 4, t, h / 2 - t * 1.4)}
    return [(k, m[k]) for k in 'abcdefg']

BL, BH = 2.5, 0.85
for i in range(NB):
    a, zc = land[i]
    gap = min(land[i - 1][0] - a if i else 9, a - land[i + 1][0]) * (R - 0.9)
    w = min(0.9, abs(gap) * 0.8)
    root = bpy.data.objects.new(f"bloc_{i}", None); sc.collection.objects.link(root)
    rr = R + 0.35
    root.location = (rr * math.cos(a), rr * math.sin(a), zc - BR - BH / 2); root.rotation_euler = (0, 0, a)
    add_box(f"corps_{i}", (BL, w, BH), (0, 0, 0), root, m_body, bevel=0.04)
    for sx in (-0.85, 0.75):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.03, location=(sx, 0, BH / 2 + 0.01)); s = bpy.context.object
        s.data.materials.append(m_screw); s.parent = root
    # chiffre 7 segments + cadre neon sur la face exterieure (x = +BL/2)
    lit = mat(f"neon_{i}", base=(0.05, 0.04, 0.0), rough=0.4, emis=YEL, strength=0.0)
    d = (i + 1) % 10; fx = BL / 2 + 0.012
    for k, (cy, cz, sw, sh) in seg_rects(d, 0, 0, w * 0.42, BH * 0.62, 0.065):
        add_box(f"seg_{i}_{k}", (0.02, sw, sh), (fx, cy, cz), root, lit if k in SEGS[d] else m_off)
    for (cy, cz, sw, sh) in ((0, BH / 2 - 0.035, w * 0.92, 0.035), (0, -BH / 2 + 0.035, w * 0.92, 0.035),
                             (w * 0.46 - 0.0175, 0, 0.035, BH * 0.92), (-w * 0.46 + 0.0175, 0, 0.035, BH * 0.92)):
        add_box(f"cadre_{i}", (0.02, sw, sh), (fx, cy, cz), root, lit)
    if i % 3 == 0:
        bpy.ops.mesh.primitive_cylinder_add(radius=0.01, depth=30, location=(BL / 2 - 0.15, 0, BH / 2 + 15)); wi = bpy.context.object
        wi.data.materials.append(m_wire); wi.parent = root
    # allumage a l'impact : flash puis extinction douce
    p = lit.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"]
    th = HITS[i]["t"]
    for tt, val in ((th - 0.001, 0.0), (th, 0.0), (th + 0.03, 9.0), (th + 0.35, 4.0), (th + 1.2, 1.0), (th + 2.5, 0.3)):
        p.default_value = val; p.keyframe_insert("default_value", frame=tt * FPS)
    # petite secousse a l'impact
    z0 = root.location.z
    for tt, dz in ((th - 0.001, 0), (th + 0.04, -0.06), (th + 0.12, 0.015), (th + 0.25, 0)):
        root.location.z = z0 + dz; root.keyframe_insert("location", index=2, frame=tt * FPS)

# ---------------- bille ----------------
bpy.ops.mesh.primitive_uv_sphere_add(radius=BR, segments=64, ring_count=32)
ball = bpy.context.object; bpy.ops.object.shade_smooth()
mb = bpy.data.materials.new("bille"); mb.use_nodes = True; n = mb.node_tree
pb = n.nodes.get("Principled BSDF")
noise = n.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 3.5
cramp = n.nodes.new("ShaderNodeValToRGB")
cramp.color_ramp.elements[0].color = (0.0, 0.35, 0.45, 1); cramp.color_ramp.elements[1].color = (0.1, 1.0, 0.75, 1)
n.links.new(noise.outputs["Fac"], cramp.inputs[0])
n.links.new(cramp.outputs[0], pb.inputs["Base Color"]); n.links.new(cramp.outputs[0], pb.inputs["Emission Color"])
pb.inputs["Emission Strength"].default_value = 7.0; pb.inputs["Roughness"].default_value = 0.15
for key in ("Coat Weight", "Clearcoat"):
    if key in pb.inputs: pb.inputs[key].default_value = 1.0; break
ball.data.materials.append(mb)
bl = bpy.data.lights.new("lumiere_bille", 'POINT'); bl.energy = 120; bl.color = (0.1, 1.0, 0.75); bl.shadow_soft_size = 0.3
blo = bpy.data.objects.new("lumiere_bille", bl); sc.collection.objects.link(blo); blo.parent = ball

# ---------------- camera ----------------
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 38; cam_d.sensor_fit = 'VERTICAL'; cam_d.sensor_height = 36
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.2; cam_d.dof.focus_object = ball
cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
tgt = bpy.data.objects.new("cible", None); sc.collection.objects.link(tgt)
con = cam.constraints.new('TRACK_TO'); con.target = tgt; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'

for f in range(sc.frame_start - 2, sc.frame_end + 3):
    t = f / FPS
    p = ball_pos(t); ball.location = p; ball.rotation_euler = (t * 2.1, -t * 3.3, 0)
    ball.keyframe_insert("location", frame=f); ball.keyframe_insert("rotation_euler", frame=f)
    sb = smooth_ball(t); lk = smooth_ball(t + 0.25, 0.35, 9)
    a = math.atan2(sb.y, sb.x); phi = a + 0.62 + 0.12 * math.sin(t * 0.35)
    rc, hc = 12.0 + 0.6 * math.sin(t * 0.42), 5.6 + 0.6 * math.sin(t * 0.31 + 1.2)
    cam.location = (rc * math.cos(phi), rc * math.sin(phi), sb.z + hc); cam.keyframe_insert("location", frame=f)
    tgt.location = (lk.x * 0.85, lk.y * 0.85, lk.z - 1.0); tgt.keyframe_insert("location", frame=f)
for obj in (ball, cam, tgt):
    if obj.animation_data and obj.animation_data.action:
        try:
            for fc in obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'
        except Exception: pass

# pas de compositing Blender (il demande une carte graphique) : le halo (bloom) est ajoute apres coup
sc.render.use_compositing = False
sc.render.use_sequencer = False

os.makedirs(OUT, exist_ok=True)
frames = [ONLY] if ONLY is not None else range(sc.frame_start, sc.frame_end + 1)
import time
for f in frames:
    t0 = time.time()
    sc.frame_set(f); sc.render.filepath = os.path.join(OUT, f"{f:04d}.png")
    bpy.ops.render.render(write_still=True)
    print(f"image {f} : {time.time() - t0:.1f}s", flush=True)
