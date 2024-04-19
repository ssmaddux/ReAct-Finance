import requests
from bs4 import BeautifulSoup
from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool, StructuredTool, tool


class StockPrice(BaseTool):
    name = "get_stock_price"
    description = "Fetches the current stock price for a given ticker."

    def _run(self, ticker: str) -> str:

        try:
            # Construct the Yahoo Finance URL
            yahoo_url = f'https://finance.yahoo.com/quote/{ticker}'

            # Send a GET request to fetch the webpage
            response = requests.get(yahoo_url)
            response.raise_for_status()  # Raise an exception for HTTP errors

            # Parse the HTML content of the webpage
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find the element containing the stock price
            price_element = soup.find('div', {'class': 'D(ib) Mend(20px)'})

            # Extract the stock price text
            stock_price = price_element.text.strip()

            return stock_price
        except Exception as e:
            print(f"Error fetching stock price for {ticker}: {e}")
            return None

