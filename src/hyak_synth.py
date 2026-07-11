# Hyak BGM 합성 툴킷 — 하드EDM/전파(denpa) 전용 저수준 DSP.
# 두루(duru_synth.py)와는 독립된 신규 코드(브랜드 분리 원칙). 결정론(고정시드). mono float64 ndarray 반환.
import numpy as np
from scipy.signal import butter, sosfilt, resample_poly

SR = 44100


def m2f(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def _t(dur):
    n = int(round(dur * SR))
    return n, np.arange(n) / SR


def _sos(fc, btype, order=4):
    fc = np.clip(fc, 20, SR / 2 - 100)
    return butter(order, fc / (SR / 2), btype=btype, output="sos")


def lp(x, fc, order=4):
    return sosfilt(_sos(fc, "low", order), x)


def hp(x, fc, order=2):
    return sosfilt(_sos(fc, "high", order), x)


def adsr(n, a, d, s, r, sus=0.7):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    a = max(a, 1); d = max(d, 1); r = max(r, 1)
    env = np.zeros(n)
    if a >= n:
        env[:] = np.linspace(0, 1, n)
        return env
    env[:a] = np.linspace(0, 1, a)
    de = min(d, n - a)
    env[a:a + de] = np.linspace(1, sus, de)
    body_end = max(a + de, n - r)
    env[a + de:body_end] = sus
    rr = n - body_end
    if rr > 0:
        env[body_end:] = np.linspace(env[body_end - 1] if body_end > 0 else sus, 0, rr)
    return env


def tail_taper(sig, rel=0.02):
    n = len(sig); r = min(int(rel * SR), n)
    if r > 1:
        sig = sig.copy()
        sig[-r:] *= 0.5 * (1 + np.cos(np.linspace(0, np.pi, r)))
    return sig


def soft_clip(x, drive=1.0, oversample=4):
    """tanh 웨이브셰이핑. 오버샘플링(기본 4x)으로 에일리어싱(=디지털 '깨짐'/비트크러시 아티팩트) 억제.
    drive<=1.02 근처는 사실상 선형 통과(안전한 헤드룸 확보 용도)이므로 오버샘플 생략."""
    if drive <= 1.02:
        return np.tanh(x * drive) / np.tanh(drive)
    n = len(x)
    up = resample_poly(x, oversample, 1)
    shaped = np.tanh(up * drive) / np.tanh(drive)
    down = resample_poly(shaped, 1, oversample)
    return down[:n] if len(down) >= n else np.pad(down, (0, n - len(down)))


# ---------- 타악 ----------
def hard_kick(dur=0.22, amp=1.0, punch=60.0, drive=1.6):
    """하드코어/전파 킥 — 피치 스윕 사인 + 클릭 트랜지언트 + (완화된) 디스토션."""
    n, t = _t(dur)
    f0, f1 = 210.0, 42.0
    sweep = f1 + (f0 - f1) * np.exp(-t * punch)
    phase = 2 * np.pi * np.cumsum(sweep) / SR
    body = np.sin(phase) * np.exp(-t / 0.16)
    click_n = int(0.004 * SR)
    click = np.zeros(n)
    if click_n < n:
        click[:click_n] = np.exp(-np.arange(click_n) / (0.0012 * SR))
    out = soft_clip(body * 1.15 + click * 0.7, drive)
    return tail_taper(amp * out, rel=0.03)


def closed_hat(dur=0.035, amp=0.30, seed=1):
    """크리스프 틱(하이패스 4차, 컷오프↑) — 이전 버전(2차/6.5kHz/18ms 고정)이
    브로드밴드 저역 누출+긴 감쇠로 '바람빠지는' 지속성 히스처럼 들려 개정(2026-07-06 사용자 피드백).
    감쇠는 dur에 비례(짧게 부르면 closed, 길게 부르면 open 캐릭터) — 상한 22ms로 여전히 크리스프하게."""
    n, t = _t(dur)
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n)
    noise = hp(noise, 8500, order=4)
    tau = min(dur / 5.0, 0.022)
    env = np.exp(-t / tau)
    return tail_taper(amp * noise * env, rel=0.006)


def clap(dur=0.14, amp=0.5, seed=7):
    n, t = _t(dur)
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n)
    noise = hp(lp(noise, 5200), 900)
    # 3연속 트랜지언트로 클랩 특유의 flam 표현
    env = np.zeros(n)
    for off in (0.0, 0.008, 0.017):
        i0 = int(off * SR)
        if i0 < n:
            seg = np.exp(-np.arange(n - i0) / (0.03 * SR))
            env[i0:] += seg * 0.6
    return tail_taper(amp * noise * env, rel=0.02)


def noise_riser(dur, amp=0.5, fc_start=300, fc_end=9000, seed=3):
    n, t = _t(dur)
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n)
    fc = fc_start * (fc_end / fc_start) ** (t / max(dur, 1e-6))
    out = np.zeros(n)
    win = 2048
    for i in range(0, n, win):
        seg = noise[i:i + win]
        f = fc[min(i, n - 1)]
        out[i:i + win] = hp(seg, f, order=2)
    env = np.linspace(0, 1, n) ** 1.5
    return amp * out * env


def noise_impact(dur=0.5, amp=0.6, seed=9):
    n, t = _t(dur)
    rng = np.random.default_rng(seed)
    noise = rng.standard_normal(n)
    noise = lp(noise, 3000)
    env = np.exp(-t / 0.18)
    return tail_taper(amp * noise * env, rel=0.05)


# ---------- 음정 있는 음색 ----------
def sub_bass(freq, dur, amp=0.9, drive=1.6):
    n, t = _t(dur)
    s = np.sin(2 * np.pi * freq * t) + 0.15 * np.sin(2 * np.pi * 2 * freq * t)
    env = adsr(n, 0.004, 0.05, 0.85, 0.03, sus=0.85)
    return tail_taper(amp * soft_clip(s * env, drive) / 1.3, rel=0.01)


def super_saw_lead(freq, dur, amp=0.5, detune_cents=9, voices=5, bright=6500):
    n, t = _t(dur)
    s = np.zeros(n)
    for k in range(voices):
        d = (k - (voices - 1) / 2) / max(1, (voices - 1) / 2)
        f = freq * (2 ** (d * detune_cents / 1200.0))
        # 밴드리밋 근사 saw: 가산합성(8배음)
        saw = np.zeros(n)
        for h in range(1, 9):
            saw += (1.0 / h) * np.sin(2 * np.pi * f * h * t)
        s += saw
    s /= voices
    env = adsr(n, 0.008, 0.08, 0.75, 0.05, sus=0.75)
    return tail_taper(amp * lp(s * env, bright) / 1.6, rel=0.01)


def pluck_arp(freq, dur, amp=0.4, bright=5200):
    n, t = _t(dur)
    saw = np.zeros(n)
    for h in range(1, 6):
        saw += (1.0 / h) * np.sin(2 * np.pi * freq * h * t)
    env = adsr(n, 0.002, 0.10, 0.0, 0.02, sus=0.0)
    return tail_taper(amp * lp(saw * env, bright) / 1.4, rel=0.01)


def bleat_hit(freq, dur, amp=0.35):
    """카와이 전파 특유의 삑삑거리는 스퀘어 리드 악센트."""
    n, t = _t(dur)
    sq = np.sign(np.sin(2 * np.pi * freq * t))
    env = adsr(n, 0.002, 0.05, 0.0, 0.02, sus=0.0)
    return tail_taper(amp * lp(sq * env, 4000) / 1.5, rel=0.01)


# ---------- 마스터 체인 ----------
def limiter(x, ceiling=0.95, knee=0.85):
    peak = np.max(np.abs(x)) + 1e-9
    if peak <= ceiling:
        return x
    ratio = ceiling / peak
    return x * ratio if ratio < 1 else x


def sidechain_env(n, kick_times, sr=SR, depth=0.7, attack=0.002, release=0.14):
    """킥 위치마다 덕킹하는 볼륨 엔벨로프(1.0=풀볼륨). 결정론(입력시간에만 의존)."""
    env = np.ones(n)
    a = max(1, int(attack * sr))
    r = max(1, int(release * sr))
    for kt in kick_times:
        i0 = int(kt * sr)
        if i0 >= n:
            continue
        dip = np.zeros(a + r)
        dip[:a] = np.linspace(1.0, 1.0 - depth, a)
        dip[a:] = np.linspace(1.0 - depth, 1.0, r)
        i1 = min(n, i0 + len(dip))
        seg_len = i1 - i0
        env[i0:i1] = np.minimum(env[i0:i1], dip[:seg_len])
    return env
