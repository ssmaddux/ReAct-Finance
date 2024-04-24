from langchain_openai import ChatOpenAI
from langchain.agents import AgentType, create_react_agent, initialize_agent
from langchain.agents import Tool
from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
from yahootool2 import StockPrice
from tenktool5 import Tenk
from finViz import TenkSearchTool


llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.3)


tools = [YahooFinanceNewsTool(), StockPrice(), Tenk(), TenkSearchTool()]
agent_chain = initialize_agent(tools, llm, agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, verbose=True, handle_parsing_errors=True,)

agent_chain.invoke(
    "Get me the 10-k for salesforce.",
)
