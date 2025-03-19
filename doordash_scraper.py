import asyncio
import json
import time
import os
import math

from dotenv import load_dotenv
from scrapybara import Scrapybara
from undetected_playwright.async_api import async_playwright


load_dotenv()
SCRAPYBARA_API_KEY = os.getenv("SCRAPYBARA_API_KEY")

async def get_scrapybara_browser():
    """
    Starts a Scrapybara browser instance using the SCRAPYBARA_API_KEY from env (.env).
    """
    if not SCRAPYBARA_API_KEY:
        raise ValueError("SCRAPYBARA_API_KEY not set in environment or .env file!")

    client = Scrapybara(api_key=SCRAPYBARA_API_KEY)
    instance = client.start_browser()
    return instance

async def setup_address(page):
    """
    1. Simulate entering an address (San Francisco, CA).
    2. Accept address suggestions.
    3. Click Save.
    4. Dismiss any 'outside area' modal with ESC.

    This function can be adjusted or skipped depending on the store/region specifics.
    """
    print(">>> Setting address to 'San Francisco, CA'...")

    try:
        # Wait for the address button and click it
        await page.wait_for_selector('[data-testid="addressTextButton"]', state="visible", timeout=10000)
        await page.locator('[data-testid="addressTextButton"]').click()

        # Fill the address input
        await page.wait_for_selector('[data-testid="AddressAutocompleteField"]', state="visible", timeout=10000)
        await page.get_by_test_id("AddressAutocompleteField").first.fill("San Francisco, CA")
        await asyncio.sleep(1)

        await page.keyboard.press("Enter")
        await asyncio.sleep(1)

        await page.wait_for_selector('[data-anchor-id="AddressEditSave"]', state="visible", timeout=8000)
        await page.locator('[data-anchor-id="AddressEditSave"]').click()
        await asyncio.sleep(2)

        await page.keyboard.press("Escape")
        await asyncio.sleep(1)

        print(">>> ADDRESS SETUP COMPLETE")
    except Exception as e:
        print(f"[WARNING] Address setup step encountered an error: {e}")


async def process_section(page, section_idx, start_y, seen_items):
    """
    Scroll to the given position on the page, find all [data-anchor-id="MenuItem"] items,
    click each item to open its detail modal, then press ESC to close the modal.

    This triggers the network request for item details, captured by our response handler.
    """
    print(f"\n>>> Processing section {section_idx} | scroll position: {start_y} px")
    # Scroll to the correct vertical position
    await page.evaluate(f"window.scrollTo(0, {start_y})")
    await asyncio.sleep(1.5)  # Give time for the section to load

    # Grab all item locators
    items = await page.locator('[data-anchor-id="MenuItem"]').all()
    print(f"[INFO] Found {len(items)} menu items in section {section_idx}")

    # Attempt to click each item to force the itemPage GraphQL request
    item_click_count = 0
    for idx, item in enumerate(items):
        try:
            # Some items may not be visible or clickable; check if it has text
            item_text = await item.text_content()
            if not item_text:
                continue

            # If we haven't seen an item with exactly that text, let's attempt a click
            if item_text not in seen_items:
                await item.click()
                # Wait a bit to let the item modal and network request fire
                await asyncio.sleep(0.5)

                # Press ESC to close the modal
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.3)

                seen_items.add(item_text)
                item_click_count += 1
        except Exception as e:
            print(f"[ERROR] Section {section_idx}, item {idx}: {e}")

    print(f"[INFO] Finished section {section_idx}; clicked {item_click_count} new items.")


async def retrieve_menu_items(instance, start_url: str):
    """
    1. Connect to the remote Scrapybara browser via CDP URL.
    2. Navigate to the DoorDash store page.
    3. Setup address if needed.
    4. Scroll in 'sections' to load all items, clicking each to trigger item detail requests.
    5. Capture each response to the 'https://www.doordash.com/graphql/itemPage?operation=itemPage'.
    6. Return the collected item data as a list of dictionaries.
    """

    menu_items = []
    seen_items = set()

    start_time = time.time()

    # Retrieve CDP URL from the instance
    cdp_url = instance.get_cdp_url().cdp_url

    # Connect with async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp_url)
        page = await browser.new_page()

        async def response_handler(response):
            try:
                # This is the GraphQL item detail request for a single item
                if "graphql/itemPage?operation=itemPage" in response.url and response.status == 200:
                    json_data = await response.json()
                    menu_items.append(json_data)
                    print(f"[DEBUG] Captured item JSON from {response.url}")
            except Exception as err:
                print(f"[ERROR] Could not parse item JSON: {err}")

        page.on("response", response_handler)

        # 4) Go to the DoorDash store
        print(f"\n>>> Navigating to {start_url}")
        await page.goto(start_url, wait_until="networkidle")
        print("[INFO] Page loaded")

        # Setup address (some restaurants may require location set)
        await setup_address(page)
        await asyncio.sleep(2)

        # 5) Determine how many "sections" to scroll through
        total_height = await page.evaluate("document.body.scrollHeight")
        viewport_height = await page.evaluate("window.innerHeight")

        # If the page has no content or we can't measure, fallback
        if not viewport_height or viewport_height <= 0:
            viewport_height = 1000

        sections = math.ceil(total_height / viewport_height)
        print(f"\n[INFO] Document height: {total_height}px, viewport: {viewport_height}px.")
        print(f"[INFO] We will scroll ~{sections} sections to ensure everything loads.")

        # 6) Scroll section by section, gather items
        for i in range(sections):
            start_y = i * viewport_height
            await process_section(page, i, start_y, seen_items)

        # Additional wait to ensure all requests are completed
        await asyncio.sleep(2)
        await page.close()
        await browser.close()

    elapsed = time.time() - start_time
    print(f"\n>>> Total unique items found: {len(menu_items)}")
    print(f">>> Elapsed time: {elapsed:.2f} seconds")
    return menu_items


async def main():
    instance = await get_scrapybara_browser()
    try:
        # Change to whichever store you'd like
        store_url = (
            "https://www.doordash.com/store/panda-express-san-francisco-980938/12722988/?event_type=autocomplete&pickup=false"
        )

        print(f"\n[INFO] Starting scrape for: {store_url}")
        data = await retrieve_menu_items(instance, store_url)

        print(f"\n[INFO] Retrieved {len(data)} items of data from the store.")
        if data:
            with open("menu_items.json", "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            print("[INFO] menu_items.json has been saved.")
        else:
            print("[WARNING] No item data captured.")

    finally:
        instance.stop()
        print("[INFO] Scrapybara instance stopped.")

if __name__ == "__main__":
    asyncio.run(main())
