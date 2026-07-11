# Hyak ep5 BGM 풀버전 — 2048 퍼즐 편. 210BPM, 140마디(4/4) = 160.000s.
#   숏폼(build_track_ep5.py)의 음악 DNA를 유지하되, 영상 싱크(나레이션·CD 로딩바·드롭 프레임)를
#   버리고 **완결형 곡 구조**로 재편곡. 구조 뼈대는 ep3 풀버전 템플릿에서 계승:
#   인트로-빌드-버스A-코러스A-브레이크1-빌드2-코러스B-버스B-브레이크2-빌드3-파이널-아웃트로.
#   ★ep5 정체성 보존:
#     - 화성 Am–G–F–E (4음 8va 와이드 보이싱, 하모닉마이너 V=E[G#]), 후반 1/3 +2반음 키업.
#     - 벨 리드(pluck_arp) 하강 가이드톤 컨투어 BELL.
#     - 슈퍼소 코드찹(FB 게이트) + pad/reverb 앰비언트 베드.
#     - load_blip(고속감쇠 사인+옥타브 배음) = 퍼즐 모티프 → 빌드 구간 시그니처 ARP/악센트
#       (단 영상싱크 로딩바 기믹 아님, 순수 음악 모티프).
#   ep3 화성(Dm–Bb–C–A)은 사용하지 않음 — 이 곡은 ep5처럼 들려야 함.
#   루프 아님 → 자연스러운 엔딩. 순수 hyak_synth 코드합성(외부 wav 0, CC0).
import numpy as np, sys, os, wave
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '음원'))
from hyak_synth import (SR, m2f, adsr, lp, hp, soft_clip, sub_bass, super_saw_lead,
                        pluck_arp, hard_kick, clap, closed_hat, bleat_hit, noise_riser,
                        noise_impact, sidechain_env, limiter)

BPM = 210.0
BEAT = 60.0 / BPM              # 0.285714s
BAR = BEAT * 4                 # 1.142857s
N_BARS = 140
DUR = BAR * N_BARS             # 160.000000s
N = int(round(DUR * SR))       # 7,056,000
assert N == 7056000, N
print(f"[i] ep5 fullver BPM={BPM} beat={BEAT:.6f}s bar={BAR:.6f}s dur={DUR:.6f}s N={N}")
RNG = np.random.default_rng(20260711)

mix = np.zeros(N)       # 드럼 + fx(비-덕킹)
melodic = np.zeros(N)   # 베이스 + 리드 + 코드찹 + 블립(사이드체인 덕킹)
amb = np.zeros(N)       # 앰비언트 패드 베드(리버브 대상, 약펌프)
kick_times = []

def place(buf, sig, t):
    i0 = int(round(t * SR)); i1 = min(N, i0 + len(sig))
    if i0 < N and i1 > i0: buf[i0:i1] += sig[:i1 - i0]
def bar_time(bar, sub=0): return bar * BAR + sub * (BEAT / 2.0)   # sub = 8분 인덱스
def bt(bar, beat=0.0): return bar * BAR + beat * BEAT            # beat = 4분(소수 허용)

# ── 음악 DNA (숏폼 build_track_ep5서 계승) ─────────────────────────────────
#   王道진행 파생 Am–G–F–E: vim7 귀결(단조 중력)+하모닉마이너 V(E=G#) 색채.
CHORDS = [
    {"root": 45, "tones": [69, 72, 76, 81]},   # Am add8va (A C E A)
    {"root": 43, "tones": [67, 71, 74, 79]},   # G  (G B D G)
    {"root": 41, "tones": [65, 69, 72, 77]},   # F  (F A C F)
    {"root": 40, "tones": [64, 68, 71, 76]},   # E  (E G# B E) — 하모닉마이너 V
]
KEYUP_FROM = 100                # ★파이널(후반 1/3)부터 +2반음 키업 = 상승·승리 밝음
def _kup(bar): return 2 if bar >= KEYUP_FROM else 0
def ch(bar):
    c = CHORDS[bar % 4]; k = _kup(bar)
    return {"root": c["root"] + k, "tones": [t + k for t in c["tones"]]}

# 벨 리드 = 하강 가이드톤 컨투어(코드톤 관통, 정본 아치 회피)
BELL = [76, 74, 72, 71, 74, 72, 71, 69]     # E D C B / D C B A
# load_blip 퍼즐 모티프용 A 하모닉마이너 상승 스케일
BLIP_SCALE = [69, 71, 72, 74, 76, 77, 80, 81]   # A B C D E F G# A

# ── ep5 커스텀 신스(verbatim 계승) ────────────────────────────────────────
def pad(midi, dur, amp=0.4, a=0.5, r=0.8, fc=2400, warm=True):
    """디튠 소 앙상블 패드. LFO/비브라토 없음(정적 디튠만 = 아날로그 온기)."""
    n = int(dur * SR); t = np.arange(n) / SR; f = m2f(midi); s = np.zeros(n)
    for dc in (-6, -2.5, 0, 2.5, 6):
        ff = f * 2 ** (dc / 1200.0); ph = RNG.random()
        s += 2.0 * ((ff * t + ph) % 1.0) - 1.0
    s /= 5.0
    if warm:
        s = s * 0.8 + soft_clip(s, 1.15) * 0.2
    s = lp(s, fc, order=4)
    return (s * adsr(n, a, 0.2, 0.8, r, sus=0.8) * amp)[:n]

def tick(dur=0.09, amp=0.4, freq=1900):
    n = int(dur * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * freq * t) * np.exp(-t * 55)
    click = RNG.standard_normal(n) * np.exp(-t * 400) * 0.4
    return hp(body + click, 900, order=2) * amp

def reverb(x, mix=0.28, decay=0.72):
    """간이 Schroeder(4콤브+2올패스) = 앰비언트 공간감. 저레벨 베드에만 적용."""
    combs = [(1687, decay), (1601, decay - 0.02), (2053, decay - 0.04), (2251, decay - 0.06)]
    out = np.zeros_like(x)
    for d, g in combs:
        y = np.zeros_like(x); buf = np.zeros(d)
        for i in range(len(x)):
            v = x[i] + g * buf[i % d]; buf[i % d] = v; y[i] = v
        out += y
    out /= len(combs)
    for d, g in [(389, 0.7), (127, 0.7)]:
        y = np.zeros_like(out); buf = np.zeros(d)
        for i in range(len(out)):
            bv = buf[i % d]; v = out[i] + (-g) * bv; buf[i % d] = v; y[i] = g * v + bv
        out = y
    return x * (1 - mix) + out * mix

def load_blip(freq, dur=0.05, amp=0.2):
    """로딩 블립 = 고속감쇠 사인 + 옥타브/3배음(게임 블립). ep5 시그니처."""
    n = int(dur * SR); t = np.arange(n) / SR
    s = np.sin(2 * np.pi * freq * t) * np.exp(-t * 52)
    s += np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t * 70) * 0.55
    s += np.sin(2 * np.pi * freq * 3 * t) * np.exp(-t * 90) * 0.25
    return hp(s * amp, 300, order=2)

# ── 슈퍼소 코드찹(와이드 보이싱, FB 싱코 게이트) ──────────────────────────
FB_PAT = [1, 1, 1, 0, 1, 1, 1, 1]           # ep5 셔플 게이트
def lay_chop(bars, amp=0.5, bright=8800, closed=False, air=True):
    for bar in bars:
        voic = ch(bar)["tones"]
        for sub in range(8):
            if not FB_PAT[sub]: continue
            t0 = bt(bar, (sub >> 1) + (sub & 1) * (2 / 3))    # 스윙 8분(오프비트 2/3)
            dur = (BEAT / 2) * 0.95
            for m_ in voic:
                s_ = super_saw_lead(m2f(m_), dur, amp=amp / len(voic),
                                    bright=(900 if closed else bright))
                env = adsr(len(s_), 0.004, 0.05, 0.6, 0.06, sus=0.6)
                place(melodic, s_[:len(env)] * env, t0)
                if air and not closed:
                    sa = super_saw_lead(m2f(m_ + 12), dur, amp=amp * 0.14 / len(voic), bright=9500)
                    place(melodic, sa, t0)

# ── 드럼·베이스·리드·앰비언트 레이어 헬퍼 (ep3 형태 계승) ─────────────────
def lay_drums(bars, kamp=0.85, hat=0.12, with_clap=True, four_floor=True, hseed=200):
    for bar in bars:
        if four_floor:
            for beat in range(4):
                tk = bar_time(bar, beat * 2)
                place(mix, hard_kick(amp=kamp, punch=55), tk); kick_times.append(tk)
        else:
            for beat in (0, 2):
                tk = bar_time(bar, beat * 2)
                place(mix, hard_kick(amp=kamp * 0.9, punch=55), tk); kick_times.append(tk)
        for e in range(8):
            place(mix, closed_hat(amp=hat, seed=hseed + bar * 8 + e), bar_time(bar, e))
        if with_clap:
            place(mix, clap(amp=0.44, seed=300 + bar), bar_time(bar, 2))
            place(mix, clap(amp=0.44, seed=340 + bar), bar_time(bar, 6))

def lay_halftime(bars, kamp=0.8):
    for bar in bars:
        tk = bar_time(bar, 0); place(mix, hard_kick(amp=kamp, drive=1.2, punch=52), tk); kick_times.append(tk)
        place(mix, clap(amp=0.34, seed=360 + bar), bar_time(bar, 4))

def lay_bass(bars, amp=0.85, whole=False, drive=1.4):
    for bar in bars:
        f = m2f(ch(bar)["root"])
        if whole:
            place(melodic, sub_bass(f, BAR * 0.97, amp=amp, drive=drive), bar_time(bar))
        else:
            for beat in range(4):
                place(melodic, sub_bass(f, BEAT * 0.98, amp=amp, drive=drive), bar_time(bar, beat * 2))

def lay_bell(bars, amp=0.20, octave=1):
    """벨 리드 하강 가이드톤(pluck_arp) = ep5 리드 정체성. 4분 그리드."""
    for bar in bars:
        for q in range(4):
            mi = BELL[(bar * 4 + q) % len(BELL)] + 12 * octave + _kup(bar)
            place(melodic, pluck_arp(m2f(mi), BEAT * 0.9, amp=amp, bright=6200), bt(bar, q))

def lay_open_hats(bars, amp=0.30):
    for bar in bars:
        for e in (1, 3, 5, 7):
            place(mix, closed_hat(dur=0.11, amp=amp, seed=500 + bar * 8 + e), bar_time(bar, e))

def lay_pad(bars, amp=0.40, ticks=False):
    for bar in bars:
        for mi in ch(bar)["tones"]:
            place(amb, pad(mi, BAR * 0.98, amp=amp * 0.42, a=0.6, fc=1900), bt(bar))
            place(amb, pad(mi + 12, BAR * 0.98, amp=amp * 0.26, a=0.8, fc=3000), bt(bar))
        if ticks:
            for b in range(4):
                place(amb, tick(amp=0.16), bt(bar, b))

def lay_break_motif(bars):
    """브레이크다운: 벨 스퀘어 악센트(bleat) + 홀드 베이스로 숨쉬기."""
    motif = [76, 72, 74, 71]
    for k, bar in enumerate(bars):
        deg = motif[k % 4] + _kup(bar)
        place(melodic, bleat_hit(m2f(deg), BEAT * 1.6, amp=0.26), bar_time(bar, 0))
        place(melodic, bleat_hit(m2f(deg - 5), BEAT * 1.2, amp=0.18), bar_time(bar, 4))

def lay_blip_arp(bars, amp=0.30, dense=False, climb=True):
    """★load_blip 퍼즐 모티프 = 빌드 구간 시그니처 ARP. 상승 스케일 = 긴장 축적.
       16분(dense) 또는 8분 그리드로 BLIP_SCALE를 훑어 올라감(퍼즐 '틱업' 정취)."""
    steps = 16 if dense else 8
    grid = 0.25 if dense else 0.5     # 16분 / 8분 (BEAT 단위)
    for j, bar in enumerate(bars):
        for s in range(steps):
            idx = (s + j * (steps // 2)) % len(BLIP_SCALE)
            oct_up = 12 if (climb and s >= steps // 2) else 0
            mi = BLIP_SCALE[idx] + oct_up + _kup(bar)
            a = amp * (0.7 + 0.3 * s / steps)          # 마디 내 상승 크레셴도
            place(melodic, load_blip(m2f(mi), dur=0.055, amp=a), bt(bar, s * grid))

# ══ 곡 구조 (140마디, 에너지 상승 + 브레이크 딥) ═══════════════════════════
# 0-3 인트로 (앰비언트 페이드인)
lay_pad(range(0, 4), amp=0.42, ticks=True)
place(mix, noise_riser(BAR * 4, amp=0.42, fc_start=200, fc_end=5000, seed=11), bar_time(0))
for b, deg in [(0, 74), (1, 76), (2, 77), (3, 81)]:
    place(melodic, bleat_hit(m2f(deg), BEAT * 0.9, amp=0.18), bar_time(b, 0))

# 4-11 빌드 (드럼 진입 + load_blip 퍼즐 모티프 상승)
lay_drums(range(4, 12), with_clap=False, four_floor=False, hat=0.10, kamp=0.78)
lay_bass(range(4, 12), amp=0.62)
lay_pad(range(4, 12), amp=0.30, ticks=True)
lay_blip_arp(range(4, 12), amp=0.24, dense=False)
lay_blip_arp(range(8, 12), amp=0.30, dense=True)          # 후반 가속
place(mix, noise_riser(BAR * 4, amp=0.5, fc_start=300, fc_end=7000, seed=21), bar_time(8))
place(mix, noise_impact(amp=0.6, seed=22), bar_time(12) - 0.02)

# 12-27 버스A ×4 (벨 리드 주도, 코드찹 은은, 4온플로어)
lay_drums(range(12, 28), hat=0.11)
lay_bass(range(12, 28), amp=0.82)
lay_bell(range(12, 28), amp=0.22)
lay_chop(range(12, 28), amp=0.24, bright=4200, closed=True, air=False)
lay_pad(range(12, 28), amp=0.20)

# 28-43 코러스A ×4 (풀 코드찹 + 벨 + 오픈햇)
lay_drums(range(28, 44), hat=0.13)
lay_bass(range(28, 44), amp=0.9)
lay_chop(range(28, 44), amp=0.50, bright=8600)
lay_bell(range(28, 44), amp=0.20)
lay_open_hats(range(28, 44), amp=0.30)
lay_pad(range(28, 44), amp=0.18)

# 44-51 브레이크1 (하프타임, 숨쉬기 — 코러스 아래로 딥)
lay_halftime(range(44, 52))
lay_bass(range(44, 52), amp=0.5, whole=True)
lay_break_motif(range(44, 52))
lay_pad(range(44, 52), amp=0.40, ticks=True)

# 52-55 빌드2 (짧은 재점화 + 블립)
lay_drums(range(52, 56), with_clap=False, four_floor=False, hat=0.11)
lay_bass(range(52, 56), amp=0.7)
lay_blip_arp(range(52, 56), amp=0.30, dense=True)
place(mix, noise_riser(BAR * 4, amp=0.58, fc_start=350, fc_end=8500, seed=41), bar_time(52))
place(mix, noise_impact(amp=0.72, seed=42), bar_time(56) - 0.02)

# 56-71 코러스B ×4 (에너지 상향)
lay_drums(range(56, 72), hat=0.14)
lay_bass(range(56, 72), amp=0.94)
lay_chop(range(56, 72), amp=0.55, bright=9000)
lay_bell(range(56, 72), amp=0.22)
lay_open_hats(range(56, 72), amp=0.33)
lay_pad(range(56, 72), amp=0.16)

# 72-87 버스B ×4 (리드 옥타브 낮춰 대비 + 블립 악센트)
lay_drums(range(72, 88), hat=0.12)
lay_bass(range(72, 88), amp=0.84)
lay_bell(range(72, 88), amp=0.20, octave=0)
lay_chop(range(72, 88), amp=0.26, bright=4600, closed=True, air=False)
lay_blip_arp(range(80, 88), amp=0.18, dense=False)        # 인터루드 텍스처
lay_pad(range(72, 88), amp=0.18)

# 88-95 브레이크2 (하프타임 딥)
lay_halftime(range(88, 96))
lay_bass(range(88, 96), amp=0.5, whole=True)
lay_break_motif(range(88, 96))
lay_pad(range(88, 96), amp=0.40, ticks=True)

# 96-99 빌드3 (최종 프리드롭, 블립 최대 가속)
lay_drums(range(96, 100), with_clap=False, four_floor=False, hat=0.13)
lay_bass(range(96, 100), amp=0.75)
lay_blip_arp(range(96, 100), amp=0.34, dense=True)
place(mix, noise_riser(BAR * 4, amp=0.65, fc_start=400, fc_end=9500, seed=93), bar_time(96))
place(mix, noise_impact(amp=0.82, seed=94), bar_time(100) - 0.02)

# 100-135 파이널 ×9 (최대 에너지, +2반음 키업 = 상승·승리, 36마디)
lay_drums(range(100, 136), hat=0.15, kamp=0.9)
lay_bass(range(100, 136), amp=0.98)
lay_chop(range(100, 136), amp=0.58, bright=9400)
lay_bell(range(100, 136), amp=0.24)
lay_open_hats(range(100, 136), amp=0.35)
lay_pad(range(100, 136), amp=0.16)
for bar in range(100, 136, 4):                            # 4마디마다 임팩트 강조
    place(mix, noise_impact(amp=0.32, seed=700 + bar), bar_time(bar))
# 파이널 후반 블립 카운터모티프(퍼즐 승리감)
lay_blip_arp(range(116, 132), amp=0.14, dense=False)

# 136-139 아웃트로 (자연 마무리)
lay_drums(range(136, 139), with_clap=False, hat=0.10)
lay_bass(range(136, 139), amp=0.8)
lay_bell(range(136, 139), amp=0.18)
lay_pad(range(136, 140), amp=0.36)
place(mix, hard_kick(amp=1.0, drive=1.4, punch=50), bar_time(139, 0)); kick_times.append(bar_time(139, 0))
place(mix, noise_impact(dur=1.2, amp=0.75, seed=99), bar_time(139, 0))
for mi in ch(139)["tones"]:                               # 최종 코드 링아웃
    place(amb, pad(mi, BAR * 1.5, amp=0.34, a=0.05, r=1.2, fc=2600), bar_time(139, 0))

# ── 사이드체인 + 믹스 (ep3 체인: sidechain → softclip → limiter) ──────────
kick_times = sorted(set(kick_times))
duck = sidechain_env(N, kick_times, depth=0.62, attack=0.002, release=0.11)
melodic *= duck
amb = reverb(amb, mix=0.28, decay=0.70)                   # 앰비언트 공간감
amb *= (0.7 + 0.3 * duck)                                 # 앰비언트 약펌프
master = mix * 0.85 + melodic * 0.95 + amb * 0.65
master = soft_clip(master, drive=1.02)
master = limiter(master, ceiling=0.92)

# 자연 엔딩(루프 아님): 인트로 마이크로 페이드 + 아웃트로 링아웃 페이드
si = int(0.005 * SR); master[:si] *= np.linspace(0, 1, si)
of = int(1.0 * SR); master[-of:] *= np.linspace(1, 0, of) ** 0.8

# ── 메트릭 ────────────────────────────────────────────────────────────────
def rms_db(a): return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9)
peak = float(np.max(np.abs(master)))
clipc = int(np.sum(np.abs(master) > 0.999))
nan = bool(np.any(~np.isfinite(master)))
print(f"[i] peak={peak:.4f} rms={rms_db(master):.2f}dB clip>0.999={clipc} nan={nan}")
SECTIONS = {'intro': (0, 4), 'build': (4, 12), 'verseA': (12, 28), 'chorusA': (28, 44),
            'break1': (44, 52), 'build2': (52, 56), 'chorusB': (56, 72), 'verseB': (72, 88),
            'break2': (88, 96), 'build3': (96, 100), 'final': (100, 136), 'outro': (136, 140)}
sec_rms = {}
for name, (b0, b1) in SECTIONS.items():
    i0, i1 = int(b0 * BAR * SR), int(b1 * BAR * SR)
    sec_rms[name] = rms_db(master[i0:i1])
    print(f"    {name:<9} {sec_rms[name]:6.2f} dB")

# ── 저장 (스테레오 int16 44100) ───────────────────────────────────────────
stereo = np.stack([master, master], 1)
i16 = np.clip(stereo * 32767, -32768, 32767).astype(np.int16)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hyak_ep5_fullver.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(i16.tobytes())
print(f"[OK] saved {out} ({N} spl, {N / SR:.6f}s)")

# ── HARD REQUIREMENTS 자체 점검 ───────────────────────────────────────────
print("\n[CHECK]")
print(f"  peak<1.0 & clip==0     : {'PASS' if peak < 1.0 and clipc == 0 else 'FAIL'} (peak={peak:.4f}, clip={clipc})")
print(f"  nan==False             : {'PASS' if not nan else 'FAIL'}")
print(f"  N==7056000 (160.0s)    : {'PASS' if N == 7056000 else 'FAIL'} (N={N})")
asc = sec_rms['final'] > sec_rms['verseA']
dip1 = sec_rms['break1'] < sec_rms['chorusA'] and sec_rms['break1'] < sec_rms['chorusB']
dip2 = sec_rms['break2'] < sec_rms['chorusB'] and sec_rms['break2'] < sec_rms['final']
print(f"  final>verseA           : {'PASS' if asc else 'FAIL'} ({sec_rms['final']:.2f}>{sec_rms['verseA']:.2f})")
print(f"  breaks dip < chorus    : {'PASS' if dip1 and dip2 else 'FAIL'} "
      f"(b1={sec_rms['break1']:.2f} b2={sec_rms['break2']:.2f} chA={sec_rms['chorusA']:.2f} chB={sec_rms['chorusB']:.2f})")
