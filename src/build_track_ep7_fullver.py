# Hyak ep7 BGM 풀버전 — 탄막 회피 편. 210BPM, 140마디(4/4) = 160.000s.
#   숏폼(35마디 40s 게임싱크)의 음악 DNA(duru ep13 rondo 이식·카와이 퓨처베이스·I-V-vi-IV·
#   supersaw/kbass/bell/crystal·A_HOOK/B_MEL)를 유지하되, 게임이벤트 싱크(봄 b28·격파 b34)를 버리고
#   완결형 곡 구조로 재편곡. 루프 아님 → 자연 엔딩(C장조 해결 + 링아웃).
#   ★ep7 BGM은 100% 코드합성 오리지널(외부샘플 0). 사용자 확정: 두루 오리지널 이식 → CC0 대상.
#   구조: 인트로-빌드-A플로어-A드롭-아이시브레이크1-빌드2-B코러스-A버스-아이시브레이크2-빌드3-파이널-아웃트로.
import os, sys, numpy as np
from scipy.signal import sawtooth, square
sys.path.insert(0, r"D:/Akashic Records/projects/duru/영상소스/assets/bgm")
import duru_synth as ds
SR = ds.SR; m = ds.m2f
BPM = 210.0; spb = 60.0/BPM; bar = 4*spb; e8 = spb/2; e16 = spb/4
NB = 140; DUR = NB*bar; N = int(round(DUR*SR))
print(f"[i] ep7 fullver BPM={BPM} bar={bar:.4f}s bars={NB} dur={DUR:.4f}s N={N}")
rng = np.random.default_rng(7)

# ── 신스(론도 계승, 숏폼 빌더서 이식) ──
def supersaw(midis, dur, amp, detune=17.0, fc=4600):
    n = int(dur*SR)
    if n < 8: return np.zeros(max(n,1))
    t = np.arange(n)/SR; s = np.zeros(n); dets = [-1,-0.6,-0.25,0.25,0.6,1.0]
    for mi in midis:
        f0 = m(mi)
        for dt in dets: s += sawtooth(2*np.pi*f0*(2**(dt*detune/1200.0))*t)
    s /= (len(midis)*len(dets))
    return amp*ds.lp(s*ds.adsr(n,0.010,0.12,0.86,0.30,sus=0.86), fc)
def kbass(mi, dur, amp):
    n = int(dur*SR)
    if n < 6: return np.zeros(max(n,1))
    t = np.arange(n)/SR; f = m(mi)
    s = 0.6*sawtooth(2*np.pi*f*t)+0.4*square(2*np.pi*f*t); sub = np.sin(2*np.pi*(f/2)*t)
    body = ds.lp(s,1600)*np.exp(-t/0.16)*np.minimum(1,t/0.003) + 0.8*sub*np.exp(-t/0.22)*np.minimum(1,t/0.004)
    return amp*ds.tail_taper(body, rel=0.03)
def bell(mi, dur, amp):
    n = int(dur*SR)
    if n < 6: return np.zeros(max(n,1))
    t = np.arange(n)/SR; f = m(mi)
    mod = np.sin(2*np.pi*f*2.0*t)*np.exp(-t/0.14)*2.6
    s = np.sin(2*np.pi*f*t+mod)+0.3*np.sin(2*np.pi*2*f*t)*np.exp(-t/0.22)
    return amp*ds.tail_taper(s*np.exp(-t/0.45)*np.minimum(1,t/0.002), rel=0.04)
def crystal(mi, dur, amp):
    n = int(dur*SR)
    if n < 6: return np.zeros(max(n,1))
    t = np.arange(n)/SR; f = m(mi); s = np.zeros(n)
    for k,w,dk in [(1,1.0,1.3),(2.01,0.5,0.9),(3.01,0.3,0.6),(4.04,0.2,0.42),(5.43,0.12,0.3),(6.8,0.07,0.22)]:
        s += w*np.sin(2*np.pi*f*k*t)*np.exp(-t/dk)
    return amp*(s/2.0)*np.minimum(1,t/0.002)
def pkick(amp=1.0):
    dur=0.30; n=int(dur*SR); t=np.arange(n)/SR
    f=130*np.exp(-t/0.013)+46
    body=np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-t/0.17)
    click=ds.hp(rng.standard_normal(n),3200)*np.exp(-t/0.004)*0.5
    return amp*(body+click)
def crash(dur=1.4, amp=0.5, seed=7):
    n=int(dur*SR); r=np.random.default_rng(seed)
    return amp*ds.hp(r.standard_normal(n),5000)*np.exp(-np.arange(n)/(0.5*SR))
def riser(dur, amp=0.4, seed=3):
    n=int(dur*SR); r=np.random.default_rng(seed); t=np.arange(n)/SR
    return amp*ds.hp(r.standard_normal(n),2000)*(t/dur)**2.0*np.minimum(1,t/0.01)

# ── 버스 ──
chL=np.zeros(N); chR=np.zeros(N); bsL=np.zeros(N); bsR=np.zeros(N)
oL=np.zeros(N); oR=np.zeros(N); rev=np.zeros(N); kick_times=[]
def put(bL,bR,sig,t0,amp,pan=0.0,rs=0.0):
    i=int(round(t0*SR)); nn=min(len(sig),N-i)
    if i<0 or nn<=0: return
    th=(pan+1)*0.25*np.pi; bL[i:i+nn]+=sig[:nn]*amp*np.cos(th); bR[i:i+nn]+=sig[:nn]*amp*np.sin(th)
    if rs>0: rev[i:i+nn]+=sig[:nn]*amp*rs

# ── 화성 ──
V={'C':[60,64,67,71,74],'G':[59,62,67,71,74],'Am':[60,64,69,72,76],
   'F':[60,65,69,72,77],'Em':[59,62,64,67,71],'Dm':[60,62,65,69,72]}
ROOT={'C':36,'G':43,'Am':45,'F':41,'Em':40,'Dm':38}
A_CYC=['C','C','G','G','Am','Am','F','F']       # I-V-vi-IV Axis
B_CYC=['F','F','G','G','Em','Em','Am','Am']
K_CYC=['F','C','Dm','G']

# ── 구조 플랜(140마디) ──  각 항목 = (chord_name, section_label)
plan=[]
def add(cyc, n, label):
    for i in range(n): plan.append((cyc[i%len(cyc)], label))
add(['C'],4,'I')          # 0-3   인트로
add(A_CYC,8,'BLD')        # 4-11  빌드
add(A_CYC,16,'A')         # 12-27 A플로어
add(A_CYC,16,'AD')        # 28-43 A드롭/코러스
add(K_CYC,8,'K')          # 44-51 아이시 브레이크1
add(A_CYC,4,'BLD')        # 52-55 빌드2
add(B_CYC,16,'B')         # 56-71 B코러스
add(A_CYC,16,'A')         # 72-87 A버스
add(K_CYC,8,'K')          # 88-95 아이시 브레이크2
add(A_CYC,4,'BLD')        # 96-99 빌드3
add(A_CYC,36,'AD')        # 100-135 파이널 코러스
add(['C'],4,'O')          # 136-139 아웃트로
assert len(plan)==NB, len(plan)

# ── 멜로디(론도 계승) ──
A_HOOK=[(0,72,.5),(.5,76,.5),(1,79,1),(2,76,.5),(2.5,79,.5),(3,84,1),
        (4,83,.5),(4.5,79,.5),(5,76,.5),(5.5,79,.5),(6,76,2),
        (8,74,.5),(8.5,79,.5),(9,83,1),(10,79,.5),(10.5,74,.5),(11,79,1),
        (12,78,.5),(12.5,74,.5),(13,71,.5),(13.5,74,.5),(14,79,2)]
B_MEL=[(0,69,1),(1,72,1),(2,77,2),(4,76,1),(5,72,1),(6,69,2),
       (8,71,1),(9,74,1),(10,79,2),(12,78,1),(13,74,1),(14,71,2)]
def place_mel_block(seq, b0, b1, fn, amp, pan, rs, every=4):
    """b0..b1 범위에 every마디마다 멜로디 반복 배치."""
    for sbar in range(b0, b1, every):
        t0=sbar*bar
        for (b,mi,d) in seq:
            if b/4.0 >= (b1-sbar): break
            put(oL,oR, fn(mi, d*spb*0.96, amp), t0+b*spb, 1.0, pan, rs)

# ── 마디별 렌더 ──
for i,(nm,label) in enumerate(plan):
    t0=i*bar; chord=V[nm]; root=ROOT[nm]
    intro=(label=='I'); build=(label=='BLD'); icy=(label=='K'); outro=(label=='O')
    floor=(label=='A'); drop=(label=='AD'); Bsec=(label=='B')
    full = drop or Bsec or outro
    if build:
        # 로컬 빌드 진행도(각 빌드 블록 내 0→1)
        g = 0.42
    else:
        g = 1.0 if full else (0.34 if floor else (0.5 if icy else 0.4))
    # 코드
    cdur=bar*(1.6 if icy else 1.0)+0.05; camp=(0.30 if not icy else 0.24)*(0.5+0.5*g)
    put(chL,chR, supersaw(chord,cdur,camp,fc=(2800 if icy else 4600)), t0, 1.0, 0.0, 0.18 if not icy else 0.34)
    if icy:
        put(chL,chR, supersaw([x+12 for x in chord[:3]],cdur,0.09,detune=10,fc=6500), t0,1.0,0.0,0.4)
    # 베이스
    if icy:
        put(bsL,bsR, kbass(root-12, bar*0.9, 0.40), t0,1.0,0.0)
    elif intro:
        put(bsL,bsR, kbass(root-12, bar*0.9, 0.30), t0,1.0,0.0)
    else:
        pat=[0,0,7,0,0,12,0,7] if (i%2==0) else [0,7,0,12,0,0,7,0]
        for j,off in enumerate(pat):
            put(bsL,bsR, kbass(root-12+off, e8*0.92, 0.38*(0.6+0.4*g)), t0+j*e8, 1.0, 0.0)
    # 아르페지오 / 크리스털
    notes=sorted(chord)
    if drop or floor or build or Bsec or outro:
        for s in range(16):
            mi=notes[s%len(notes)]+(12 if s%len(notes)>=3 else 0)
            put(oL,oR, ds.pluck(m(mi+12),0.10,0.055*g,decay=0.07), t0+s*e16, 1.0, 0.22*((s%2)*2-1), 0.10)
    elif icy:
        for s in range(8):
            mi=notes[s%len(notes)]+12+(12 if s>=4 else 0)
            put(oL,oR, crystal(mi, 0.9, 0.08), t0+s*e8, 1.0, 0.28*((s%2)*2-1), 0.5)
    elif intro:
        for s in range(8):
            put(oL,oR, crystal(notes[s%len(notes)]+12, 0.8, 0.06), t0+s*e8,1.0,0.25*((s%2)*2-1),0.45)
    # 드럼
    if full or (build and i%1==0):
        for bt in range(4):
            put(oL,oR, pkick(0.95 if bt==0 else 0.82), t0+bt*spb,1.0,0.0); kick_times.append(t0+bt*spb)
        for bt in (1,3): put(oL,oR, ds.clap(0.16,0.5,seed=i*4+bt), t0+bt*spb,1.0,0.05,0.12)
        for s in range(8): put(oL,oR, ds.hat(0.03,0.10 if s%2 else 0.05,seed=i*8+s,fc=8200), t0+s*e8,1.0,-0.12,0.03)
    elif floor:
        for bt in range(4): put(oL,oR, pkick(0.8 if bt==0 else 0.7), t0+bt*spb,1.0,0.0); kick_times.append(t0+bt*spb)
        for bt in (1,3): put(oL,oR, ds.clap(0.16,0.4,seed=i*4+bt), t0+bt*spb,1.0,0.05,0.12)
        for s in range(8): put(oL,oR, ds.hat(0.03,0.06,seed=i*8+s,fc=8500), t0+s*e8,1.0,-0.1,0.03)
    elif icy:
        put(oL,oR, pkick(0.7), t0,1.0,0.0); kick_times.append(t0)
        if i%2==1: put(oL,oR, ds.clap(0.16,0.32,seed=i+99), t0+2*spb,1.0,0.05,0.22)

# ── 멜로디 배치 ──
place_mel_block(A_HOOK, 12, 28, bell, 0.10, 0.10, 0.18)     # A플로어(은은)
place_mel_block(A_HOOK, 28, 44, bell, 0.17, 0.10, 0.18)     # A드롭(풀)
place_mel_block(B_MEL, 56, 72, bell, 0.15, 0.12, 0.16)      # B코러스
place_mel_block(A_HOOK, 72, 88, bell, 0.13, 0.10, 0.18)     # A버스
place_mel_block(A_HOOK, 100, 136, bell, 0.18, 0.10, 0.18)   # 파이널

# ── 라이저·크래시(섹션 경계) ──
for sbar in (10, 28, 54, 56, 98, 100):
    put(oL,oR, riser(bar*2.0, 0.36, seed=sbar), (sbar-2)*bar, 1.0, 0.0, 0.05)
for sbar in (12, 28, 56, 100):
    put(oL,oR, crash(1.4,0.40,seed=sbar+50), sbar*bar, 1.0, 0.0, 0.25)

# ── 아웃트로: C장조 해결 + 승리 벨 + 링아웃 ──
ts=136*bar
put(oL,oR, pkick(1.0), ts,1.0,0.0); kick_times.append(ts)
put(oL,oR, crash(1.8,0.5,seed=221), ts,1.0,0.0,0.3)
put(chL,chR, supersaw([60,64,67,72,76], bar*3.6, 0.32), ts,1.0,0.0,0.3)
put(bsL,bsR, kbass(24, bar*0.9, 0.5), ts,1.0,0.0)
for j,mi in enumerate([72,76,79,84]): put(oL,oR, bell(mi, 1.6, 0.17), ts+j*e8, 1.0, 0.0, 0.24)

# ── 사이드체인 ──
def sidechain(depth, tau=0.19, win=0.7):
    scv=np.ones(N); L=int(win*SR)
    for kt in sorted(set(kick_times)):
        i=int(kt*SR)
        if i>=N: continue
        seg=min(L,N-i); tt=np.arange(seg)/SR
        scv[i:i+seg]=np.minimum(scv[i:i+seg], 1-depth*np.exp(-tt/tau))
    return scv
sc_ch=sidechain(0.78); sc_bs=sidechain(0.38)
L = oL + chL*sc_ch + bsL*sc_bs
R = oR + chR*sc_ch + bsR*sc_bs

# ── 마스터(카와이) ──
st=ds.master_chain(L,R,rev,rev_wet=0.28,wow=False,crackle_amp=0.0,crackle_density=0,
   sat_drive=1.18,widen_amt=0.34,master_lp=18500,hi_shelf=0.22,hp_fc=30,limit_ceiling=0.97,peak_ceiling=0.99,
   target_dbfs=-11.0,fade_in=0.0,fade_out=0.0,tot_samples=N)
out=np.clip(st,-0.999,0.999)
xf=int(0.003*SR); out[:xf]*= (np.linspace(0,1,xf)[:,None] if out.ndim>1 else np.linspace(0,1,xf))
of=int(2.4*SR); fade=np.linspace(1,0,of)**0.8
out[-of:]= out[-of:]*(fade[:,None] if out.ndim>1 else fade)

HERE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(HERE,'hyak_ep7_fullver.wav')
ds.write_wav(OUT,out)
peak=float(np.max(np.abs(out)))
mono = out.mean(1) if out.ndim>1 else out
def rms_db(a): return 20*np.log10(np.sqrt(np.mean(a**2))+1e-9)
print(f"[OK] {OUT} peak={peak:.3f} len={len(out)/SR:.3f}s clip={int(np.sum(np.abs(out)>0.999))} nan={bool(np.any(~np.isfinite(out)))}")
for name,(b0,b1) in {'intro':(0,4),'A-floor':(12,28),'A-drop':(28,44),'break1':(44,52),
                     'B':(56,72),'A-verse':(72,88),'final':(100,136)}.items():
    print(f"    {name:<9} {rms_db(mono[int(b0*bar*SR):int(b1*bar*SR)]):6.2f} dB")
