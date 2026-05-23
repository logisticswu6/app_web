import streamlit as st
import requests
import json
import time

# 設定網頁標題
st.set_page_config(page_title="Discord 發文助手 (雲端同步網頁版)", page_icon="🚀", layout="centered")

# ==================== 🛠️ 雲端資料庫設定區 ====================
# 請在下方雙引號內填入你在 JSONBin.io 取得的金鑰與資料庫 ID
JSONBIN_API_KEY = "$2a$10$Ra1BhjITYBEhe1ggEvr3o.wMqppUZSYG.IffOOpli7EWDah1OnumC"  # 填入你的 Master Key
JSONBIN_BIN_ID = "6a11c2ce6610dd3ae892a792"       # 填入你的 Bin ID
# ==========================================================

# 自訂按鈕樣式
st.markdown("<style>div.stButton > button:first-child { width: 100%; height: 50px; font-size: 18px !important; font-weight: bold; }</style>", unsafe_allow_html=True)

# --- JSONBin 雲端讀寫邏輯 ---
def load_cloud_config():
    headers = {"X-Master-Key": JSONBIN_API_KEY}
    try:
        res = requests.get(f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}/latest", headers=headers)
        if res.status_code == 200:
            return res.json().get("record", {})
    except:
        pass
    return {"tokens": {}, "groups": {}, "user_id": ""}

def save_cloud_config(data):
    headers = {"X-Master-Key": JSONBIN_API_KEY, "Content-Type": "application/json"}
    try:
        requests.put(f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}", json=data, headers=headers)
    except:
        st.error("雲端資料庫寫入失敗，請檢查網路！")

# 檢查設定
if "XXX" in JSONBIN_API_KEY or "XXX" in JSONBIN_BIN_ID:
    st.error("❌ 請先在程式碼最上方填入有效的 JSONBIN_API_KEY 和 JSONBIN_BIN_ID！")
    st.stop()

# 讀取雲端資料
if 'cloud_config' not in st.session_state:
    st.session_state.cloud_config = load_cloud_config()

config = st.session_state.cloud_config

# --- Discord 雙發送邏輯 ---
def post_to_discord(token, group_num, user_id, content):
    channel_id = "1278344397808996454"
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    headers = {"Authorization": token, "Content-Type": "application/json"}
    final_text = f"太屌了 這是本群第{group_num}個合作群組\n<@&1277926068891684946>\n代表: <@{user_id}>\n{content}"
    try:
        res = requests.post(url, json={"content": "<@&1277926068891684946>"}, headers=headers)
        if res.status_code == 200:
            msg_id = res.json().get("id")
            time.sleep(0.3)
            requests.patch(f"{url}/{msg_id}", json={"content": final_text}, headers=headers)
            return True, "發送成功，且已強制觸發通知！"
        return False, f"發送失敗，錯誤代碼: {res.status_code}"
    except Exception as e:
        return False, str(e)

# --- UI 介面 ---
st.title("🚀 Discord 發文助手 (雲端同步版)")

# 手動同步刷新按鈕
if st.button("🔄 同步/刷新雲端最新資料"):
    st.session_state.cloud_config = load_cloud_config()
    st.rerun()

# 1. 操作人員
st.subheader("1. 操作人員 (Token)")
with st.expander("💡 如何獲取 Discord User Token？"):
    st.markdown("1. 電腦網頁版 Discord 按 F12 -> Console。\n2. 複製下方代碼貼上按 Enter：")
    js_code = '(webpackChunkdiscord_app ? window.webpackChunkdiscord_app.push([ [Math.random()], {}, (e) => { for (const n of Object.keys(e.c).map((n) => e.c[n].exports)) if (n && n.default && void 0 !== n.default.getToken) console.log("%c你的 Token 在這裡：\\n\\n%c" + n.default.getToken(), "color: green; font-size: 16px; font-weight: bold;", "color: red; font-size: 14px; font-weight: bold; background: #fee; padding: 5px; border: 1px solid red;"); } ]) : console.error("請在 Discord 網頁版執行此指令"));'
    st.code(js_code, language="javascript")

token_options = list(config["tokens"].keys()) + ["➕ 新增人員/Token..."]
selected_user = st.selectbox("選擇發文身分：", options=token_options)

current_token = ""
if selected_user == "➕ 新增人員/Token...":
    with st.form("add_user", clear_on_submit=True):
        name = st.text_input("人員名稱：")
        tk_val = st.text_input("Token：", type="password")
        if st.form_submit_button("💾 儲存人員資料"):
            if name.strip() and tk_val.strip():
                config["tokens"][name.strip()] = tk_val.strip()
                save_cloud_config(config)
                st.success("已同步至雲端選單！")
                st.session_state.cloud_config = config
                st.rerun()
else:
    current_token = config["tokens"].get(selected_user, "")
    if selected_user and st.button("🗑️ 刪除此人員", key="del_u"):
        del config["tokens"][selected_user]
        save_cloud_config(config)
        st.session_state.cloud_config = config
        st.rerun()

# 2. 合作群組編號
st.subheader("2. 合作群組編號")
group_options = list(config["groups"].keys()) + ["➕ 新增群組編號..."]
selected_group = st.selectbox("選擇合作群組編號：", options=group_options)

real_group_num = ""
if selected_group == "➕ 新增群組編號...":
    with st.form("add_group", clear_on_submit=True):
        num = st.text_input("群組編號數字：")
        g_name = st.text_input("對象名稱 (選填)：")
        if st.form_submit_button("💾 儲存群組編號"):
            if num.strip():
                display_name = g_name.strip() if g_name.strip() else num.strip()
                config["groups"][display_name] = num.strip()
                save_cloud_config(config)
                st.success("已同步至雲端選單！")
                st.session_state.cloud_config = config
                st.rerun()
else:
    real_group_num = config["groups"].get(selected_group, "")
    if selected_group and st.button("🗑️ 刪除此編號", key="del_g"):
        del config["groups"][selected_group]
        save_cloud_config(config)
        st.session_state.cloud_config = config
        st.rerun()

# 3. 內文填寫
st.subheader("3. 發文內容填寫")
user_id = st.text_input("代表使用者 ID：", value=config.get("user_id", ""))
content = st.text_area("文宣內容：", height=150)

if st.button("🚀 立即發送 (強制通知)"):
    if current_token and real_group_num and user_id.strip() and content.strip():
        config["user_id"] = user_id.strip()
        save_cloud_config(config)
        success, msg = post_to_discord(current_token, real_group_num, user_id.strip(), content.strip())
        if success: st.success(msg)
        else: st.error(msg)
