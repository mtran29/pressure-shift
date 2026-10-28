# Fast submission and deployment steps

## 1. Test locally

```bash
cd /Users/minhtran/Documents/Codex/2026-10-14/tj/outputs/pressure-shift
python3 -m unittest discover -s tests -v
python3 app.py
```

Open <http://localhost:8000>, press **Play**, and confirm that two overlays and a recap appear over the 70-second illustrated feed. At the default 4× speed this takes about 18 seconds. The first run is labeled **Local editorial fallback** until Foundry is configured.

## 2. Connect the Foundry deployment

Open the `gpt-5-mini` deployment in your `pressure-shift` Foundry project and select **Continue in code**. Its displayed Responses URL ends in `/openai/v1/responses`; this app uses the same resource's base URL to call Chat Completions. In a new Terminal window, set:

```zsh
export AZURE_OPENAI_ENDPOINT='https://pressure-shift-foundry.services.ai.azure.com'
export AZURE_OPENAI_DEPLOYMENT='gpt-5-mini'
read -s 'AZURE_OPENAI_API_KEY?Paste Foundry API key: '
export AZURE_OPENAI_API_KEY
python3 app.py
```

Do not paste the key into chat, GitHub, screenshots, or the demo video. Run the replay again. The overlay source should say **Microsoft Foundry · gpt-5-mini**. If it says **Local editorial fallback**, check the API's `reason` field without sharing secrets.

## 3. Publish the code

Create an empty **public** GitHub repository at <https://github.com/new>. Give it a name such as `pressure-shift`. Do not add GitHub's initial README because this folder already has one. Then:

```bash
cd /Users/minhtran/Documents/Codex/2026-10-14/tj/outputs/pressure-shift
git remote add origin https://github.com/YOUR-USERNAME/pressure-shift.git
git push -u origin main
```

If GitHub asks you to sign in, complete its browser authentication flow. Check the public repository in a private window. The `.env` file and Python cache are ignored by Git.

## 4. Host the app on Azure Container Apps

This is the preferred path if time allows. In Azure Cloud Shell or a terminal with Azure CLI, use the [official `az containerapp up` guide](https://learn.microsoft.com/en-us/azure/container-apps/containerapp-up) to deploy the public GitHub repo. The Dockerfile exposes port 8000.

```bash
az containerapp up \
  --name pressure-shift-demo \
  --resource-group pressure-shift-rg \
  --location eastus \
  --repo https://github.com/YOUR-USERNAME/pressure-shift \
  --ingress external
```

This command may create a Container Apps environment, registry, and Log Analytics workspace, which use Azure credit. Once the app exists, set the endpoint and deployment name as environment variables. Store the API key as a Container Apps secret, then reference that secret as an environment variable. See [Microsoft's secret instructions](https://learn.microsoft.com/en-us/azure/container-apps/manage-secrets). In the Azure portal, use **Secrets** to add a secret named `foundry-key`; use **Containers → Environment variables** to set `AZURE_OPENAI_API_KEY` from that secret. Set `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_DEPLOYMENT` as plain environment variables. Restart or create a revision after changing the environment.

Test the public app URL in a private window. Keep it available through judging, per the hackathon rules.

## 5. Video and Innovation Studio

Follow `SUBMISSION.md` for a 110-second demo outline and pitch. Upload the video publicly to a permitted service. In Innovation Studio include the GitHub URL, video URL, pitch, and working app URL or runnable test build instructions. Confirm all links work without your login.
