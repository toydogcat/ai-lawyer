
# 步驟 2：導入 MCP 成為 AI 的法規檢索工具 (Phase 2)

決定用 MCP（https://lobehub.com/zh-TW/mcp/wasonisgood-legel-mcp），下一步就變成：「讓 Python 腳本能跟這個本地端的 MCP Server 溝通，並讓 Gemini 知道它有這個工具可以使用 (Function Calling / Tool Calling)。」

## 準備動作：啟動 MCP Server
先在開發環境把那個開源的 MCP 跑起來。通常這種專案都會提供 Dockerfile 或簡單的 Node.js/Python 啟動指令。請確保它在你本地的某個 Port（例如 stdio 或 SSE 模式）順利運行。

## 法律 MCP 
https://lobehub.com/zh-TW/mcp/wasonisgood-legel-mcp

## 生成 MCP Client 程式碼
「我現在本地端運行了一個針對台灣法規的 MCP (Model Context Protocol) Server。
請幫我寫一段 Python 程式碼，結合 langchain-google-genai (使用 gemini-3.1-flash-lite-preview) 與 MCP Client SDK。

需求如下：

1. 建立一個 MCP Client 連線到這個本地伺服器 (請示範使用 stdio 模式啟動外部指令的方式)。

2. 取得該 MCP Server 提供的所有 Tools。

3. 設定一個 LangChain 的 Agent，綁定 Gemini 模型，並將取得的 MCP Tools 綁定給這個 Agent (Tool Calling)。

4. 寫一個測試對話：『請問台灣刑法對於公然侮辱的罰則是什麼？』，讓 Agent 自動判斷並呼叫 MCP Tool 去查法規，然後回答我。

5. 請提供完整的非同步 (async) 程式碼結構以及需要的 pip install 套件，到requirements.txt。」

## 驗證事項 (Definition of Done)
[ ] 驗證 1 (連線成功)： Python 腳本能成功讀取到 MCP Server 提供的工具列表（例如可能會印出類似 search_law, get_article 之類的方法名）。

[ ] 驗證 2 (自動呼叫工具)： 當你問一個法律問題時，你能從終端機的 Log 中看到，Gemini 並沒有直接靠自己的內建知識亂猜，而是觸發了 Tool Calling，把搜尋關鍵字傳給了 MCP。

[ ] 驗證 3 (結合 Context 回答)： 最終輸出的答案，是 Gemini 拿到 MCP 回傳的真實條文後，整理出來的正確回覆。
