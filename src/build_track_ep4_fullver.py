# Hyak ep4 BGM 풀버전 — 블랙홀 편. 200BPM, 132마디(4/4) = 158.400s.
#   숏폼(20마디 24s half-open 루프)의 음악 DNA를 유지하되, 영상 싱크(seam·나레이션 진입·인폴 프레임)를
#   버리고 **완결형 곡 구조**로 재편곡(ep3 fullver 템플릿의 섹션 아크를 132마디로 스케일).
#   ★EP4 정체성 보존: Em–G–D–Am(i–bIII–bVII–iv) 화성 · LEAD_PHRASE 아이시 멜로디 ·
#     하프타임/퓨처베이스 필 · 커스텀 신스(fb_chop·fb_wall·glitter·drone·pad·lead)를 숏폼서 그대로 이식.
#   구조(132마디): 인트로-빌드-버스A-코러스A-브레이크1-빌드2-코러스B-버스B-브레이크2-빌드3-파이널-아웃트로.
#   루프 아님 → half-open 블립마스킹 대신 자연스러운 엔딩. 순수 hyak_synth 코드합성(외부샘플 0, CC0).
import numpy as np, sys, os, wave
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '음원'))
from hyak_synth import (SR, m2f, hard_kick, closed_hat, clap, noise_riser, noise_impact,
                        sub_bass, super_saw_lead, pluck_arp, bleat_hit, sidechain_env, limiter, soft_clip, lp, hp)

BPM = 200.0
BEAT = 60.0 / BPM              # 0.30s
BAR = BEAT * 4                 # 1.20s
N_BARS = 132
DUR = BAR * N_BARS             # 158.400000s
N = int(round(DUR * SR))       # 6,985,440
print(f"[i] ep4 fullver BPM={BPM} bar={BAR:.6f}s dur={DUR:.6f}s N={N}")

mix = np.zeros(N); melodic = np.zeros(N); wallbus = np.zeros(N); kick_times = []

def place(buf, sig, t):
    i0 = int(round(t * SR)); i1 = min(N, i0 + len(sig))
    if i0 < N and i1 > i0: buf[i0:i1] += sig[:i1 - i0]
def bt(bar, sub=0): return bar * BAR + sub * (BEAT / 2.0)   # sub = 8분 단위(0..7)

# ── EP4 화성 골격 (신규 지문: i–bIII–bVII–iv in E minor) — 숏폼서 계승 ─────────────
CHORDS = [
    {"bass": 40, "tones": [64, 67, 71]},   # Em
    {"bass": 43, "tones": [67, 71, 74]},   # G
    {"bass": 38, "tones": [62, 66, 69]},   # D
    {"bass": 33, "tones": [60, 64, 69]},   # Am(1전위 보이싱)
]
def ch(bar): return CHORDS[bar % 4]

# ── EP4 아이시 리드 (사전작곡 멜로디, 모듈로 인덱스 금지 교훈) — 숏폼서 계승 ─────────
#   E minor 관통 컨투어: 상승(정점 D6) → 하강 해소. 마디 경계 도약 ≤3반음.
LEAD_PHRASE = [
    [(0.0, 79, 2.0), (2.0, 83, 2.0)],                # barA (Em): G5→B5
    [(0.0, 81, 2.0), (2.0, 86, 1.0), (3.0, 83, 1.0)],# barB (G):  A5→D6(정점)→B5
    [(0.0, 81, 2.0), (2.0, 78, 2.0)],                # barC (D):  A5→F#5
    [(0.0, 76, 2.5), (2.5, 79, 1.5)],                # barD (Am): E5→G5
]

# ══ EP4 커스텀 신스 프리미티브 (숏폼 build_track_ep4_v1.py서 verbatim 이식) ══════════
def lay_halftime(bars, kamp=1.0, snamp=0.5, hat=0.28, hseed=210):
    """하프타임: 킥 = 1·3박(비트1=sub0, 비트3=sub4), 스네어(클랩) = 3박."""
    for bar in bars:
        tk = bt(bar, 0); place(mix, hard_kick(amp=kamp), tk); kick_times.append(tk)
        place(mix, clap(amp=snamp, seed=300 + bar), bt(bar, 4))
        for e in range(8):
            place(mix, closed_hat(amp=hat, seed=hseed + bar * 8 + e), bt(bar, e))

def lay_glitter(bars, amp=0.30, up=24, decim=1):
    """16분 글리터 아르페지오(고역 +2옥타브). decim=2 → 절반 밀도."""
    for bar in bars:
        tones = ch(bar)["tones"]
        for s in range(0, 16, decim):
            deg = tones[s % 3] + up + (12 if s % 8 == 7 else 0)   # 매 8스텝째 옥타브 스파크
            place(melodic, pluck_arp(m2f(deg), BEAT / 4.0 * 0.85, amp=amp), bar * BAR + s * (BEAT / 4.0))

def lay_bass_pulse(bars, amp=0.6, every=2):
    """베이스 펄스(every=2 → 8분)."""
    for bar in bars:
        f = m2f(ch(bar)["bass"])
        for sub in range(0, 8, every):
            place(melodic, sub_bass(f, BEAT / 2 * 0.9, amp=amp), bt(bar, sub))

def lay_pad(bars, amp=0.10, fc=1600):
    """코스믹 패드: 코드 3성 롱 새성분 → LP."""
    seg = np.zeros(N)
    for bar in bars:
        for t_ in ch(bar)["tones"]:
            place(seg, super_saw_lead(m2f(t_), BAR * 0.98, amp=amp, bright=fc), bt(bar))
    return lp(seg, fc)

def lay_drone(bars, amp=0.5):
    seg = np.zeros(N)
    for bar in bars:
        place(seg, sub_bass(m2f(ch(bar)["bass"]), BAR * 0.98, amp=amp), bt(bar))
    return lp(seg, 850)

def lay_lead(start_bar, n_bars, up=0, amp=0.30, bright=5200, echo=True):
    """아이시 리드 + 딜레이 에코(0.3s ×2 감쇠 = 우주 공간감)."""
    for k in range(n_bars):
        bar = start_bar + k
        for (b_off, midi, dur) in LEAD_PHRASE[k % 4]:
            t = bar * BAR + b_off * BEAT
            sig = super_saw_lead(m2f(midi + up), dur * BEAT * 0.95, amp=amp, bright=bright)
            place(melodic, sig, t)
            if echo:
                place(melodic, sig * 0.42, t + 0.3)
                place(melodic, sig * 0.20, t + 0.6)

FB_PAT = [1, 0, 1, 1, 0, 1, 1, 0]          # 8분 싱코페이션 게이트
def lay_fb_chop(bars, amp=0.50, bright=8800, closed=False):
    """와이드 9th 슈퍼소 코드찹. closed=True → LP 닫힌 프리드롭 예고(필터 오픈 전)."""
    for bar in bars:
        tones = ch(bar)["tones"]
        voic = tones + [tones[0] + 14]        # 9th 와이드 보이싱
        for sub in range(8):
            if not FB_PAT[sub]: continue
            dur = BEAT / 2 * 0.62             # 릴리즈 컷(~55% 유지 + 뚝)
            ln = int(dur * SR) + 64
            seg = np.zeros(ln)
            for m_ in voic:
                s_ = super_saw_lead(m2f(m_), dur, amp=amp / len(voic), bright=(900 if closed else bright))
                seg[:len(s_)] += s_[:ln]
            if not closed:
                for m_ in voic[:3]:           # +1옥타브 에어 레이어(청량 고역)
                    s_ = super_saw_lead(m2f(m_ + 12), dur, amp=amp * 0.16 / 3, bright=9500)
                    seg[:len(s_)] += s_[:ln]
                seg = hp(seg, 160)            # 저역 분리(서브는 sub_bass 전담)
            place(melodic, seg, bt(bar, sub))

def lay_fb_wall(bars, amp_low=1.25, amp_mid=0.85):
    """드롭 지속층: 로우 보이싱(E3, LP2200) 벽 + 미드 브라스 스택. duck2 펌프로 '차오름'."""
    seg = np.zeros(N)
    for bar in bars:
        tones = ch(bar)["tones"]
        for m_ in tones:                       # 로우 벽(-12 = E3 영역, 150-400Hz)
            place(seg, super_saw_lead(m2f(m_ - 12), BAR * 0.98, amp=amp_low / 3, bright=2200), bt(bar))
        for m_ in tones:                       # 미드 브라스(원 옥타브, 4분×4 재타격)
            for q in range(4):
                place(seg, super_saw_lead(m2f(m_), BEAT * 0.92, amp=amp_mid / 3, bright=3200), bt(bar, q * 2))
    return lp(seg, 2600)

def lay_snare_roll(t0, t1, n=16, amp0=0.18, amp1=0.55, seed=770):
    """드롭 직전 클랩 16분 롤(가속 크레셴도) — 표준 퓨베 필."""
    for i in range(n):
        x = i / max(1, n - 1)
        tt = t0 + (t1 - t0) * x
        place(mix, clap(amp=amp0 + (amp1 - amp0) * x * x, seed=seed + i), tt)

def lay_pure_sub(bars, amp=0.78):
    """순수 서브(E1, LP75 = 60-150 하모닉 정리) — 드롭 저역 앵커."""
    for bar in bars:
        fq = m2f(ch(bar)["bass"] - 12)
        for sub_ in range(0, 8, 2):
            place(melodic, lp(sub_bass(fq, BEAT / 2 * 0.9, amp=amp), 75), bt(bar, sub_))

def lay_pulse_hats(bars, amp0=0.16, ramp=0.0, base=0):
    for bar in bars:
        for e in range(8):
            place(mix, closed_hat(amp=amp0 + ramp * (bar - base), seed=600 + bar * 8 + e), bt(bar, e))

def lay_open_hats(bars, amp=0.30):
    for bar in bars:
        for e in (1, 3, 5, 7):
            place(mix, closed_hat(dur=0.11, amp=amp, seed=940 + bar * 8 + e), bt(bar, e))

# 강펌프(퓨베 청량감) 구간 마스크 — 코러스/파이널
drop_bars = set()

# ══ 곡 구조 (132마디) ═══════════════════════════════════════════════════════════
# ── 0-3 인트로 (谷, 조용) : 드론 bed + 코스믹 패드 + 희미 글리터 틱 + 리드 예고 ──
melodic += lay_drone(range(0, 4), amp=0.42)
melodic += lay_pad(range(0, 4), amp=0.07, fc=1800)
lay_glitter(range(0, 4), amp=0.05, up=12, decim=8)
for b, deg in [(0, 76), (2, 79)]:                     # 아이시 리드 서주(에코)
    s0 = super_saw_lead(m2f(deg), BEAT * 1.6, amp=0.16, bright=4800)
    place(melodic, s0, bt(b)); place(melodic, s0 * 0.4, bt(b) + 0.3)
place(mix, noise_riser(BAR * 1.0, amp=0.20, fc_start=200, fc_end=2200, seed=11), bt(3))

# ── 4-7 빌드 : 베이스 펄스 + 하이햇 램프 + 글리터 진입 → 임팩트 ──
lay_bass_pulse(range(4, 8), amp=0.48, every=2)
lay_pulse_hats(range(4, 8), amp0=0.14, ramp=0.03, base=4)
melodic += lay_drone(range(4, 8), amp=0.40)
lay_glitter([6, 7], amp=0.14, decim=2)
lay_lead(4, 4, amp=0.22, bright=5000)
place(mix, noise_riser(BAR * 2.0, amp=0.42, fc_start=300, fc_end=7000, seed=21), bt(6))
place(mix, noise_impact(amp=0.60, seed=22), bt(8) - 0.02)

# ── 8-23 버스A ×4 (하프타임 라이트 · 리드 관통 · 베이스 · 중밀도) ──
lay_halftime(range(8, 24), kamp=0.78, snamp=0.42, hat=0.26, hseed=200)
lay_bass_pulse(range(8, 24), amp=0.52, every=2)
lay_lead(8, 16, amp=0.28, bright=5600)
lay_glitter(range(8, 24), amp=0.16, decim=2)
melodic += lay_pad(range(8, 24), amp=0.06, fc=2200)

# ── 24-39 코러스A ×4 (퓨베 코드찹 + 서스테인 벽 + 글리터 풀 + 리드) ──
lay_halftime(range(24, 40), kamp=0.95, snamp=0.55, hat=0.32, hseed=800)
for b in range(24, 40):
    lay_fb_chop([b], amp=0.46, bright=8600)
    wallbus += lay_fb_wall([b], amp_low=0.95, amp_mid=0.64)
lay_pure_sub(range(24, 40), amp=0.72)
lay_glitter(range(24, 40), amp=0.26, decim=1)
lay_lead(24, 16, amp=0.28, bright=6200)
lay_open_hats(range(24, 40), amp=0.28)
drop_bars |= set(range(24, 40))

# ── 40-47 브레이크1 (谷, 숨쉬기) : 드론 + 패드 + 희미 리드 · DIP ──
melodic += lay_drone(range(40, 48), amp=0.42)
melodic += lay_pad(range(40, 48), amp=0.07, fc=1900)
lay_glitter(range(40, 48), amp=0.06, up=12, decim=8)
lay_lead(40, 8, amp=0.18, bright=4800)
for bar, sub in [(42, 4), (45, 4)]:
    place(mix, clap(amp=0.16, seed=360 + bar), bt(bar, sub))

# ── 48-51 빌드2 : 라이저 + 스네어 롤 → 슬램 ──
lay_bass_pulse(range(48, 52), amp=0.52, every=2)
lay_pulse_hats(range(48, 52), amp0=0.16, ramp=0.03, base=48)
melodic += lay_drone(range(48, 52), amp=0.40)
lay_glitter([50, 51], amp=0.20, decim=1)
place(mix, noise_riser(BAR * 3.0, amp=0.55, fc_start=300, fc_end=9000, seed=41), bt(48))
lay_snare_roll(bt(51, 0), bt(52, 0) - 0.01, n=16, amp0=0.16, amp1=0.55, seed=470)
place(mix, noise_impact(amp=0.75, seed=42), bt(52) - 0.02)

# ── 52-67 코러스B ×4 (코러스A보다 두껍게) ──
lay_halftime(range(52, 68), kamp=1.0, snamp=0.58, hat=0.34, hseed=1200)
for b in range(52, 68):
    lay_fb_chop([b], amp=0.50, bright=8800)
    wallbus += lay_fb_wall([b], amp_low=1.0, amp_mid=0.70)
lay_pure_sub(range(52, 68), amp=0.78)
lay_glitter(range(52, 68), amp=0.28, decim=1)
lay_lead(52, 16, amp=0.30, bright=6600)
lay_open_hats(range(52, 68), amp=0.32)
drop_bars |= set(range(52, 68))

# ── 68-83 버스B/인터루드 (리드 변주 · 대비 낮춤) ──
lay_halftime(range(68, 84), kamp=0.80, snamp=0.44, hat=0.28, hseed=1600)
lay_bass_pulse(range(68, 84), amp=0.54, every=2)
lay_lead(68, 16, up=0, amp=0.26, bright=5400)
lay_glitter(range(68, 84), amp=0.18, decim=2)
melodic += lay_pad(range(68, 84), amp=0.06, fc=2200)

# ── 84-91 브레이크2 (谷) · DIP ──
melodic += lay_drone(range(84, 92), amp=0.42)
melodic += lay_pad(range(84, 92), amp=0.07, fc=1900)
lay_glitter(range(84, 92), amp=0.06, up=12, decim=8)
lay_lead(84, 8, amp=0.18, bright=4800)
for bar, sub in [(86, 4), (89, 4)]:
    place(mix, clap(amp=0.16, seed=380 + bar), bt(bar, sub))

# ── 92-95 빌드3 : 최대 라이저 + 스네어 롤 → 슬램 ──
lay_bass_pulse(range(92, 96), amp=0.54, every=2)
lay_pulse_hats(range(92, 96), amp0=0.18, ramp=0.03, base=92)
lay_glitter([94, 95], amp=0.22, decim=1)
place(mix, noise_riser(BAR * 3.0, amp=0.65, fc_start=350, fc_end=10000, seed=93), bt(92))
lay_snare_roll(bt(95, 0), bt(96, 0) - 0.01, n=16, amp0=0.18, amp1=0.60, seed=930)
place(mix, noise_impact(amp=0.85, seed=94), bt(96) - 0.02)

# ── 96-127 파이널 (최대 에너지, 32마디) : 풀 텍스처 + 클라이맥스 리드 + 임팩트 ──
lay_halftime(range(96, 128), kamp=1.0, snamp=0.62, hat=0.38, hseed=2000)
for b in range(96, 128):
    lay_fb_chop([b], amp=0.55, bright=8800)
    wallbus += lay_fb_wall([b], amp_low=1.05, amp_mid=0.72)
lay_pure_sub(range(96, 128), amp=0.84)
lay_glitter(range(96, 128), amp=0.30, decim=1)
lay_lead(96, 16, amp=0.30, bright=7000)
# 후반 16마디: 클라이맥스 파워 프레이즈(E6→D6→B5) 관통
for k in range(112, 128):
    for (b_off, midi, dur) in [(0.0, 88, 2.0), (2.0, 86, 1.0), (3.0, 83, 1.0)]:
        t = bt(k) + b_off * BEAT
        s_ = super_saw_lead(m2f(midi), dur * BEAT * 0.95, amp=0.28, bright=7200)
        place(melodic, s_, t); place(melodic, s_ * 0.42, t + 0.3)
lay_open_hats(range(96, 128), amp=0.36)
for bar in range(96, 128, 4):
    place(mix, noise_impact(amp=0.32, seed=700 + bar), bt(bar))
drop_bars |= set(range(96, 128))

# ── 128-131 아웃트로 (자연 마무리) : 드롭 감쇠 + 마지막 킥/크래시 + 드론 테일 ──
lay_halftime([128, 129], kamp=0.9, snamp=0.5, hat=0.30, hseed=2400)
lay_bass_pulse([128, 129], amp=0.60, every=2)
for b in (128, 129):
    lay_fb_chop([b], amp=0.42, bright=8200)
    wallbus += lay_fb_wall([b], amp_low=0.85, amp_mid=0.55)
melodic += lay_drone([130, 131], amp=0.40)
melodic += lay_pad([130, 131], amp=0.07, fc=1700)
s_end = super_saw_lead(m2f(76), BAR * 1.6, amp=0.20, bright=5200)   # E5 롱테일 해소
place(melodic, s_end, bt(130)); place(melodic, s_end * 0.4, bt(130) + 0.3)
place(mix, hard_kick(amp=1.0, drive=1.4), bt(130, 0)); kick_times.append(bt(130, 0))
place(mix, noise_impact(dur=1.4, amp=0.8, seed=99), bt(130, 0))

# ── 사이드체인 + 믹스 (드롭 구간 강펌프 = 퓨베 청량감) ────────────────────────────
duck  = sidechain_env(N, kick_times, depth=0.60, attack=0.002, release=0.10)
duck2 = sidechain_env(N, kick_times, depth=0.82, attack=0.002, release=0.13)
dropmask = np.zeros(N)
for b in drop_bars:
    dropmask[int(bt(b) * SR):int(bt(b + 1) * SR)] = 1.0
melodic *= duck * (1 - dropmask) + duck2 * dropmask
wallbus *= (0.5 + 0.5 * duck2)                        # 벽 = 반펌프(대역 채움 유지 + 펌핑감)
master = mix * 0.85 + melodic * 0.95 + wallbus * 0.95
master = soft_clip(master, drive=1.02)
master = limiter(master, ceiling=0.92)

so, si = int(0.08 * SR), int(0.005 * SR)
master[-so:] *= np.linspace(1, 0, so)
master[:si] *= np.linspace(0, 1, si)

def rms_db(a): return 20 * np.log10(np.sqrt(np.mean(a ** 2)) + 1e-9)
peak = np.max(np.abs(master))
print(f"[i] peak={peak:.4f} rms={rms_db(master):.2f}dB clip>0.999={int(np.sum(np.abs(master)>0.999))} nan={bool(np.any(~np.isfinite(master)))}")
SECT = {'intro':(0,4),'build':(4,8),'verseA':(8,24),'chorusA':(24,40),'break1':(40,48),
        'build2':(48,52),'chorusB':(52,68),'verseB':(68,84),'break2':(84,92),
        'build3':(92,96),'final':(96,128),'outro':(128,132)}
for name, (b0, b1) in SECT.items():
    i0, i1 = int(b0 * BAR * SR), int(b1 * BAR * SR)
    print(f"    {name:<9} {rms_db(master[i0:i1]):6.2f} dB")

stereo = np.stack([master, master], 1)
i16 = np.clip(stereo * 32767, -32768, 32767).astype(np.int16)
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hyak_ep4_fullver.wav")
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(i16.tobytes())
print(f"[OK] saved {out} ({N} spl, {N/SR:.6f}s)")
