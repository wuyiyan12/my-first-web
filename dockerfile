# 第一步：选择一个轻量级的“箱子底板”（基础镜像）
# 使用官方Python 3.10的 slim 版本，基于Debian
FROM python:3.10-slim

# 第二步：设置容器内的“工作目录”（相当于cd进去）
WORKDIR /app

# 第三步：将“装箱清单”（requirements.txt）先复制到工作目录
# 这步先做，是为了利用Docker的缓存层，避免依赖没变时重复安装
COPY requirements.txt .

# 第四步：在容器内安装所有Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 第五步：将你当前目录下的所有应用代码复制到容器的“工作目录”
COPY . .

# 第六步：告诉Docker这个容器对外暴露哪个端口
# Flask默认跑在5000端口，容器内部要用这个端口
EXPOSE 5000

# 第七步：定义容器启动时自动执行的命令
# 这里启动Gunicorn，一个生产级的WSGI服务器，替代Flask自带的开发服务器
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]