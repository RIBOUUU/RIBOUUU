"""Spirale EPIQUE en BOUCLE PARFAITE (Blender Cycles) : montee qui pulse -> tourbillon + tube -> DROP -> retour.

Principe de la boucle : toute la scene est periodique. Apres une periode P (16 s), la bille a tourne de DA
et descendu de DZ ; chaque element (bloc, entonnoir, poussiere) existe en plusieurs copies decalees de
(DA, DZ, P), et toutes les animations sont des fonctions de (t - k P). La camera, le soleil et la bille
suivent des regles qui tournent avec la spirale : l'image a t + P est exactement celle a t.

Usage : python blender_boucle.py <timeline_boucle.json> <dossier_sortie> [w] [h] [samples] [debut-fin | liste]
(les numeros d'images sont ceux de la video : 0 .. 479)
"""
import json, math, sys, os, time, random
import bpy
from mathutils import Vector

TLP, OUT = sys.argv[1], sys.argv[2]
W = int(sys.argv[3]) if len(sys.argv) > 3 else 720
H = int(sys.argv[4]) if len(sys.argv) > 4 else 1280
SAMPLES = int(sys.argv[5]) if len(sys.argv) > 5 else 18
SEL = sys.argv[6] if len(sys.argv) > 6 else None
FPS = 30

TL = json.load(open(TLP)); HITS = TL["hits"]; TUN = TL["tunnel"]; KICKS = TL["kicks"]
PER = TL["period"]; OFF = TL["offset"]; EXIT = TUN["exit"]
NV = int(round(PER * FPS)); F0 = int(round(OFF * FPS))          # images video : scene F0 .. F0+NV-1

R, V, BR, SLOPE = 5.0, 5.5, 0.28, 1.3
RF, R0, HF, TUBE = 1.5, 0.30, 1.7, 3.4
PIRATE = os.environ.get("THEME") == "pirate"     # theme « grande aventure en mer » (caisses, tourbillon, ocean)
C_BUILD, C_DROP = (1.0, 0.42, 0.0), (1.0, 0.04, 0.40)            # chiffres : jaune (montee), magenta (drop)
B_BUILD, B_DROP = (0.1, 1.0, 0.75), (1.0, 0.72, 0.08)            # bille : cyan (montee), or (drop)
C_FUN = C_DROP
if PIRATE:
    C_BUILD, C_DROP = (1.0, 0.55, 0.06), (1.0, 0.07, 0.03)        # chiffres : or, puis rouge
    B_BUILD, B_DROP = (0.05, 0.35, 1.0), (1.0, 0.68, 0.06)        # perle bleue -> tresor en or
    C_FUN = (0.75, 0.95, 1.0)                                    # ecume du tourbillon

def P3(a, r, z): return Vector((r * math.cos(a), r * math.sin(a), z))
def sstep(e0, e1, x):
    u = min(1.0, max(0.0, (x - e0) / (e1 - e0))); return u * u * (3 - 2 * u)

def hop_params(z0, z1, T):
    """rebond dont la hauteur depend de la duree : petits sauts rapides, grands sauts lents"""
    dy = z1 - z0; Hh = min(2.2, 0.15 + 1.6 * T)
    x = (math.sqrt(2 * Hh) + math.sqrt(2 * Hh - 2 * dy)) / T
    g = x * x; return g, math.sqrt(2 * g * Hh)

# ---------------- trajectoire d'une periode ----------------
# Gravite fixe. Chaque rebond est un point de contact : sol (F), plafond (C : la bille monte taper une caisse
# suspendue par en dessous), mur interieur (W) ou exterieur (O). La caisse est orientee selon la normale
# du choc (vitesse sortante - vitesse entrante), calculee plus bas : elle est donc toujours juste.
G = 28.0; HC, HW, WD = 5.2, 4.0, 2.2
PAT_A = "FFCFWFFCFWFCFFWFF"            # montee (le dernier rebond saute dans le tourbillon)
PAT_B = "FCWFCWFCWF"                   # drop : la bille tape dans tous les sens
def hit_type(i, sec, j): return (PAT_B[j % len(PAT_B)] if sec else PAT_A[i % len(PAT_A)])
def hop_seg(t0, T, a0, r0, z0, a1, r1, z1):
    return ("hop", t0, t0 + T, (a0, r0, z0, a1, r1, z1, G, (z1 - z0) / T + G * T / 2, T))
SEGS, BLOCKS = [], []
a, r, z = 0.0, R, 0.0; zb = 0.0
FN = None; jB = 0
for i, h in enumerate(HITS):
    t0, T = h["t"], h["dur"]
    kind = "sortie" if abs(t0 - TUN["exit"]) < 1e-6 else "normal"
    BLOCKS.append(dict(a=a, r=r, z=z, t=t0, sec=h["sec"], kind=kind, i=i))
    if abs(t0 + T - TUN["rim"]) < 1e-6:
        ac = a - V * T / R; zr = zb - SLOPE * T * 0.6
        SEGS.append(hop_seg(t0, T, a, r, z, ac, R, zr))
        C = P3(ac, R + RF, 0); top = zr - BR; k = HF / (RF / R0 - 1)
        F = TUN["drop"] - TUN["rim"]; D = TUN["exit"] - TUN["drop"]
        arr = []; th = ac + math.pi; n = 900
        for q in range(n + 1):
            u = q / n; rr = RF * (R0 / RF) ** (u ** 2)
            arr.append((th, rr)); th += V * (1 + 1.8 * u) / rr * F / n
        z_hole = top - HF + BR; z_e = z_hole - TUBE - 1.1; v0 = 1.5
        FN = dict(C=C, ac=ac, top=top, k=k, arr=arr, F=F, D=D, rim=TUN["rim"], drop=TUN["drop"], exit=TUN["exit"],
                  z_hole=z_hole, z_e=z_e, v0=v0, A=2 * (z_hole - z_e - v0 * D) / (D * D), w_end=V * 2.8 / R0)
        SEGS.append(("funnel", TUN["rim"], TUN["drop"], FN)); SEGS.append(("drop", TUN["drop"], TUN["exit"], FN))
        a, r, z = ac, R + RF, z_e; zb = z_e
    else:
        na = a - V * T / R; zb -= SLOPE * T
        last = i + 1 >= len(HITS)
        if not last and HITS[i + 1]["sec"]: jB += 1
        ty = "F" if last or abs(HITS[i + 1]["t"] - TUN["exit"]) < 1e-6 else hit_type(i + 1, HITS[i + 1]["sec"], jB - 1)
        if i + 2 < len(HITS) and abs(HITS[i + 1]["t"] + HITS[i + 1]["dur"] - TUN["rim"]) < 1e-6: ty = "F"
        nr, nz = R, zb
        if ty == "C": nz = zb + HC
        elif ty == "W": nr, nz = R - WD, zb + HW
        elif ty == "O": nr, nz = R + WD, zb + HW
        SEGS.append(hop_seg(t0, T, a, r, z, na, nr, nz))
        a, r, z = na, nr, nz
DA, DZ = a, z                     # decalage d'une periode a la suivante (rayon revenu a R)
print(f"periode : rotation {DA:.3f} rad, descente {DZ:.2f}", flush=True)

def Tk(v, k):
    c, s = math.cos(k * DA), math.sin(k * DA)
    return Vector((v.x * c - v.y * s, v.x * s + v.y * c, v.z + k * DZ))

def funnel_state(t):
    u = min(1.0, max(0.0, (t - FN["rim"]) / FN["F"])) * (len(FN["arr"]) - 1)
    q = min(int(u), len(FN["arr"]) - 2); f = u - q
    return (FN["arr"][q][0] * (1 - f) + FN["arr"][q + 1][0] * f, FN["arr"][q][1] * (1 - f) + FN["arr"][q + 1][1] * f)

def ball0(t):
    for kind, t0, t1, p in SEGS:
        if t < t1 or kind == SEGS[-1][0] and t1 == SEGS[-1][2]:
            if kind == "hop":
                a0, r0, z0, a1, r1, z1, g, vy, T = p
                s = t - t0; kk = s / T
                return P3(a0 + (a1 - a0) * kk, r0 + (r1 - r0) * kk, z0 + vy * s - g * s * s / 2)
            if kind == "funnel":
                th, rr = funnel_state(t)
                return FN["C"] + Vector((rr * math.cos(th), rr * math.sin(th), FN["top"] - FN["k"] * (RF / rr - 1) + BR * 1.15))
            s = t - FN["drop"]; u = s / FN["D"]
            th = FN["arr"][-1][0] + FN["w_end"] * s * (1 - 0.5 * min(u, 1))
            rr = R0 * max(0.0, 1 - u / 0.3)
            return FN["C"] + Vector((rr * math.cos(th), rr * math.sin(th), FN["z_hole"] - FN["v0"] * s - FN["A"] * s * s / 2))

def ball_pos(t):
    k = math.floor(t / PER); return Tk(ball0(t - k * PER), k)

def smooth_ball(t, win=0.45, n=13):
    v = Vector((0, 0, 0))
    for q in range(n): v += ball_pos(t + (q / (n - 1) - 0.5) * 2 * win)
    return v / n

def loc(t): return t - math.floor(t / PER) * PER
def drop_e(tl): return sstep(EXIT, EXIT + 0.25, tl) * (1 - sstep(PER - 0.8, PER, tl))

# evenements repetes sur plusieurs periodes
def rep(ts, m0=-2, m1=4): return sorted(x + m * PER for m in range(m0, m1) for x in ts)
ALLHITS = rep([h["t"] for h in HITS]); ALLKICKS = rep(KICKS); ALLBOOMS = rep([TUN["exit"]])

# ---------------- scene ----------------
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
sc.cycles.samples = SAMPLES; sc.cycles.use_adaptive_sampling = True; sc.cycles.use_denoising = True
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
sc.cycles.max_bounces = 4; sc.cycles.transparent_max_bounces = 10
if os.environ.get("RAPIDE") == "1":      # reglages de calcul plus rapides (difference a peine visible apres debruitage)
    sc.cycles.max_bounces = 3; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 2
    sc.cycles.transmission_bounces = 4; sc.cycles.adaptive_threshold = 0.05; sc.cycles.adaptive_min_samples = 4
    sc.render.motion_blur_position = 'CENTER'
    for k_, v_ in (("denoising_prefilter", 'FAST'), ("denoising_quality", 'BALANCED')):
        try: setattr(sc.cycles, k_, v_)
        except Exception: pass
sc.cycles.caustics_reflective = False; sc.cycles.caustics_refractive = False
sc.render.resolution_x, sc.render.resolution_y = W, H
sc.render.fps = FPS
sc.render.use_motion_blur = True; sc.render.motion_blur_shutter = 0.45
sc.frame_start = F0; sc.frame_end = F0 + NV - 1
for vt, lk in (('AgX', 'AgX - Punchy'), ('AgX', 'Punchy'), ('Filmic', 'Medium High Contrast')):
    try:
        sc.view_settings.view_transform = vt
        try: sc.view_settings.look = lk
        except Exception: pass
        break
    except Exception: continue
sc.render.image_settings.file_format = 'PNG'
KF0, KF1 = F0 - 2, F0 + NV + 2                                    # images ou l'on pose des cles

def mat(name, base=(0.02, 0.02, 0.022), rough=0.4, metal=0.0, emis=None, strength=0.0, coat=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*base, 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    for key in ("Coat Weight", "Clearcoat"):
        if key in p.inputs: p.inputs[key].default_value = coat; break
    if emis is not None:
        p.inputs["Emission Color"].default_value = (*emis, 1); p.inputs["Emission Strength"].default_value = strength
    return m

def key_series(sock, fnc):
    last = None
    for f in range(KF0, KF1 + 1):
        v = fnc(f / FPS)
        if last is not None and abs(v - last) < 1e-4 and f < KF1: continue      # valeurs constantes : pas de cle
        sock.default_value = v; sock.keyframe_insert("default_value", frame=f); last = v

world = bpy.data.worlds.new("ciel"); sc.world = world; world.use_nodes = True
nt = world.node_tree; nt.nodes.clear()
tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
ramp = nt.nodes.new("ShaderNodeValToRGB"); bg = nt.nodes.new("ShaderNodeBackground"); out = nt.nodes.new("ShaderNodeOutputWorld")
nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs[0])
nt.links.new(ramp.outputs[0], bg.inputs[0]); nt.links.new(bg.outputs[0], out.inputs[0])
cr = ramp.color_ramp
if PIRATE:     # coucher de soleil sur la mer : horizon dore, haut du ciel bleu profond
    cr.elements[0].position = 0.3; cr.elements[0].color = (0.02, 0.06, 0.12, 1)
    cr.elements[1].position = 0.95; cr.elements[1].color = (0.05, 0.10, 0.32, 1)
    e = cr.elements.new(0.50); e.color = (1.0, 0.58, 0.22, 1)
    e = cr.elements.new(0.56); e.color = (0.95, 0.40, 0.32, 1)
    e = cr.elements.new(0.70); e.color = (0.25, 0.22, 0.50, 1)
else:
    cr.elements[0].position = 0.25; cr.elements[0].color = (0.035, 0.03, 0.09, 1)
    cr.elements[1].position = 0.92; cr.elements[1].color = (0.10, 0.07, 0.22, 1)
    e = cr.elements.new(0.50); e.color = (0.95, 0.38, 0.22, 1)
    e = cr.elements.new(0.62); e.color = (0.38, 0.16, 0.34, 1)
bg.inputs[1].default_value = 0.85

sun_d = bpy.data.lights.new("soleil", 'SUN'); sun_d.energy = 2.6; sun_d.color = (1.0, 0.72, 0.55); sun_d.angle = math.radians(4)
sun = bpy.data.objects.new("soleil", sun_d); sc.collection.objects.link(sun)
for f in range(KF0, KF1 + 1):          # le soleil tourne avec la spirale (periodique)
    sun.rotation_euler = (math.radians(55), 0, math.radians(35) + DA * (f / FPS) / PER)
    sun.keyframe_insert("rotation_euler", index=2, frame=f)

# ---------------- blocs ----------------
SEG7 = {0: 'abcdef', 1: 'bc', 2: 'abged', 3: 'abgcd', 4: 'fgbc', 5: 'afgcd', 6: 'afgedc', 7: 'abc', 8: 'abcdefg', 9: 'abcfgd'}
m_body = mat("bloc", base=(0.018, 0.018, 0.02), rough=0.3, coat=0.7)
if PIRATE:     # bois de caisse : veines (texture d'ondes) + variations
    nb_ = m_body.node_tree; pbb = nb_.nodes.get("Principled BSDF")
    tco_ = nb_.nodes.new("ShaderNodeTexCoord"); wv = nb_.nodes.new("ShaderNodeTexWave")
    wv.inputs["Scale"].default_value = 1.4; wv.inputs["Distortion"].default_value = 7.0; wv.inputs["Detail"].default_value = 4.0
    rp = nb_.nodes.new("ShaderNodeValToRGB")
    rp.color_ramp.elements[0].color = (0.17, 0.085, 0.035, 1); rp.color_ramp.elements[1].color = (0.34, 0.18, 0.08, 1)
    nb_.links.new(tco_.outputs["Object"], wv.inputs["Vector"]); nb_.links.new(wv.outputs["Fac"], rp.inputs[0])
    nb_.links.new(rp.outputs[0], pbb.inputs["Base Color"])
    pbb.inputs["Roughness"].default_value = 0.55
    for key in ("Coat Weight", "Clearcoat"):
        if key in pbb.inputs: pbb.inputs[key].default_value = 0.25; break
m_iron = mat("fer", base=(0.08, 0.075, 0.07), rough=0.45, metal=1.0)
m_off = mat("segment_eteint", base=(0.06, 0.06, 0.065), rough=0.5)
m_wire = mat("corde", base=(0.45, 0.33, 0.18), rough=0.9) if PIRATE else mat("fil", base=(0.3, 0.3, 0.32), rough=0.3, metal=1.0)
m_screw = mat("vis", base=(0.8, 0.8, 0.82), rough=0.25, metal=1.0)

def add_box(name, size, loc_, parent, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc_)
    o = bpy.context.object; o.name = name; o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        bm = o.modifiers.new("biseau", 'BEVEL'); bm.width = bevel; bm.segments = 3
    o.data.materials.append(m); o.parent = parent
    return o

def seg_rects(w, h, t):
    m = {'a': (0, h / 2 - t / 2, w - 2 * t, t), 'd': (0, -h / 2 + t / 2, w - 2 * t, t), 'g': (0, 0, w - 2 * t, t),
         'f': (-w / 2 + t / 2, h / 4, t, h / 2 - t * 1.4), 'b': (w / 2 - t / 2, h / 4, t, h / 2 - t * 1.4),
         'e': (-w / 2 + t / 2, -h / 4, t, h / 2 - t * 1.4), 'c': (w / 2 - t / 2, -h / 4, t, h / 2 - t * 1.4)}
    return [(k, m[k]) for k in 'abcdefg']

def impulses(b):
    th = b["t"]; A = 1.0 if b["kind"] == "sortie" else (0.42 if b["sec"] == 0 else 0.6)
    imp = [(th, A)]
    imp += [(x, 0.16 * A) for x in ALLHITS if th < x <= th + 1.6]
    imp += [(x, 0.13 if loc(x) >= EXIT - 1e-6 else 0.07) for x in ALLKICKS if th + 0.01 < x]
    imp += [(x, 0.4) for x in ALLBOOMS if th + 0.01 < x]
    return imp

def make_dz(imp):
    def dz(t):
        v = 0.0
        for ti, am in imp:
            s = t - ti
            if 0 < s < 2.0: v -= am * math.exp(-3.2 * s) * math.sin(2 * math.pi * 2.4 * s)
        return v
    return dz

def make_neon(b):
    th = b["t"]
    ks = [x for x in ALLKICKS if x > th + 0.01 and loc(x) >= EXIT - 1e-6]; bs = [x for x in ALLBOOMS if x > th + 0.01]
    def neon(t):
        if t < th: return 0.0
        v = 0.35 + 8.6 * math.exp(-(t - th) / 0.35)
        for x in bs:
            if 0 <= t - x < 3: v += 6.0 * math.exp(-(t - x) / 0.45)
        for x in ks:
            if 0 <= t - x < 1: v += 2.2 * math.exp(-(t - x) / 0.14)
        return v
    return neon

FUN_K = (0, 1)                                       # copies d'entonnoir utiles
def fun_center(k): return Tk(FN["C"], k)

BL, BH = 1.9, 0.85
from mathutils import Matrix
def vel(t, e=0.004): return (ball_pos(t + e) - ball_pos(t - e)) / (2 * e)
def contact_frame(b):
    """normale du choc + axes de la caisse (le bout lumineux tourne vers la camera)"""
    t = b["t"]; e = 0.012
    n = vel(t + e) - vel(t - e)
    n = n.normalized() if n.length > 1e-3 else Vector((0, 0, 1))
    p = ball_pos(t)
    d = P3(b["a"] + 0.62, 12.0, p.z + 2.0) - p                    # direction approximative de la camera
    x = d - n * d.dot(n)
    if x.length < 1e-3: x = Vector((1, 0, 0)) - n * n.x
    x.normalize(); y = n.cross(x)
    return n, x, y
n_blocks = 0
for k in (-1, 0, 1, 2):
    for b in BLOCKS:
        tg = b["t"] + k * PER
        if not (OFF - 6.5 <= tg <= OFF + PER + 9.5): continue         # hors champ pendant toute la video
        i = b["i"]; s = b["sec"]; nm = f"{k}_{i}"
        n, xa, ya = contact_frame(b)
        if b["kind"] == "sortie":
            w = 1.4; bl = 2.6; n = Vector((0, 0, 1)); xa = Vector((math.cos(b["a"]), math.sin(b["a"]), 0)); ya = n.cross(xa)
        else:
            w = 0.9; bl = BL
        rot = Matrix((xa, ya, n)).transposed().to_euler()
        root = bpy.data.objects.new(f"bloc_{nm}", None); sc.collection.objects.link(root)
        base = ball_pos(b["t"]) - n * (BR + BH / 2)
        if b["kind"] == "sortie": base = P3(b["a"], b["r"], b["z"] - BR - BH / 2)
        root.location = Tk(base, k); root.rotation_euler = rot
        if k: root.rotation_euler = (Matrix.Rotation(k * DA, 3, 'Z') @ rot.to_matrix()).to_euler()
        piv = bpy.data.objects.new(f"pivot_{nm}", None); sc.collection.objects.link(piv); piv.parent = root
        add_box(f"corps_{nm}", (bl, w, BH), (0, 0, 0), piv, m_body, bevel=0.04)
        if PIRATE:     # cerclages en fer aux deux bouts de la caisse
            for sx in (-bl / 2 + 0.22, bl / 2 - 0.34):
                add_box(f"cerclage_{nm}", (0.12, w + 0.03, BH + 0.03), (sx, 0, 0), piv, m_iron, bevel=0.01)
        for sx in (-0.6, 0.5):
            bpy.ops.mesh.primitive_cylinder_add(radius=0.045, depth=0.03, location=(sx, 0, BH / 2 + 0.01)); sw = bpy.context.object
            sw.data.materials.append(m_screw); sw.parent = piv
        lit = mat(f"neon_{nm}", base=(0.05, 0.04, 0.0), rough=0.4, emis=C_DROP if s else C_BUILD, strength=0.0)
        d = (i + 1) % 10; fx = bl / 2 + 0.012
        for kk, (cy, cz, sw_, sh) in seg_rects(min(w, 0.9) * 0.42, BH * 0.62, 0.065 * min(1, w / 0.6)):
            add_box(f"seg_{nm}_{kk}", (0.02, sw_, sh), (fx, cy, cz), piv, lit if kk in SEG7[d] else m_off)
        for (cy, cz, sw_, sh) in ((0, BH / 2 - 0.035, w * 0.92, 0.035), (0, -BH / 2 + 0.035, w * 0.92, 0.035),
                                  (w * 0.46 - 0.0175, 0, 0.035, BH * 0.92), (-w * 0.46 + 0.0175, 0, 0.035, BH * 0.92)):
            add_box(f"cadre_{nm}", (0.02, sw_, sh), (fx, cy, cz), piv, lit)
        if b["kind"] == "sortie":
            for sy in (-1, 1):
                add_box(f"lisere_{nm}", (bl * 0.96, 0.04, 0.03), (0, sy * (w / 2 - 0.05), BH / 2 + 0.005), piv, lit)
        # cordes : les caisses du plafond sont suspendues, quelques caisses du sol aussi
        wx = Tk(base, k)
        clash = any((wx.xy - fun_center(q).xy).length < RF + 0.6 for q in (k - 1, k, k + 1))
        hang = n.z < -0.8 or (n.z > 0.8 and i % (6 if PIRATE else 3) == 0)
        if hang and not clash and b["kind"] == "normal":
            sz = 1 if n.z > 0 else -1
            bpy.ops.mesh.primitive_cylinder_add(radius=0.02 if PIRATE else 0.01, depth=30, location=(bl / 2 - 0.15, 0, sz * (BH / 2 + 15))); wi = bpy.context.object
            wi.data.materials.append(m_wire); wi.parent = piv
        bt = dict(b); bt["t"] = tg
        key_series(lit.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"], make_neon(bt))
        dz = make_dz(impulses(bt))
        for f in range(max(KF0, int(tg * FPS) - 1), KF1 + 1):
            t = f / FPS
            piv.location.z = dz(t); piv.keyframe_insert("location", index=2, frame=f)       # recule selon la normale
            piv.rotation_euler.x = 0.35 * dz(t - 0.06); piv.keyframe_insert("rotation_euler", index=0, frame=f)
        n_blocks += 1
print("blocs :", n_blocks, flush=True)

# ---------------- entonnoirs + tubes ----------------
def funnel_mesh(name):
    rings = []; nr, na = 56, 128
    for q in range(nr + 1):
        u = q / nr; rr = (RF + 0.35) * (R0 / (RF + 0.35)) ** u
        rings.append((rr, 0.0 if rr >= RF else -FN["k"] * (RF / rr - 1)))
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

def glow0(tl):
    v = 1.2 + 7.0 * sstep(FN["rim"] - 0.3, FN["drop"], tl) ** 2
    if tl > FN["drop"]: v = 1.2 + 14.0 * math.exp(-(tl - FN["drop"]) / 0.35)
    return v

for k in FUN_K:
    C = fun_center(k); top = FN["top"] + k * DZ; sh = k * PER
    fo = funnel_mesh(f"entonnoir_{k}"); fo.location = (C.x, C.y, top)
    fm, ph_s, gl_s = funnel_material(f"tourbillon_{k}", C_FUN); fo.data.materials.append(fm)
    if PIRATE:     # eau profonde, tres brillante
        pf = fm.node_tree.nodes.get("Principled BSDF")
        pf.inputs["Base Color"].default_value = (0.0, 0.07, 0.13, 1); pf.inputs["Roughness"].default_value = 0.06
    def phase(t, sh=sh):
        tl = t - sh; th, _ = funnel_state(tl)
        return -4.8 * tl - 2.0 * (th - FN["arr"][0][0])
    glow = lambda t, sh=sh: glow0(t - sh)
    key_series(ph_s, phase); key_series(gl_s, glow)
    bpy.ops.mesh.primitive_torus_add(major_radius=RF + 0.35, minor_radius=0.05, location=(C.x, C.y, top))
    ring = bpy.context.object; rm = mat(f"anneau_{k}", base=(0.05, 0.05, 0.05), emis=C_FUN, strength=3.0); ring.data.materials.append(rm)
    key_series(rm.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"], glow)
    z_top = top - HF; z_bot = FN["z_e"] + k * DZ + 0.85
    bpy.ops.mesh.primitive_cylinder_add(radius=0.42, depth=z_top - z_bot, vertices=64, end_fill_type='NOTHING',
                                        location=(C.x, C.y, (z_top + z_bot) / 2))
    tb = bpy.context.object; tb.data.materials.append(m_glass); bpy.ops.object.shade_smooth()
    zz = z_top - 0.3
    while zz > z_bot + 0.1:
        bpy.ops.mesh.primitive_torus_add(major_radius=0.45, minor_radius=0.035, location=(C.x, C.y, zz))
        tr_o = bpy.context.object; tm = mat(f"anneau_tube_{k}_{zz:.2f}", base=(0.6, 0.4, 0.1) if PIRATE else (0.05, 0.05, 0.05), metal=1.0 if PIRATE else 0.0,
                                 rough=0.3, emis=(1.0, 0.6, 0.1) if PIRATE else C_DROP, strength=0.5)
        tr_o.data.materials.append(tm)
        dzz = FN["z_hole"] + k * DZ - zz; s_ = (-FN["v0"] + math.sqrt(FN["v0"] ** 2 + 2 * FN["A"] * max(dzz, 0))) / FN["A"]
        tp = FN["drop"] + s_ + sh
        key_series(tm.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"],
                   lambda t, tp=tp: 0.6 + 25 * math.exp(-max(0, t - tp) / 0.25) * (t >= tp - 0.02))
        zz -= 0.55

# ---------------- poussieres lumineuses (periodiques elles aussi) ----------------
rnd = random.Random(5)
tmpl = []
while len(tmpl) < 110:
    rr = rnd.uniform(2.5, 16); aa = rnd.uniform(0, 2 * math.pi); zz = rnd.uniform(DZ, 0) + 4
    p = P3(aa, rr, zz)
    if abs(rr - R) < 1.2 or abs(rr - R - RF) < RF + 0.6: continue
    tmpl.append((p, rnd.uniform(0.025, 0.06), rnd.randrange(3)))
COLS = [(1.0, 0.55, 0.25), (1.0, 0.35, 0.6), (0.5, 0.7, 1.0)]
if PIRATE: COLS = [(1.0, 0.62, 0.2), (1.0, 0.85, 0.5), (0.7, 0.9, 1.0)]      # paillettes d'or et embruns
for ci, col in enumerate(COLS):
    verts, faces = [], []
    for k in (-1, 0, 1, 2):
        for p, sz, c in tmpl:
            if c != ci: continue
            q = Tk(p, k); b0 = len(verts)
            for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                verts.append((q.x + d[0] * sz, q.y + d[1] * sz, q.z + d[2] * sz))
            for f_ in ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)):
                faces.append(tuple(b0 + x for x in f_))
    me = bpy.data.meshes.new(f"poussieres_{ci}"); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(f"poussieres_{ci}", me); sc.collection.objects.link(o)
    o.data.materials.append(mat(f"poussiere_{ci}", base=(0, 0, 0), emis=col, strength=8.0))

# ---------------- ocean (suit la descente : reste periodique) ----------------
FOND = os.environ.get("FOND") == "1"         # fond transparent : un mur d'images est ajoute au montage
if FOND: sc.render.film_transparent = True
if PIRATE and not FOND:
    bpy.ops.mesh.primitive_plane_add(size=900); sea = bpy.context.object
    ms = mat("ocean", base=(0.01, 0.06, 0.10), rough=0.08)
    ns = ms.node_tree; pse = ns.nodes.get("Principled BSDF")
    nz_ = ns.nodes.new("ShaderNodeTexNoise"); nz_.inputs["Scale"].default_value = 60.0; nz_.inputs["Detail"].default_value = 6.0
    bump = ns.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.25
    ns.links.new(nz_.outputs["Fac"], bump.inputs["Height"]); ns.links.new(bump.outputs["Normal"], pse.inputs["Normal"])
    sea.data.materials.append(ms)
    for f in range(KF0, KF1 + 1):
        t = f / FPS
        sea.location = (0, 0, smooth_ball(t, 1.5, 9).z - 24); sea.rotation_euler = (0, 0, DA * t / PER)
        sea.keyframe_insert("location", frame=f); sea.keyframe_insert("rotation_euler", index=2, frame=f)

# ---------------- bille ----------------
bpy.ops.mesh.primitive_uv_sphere_add(radius=BR, segments=64, ring_count=32)
ball = bpy.context.object; bpy.ops.object.shade_smooth()
mb = bpy.data.materials.new("bille"); mb.use_nodes = True; n = mb.node_tree
pb = n.nodes.get("Principled BSDF")
noise = n.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value = 3.5
cramp = n.nodes.new("ShaderNodeValToRGB")
cramp.color_ramp.elements[0].color = (0.35, 0.35, 0.35, 1); cramp.color_ramp.elements[1].color = (1, 1, 1, 1)
rgb = n.nodes.new("ShaderNodeRGB"); vm = n.nodes.new("ShaderNodeVectorMath"); vm.operation = 'MULTIPLY'
n.links.new(noise.outputs["Fac"], cramp.inputs[0]); n.links.new(cramp.outputs[0], vm.inputs[0]); n.links.new(rgb.outputs[0], vm.inputs[1])
n.links.new(vm.outputs[0], pb.inputs["Base Color"]); n.links.new(vm.outputs[0], pb.inputs["Emission Color"])
pb.inputs["Emission Strength"].default_value = 7.0; pb.inputs["Roughness"].default_value = 0.15
for key in ("Coat Weight", "Clearcoat"):
    if key in pb.inputs: pb.inputs[key].default_value = 1.0; break
ball.data.materials.append(mb)
bl_d = bpy.data.lights.new("lumiere_bille", 'POINT'); bl_d.energy = 120; bl_d.shadow_soft_size = 0.3
blo = bpy.data.objects.new("lumiere_bille", bl_d); sc.collection.objects.link(blo); blo.parent = ball

def ball_col(tl):
    u = sstep(FN["drop"], FN["exit"], tl) * (1 - sstep(PER - 1.5, PER, tl))
    return [B_BUILD[j] * (1 - u) + B_DROP[j] * u for j in range(3)]

# ---------------- camera ----------------
cam_d = bpy.data.cameras.new("cam"); cam_d.lens = 36; cam_d.sensor_fit = 'VERTICAL'; cam_d.sensor_height = 36
cam_d.dof.use_dof = True; cam_d.dof.aperture_fstop = 2.4; cam_d.dof.focus_object = ball
cam = bpy.data.objects.new("cam", cam_d); sc.collection.objects.link(cam); sc.camera = cam
tgt = bpy.data.objects.new("cible", None); sc.collection.objects.link(tgt)
con = cam.constraints.new('TRACK_TO'); con.target = tgt; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
W2 = 2 * math.pi / PER

def rig(t):
    k = math.floor(t / PER); tl = t - k * PER; e = drop_e(tl)
    sb = smooth_ball(t); lk = smooth_ball(t + 0.25, 0.35, 9)
    a_ = math.atan2(sb.y, sb.x)
    phi = a_ + 0.62 + 0.12 * math.sin(2 * W2 * t) + 0.22 * e * math.sin(7 * W2 * t)
    rc = 13.5 - 2.2 * e + 0.6 * math.sin(3 * W2 * t); hc = 2.6 - 0.6 * e + 0.6 * math.sin(2 * W2 * t + 1.2)   # vue plus de cote : on voit les chocs en haut, en bas et sur les cotes
    for x in KICKS:                                  # le zoom « pompe » sur les kicks du drop
        s = tl - x
        if x >= EXIT - 1e-6 and 0 <= s < 0.5: rc -= 0.45 * math.exp(-s / 0.09)
    pos = Vector((rc * math.cos(phi), rc * math.sin(phi), sb.z + hc))
    tg = Vector((lk.x * 0.85, lk.y * 0.85, lk.z - 0.2))
    C = fun_center(k); top = FN["top"] + k * DZ; ac = FN["ac"] + k * DA
    wf = sstep(FN["rim"] - 0.45, FN["rim"] + 0.2, tl) * (1 - sstep(FN["drop"] - 0.12, FN["drop"] + 0.12, tl))
    wd = sstep(FN["drop"] - 0.12, FN["drop"] + 0.12, tl) * (1 - sstep(FN["exit"] + 0.1, FN["exit"] + 0.7, tl))
    if wf > 0:
        u = (tl - FN["rim"]) / FN["F"]; psi = ac + 0.35 + 0.6 * u
        fp = Vector((C.x + 3.3 * math.cos(psi), C.y + 3.3 * math.sin(psi), top + 6.3 - 1.2 * u))
        pos = pos.lerp(fp, wf); tg = tg.lerp(Vector((C.x, C.y, top - 0.9)), wf)
    if wd > 0:
        bp = ball_pos(min(t, k * PER + FN["exit"])); psi = ac + 0.75
        dp = Vector((C.x + 5.2 * math.cos(psi), C.y + 5.2 * math.sin(psi), bp.z + 1.0))
        pos = pos.lerp(dp, wd); tg = tg.lerp(Vector((C.x, C.y, bp.z - 0.6)), wd)
    s = tl - FN["exit"]
    if 0 < s < 0.8:
        kk = 0.25 * math.exp(-6 * s); pos += Vector((math.sin(53 * s), math.cos(47 * s), math.sin(61 * s))) * kk
    return pos, tg

for f in range(KF0, KF1 + 1):
    t = f / FPS; tl = loc(t); ps, ts = Vector((0, 0, 0)), Vector((0, 0, 0))
    for q in range(7):
        p_, t_ = rig(t + (q / 6 - 0.5) * 0.2); ps += p_; ts += t_
    cam.location = ps / 7; tgt.location = ts / 7
    cam.keyframe_insert("location", frame=f); tgt.keyframe_insert("location", frame=f)
    ball.location = ball_pos(t); ball.rotation_euler = (5 * W2 * t, -8 * W2 * t, 0)
    ball.keyframe_insert("location", frame=f); ball.keyframe_insert("rotation_euler", frame=f)
    c = ball_col(tl); rgb.outputs[0].default_value = (*c, 1); rgb.outputs[0].keyframe_insert("default_value", frame=f)
    bl_d.color = c; bl_d.keyframe_insert("color", frame=f)
    boost = sstep(FN["rim"], FN["drop"], tl) * (1 - sstep(FN["exit"], FN["exit"] + 0.6, tl))
    pulse = sum(math.exp(-(tl - x) / 0.12) for x in KICKS if x >= EXIT - 1e-6 and 0 <= tl - x < 0.6)
    bl_d.energy = 120 + 160 * boost + 90 * pulse; bl_d.keyframe_insert("energy", frame=f)

if os.environ.get("EXPORT_BILLE"):       # positions de la bille + camera image par image (pour la trainee au montage)
    rows = []
    for f in range(NV):
        sc.frame_set(F0 + f); rows.append(dict(f=f, cam=[list(r) for r in cam.matrix_world.inverted()]))
    g0 = 2 * (F0 - NV) - 4                       # grille globale de positions (60 par seconde) sur 2 periodes
    pos = [list(ball_pos(g / 60)) + list(ball_col(loc(g / 60))) for g in range(g0, 2 * (F0 + NV) + 1)]
    json.dump(dict(lens=cam_d.lens, sensor=cam_d.sensor_height, br=BR, g0=g0, pos=pos, frames=rows),
              open(os.environ["EXPORT_BILLE"], "w"))
    print("export ok", flush=True); sys.exit(0)
sc.render.use_compositing = False; sc.render.use_sequencer = False
# acceleration : modificateurs figes une fois pour toutes + donnees persistantes entre les images
dg = bpy.context.evaluated_depsgraph_get()
for o_ in [o_ for o_ in sc.objects if o_.type == 'MESH' and o_.modifiers]:
    me_ = bpy.data.meshes.new_from_object(o_.evaluated_get(dg)); o_.modifiers.clear(); o_.data = me_
sc.render.use_persistent_data = os.environ.get("PERSIST") == "1"
os.makedirs(OUT, exist_ok=True)
if SEL is None: frames = range(0, NV)
elif "-" in SEL: a0, a1 = map(int, SEL.split("-")); frames = range(a0, a1)
else: frames = [int(x) for x in SEL.split(",")]
for f in frames:
    path = os.path.join(OUT, f"{f:04d}.png")
    if os.path.exists(path): continue
    t0 = time.time()
    sc.frame_set(F0 + f); sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"image {f} : {time.time() - t0:.1f}s", flush=True)
