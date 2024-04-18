async def returned_yahoo_ticker(txt_data):
    txt_data = await yahoo_tool()
    success, ticker_amount = call_openai_get_summary_for_yahoo(txt_data)
    if success:
        print(f"Ticker amount: {ticker_amount}")
    else:
        print("Error occurred while fetching ticker amount")






def call_openai_get_summary_for_yahoo(txt_data):
    txt_data = txt_data[:4000] # only first 4k characters
    print(f"Calling OpenAI to summarize")
    API_KEY = os.environ.get("OPENAI_API_KEY")
    if not API_KEY:
        print("Error: OpenAi API key not found.")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {API_KEY}"
    }
    payload = {
        "model": "gpt-4",
        "messages": [
            {
                "role": "user",
                "content": f"Tell me information about apple from this text data. The ticker for apple is AAPL:\n{txt_data}"
            }
        ],
        "max_tokens": 4096,
        "temperature": 0,
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





async def yahoo_tool():
    ticker = 'AAPL'
    yahoo_url = f'https://finance.yahoo.com/quote/{ticker}?.tsrc=fin-srch'
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        yahoo_content = await get_webpage_async(page, yahoo_url)  # Pass page and yahoo_url
        cleaned_yahoo_content = html_strip_all_tags(yahoo_content)
        print(f"this is the yahoo content " + cleaned_yahoo_content)
        return cleaned_yahoo_content
