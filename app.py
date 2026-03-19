import asyncio
import os
import sys
import warnings
import base64
import ast
import json
import streamlit as st
from io import BytesIO
from dotenv import load_dotenv

warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*create_react_agent.*")

try:
    from pypdf import PdfReader
except ImportError:
    st.error("請先安裝 pypdf 套件： pip install pypdf")

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

load_dotenv()

st.set_page_config(page_title="AI Lawyer", page_icon="⚖️", layout="wide")
st.title("⚖️ AI Lawyer (Part 4: Multimodal & Actionable UI)")
st.markdown("結合本地 MCP 法規資料庫、支援多模態文件解讀，並提供律師實務輸出的 AI 專家。")

# 初始化對話紀錄
if "messages" not in st.session_state:
    st.session_state.messages = []

# ==========================================
# 核心邏輯 - 所有函式定義
# ==========================================

def parse_uploaded_files(files):
    text_context = ""
    image_contents = []
    
    for file in files:
        if file.type == "application/pdf":
            reader = PdfReader(file)
            pdf_text = "".join(page.extract_text() + "\n" for page in reader.pages)
            text_context += f"\n\n[附件 PDF: {file.name}] 內容：\n{pdf_text}\n"
        elif file.type in ["image/png", "image/jpeg", "image/jpg"]:
            encoded_image = base64.b64encode(file.read()).decode("utf-8")
            image_contents.append({
                "type": "image_url",
                "image_url": f"data:{file.type};base64,{encoded_image}"
            })
    return text_context, image_contents

def clean_ai_output(raw_content):
    """處理並清理 AI 回傳的結構化內容，提取出純文字"""
    if isinstance(raw_content, list):
        texts = [item['text'] for item in raw_content if isinstance(item, dict) and 'text' in item]
        return "\n".join(texts)
    elif isinstance(raw_content, str):
        try:
            parsed = ast.literal_eval(raw_content)
            if isinstance(parsed, list):
                texts = [item['text'] for item in parsed if isinstance(item, dict) and 'text' in item]
                return "\n\n".join(texts).replace('\\n', '\n')
        except (ValueError, SyntaxError):
            pass 
        return raw_content.replace('\\n', '\n')
    return str(raw_content)

def generate_legal_document(doc_type):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return "錯誤：請確認 API Key 設定。"
    
    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview") 
    history_text = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in st.session_state.messages])
    
    if doc_type == "summary":
        prompt = f"""
        你是專業的台灣律師。請根據以下我們與客戶的對話紀錄，整理出一份「法律諮詢總結」。
        請包含以下結構：
        1. 案件客觀事實與時間軸 (Fact & Timeline)
        2. 雙方爭點 (Issue)
        3. 涉及法規 (Rule - 請列出我們討論到的 MCP 法規條文)
        4. 後續行動建議 (Actionable Advice)
        
        【對話紀錄】：
        {history_text}
        """
    else:
        prompt = f"""
        你是專業的台灣律師。請根據以下對話紀錄，為客戶草擬一份符合台灣法院實務格式的「起訴狀」或「告訴狀」草稿。
        要求：
        1. 自動判斷應該寫民事還是刑事。
        2. 當事人資訊（姓名、身分證、地址）請用 [ＯＯＯ] 保留空格。
        3. 必須引述對話中討論到的法規條文作為請求權基礎。
        
        【對話紀錄】：
        {history_text}
        """
    response = llm.invoke(prompt)
    return clean_ai_output(response.content)

def generate_chat_pdf(messages):
    try:
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import SimpleDocTemplate, Paragraph, PageBreak, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.pagesizes import A4
    except ImportError:
        st.error("請先安裝 reportlab 套件： pip install reportlab")
        return None

    font_path = "jf-openhuninn-2.0.ttf"
    if not os.path.exists(font_path):
        import urllib.request
        url = "https://raw.githubusercontent.com/justfont/open-huninn-font/master/font/jf-openhuninn-2.0.ttf"
        try:
            urllib.request.urlretrieve(url, font_path)
        except Exception as e:
            st.error(f"下載中文字型失敗：{e}")
            return None

    try:
        pdfmetrics.registerFont(TTFont('Huninn', font_path))
    except Exception as e:
        st.error(f"字型載入失敗：{e}")
        return None

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    
    user_style = ParagraphStyle(
        'UserStyle', 
        parent=styles['Normal'], 
        fontName='Huninn', 
        fontSize=11, 
        textColor='#000000',
        leading=18,
        spaceAfter=20
    )
    user_label_style = ParagraphStyle(
        'UserLabel', 
        parent=styles['Heading3'], 
        fontName='Huninn', 
        fontSize=13, 
        textColor='#003366',
        spaceAfter=8
    )
    ai_style = ParagraphStyle(
        'AIStyle', 
        parent=styles['Normal'], 
        fontName='Huninn', 
        fontSize=11, 
        textColor='#000000',
        leading=18,
        spaceAfter=20
    )
    ai_label_style = ParagraphStyle(
        'AILabel', 
        parent=styles['Heading3'], 
        fontName='Huninn', 
        fontSize=13, 
        textColor='#800000',
        spaceAfter=8
    )

    story = []
    
    i = 0
    while i < len(messages):
        msg = messages[i]
        if msg["role"] == "user":
            user_msg = str(msg["content"]).replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
            ast_msg = ""
            i += 1
            if i < len(messages) and messages[i]["role"] == "assistant":
                ast_msg = str(messages[i]["content"]).replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
                i += 1
            
            story.append(Paragraph("User:", user_label_style))
            story.append(Paragraph(user_msg, user_style))
            
            if ast_msg:
                story.append(Paragraph("AI Lawyer:", ai_label_style))
                story.append(Paragraph(ast_msg, ai_style))
            
            # 使用者要求的每一輪獨立一頁
            story.append(PageBreak())
        else:
            i += 1

    try:
        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    except Exception as e:
        st.error(f"產生 PDF 時發生錯誤：{e}")
        return None

async def process_chat(user_input, attached_files):
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        st.error("錯誤：請在 .env 檔案中設定 GOOGLE_API_KEY")
        return None

    llm = ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite-preview")
    
    server_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "legel-mcp", "mcp_server_final.py"))
    server_params = StdioServerParameters(command=sys.executable, args=[server_script], env=os.environ.copy())

    chat_history = [SystemMessage(content="你是專業的台灣法律助理。請盡量使用工具檢索到的法規內容回答問題。")]
    
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            chat_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            chat_history.append(AIMessage(content=msg["content"]))
            
    parsed_text, parsed_images = parse_uploaded_files(attached_files)
    final_input_text = user_input + parsed_text
    
    message_content = [{"type": "text", "text": final_input_text}]
    message_content.extend(parsed_images)
    chat_history.append(HumanMessage(content=message_content))

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await load_mcp_tools(session)
            
            agent_executor = create_react_agent(llm, tools)
            status_container = st.status("Agent 思考與檢索中...", expanded=True)
            
            try:
                final_answer = ""
                async for step in agent_executor.astream({"messages": chat_history}, stream_mode="values"):
                    message = step["messages"][-1]
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tc in message.tool_calls:
                            status_container.write(f"👉 呼叫法規庫: `{tc['name']}`\n參數: `{tc['args']}`")
                    
                    if message.type == "ai" and not message.tool_calls:
                        if message.content:
                            final_answer = clean_ai_output(message.content)
                
                status_container.update(label="任務完成！", state="complete", expanded=False)
                return final_answer
            except Exception as e:
                status_container.update(label="發生錯誤！", state="error", expanded=True)
                st.error(str(e))
                return None

# ==========================================
# 側邊欄 (Sidebar) - UI 渲染區
# ==========================================
with st.sidebar:
    st.header("📂 案件資料上傳")
    uploaded_files = st.file_uploader(
        "上傳相關文件 (支援 PDF, PNG, JPG)", 
        accept_multiple_files=True, 
        type=['pdf', 'png', 'jpg', 'jpeg']
    )
    
    st.divider()
    st.header("🛠️ 律師實務工具")
    st.markdown("*(產生結果將直接顯示於右側對話中)*")
    
    col1, col2 = st.columns(2)
    with col1:
        btn_summary = st.button("📝 產生諮詢總結", use_container_width=True)
        if "summary_text" in st.session_state:
            st.download_button(
                label="📥 下載總結 (MD)",
                data=st.session_state.summary_text,
                file_name="法律諮詢總結.md",
                mime="text/markdown",
                use_container_width=True
            )
    with col2:
        btn_draft = st.button("⚖️ 草擬訴狀草稿", use_container_width=True)
        if "draft_text" in st.session_state:
            st.download_button(
                label="📥 下載草稿 (MD)",
                data=st.session_state.draft_text,
                file_name="訴狀草稿.md",
                mime="text/markdown",
                use_container_width=True
            )

    st.divider()
    st.header("📄 匯出紀錄")
    # 點擊按鈕後才產生 PDF
    if st.button("⚙️ 準備 PDF 檔案", use_container_width=True):
        if not st.session_state.messages:
            st.warning("目前沒有對話紀錄可以匯出喔！")
        else:
            with st.spinner("正在產生 PDF (首次需下載中文字型)..."):
                pdf_bytes = generate_chat_pdf(st.session_state.messages)
                if pdf_bytes:
                    st.session_state.pdf_data = pdf_bytes

    if "pdf_data" in st.session_state and st.session_state.pdf_data:
        st.download_button(
            label="📥 點擊下載對話紀錄",
            data=st.session_state.pdf_data,
            file_name="AI_Lawyer_Chat_History.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.divider()
    st.header("💾 狀態存檔與讀取")
    chat_json_str = json.dumps(st.session_state.messages, ensure_ascii=False, indent=2)
    st.download_button(
        label="⬇️ 儲存對話狀態 (JSON)",
        data=chat_json_str,
        file_name="AI_Lawyer_Chat_State.json",
        mime="application/json",
        use_container_width=True
    )
    
    uploaded_json = st.file_uploader("上傳先前的對話狀態 (JSON)", type=['json'], key="json_uploader")
    if uploaded_json is not None:
        try:
            loaded_messages = json.loads(uploaded_json.getvalue())
            if st.button("🔄 載入歷史訊息", use_container_width=True):
                st.session_state.messages = loaded_messages
                st.session_state.pop("pdf_data", None)
                st.session_state.pop("summary_text", None)
                st.session_state.pop("draft_text", None)
                st.rerun()
        except Exception as e:
            st.error(f"解析 JSON 失敗：{e}")

# ==========================================
# 主畫面 - UI 渲染與事件觸發區
# ==========================================
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if btn_summary:
    if not st.session_state.messages:
        st.warning("請先進行對話，才能產生總結喔！")
    else:
        with st.chat_message("assistant"):
            with st.spinner("正在為您撰寫諮詢總結..."):
                summary_text = generate_legal_document("summary")
                st.session_state.summary_text = summary_text
                st.markdown("### 📝 法律諮詢總結\n" + summary_text)
                st.session_state.messages.append({"role": "assistant", "content": "【已自動產生法律諮詢總結】\n" + summary_text})
                # 強制重新渲染讓側邊欄顯示下載按鈕
                st.rerun()

if btn_draft:
    if not st.session_state.messages:
        st.warning("請先進行對話，才能草擬訴狀喔！")
    else:
        with st.chat_message("assistant"):
            with st.spinner("正在為您草擬訴狀..."):
                draft_text = generate_legal_document("draft")
                st.session_state.draft_text = draft_text
                st.markdown("### ⚖️ 訴狀草稿\n" + draft_text)
                st.session_state.messages.append({"role": "assistant", "content": "【已自動產生訴狀草稿】\n" + draft_text})
                st.rerun()

if prompt := st.chat_input("請輸入您的法律問題，或在左側上傳文件後發問..."):
    with st.chat_message("user"):
        st.markdown(prompt)
        if uploaded_files:
            st.caption(f"*(附帶 {len(uploaded_files)} 份文件)*")
            
    with st.chat_message("assistant"):
        answer = asyncio.run(process_chat(prompt, uploaded_files))
        if answer:
            st.markdown(answer)
            save_user_prompt = prompt
            if uploaded_files:
                save_user_prompt += f"\n[附帶了 {len(uploaded_files)} 份檔案供參考]"
                
            st.session_state.messages.append({"role": "user", "content": save_user_prompt})
            st.session_state.messages.append({"role": "assistant", "content": answer})
