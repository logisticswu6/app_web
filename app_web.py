import streamlit as st
import requests
import json
import time

st.set_page_config(page_title="Discord 發文助手 (歷史訊息覆蓋修正版)", page_icon="🚀", layout="centered")

# ==================== 🛠️ 雲端資料庫設定區 ====================
JSONBIN_API_KEY = "$2a$10$Ra1BhjITYBEhe1ggEvr3o.wMqppUZSYG.IffOOpli7EWDah1OnumC"  # 填入你的 Master Key
JSONBIN_BIN_ID = "6a11c2ce6610dd3ae892a792"       # 填入你的 Bin ID
# ==========================================================

st.markdown("<style>div.stButton > button:first-child { width: 100%; height: 50px; font-size: 18px !important; font-weight: bold; }</style>", unsafe_allow_html=True)

def load_cloud_config():
    headers = {"X-Master-Key": JSONBIN_API_KEY}
    try:
        res = requests.get(f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}/latest", headers=headers)
        if res.status_code == 200:
            data = res.json().get("record", {})
            # 資料相容性檢查結構
            raw_groups = data.get("groups", {})
            cleaned_groups = {}
            for k, v in raw_groups.items():
                if isinstance(v, dict):
                    cleaned_groups[k] = v
                else:
                    cleaned_groups[k] = {"group_num": str(v), "message_id": ""}
            data["groups"] = cleaned_groups
            return data
    except:
        pass
    return {"tokens": {}, "groups": {}, "user_id": ""}

def save_cloud_config(data):
    headers = {"X-Master-Key": JSONBIN_API_KEY, "Content-Type": "application/json"}
    try:
        requests.put(f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}", json=data, headers=headers)
    except:
        st.error("雲端資料庫寫入失敗！")

if "XXX" in JSONBIN_API_KEY or "XXX" in JSONBIN_BIN_ID:
    st.error("❌ 請先填寫程式碼最上方的 JSONBin 設定欄位！")
    st.stop()

if 'cloud_config' not in st.session_state:
    st.session_state.cloud_config = load_cloud_config()

config = st.session_state.cloud_config

st.title("🚀 Discord 發文助手 (覆蓋修正版)")

if st.button("🔄 同步/刷新雲端最新資料"):
    st.session_state.cloud_config = load_cloud_config()
    st.rerun()

# 1. 操作人員
st.subheader("1. 操作人員 (Token)")
with st.expander("💡 如何獲取 Discord User Token？"):
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
                st.rerun()
else:
    current_token = config["tokens"].get(selected_user, "")
    if selected_user and st.button("🗑️ 刪除此人員", key="del_u"):
        del config["tokens"][selected_user]
        save_cloud_config(config)
        st.rerun()

# 2. 合作群組編號
st.subheader("2. 合作群組編號")
group_options = list(config["groups"].keys()) + ["➕ 新增群組編號..."]
selected_group = st.selectbox("選擇合作群組編號：", options=group_options)

g_data = {}
if selected_group == "➕ 新增群組編號...":
    with st.form("add_group", clear_on_submit=True):
        num = st.text_input("群組編號數字：")
        g_name = st.text_input("對象名稱 (選填)：")
        if st.form_submit_button("💾 儲存群組編號"):
            if num.strip():
                display_name = g_name.strip() if g_name.strip() else num.strip()
                config["groups"][display_name] = {"group_num": num.strip(), "message_id": ""}
                save_cloud_config(config)
                st.success("已同步至雲端選單！")
                st.rerun()
else:
    g_data = config["groups"].get(selected_group, {})
    if selected_group and st.button("🗑️ 刪除此編號", key="del_g"):
        del config["groups"][selected_group]
        save_cloud_config(config)
        st.rerun()

# 3. 內文填寫
st.subheader("3. 發文內容填寫")
user_id = st.text_input("代表使用者 ID：", value=config.get("user_id", ""))
content = st.text_area("文宣內容：", height=150)

if st.button("🚀 提交發送 / 覆蓋修正"):
    if current_token and g_data and user_id.strip() and content.strip():
        config["user_id"] = user_id.strip()
        
        num = g_data.get("group_num")
        msg_id = g_data.get("message_id", "")
        
        channel_id = "1278344397808996454"
        base_url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
        headers = {"Authorization": current_token, "Content-Type": "application/json"}
        final_text = f"太屌了 這是本群第{num}個合作群組\n<@&1277926068891684946>\n代表: <@{user_id.strip()}>\n{content.strip()}"
        
        # 💥 網頁版核心歷史判定：有舊 ID 直接執行 PATCH 修正
        if msg_id:
            try:
                edit_res = requests.patch(f"{base_url}/{msg_id}", json={"content": final_text}, headers=headers)
                if edit_res.status_code == 200:
                    save_cloud_config(config)
                    st.success("🎯 偵測到群組歷史！已成功為您遠端更正原訊息內容，未發送新訊息。")
                elif edit_res.status_code == 404:
                    msg_id = "" # 原貼文不見了，直接往下遞補重發
                else:
                    st.error(f"覆蓋修正失敗: {edit_res.text}")
            except Exception as e:
                st.error(f"連線異常: {e}")
                
        # 執行首次新貼文發送
        if not msg_id:
            try:
                res = requests.post(base_url, json={"content": "<@&1277926068891684946>"}, headers=headers)
                if res.status_code == 200:
                    new_id = res.json().get("id")
                    time.sleep(0.3)
                    requests.patch(f"{base_url}/{new_id}", json={"content": final_text}, headers=headers)
                    
                    config["groups"][selected_group]["message_id"] = new_id
                    save_cloud_config(config)
                    st.success("🆕 新編號首次發布成功！已自動鎖定訊息 ID 至雲端。")
                    st.rerun()
                else:
                    st.error(f"發送失敗: {res.text}")
            except Exception as e:
                st.error(str(e))
