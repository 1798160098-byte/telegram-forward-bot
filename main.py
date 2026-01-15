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
# 确保这个地址是 n8n 的公网地址 (Production URL)
N8N_WEBHOOK = os.environ.get('N8N_WEBHOOK') 
TARGET_CHAT_ID = int(os.environ.get('TARGET_CHAT_ID'))

print(">>> 正在初始化客户端...")
client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# --- 2. 通用发送函数 ---
async def post_to_n8n(payload, files=None):
    """发送数据到 n8n，增加重试机制"""
    try:
        if files:
            # 发送图片
            requests.post(N8N_WEBHOOK, data=payload, files=files, timeout=30)
        else:
            # 发送纯文本
            requests.post(N8N_WEBHOOK, json=payload, timeout=10)
        print(f"✅ [成功推送] 内容: {payload.get('text', '')[:10]}...")
    except Exception as e:
        print(f"❌ [推送失败] 错误: {e}")
        # 这里不抛出异常，防止导致脚本崩溃

# --- 3. 启动测试 ---
def send_startup_notification():
    print(">>> 发送启动自检信号...")
    payload = {
        'type': 'text',
        'text': '🟢 监控机器人已启动 (Python -> n8n)',
        'source': '系统通知'
    }
    # 使用同步请求发送启动消息
    try:
        requests.post(N8N_WEBHOOK, json=payload, timeout=5)
        print("✅ 自检信号发送成功")
    except Exception as e:
        print(f"❌ 自检失败: {e}")
        print("⚠️ 请检查 N8N_WEBHOOK 环境变量是否填写正确，且 n8n 是否处于 Active 状态")

# --- 4. 监听逻辑 ---
@client.on(events.NewMessage(chats=TARGET_CHAT_ID))
async def handler(event):
    chat = await event.get_chat()
    source_name = chat.title or "Channel"
    
    # 获取文本内容 (如果是图片，这就是 caption)
    msg_text = event.text or ""

    if event.photo:
        print(f"📸 检测到图片消息: {msg_text[:10]}...")
        img_buffer = BytesIO()
        await event.download_media(file=img_buffer)
        img_buffer.seek(0)
        
        payload = {
            'type': 'image',
            'text': msg_text, # 把图片下方的文字传过去
            'source': source_name
        }
        files = {'file': ('image.jpg', img_buffer, 'image/jpeg')}
        
        await post_to_n8n(payload, files=files)
        
        # 清理内存
        img_buffer.close()
        del img_buffer
        gc.collect()
        
    elif msg_text:
        print(f"📝 检测到文字消息: {msg_text[:10]}...")
        payload = {
            'type': 'text',
            'text': msg_text,
            'source': source_name
        }
        await post_to_n8n(payload)

# --- 5. 入口 ---
if __name__ == '__main__':
    client.start()
    send_startup_notification()
    print(f"🚀 监控运行中... 目标频道 ID: {TARGET_CHAT_ID}")
    client.run_until_disconnected()
