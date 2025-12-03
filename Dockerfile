# 1. 选择基础镜像
FROM python:3.10-slim

# 2. 设置容器内的工作目录
WORKDIR /app

# === 🚀 换源：使用阿里云镜像 (解决 apt-get 卡顿) ===
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list

# 3. 安装系统级依赖
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 4. 复制依赖文件
COPY requirements.txt .

# === 5. 安装依赖 (关键修改) ===

# 5.1 安装 PyTorch (CPU版本 - 轻量、通用、下载快)
RUN pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

# 5.2 安装 requirements.txt 中的其他依赖
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# ============================

# 6. 复制项目代码
COPY . .

# 7. 暴露端口
EXPOSE 8000

# 8. 启动命令
CMD ["python", "main.py"]