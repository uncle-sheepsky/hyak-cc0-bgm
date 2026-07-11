# Hyak ep3 BGM 풀버전 — 수박게임 편. 180BPM, 120마디(4/4) = 160.000s.
#   숏폼(18마디 24s 영상싱크 루프)의 음악 DNA(CHORDS Dm–Bb–C–A + ASCEND 리드)를 유지하되,
#   영상 싱크(콜드오픈·나레이션 진입·드롭 프레임)를 버리고 **완결형 곡 구조**로 재편곡.
#   구조: 인트로-빌드-버스A-코러스A-브레이크1-빌드2-코러스B-버스B-브레이크2-빌드3-파이널코러스-아웃트로.
#   루프 아님 → half-open 블립마스킹 대신 자연스러운 엔딩. 순수 hyak_synth 코드합성(외부샘플 0, CC0).
import numpy as np, sys, os, wave
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '음원'))
from hyak_synth import (SR, m2f, hard_kick, closed_hat, clap, noise_riser, noise_impact,
                        sub_bass, super_saw_lead, pluck_arp, bleat_hit, sidechain_env, limiter, soft_clip)

BPM = 180.0
BEAT = 60.0 / BPM
BAR = BEAT * 4                 # 1.333333s
N_BARS = 120
DUR = BAR * N_BARS             # 160.000000s
N = int(round(DUR * SR))
print(f"[i] ep3 fullver BPM={BPM} bar={BAR:.6f}s dur={DUR:.6f}s N={N}")

mix = np.zeros(N)
melodic = np.zeros(N)
kick_times = []

def place(buf, sig, t):
    i0 = int(round(t * SR)); i1 = min(N, i0 + len(sig))
    if i0 < N and i1 > i0: buf[i0:i1] += sig[:i1 - i0]
def bar_time(bar, sub=0): return bar * BAR + sub * (BEAT / 2.0)

# ── 음악 DNA (숏폼서 계승) ─────────────────────────────────────────────
CHORDS = [
    {"bass": 38, "tones": [62, 65, 69]},   # Dm
    {"bass": 34, "tones": [58, 62, 65]},   # Bb
    {"bass": 36, "tones": [60, 64, 67]},   # C
    {"bass": 33, "tones": [61, 64, 69]},   # A(maj)
]
ASCEND = [
    [62, 65, 69, 74, 69, 74, 77, 81],
    [58, 62, 65, 70, 65, 70, 74, 77],
    [60, 64, 67, 72, 67, 72, 76, 79],
    [61, 64, 69, 73, 69, 73, 76, 81],
]
# 콜-리스폰스 확보용 하강 응답구(버스 2패스째 변주)
DESCEND = [
    [81, 77, 74, 69, 74, 69, 65, 62],
    [77, 74, 70, 65, 70, 65, 62, 58],
    [79, 76, 72, 67, 72, 67, 64, 60],
    [81, 76, 73, 69, 73, 69, 64, 61],
]

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
        f = m2f(CHORDS[bar % 4]["bass"])
        if whole:
            place(melodic, sub_bass(f, BAR * 0.97, amp=amp), bar_time(bar))
        else:
            for beat in range(4):
                place(melodic, sub_bass(f, BEAT * 0.98, amp=amp), bar_time(bar, beat * 2))

def lay_lead(bars, seq=ASCEND, bright=8200, amp=0.56):
    for bar in bars:
        for e, deg in enumerate(seq[bar % 4]):
            place(melodic, super_saw_lead(m2f(deg), BEAT / 2 * 0.9, amp=amp, bright=bright), bar_time(bar, e))

def lay_arp(bars, amp=0.30):
    for bar in bars:
        tones = CHORDS[bar % 4]["tones"]
        for s in range(16):
            place(melodic, pluck_arp(m2f(tones[s % 3] + 12), BEAT / 4.0 * 0.85, amp=amp), bar * BAR + s * (BEAT / 4.0))

def lay_open_hats(bars, amp=0.32):
    for bar in bars:
        for e in (1, 3, 5, 7):
            place(mix, closed_hat(dur=0.11, amp=amp, seed=500 + bar * 8 + e), bar_time(bar, e))

def lay_breakdown_motif(bars):
    motif = [69, 72, 76, 72]
    for k, bar in enumerate(bars):
        deg = motif[k % 4]
        place(melodic, bleat_hit(m2f(deg), BEAT * 1.6, amp=0.30), bar_time(bar, 0))
        place(melodic, bleat_hit(m2f(deg + 3), BEAT * 1.2, amp=0.20), bar_time(bar, 4))

# ══ 곡 구조 (120마디) ═══════════════════════════════════════════════════
# 0-3 인트로
place(mix, noise_riser(BAR * 4, amp=0.55, fc_start=250, fc_end=6000, seed=11), bar_time(0))
for b, deg in [(0, 74), (1, 77), (2, 79), (3, 81)]:
    place(melodic, bleat_hit(m2f(deg), BEAT * 0.9, amp=0.22), bar_time(b, 0))

# 4-7 빌드
lay_drums(range(4, 8), with_clap=False, hat=0.22)
place(mix, noise_impact(amp=0.65, seed=21), bar_time(8) - 0.02)

# 8-23 버스A ×2 (콜=ASCEND / 리스폰스=DESCEND 교대)
for bar in range(8, 24):
    seq = ASCEND if (bar // 4) % 2 == 0 else DESCEND
    lay_lead([bar], seq=seq, bright=6200, amp=0.44)
lay_drums(range(8, 24))
lay_bass(range(8, 24))

# 24-39 코러스A ×2
lay_drums(range(24, 40))
lay_bass(range(24, 40))
lay_lead(range(24, 40), bright=8200, amp=0.56)
lay_arp(range(24, 40), amp=0.32)
lay_open_hats(range(24, 40), amp=0.32)

# 40-47 브레이크다운1(하프타임, 숨쉬기)
lay_halftime(range(40, 48))
lay_bass(range(40, 48), amp=0.55, whole=True)
lay_breakdown_motif(range(40, 48))

# 48-51 빌드2
lay_drums(range(48, 52), with_clap=False, hat=0.24)
place(mix, noise_riser(BAR * 4, amp=0.6, fc_start=300, fc_end=8000, seed=41), bar_time(48))
place(mix, noise_impact(amp=0.75, seed=42), bar_time(52) - 0.02)

# 52-67 코러스B ×2
lay_drums(range(52, 68))
lay_bass(range(52, 68), amp=0.9)
lay_lead(range(52, 68), bright=8600, amp=0.58)
lay_arp(range(52, 68), amp=0.34)
lay_open_hats(range(52, 68), amp=0.34)

# 68-83 버스B/인터루드 (리드 옥타브 낮춰 대비)
for bar in range(68, 84):
    seq = DESCEND if (bar // 4) % 2 == 0 else ASCEND
    lay_lead([bar], seq=seq, bright=6600, amp=0.46)
lay_drums(range(68, 84), hat=0.26)
lay_bass(range(68, 84), amp=0.8)
lay_arp(range(68, 84), amp=0.20)

# 84-91 브레이크다운2
lay_halftime(range(84, 92))
lay_bass(range(84, 92), amp=0.55, whole=True)
lay_breakdown_motif(range(84, 92))

# 92-95 빌드3
lay_drums(range(92, 96), with_clap=False, hat=0.26)
place(mix, noise_riser(BAR * 4, amp=0.65, fc_start=350, fc_end=9000, seed=93), bar_time(92))
place(mix, noise_impact(amp=0.8, seed=94), bar_time(96) - 0.02)

# 96-115 파이널 코러스 (최대 에너지, 20마디)
lay_drums(range(96, 116))
lay_bass(range(96, 116), amp=0.98)
lay_lead(range(96, 116), bright=9200, amp=0.62)
lay_arp(range(96, 116), amp=0.38)
lay_open_hats(range(96, 116), amp=0.36)
for bar in (96, 100, 104, 108, 112):
    place(mix, noise_impact(amp=0.35, seed=700 + bar), bar_time(bar))

# 116-119 아웃트로(자연 마무리)
lay_drums(range(116, 119), with_clap=False)
lay_bass(range(116, 119), amp=0.8)
place(mix, hard_kick(amp=1.0, drive=1.4), bar_time(119, 0)); kick_times.append(bar_time(119, 0))
place(mix, noise_impact(dur=1.2, amp=0.8, seed=99), bar_time(119, 0))

# ── 사이드체인 + 믹스 ────────────────────────────────────────────────────
duck = sidechain_env(N, kick_times, depth=0.62, attack=0.002, release=0.10)
melodic *= duck
master = mix * 0.85 + melodic * 0.95
master = soft_clip(master, drive=1.02)
master = limiter(master, ceiling=0.92)

seam_out = int(0.08 * SR)
master[-seam_out:] *= np.linspace(1, 0, seam_out)
si = int(0.005 * SR); master[:si] *= np.linspace(0, 1, si)

def rms_db(a): return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9)
peak = np.max(np.abs(master))
print(f"[i] peak={peak:.4f} rms={rms_db(master):.2f}dB clip>0.999={int(np.sum(np.abs(master)>0.999))} nan={bool(np.any(~np.isfinite(master)))}")
for name, (b0, b1) in {'intro':(0,4),'verseA':(8,24),'chorusA':(24,40),'break1':(40,48),
                       'chorusB':(52,68),'verseB':(68,84),'final':(96,116)}.items():
    i0, i1 = int(b0*BAR*SR), int(b1*BAR*SR)
    print(f"    {name:<9} {rms_db(master[i0:i1]):6.2f} dB")

stereo = np.stack([master, master], 1)
i16 = np.clip(stereo * 32767, -32768, 32767).astype(np.int16)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hyak_ep3_fullver.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(i16.tobytes())
print(f"[OK] saved {out} ({N} spl, {N/SR:.6f}s)")
