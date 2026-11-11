"""Hand-drawn copper: the core regulator block (Raspberry Pi's figure 4 layout, rotated), the USB pair from
the connector through U6 and the series resistors to U1, and the QSPI/USB supply pins.
Coordinates are mm relative to the board corner.
Idempotent: first deletes every track and via on the board. 05_fanout.py imports this module, adds the U1
fan-out and saves both, so run 05 rather than this file. Then run the autorouter."""
from pcblib import *
from kipy.board_types import Track, Via
from kipy.proto.board import board_types_pb2 as bt

k, b, doc = open_board()
N = lambda v: int(round(v * 1e6))
nets = {n.name: n for n in b.get_nets()}
F = fps(b)


old = list(b.get_tracks()) + list(b.get_vias())
if old:
    b.remove_items(old)


def pad(ref, num):
    p = next(p for p in F[ref].definition.pads if p.number == num)
    return round(p.position.x / 1e6 - X0, 4), round(p.position.y / 1e6 - Y0, 4)


items = []


def T(net, w, *pts, layer=bt.BL_F_Cu):
    for a, c in zip(pts, pts[1:]):
        t = Track()
        t.net, t.layer, t.width, t.locked = nets[net], layer, N(w), True
        t.start, t.end = mm(X0 + a[0], Y0 + a[1]), mm(X0 + c[0], Y0 + c[1])
        items.append(t)


def V(net, x, y):
    v = Via()
    v.net, v.position, v.locked = nets[net], mm(X0 + x, Y0 + y), True
    v.diameter, v.drill_diameter = N(0.55), N(0.25)
    items.append(v)


pin = lambda n: pad('U1', str(n))
c6g, c6v = pad('C6', '2'), pad('C6', '1')
c7g, c7v = pad('C7', '2'), pad('C7', '1')
lx, l1v = pad('L1', '2'), pad('L1', '1')
c8a, c8g = pad('C8', '1'), pad('C8', '2')

# VREG_LX: through the pad gaps of C6 and C7, then into the inductor
y = pin(48)[1]
assert abs((c6g[1] + c6v[1]) / 2 - y) < 0.01, 'C6/C7 gap must line up with pin 48'
T('/VREG_LX', 0.13, pin(48), (26.7, y), (26.4, y - 0.3))
T('/VREG_LX', 0.3, (26.4, y - 0.3), (lx[0] + 0.7, y - 0.3 - (26.4 - lx[0] - 0.7)), lx)
# VREG_VIN and VREG_PGND straight into C6
T('+3V3', 0.2, pin(49), (c6v[0], pin(49)[1]))
T('GND', 0.2, pin(47), (c6g[0], pin(47)[1]))
# VREG_AVDD: filter R15/C8
T('Net-(U1-VREG_AVDD)', 0.2, pin(46), (29.15, pin(46)[1]), (28.85, pin(46)[1] - 0.3), (28.85, c8a[1]), c8a)
T('Net-(U1-VREG_AVDD)', 0.2, pad('R15', '2'), (c8a[0], pad('R15', '2')[1] + c8a[0] - pad('R15', '2')[0]), c8a)
# ground vias of the two regulator capacitors and C8
for g in (c7g, c6g):
    V('GND', g[0], 9.55)
    T('GND', 0.3, g, (g[0], 9.55))
T('GND', 0.3, c8g, (c8g[0], c8g[1] + 0.4), (c7g[0], c8g[1] + 0.4 + c8g[0] - c7g[0]), (c7g[0], 9.55))
# +1V1: inductor to C7, with the via that feeds the DVDD pins
T('+1V1', 0.4, (l1v[0] + 0.4, 11.15), (c7v[0], 11.15))
V('+1V1', 26.48, 11.2)
# VREG_FB: sensed at C7 through a via inside the pad ring and a bottom-layer track
fb = pin(50)
V('+1V1', 30.5, fb[1])
T('+1V1', 0.15, fb, (30.5, fb[1]))
T('+1V1', 0.2, (30.5, fb[1]), (30.5 - (fb[1] - 11.2), 11.2), (26.48, 11.2), layer=bt.BL_B_Cu)
# USB: series resistors to pins 51/52
r4, r3 = pad('R4', '2'), pad('R3', '2')
dm, dp = pin(51), pin(52)
T('/USB_DM', 0.22, dm, (r4[0] + 0.34 + (r4[1] - dm[1]), dm[1]), (r4[0] + 0.34, r4[1]), r4)
T('/USB_DP', 0.22, dp, (r3[0] + 0.2 + (r3[1] - dp[1]), dp[1]), (r3[0] + 0.2, r3[1]), r3)
# USB_OTP_VDD and QSPI_IOVDD into C18
c18 = pad('C18', '1')
for n in (53, 54):
    T('+3V3', 0.2, pin(n), (c18[0], pin(n)[1]))

# ---- USB connector to U6. The receptacle's pad order is B7(D-) A6(D+) A7(D-) B6(D+): the outer pads run
# straight to U6, each inner pad joins its twin through a bottom-layer jumper.
DN, DP, BL = '/USB_CONN_DN', '/USB_CONN_DP', bt.BL_B_Cu
b7, a6, a7, b6 = (pad('J1', n) for n in ('B7', 'A6', 'A7', 'B6'))
u_dn_l, u_dp_l, u_dn_r, u_dp_r = (pad('U6', n) for n in ('4', '6', '3', '1'))
xe = b7[0] + 0.6                                            # just past the pad ends
T(DN, 0.2, b7, (xe + 0.2, b7[1]), (xe + 0.2 + b7[1] - u_dn_l[1], u_dn_l[1]), u_dn_l)
T(DP, 0.2, b6, (xe + 0.35, b6[1]), (xe + 0.6, b6[1] + 0.25), (u_dp_l[0] - 0.45, b6[1] + 0.25),
  (u_dp_l[0] - 0.45 + b6[1] + 0.25 - u_dp_l[1], u_dp_l[1]), u_dp_l)
ve, vg = (8.9, a6[1] - 0.15), (8.75, b6[1] + 0.25)          # D+ jumper
vf, vh = (9.55, a7[1] - 0.15), (9.55, u_dn_l[1])            # D- jumper
T(DP, 0.2, a6, (ve[0] - 0.3, a6[1]), (ve[0] - 0.15, ve[1]), ve)
T(DN, 0.2, a7, (vf[0] - 0.3, a7[1]), (vf[0] - 0.15, vf[1]), vf)
for net, v in ((DP, ve), (DP, vg), (DN, vf), (DN, vh)):
    V(net, *v)
T(DP, 0.2, ve, (ve[0], vg[1] - 0.15), vg, layer=BL)
T(DN, 0.2, vf, vh, layer=BL)
# VBUS and GND pins of U6: a via under the body and one beside the ground pin
T('VBUS', 0.3, pad('U6', '5'), (11.9, 5.75))
V('VBUS', 11.9, 5.75)
T('GND', 0.3, pad('U6', '2'), (14.2, 5.75))
V('GND', 14.2, 5.75)

# ---- USB pair from U6 to the series resistors: 0.22 mm tracks, 0.15 mm gap
P = 0.37                                                    # pair pitch
D = P * 2 ** 0.5
r4i, r3i = pad('R4', '1'), pad('R3', '1')
yn, xn = 7.0, 24.1                                          # D- runs east at yn, then south at xn
yp, xp = yn + P, xn - P
T(DN, 0.22, u_dn_r, (14.6, u_dn_r[1]), (14.6 + yn - u_dn_r[1], yn), (xn - 0.5, yn), (xn, yn + 0.5),
  (xn, r4i[1] - 0.3), (xn + 0.3, r4i[1]), r4i)
x1 = 14.6 - D + (u_dp_r[1] - u_dn_r[1])                     # where D+ starts to follow the D- diagonal
T(DP, 0.22, u_dp_r, (x1, u_dp_r[1]), (x1 + yp - u_dp_r[1], yp), (xn - 0.5 + P - D, yp), (xp, yn + 0.5 + D - P),
  (xp, r3i[1] - 0.3), (xp + 0.3, r3i[1]), r3i)


def commit():
    b.create_items(items)
    b.save()
    print('created', len(items), 'removed', len(old))


if __name__ == '__main__':
    commit()
