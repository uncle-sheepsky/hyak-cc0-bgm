# Hyak ep2 BGM 풀버전 — 테트리스 편. 180BPM, 120마디(4/4) = 160.000s.
#   숏폼은 duru ep33(코로베이니키 붐뱁) 포팅 wav를 잘라 썼으나, 풀버전은 **퍼블릭 도메인 멜로디
#   「코로베이니키」(러시아 민요, PD)를 hyak_synth로 자체 하드EDM 편곡** = 외부 wav 의존 제거·순수 코드합성.
#   CC0 유효(멜로디=PD, 편곡·반주·드럼 전부 코드합성, 외부샘플 0). 자기완결(duru 결합 없음).
#   구조: 인트로-빌드-A테마-A드롭-브레이크1-빌드2-A드롭2-B변주-브레이크2-빌드3-파이널-아웃트로.
import numpy as np, sys, os, wave
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '음원'))
from hyak_synth import (SR, m2f, hard_kick, closed_hat, clap, noise_riser, noise_impact,
                        sub_bass, super_saw_lead, pluck_arp, bleat_hit, sidechain_env, limiter, soft_clip)

BPM = 180.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
N_BARS = 120
DUR = BAR * N_BARS
N = int(round(DUR * SR))
print(f"[i] ep2 fullver BPM={BPM} bar={BAR:.6f}s dur={DUR:.6f}s N={N}")

mix = np.zeros(N); melodic = np.zeros(N); kick_times = []
def place(buf, sig, t):
    i0 = int(round(t * SR)); i1 = min(N, i0 + len(sig))
    if i0 < N and i1 > i0: buf[i0:i1] += sig[:i1 - i0]
def bar_time(bar, sub=0): return bar * BAR + sub * (BEAT / 2.0)

# ── 코로베이니키(테트리스 테마 A) — E단조, 8마디 프레이즈 ────────────────────
# 각 음 = (프레이즈 내 beat 오프셋, MIDI, 지속 beats). 8마디=32비트.
KOROB = [
    (0,76,1),(1,71,.5),(1.5,72,.5),(2,74,1),(3,72,.5),(3.5,71,.5),      # bar1  E5 B4 C5 D5 C5 B4
    (4,69,1),(5,69,.5),(5.5,72,.5),(6,76,1),(7,74,.5),(7.5,72,.5),      # bar2  A4 A4 C5 E5 D5 C5
    (8,71,1.5),(9.5,72,.5),(10,74,1),(11,76,1),                          # bar3  B4 C5 D5 E5
    (12,72,1),(13,69,1),(14,69,1),                                       # bar4  C5 A4 A4 (rest)
    (16.5,74,1),(17.5,77,.5),(18,81,1),(19,79,.5),(19.5,77,.5),          # bar5  D5 F5 A5 G5 F5
    (20,76,1.5),(21.5,72,.5),(22,76,1),(23,74,.5),(23.5,72,.5),          # bar6  E5 C5 E5 D5 C5
    (24,71,1),(25,71,.5),(25.5,72,.5),(26,74,1),(27,76,1),               # bar7  B4 B4 C5 D5 E5
    (28,72,1),(29,69,1),(30,69,1),                                       # bar8  C5 A4 A4 (rest)
]
# 8마디 화성(테트리스 관용 하모나이제이션): Em B Em Em Am Em B Em
BASS = [40, 47, 40, 40, 45, 40, 47, 40]
TONES = [[64,67,71],[59,63,66],[64,67,71],[64,67,71],[69,72,76],[64,67,71],[59,63,66],[64,67,71]]

def lay_drums(bars, kamp=1.0, hat=0.30, with_clap=True, hseed=200):
    for bar in bars:
        for beat in range(4):
            tk = bar_time(bar, beat * 2); place(mix, hard_kick(amp=kamp), tk); kick_times.append(tk)
        for e in range(8):
            place(mix, closed_hat(amp=hat, seed=hseed + bar * 8 + e), bar_time(bar, e))
        if with_clap:
            place(mix, clap(amp=0.42, seed=300 + bar), bar_time(bar, 2))
            place(mix, clap(amp=0.42, seed=340 + bar), bar_time(bar, 6))

def lay_halftime(bars, kamp=0.75):
    for bar in bars:
        tk = bar_time(bar, 0); place(mix, hard_kick(amp=kamp, drive=1.2), tk); kick_times.append(tk)
        place(mix, clap(amp=0.30, seed=360 + bar), bar_time(bar, 4))

def lay_bass(bars, amp=0.85, whole=False):
    for bar in bars:
        f = m2f(BASS[bar % 8])
        if whole:
            place(melodic, sub_bass(f, BAR * 0.97, amp=amp), bar_time(bar))
        else:
            for beat in range(4):
                place(melodic, sub_bass(f, BEAT * 0.98, amp=amp), bar_time(bar, beat * 2))

def lay_melody(block_start, bright=8200, amp=0.56, oct_shift=0):
    """block_start 마디부터 8마디에 걸쳐 코로베이니키 프레이즈 1회."""
    for (b, mi, d) in KOROB:
        t = block_start * BAR + b * BEAT
        place(melodic, super_saw_lead(m2f(mi + oct_shift), BEAT * d * 0.92, amp=amp, bright=bright), t)

def lay_arp(bars, amp=0.30):
    for bar in bars:
        tones = TONES[bar % 8]
        for s in range(16):
            place(melodic, pluck_arp(m2f(tones[s % 3] + 12), BEAT / 4.0 * 0.85, amp=amp), bar * BAR + s * (BEAT / 4.0))

def lay_open_hats(bars, amp=0.32):
    for bar in bars:
        for e in (1, 3, 5, 7):
            place(mix, closed_hat(dur=0.11, amp=amp, seed=500 + bar * 8 + e), bar_time(bar, e))

def lay_breakdown_motif(bars):
    motif = [64, 67, 71, 67]  # Em
    for k, bar in enumerate(bars):
        deg = motif[k % 4]
        place(melodic, bleat_hit(m2f(deg), BEAT * 1.6, amp=0.30), bar_time(bar, 0))
        place(melodic, bleat_hit(m2f(deg + 3), BEAT * 1.2, amp=0.20), bar_time(bar, 4))

# ══ 곡 구조 (120마디) ═══════════════════════════════════════════════════
# 0-3 인트로
place(mix, noise_riser(BAR * 4, amp=0.55, fc_start=250, fc_end=6000, seed=11), bar_time(0))
for b, deg in [(0, 76), (1, 79), (2, 81), (3, 83)]:
    place(melodic, bleat_hit(m2f(deg), BEAT * 0.9, amp=0.22), bar_time(b, 0))
# 4-7 빌드
lay_drums(range(4, 8), with_clap=False, hat=0.22)
place(mix, noise_impact(amp=0.65, seed=21), bar_time(8) - 0.02)
# 8-15 A테마(멜로디 은은, 드럼 진입) — 8마디 프레이즈 1회
lay_drums(range(8, 16)); lay_bass(range(8, 16)); lay_melody(8, bright=6200, amp=0.46)
# 16-23 A드롭(풀) — 프레이즈 1회 + 아르페지오
lay_drums(range(16, 24)); lay_bass(range(16, 24), amp=0.9); lay_melody(16, bright=8400, amp=0.58)
lay_arp(range(16, 24), amp=0.32); lay_open_hats(range(16, 24), amp=0.32)
# 24-31 브레이크1(하프타임)
lay_halftime(range(24, 32)); lay_bass(range(24, 32), amp=0.55, whole=True); lay_breakdown_motif(range(24, 32))
# 32-35 빌드2
lay_drums(range(32, 36), with_clap=False, hat=0.24)
place(mix, noise_riser(BAR * 4, amp=0.6, fc_start=300, fc_end=8000, seed=41), bar_time(32))
place(mix, noise_impact(amp=0.75, seed=42), bar_time(36) - 0.02)
# 36-51 A드롭2 ×2 (16마디 = 프레이즈 2회)
lay_drums(range(36, 52)); lay_bass(range(36, 52), amp=0.9)
lay_melody(36, bright=8600, amp=0.58); lay_melody(44, bright=8600, amp=0.58)
lay_arp(range(36, 52), amp=0.34); lay_open_hats(range(36, 52), amp=0.34)
# 52-67 B변주(멜로디 옥타브 아래 + 아르페지오 강조)
lay_drums(range(52, 68), hat=0.26); lay_bass(range(52, 68), amp=0.8)
lay_melody(52, bright=6600, amp=0.48, oct_shift=-12); lay_melody(60, bright=6600, amp=0.48, oct_shift=-12)
lay_arp(range(52, 68), amp=0.26)
# 68-75 브레이크2
lay_halftime(range(68, 76)); lay_bass(range(68, 76), amp=0.55, whole=True); lay_breakdown_motif(range(68, 76))
# 76-79 빌드3
lay_drums(range(76, 80), with_clap=False, hat=0.26)
place(mix, noise_riser(BAR * 4, amp=0.65, fc_start=350, fc_end=9000, seed=93), bar_time(76))
place(mix, noise_impact(amp=0.8, seed=94), bar_time(80) - 0.02)
# 80-115 파이널(프레이즈 반복 최대 에너지, 옥타브 상단 강조)
for blk in (80, 88, 96, 104):
    lay_melody(blk, bright=9200, amp=0.62)
lay_melody(112, bright=9200, amp=0.62)  # partial(112-119 중 앞부분)
lay_drums(range(80, 116)); lay_bass(range(80, 116), amp=0.98)
lay_arp(range(80, 116), amp=0.38); lay_open_hats(range(80, 116), amp=0.36)
for bar in (80, 88, 96, 104, 112):
    place(mix, noise_impact(amp=0.35, seed=700 + bar), bar_time(bar))
# 116-119 아웃트로
lay_drums(range(116, 119), with_clap=False); lay_bass(range(116, 119), amp=0.8)
place(mix, hard_kick(amp=1.0, drive=1.4), bar_time(119, 0)); kick_times.append(bar_time(119, 0))
place(mix, noise_impact(dur=1.2, amp=0.8, seed=99), bar_time(119, 0))

# ── 믹스 ────────────────────────────────────────────────────────────────
duck = sidechain_env(N, kick_times, depth=0.65, attack=0.002, release=0.10)
melodic *= duck
master = mix * 0.85 + melodic * 0.95
master = soft_clip(master, drive=1.02)
master = limiter(master, ceiling=0.92)
seam_out = int(0.08 * SR); master[-seam_out:] *= np.linspace(1, 0, seam_out)
si = int(0.005 * SR); master[:si] *= np.linspace(0, 1, si)

def rms_db(a): return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9)
print(f"[i] peak={np.max(np.abs(master)):.4f} rms={rms_db(master):.2f}dB clip>0.999={int(np.sum(np.abs(master)>0.999))} nan={bool(np.any(~np.isfinite(master)))}")
for name, (b0, b1) in {'intro':(0,4),'Atheme':(8,16),'Adrop':(16,24),'break1':(24,32),
                       'Adrop2':(36,52),'Bvar':(52,68),'final':(80,116)}.items():
    i0, i1 = int(b0*BAR*SR), int(b1*BAR*SR)
    print(f"    {name:<9} {rms_db(master[i0:i1]):6.2f} dB")

stereo = np.stack([master, master], 1)
i16 = np.clip(stereo * 32767, -32768, 32767).astype(np.int16)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hyak_ep2_fullver.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(i16.tobytes())
print(f"[OK] saved {out} ({N} spl, {N/SR:.6f}s)")
