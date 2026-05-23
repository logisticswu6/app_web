import streamlit as st
import requests, json

# 透過 st.secrets 讀取，這是在 Streamlit Cloud 後台設定的
s = json.loads(st.secrets["CONFIG_DATA"])

st.markdown('<meta http-equiv="refresh" content="20">', unsafe_allow_html=True)

# 取得最新的雲端資料庫資料
config = requests.get(f"https://api.jsonbin.io/v3/b/{s['JSONBIN_BIN_ID']}/latest", headers={"X-Master-Key": s['JSONBIN_API_KEY']}).json().get("record", {})

st.title("🚀 Discord 雲端同步助手")
u = st.selectbox("人員", list(config["tokens"].keys()))
g = st.selectbox("群組", list(config["groups"].keys()))
uid = st.text_input("User ID", value=config.get("user_id", ""))
txt = st.text_area("文宣內容")

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
    st.success("操作完成")
