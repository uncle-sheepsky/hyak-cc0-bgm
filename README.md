> 📦 **통합 안내 / Unified** — 이 채널 음원은 [**duru-ai-cc0-bgm**](https://github.com/uncle-sheepsky/duru-ai-cc0-bgm) 단일 CC0 팩으로 통합되었습니다. 이 repo 파일은 기존 링크 유지를 위해 그대로 둡니다.
> Now unified into **duru-ai-cc0-bgm** — files here are kept so existing links keep working.

# hyak — CC0 BGM Pack (full versions)

Original background music from the **hyak** YouTube channel ("에펙 없이 코드로 / how far can code go without After Effects"), released into the public domain under **CC0 1.0**. Six fully-original tracks (ep1, 3, 4, 5, 6, 7).

Every track is **100% synthesized in code** (Python + NumPy/SciPy) — no external audio samples, no paid libraries, no VSTs. The music *is* code: the exact builder script for each track is in [`src/`](src/). Run it, and it regenerates the track bit-for-bit (deterministic).

> **License: [CC0 1.0 Universal](LICENSE) (public domain dedication).**
> Use these tracks for anything — videos, games, streams, commercial projects — **no attribution required**. Attribution is welcome but never obligatory. See [LICENSE](LICENSE).

---

## Tracks

Each track ships as **FLAC** (lossless, in [`flac/`](flac/)) and **MP3 320 kbps** ([`mp3/`](mp3/)).

All six tracks are **fully original compositions**. (The ep2 "Tetris" track is an arrangement of an existing folk tune and is **not** part of this CC0 release — see below.)

| # | File | Theme | Length | BPM | Key / progression | Notes |
|---|------|-------|--------|-----|-------------------|-------|
| 1 | `hyak-ep1-rhythm` | Rhythm game | 2:40 | 180 | A minor · Am–F–C–G | Hard EDM / 전파 |
| 3 | `hyak-ep3-suika` | Suika (fruit merge) | 2:40 | 180 | D minor · Dm–B♭–C–A | Original |
| 4 | `hyak-ep4-blackhole` | Black hole | 2:38 | 200 | E minor · Em–G–D–Am (i–♭III–♭VII–iv) | Halftime / futurebase |
| 5 | `hyak-ep5-2048` | 2048 | 2:40 | 210 | A harmonic minor · Am–G–F–E | +2 key-up |
| 6 | `hyak-ep6-galaxy` | Galaxy collision | 2:40 | 210 | F major · FM7–G7–Em7–Am7 (Royal Road) | Cosmic / ambient, +2 key-up |
| 7 | `hyak-ep7-danmaku` | Bullet-hell dodge | 2:40 | 210 | C major · C–G–Am–F (I–V–vi–IV) | Kawaii futurebase, true stereo |

All tracks are complete standalone songs (intro → builds → choruses → breakdowns → final → natural ending) — **not loops**. The shorter loop edits used in the videos are separate.

---

## Regenerating from source

Tracks 1–6 depend only on the bundled synth engine [`src/hyak_synth.py`](src/hyak_synth.py):

```bash
pip install numpy scipy
cd src
python build_track_ep3_fullver.py   # writes hyak_ep3_fullver.wav
```

Rendering is deterministic — same script, same bytes (verified via SHA-256).

> **Note on ep7:** `build_track_ep7_fullver.py` additionally imports `duru_synth` (the author's shared low-level DSP module from a sibling project) for its stereo master chain. It will not run standalone without that module, but the rendered FLAC/MP3 are provided and are CC0 like the rest.

---

## Provenance & licensing basis

- **All six released tracks (ep1, 3, 4, 5, 6, 7)** — fully original compositions, synthesized entirely in code. No third-party material.
- **Track 7 (Danmaku)** — a fully original, code-synthesized track (an adaptation of the author's own composition from a sibling project). It contains **no material from Touhou Project or any third party**; the episode video is fan work, but this music stands on its own and is CC0.

### Excluded from this CC0 release

- **ep2 (Tetris)** is deliberately **not** included. Its melody is an arrangement of **"Korobeiniki"** — a public-domain Russian folk tune, but one strongly associated with the Tetris brand. To keep this release unambiguous and worry-free for anyone who reuses it, we only dedicate **fully original compositions** to the public domain. The ep2 arrangement remains all-rights-reserved by hyak.

The author (**hyak**) is the sole rights holder of these compositions and dedicates them to the public domain via CC0 1.0.

---

## Channel

▶ hyak — https://www.youtube.com/@Hyak-y0m

Made with Claude + code, no After Effects.
