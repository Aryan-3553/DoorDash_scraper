def generate_script(demonstrations):
    """
    Generates a Python script (as a single string) that uses the Playwright library
    to mimic user interactions described in the demonstration JSON, with added
    robust practices:
      - wait_for_selector before clicks
      - try/except blocks for missing elements
      - brief wait_for_timeout after each action
    """

    CHATGPT CONVERSATION LINK: https://chatgpt.com/share/67db4b08-98b0-800c-8e9c-85041e67338c


    script_lines = []

    # ---------------------------------------------------
    # 1) Create the initial script template and headers
    # ---------------------------------------------------
    script_lines.append("import asyncio")
    script_lines.append("from playwright.async_api import async_playwright")
    script_lines.append("")
    script_lines.append("async def run(playwright):")
    script_lines.append("    browser = await playwright.chromium.launch(headless=False)")
    script_lines.append("    page = await browser.new_page()")
    script_lines.append("")
    script_lines.append("    # -- Insert generated actions below --")

    # ---------------------------------------------------
    # 2) Access subtasks from the JSON
    # ---------------------------------------------------
    subtasks = demonstrations["trajectory_decomposition"]["subtasks"]

    for subtask in subtasks:
        # Each subtask typically has a description & action_descriptions
        subtask_comment = subtask["action_description"]["description"]
        script_lines.append(f"    # Subtask: {subtask_comment}")

        action_descriptions = subtask["action_description"]["action_descriptions"]

        for action_text in action_descriptions:
            # ----------------------------------------------------------------
            # 3) Map the textual description to robust Playwright code
            # ----------------------------------------------------------------

            # Quick example patterns:
            # "URL navigation to https://www.ubereats.com/"
            # "Click on the close button of location access modal."
            # "Type '2390 el camino real' into the delivery address input field."
            # "Scroll to explore featured items."
            
            # We'll place everything in a try/except to handle potential failures
            script_lines.append(f"    # {action_text}")

            if "URL navigation to " in action_text:
                # Extract the URL
                parts = action_text.split(" to ")
                if len(parts) > 1:
                    url = parts[1].strip()
                    script_lines.append("    try:")
                    script_lines.append(f"        await page.goto('{url}')")
                    # Wait until network is idle or some load state
                    script_lines.append("        await page.wait_for_load_state('networkidle')")
                    script_lines.append("        await page.wait_for_timeout(500)  # Short pause after navigation")
                    script_lines.append("    except Exception as e:")
                    script_lines.append("        print(f'[ERROR] Failed to navigate to URL:', e)")
                    script_lines.append("")
            
            elif "Click on " in action_text.lower():
                # You might parse out a more specific selector from the text
                # For now, we assume some placeholder
                selector = "selector_for_element"

                script_lines.append("    try:")
                script_lines.append(f"        await page.wait_for_selector('{selector}', timeout=5000)")
                script_lines.append(f"        await page.click('{selector}')")
                script_lines.append("        await page.wait_for_timeout(500)  # Brief pause")
                script_lines.append("    except Exception as e:")
                script_lines.append("        print(f'[ERROR] Failed to click element:', e)")
                script_lines.append("")

            elif action_text.lower().startswith("type '"):
                # Very simplistic approach to extract the typed text and field
                typed_selector = "selector_for_input"
                # Example: "Type '2390 el camino real' into the delivery address input field."
                # You can try a small parse to extract the text in quotes:
                import re
                match = re.search(r"Type '(.*?)' into", action_text, re.IGNORECASE)
                text_to_fill = match.group(1) if match else "example_text"

                script_lines.append("    try:")
                script_lines.append(f"        await page.wait_for_selector('{typed_selector}', timeout=5000)")
                script_lines.append(f"        await page.fill('{typed_selector}', '{text_to_fill}')")
                script_lines.append("        await page.wait_for_timeout(500)")
                script_lines.append("    except Exception as e:")
                script_lines.append("        print(f'[ERROR] Failed to fill input:', e)")
                script_lines.append("")

            elif "scroll" in action_text.lower():
                # Generic scroll
                script_lines.append("    try:")
                script_lines.append("        await page.evaluate('window.scrollBy(0, 800)')")
                script_lines.append("        await page.wait_for_timeout(500)")
                script_lines.append("    except Exception as e:")
                script_lines.append("        print(f'[ERROR] Scroll action failed:', e)")
                script_lines.append("")

            else:
                # Fallback if not recognized
                script_lines.append("    # Unrecognized action; insert custom logic if needed.")
                script_lines.append("    pass")
                script_lines.append("")

    # ---------------------------------------------------
    # 4) Close out the script
    # ---------------------------------------------------
    script_lines.append("    # -- End of generated actions --")
    script_lines.append("    await browser.close()")
    script_lines.append("")
    script_lines.append("async def main():")
    script_lines.append("    async with async_playwright() as p:")
    script_lines.append("        await run(p)")
    script_lines.append("")
    script_lines.append("if __name__ == '__main__':")
    script_lines.append("    asyncio.run(main())")

    final_script = "\n".join(script_lines)
    return final_script
