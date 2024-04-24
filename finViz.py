from bs4 import BeautifulSoup
import re
import requests
import os
from collections import OrderedDict
import asyncio
from playwright.async_api import async_playwright
import traceback
import time
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool
from typing import Optional, Type
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

class TenKInput(BaseModel):
    ticker: str = Field(description="stock ticker.")

async def get_webpage_async(page, url, approach=0):
    try:  
        if approach == 0:
            print(f"Getting {url} with wait 1 seconds.")
            await page.goto(url, timeout=60000)
            await asyncio.sleep(1) # wait for seconds seems like a questionable hack0
        elif approach == 1:
            print(f"Getting {url} with wait network idle.")
            await page.goto(url, wait_until='networkidle',timeout=60000)
            await asyncio.sleep(5) # wait for seconds seemed to much like a questionable hack
        elif approach == 2:
            print(f"Getting {url}  with wait for page load.")
            await page.goto(url, wait_until='load', timeout=60000) # timed out too much waiting for page load with lots of ads
        elif approach == 3:
            print(f"Getting {url}  with wait for body tag.")
            await page.goto(url, timeout=60000)
            await page.waitForSelector('body') # seemed reasonable compromise, look for body tag

        # Now, we grab the fully loaded content of the page
        content = await page.content()
        return content
    except Exception as e:
        print(f"Error loading page {url}: {e}")
        #traceback.print_exc()
        return "ERROR"  # Provides a graceful failure mode in case of error

def get_finviz_links(html_data):
    start_pos = html_data.find("Show Previous Ratings")
    first_ten_unique_links = []
    if start_pos != -1:
        searchable_html = html_data[start_pos:]
        url_pattern = r'https?://[^\s"\';]*(?:(?<!["\';])\b)'
        urls_found = re.findall(url_pattern, searchable_html)
        unique_links = list(OrderedDict.fromkeys(urls_found))
        first_ten_unique_links = unique_links[:10]
    return first_ten_unique_links

def html_strip_all_tags_old(html_string):
    # Enhanced pattern to handle spaces and improper slashes in script tags
    script_pattern = re.compile(r'<\s*script[^>]*>.*?<\s*/\s*script\s*>', re.DOTALL | re.IGNORECASE)
    no_script_html = re.sub(script_pattern, '', html_string)
    
    # Remove all remaining tags and HTML entities
    tags_and_entities_pattern = re.compile('(<.*?>)|(&[a-zA-Z]{3,4};)')
    cleaned_text = re.sub(tags_and_entities_pattern, '', no_script_html)
    
    return cleaned_text

def html_strip_all_tags(html_string):
    # Enhanced pattern to handle spaces and improper slashes in script and style tags
    script_style_pattern = re.compile(
        r'<\s*(script|style)[^>]*>.*?<\s*/\s*(script|style)\s*>',
        re.DOTALL | re.IGNORECASE
    )
    no_script_style_html = re.sub(script_style_pattern, '', html_string)

    # Handle iframes and other potentially problematic tags that can contain non-text content
    non_text_content_pattern = re.compile(
        r'<\s*(iframe|object|embed|applet)[^>]*>.*?<\s*/\s*(iframe|object|embed|applet)\s*>',
        re.DOTALL | re.IGNORECASE
    )
    cleaned_html = re.sub(non_text_content_pattern, '', no_script_style_html)
    
    # Remove all remaining tags and HTML entities
    tags_and_entities_pattern = re.compile('(<.*?>)|(&[a-zA-Z]{3,4};)')
    cleaned_text = re.sub(tags_and_entities_pattern, '', cleaned_html)
    
    return cleaned_text



def call_openai_get_summary(company_name,txt_data):
    txt_data = txt_data[:45000]
    print(f"Calling OpenAI to summarize for {company_name}")
    YOUR_API_KEY = os.environ.get("OPENAI_API_KEY")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {YOUR_API_KEY}"
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "user",
                "content": f"Summarize this text in 500 words or less with only information related to {company_name}:\n{txt_data}"
            }
        ],
        "max_tokens": 4096,
        "temperature": 0.5,
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.ok:
        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return True, response_data['choices'][0]['message']['content']
        else:
            print(f"OpenAI Error:No response choices found:{txt_data}")
            return False, "No response choices found."
    else:
        print(f"OpenAI Error:Response Not Ok:{txt_data}")
        return False, f"Request failed with status code: {response.status_code}"

async def get_finviz_links_summary(page, ticker, url):
    html_data = await get_webpage_async(page, url)

    if ('ERROR' in html_data):
            return "Error: Unable to get FinViz web page."

    soup = BeautifulSoup(html_data, "html.parser")
    company_name = soup.title.string.replace("Stock Price and Quote","")

    news_summary = ""        
    first_ten_links = get_finviz_links(html_data)
    count_content_chunks = 0
    for link_url in first_ten_links:
        webpage_content = await get_webpage_async(page, link_url)
        txt_data = html_strip_all_tags(webpage_content)
        if len(txt_data) > 500: # only if the content is over 500 characters
            success, summary_txt = call_openai_get_summary(company_name,txt_data)
            if (success):
                count_content_chunks += 1
                news_summary += f"=========================\n"
                news_summary += f"Reference: {link_url}\n"
                news_summary += f"Summary: {summary_txt}\n\n"
            else:
                print(f"Error Calling OpenAI: {summary_txt}")
            if count_content_chunks > 2: 
                break

    return news_summary

class TenkSearchTool(BaseTool):
    name = "tenk_search"
    description = "Looks up 10-k filings for a given company"
    args_schema: Type[BaseModel] = TenKInput

    def _run(
        self, ticker: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool."""
        return "LangChain"

    async def _arun(
        self, ticker: str, run_manager: Optional[AsyncCallbackManagerForToolRun] = None
    ) -> str:
        """Use the tool asynchronously."""
        raise NotImplementedError("custom_search does not support async")
     
async def main(ticker: str)-> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Launch browser once
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36'
        context = await browser.new_context(user_agent=user_agent)  
        page = await browser.new_page()
        
        # Prompt user for ticker symbol
        # ticker = input("Please enter the ticker symbol of the company (e.g., AAPL for Apple, CRM for Salesforce): ")
        fin_viz_url = f"https://finviz.com/quote.ashx?t={ticker}&p=d"
        summary = await get_finviz_links_summary(page, ticker, fin_viz_url)

        # TEST CODE
        #html_data = await get_webpage_async(page, "https://www.chrisclark.com")
        #success, summary = call_openai_get_summary(ticker,html_data)

        if len(summary) > 10:
            print(f"Here's the news summary for {ticker}:\n\n{summary}")
        await browser.close()  # Ensure the browser is closed after operations

if __name__ == "__main__":
    asyncio.run(main())
