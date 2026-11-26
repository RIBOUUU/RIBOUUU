"""Spirale EPIQUE (Blender Cycles) : blocs qui rebondissent fort, entonnoirs-tourbillons qui aspirent
la bille puis la recrachent par un tube en verre, musique de plus en plus epique (epique_audio.py).

Usage : python blender_epique.py <timeline_epique.json> <dossier_sortie> [w] [h] [samples] [debut-fin | liste,d,images]
"""
import json, math, sys, os, time
import bpy
from mathutils import Vector

TLP, OUT = sys.argv[1], sys.argv[2]
W = int(sys.argv[3]) if len(sys.argv) > 3 else 720
H = int(sys.argv[4]) if len(sys.argv) > 4 else 1280
SAMPLES = int(sys.argv[5]) if len(sys.argv) > 5 else 20
SEL = sys.argv[6] if len(sys.argv) > 6 else None
FPS = 30

TL = json.load(open(TLP)); HITS = TL["hits"]; TUN = TL["tunnels"]; END = TL["end"]
NF = int(math.ceil(END * FPS - 1e-6))

R, V, BR, G, SLOPE = 5.0, 5.5, 0.28, 39.0, 1.3
RF, R0, HF, TUBE = 1.5, 0.30, 1.7, 3.4          # entonnoir : rayon, trou, profondeur ; longueur du tube
NEON = [(1.0, 0.42, 0.0), (1.0, 0.10, 0.02), (1.0, 0.04, 0.40)]     # chiffres : jaune, rouge, magenta
BALLC = [(0.1, 1.0, 0.75), (0.55, 0.35, 1.0), (1.0, 0.72, 0.08)]    # bille : cyan, violet, or

def P(a, r, z): return Vector((r * math.cos(a), r * math.sin(a), z))
def sstep(e0, e1, x):
    u = min(1.0, max(0.0, (x - e0) / (e1 - e0))); return u * u * (3 - 2 * u)

def hop_params(z0, z1, T):
    dy = z1 - z0; g = G; vy = (dy + g * T * T / 2) / T
    if vy > 0 and vy * vy / (2 * g) > 2.2:          # note longue : la bille flotte
        lo, hi = 0.5, G
        for _ in range(40):
            gm = (lo + hi) / 2; v = (dy + gm * T * T / 2) / T
            if v > 0 and v * v / (2 * gm) > 2.2: hi = gm
            else: lo = gm
        g = lo; vy = (dy + g * T * T / 2) / T
    return g, vy

# ---------------- trajectoire ----------------
SEGS, BLOCKS, FUN = [], [], []
a, r, z = 0.0, R, 0.0
for i, h in enumerate(HITS):
    t0, T, s = h["t"], h["dur"], h["sec"]
    kind = "sortie" if i > 0 and HITS[i - 1]["sec"] != s else "normal"
    BLOCKS.append(dict(a=a, r=r, z=z, t=t0, sec=s, kind=kind, i=i))
    last_sec = i < len(HITS) - 1 and HITS[i + 1]["sec"] != s
    if last_sec:
        tn = TUN[s]
        ac = a - V * T / R; zr = z - SLOPE * T * 0.6
        g, vy = hop_params(z, zr, T)
        SEGS.append(("hop", t0, t0 + T, (a, r, z, ac, R, zr, g, vy, T)))
        C = P(ac, R + RF, 0)
        top = zr - BR; k = HF / (RF / R0 - 1)
        F = tn["drop"] - tn["rim"]; D = tn["exit"] - tn["drop"]
        arr = []; th = ac + math.pi; n = 900
        for q in range(n + 1):
            u = q / n; rr = RF * (R0 / RF) ** (u ** 2)
            arr.append((th, rr)); th += V * (1 + 1.8 * u) / rr * F / n
        w_end = V * 2.8 / R0
        z_hole = top - HF + BR
        z_e = z_hole - TUBE - 1.1
        v0 = 1.5; A = 2 * (z_hole - z_e - v0 * D) / (D * D)
        fn = dict(C=C, ac=ac, zr=zr, top=top, k=k, arr=arr, F=F, D=D, rim=tn["rim"], drop=tn["drop"],
                  exit=tn["exit"], z_hole=z_hole, z_e=z_e, v0=v0, A=A, w_end=w_end, sec=s)
        FUN.append(fn)
        SEGS.append(("funnel", tn["rim"], tn["drop"], fn)); SEGS.append(("drop", tn["drop"], tn["exit"], fn))
        a, r, z = ac, R + RF, z_e
    else:
        na = a - V * T / R; nz = z - SLOPE * T
        if i == len(HITS) - 1: na, nz = a, z       # final : grand saut sur place
        g, vy = hop_params(z, nz, T)
        SEGS.append(("hop", t0, t0 + T, (a, r, z, na, R, nz, g, vy, T)))
        a, r, z = na, R, nz

def funnel_state(fn, t):
    u = min(1.0, max(0.0, (t - fn["rim"]) / fn["F"])) * (len(fn["arr"]) - 1)
    q = min(int(u), len(fn["arr"]) - 2); f = u - q
    th = fn["arr"][q][0] * (1 - f) + fn["arr"][q + 1][0] * f
    rr = fn["arr"][q][1] * (1 - f) + fn["arr"][q + 1][1] * f
    return th, rr

def ball_pos(t):
    if t < HITS[0]["t"]:
        d = HITS[0]["t"] - t
        return P(0, R, 9 * d * d + 2.4 * d)
    for kind, t0, t1, p in SEGS:
        if t < t1 or (kind, t0, t1, p) == SEGS[-1]:
            if kind == "hop":
                a0, r0, z0, a1, r1, z1, g, vy, T = p
                s = t - t0; kk = s / T
                return P(a0 + (a1 - a0) * kk, r0 + (r1 - r0) * kk, z0 + vy * s - g * s * s / 2)
            fn = p
            if kind == "funnel":
                th, rr = funnel_state(fn, t)
                zz = fn["top"] - fn["k"] * (RF / rr - 1) + BR * 1.15
                return fn["C"] + Vector((rr * math.cos(th), rr * math.sin(th), zz))
            s = t - fn["drop"]; u = s / fn["D"]
            th = fn["arr"][-1][0] + fn["w_end"] * s * (1 - 0.5 * min(u, 1))
            rr = R0 * max(0.0, 1 - u / 0.3)
            zz = fn["z_hole"] - fn["v0"] * s - fn["A"] * s * s / 2
            return fn["C"] + Vector((rr * math.cos(th), rr * math.sin(th), zz))

def smooth_ball(t, win=0.45, n=13):
    v = Vector((0, 0, 0))
    for k in range(n): v += ball_pos(t + (k / (n - 1) - 0.5) * 2 * win)
    return v / n

def sec_at(t):
    return sum(1 for fn in FUN if t >= fn["exit"])

# ---------------- scene ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = SAMPLES; sc.cycles.use_adaptive_sampling = True
sc.cycles.use_denoising = True
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
sc.cycles.max_bounces = 4; sc.cycles.transparent_max_bounces = 10
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.fps = FPS
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.45
sc.frame_start = 0; sc.frame_end = NF - 1
for vt, lk in (('AgX', 'AgX - Punchy'), ('AgX', 'Punchy'), ('Filmic', 'Medium High Contrast')):
    try:
        sc.view_settings.view_transform = vt
        try: sc.view_settings.look = lk
        except Exception: pass
        break
    except Exception: continue
sc.render.image_settings.file_format = 'PNG'

def mat(name, base=(0.02, 0.02, 0.022), rough=0.4, metal=0.0, emis=None, strength=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*base, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    for key in ("Coat Weight", "Clearcoat"):
        if key in p.inputs: p.inputs[key].default_value = coat; break
    if emis is not None:
        p.inputs["Emission Color"].default_value = (*emis, 1)
        p.inputs["Emission Strength"].default_value = strength
    return m

def key_series(sock, fnc, f0, f1):
    """pose une cle par image (f0..f1) sur une entree de noeud"""
    for f in range(max(f0, -2), min(f1, NF + 2) + 1):
        sock.default_value = fnc(f / FPS); sock.keyframe_insert("default_value", frame=f)

# ciel : crepuscule plus sombre et plus contraste
world = bpy.data.worlds.new("ciel"); sc.world = world; world.use_nodes = True
nt = world.node_tree; nt.nodes.clear()
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
ramp = nt.nodes.new("ShaderNodeValToRGB"); bg = nt.nodes.new("ShaderNodeBackground"); out = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs[0])
nt.links.new(ramp.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], out.inputs[0])
cr = ramp.color_ramp
cr.elements[0].position = 0.25; cr.elements[0].color = (0.035, 0.03, 0.09, 1)
cr.elements[1].position = 0.92; cr.elements[1].color = (0.10, 0.07, 0.22, 1)
e = cr.elements.new(0.50); e.color = (0.95, 0.38, 0.22, 1)
e = cr.elements.new(0.62); e.color = (0.38, 0.16, 0.34, 1)
bg.inputs[1].default_value = 0.85

sun_d = bpy.data.lights.new("soleil", 'SUN'); sun_d.energy = 2.6; sun_d.color = (1.0, 0.72, 0.55); sun_d.angle = math.radians(4)
sun = bpy.data.objects.new("soleil", sun_d); sc.collection.objects.link(sun)
sun.rotation_euler = (math.radians(55), 0, math.radians(35))

# ---------------- blocs ----------------
SEG7 = {0: 'abcdef', 1: 'bc', 2: 'abged', 3: 'abgcd', 4: 'fgbc', 5: 'afgcd', 6: 'afgedc', 7: 'abc', 8: 'abcdefg', 9: 'abcfgd'}
m_body = mat("bloc", base=(0.018, 0.018, 0.02), rough=0.3, coat=0.7)
m_off = mat("segment_eteint", base=(0.06, 0.06, 0.065), rough=0.5)
m_wire = mat("fil", base=(0.3, 0.3, 0.32), rough=0.3, metal=1.0)
m_screw = mat("vis", base=(0.8, 0.8, 0.82), rough=0.25, metal=1.0)

def add_box(name, size, loc, parent, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bm = o.modifiers.new("biseau", 'BEVEL'); bm.width = bevel; bm.segments = 3
    o.data.materials.append(m); o.parent = parent
    return o

def seg_rects(cx, cz, w, h, t):
    m = {'a': (cx, cz + h / 2 - t / 2, w - 2 * t, t), 'd': (cx, cz - h / 2 + t / 2, w - 2 * t, t), 'g': (cx, cz, w - 2 * t, t),
         'f': (cx - w / 2 + t / 2, cz + h / 4, t, h / 2 - t * 1.4), 'b': (cx + w / 2 - t / 2, cz + h / 4, t, h / 2 - t * 1.4),
         'e': (cx - w / 2 + t / 2, cz - h / 4, t, h / 2 - t * 1.4), 'c': (cx + w / 2 - t / 2, cz - h / 4, t, h / 2 - t * 1.4)}
    return [(k, m[k]) for k in 'abcdefg']

BOOMS = [fn["exit"] for fn in FUN] + [HITS[-1]["t"]]
AMP = [0.45, 0.55, 0.65]

def bounce_fn(b):
    imps = [(b["t"], 1.0 if b["kind"] == "sortie" else AMP[b["sec"]])]
    for h in HITS:                                   # chaque nouvelle note refait vibrer les blocs voisins
        if h["sec"] == b["sec"] and b["t"] < h["t"] <= b["t"] + 1.6:
            imps.append((h["t"], 0.16 * imps[0][1]))
    for tb in BOOMS:
        if tb > b["t"] + 0.01: imps.append((tb, 0.35))
    def dz(t):
        v = 0.0
        for ti, am in imps:
            s = t - ti
            if s > 0: v -= am * math.exp(-3.2 * s) * math.sin(2 * math.pi * 2.4 * s)
        return v
    return dz

BL, BH = 2.5, 0.85
for b in BLOCKS:
    i = b["i"]; s = b["sec"]
    if b["kind"] == "sortie":
        w = 1.4; bl = 2.6; rr = b["r"]
    else:
        nb = [o for o in BLOCKS if abs(o["i"] - i) == 1 and o["kind"] == "normal" and o["sec"] == s]
        dmin = min([(P(o["a"], o["r"], 0) - P(b["a"], b["r"], 0)).length for o in nb] + [9])
        w = min(0.9, dmin * 0.75); bl = BL; rr = b["r"] + 0.35
    root = bpy.data.objects.new(f"bloc_{i}", None); sc.collection.objects.link(root)
    root.location = (rr * math.cos(b["a"]), rr * math.sin(b["a"]), b["z"] - BR - BH / 2); root.rotation_euler = (0, 0, b["a"])
    add_box(f"corps_{i}", (bl, w, BH), (0, 0, 0), root, m_body, bevel=0.04)
    for sx in (-0.85, 0.75):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.03, location=(sx, 0, BH / 2 + 0.01)); sw = bpy.context.object
        sw.data.materials.append(m_screw); sw.parent = root
    lit = mat(f"neon_{i}", base=(0.05, 0.04, 0.0), rough=0.4, emis=NEON[s], strength=0.0)
    d = (i + 1) % 10; fx = bl / 2 + 0.012
    for k, (cy, cz, sw_, sh) in seg_rects(0, 0, min(w, 0.9) * 0.42, BH * 0.62, 0.065):
        add_box(f"seg_{i}_{k}", (0.02, sw_, sh), (fx, cy, cz), root, lit if k in SEG7[d] else m_off)
    for (cy, cz, sw_, sh) in ((0, BH / 2 - 0.035, w * 0.92, 0.035), (0, -BH / 2 + 0.035, w * 0.92, 0.035),
                              (w * 0.46 - 0.0175, 0, 0.035, BH * 0.92), (-w * 0.46 + 0.0175, 0, 0.035, BH * 0.92)):
        add_box(f"cadre_{i}", (0.02, sw_, sh), (fx, cy, cz), root, lit)
    if b["kind"] == "sortie":   # bord lumineux sur le dessus du bloc d'arrivee
        for sy in (-1, 1):
            add_box(f"liseré_{i}", (bl * 0.96, 0.04, 0.03), (0, sy * (w / 2 - 0.05), BH / 2 + 0.005), root, lit)
    # fil de suspension, sauf s'il traverserait un entonnoir ou un tube
    wx = root.matrix_world @ Vector((bl / 2 - 0.15, 0, 0)) if False else P(b["a"], rr + bl / 2 - 0.15, 0)
    clash = any((Vector((wx.x, wx.y, 0)) - Vector((fn["C"].x, fn["C"].y, 0))).length < RF + 0.6 and fn["top"] > b["z"] for fn in FUN)
    if i % 3 == 0 and not clash and b["kind"] == "normal":
        bpy.ops.mesh.primitive_cylinder_add(radius=0.01, depth=30, location=(bl / 2 - 0.15, 0, BH / 2 + 15)); wi = bpy.context.object
        wi.data.materials.append(m_wire); wi.parent = root
    # neon : flash a l'impact, puis re-flash a chaque BOUM
    th = b["t"]; booms = [tb for tb in BOOMS if tb > th + 0.01]
    def neon(t, th=th, booms=booms):
        if t < th: return 0.0
        v = 0.35 + 8.6 * math.exp(-(t - th) / 0.35)
        for tb in booms:
            if t >= tb: v += 6.0 * math.exp(-(t - tb) / 0.45)
        return v
    key_series(lit.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"], neon, int(th * FPS) - 1, NF + 1)
    # rebond (fort) : enfoncement, sursaut, oscillation amortie + bascule
    dz = bounce_fn(b); z0 = root.location.z
    for f in range(int(th * FPS) - 1, NF + 2):
        t = f / FPS
        root.location.z = z0 + dz(t); root.keyframe_insert("location", index=2, frame=f)
        root.rotation_euler.x = 0.35 * dz(t - 0.06); root.keyframe_insert("rotation_euler", index=0, frame=f)

# ---------------- entonnoirs + tubes ----------------
def funnel_mesh(name, k):
    rings = []; nr, na = 56, 128
    for q in range(nr + 1):
        u = q / nr; rr = (RF + 0.35) * (R0 / (RF + 0.35)) ** u
        zz = 0.0 if rr >= RF else -k * (RF / rr - 1)
        rings.append((rr, zz))
    verts, faces = [], []
    for rr, zz in rings:
        for j in range(na):
            ph = 2 * math.pi * j / na; verts.append((rr * math.cos(ph), rr * math.sin(ph), zz))
    for q in range(nr):
        for j in range(na):
            a0 = q * na + j; a1 = q * na + (j + 1) % na
            faces.append((a0, a1, a1 + na, a0 + na))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); sc.collection.objects.link(o)
    for p in me.polygons: p.use_smooth = True
    so = o.modifiers.new("epaisseur", 'SOLIDIFY'); so.thickness = 0.05
    return o

def funnel_material(name, col):
    m = mat(name, base=(0.015, 0.015, 0.02), rough=0.22, coat=0.8, emis=col, strength=0.0)
    n = m.node_tree; L = n.links; pb = n.nodes.get("Principled BSDF")
    tco = n.nodes.new("ShaderNodeTexCoord"); sp = n.nodes.new("ShaderNodeSeparateXYZ")
    L.new(tco.outputs["Object"], sp.inputs[0])
    def M(op, a, b=None, c=None):
        nd = n.nodes.new("ShaderNodeMath"); nd.operation = op
        for idx, v in enumerate((a, b, c)):
            if v is None: continue
            if isinstance(v, (int, float)): nd.inputs[idx].default_value = v
            else: L.new(v, nd.inputs[idx])
        return nd.outputs[0]
    ang = M('ARCTAN2', sp.outputs["Y"], sp.outputs["X"])
    rad = M('SQRT', M('ADD', M('MULTIPLY', sp.outputs["X"], sp.outputs["X"]), M('MULTIPLY', sp.outputs["Y"], sp.outputs["Y"])))
    phase = n.nodes.new("ShaderNodeValue"); glow = n.nodes.new("ShaderNodeValue")
    arg = M('MULTIPLY_ADD', M('LOGARITHM', M('MAXIMUM', rad, 0.05), 2.71828), 7.0, M('MULTIPLY_ADD', ang, 4.0, phase.outputs[0]))
    mr = n.nodes.new("ShaderNodeMapRange"); mr.clamp = True
    L.new(M('SINE', arg), mr.inputs["Value"]); mr.inputs["From Min"].default_value = 0.55; mr.inputs["From Max"].default_value = 1.0
    L.new(M('MULTIPLY', mr.outputs["Result"], glow.outputs[0]), pb.inputs["Emission Strength"])
    return m, phase.outputs[0], glow.outputs[0]

m_glass = bpy.data.materials.new("verre"); m_glass.use_nodes = True
gn = m_glass.node_tree; gn.nodes.clear()
o_ = gn.nodes.new("ShaderNodeOutputMaterial"); mix = gn.nodes.new("ShaderNodeMixShader")
tr_ = gn.nodes.new("ShaderNodeBsdfTransparent"); gl = gn.nodes.new("ShaderNodeBsdfPrincipled")
gl.inputs["Base Color"].default_value = (0.9, 0.95, 1.0, 1); gl.inputs["Roughness"].default_value = 0.04
lw = gn.nodes.new("ShaderNodeLayerWeight"); lw.inputs["Blend"].default_value = 0.25
mm = gn.nodes.new("ShaderNodeMath"); mm.operation = 'MULTIPLY_ADD'; mm.inputs[1].default_value = 0.9; mm.inputs[2].default_value = 0.08
mm.use_clamp = True
gn.links.new(lw.outputs["Facing"], mm.inputs[0]); gn.links.new(mm.outputs[0], mix.inputs[0])
gn.links.new(tr_.outputs[0], mix.inputs[1]); gn.links.new(gl.outputs[0], mix.inputs[2]); gn.links.new(mix.outputs[0], o_.inputs[0])

for q, fn in enumerate(FUN):
    col = NEON[fn["sec"] + 1]
    fo = funnel_mesh(f"entonnoir_{q}", fn["k"]); fo.location = (fn["C"].x, fn["C"].y, fn["top"])
    fm, ph_s, gl_s = funnel_material(f"tourbillon_{q}", col); fo.data.materials.append(fm)
    rim, drop, ex = fn["rim"], fn["drop"], fn["exit"]
    def phase(t, fn=fn):
        th, _ = funnel_state(fn, t)
        return -(1.2 * t) * 4 - 0.5 * 4 * (th - fn["arr"][0][0])
    def glow(t, rim=rim, drop=drop, ex=ex):
        v = 1.2 + 7.0 * sstep(rim - 0.3, drop, t) ** 2
        if t > drop: v = 1.2 + 14.0 * math.exp(-(t - drop) / 0.35)
        return v
    key_series(ph_s, phase, 0, NF + 1); key_series(gl_s, glow, 0, NF + 1)
    # anneau lumineux autour de l'entonnoir
    bpy.ops.mesh.primitive_torus_add(major_radius=RF + 0.35, minor_radius=0.05, location=(fn["C"].x, fn["C"].y, fn["top"]))
    ring = bpy.context.object; rm = mat(f"anneau_{q}", base=(0.05, 0.05, 0.05), emis=col, strength=3.0); ring.data.materials.append(rm)
    key_series(rm.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"], glow, 0, NF + 1)
    # tube en verre sous le trou
    z_top = fn["top"] - HF; z_bot = fn["z_e"] + 0.85
    bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=z_top - z_bot, vertices=64, end_fill_type='NOTHING',
                                        location=(fn["C"].x, fn["C"].y, (z_top + z_bot) / 2))
    tb = bpy.context.object; tb.data.materials.append(m_glass); bpy.ops.object.shade_smooth()
    # anneaux du tube : s'allument quand la bille passe
    zz = z_top - 0.3
    while zz > z_bot + 0.1:
        bpy.ops.mesh.primitive_torus_add(major_radius=0.45, minor_radius=0.035, location=(fn["C"].x, fn["C"].y, zz))
        tr_o = bpy.context.object; tm = mat(f"anneau_tube_{q}_{zz:.2f}", base=(0.05, 0.05, 0.05), emis=col, strength=0.5)
        tr_o.data.materials.append(tm)
        # instant du passage : z(s) = z_hole - v0 s - A s^2 / 2
        dzz = fn["z_hole"] - zz; s_ = (-fn["v0"] + math.sqrt(fn["v0"] ** 2 + 2 * fn["A"] * max(dzz, 0))) / fn["A"]
        tp = fn["drop"] + s_
        key_series(tm.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"],
                   lambda t, tp=tp: 0.6 + 25 * math.exp(-max(0, t - tp) / 0.25) * (t >= tp - 0.02), int((tp - 0.3) * FPS), NF + 1)
        zz -= 0.55

# ---------------- poussieres lumineuses (bokeh) ----------------
import random
rnd = random.Random(5)
zmin = min(b["z"] for b in BLOCKS) - 6
for q in range(170):
    rr = rnd.uniform(2.5, 16); aa = rnd.uniform(0, 2 * math.pi); zz = rnd.uniform(zmin, 8)
    if abs(rr - R) < 1.2 or any((Vector((rr * math.cos(aa), rr * math.sin(aa))) - fn["C"].xy).length < RF + 0.6 for fn in FUN):
        continue
    bpy.ops.mesh.primitive_ico_sphere_add(radius=rnd.uniform(0.025, 0.06), subdivisions=1, location=(rr * math.cos(aa), rr * math.sin(aa), zz))
    o = bpy.context.object
    c = rnd.choice([(1.0, 0.55, 0.25), (1.0, 0.35, 0.6), (0.5, 0.7, 1.0)])
    o.data.materials.append(mat(f"poussiere_{q}", base=(0, 0, 0), emis=c, strength=rnd.uniform(4, 12)))

# ---------------- bille ----------------
bpy.ops.mesh.primitive_uv_sphere_add(radius=BR, segments=64, ring_count=32)
ball = bpy.context.object; bpy.ops.object.shade_smooth()
mb = bpy.data.materials.new("bille"); mb.use_nodes = True; n = mb.node_tree
pb = n.nodes.get("Principled BSDF")
noise = n.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 3.5
cramp = n.nodes.new("ShaderNodeValToRGB")
cramp.color_ramp.elements[0].color = (0.35, 0.35, 0.35, 1); cramp.color_ramp.elements[1].color = (1, 1, 1, 1)
rgb = n.nodes.new("ShaderNodeRGB")
vm = n.nodes.new("ShaderNodeVectorMath"); vm.operation = 'MULTIPLY'
n.links.new(noise.outputs["Fac"], cramp.inputs[0]); n.links.new(cramp.outputs[0], vm.inputs[0]); n.links.new(rgb.outputs[0], vm.inputs[1])
n.links.new(vm.outputs[0], pb.inputs["Base Color"]); n.links.new(vm.outputs[0], pb.inputs["Emission Color"])
pb.inputs["Emission Strength"].default_value = 7.0; pb.inputs["Roughness"].default_value = 0.15
for key in ("Coat Weight", "Clearcoat"):
    if key in pb.inputs: pb.inputs[key].default_value = 1.0; break
ball.data.materials.append(mb)
bl_d = bpy.data.lights.new("lumiere_bille", 'POINT'); bl_d.energy = 120; bl_d.shadow_soft_size = 0.3
blo = bpy.data.objects.new("lumiere_bille", bl_d); sc.collection.objects.link(blo); blo.parent = ball

def ball_col(t):
    c = list(BALLC[0])
    for q, fn in enumerate(FUN):          # la couleur change pendant la chute dans le tube
        u = sstep(fn["drop"], fn["exit"], t)
        c = [c[j] * (1 - u) + BALLC[q + 1][j] * u for j in range(3)]
    return c

for f in range(-2, NF + 3):
    t = f / FPS; c = ball_col(t)
    rgb.outputs[0].default_value = (*c, 1); rgb.outputs[0].keyframe_insert("default_value", frame=f)
    bl_d.color = c; bl_d.keyframe_insert("color", frame=f)
    boost = sum(sstep(fn["rim"], fn["drop"], t) * (1 - sstep(fn["exit"], fn["exit"] + 0.6, t)) for fn in FUN)
    bl_d.energy = 120 + 160 * boost; bl_d.keyframe_insert("energy", frame=f)

# ---------------- camera ----------------
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 36; cam_d.sensor_fit = 'VERTICAL'; cam_d.sensor_height = 36
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.4; cam_d.dof.focus_object = ball
cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
tgt = bpy.data.objects.new("cible", None); sc.collection.objects.link(tgt)
con = cam.constraints.new('TRACK_TO'); con.target = tgt; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'

def rig(t):
    e = sec_at(t)
    sb = smooth_ball(t); lk = smooth_ball(t + 0.25, 0.35, 9)
    a_ = math.atan2(sb.y, sb.x)
    phi = a_ + 0.62 + 0.12 * math.sin(t * 0.35) + 0.18 * e * math.sin(t * 0.9)
    rc = 12.0 - 1.3 * e + 0.6 * math.sin(t * 0.42); hc = 5.6 - 0.5 * e + 0.6 * math.sin(t * 0.31 + 1.2)
    pos = Vector((rc * math.cos(phi), rc * math.sin(phi), sb.z + hc))
    tg = Vector((lk.x * 0.85, lk.y * 0.85, lk.z - 1.0))
    for fn in FUN:
        wf = sstep(fn["rim"] - 0.45, fn["rim"] + 0.2, t) * (1 - sstep(fn["drop"] - 0.12, fn["drop"] + 0.12, t))
        wd = sstep(fn["drop"] - 0.12, fn["drop"] + 0.12, t) * (1 - sstep(fn["exit"] + 0.1, fn["exit"] + 0.7, t))
        if wf > 0:      # vue plongeante dans le tourbillon, qui tourne doucement autour
            u = (t - fn["rim"]) / fn["F"]; psi = fn["ac"] + 0.35 + 0.6 * u
            fp = Vector((fn["C"].x + 3.3 * math.cos(psi), fn["C"].y + 3.3 * math.sin(psi), fn["top"] + 6.3 - 1.2 * u))
            ft = Vector((fn["C"].x, fn["C"].y, fn["top"] - 0.9))
            pos = pos.lerp(fp, wf); tg = tg.lerp(ft, wf)
        if wd > 0:      # on suit la bille qui descend dans le tube en verre
            bp = ball_pos(min(t, fn["exit"]))
            psi = fn["ac"] + 0.75
            dp = Vector((fn["C"].x + 5.2 * math.cos(psi), fn["C"].y + 5.2 * math.sin(psi), bp.z + 1.0))
            dt_ = Vector((fn["C"].x, fn["C"].y, bp.z - 0.6))
            pos = pos.lerp(dp, wd); tg = tg.lerp(dt_, wd)
    tf = HITS[-1]["t"]; wz = sstep(tf - 0.1, tf + 1.3, t)
    if wz > 0:          # final : on recule pour reveler toute la structure
        bp = ball_pos(t); ab = math.atan2(bp.y, bp.x) + 0.95
        wp = Vector((19 * math.cos(ab), 19 * math.sin(ab), bp.z + 8.5))
        wt = Vector((bp.x * 0.3, bp.y * 0.3, bp.z - 5.0))
        pos = pos.lerp(wp, wz); tg = tg.lerp(wt, wz)
    for tb in BOOMS:   # secousse a chaque BOUM
        s = t - tb
        if 0 < s < 0.8:
            k = 0.22 * math.exp(-6 * s)
            pos += Vector((math.sin(53 * s), math.cos(47 * s), math.sin(61 * s))) * k
    return pos, tg

for f in range(-2, NF + 3):
    t = f / FPS; ps, ts = Vector((0, 0, 0)), Vector((0, 0, 0))
    for q in range(7):
        p_, t_ = rig(t + (q / 6 - 0.5) * 0.2); ps += p_; ts += t_
    cam.location = ps / 7; tgt.location = ts / 7
    cam.keyframe_insert("location", frame=f); tgt.keyframe_insert("location", frame=f)
    p = ball_pos(t); ball.location = p; ball.rotation_euler = (t * 2.1, -t * 3.3, 0)
    ball.keyframe_insert("location", frame=f); ball.keyframe_insert("rotation_euler", frame=f)

sc.render.use_compositing = False
sc.render.use_sequencer = False

os.makedirs(OUT, exist_ok=True)
if SEL is None: frames = range(0, NF)
elif "-" in SEL: a0, a1 = map(int, SEL.split("-")); frames = range(a0, a1)
else: frames = [int(x) for x in SEL.split(",")]
print("images :", NF, "| tunnels :", [(round(fn["rim"], 2), round(fn["exit"], 2)) for fn in FUN], flush=True)
for f in frames:
    if os.path.exists(os.path.join(OUT, f"{f:04d}.png")): continue      # reprise possible
    t0 = time.time()
    sc.frame_set(f); sc.render.filepath = os.path.join(OUT, f"{f:04d}.png")
    bpy.ops.render.render(write_still=True)
    print(f"image {f} : {time.time() - t0:.1f}s", flush=True)
