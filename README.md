# Zen AM Thumbnail Server

Flask webhook that generates Zen AM thumbnails on demand.
Called by n8n → returns base64 PNG.

---

## Deploy to Railway (5 min)

### Step 1 — GitHub repo
1. Go to github.com → New repository → name it `zen-am-thumbnail-server`
2. Upload ALL files from this folder:
   - app.py
   - requirements.txt
   - Procfile
   - railway.toml
   - zen_am_template.png  ← your clean base template
   - Antonio-Bold.ttf     ← your font file

### Step 2 — Railway
1. Go to railway.app → Login with GitHub
2. Click **New Project** → **Deploy from GitHub repo**
3. Select `zen-am-thumbnail-server`
4. Railway auto-detects Python and deploys
5. Go to **Settings → Networking → Generate Domain**
6. Copy your Railway URL — looks like: `https://zen-am-thumbnail-server-production.up.railway.app`

### Step 3 — Test it
```bash
curl -X POST https://YOUR-RAILWAY-URL/generate \
  -H "Content-Type: application/json" \
  -d '{"line1": "ITS RELEASE", "line2": "SEASON"}'
```
Should return JSON with `image_base64` field.

### Step 4 — Update n8n
In the **Generate Thumbnail** node, replace the Execute Command node with
an HTTP Request node pointing to:
`POST https://YOUR-RAILWAY-URL/generate`

---

## n8n HTTP Request Node Setup

- **Method**: POST  
- **URL**: `https://YOUR-RAILWAY-URL/generate`  
- **Body Type**: JSON  
- **Body**:
```json
{
  "line1": "{{ $('🤖 Claude — Episode Analyzer').first().json.thumbnailLine1 }}",
  "line2": "{{ $('🤖 Claude — Episode Analyzer').first().json.thumbnailLine2 }}"
}
```
- The response `image_base64` field contains the PNG ready to upload to YouTube.

---

## Free Tier Limits (Railway)
- $5/month free credit (enough for ~500 thumbnail generations)
- Sleeps after inactivity — first request may take 5-10 sec to wake up
- Upgrade to Hobby ($5/mo) if you need it always-on
