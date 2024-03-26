# 使用Python官方的镜像作为基础镜像
FROM python:3.7.9

# 将当前目录下的所有文件复制到容器的/app目录下
COPY . /app

# 设置工作目录为/app
WORKDIR /app

RUN pip config set global.index-url https://mirror.baidu.com/pypi/simple

# 安装所需的依赖
RUN pip install -r requirements.txt

# Expose port 5010
EXPOSE 5010

# 运行Python程序
CMD ["python", "main.py"]
