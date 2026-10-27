# Pressure Shift

A synthetic match insights demo for the Microsoft × Premier League Inside the Game hackathon. It replays fictional football events, detects changes in high pressure with deterministic Python rules, and uses a Microsoft Foundry model deployment to write evidence-backed overlays and two audience versions.

## Run locally

Requires Python 3.10 or newer. No third-party packages are required.

```bash
python3 app.py
```

Open <http://localhost:8000>. The demo runs with clearly labeled local fallback wording until Foundry is configured.

## Connect Microsoft Foundry

In your `pressure-shift` Foundry project, open the `gpt-5-mini` deployment, choose **Continue in code**, and copy the **Azure OpenAI endpoint** and key. Set them as environment variables in your shell or hosting service. Keep the key private; never commit it.

```bash
export AZURE_OPENAI_ENDPOINT='https://YOUR-RESOURCE.openai.azure.com'
export AZURE_OPENAI_API_KEY='YOUR-KEY'
export AZURE_OPENAI_DEPLOYMENT='gpt-5-mini'
python3 app.py
```

The backend calls `POST {endpoint}/openai/v1/chat/completions` using the deployment name, with minimal reasoning effort. It sends compact computed facts and event IDs, validates the returned IDs, and falls back to local wording if the call fails. The UI identifies the source of each explanation. The key never reaches the browser.

## How it works

1. `engine.py` generates a deterministic, fictional five-minute passage with continuous possessions. Consecutive passes share endpoints; shots, recoveries, and goal kicks explain changes of possession.
2. Adjacent 100-second windows are compared for high recoveries, attacking-third pressures, failed exits, and successful progressive passes. Blue attacks right, so Red's high press occurs at x ≤ 33 in Blue's defensive third.
3. Two triggered insights cover a press surge and the opponent's response.
4. `app.py` asks Foundry to express each evidence packet as an overlay plus casual and analyst explanations.
5. `tracking.py` generates a separate 11-v-11 synthetic tracking layer. Event actors and completed-pass recipients arrive at the recorded coordinates, while off-ball players hold a shifting 4-3-3 shape.
6. The browser renders the timed pitch replay, evidence panel, audience modes, and a segment recap.

The replay clock advances continuously. At the default **1×** speed, one wall-clock second equals one match second; **8×** completes the five-minute passage in about 37 seconds for a demo. The ball moves along pass and shot paths between tagged timestamps. The 22 numbered players move between half-second tracking frames. The positions are procedural, not video-derived tracking data.

All clubs, players, events, and coordinates are fictional. This project uses no Premier League match data or match footage.

## Verify

```bash
python3 -m unittest discover -s tests -v
```

For judging, the app can be run locally from this repository. An Azure hosted instance can use the same environment variables. The demo video should show the live app and briefly show the Foundry model deployment and evaluation.
