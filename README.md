# 人脸识别签到服务

Flask + face_recognition 的人脸签到服务：录入学生人脸、刷脸签到、查/改/删记录，数据落 MySQL，附 Dockerfile 可一键起。

个人项目（学习/课程练习性质，不是生产系统）—— 用来把「人脸识别 + Python 服务 + 数据库 + 容器化」这条链路完整跑一遍。

## 接口

| 接口 | 方法 | 说明 |
| --- | --- | --- |
| `/student/info` | GET | 学生列表（学号 / 姓名 / 性别 / 年龄 / 专业） |
| `/enter/face-data` | POST | 录入人脸，multipart 传 `id`、`name`、`file`；校验参数、是否重复录入、是否与人脸库撞脸 |
| `/recognise/face` | POST | 刷脸签到，multipart 传 `course`、`file`；命中后写签到记录并返回姓名与时间 |
| `/information/query` | GET | 签到记录列表 |
| `/information/modify` | POST | 修改学生信息（姓名 / 性别 / 专业 / 年龄） |
| `/information/delete` | POST | 按学号删除学生 |

返回统一是 `{"code": ..., "msg": ..., "data": ...}`，`code=200` 为成功，负数是校验类错误（脸没识别到、多张脸、已存在等），5xx 是数据库操作失败。

## 技术栈

- Flask + Flask-SQLAlchemy + MySQL（PyMySQL 驱动）
- face_recognition / dlib：`face_locations` 定位、`face_encodings` 取 128 维特征
- gevent.pywsgi 起服务
- Docker（`python:3.7.9` 基础镜像，暴露 5010）

## 快速开始

### 本地跑

```sh
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # 填自己的 MySQL 连接串
set -a; source .env; set +a
python main.py                # 监听 0.0.0.0:5010
```

首次启动会自动 `db.create_all()` 建 `basic_name`（人脸库）和 `record_data`（签到记录）两张表。dlib 编译比较慢，macOS 上建议先 `brew install cmake`。

### Docker

```sh
docker build -t face-attendance .
docker run --rm -p 5010:5010 \
  -e DATABASE_URL='mysql+pymysql://user:password@host:3306/face_attendance' \
  face-attendance
```

## 几个实现要点

- **人脸特征存 BLOB**：128 维向量 `tobytes()` 存 MySQL，服务启动时全部读进内存，识别时用 `face_distance` 逐个比、取最小距离。
- **阈值 0.39**（比 face_recognition 默认的 0.6 严）：既用于识别判定，也用于「这张脸是不是已经录过」的查重。
- **两张表**：`basic_name` 存人脸库（学号主键 + 特征 + 原始图字节），`record_data` 存每次签到（学号 / 姓名 / 时间 / 课程）。
- **CORS 全开**（`origins='*'`）：方便前端联调，正式环境必须收紧。

## 注意

- 这个服务本质是**采集人脸数据**，仓库里不含任何真实学生数据；测试请用自己或朋友的照片，别把真人库提交上来。
- 数据库连接串只从环境变量读，`.env` 已进 `.gitignore`。
- 识别阈值、去重逻辑都是经验值，换摄像头/光线条件要重新调。

## License

MIT
