FROM python:3.10-slim

WORKDIR /app
ENV TZ=Asia/Shanghai

# 👇 这一行是专门治“哑巴”的
ENV PYTHONUNBUFFERED=1

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 启动
CMD ["python", "main.py"]
