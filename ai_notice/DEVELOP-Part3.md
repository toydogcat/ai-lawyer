
# 步驟 3：打造 Agentic 視覺化對話介面 (Phase 3)

目前我們有兩個獨立的模組：
1. app.py：具備 Streamlit 視覺化介面，但只能做純文字 Context 的限制對答。
2. run_mcp.py：擁有強大的自動檢索能力與工具呼叫 (Tool Calling)，但只能在終端機運作。

## 階段 3 的核心目標： 
將兩者結合！我們要升級 app.py，把 LangGraph React Agent 塞進 Streamlit 中，打造一個類似 ChatGPT 的網頁對話框。
這不僅能讓你在後續測試時更直覺，我們還可以利用 Streamlit 的功能，把 Agent 「思考中...」、「正在呼叫哪個工具...」的過程，即時顯示在網頁畫面上。

## 生成整合版 UI
「我需要重構一個 Streamlit 應用程式 app.py。
目前我有一支 run_mcp.py，裡面使用 langchain-mcp-adapters 與 langgraph 成功串接了本地端的 MCP Server，並建立了 React Agent。

請幫我寫一份新的 app.py，需求如下：
1. 保留原本 run_mcp.py 中初始化 MCP Client、綁定 Tools 與建立 Agent 的邏輯。
2. 使用 Streamlit 的 st.chat_message 和 st.chat_input 建立一個對話介面。
3. 使用 st.session_state 來儲存對話歷史紀錄，讓 Agent 能擁有上下文記憶。
4. 當使用者輸入問題時，呼叫 Agent 處理。請特別設計一段邏輯：如果 Agent 在思考過程中觸發了 Tool Call（例如 search_law），請使用 st.status 或 st.expander 在畫面上顯示『Agent 正在查詢法規...』的過渡動畫或提示。
5. 請提供完整的 Python 程式碼，並確保相容於非同步 (async) 執行環境。」

## 驗證事項 (Definition of Done)
[ ] 驗證 1 (UI 呈現)： 執行 streamlit run app.py 後，能看到一個乾淨的對話視窗，而不是之前的「輸入 Context」與「輸入 Question」兩個大框框。
[ ] 驗證 2 (狀態可視化)： 丟入「刑法公然侮辱的罰則」時，網頁畫面上能看到 Agent 正在使用工具的提示（例如展開的 status bar），接著才吐出最終答案。
[ ] 驗證 3 (記憶測試)： 緊接著問它：「那如果改成用暴力手段呢？」，它必須能結合上一句的上下文，自動推斷出你問的是「強暴公然侮辱罪」，並給出正確解答（刑法第 309 條第 2 項）。傳的真實條文後，整理出來的正確回覆。
