import os
import asyncio
import requests
import gc
from io import BytesIO
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- 1. 读取配置 ---
API_ID = int(os.environ.get('API_ID'))
API_HASH = os.environ.get('API_HASH')
SESSION_STRING = os.environ.get('SESSION_STRING')
N8N_WEBHOOK = os.environ.get('N8N_WEBHOOK')
TARGET_CHAT_ID = int(os.environ.get('TARGET_CHAT_ID'))

print("正在初始化客户端...")
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# --- 2. 定义发送函数 ---
async def send_text(text, source_name):
    """发送文字消息"""
    try:
        payload = {
            'type': 'text',
            'text': text,
            'source': source_name
        }
        requests.post(N8N_WEBHOOK, json=payload, timeout=5)
        print(f"[文字] 推送成功: {text[:10]}...")
    except Exception as e:
        print(f"[文字] 推送失败: {e}")

async def send_image(img_buffer, caption, source_name):
    """发送图片消息"""
    try:
        img_buffer.seek(0)
        payload = {
            'type': 'image',
            'text': caption or "",
            'source': source_name
        }
        files = {'file': ('image.jpg', img_buffer, 'image/jpeg')}
        requests.post(N8N_WEBHOOK, data=payload, files=files, timeout=30)
        print("[图片] 推送成功")
    except Exception as e:
        print(f"[图片] 推送失败: {e}")

# --- 3. 核心：启动时发送测试通知 (新加的功能) ---
def send_startup_notification():
    print("正在发送启动测试消息...")
    try:
        # 这里构造一条假消息，模拟频道发送
        # n8n 会自动加上 [通知] 前缀，所以这里内容简单点即可
        test_payload = {
            'type': 'text',
            'text': '监控机器人已成功启动！Zeabur 到 n8n 链路通畅。',
            'source': '系统自检'
        }
        resp = requests.post(N8N_WEBHOOK, json=test_payload, timeout=10)
        if resp.status_code == 200:
            print("✅ 测试消息发送成功！请检查钉钉。")
        else:
            print(f"❌ n8n 返回错误: {resp.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到 n8n: {e}")
        print("请检查 Zeabur 环境变量里的 N8N_WEBHOOK 地址是否填对 (要是公网IP)！")

# --- 4. 监听逻辑 ---
@client.on(events.NewMessage(chats=TARGET_CHAT_ID))
async def handler(event):
    chat = await event.get_chat()
    chat_title = chat.title or "Channel"

    if event.text:
        asyncio.create_task(send_text(event.text, chat_title))

    if event.photo:
        print("检测到图片...")
        img_buffer = BytesIO()
        await event.download_media(file=img_buffer)
        await send_image(img_buffer, event.text, chat_title)
        img_buffer.close()
        del img_buffer
        gc.collect()

# --- 5. 主程序入口 ---
if __name__ == '__main__':
    # 启动客户端
    client.start()
    
    # 【重点】在正式监听之前，先发一条测试消息
    send_startup_notification()
    
    print("监控已就绪！等待频道更新消息...")
    client.run_until_disconnected()
