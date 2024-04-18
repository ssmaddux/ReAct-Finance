from langchain_openai import ChatOpenAI
from langchain.agents import AgentType, create_react_agent, initialize_agent
from langchain.agents import Tool
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
from yahootool2 import get_stock_price
from tenktool5 import main


llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.3)
ticker = input("Enter the stock ticker (e.g., AAPL): ").upper()
stock_price_tool = get_stock_price(ticker)

tools = [YahooFinanceNewsTool(), get_stock_price]
agent_chain = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True, handle_parsing_errors=True,)

agent_chain.invoke(
    "What is salesforces latest stock options price. Also is there any recent news about salesforce you can provide?",
)
