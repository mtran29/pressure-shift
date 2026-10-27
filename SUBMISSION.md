# Innovation Studio submission draft

## Project name
Pressure Shift: Explainable Live Match Intelligence

## Elevator pitch
Pressure Shift turns a synthetic football event stream into timely, explainable studio overlays. A transparent Python engine detects when a high press changes the opponent's buildup and when that tactical story shifts again. Microsoft Foundry's gpt-5-mini deployment expresses the verified facts as concise overlays, casual-fan explanations, analyst context, and a segment recap. Every insight links to supporting event IDs, so producers can inspect the evidence before putting a story on screen. A browser replay shows the full ingest, interpret, explain, render, and personalize pipeline without using real match footage or data.

## What to show in the under-two-minute video

1. **0–15s:** Explain the problem: stats alone do not explain a tactical shift. Show the fictional pitch replay.
2. **15–40s:** Red's press rises. Point to the timed overlay and evidence panel: three high recoveries, seven pressures, four failed exits.
3. **40–60s:** Switch Casual Fan ↔ Analyst to show different wording from the same verified fact packet.
4. **60–80s:** Blue starts passing through. Show the second overlay and that the earlier press story updates.
5. **80–100s:** Show the recap and briefly the Foundry deployment / model monitoring screen.
6. **100–110s:** Show public repo and simple architecture diagram; state that all data are synthetic.

Record the app functioning on your computer. Upload the video to a permitted public service and put its URL in Innovation Studio. Do not include copyrighted match footage or music.

## Architecture

`Synthetic event stream → Python window metrics → evidence packet → Microsoft Foundry gpt-5-mini → checked narrative → timed overlay + audience modes + recap`

## Judging access

The app can be run from the public repository with `python3 app.py` and no dependencies. With Foundry credentials configured on the host, the same app shows live Foundry-generated wording; otherwise it clearly labels local fallback copy. For a public hosted demo, configure the environment variables on the hosting platform. Never publish an API key.

## Submission checklist

- [ ] Public GitHub repository URL
- [ ] Public working demo or downloadable test build and instructions
- [ ] Public video URL, under two minutes, on YouTube / Vimeo / Facebook Video / Youku
- [ ] Pitch includes Microsoft Foundry and the problem solved
- [ ] Confirm all data and visuals are fictional
- [ ] Verify submitted links in a private browser window

