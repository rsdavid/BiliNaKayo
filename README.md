# BiliNaKayo! Auto-Poster

Every hour this makes a short cartoon video (about 8 seconds, with a Taglish voiceover and subtitles) for the next product in your list and posts it as a Reel on your **BiliNaKayo!** Facebook Page. Your affiliate link goes in the first comment. It runs for free in the cloud on GitHub, so your computer can stay off.

## How it works

1. You add products (name, price, affiliate link, optional image link) to `data/products.csv`.
2. Each hour, the bot takes the first product marked `ready`.
3. Claude writes the hook, voiceover and caption (or a plain template if you skip the Claude key).
4. A cartoon video is drawn (mascot "Bili", product card, price sticker, subtitles, "LINK SA COMMENTS" button).
5. The Reel is posted, the link goes in the first comment, and the product is marked `posted`.

The video always carries a `#ad` tag and the caption has an affiliate disclosure.

---

## Setup (one time, about 45 minutes)

### Step 1: Get your Facebook Page ID and token

1. Go to https://developers.facebook.com, log in with the Facebook account that manages BiliNaKayo!, and create an **App** (type: Business, or "Other").
2. Open the **Graph API Explorer** (Tools menu). Choose your app, click **Generate Access Token**, and tick these permissions:
   `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`, `pages_manage_engagement`.
3. Turn that short token into a long one by opening this address in your browser (fill in the capitals):
   `https://graph.facebook.com/v26.0/oauth/access_token?grant_type=fb_exchange_token&client_id=APP_ID&client_secret=APP_SECRET&fb_exchange_token=SHORT_TOKEN`
4. Copy the `access_token` it shows, then open:
   `https://graph.facebook.com/v26.0/me/accounts?access_token=LONG_TOKEN`
5. Find **BiliNaKayo!** in the list. Its `id` is your **Page ID** and its `access_token` is your **Page token** (this one does not expire).

Keep both private. If you get stuck on this step, ask Claude and paste the error message.

### Step 2: Put the project on GitHub

1. Make a free account at https://github.com and create a **new repository** (name it `bilinakayo`).
2. Upload all the files from this folder, including the hidden `.github` folder. (Dragging the whole folder contents onto the "uploading an existing file" page works.)
3. In the repository go to **Settings > Secrets and variables > Actions > New repository secret** and add:
   - `FB_PAGE_ID`: your Page ID
   - `FB_PAGE_TOKEN`: your Page token
   - `ANTHROPIC_API_KEY`: optional. Get one at https://console.anthropic.com. It costs a very small amount per post (the model used is Claude's cheapest). Without it, the bot uses simple template captions.

### Step 3: Test it

1. Add at least one real product to `data/products.csv` (see below) with status `ready`.
2. Go to the **Actions** tab, choose **Post to BiliNaKayo**, click **Run workflow**.
3. Watch the run. A green check means it posted. A red X means open the run and read the message (usually a token or permission problem).

After that it runs by itself every hour.

---

## Adding products

Open `data/products.csv` on GitHub and click the pencil icon. One product per row:

| column | what to put |
|---|---|
| `platform` | Lazada, Temu, Amazon or TikTok |
| `title` | the product name (long names are fine; Claude shortens them) |
| `price` | e.g. `599` (pesos assumed; use `$12.99` for dollars) |
| `image_url` | optional: a direct link to the product photo. If empty, the bot tries to find one, and if that fails it draws a gift box |
| `link` | **your affiliate link** |
| `status` | `ready` to post. Anything else (`skip`, `needs_link`) is ignored |

The bot posts rows from top to bottom. It warns in the run log when fewer than 5 products are left, so add products in batches (30 at a time is about a day and a half).

Only use product photos you are allowed to use. Your affiliate program's own image or banner tools are the safest source.

## Settings

- **Posting hours:** by default it posts from 6:00 AM to 11:59 PM Philippine time (18 posts a day). To change it, go to **Settings > Secrets and variables > Actions > Variables**, add `ACTIVE_HOURS` with a value like `0-24` (all day and night) or `8-22`.
- **Background music:** drop royalty-free `.mp3` files you have the rights to into `assets/music/`. They play quietly under the voice. No music is included, because copyrighted music can get your Reels muted or removed.
- **Voice:** it uses a free Filipino text-to-speech voice. If that service is ever unavailable, the video is posted with subtitles and no voice.

## Good to know

- Facebook allows 30 API-posted Reels per 24 hours, so hourly is within the limit. Posting too much can still reduce reach, so watch your results and adjust `ACTIVE_HOURS`.
- GitHub's hourly schedule can run a few minutes late. That is normal.
- A private repository gets 2,000 free minutes per month. Each run takes about 1 to 2 minutes, so 18 posts a day fits.
- If GitHub ever pauses the schedule after a long quiet period, open the Actions tab and click **Enable workflow**.
- Temu and TikTok Shop links come from your affiliate dashboards, so they must be pasted in by you. Amazon links can be made by adding your `tag=` to the product address.

## Test on your own computer (optional)

```
pip install -r requirements.txt
python main.py --sample --dry-run
```
This makes a sample video in the `output` folder and posts nothing. It needs Python and ffmpeg installed.
