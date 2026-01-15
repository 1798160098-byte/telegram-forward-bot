import os
import asyncio
import requests
import gc
from io import BytesIO
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# --- 1. 读取 Zeabur 里填写的配置 ---
API_ID = int(os.environ.get('API_ID'))
API_HASH = os.environ.get('API_HASH')
SESSION_STRING = os.environ.get('SESSION_STRING')
N8N_WEBHOOK = os.environ.get('N8N_WEBHOOK')
TARGET_CHAT_ID = int(os.environ.get('TARGET_CHAT_ID'))

print("正在启动频道监控程序...")

# --- 2. 登录 Telegram (使用 Session String 免验证码) ---
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# --- 3. 定义发送函数 ---
async def send_text(text, source_name):
    """只发文字，追求极速"""
    try:
        payload = {
            'type': 'text',
            'text': text,
            'source': source_name
        }
        # 5秒超时，发不出去就算了，别卡死程序
        requests.post(N8N_WEBHOOK, json=payload, timeout=5)
        print(f"[文字] 已推送到 n8n: {text[:10]}...")
    except Exception as e:
        print(f"[文字] 推送失败: {e}")

async def send_image(img_buffer, caption, source_name):
    """发送图片，允许慢一点"""
    try:
        img_buffer.seek(0) # 指针归位
        payload = {
            'type': 'image',
            'text': caption or "",
            'source': source_name
        }
        # 上传文件
        files = {'file': ('image.jpg', img_buffer, 'image/jpeg')}
        requests.post(N8N_WEBHOOK, data=payload, files=files, timeout=30)
        print("[图片] 已推送到 n8n")
    except Exception as e:
        print(f"[图片] 推送失败: {e}")

# --- 4. 监听逻辑 (核心) ---
# chats=TARGET_CHAT_ID 确保了只监听这一个频道
@client.on(events.NewMessage(chats=TARGET_CHAT_ID))
async def handler(event):
    # 获取频道名称用于显示
    chat = await event.get_chat()
    chat_title = chat.title or "Channel"

    # 策略 A: 如果有文字，立刻用异步任务发送 (0延迟)
    if event.text:
        asyncio.create_task(send_text(event.text, chat_title))

    # 策略 B: 如果有图片，下载到内存处理
    if event.photo:
        print("检测到图片，开始下载...")
        img_buffer = BytesIO()
        # 下载图片到内存流，不占硬盘
        await event.download_media(file=img_buffer)

        # 发送图片
        await send_image(img_buffer, event.text, chat_title)

        # 清理内存 (Zeabur 免费版内存小，这一步很重要)
        img_buffer.close()
        del img_buffer
        gc.collect()

print("监控已就绪！等待频道更新消息...")
client.start()
client.run_until_disconnected()
