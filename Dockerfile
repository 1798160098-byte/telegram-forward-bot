FROM python:3.10-slim

WORKDIR /app
ENV TZ=Asia/Shanghai

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 启动
CMD ["python", "main.py"]
