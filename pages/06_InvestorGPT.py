import streamlit as st
import os
import requests
from langchain.schema import SystemMessage
from langchain.agents import initialize_agent, AgentType
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Any, Type
from langchain.chat_models import ChatOpenAI
from langchain.utilities import DuckDuckGoSearchAPIWrapper

st.set_page_config(
    page_icon="🤖",
    page_title="InvestorGPT",
)

st.markdown(
    """
    # InvestorGPT

    InvestorGPT에 오신것을 환영합니다!

    회사 이름을 입력해서 시작하세요.

    에이전트가 당신에게 정보를 찾아줄 것입니다.
    """
)

llm = ChatOpenAI(temperature=0.1, model="gpt-4o")

alpha_vantage_api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")


class StockMarketSymbolSearchToolArgsSchema(BaseModel):
    query: str = Field(description="The query you will search for")


class CompanyOverviewArgsSchema(BaseModel):
    symbol: str = Field(description="Stock symbol of the company. Example: AAPL, TSLA")


class CompanyOverviewTool(BaseTool):
    name = "CompanyOverview"
    description = """
    Use this to get an overview of the financials of the company.
    You should enter a stock symbol.
    """
    args_schema: Type[CompanyOverviewArgsSchema] = CompanyOverviewArgsSchema

    def _run(self, symbol):
        r = requests.get(
            f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={alpha_vantage_api_key}"
        )
        return r.json()


class StockMarketSymbolSearchTool(BaseTool):
    name = "StockMarketSymbolSearchTool"
    description = """
    Use this tool to find the stock market symbol for a company.
    It takes a query as an argument.
    Example query: Stock Market Symbol for Apple Company
    """
    args_schema: Type[StockMarketSymbolSearchToolArgsSchema] = (
        StockMarketSymbolSearchToolArgsSchema
    )

    def _run(self, query):
        try:
            # Alpha Vantage SYMBOL_SEARCH API 사용
            endpoint = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={query}&apikey={alpha_vantage_api_key}"
            response = requests.get(endpoint)
            data = response.json()
            print(f"DATA: {data}\n\n")

            if "bestMatches" in data and len(data["bestMatches"]) > 0:
                matches = data["bestMatches"]
                results = []

                for match in matches[:3]:  # 상위 3개 결과만 표시
                    symbol = match["1. symbol"]
                    name = match["2. name"]
                    market = match["4. region"]
                    results.append(f"{symbol}: {name} ({market})")

                return "검색 결과:\n" + "\n".join(results)
            else:
                return f"'{query}'에 대한 주식 심볼을 찾을 수 없습니다."

        except Exception as e:
            return f"심볼 검색 중 오류 발생: {str(e)}"


class CompanyIncomeStatementTool(BaseTool):
    name = "CompanyIncomeStatement"
    description = """
    Use this to get the income statement of a company.
    You should enter a stock symbol.
    """
    args_schema: Type[CompanyOverviewArgsSchema] = CompanyOverviewArgsSchema

    def _run(self, symbol):
        r = requests.get(
            f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={alpha_vantage_api_key}"
        )
        return r.json()


class CompanyStockPerformanceTool(BaseTool):
    name = "CompanyStockPerformance"
    description = """
    Use this to get the weekly performance of a company stock.
    You should enter a stock symbol.
    """
    args_schema: Type[CompanyOverviewArgsSchema] = CompanyOverviewArgsSchema

    def _run(self, symbol):
        r = requests.get(
            f"https://www.alphavantage.co/query?function=TIME_SERIES_WEEKLY&symbol={symbol}&apikey={alpha_vantage_api_key}"
        )
        respnse = r.json()
        return list(respnse["Weekly Time Series"].items())[:200]


agent = initialize_agent(
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    handle_parsing_errors=True,
    verbose=True,
    tools=[
        StockMarketSymbolSearchTool(),
        CompanyOverviewTool(),
        CompanyIncomeStatementTool(),
        CompanyStockPerformanceTool(),
    ],
    agent_kwargs={
        "system_message": SystemMessage(
            content="""
        You are a hedge fund manager.
                                        
        You evaluate a company and provide your opinion and reasons why the stock is a buy or not.

        Consider the performance of a stock, the company overview and the income statement.

        Be assertive in your judgement and recommend the stock or advise the user against it.
                                        
        Answer in Korean
"""
        )
    },
)

company = st.text_input("관심있는 회사명을 입력하세요.")

if company:
    result = agent.invoke(company)

    st.write(result["output"])
