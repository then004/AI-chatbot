# Reddit market validation setup

P3 is opt-in and does not crawl automatically. Create a Reddit personal-use script app, then set local environment variables without committing them:

```powershell
$env:REDDIT_CLIENT_ID='your-client-id'
$env:REDDIT_CLIENT_SECRET='your-client-secret'
$env:REDDIT_USER_AGENT='startup-research/0.1 by your-reddit-name'
```

Without all three values, proposal confirmation returns `blocked` and sends no network request. The app uses PRAW only after explicit proposal confirmation. Fast/standard/deep limits and Reddit rate limits apply; domestic network/proxy restrictions may prevent access. Do not paste credentials into the UI or commit `.env` files.

After configuring credentials, start FastAPI on `127.0.0.1:8100`, create a proposal in the Market Validation page, review/edit its query and subreddit list, and select Confirm. The task should move queued → running → succeeded or failed; the run endpoint then exposes source permalinks and the structured analysis. This manual path was not executed in this environment because no real credentials were used.
