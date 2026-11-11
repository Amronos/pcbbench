"""Compare lib/devboard RM2 pads and pins with the datasheet (fig. 6, table 2) and Raspberry Pi's own KiCad files."""
import re,sys
R='/home/ubuntu/pcbbench-run/'
def pads(path):
    s=open(path).read().replace('\r','')
    out={}
    for m in re.finditer(r'\(pad "(\d+)" smd \w+\s+\(at ([-\d.]+) ([-\d.]+)(?: ([-\d.]+))?\)\s+\(size ([\d.]+) ([\d.]+)\)',s):
        n,x,y,rot,w,h=m.groups(); w,h=float(w),float(h)
        if rot and float(rot)%180==90: w,h=h,w
        out[int(n)]=(float(x),float(y),w,h)
    return out
def pins(path):
    s=open(path).read().replace('\r','')
    return {int(n):(nm,t) for t,nm,n in re.findall(r'\(pin (\w+) line\s+\(at [^)]*\)\s+\(length [^)]*\)\s+\(name "([^"]+)".*?\(number "(\d+)"',s,flags=re.S)}
# Datasheet figure 6: body 14.5 x 16.5 centred on origin, pads 2.0 x 1.0 overhanging the body edge by 0.5,
# pitch 1.5, pin 7/15 centre 1.8 above the bottom edge, pin 8 centre 2.75 from the left edge.
W,H=14.5,16.5
ds={}
for i in range(7):
    y=H/2-1.8-1.5*(6-i)
    ds[1+i]=(-W/2-0.5+1.0,y,2.0,1.0)
    ds[21-i]=(W/2+0.5-1.0,y,2.0,1.0)
for i in range(7):
    ds[8+i]=(-W/2+2.75+1.5*i,H/2+0.5-1.0,1.0,2.0)
mine=pads(R+'lib/devboard.pretty/RaspberryPi_RM2.kicad_mod')
off=pads(R+'scratch/rm2/official_rm2-kicad/kicad/rpi_rmc20452t.kicad_mod')
ok=True
for n in range(1,22):
    a,b,c=mine[n],tuple(round(v,4) for v in ds[n]),off[n]
    good = a==b==c; ok&=good
    print(n,a,'datasheet',b,'official',c,'OK' if good else 'MISMATCH')
table2={1:'GND',2:'NC',3:'SCLK',4:'GND',5:'DI',6:'DO',7:'GND',8:'GPIO0',9:'CS',10:'nIRQ',11:'GND',12:'WL_ON',13:'BT_ON',14:'VDDIO',15:'GND',16:'VIN',17:'GPIO2',18:'GPIO1',19:'NC',20:'NC',21:'GND'}
mp=pins(R+'lib/devboard.kicad_sym'); op=pins(R+'scratch/rm2/official_rm2-kicad/kicad/RPI_RMC20452T.kicad_sym')
for n in range(1,22):
    good = mp[n][0]==table2[n]==op[n][0]; ok&=good
    print(n,mp[n],'official',op[n],'OK' if good else 'MISMATCH')
print('ALL OK' if ok and len(mine)==21 and len(mp)==21 else 'FAIL')
