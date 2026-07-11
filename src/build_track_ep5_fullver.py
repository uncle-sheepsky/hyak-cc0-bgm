# Hyak ep5 BGM 풀버전 — 은하 충돌(galaxy collision) 편. 210BPM, 140마디(4/4) = 160.000s.
#   숏폼(ep5 v3 40s)의 음악 DNA(王道진행 Royal Road FM7add9–G7add9–Em7add9–Am7add9, F장조/Am 귀결 +
#     벨 리드 하강폭포 + 와이드 7th/9th 코드찹 + 엠비언트 패드 베드 상시 + Schroeder 리버브 + 뒤 1/3 +2 키업)를
#     그대로 계승하되, 영상 싱크(seam·나레이션 진입·드롭 프레임)를 버리고 **완결형 곡 구조**로 재편곡.
#   구조: 인트로-빌드-버스A-코러스A-브레이크1-빌드2-코러스B-버스B-브레이크2-빌드3-파이널-아웃트로.
#   루프 아님 → half-open 블립마스킹 대신 자연스러운 엔딩. 순수 hyak_synth 코드합성(외부샘플 0, CC0).
#   ★캐릭터 = COSMIC / royal-road / ambient (NOT ep3 하드스타일). 벨·패드·리버브가 전경, 하드킥은 리듬 엔진.
import numpy as np, sys, os, wave
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '음원'))
from hyak_synth import (SR, m2f, adsr, lp, hp, soft_clip, sub_bass, super_saw_lead,
                        pluck_arp, hard_kick, clap, closed_hat, noise_riser, noise_impact,
                        sidechain_env, limiter)

BPM = 210.0
BEAT = 60.0 / BPM
BAR = BEAT * 4                 # 60/210*4 = 1.142857142857s
N_BARS = 140
DUR = BAR * N_BARS             # 160.000000s
N = int(round(DUR * SR))       # 7,056,000 spl
assert N == 7056000, (N, DUR, BAR)
print(f"[i] ep5 fullver BPM={BPM} beat={BEAT:.6f}s bar={BAR:.6f}s dur={DUR:.6f}s N={N}")
RNG = np.random.default_rng(20260711)

# ── place / bar_time 헬퍼 (템플릿 계승; sub = 8분음표 단위 = BEAT/2) ──────────
def place(buf, sig, t):
    i0 = int(round(t * SR)); i1 = min(N, i0 + len(sig))
    if i0 < N and i1 > i0: buf[i0:i1] += sig[:i1 - i0]
def bar_time(bar, sub=0): return bar * BAR + sub * (BEAT / 2.0)

# ── 화성 (ep5 계승: 王道진행 Royal Road IVM7–V7–iiim7–vim7, F장조/Am 귀결) ────
#   7th/9th 와이드 보이싱 = bittersweet 코스믹 정석(트라이어드 아님). vim7(Am7)로 귀결 = 단조 중력+장조 색채.
CHORDS = [
    {"root": 41, "tones": [65, 69, 72, 76, 79]},   # FM7add9  (F A C E G)
    {"root": 43, "tones": [67, 71, 74, 77, 81]},   # G7add9   (G B D F A)
    {"root": 40, "tones": [64, 67, 71, 74, 78]},   # Em7add9  (E G B D F#)
    {"root": 45, "tones": [69, 72, 76, 79, 83]},   # Am7add9  (A C E G B)
]
# ★뒤 1/3(파이널) +2반음 키업(J-pop/전파 리프트) = 상승감 + 지문 이동
KEYUP_FROM = 100                # 파이널 코러스(100~135) = 곡 뒤 1/3
def _kup(bar): return 2 if bar >= KEYUP_FROM else 0
def ch(bar):
    c = CHORDS[bar % 4]; k = _kup(bar)
    return {"root": c["root"] + k, "tones": [t + k for t in c["tones"]]}

# ── 엠비언트 베드용 신스 (ep5 v3서 verbatim: 디튠 정적 소 패드 — LFO/비브라토 없음=울렁 X) ──
def pad(midi, dur, amp=0.4, a=0.5, r=0.8, fc=2400, warm=True):
    """디튠 소 앙상블 패드. LFO/비브라토 없음(정적 디튠만 = 아날로그 온기, 울렁 X)."""
    n = int(dur * SR); t = np.arange(n) / SR; f = m2f(midi); s = np.zeros(n)
    for dc in (-6, -2.5, 0, 2.5, 6):                 # 완만 정적 디튠(비브라토 아님)
        ff = f * 2 ** (dc / 1200.0); ph = RNG.random()
        s += 2.0 * ((ff * t + ph) % 1.0) - 1.0
    s /= 5.0
    if warm:                                          # 저역 배음 보강(따뜻한 몸통, 사인 아님=삼각 근사 소프트클립)
        s = s * 0.8 + soft_clip(s, 1.15) * 0.2
    s = lp(s, fc, order=4)
    return (s * adsr(n, a, 0.2, 0.8, r, sus=0.8) * amp)[:n]

def tick(dur=0.09, amp=0.4, freq=1900):
    n = int(dur * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * freq * t) * np.exp(-t * 55)
    click = RNG.standard_normal(n) * np.exp(-t * 400) * 0.4
    return hp(body + click, 900, order=2) * amp

# ── 간이 리버브(Schroeder: 4콤브+2올패스) = 엠비언트 우주 공간감 (ep5 v3서 verbatim) ──
def reverb(x, mix=0.28, decay=0.72):
    combs = [(1687, decay), (1601, decay - 0.02), (2053, decay - 0.04), (2251, decay - 0.06)]
    out = np.zeros_like(x)
    for d, g in combs:
        y = np.zeros_like(x); buf = np.zeros(d)
        for i in range(len(x)):
            v = x[i] + g * buf[i % d]; buf[i % d] = v; y[i] = v
        out += y
    out /= len(combs)
    for d, g in [(389, 0.7), (127, 0.7)]:               # 올패스
        y = np.zeros_like(out); buf = np.zeros(d)
        for i in range(len(out)):
            bv = buf[i % d]; v = out[i] + (-g) * bv; buf[i % d] = v + 0 * bv; y[i] = g * v + bv
        out = y
    return x * (1 - mix) + out * mix

# ── 퓨처베이스/코스믹 코드찹(와이드 9th, 싱코 게이트) — ep5 지문 게이트 ────────
FB_PAT = [1, 0, 1, 0, 1, 1, 0, 1]                        # ★ep5 게이트
def lay_fb_chop(buf, bar, amp=0.5, bright=8800, closed=False):
    c = ch(bar); voic = c["tones"]                        # 7th/9th 와이드 보이싱(이미 5음)
    for sub in range(8):
        if not FB_PAT[sub]: continue
        t0 = bar_time(bar, sub)                            # sub = 8분음표 인덱스
        dur = (BEAT / 2) * 0.95
        for m_ in voic:
            s_ = super_saw_lead(m2f(m_), dur, amp=amp / len(voic), bright=(900 if closed else bright))
            env = adsr(len(s_), 0.004, 0.05, 0.6, 0.06, sus=0.6)   # 릴리즈컷(게이트 느낌)
            place(buf, s_[:len(env)] * env, t0)
            if not closed:                                # +1옥타브 에어
                sa = super_saw_lead(m2f(m_ + 12), dur, amp=amp * 0.14 / len(voic), bright=9500)
                place(buf, sa, t0)

# ── 벨 리드 하강폭포 라인 (ep5 계승: 코드톤 관통 하강, 정본 아치 회피) ──────────
BELL = [76, 74, 72, 71, 74, 72, 71, 69]     # E D C B / D C B A 하강 라인
def lay_bell(bars, amp=0.20, dense=False, oct_up=12):
    for bar in bars:
        steps = 8 if dense else 4
        for q in range(steps):
            mi = BELL[(bar * steps + q) % len(BELL)]
            dur = (BEAT / 2 if dense else BEAT) * 0.9
            place(lead, pluck_arp(m2f(mi + oct_up + _kup(bar)), dur, amp=amp),
                  bar_time(bar, q * (1 if dense else 2)))

# ═══ 레이어 버퍼 ═══════════════════════════════════════════════════════
amb = np.zeros(N); fb = np.zeros(N); lead = np.zeros(N); sub = np.zeros(N)
drums = np.zeros(N); fx = np.zeros(N); kick_times = []

def four_on_floor(bar, kamp=0.8, punch=55):
    for b in range(4):
        tk = bar_time(bar, b * 2); place(drums, hard_kick(0.24, amp=kamp, punch=punch), tk); kick_times.append(tk)
def halftime_kick(bar, kamp=0.72):
    for b in (0, 2):
        tk = bar_time(bar, b * 2); place(drums, hard_kick(0.26, amp=kamp, punch=52, drive=1.3), tk); kick_times.append(tk)
def claps(bar, amp=0.44):
    place(drums, clap(amp=amp, seed=300 + bar), bar_time(bar, 2))
    place(drums, clap(amp=amp, seed=340 + bar), bar_time(bar, 6))
def hats(bar, amp=0.12, n=8):
    for r in range(n): place(drums, closed_hat(amp=amp, seed=500 + bar * 8 + r), bar_time(bar, r))
def open_hats(bar, amp=0.30):
    for e in (1, 3, 5, 7): place(drums, closed_hat(dur=0.11, amp=amp, seed=600 + bar * 8 + e), bar_time(bar, e))
def lay_bass(bars, amp=0.55, whole=False, drive=1.4):
    for bar in bars:
        f = m2f(ch(bar)["root"])
        if whole:
            place(sub, sub_bass(f, BAR * 0.98, amp=amp, drive=drive), bar_time(bar))
        else:
            for b in range(4):
                place(sub, sub_bass(f, BEAT * 0.95, amp=amp, drive=drive), bar_time(bar, b * 2))

# ── 엠비언트 패드 베드 (전 구간 상시; 섹션별 레벨만 조정 — ep5 정신) ──────────
def amb_amp(bar):
    if bar < 4:  return 0.44                 # 인트로 = 패드 전경
    if bar in range(44, 52) or bar in range(88, 96): return 0.46   # 브레이크 = 엠비언트 부상
    return 0.36
def lay_amb(bars):
    for bar in bars:
        c = ch(bar); aa = amb_amp(bar)
        for mi in c["tones"]:
            place(amb, pad(mi, BAR * 0.98, amp=aa * 0.42, a=0.6, fc=1900), bar_time(bar))       # 하단 온기
            place(amb, pad(mi + 12, BAR * 0.98, amp=aa * 0.26, a=0.8, fc=3000), bar_time(bar))   # 상단 에어

lay_amb(range(N_BARS))                        # ★패드 베드 = 전 140마디 상시

# ═══ 곡 구조 (140마디, 210BPM) ═══════════════════════════════════════════
# 0-3 인트로 (패드 + 벨 스파클 + 라이저)
place(fx, noise_riser(BAR * 4, amp=0.42, fc_start=200, fc_end=5000, seed=11), bar_time(0))
for b, deg in [(0, 76), (1, 79), (2, 81), (3, 83)]:
    place(lead, pluck_arp(m2f(deg + 12), BEAT * 1.4, amp=0.16), bar_time(b, 0))
for bar in range(0, 4):
    for b in range(4): place(amb, tick(amp=0.14), bar_time(bar, b * 2))

# 4-11 빌드 (4온플로어 킥 진입 = 숏폼과 동일 · 코드찹 필터 오픈 · 벨 상승)
for bar in range(4, 12):
    g = (bar - 4) / 7.0
    four_on_floor(bar, kamp=0.72 + 0.10 * g, punch=55)
    hats(bar, amp=0.09 + 0.06 * g)
    if bar >= 8: claps(bar, amp=0.34)
    lay_fb_chop(fb, bar, amp=0.18 + 0.16 * g, bright=(3200 + 5000 * g), closed=(g < 0.5))
    lay_bass([bar], amp=0.44 + 0.12 * g)
lay_bell(range(4, 12), amp=0.16, dense=False)
place(fx, noise_impact(0.6, amp=0.6, seed=21), bar_time(12) - 0.02)

# 12-27 버스A/플로어 (벨 전경 · 하프타임 킥 · 코드찹 은은 · 엠비언트 부각)
for bar in range(12, 28):
    halftime_kick(bar, kamp=0.70)
    claps(bar, amp=0.40)
    hats(bar, amp=0.10)
    lay_fb_chop(fb, bar, amp=0.20, bright=3600, closed=True)
lay_bass(range(12, 28), amp=0.48)
lay_bell(range(12, 28), amp=0.19, dense=False)

# 28-43 코러스A (풀 4온플로어 · 코드찹 밝게 · 벨 하강폭포 밀도 · 오픈햇)
for bar in range(28, 44):
    four_on_floor(bar, kamp=0.84, punch=55)
    claps(bar, amp=0.46)
    hats(bar, amp=0.14); open_hats(bar, amp=0.30)
    lay_fb_chop(fb, bar, amp=0.50, bright=8600)
lay_bass(range(28, 44), amp=0.56)
lay_bell(range(28, 44), amp=0.22, dense=True)

# 44-51 브레이크1 (엠비언트 브레이크다운 · 하프타임 · 코드찹/킥 후퇴 = 谷)
for bar in range(44, 52):
    if bar % 2 == 0:
        tk = bar_time(bar, 0); place(drums, hard_kick(0.26, amp=0.5, punch=50, drive=1.2), tk); kick_times.append(tk)
    place(drums, clap(amp=0.26, seed=360 + bar), bar_time(bar, 4))
lay_bass(range(44, 52), amp=0.42, whole=True)
lay_bell(range(44, 52), amp=0.16, dense=False, oct_up=12)

# 52-55 빌드2 (라이저 + 코드찹 필터 오픈)
for bar in range(52, 56):
    g = (bar - 52) / 3.0
    four_on_floor(bar, kamp=0.72 + 0.10 * g)
    hats(bar, amp=0.10 + 0.06 * g)
    lay_fb_chop(fb, bar, amp=0.24 + 0.18 * g, bright=(4000 + 5000 * g), closed=(g < 0.4))
    lay_bass([bar], amp=0.5)
place(fx, noise_riser(BAR * 4, amp=0.55, fc_start=300, fc_end=8500, seed=41), bar_time(52))
place(fx, noise_impact(0.7, amp=0.72, seed=42), bar_time(56) - 0.02)

# 56-71 코러스B (최대 전 최고조 · 코드찹 최밝 · 벨 밀도 · 에어)
for bar in range(56, 72):
    four_on_floor(bar, kamp=0.88, punch=55)
    claps(bar, amp=0.48)
    hats(bar, amp=0.15); open_hats(bar, amp=0.32)
    lay_fb_chop(fb, bar, amp=0.54, bright=9000)
lay_bass(range(56, 72), amp=0.60)
lay_bell(range(56, 72), amp=0.24, dense=True)

# 72-87 버스B/인터루드 (벨 하강 대비 · 코드찹 후퇴 · 밀도 감)
for bar in range(72, 88):
    four_on_floor(bar, kamp=0.76)
    claps(bar, amp=0.40)
    hats(bar, amp=0.12)
    lay_fb_chop(fb, bar, amp=0.30, bright=6000, closed=(bar % 4 < 2))
lay_bass(range(72, 88), amp=0.52)
lay_bell(range(72, 88), amp=0.20, dense=False)

# 88-95 브레이크2 (엠비언트 브레이크다운 = 谷)
for bar in range(88, 96):
    if bar % 2 == 0:
        tk = bar_time(bar, 0); place(drums, hard_kick(0.26, amp=0.5, punch=50, drive=1.2), tk); kick_times.append(tk)
    place(drums, clap(amp=0.26, seed=360 + bar), bar_time(bar, 4))
lay_bass(range(88, 96), amp=0.42, whole=True)
lay_bell(range(88, 96), amp=0.16, dense=False)

# 96-99 빌드3 (최종 라이저)
for bar in range(96, 100):
    g = (bar - 96) / 3.0
    four_on_floor(bar, kamp=0.74 + 0.12 * g)
    hats(bar, amp=0.10 + 0.08 * g)
    lay_fb_chop(fb, bar, amp=0.26 + 0.20 * g, bright=(4200 + 5200 * g), closed=(g < 0.4))
    lay_bass([bar], amp=0.52)
place(fx, noise_riser(BAR * 4, amp=0.62, fc_start=350, fc_end=9500, seed=93), bar_time(96))
place(fx, noise_impact(0.8, amp=0.8, seed=94), bar_time(100) - 0.02)

# 100-135 파이널 (최대 에너지, +2 키업, 36마디) ★뒤 1/3 키업
for bar in range(100, 136):
    four_on_floor(bar, kamp=0.92, punch=54)
    claps(bar, amp=0.50)
    hats(bar, amp=0.16); open_hats(bar, amp=0.34)
    lay_fb_chop(fb, bar, amp=0.58, bright=9200)
lay_bass(range(100, 136), amp=0.64)
lay_bell(range(100, 136), amp=0.26, dense=True)
for bar in range(100, 136, 4):
    place(fx, noise_impact(0.4, amp=0.30, seed=700 + bar), bar_time(bar))

# 136-139 아웃트로 (자연 마무리 = 파이널 히트 + 코드 링아웃, 루프 폐기)
for bar in range(136, 139):
    halftime_kick(bar, kamp=0.7)
    lay_fb_chop(fb, bar, amp=0.30, bright=6000, closed=True)
lay_bass(range(136, 139), amp=0.5, whole=True)
place(drums, hard_kick(0.4, amp=1.0, punch=50, drive=1.4), bar_time(139, 0)); kick_times.append(bar_time(139, 0))
place(fx, noise_impact(1.6, amp=0.8, seed=99), bar_time(139, 0))
for mi in ch(139)["tones"]:                      # 파이널 코드 홀드(링아웃)
    place(amb, pad(mi, BAR * 0.98, amp=0.5, a=0.02, r=0.9, fc=2200), bar_time(139))
    place(fb, super_saw_lead(m2f(mi), BAR * 0.9, amp=0.10, bright=7000), bar_time(139))

# ═══ 믹스 + 사이드체인 펌프 (템플릿 mix chain: sidechain → softclip → limiter) ═══
kick_times = sorted(set(kt for kt in kick_times if kt < DUR))
duck = sidechain_env(N, kick_times, depth=0.62, attack=0.002, release=0.11)
fb *= duck; lead *= duck; sub *= (0.5 + 0.5 * duck)
amb *= (0.75 + 0.25 * duck)                       # 엠비언트 살짝만 펌프

# 엠비언트에 Schroeder 리버브(우주 공간감)
amb = reverb(amb, mix=0.28, decay=0.72)

# 버스 카빙(마스킹·머드 제거) — 서브=저역 전담, 코드찹/벨/패드=중고역
fb = hp(fb, 200, order=2)
lead = hp(lead, 340, order=2)
amb = hp(amb, 110, order=2)
sub = hp(sub, 30, order=2); sub = lp(sub, 180, order=4)
drums_sub = lp(drums, 120, order=2); drums_hi = hp(drums, 120, order=2)

# 코드찹·벨 새추레이션(중고역 존재감, exciter)
fb = fb * 0.75 + soft_clip(fb * 1.5, 1.35) * 0.25
lead = lead * 0.8 + soft_clip(lead * 1.4, 1.3) * 0.2

# 레벨 합성 (코스믹 = 코드찹/벨/패드 전경, 서브 억제)
master = fb * 1.9 + lead * 1.6 + sub * 0.42 + drums_sub * 0.62 + drums_hi * 0.85 + amb * 0.85 + fx * 0.55

master = soft_clip(master, drive=1.03)
master = limiter(master, ceiling=0.94)

# ★엔딩(루프 폐기): 인트로 마이크로 페이드 + 아웃트로 1.4s 링아웃 페이드
xf = int(0.005 * SR); master[:xf] *= np.linspace(0, 1, xf)
of = int(1.4 * SR);   master[-of:] *= np.linspace(1, 0, of) ** 0.8

# ═══ 메트릭 ═══════════════════════════════════════════════════════════
def rms_db(a): return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9)
peak = float(np.max(np.abs(master)))
clipn = int(np.sum(np.abs(master) > 0.999))
nan = bool(np.any(~np.isfinite(master)))
print(f"[i] peak={peak:.4f} rms={rms_db(master):.2f}dB clip>0.999={clipn} nan={nan} N={N} dur={N/SR:.6f}s")
SECS = {'intro':(0,4),'build':(4,12),'verseA':(12,28),'chorusA':(28,44),'break1':(44,52),
        'build2':(52,56),'chorusB':(56,72),'verseB':(72,88),'break2':(88,96),
        'build3':(96,100),'final':(100,136),'outro':(136,140)}
sec_rms = {}
for name, (b0, b1) in SECS.items():
    i0, i1 = int(round(b0 * BAR * SR)), int(round(b1 * BAR * SR))
    sec_rms[name] = rms_db(master[i0:i1])
    print(f"    {name:<9} {sec_rms[name]:6.2f} dB")

# 하드 요건 체크
print(f"[chk] peak<1.0 & clip==0 : {bool(peak < 1.0 and clipn == 0)}")
print(f"[chk] nan==False         : {bool(nan == False)}")
print(f"[chk] N==7056000         : {bool(N == 7056000)}")
print(f"[chk] final>verseA       : {bool(sec_rms['final'] > sec_rms['verseA'])} (final {sec_rms['final']:.2f} vs verseA {sec_rms['verseA']:.2f})")
print(f"[chk] break1<chorusA&B   : {bool(sec_rms['break1'] < sec_rms['chorusA'] and sec_rms['break1'] < sec_rms['chorusB'])}")
print(f"[chk] break2<chorusB&fin : {bool(sec_rms['break2'] < sec_rms['chorusB'] and sec_rms['break2'] < sec_rms['final'])}")

# ═══ WAV 출력 (stereo int16 44100) ═══
stereo = np.stack([master, master], 1)
i16 = np.clip(stereo * 32767, -32768, 32767).astype(np.int16)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hyak_ep5_fullver.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(i16.tobytes())
print(f"[OK] saved {out} ({N} spl, {N/SR:.6f}s)")
