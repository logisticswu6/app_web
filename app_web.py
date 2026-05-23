import streamlit as st
import requests, json

# 透過 Streamlit Secrets 讀取加密參數
s = json.loads(st.secrets["CONFIG_DATA"])

st.set_page_config(page_title="Discord 雲端助手", page_icon="🚀")
st.markdown('<meta http-equiv="refresh" content="20">', unsafe_allow_html=True)

# 讀取雲端資料
def load_data():
    res = requests.get(f"https://api.jsonbin.io/v3/b/{s['JSONBIN_BIN_ID']}/latest", headers={"X-Master-Key": s['JSONBIN_API_KEY']})
    return res.json().get("record", {})

config = load_data()

st.title("🚀 Discord 雲端同步助手")

# UI 按鈕與輸入
u = st.selectbox("選擇人員", list(config["tokens"].keys()))
if st.button("🗑️ 刪除此人員"):
    del config["tokens"][u]
    requests.put(f"https://api.jsonbin.io/v3/b/{s['JSONBIN_BIN_ID']}", json=config, headers={"X-Master-Key": s['JSONBIN_API_KEY'], "Content-Type": "application/json"})
    st.rerun()

g = st.selectbox("選擇群組", list(config["groups"].keys()))
if st.button("🗑️ 刪除此群組"):
    del config["groups"][g]
    requests.put(f"https://api.jsonbin.io/v3/b/{s['JSONBIN_BIN_ID']}", json=config, headers={"X-Master-Key": s['JSONBIN_API_KEY'], "Content-Type": "application/json"})
    st.rerun()

uid = st.text_input("User ID", value=config.get("user_id", ""))
txt = st.text_area("文宣內容")

# 功能按鈕
col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 手動刷新"): st.rerun()
with col2:
    if st.button("🚀 提交 / 修正"):
        g_d = config["groups"][g]
        text = f"太屌了 這是本群第{g_d['group_num']}個合作群組\n<@&1277926068891684946>\n代表: <@{uid}>\n{txt}"
        h = {"Authorization": config["tokens"][u], "Content-Type": "application/json"}
        
        if g_d.get("message_id"):
            requests.patch(f"https://discord.com/api/v9/channels/1278344397808996454/messages/{g_d['message_id']}", json={"content": text}, headers=h)
        else:
            res = requests.post("https://discord.com/api/v9/channels/1278344397808996454/messages", json={"content": "<@&1277926068891684946>"}, headers=h)
            n_id = res.json()['id']
            requests.patch(f"https://discord.com/api/v9/channels/1278344397808996454/messages/{n_id}", json={"content": text}, headers=h)
            config["groups"][g]["message_id"] = n_id
            requests.put(f"https://api.jsonbin.io/v3/b/{s['JSONBIN_BIN_ID']}", json=config, headers={"X-Master-Key": s['JSONBIN_API_KEY'], "Content-Type": "application/json"})
        st.success("操作完成！")
