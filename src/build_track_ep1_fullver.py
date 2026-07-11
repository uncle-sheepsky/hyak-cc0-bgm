# Hyak ep1 BGM 풀버전 — 리듬게임 편. 180BPM, 120마디(4/4) = 160.000s.
#   구 96s(72마디) 완결본을 채널 풀버전 표준(2~3분)에 맞춰 120마디로 재확장.
#   음악 DNA(Am–F–C–G + CALL/RESPONSE 리드) 유지. 순수 hyak_synth 코드합성(외부샘플 0, CC0).
#   구조: 인트로-빌드-버스A-코러스A-브레이크1-빌드2-코러스B-버스B-브레이크2-빌드3-파이널-아웃트로.
import numpy as np, sys, os, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hyak_synth import (SR, m2f, hard_kick, closed_hat, clap, noise_riser, noise_impact,
                        sub_bass, super_saw_lead, pluck_arp, bleat_hit, sidechain_env, limiter, soft_clip)

BPM = 180.0
BEAT = 60.0 / BPM
BAR = BEAT * 4
N_BARS = 120
DUR = BAR * N_BARS            # 160.000000s
N = int(round(DUR * SR))
print(f"[i] ep1 fullver BPM={BPM} bar={BAR:.6f}s dur={DUR:.6f}s N={N}")

mix = np.zeros(N); melodic = np.zeros(N); kick_times = []
def place(buf, sig, t):
    i0 = int(round(t * SR)); i1 = min(N, i0 + len(sig))
    if i0 < N and i1 > i0: buf[i0:i1] += sig[:i1 - i0]
def bar_time(bar, sub=0): return bar * BAR + sub * (BEAT / 2.0)

CHORDS = [
    {"bass": 45, "tones": [69, 72, 76]},   # Am
    {"bass": 41, "tones": [65, 69, 72]},   # F
    {"bass": 48, "tones": [72, 76, 79]},   # C
    {"bass": 43, "tones": [67, 71, 74]},   # G
]
CALL = [
    [69, 72, 76, 72, 69, 72, 76, 81],
    [65, 69, 72, 69, 65, 69, 72, 77],
    [72, 76, 79, 76, 72, 76, 79, 84],
    [67, 71, 74, 71, 67, 71, 74, None],
]
RESPONSE = [
    [76, 72, 69, 72, 76, 74, 72, 71],
    [69, 65, 72, 69, 65, 64, 65, 69],
    [67, 64, 60, 64, 67, 72, 76, 79],
    [74, 71, 67, 74, 71, 67, 74, None],
]
SEQ = CALL + RESPONSE  # 8-bar

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

def lay_lead(bars, bright=8200, amp=0.56):
    for k, bar in enumerate(bars):
        pat = SEQ[k % 8]
        for e, deg in enumerate(pat):
            if deg is None: continue
            dur = BEAT / 2.0 * 0.92
            if e == 7: dur = BEAT * 0.9
            place(melodic, super_saw_lead(m2f(deg), dur, amp=amp, bright=bright), bar_time(bar, e))

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
for b, deg in [(0, 76), (1, 79), (2, 81), (3, 84)]:
    place(melodic, bleat_hit(m2f(deg), BEAT * 0.9, amp=0.22), bar_time(b, 0))
# 4-7 빌드
lay_drums(range(4, 8), with_clap=False, hat=0.22)
place(mix, noise_impact(amp=0.65, seed=21), bar_time(8) - 0.02)
# 8-23 버스A ×2
lay_drums(range(8, 24)); lay_bass(range(8, 24)); lay_lead(range(8, 24), bright=6200, amp=0.44)
# 24-39 코러스A ×2
lay_drums(range(24, 40)); lay_bass(range(24, 40)); lay_lead(range(24, 40), bright=8200, amp=0.56)
lay_arp(range(24, 40), amp=0.32); lay_open_hats(range(24, 40), amp=0.32)
# 40-47 브레이크1
lay_halftime(range(40, 48)); lay_bass(range(40, 48), amp=0.55, whole=True); lay_breakdown_motif(range(40, 48))
# 48-51 빌드2
lay_drums(range(48, 52), with_clap=False, hat=0.24)
place(mix, noise_riser(BAR * 4, amp=0.6, fc_start=300, fc_end=8000, seed=41), bar_time(48))
place(mix, noise_impact(amp=0.75, seed=42), bar_time(52) - 0.02)
# 52-67 코러스B ×2
lay_drums(range(52, 68)); lay_bass(range(52, 68), amp=0.9); lay_lead(range(52, 68), bright=8600, amp=0.58)
lay_arp(range(52, 68), amp=0.34); lay_open_hats(range(52, 68), amp=0.34)
# 68-83 버스B/인터루드
lay_drums(range(68, 84), hat=0.26); lay_bass(range(68, 84), amp=0.8); lay_lead(range(68, 84), bright=6600, amp=0.46)
lay_arp(range(68, 84), amp=0.20)
# 84-91 브레이크2
lay_halftime(range(84, 92)); lay_bass(range(84, 92), amp=0.55, whole=True); lay_breakdown_motif(range(84, 92))
# 92-95 빌드3
lay_drums(range(92, 96), with_clap=False, hat=0.26)
place(mix, noise_riser(BAR * 4, amp=0.65, fc_start=350, fc_end=9000, seed=93), bar_time(92))
place(mix, noise_impact(amp=0.8, seed=94), bar_time(96) - 0.02)
# 96-115 파이널 코러스
lay_drums(range(96, 116)); lay_bass(range(96, 116), amp=0.98); lay_lead(range(96, 116), bright=9200, amp=0.62)
lay_arp(range(96, 116), amp=0.38); lay_open_hats(range(96, 116), amp=0.36)
for bar in (96, 100, 104, 108, 112):
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
for name, (b0, b1) in {'intro':(0,4),'verseA':(8,24),'chorusA':(24,40),'break1':(40,48),
                       'chorusB':(52,68),'verseB':(68,84),'final':(96,116)}.items():
    i0, i1 = int(b0*BAR*SR), int(b1*BAR*SR)
    print(f"    {name:<9} {rms_db(master[i0:i1]):6.2f} dB")

stereo = np.stack([master, master], 1)
i16 = np.clip(stereo * 32767, -32768, 32767).astype(np.int16)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hyak_ep1_fullver.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(i16.tobytes())
print(f"[OK] saved {out} ({N} spl, {N/SR:.6f}s)")
