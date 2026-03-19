# AI Lawyer 專案開發注意事項

## 環境設定
- **Python 環境**：使用 Conda `toby` 環境
  - 路徑：`/home/toymsi/miniconda3/envs/toby/bin/python`
  - 啟用方式：`conda activate toby`
- **環境變數**：複製 `.env.example` 為 `.env` 並確實填入你的 `GOOGLE_API_KEY`。此專案主要透過 LangChain 呼叫 Gemini，因此吃的是 `GOOGLE_API_KEY` 環境變數。
- **專案依賴安裝**：
  建議直接安裝主專案與 MCP 的所有相關 dependencies：
  ```bash
  pip install -r requirements.txt
  pip install -r legel-mcp/requirements.txt
  ```

## 執行與測試方式

### 1. 執行基礎測試介面（純文字 Context 限制對答）
```bash
streamlit run app.py
```
- 開啟 `http://localhost:8501` 在網頁上貼上自訂法規段落與問題進行安全沙盒測試。

### 2. 執行 MCP 本地串接自動檢索程式
```bash
python run_mcp.py
```
- 該程式將透過 `stdio` 喚起 `legel-mcp/mcp_server_final.py`，並利用 Gemini 生成具有 Tool Calling 能力的 LangGraph React Agent。
- 可在終端機觀察 Agent 如何自動搜尋關鍵字法規（例如觸發 `search_by_keyword`）並最終綜合真實條文給出結果。

## 注意事項
- **MCP Server Repository**：本專案依賴本地資料夾下的 `legel-mcp/`。若您從新的機器部署，請確保該 Repo 也同時被完整克隆。
- **套件更新**：專案深度依賴了 `langchain-mcp-adapters` 與 `langgraph`，若遇到工具無法綁定的錯誤，請優先嘗試升級 langchain 生態系的套件版本。
