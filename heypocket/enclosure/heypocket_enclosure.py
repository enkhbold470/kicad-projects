"""HeyPocket enclosure: front shell, back lid (MagSafe ring recess), button plunger.

Frame: X right, Y up as seen from the FRONT, Z towards the front face.
  z = 0      back (lid outer, phone side)      z = 1.2  lid inner / shell rim
  z = 8.2    front inner face                   z = 9.4  front outer face
Board positions come straight from the EasyEDA PCBs (main board PCB1, USB board USB_PCB).
Usage: python heypocket_enclosure.py <outdir>
"""
import sys, json
from pathlib import Path
from build123d import *

OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)

# ---------------- envelope
W, H, R_PLAN = 60.0, 102.0, 4.0     # 102 mm leaves 55.5 mm between the boards for a 605050 incl. its PCM
WALL, FRONT_T, LID_T, CAV = 1.6, 1.2, 1.2, 7.9     # 3.5 mm above the main PCB for the 3.3 mm SKRT side switch
Z_LID_IN, Z_FRONT_IN = LID_T, LID_T + CAV
Z_FRONT_OUT = Z_FRONT_IN + FRONT_T
IW, IH = W - 2 * WALL, H - 2 * WALL           # 56.8 x 94.8
XI, YI = IW / 2, IH / 2                         # inner wall at x=+-28.4, y=+-47.4

# ---------------- boards (board-local mm, Y up) -> enclosure
MB = (2.4, 35.8)            # main board centre: 1.0 mm from right wall, 0.6 mm from top wall
MB_TOP_Z = Z_FRONT_IN - 3.5  # PCB top surface (tallest top parts: SKRTLAE010 3.3 mm, E73 module <= 3.0 mm)
PCB_T = 1.0
UB = (2.4, -40.773)         # USB board centre: under the FFC, USB-C mouth 0.2 mm inside the wall
UB_TOP_Z = Z_FRONT_IN - 4.6  # TYPE-C-31-M-12 is 3.26 mm tall
mb = lambda x, y: (MB[0] + x, MB[1] + y)
ub = lambda x, y: (UB[0] + x, UB[1] + y)

MAIN_HOLES = [mb(-22.6, -10.6), mb(22.6, -10.6), mb(6.0, 10.6)]
USB_HOLES = [ub(-9.8, 1.5), ub(9.8, 1.5)]
MICS = [mb(-6.288, 10.88), mb(11.713, 10.88)]
LEDS = [(mb(16.605, 11.455), 0.5), (mb(18.3, 11.405), 0.5), (mb(20.0, 11.405), 0.5), (mb(22.6, 11.4), 0.7)]
LED_MAX_H = 0.8             # tallest LED (0603 parts; the XL-1615 RGB is 0.6)
SW1_Y, SW1_Z = mb(0, 5.0)[1], MB_TOP_Z + 0.7       # MSK12C02 lever (body 1.4 mm)
SW2_Y, SW2_Z = mb(0, -4.7)[1], MB_TOP_Z + 1.65     # ALPS SKRTLAE010 side-push actuator (body 3.3 mm)
SW2_TIP_X = MB[0] + 25.35                          # actuator tip, from the footprint outline (0.35 mm past the board edge)
USBC_X, USBC_Z = ub(0, 0)[0], UB_TOP_Z + 1.63
LID_BOSSES = [(-27.6, -5.0), (27.6, -5.0), (-25.0, -46.6), (25.0, -46.6)]   # all outside the MagSafe ring
RING_C, RING_OD, RING_ID = (0.0, 15.5), 56.4, 45.6  # keeps the BLE antenna corner outside the ring

def cyl(x, y, z0, h, r):
    return Pos(x, y, z0 + h / 2) * Cylinder(r, h)

def slot(center, along, normal, length, height, depth):
    """Rounded slot through a wall: `along` = slot length direction, `normal` = through direction."""
    pl = Plane(origin=center, x_dir=along, z_dir=normal)
    return extrude(pl * RectangleRounded(length, height, min(length, height) / 2 - 0.01), amount=depth / 2, both=True)

# ---------------- shell
outer = extrude(Plane.XY.offset(Z_LID_IN) * RectangleRounded(W, H, R_PLAN), amount=Z_FRONT_OUT - Z_LID_IN)
outer = fillet(outer.edges().group_by(Axis.Z)[-1], radius=1.0)
cavity = extrude(Plane.XY.offset(Z_LID_IN) * RectangleRounded(IW, IH, R_PLAN - WALL), amount=CAV)
shell = outer - cavity

for (x, y) in MAIN_HOLES:   # board standoffs, M1.6 thread-forming screws from the back
    shell += cyl(x, y, MB_TOP_Z, Z_FRONT_IN - MB_TOP_Z, 1.7)
    shell -= cyl(x, y, MB_TOP_Z, 3.0, 0.65)
for (x, y) in USB_HOLES:
    shell += cyl(x, y, UB_TOP_Z, Z_FRONT_IN - UB_TOP_Z, 1.7)
    shell -= cyl(x, y, UB_TOP_Z, 4.0, 0.65)
for (x, y) in LID_BOSSES:   # lid bosses, M2 thread-forming flat heads
    shell += cyl(x, y, Z_LID_IN, CAV, 1.6)
    shell -= cyl(x, y, Z_LID_IN, 5.5, 0.8)

for (x, y) in MICS:         # acoustic tube down to the PCB (0.4 mm foam gasket closes the gap) + port
    tube_z0 = MB_TOP_Z + 0.4
    shell += cyl(x, y, tube_z0, Z_FRONT_IN - tube_z0, 1.2)
    shell -= cyl(x, y, tube_z0, Z_FRONT_IN - tube_z0, 0.5)
    shell -= cyl(x, y, Z_FRONT_IN - 0.01, FRONT_T + 0.02, 0.5)

baf_z0 = MB_TOP_Z + LED_MAX_H + 0.15                # light baffle: solid block over the LED row, one bore per LED
baf = Pos(*mb(19.65, 11.35), (baf_z0 + Z_FRONT_IN) / 2 + 0.05) * Box(8.3, 2.9, Z_FRONT_IN - baf_z0 + 0.1)
shell += baf
for (x, y), r in LEDS:      # light channels + a shallow status bar to fill with clear UV resin
    shell -= cyl(x, y, baf_z0 - 0.01, Z_FRONT_OUT - baf_z0 + 0.02, r)
bar_x = (LEDS[0][0][0] + LEDS[-1][0][0]) / 2
shell -= Pos(bar_x, LEDS[0][0][1], Z_FRONT_OUT - 0.2) * extrude(RectangleRounded(9.2, 2.8, 1.0), amount=0.4, both=True)

# USB-C opening + plug overmould relief in the bottom wall
shell -= slot((USBC_X, -YI - WALL / 2, USBC_Z), (1, 0, 0), (0, 1, 0), 9.4, 3.9, WALL + 1.0)
shell -= slot((USBC_X, -H / 2 + 0.3, USBC_Z), (1, 0, 0), (0, 1, 0), 12.4, 5.6, 0.6)

# right wall: recessed slot for the slide-switch lever, hole for the button plunger
shell -= slot((XI + WALL / 2, SW1_Y, SW1_Z), (0, 1, 0), (1, 0, 0), 5.0, 1.6, WALL + 1.0)
shell -= slot((W / 2 - 0.5, SW1_Y, SW1_Z), (0, 1, 0), (1, 0, 0), 8.0, 3.6, 1.0)
shell -= Pos(XI + WALL / 2, SW2_Y, SW2_Z) * Rot(0, 90, 0) * Cylinder(1.1, WALL + 1.0)
shell -= Pos(XI + 0.125 - 0.05, SW2_Y, SW2_Z) * Rot(0, 90, 0) * Cylinder(1.75, 0.35)       # flange counterbore, floor at XI + 0.25

# top-edge groove that receives the lid tongue
shell -= Pos(0, YI + 0.35, Z_LID_IN + 0.35) * Box(31.0, 0.7 + 0.02, 0.7)

# ---------------- lid
lid = extrude(RectangleRounded(W, H, R_PLAN), amount=LID_T)
lid = fillet(lid.edges().group_by(Axis.Z)[0], radius=0.6)
lip_outer = extrude(Plane.XY.offset(LID_T) * RectangleRounded(IW - 0.3, IH - 0.3, R_PLAN - WALL - 0.15), amount=0.8)
lip_inner = extrude(Plane.XY.offset(LID_T) * RectangleRounded(IW - 1.9, IH - 1.9, max(R_PLAN - WALL - 0.95, 0.5)), amount=0.8)
lip = lip_outer - lip_inner
for (x, y) in LID_BOSSES:
    lip -= cyl(x, y, LID_T, 0.8, 1.85)
lid += lip
lid += Pos(0, YI - 0.15 + 0.35, LID_T + 0.275) * Box(29.6, 0.7, 0.55)        # tongue into the shell groove
for (x, y) in LID_BOSSES:                                                     # M2 countersunk holes
    lid -= cyl(x, y, -0.01, LID_T + 0.82, 1.15)
    lid -= Pos(x, y, 0.475) * Cone(2.1, 1.15, 0.95)
ring = cyl(*RING_C, -0.01, 0.61, RING_OD / 2) - cyl(*RING_C, -0.02, 0.63, RING_ID / 2)
lid -= ring                                                                   # MagSafe ring sticker recess
lid -= Pos(RING_C[0], RING_C[1] - 34.7, 0.29) * Box(3.2, 12.2, 0.6)           # optional orientation magnet
txt = extrude(Text("HeyPocket", font_size=4.0), amount=0.3) + Pos(0, -5.2) * extrude(Text("heypcb.ai", font_size=2.6), amount=0.3)
lid -= Pos(0, -31.0, -0.01) * mirror(txt, about=Plane.YZ)                     # reads correctly on the back

# ---------------- button plunger (prints separately; drop in from inside before fitting the board)
fl_x0 = SW2_TIP_X + 0.3         # generous gap: the tip position comes from the footprint outline, not a measured part
plunger = Pos(fl_x0 + 0.2, SW2_Y, SW2_Z) * Rot(0, 90, 0) * Cylinder(1.55, 0.4)
stem_len = (W / 2 + 0.9) - (fl_x0 + 0.4)     # 0.9 mm proud of the wall
plunger += Pos(fl_x0 + 0.4 + stem_len / 2, SW2_Y, SW2_Z) * Rot(0, 90, 0) * Cylinder(1.0, stem_len)

# ---------------- placeholders for the fit check (not for manufacture)
mpcb = Pos(MB[0], MB[1], MB_TOP_Z - PCB_T) * extrude(RectangleRounded(50, 26, 1.5), amount=PCB_T)
module = Pos(*mb(-17.1, 3.9), MB_TOP_Z + 1.5) * Box(13.0, 18.0, 3.0)          # E73-2G4M08S1C
main_fpc = Pos(*mb(-0.05, -9.6), MB_TOP_Z - PCB_T - 1.0) * Box(10.0, 6.0, 2.0)   # AFC01-S10FCA-00
upcb = Pos(UB[0], UB[1], UB_TOP_Z - PCB_T) * extrude(RectangleRounded(24, 16, 1.0), amount=PCB_T)
usbc = Pos(*ub(0, -4.253), UB_TOP_Z + 1.63) * Box(8.94, 8.35, 3.26)
usb_fpc = Pos(*ub(0.05, 4.6), UB_TOP_Z - PCB_T - 1.0) * Box(10.0, 6.0, 2.0)
BAT_L = (MB[1] - 13.0) - (UB[1] + 8.0)              # free length between the board edges
battery = Pos(0, (MB[1] - 13.0 + UB[1] + 8.0) / 2, Z_FRONT_IN - 0.2 - 3.0) * Box(50, BAT_L - 0.5, 6.0)
motor = cyl(*mb(-17.0, -4.5), MB_TOP_Z - PCB_T - 2.7, 2.7, 5.0)
placeholders = {"main_pcb": mpcb, "module": module, "main_fpc": main_fpc, "usb_pcb": upcb, "usb_c": usbc,
                "usb_fpc": usb_fpc, "battery": battery, "motor": motor, "plunger": plunger}

# ---------------- checks
report = {"shell_volume_mm3": round(shell.volume, 1), "lid_volume_mm3": round(lid.volume, 1),
          "outer_mm": [W, H, Z_FRONT_OUT], "clash_mm3": {}}
for name, p in placeholders.items():
    for host_name, host in (("shell", shell), ("lid", lid)):
        if name == "plunger" and host_name == "shell":
            v = (host & p).volume
        else:
            v = (host & p).volume
        if v > 0.001: report["clash_mm3"][f"{name}~{host_name}"] = round(v, 3)
pairs = [("battery", "main_fpc"), ("battery", "usb_fpc"), ("battery", "main_pcb"), ("battery", "usb_pcb"), ("motor", "main_fpc"), ("plunger", "main_pcb")]
for a, b in pairs:
    v = (placeholders[a] & placeholders[b]).volume
    if v > 0.001: report["clash_mm3"][f"{a}~{b}"] = round(v, 3)
# clearance from the antenna strip to the ring and to every screw
ant = (mb(-23.6, 9.4), mb(-10.6, 12.9))                 # E73 ceramic-antenna end
nearest = (max(ant[0][0], min(RING_C[0], ant[1][0])), max(ant[0][1], min(RING_C[1], ant[1][1])))
report["antenna_to_ring_od_mm"] = round(((nearest[0] - RING_C[0]) ** 2 + (nearest[1] - RING_C[1]) ** 2) ** 0.5 - RING_OD / 2, 2)
report["antenna_to_nearest_screw_mm"] = round(min(((x - max(ant[0][0], min(x, ant[1][0]))) ** 2 + (y - max(ant[0][1], min(y, ant[1][1]))) ** 2) ** 0.5
                                                  for (x, y) in MAIN_HOLES + LID_BOSSES), 2)
report["battery_envelope_mm"] = [round(BAT_L, 2), round(2 * (27.6 - 1.6), 2), round(Z_FRONT_IN - Z_LID_IN - 0.4, 2)]
report["ffc_entry_to_entry_mm"] = round((MB[1] - 12.727) - (UB[1] + 7.727), 2)
report["plunger_gap_to_switch_mm"] = round(fl_x0 - SW2_TIP_X, 3)
report["plunger_free_play_mm"] = round((XI + 0.25) - (fl_x0 + 0.4), 3)
report["baffle_gap_above_pcb_mm"] = round(baf_z0 - MB_TOP_Z, 2)
report["usbc_mouth_to_outer_face_mm"] = round(H / 2 - 0.3 - 0.6 - (-(UB[1] - 8.427)) + 0.6, 2)

# ---------------- export
for name, part in (("heypocket_shell", shell), ("heypocket_lid", lid), ("heypocket_button_plunger", plunger)):
    export_step(part, str(OUT / f"{name}.step"))
    export_stl(part, str(OUT / f"{name}.stl"), tolerance=0.01, angular_tolerance=0.15)
asm = Compound(children=[shell, lid, plunger] + list(placeholders.values())[:-1], label="heypocket_assembly")
export_step(asm, str(OUT / "heypocket_assembly_fitcheck.step"))
(OUT / "fit_report.json").write_text(json.dumps(report, indent=1))
print(json.dumps(report, indent=1))
