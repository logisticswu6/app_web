import streamlit as st
import requests
import json
import time

# 設定網頁標題與外觀
st.set_page_config(page_title="Discord 雲端發文助手", page_icon="🚀", layout="centered")

# CSS 優化
st.markdown("""<style>div.stButton > button { width: 100%; height: 50px; font-size: 18px !important; font-weight: bold; }</style>""", unsafe_allow_html=True)

# ----------------- 雲端資料同步邏輯 (取代本地檔案) -----------------
def load_config():
    try:
        url = f"https://api.jsonbin.io/v3/b/{st.secrets['JSONBIN_BIN_ID']}/latest"
        headers = {"X-Master-Key": st.secrets['JSONBIN_API_KEY']}
        return requests.get(url, headers=headers).json().get("record", {"tokens": {}, "groups": {}, "user_id": ""})
    except:
        return {"tokens": {}, "groups": {}, "user_id": ""}

def save_config(config_data):
    try:
        url = f"https://api.jsonbin.io/v3/b/{st.secrets['JSONBIN_BIN_ID']}"
        headers = {
            "X-Master-Key": st.secrets['JSONBIN_API_KEY'],
            "Content-Type": "application/json"
        }
        requests.put(url, json=config_data, headers=headers)
    except Exception as e:
        st.error(f"雲端儲存失敗: {e}")

# 初始化資料
if 'config' not in st.session_state:
    st.session_state.config = load_config()
config = st.session_state.config

# ----------------- 核心發送邏輯 -----------------
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
            return True, "發送成功！"
        return False, f"失敗: {res.status_code}"
    except Exception as e:
        return False, f"異常: {e}"

# ----------------- UI 介面 (功能全保留) -----------------
st.title("🚀 Discord 雲端發文助手")

# 1. 人員管理
st.subheader("1. 操作人員 (Token)")
token_options = list(config["tokens"].keys()) + ["➕ 新增人員/Token..."]
selected_user = st.selectbox("選擇身分：", options=token_options)

if selected_user == "➕ 新增人員/Token...":
    with st.form("add_user", clear_on_submit=True):
        n = st.text_input("人員名稱：")
        t = st.text_input("Token：", type="password")
        if st.form_submit_button("💾 儲存"):
            config["tokens"][n] = t
            save_config(config); st.rerun()
else:
    if st.button("🗑️ 刪除此人員"):
        del config["tokens"][selected_user]
        save_config(config); st.rerun()

# 2. 群組管理
st.subheader("2. 合作群組")
group_options = list(config["groups"].keys()) + ["➕ 新增群組..."]
selected_group = st.selectbox("選擇群組：", options=group_options)

if selected_group == "➕ 新增群組...":
    with st.form("add_group", clear_on_submit=True):
        num = st.text_input("群組編號：")
        name = st.text_input("群組名稱：")
        if st.form_submit_button("💾 儲存"):
            config["groups"][name if name else num] = num
            save_config(config); st.rerun()
else:
    if st.button("🗑️ 刪除此群組"):
        del config["groups"][selected_group]
        save_config(config); st.rerun()

# 3. 發送
user_id = st.text_input("代表 ID：", value=config.get("user_id", ""))
content = st.text_area("文宣：")

if st.button("🚀 立即發送"):
    config["user_id"] = user_id
    save_config(config)
    success, msg = post_to_discord(config["tokens"][selected_user], config["groups"][selected_group], user_id, content)
    if success: st.success(msg)
    else: st.error(msg)
