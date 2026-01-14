import os
import asyncio
import requests
import gc
from io import BytesIO
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- 从环境变量读取配置 (在 Zeabur 里填) ---
API_ID = int(os.environ.get('API_ID'))
API_HASH = os.environ.get('API_HASH')
SESSION_STRING = os.environ.get('SESSION_STRING')

# 你的 n8n 地址
N8N_WEBHOOK = os.environ.get('N8N_WEBHOOK')

# 监控配置
TARGET_CHAT_ID = int(os.environ.get('TARGET_CHAT_ID'))
TARGET_BOT_ID = int(os.environ.get('TARGET_BOT_ID'))
# ------------------------------------------

print("正在启动...")
# 使用 StringSession 免验证码登录
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

async def send_text(text, sender_name):
    """极速发送文本"""
    try:
        payload = {
            'type': 'text',
            'text': text,
            'sender': sender_name
        }
        # 5秒超时，保证不阻塞
        requests.post(N8N_WEBHOOK, json=payload, timeout=5)
        print(f"[Text] 发送成功: {text[:10]}...")
    except Exception as e:
        print(f"[Text] 发送失败: {e}")

async def send_image(img_buffer, caption, sender_name):
    """发送图片"""
    try:
        img_buffer.seek(0)
        payload = {
            'type': 'image',
            'text': caption or "",
            'sender': sender_name
        }
        files = {'file': ('image.jpg', img_buffer, 'image/jpeg')}
        requests.post(N8N_WEBHOOK, data=payload, files=files, timeout=30)
        print("[Image] 图片发送成功")
    except Exception as e:
        print(f"[Image] 图片发送失败: {e}")

@client.on(events.NewMessage(chats=TARGET_CHAT_ID))
async def handler(event):
    sender = await event.get_sender()
    # 1. 验证是否是目标机器人发的消息
    if not sender or sender.id != TARGET_BOT_ID:
        return

    sender_name = sender.first_name or "Bot"

    # 2. 如果有文字，立刻发送（毫秒级响应）
    if event.text:
        asyncio.create_task(send_text(event.text, sender_name))

    # 3. 如果有图片，下载到内存并发送
    if event.photo:
        print("检测到图片，正在处理...")
        img_buffer = BytesIO()
        await event.download_media(file=img_buffer)

        await send_image(img_buffer, event.text, sender_name)

        # 释放内存
        img_buffer.close()
        del img_buffer
        gc.collect()

print("监控服务已启动！等待消息中...")
client.start()
client.run_until_disconnected()
