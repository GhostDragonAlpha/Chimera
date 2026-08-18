
import sys, json, math, subprocess
from pathlib import Path
NATIVE = Path('E:/PythonChimera/ChimeraEngine/native')
def read_chimera(path):
    gd = {}
    for line in open(path):
        line = line.strip()
        if not line or line.startswith('#'): continue
        if '=' in line:
            k, v = line.split('=', 1)
            v = v.split('#')[0].strip()
            gd[k.strip()] = v.strip()
    return gd
def gen_terrain_py(gd):
    seed=int(gd['terrainSeed']); amp=int(gd['terrainAmp']); x0=int(gd['terrainX0']); x1=int(gg['terrainX1']); tsc=int(gd['terrainScale'])
    terr={}; rng=seed
    for x in range(x0,x1+1):
        rng=(rng*1103515245+12345)&0x7fffffff; terr[x]=(rng%(2*amp+1))-amp
    for _ in range(10000):
        changed=False; nterr=dict(terr)
        for x in range(x0,x1+1):
            a=terr.get(x-1,0); b=terr.get(x,0); c=terr.get(x+1,0); n=(a+2*b+c)>>2
            if n!=b: nterr[x]=n; changed=True
        terr=nterr
        if not changed: break
    return terr,_,_
gg=read_chimera(NATIVE/'genomes'/'beargoal.chimera')
ter8,_,_=gen_terrain_py(gg); TSC8=int(gg['terrainScale'])
p2=subprocess.Popen([str(NATIVE/'ca_core.exe'),str(NATIVE/'genomes'/'bearhill.chimera'),'selftest'],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
lines2=[]
for line in p2.stdout:
    lines2.append(line.strip())
    if '{"type":"final"}' in line: break
p2.terminate()
gfin=None
for l in lines2:
    if l.startswith('{'):
        try:
            m=json.loads(l)
            if m.get('type')=='final': gfin=m
        except: pass
PI=math.pi; A=float(gg['b4A']); T=float(gg['b4T'])
ALPHA=float(gg['l5Alpha']); GAMMA=float(gg['l5Gamma'])
EPS0=float(gg['l5Eps0']); EPSDECAY=float(gg['l5EpsDecay']); EPSMIN=float(gg['l5EpsMin'])
RBECK=float(gg['r5Beckon']); RWNEAR=float(gg['r5WaveNear'])
G=float(gg['gravity'])/(float(gg['tickHz'])**2*float(gg['cell']))
GOALX=int(gg['goalX']); omega=2*PI/T
ac=G/(omega*(int(gg['terrainSlope'])/TSC8)); tau=G/(A*omega)
budget=math.ceil(GOALX/(4*ac/T))
cells_list=gfin['cells'] if gfin else []
loY=float(min(c[1] for c in cells_list)); loX=min(c[0] for c in cells_list); hiX=max(c[0] for c in cells_list)
def col_h(x): return loY+ter8.get(x,0)/TSC8
def ground_at(bx_):
    g=None
    for x in range(math.floor(bx_)+loX,math.floor(bx_)+hiX+1):
        h=ter8.get(x,0); g=h if g is None else max(g,h)
    return loY+g/TSC8
def phys(y_,v_,bx_):
    v_-=G; y_+=v_; pen=ground_at(bx_)-(y_+loY); ct=False
    if pen>=0: y_+=pen; v_=0.0; ct=True
    return y_,v_,ct
st={'rng':1337,'y':0.0,'v':0.0,'contact':True,'bx':0.0,'epTick':0,'epReward':0.0,'gaitT':0}
def rnd():
    st['rng']=(st['rng']*1103515245.0+12345.0)%4294967296.0; st['rng']=int(st['rng'])&0x7fffffff
    return st['rng']/0x7fffffff
Q=[[0.0]*5 for _ in range(12)]; eps=EPS0; visits=[0]*12; arrivals=0; episode=0; arrived_list=[]
def nav_state():
    bxx=math.floor(st['bx']); bearing=0 if GOALX>bxx else 1
    ss=(col_h(bxx+1)-col_h(bxx-1))/2; slope=0 if ss>0 else (1 if ss>=-tau else 2)
    return (bearing*3+slope)*2+(1 if st['contact'] else 0)
def spawn():
    st['epTick']=0; st['epReward']=0.0
    st['bx']=0.0 if rnd()<0.5 else 30.0; st['y']=ground_at(st['bx'])-loY; st['v']=0.0; st['contact']=True
guard=0
while episode<320 and guard<320*budget*3:
    guard+=1; st['y'],st['v'],st['contact']=phys(st['y'],st['v'],st['bx']); s=nav_state(); visits[s]+=1
    if rnd()<eps: a=math.floor(rnd()*5)
    else:
        q=Q[s]; a=0
        for i in range(1,5):
            if q[i]>q[a]: a=i
    d0=abs(GOALX-st['bx'])
    if a!=0:
        d=1.0 if a in (1,3) else -1.0; amp=A if a<=2 else ac; st['gaitT']+=1; phi=2*PI*st['gaitT']/T
        if st['contact']: st['bx']+=d*amp*(2*PI/T)*abs(math.cos(phi))
    d1=abs(GOALX-st['bx']); r=RBECK*(d0-d1)-1.0/budget; terminal=False
    if math.floor(st['bx'])==GOALX: r+=RWNEAR; terminal=True; arrivals+=1
    st['epReward']+=r; st['epTick']+=1; s2=nav_state(); mx=max(Q[s2])
    slope=(s//2)%3
    if slope>=1 and 1<=a<=4 and (s2%2==0) and mx<0.0: mx=0.0
    Q[s][a]+=ALPHA*(r+(0.0 if terminal else GAMMA*mx)-Q[s][a])
    if terminal or st['epTick']>=budget:
        arrived_list.append(1 if terminal else 0); episode+=1; eps=max(EPSMIN,eps*EPSDECAY); spawn()
first30=sum(arrived_list[:30])/30; last30=sum(arrived_list[-30:])/30
print(f'arrivals={arrivals} first30={first30:.3f} last30={last30:.3f}')
for s in range(12):
    if visits[s]>0:
        greedy=max(range(5),key=lambda i:Q[s][i])
        print(f'  s{s} v={visits[s]} Q={[round(q,4) for q in Q[s]]} greedy=verb{greedy}')
def greedy_rollout(bx0):
    bx=float(bx0); y=ground_at(bx)-loY; v=0.0; contact=True; gt=0
    for tick in range(1,budget+1):
        y,v,contact=phys(y,v,bx); bxx=math.floor(bx)
        bearing=0 if GOALX>bxx else 1; ss=(col_h(bxx+1)-col_h(bxx-1))/2
        slope=0 if ss>0 else (1 if ss>=-tau else 2); s=(bearing*3+slope)*2+(1 if contact else 0)
        q=Q[s]; a=0
        for i in range(1,5):
            if q[i]>q[a]: a=i
        if a!=0:
            d=1.0 if a in (1,3) else -1.0; amp=A if a<=2 else ac; gt+=1; phi=2*PI*gt/T
            if contact: bx+=d*amp*(2*PI/T)*abs(math.cos(phi))
        if math.floor(bx)==GOALX: return True,tick
    return False,None
for sp in [0.0,30.0]:
    arr,tick=greedy_rollout(sp)
    print(f'Greedy bx={sp:.1f}: {"ARRIVED@"+str(tick) if arr else "STALLED"}')
