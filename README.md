# Pressure Shift

A fictional 70-second, 11-v-11 match feed that shows AI insights as **timed graphical overlays while the match is playing**. Red's press becomes an overlay only after two close challenges, a failed Blue exit, and a high recovery. A second overlay appears when Blue completes two forward passes after restarting. Fan and analyst modes, plus English and Spanish, change the explanation on the same feed.

## Run

Python 3.10+; no third-party packages.

```bash
python3 app.py
```

Open <http://localhost:8000>. Wait until the status says **Ready**, then press **Play**. Use **Jump to: Red's press** and **Blue's response** to inspect each overlay immediately, or use **4× demo** to see both in about 18 seconds. Fan, Analyst, and language controls change the wording while an overlay is visible. Use **1×** to inspect player movement.

The app works without cloud credentials and labels those outputs **Local editorial fallback**. For a live Foundry response, the server reads the environment variables listed in [`.env.example`](.env.example); the API key remains on the server.

## How it works

1. `simulation.py` generates a seeded 10 Hz scene in pitch metres. It maintains 22 independent positions and velocities with acceleration and speed limits, support runs, and coordinated team shifts. Pass destinations come from each receiver's generated position at arrival.
2. `insights.py` counts completed fictional events and emits evidence packets only after the high press and Blue's response have happened.
3. `foundry.py` sends verified facts to Microsoft Foundry's `gpt-5-mini`. Its editorial output contains English and Spanish overlays, fan and analyst explanations, a rationale, evidence IDs, and a visual focus. The server validates these fields before display. A local preview keeps overlays timely if the model is slow or unavailable.
4. `static/index.html` renders the moving match scene, pressure cue, highlighted zone or pass lane, synchronized lower-third overlays, signal rail, and recap.

The pitch is an **illustration of a generated match**, not reconstructed video or measured player tracking. The mock score, teams, and players are fictional. No Premier League match data or footage is used.

## What SkillCorner informed

The [official SkillCorner open-data repository](https://github.com/SkillCorner/opendata) provides a public 10 Hz tracking sample. We examined the opening 8m43s of match `1874553` only to set broad movement priors. Its one-second player displacement had a median of **1.95 m**, p90 **4.40 m**, and p99 **6.65 m**. `tools/analyze_tracking_reference.py` recomputes these values from a separately obtained file.

For comparison, the new generated scene's one-second displacement median is **1.76 m**, p90 **4.91 m**, and p99 **6.55 m**. Matching broad movement rates does not prove realistic tactics or off-ball decisions.

No real tracking frame, path, player identity, or event from SkillCorner is bundled in the app or served by the API. The reference repository is [MIT licensed](https://github.com/SkillCorner/opendata/blob/master/LICENSE); credit: Copyright (c) 2020 SkillCorner.

## Verify

```bash
python3 -m unittest discover -s tests -v
```

The tests check 10 Hz cadence, speed and pitch bounds, close-range pressure, continuous possession ownership, evidence timing, and output grounding. These checks establish internal consistency, not visual equivalence to real tracking.
