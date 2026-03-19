
# 步驟 1：環境建置與基礎腳本

## 檢查 .env 檔案內容
GOOGLE_API_KEY=your_gemini_api_key_here

## 法律 MCP 
https://lobehub.com/zh-TW/mcp/wasonisgood-legel-mcp

## 建立基礎腳本
「請幫我寫一個 Python 腳本 app.py。需求如下：

使用 python-dotenv 讀取 .env 檔中的 GOOGLE_API_KEY。

使用 langchain-google-genai 套件，初始化 Gemini 模型 (建議用 "gemini-3.1-flash-lite-preview"，因為我們要測試)。

寫一個簡單的 function legal_qa(context, question)，把一段虛擬的法律條文 (context) 和一個問題 (question) 丟給模型。

System Prompt 請設定得嚴格一點，要求模型『只能』依據提供的 context 回答，如果不清楚請回答『資訊不足』。

給我完整的程式碼與需要 pip install 的套件清單寫入 requirements.txt。」

前端給我測試用streamlit
