import subprocess
from playwright.async_api import async_playwright
import asyncio
from langchain.tools import BaseTool, StructuredTool, tool

async def scrape_page_text(page):
    # Wait for the content to fully load
    await page.wait_for_load_state('networkidle')
    # Evaluate JavaScript code to get the text content of the modal elements
    page_text = await page.evaluate('document.querySelector("body").innerText')
    return page_text

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        await page.goto("https://www.sec.gov/edgar/search/#/dateRange=custom&entityName=crm&startdt=2023-03-16&enddt=2024-04-10&filter_forms=10-K")

        try:
            # clicks the initial link/pauses code
            await page.click("a.preview-file", timeout=60000)
            input("enter to continue")

            # waits for modal to appear
            await page.wait_for_selector('.preview-file', timeout=60000)  # Wait for the modal to appear
            await page.click('.btn.btn-warning')

            # Wait for the new tab to open
            new_page = None
            for _ in range(30):  # Try waiting for up to 30 seconds
                new_page = await browser.contexts[0].wait_for_event('page', timeout=1000)
                if new_page:
                    break

            if new_page:
                # Capture the new URL
                new_url = new_page.url
                print("New URL:", new_url)

                # Scrape text from the new tab
                page_text = await scrape_page_text(new_page)
                
                # Display scraped data using less
                less_process = subprocess.Popen(['less'], stdin=subprocess.PIPE)
                less_process.communicate(input=page_text.encode())
                print("Page content scraped successfully from the new tab.")
            else:
                print("Timeout waiting for the new page.")

        except TimeoutError:
            print("Modal did not appear or took too long to appear.")
        
        await browser.close()
        print("Browser closed.")

# Run the async function
if __name__ == "__main__":
    asyncio.run(main())
