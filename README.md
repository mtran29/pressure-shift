# Pressure Shift

A fictional 70-second, 11-v-11 match feed that shows AI insights as **timed graphical overlays while the match is playing**. Red's press becomes an overlay only after two close challenges, a failed Blue exit, and a high recovery. A second overlay appears when Blue completes two forward passes after restarting. Fan and analyst modes, plus English and Spanish, change the explanation on the same feed.

## Run

Python 3.10+; no third-party packages.

```bash
python3 app.py
```

Open <http://localhost:8000>. Wait until the status says **Ready**, then press **Play**. Use **Jump to: Red's press** and **Blue's response** to inspect each overlay immediately, or use **4× demo** to see both in about 18 seconds. Fan, Analyst, and language controls change the wording while an overlay is visible. Use **1×** to inspect player movement. The demo works without Azure credentials with an explicitly labeled local editorial fallback. If the status says **Load failed**, check that this server is running and reload the page.

## Connect Microsoft Foundry

Use the existing `gpt-5-mini` deployment in the `pressure-shift` Foundry project. Get its Azure OpenAI endpoint and key from **Continue in code**, then set:

```bash
export AZURE_OPENAI_ENDPOINT='https://YOUR-RESOURCE.openai.azure.com'
export AZURE_OPENAI_API_KEY='YOUR-KEY'
export AZURE_OPENAI_DEPLOYMENT='gpt-5-mini'
python3 app.py
```

Never commit the key. `foundry.py` calls the model when a candidate insight is emitted. The browser first shows a grounded local preview, then updates it with the Foundry response if available. A slow model therefore does not hold the live overlay. The backend validates evidence IDs, focus ID, visual kind, and length before displaying model output. The key stays server-side.

If a Python.org installation on macOS reports `CERTIFICATE_VERIFY_FAILED`, the app uses the system CA bundle at `/etc/ssl/cert.pem` when Python has no certificates configured. Restart `app.py` after updating the code because editorial responses are cached for the running process. TLS verification remains enabled.

Foundry's role is **editorial**, not metric calculation: it decides concise wording for two audiences and two languages, gives a reason for the overlay, and selects a supported event and visual focus. The Python engine determines physical events and counts. This is a useful Foundry integration, but a serious **Best Use of Microsoft Foundry** entry would also need Foundry evaluations, monitoring evidence, and a more sophisticated editorial workflow. Do not claim that the current prototype alone demonstrates those capabilities.

## Rebuilt data pipeline

1. `simulation.py` generates a new seeded 10 Hz scene in pitch metres. It maintains 22 independent positions and velocities with acceleration and speed limits, changing support targets, coordinated team shifts, and short player-specific runs. Pass destinations are taken from the receiver's *generated* position at arrival; the ball continues with that receiver until the next action. No earlier project event script is used.
2. `insights.py` counts completed fictional events and emits evidence packets at 36.2 s and 59.6 s in this scene.
3. `foundry.py` produces a validated editorial decision: English/Spanish overlay, fan/analyst explanation, rationale, event IDs, and visual kind.
4. `static/index.html` renders a synthetic match feed with a scoreboard, 22 moving players, a moving ball, pressure cues, a highlighted zone or pass lane, and lower-third overlays at the detection times. A separate rail shows the underlying signals and event trail. The recap combines the two checked editorial decisions when the passage finishes.

The pitch is an **illustration of a generated match**, not reconstructed video or measured player tracking. The mock score, teams, and players are fictional. No Premier League match data or footage is used.

## What SkillCorner informed

The [official SkillCorner open-data repository](https://github.com/SkillCorner/opendata) contains 10 Australian A-League matches with 10 fps tracking, ball position, possession, and detected/extrapolated flags. We inspected a byte-range prefix of one official JSONL file (match `1874553`), representing its opening 8m43s. In that prefix, 4,173 frames had 22 player positions; roughly half the player points were flagged detected. One-second player displacement had a median of **1.95 m**, p90 **4.40 m**, and p99 **6.65 m**. These are broad reference priors, not a learned physical model. `tools/analyze_tracking_reference.py` recomputes them from a separately obtained file. The generated scene has a 10 Hz cadence and a 6.7 m/s outfield speed cap. Its movement remains a simplification of real football.

For comparison, the new generated scene's one-second displacement median is **1.76 m**, p90 **4.91 m**, and p99 **6.55 m**. Matching broad movement rates does not prove realistic tactics or off-ball decisions.

No real tracking frame, path, player identity, or event from SkillCorner is bundled in the app, served by the API, or included in the archive. The repository is [MIT licensed](https://github.com/SkillCorner/opendata/blob/master/LICENSE); credit: Copyright (c) 2020 SkillCorner.

## Verify

```bash
python3 -m unittest discover -s tests -v
```

The tests check 10 Hz cadence, speed and pitch bounds, close-range pressure, continuous possession ownership, evidence timing, and output grounding. These checks establish internal consistency, not visual equivalence to real tracking.
