import struct
import math
from collections import namedtuple


SIG = namedtuple("SIG", "magic mys odo")
SIG.__frmt__ = '<4s2I'
SIG.__size__ = struct.calcsize(SIG.__frmt__)

H20 = namedtuple("H20", "vdo fdo        oc vc vcM fc u02        ")
H38 = namedtuple("H38", "vdo fdo fs u01 oc vc vcM fc u02 u03 u04")
H20.__frmt__ = '<2I    4H    I'
H38.__frmt__ = '<2I 2I 4I 2I I'
H38.__size__ = struct.calcsize(H38.__frmt__)
H20.__size__ = struct.calcsize(H20.__frmt__)

O40 = namedtuple("O40", "vdo fdo    vc fc     n u01 xm ym xM yM name")
O48 = namedtuple("O48", "vdo fdo eo vc fc u00 n u01 xm ym xM yM name")
O40.__frmt__ = '<2I    2H    2H4f32s'
O48.__frmt__ = '<2I 1I 2H 1I 2H4f32s'
O40.__size__ = struct.calcsize(O40.__frmt__)
O48.__size__ = struct.calcsize(O48.__frmt__)

V10 = namedtuple("V10", "r g b a x y f")
V10.__frmt__ = '<4B2fI'
V10.__size__ = struct.calcsize(V10.__frmt__)

PLGO = namedtuple("PLGO", "obj verts faces")
PLGF = namedtuple("PLGO", "sig head objs")

MYS = {
    0x01000400: 0x38,
    0x01000300: 0x20,
    0x01000200: 0x20,
    0x02000000: 0x38
}

HTYPE = { 0x38: H38, 0x20: H20 }
OTYPE = { 0x38: O48, 0x20: O40 }

HDEFAULT = {
    0x38: H38(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0),
    0x20: H20(0, 0,       0, 0, 0, 0, 0      )
}

ODEFAULT = {
    0x38: O48(0, 0, 0, 0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, ""),
    0x20: O40(0, 0,    0, 0,    0, 0, 0.0, 0.0, 0.0, 0.0, "")
}


def decode_name(obj):
    n = obj.name
    n = n[0:n.index(b'\0')]
    return n.decode("cp932").rstrip(" \r\n\t\0")


def encode_name(name):
    return name.ljust(32, '\0').encode("cp932")


def get_min_max(verts):
    xm, ym, xM, yM = 0, 0, 0, 0
    if len(verts) > 0:
        xm = min(v.x for v in verts)
        ym = min(v.y for v in verts)
        xM = max(v.x for v in verts)
        yM = max(v.y for v in verts)
    return (xm, ym, xM, yM)


def tmp2plgf(tmp, mys):
    sig, s = SIG(b"PLG0", mys, MYS[mys]), MYS[mys]
    head = HDEFAULT[s]._asdict()
    head['vdo'], head['fdo'] = s, s
    
    objs = []
    for n, vf in tmp.items():
        obj, objsize = ODEFAULT[s]._asdict(), ODEFAULT[s].__size__
        verts, faces = vf
        obj['n'] = len(faces[0])
        obj['xm'], obj['ym'], obj['xM'], obj['yM'] = get_min_max(verts)
        obj['vc'], obj['fc'] = len(verts), len(faces) * obj['n']
        obj['name'] = encode_name(n)
        objs.append([obj, verts, faces])

        head['oc'] += 1
        head['vc'] += obj['vc']
        head['fc'] += obj['fc']
        head['vdo'] += objsize
        head['fdo'] += 0x10 * obj['vc'] + objsize

    head['vcM'] = max(o['vc'] for o,v,f in objs)
    
    if s == 0x38:
        head['fs'] = head['oc'] * objsize + head['vc'] * 0x10 + head['fc'] * 0x02 + s
        head['fs'] = math.ceil(head['fs'] / 0x04) * 0x04
        eo = head['fs'] - s
    
    if mys != 0x01000200:
        vdo, fdo = head['vdo'] - s, head['fdo'] - s
        for o, v, f in objs:
            os = OTYPE[s].__size__
            o['vdo'], o['fdo'] = vdo, fdo
            vdo, fdo = vdo + o['vc'] * 0x10 - os, fdo + o['fc'] * 0x02 - os
            if s == 0x38:
                o['eo'] = eo
                eo = eo - os
    
    ooo = [PLGO(OTYPE[s](**o), v, f) for o,v,f in objs]
    plgf = PLGF(sig, HTYPE[s](**head), ooo)
    return plgf


def _write_struct(obj, ouf):
    ouf.write(struct.pack(obj.__frmt__, *obj))


def _read_struct(cls, inf, frmt = None, size = None):
    return cls._make(struct.unpack(cls.__frmt__, inf.read(cls.__size__)))


def export_plg(filepath, plgf):
    with open(filepath, "wb") as ouf:
        _write_struct(plgf.sig, ouf)
        _write_struct(plgf.head, ouf)
        [_write_struct(o.obj, ouf) for o in plgf.objs]
        [_write_struct(v, ouf) for o in plgf.objs for v in o.verts]
        [ouf.write(struct.pack('<{:d}H'.format(o.obj.n), *f)) for o in plgf.objs for f in o.faces]
        ouf.write(b'\0' * (math.ceil(ouf.tell() / 4) * 4 - ouf.tell()))


def import_plg(filepath):
    plgf = None

    with open(filepath, "rb") as inf:
        sig = _read_struct(SIG, inf)
        head = _read_struct(HTYPE[sig.odo], inf)
        objs = [_read_struct(OTYPE[sig.odo], inf) for _ in range(0, head.oc)]
        verts = [_read_struct(V10, inf) for _ in range(0, head.vc)]
        fidxs = struct.unpack('<{:d}H'.format(head.fc), inf.read(head.fc * 0x02))

    vcc, fcc, w = 0, 0, []
    for o in objs:
        ov, of = [], []
        if o.vc > 0:
            ov = verts[vcc:vcc + o.vc]
        if o.fc > 0 and o.n > 0:
            of = [fidxs[fcc:fcc + o.fc][k:k + o.n] for k in range(0, o.fc, o.n)]
        w.append(PLGO(o, ov, of))
        vcc, fcc = vcc + o.vc, fcc + o.fc

    return PLGF(sig, head, w)


if __name__ == "__main__":
    pass
