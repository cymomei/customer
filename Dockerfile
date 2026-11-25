FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

# 先只拷依赖清单再安装，充分利用构建缓存
COPY requirements.txt /srv/requirements.txt
RUN pip install -r /srv/requirements.txt

# 保持 app/ 与 static/ 为同级目录：这样代码里
# BASE_DIR = Path(__file__).resolve().parent.parent => /srv
# FRONT_PATH = /srv/static 才能正确命中前端文件
COPY ./app /srv/app
COPY ./static /srv/static

EXPOSE 8806

# 监听 0.0.0.0，容器外（宿主机/局域网）才能访问前端
# 用模块路径 app.CustomerController:app，需在 WORKDIR /srv 下运行
CMD ["uvicorn", "app.CustomerController:app", "--host", "0.0.0.0", "--port", "8806"]
