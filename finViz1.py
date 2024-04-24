import os
import re
import requests
import asyncio
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
from langchain.tools import BaseTool
from langchain.pydantic_v1 import BaseModel, Field

# Define the input model using Pydantic for data validation
class TickerInput(BaseModel):
    ticker: str = Field(description="Stock ticker symbol for the company.")

# Asynchronous function to fetch the webpage
async def get_webpage_async(page, url, approach=0):
    try:
        if approach == 0:
            await page.goto(url, timeout=60000)
            await asyncio.sleep(1)
        elif approach == 1:
            await page.goto(url, wait_until='networkidle', timeout=60000)
            await asyncio.sleep(5)
        elif approach == 2:
            await page.goto(url, wait_until='load', timeout=60000)
        elif approach == 3:
            await page.goto(url, timeout=60000)
            await page.wait_for_selector('body')

        content = await page.content()
        return content
    except Exception as e:
        print(f"Error loading page {url}: {e}")
        return "ERROR"

# Extract links from HTML data
def get_finviz_links(html_data):
    start_pos = html_data.find("Show Previous Ratings")
    if start_pos != -1:
        searchable_html = html_data[start_pos:]
        url_pattern = r'https?://[^\s"\';]*(?:(?<!["\';])\b)'
        urls_found = re.findall(url_pattern, searchable_html)
        unique_links = list(dict.fromkeys(urls_found))
        return unique_links[:10]
    return []

# Strip HTML tags and content from script and style tags
def html_strip_all_tags(html_string):
    script_style_pattern = re.compile(r'<\s*(script|style)[^>]*>.*?<\s*/\s*(script|style)\s*>', re.DOTALL | re.IGNORECASE)
    cleaned_html = re.sub(script_style_pattern, '', html_string)
    tags_and_entities_pattern = re.compile('(<.*?>)|(&[a-zA-Z]{3,4};)')
    cleaned_text = re.sub(tags_and_entities_pattern, '', cleaned_html)
    return cleaned_text

# Call OpenAI API for text summarization
def call_openai_get_summary(company_name, txt_data):
    YOUR_API_KEY = os.environ.get("OPENAI_API_KEY")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {YOUR_API_KEY}"
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": f"Summarize this text in 500 words or less with only information related to {company_name}:\n{txt_data}"}
        ],
        "max_tokens": 4096,
        "temperature": 0.5
    }
    response = requests.post(url, json=payload, headers=headers)
    if response.ok:
        response_data = response.json()
        return True, response_data['choices'][0]['message']['content']
    else:
        return False, "Request failed"

# Main function to summarize links
async def get_finviz_links_summary(page, ticker, url):
    html_data = await get_webpage_async(page, url)
    if 'ERROR' in html_data:
        return "Error: Unable to get FinViz web page."

    soup = BeautifulSoup(html_data, "html.parser")
    company_name = soup.title.string.replace("Stock Price and Quote", "")
    news_summary = ""        
    first_ten_links = get_finviz_links(html_data)
    for link_url in first_ten_links:
        webpage_content = await get_webpage_async(page, link_url)
        txt_data = html_strip_all_tags(webpage_content)
        if len(txt_data) > 500:
            success, summary_txt = call_openai_get_summary(company_name, txt_data)
            if success:
                news_summary += f"\n=========================\nReference: {link_url}\nSummary: {summary_txt}\n"
            else:
                print(f"Error calling OpenAI: {summary_txt}")

    return news_summary

# Define the tool that integrates with LangChain
class FinvizSummaryTool(BaseTool):
    name = "Finviz Summary Tool"
    description = "Fetches and summarizes news for a given stock ticker from FinViz."
    args_schema = TickerInput
    return_direct = True

    async def _arun(self, ticker: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            url = f"https://finviz.com/quote.ashx?t={ticker}&p=d"
            summary = await get_finviz_links_summary(page, ticker, url)
            await browser.close()
            return summary

    def _run(self, ticker: str) -> str:
        return asyncio.run(self._arun(ticker))

# Example of running the tool
if __name__ == "__main__":
    tool_instance = FinvizSummaryTool()
    result = asyncio.run(tool_instance._arun("AAPL"))
    print("News Summary:", result)
