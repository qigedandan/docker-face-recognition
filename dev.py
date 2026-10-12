import os


class DEVConfig(object):
    DEBUG = True

    # 数据库连接串从环境变量读取；本地开发请复制 .env.example 为 .env 再填自己的库
    # 格式：mysql+pymysql://<账号>:<密码>@<IP>:<端口>/<库名>
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "mysql+pymysql://user:password@127.0.0.1:3306/face_attendance",
    )

    # 动态追踪修改设置，未设置只会提示警告
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 查询时是否打印原始 SQL
    SQLALCHEMY_ECHO = os.environ.get("SQLALCHEMY_ECHO", "0") == "1"
