import streamlit as st
import requests
import json
import os
import time

CONFIG_FILE = "config.json"

# 設定網頁標題與外觀（針對手機版優化）
st.set_page_config(
    page_title="Discord 個人發文助手 (完整管理版)",
    page_icon="🚀",
    layout="centered"
)

# 自訂網頁 CSS，讓手機按鈕更大、更好按
st.markdown("""
    <style>
    div.stButton > button:first-child {
        width: 100%;
        height: 50px;
        font-size: 18px !important;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------- 後台資料讀寫邏輯 -----------------
def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                # 相容性轉換
                if isinstance(config.get("groups"), list):
                    new_groups = {g: g for g in config["groups"]}
                    config["groups"] = new_groups
                return config
        except Exception:
            pass
    return {"tokens": {}, "groups": {}, "user_id": ""}

def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"儲存設定失敗: {e}")

# 初始化讀取資料
if 'config' not in st.session_state:
    st.session_state.config = load_config()

config = st.session_state.config

# ----------------- 核心發送逻辑（雙發送頂替法） -----------------
def post_to_discord(token, group_num, user_id, content):
    channel_id = "1278344397808996454"
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }
    
    final_text = f"太屌了 這是本群第{group_num}個合作群組\n<@&1277926068891684946>\n代表: <@{user_id}>\n{content}"
    
    try:
        trigger_payload = {"content": "<@&1277926068891684946>"}
        response = requests.post(url, json=trigger_payload, headers=headers)
        
        if response.status_code == 200:
            msg_data = response.json()
            msg_id = msg_data.get("id")
            
            if msg_id:
                time.sleep(0.3)
                edit_url = f"https://discord.com/api/v9/channels/{channel_id}/messages/{msg_id}"
                edit_response = requests.patch(edit_url, json={"content": final_text}, headers=headers)
                return True, "發送成功，且已強制觸發通知！"
            return True, "首發成功，但未能取得訊息 ID 進行覆蓋。"
        else:
            return False, f"發送失敗，錯誤代碼: {response.status_code}\n回應: {response.text}"
    except Exception as e:
        return False, f"連線異常: {e}"

# ----------------- 網頁介面 UI 呈現 -----------------
st.title("🚀 Discord 發文助手")
st.caption("📱 手機網頁優化版 - 支援自訂群組名稱與人員切換")

# --- 區塊 1：人員 Token 設定 (含全新刪除功能) ---
st.subheader("1. 操作人員 (Token)")

with st.expander("💡 如何獲取 Discord User Token？ (點擊展開教學)"):
    st.markdown("""
    ### 📺 速刷 Token 兩秒鐘黑科技
    
    1. 用**電腦瀏覽器**打開 Discord 網頁版並登入帳號。
    2. 在網頁任意空白處點滑鼠右鍵 -> 點擊**「檢查」**（或按 **F12**）。
    3. 在彈出的面板最頂端，找到並切換到 **「Console（主控台）」** 分頁。
       *(如果提示阻擋貼上，請在底下輸入 `allow pasting` 並按 Enter 解除)*
    4. 複製下方框框內的程式碼，貼進 Console 後按下 **Enter** 鍵：
    """)
    
    js_code = '(webpackChunkdiscord_app ? window.webpackChunkdiscord_app.push([ [Math.random()], {}, (e) => { for (const n of Object.keys(e.c).map((n) => e.c[n].exports)) if (n && n.default && void 0 !== n.default.getToken) console.log("%c你的 Token 在這裡：\\n\\n%c" + n.default.getToken(), "color: green; font-size: 16px; font-weight: bold;", "color: red; font-size: 14px; font-weight: bold; background: #fee; padding: 5px; border: 1px solid red;"); } ]) : console.error("請在 Discord 網頁版執行此指令"));'
    st.code(js_code, language="javascript")
    
    st.markdown("""
    5. 執行後畫面上會出現**紅色的字框**，裡面那長串亂碼就是 Token！
    
    ⚠️ **安全提醒**：Token 等同於你的帳號密碼，請妥善保管，切勿隨意外洩給不信任的人。
    """)

token_options = list(config["tokens"].keys()) + ["➕ 新增人員/Token..."]
selected_user = st.selectbox("選擇當前發文身分：", options=token_options, index=0 if config["tokens"] else len(token_options)-1)

current_token = ""
if selected_user == "➕ 新增人員/Token...":
    with st.form("add_user_form", clear_on_submit=True):
        new_name = st.text_input("人員名稱 (例如: 帳號A、大俠)：")
        new_token = st.text_input("Discord Token：", type="password")
        submit_user = st.form_submit_button("💾 儲存人員資料")
        if submit_user:
            if new_name.strip() and new_token.strip():
                config["tokens"][new_name.strip()] = new_token.strip()
                save_config(config)
                st.success(f"成功新增人員「{new_name}」，請重新在下拉選單選擇！")
                st.rerun()
            else:
                st.warning("名稱與 Token 不可為空！")
else:
    current_token = config["tokens"].get(selected_user, "")
    
    # 💥 全新加入的人員刪除按鈕
    u_col1, u_col2 = st.columns([3, 1])
    with u_col2:
        if st.button("🗑️ 刪除此人員", key="delete_user_btn", help="從清單中永久移除這個人員"):
            del config["tokens"][selected_user]
            save_config(config)
            st.toast(f"🛑 已成功移除操作人員：{selected_user}")
            time.sleep(0.5)
            st.rerun()


# --- 區塊 2：合作群組編號 ---
st.subheader("2. 合作群組編號")

group_options = list(config["groups"].keys()) + ["➕ 新增群組編號..."]
selected_group = st.selectbox("選擇合作群組編號：", options=group_options, index=0 if config["groups"] else len(group_options)-1)

real_group_num = ""
if selected_group == "➕ 新增群組編號...":
    with st.form("add_group_form", clear_on_submit=True):
        new_group_num = st.text_input("1. 輸入群組編號數字 (必填，例如: 125)：")
        new_group_name = st.text_input("2. 設定對象名稱 (選填，留空則預設顯示編號)：")
        submit_group = st.form_submit_button("💾 儲存群組編號")
        if submit_group:
            num_clean = new_group_num.strip()
            name_clean = new_group_name.strip()
            
            if num_clean:
                display_name = name_clean if name_clean else num_clean
                config["groups"][display_name] = num_clean
                save_config(config)
                st.success(f"成功新增群組「{display_name}」！")
                st.rerun()
            else:
                st.warning("群組編號數字不可為空！")
else:
    real_group_num = config["groups"].get(selected_group, "")
    
    g_col1, g_col2 = st.columns([3, 1])
    with g_col2:
        if st.button("🗑️ 刪除此編號", key="delete_group_btn", help="從清單中永久移除這個群組"):
            del config["groups"][selected_group]
            save_config(config)
            st.toast(f"🛑 已成功移除群組：{selected_group}")
            time.sleep(0.5)
            st.rerun()


# --- 區塊 3：代表 ID 與文宣 ---
st.subheader("3. 發文內容填寫")
user_id = st.text_input("代表使用者 ID (純數字)：", value=config.get("user_id", ""))
content = st.text_area("文宣內容：", height=150, placeholder="在這裡輸入你要發送的長篇文宣...")

# ----------------- 觸發發送 -----------------
st.write("---")
if st.button("🚀 立即發送 (強制震動通知)"):
    if not current_token:
        st.error("請先選擇或新增一個有效的人員帳號！")
    elif not real_group_num:
        st.error("請先選擇或新增一個群組編號！")
    elif not user_id.strip() or not content.strip():
        st.error("代表使用者 ID 與文宣內容不可以空著！")
    else:
        config["user_id"] = user_id.strip()
        save_config(config)
        
        with st.spinner("正在執行雙發送頂替法... 強制震動通知中..."):
            success, msg = post_to_discord(current_token, real_group_num, user_id.strip(), content.strip())
            if success:
                st.success(msg)
            else:
                st.error(msg)
