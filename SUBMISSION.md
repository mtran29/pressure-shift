# Innovation Studio draft

Public code repository: https://github.com/mtran29/pressure-shift

## Name

Pressure Shift: Live, Explainable Match Overlays

## Pitch

Pressure Shift turns a synthetic 11-v-11 football feed into timely on-screen explanations. A Python event engine detects a high press and the opponent's response from verified evidence. Microsoft Foundry's `gpt-5-mini` acts as an editorial agent, converting those evidence packets into concise overlays, fan and analyst explanations, English and Spanish versions, and a visual focus. The app renders the result directly over the live-style synthetic feed. Viewers see why the game changed without opening a statistics panel or using copyrighted match footage.

## Video plan, under two minutes

1. **0–12s:** Show the feed and say it is a fictional 10 Hz match, with no real footage.
2. **12–38s:** Press Play at 4×. Point to Red's closing run and the pressure cue, then the lower-third overlay appearing after the high recovery.
3. **38–55s:** Switch Fan ↔ Analyst and English ↔ Español while the same insight stays on screen.
4. **55–75s:** Show Blue's forward response and the second overlay. Point to the highlighted pass lane.
5. **75–95s:** Show the signal rail, evidence IDs, and recap.
6. **95–110s:** Show the Foundry model deployment and the code path `verified facts → editorial agent → validated overlay`. Explain what Foundry generated, and show the public repository.

## Architecture

`Generated 10 Hz tracking + fictional events → deterministic evidence packet → Foundry editorial agent → validated multilingual overlay + visual focus → synchronized match feed + recap`

## Honest scope

The synthetic trajectories are constrained by speed, acceleration, team shape, and broad public movement priors, but they are not a validated football simulation. This prototype uses one Foundry model call per candidate insight. It does not yet demonstrate Foundry evaluations, monitoring, or a multi-agent workflow, so do not describe it as a mature Foundry platform solution.

## Submission checklist

- [x] Public GitHub repository URL: https://github.com/mtran29/pressure-shift
- [ ] Demo video URL, under two minutes, hosted on a permitted public service
- [ ] Confirm the Foundry deployment is configured for the recorded demo
- [ ] Verify the app starts from a fresh clone with `python3 app.py`
- [ ] Confirm no API key, real match tracking, or copyrighted footage is published
