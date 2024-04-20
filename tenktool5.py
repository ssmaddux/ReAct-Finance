from playwright.sync_api import sync_playwright
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool

class Tenk(BaseTool):
    name: str = "get_tenk"
    description: str = "Fetches a 10-k filing for a given company within the last year."

    def _run(self, ticker: str) -> str:
        
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False)
                page = browser.new_page()
                url = f"https://www.sec.gov/edgar/search/#/dateRange=custom&entityName={ticker}&startdt=2023-03-16&enddt=2024-04-10&filter_forms=10-K"
                page.goto(url)
        
                try:
                    # Click the initial link
                    page.click("a.preview-file", timeout=60000)
        
                    # Wait for the modal to appear
                    page.wait_for_selector('.preview-file', timeout=60000)
                    page.click('.btn.btn-warning')  # Click the button
        
                    # Wait for the new tab to open
                    new_page = browser.contexts[0].wait_for_event('page', timeout=30000)
        
                    if new_page:
                        new_url = new_page.url
                        print("New URL:", new_url)
        
                        # Scrape text from the new tab
                        page_text = new_page.evaluate('document.querySelector("body").innerText')
                        print(page_text)
                        print("Page content scraped successfully from the new tab.")
                        return page_text  # Return the page text as a string
                    else:
                        print("Timeout waiting for the new page.")
        
                except TimeoutError:
                    print("Modal did not appear or took too long to appear.")
        
                browser.close()
                print("Browser closed.")
        
                return ""  # Return an empty string if scraping fails

# Call the function
# if __name__ == "__main__":
#     def scrape_sec_page_text(ticker):
#     ticker = input("Enter ticker symbol: ")
#     scraped_text = scrape_sec_page_text(ticker)
#     print("Scraped Text:")
#     print(scraped_text)
