import asyncio
import os
import sys
import warnings
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*create_react_agent.*")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

# 讀取 .env
load_dotenv()

async def main():
    # 1. 確保 GOOGLE_API_KEY 已設定
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("錯誤：請在 .env 檔案中設定 GOOGLE_API_KEY")
        return

    # 2. 初始化 Gemini 模型
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview")

    # 3. 設定 MCP Server 連線參數 (stdio 模式)
    server_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "legel-mcp", "mcp_server_final.py"))
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_script],
        env=os.environ.copy() # 將環境變數傳遞給 Server
    )

    print("正在啟動並連線至本機 MCP Server ...")
    
    # 4. 建立 MCP Client 連線
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化 session
            await session.initialize()
            print("MCP Server 初始化成功！")

            # 5. 取得 MCP Server 提供的所有 Tools
            tools = await load_mcp_tools(session)
            print(f"成功載入 {len(tools)} 個 tools: {[t.name for t in tools]}")

            # 6. 使用 LangGraph 建立一個具備 Tool Calling 能力的代理人 (Agent)
            # 這裡使用 prebuilt 的 create_react_agent，它會自動處理 LLM 呼叫 Tool 並且回傳的循環
            agent_executor = create_react_agent(llm, tools)

            # 7. 準備測試問題
            question = "請問台灣刑法對於公然侮辱的罰則是什麼？"
            print(f"\n[使用者測試問題]: {question}\n")
            print("Agent 思考中...\n")

            # 8. 執行問題並印出執行過程
            async for step in agent_executor.astream(
                {"messages": [("user", question)]},
                stream_mode="values",
            ):
                message = step["messages"][-1]
                
                # 印出 Agent 呼叫 Tool 的中繼紀錄 (Verification 2)
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tc in message.tool_calls:
                        print(f"👉 [Agent 觸發 Tool Call] 呼叫工具: '{tc['name']}', 參數: {tc['args']}\n")
                
                # 印出最終回答 (Verification 3)
                if message.type == "ai" and not hasattr(message, "tool_calls") or (hasattr(message, "tool_calls") and not message.tool_calls):
                    if message.content:
                        print(f"🤖 [Agent 綜合回答]:\n{message.content}\n")

if __name__ == "__main__":
    asyncio.run(main())
