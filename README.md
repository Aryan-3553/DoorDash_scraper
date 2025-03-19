# DoorDash Menu Scraper

### Objective
Create a simple automation to scroll through a DoorDash restaurant’s menu items, click on each item to open a detail modal, and capture the resulting data (name, price, description, etc.) from the GraphQL responses.

### Why Scrapybara?
DoorDash heavily employs Cloudflare to detect automated headless browsers. Scrapybara spins up a real cloud-based browser instance, lowering the chance of being flagged as a bot.

---

## Key Features

- **Remote Cloud Browser**  
  Initiates a Chrome instance in Scrapybara’s cloud environment, reducing detection risk.

- **Network Interception**  
  Utilizes Playwright to capture GraphQL calls that contain the menu’s data.

- **Address Input**  
  Some locations require an address for full menu access; the script can programmatically set it (e.g., “San Francisco, CA”).

- **Scrolling & Segmentation**  
  Divides the page into sections to ensure all items get clicked and processed.

---

## Approaches Considered

**Approach #1**  
Initially, I tried scrolling the page to find each menu item and clicking them individually. However, Cloudflare’s defenses often interfered—some requests never fully loaded, or I’d get blocked mid-way.

**Approach #2**  
The alternative strategy was to let the entire page load first, break it into sections, and then systematically click every item. This turned out to be significantly more dependable against Cloudflare restrictions, especially for pages with large menus.

### Errors I Encountered

1. **Location/Sign-In Requirements**  
   Some restaurants hide detailed item options unless you specify a location or even log in. Attempting to scrape without doing so often leads to incomplete data. I resolved this by programmatically entering an address (e.g., “San Francisco, CA”) within the script.  
   For full customization or certain exclusive items, you might need an actual DoorDash account. This adds complexity if Cloudflare or DoorDash detect too many suspicious logins.

2. **Permission Denied**  
   Early on, I saw permission-related errors in the console, often because the system’s Node installation lacked execution permissions. Reinstalling or granting the necessary rights for Playwright commands fixed it.

3. **Inconsistent Timing**  
   Sometimes the script would run fine, other times it would miss requests or time out. Adding more generous `await` calls, or capturing screenshots at each step, seemed to stabilize things. The root cause could be short bursts of rate limiting or random site load times.

4. **Selector Changes**  
   If DoorDash updates their frontend, the `[data-anchor-id="MenuItem"]` selectors might stop working. Inspect the site’s HTML in DevTools to confirm you’re using the correct attribute or class name.

---

## Installation with Rye and Running the Project

```bash
rye init
rye sync
source .venv/bin/activate

rye add scrapybara
rye add undetected-playwright-patch
rye add python-dotenv
rye add playwright

python doordash_scraper.py

