from flask import Flask, request, jsonify, Response
import face_recognition
import numpy as np
from flask_cors import CORS
import json
from dev import DEVConfig
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz
from gevent import pywsgi

app = Flask(__name__)
app.config.from_object(DEVConfig)
db = SQLAlchemy(app)
face_data = {
    "samples": [],
    "ids": [],
    "names": []
}
CORS(app, origins='*')  # 允许所有跨域请求


class basic_name(db.Model):
    id = db.Column(db.String(100), primary_key=True, comment='学号')
    name = db.Column(db.String(25), nullable=False, comment='名字')
    sex = db.Column(db.String(10), nullable=True, comment='性别')
    age = db.Column(db.Integer, nullable=True, comment='年龄')
    major = db.Column(db.String(100), nullable=True, comment='专业')
    image_shape = db.Column(db.String(100), nullable=True, comment='图片大小')
    image_address = db.Column(db.LargeBinary, nullable=True, comment='图片地址')
    face_recognition = db.Column(db.BLOB, nullable=False, comment='脸部特征')
    # record_data = db.relationship('record_data')


class record_data(db.Model):
    no = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='序号')
    id = db.Column(db.String(100), nullable=False, comment='学号')
    name = db.Column(db.String(25), nullable=False, comment='名字')
    date = db.Column(db.DateTime, nullable=False, comment='时间')
    course = db.Column(db.String(100), nullable=False, comment='课程')


def loading_face_data():
    face_data["samples"] = []
    face_data["ids"] = []
    face_data["names"] = []
    with app.app_context():
        user_list = basic_name.query.all()
    for face_encoding in user_list:
        face = np.frombuffer(face_encoding.face_recognition, dtype=np.float64)
        face_data["samples"].append(face)
        face_data["ids"].append(face_encoding.id)
        face_data["names"].append(face_encoding.name)


# 自定义序列化函数
def numpy_array_serializer(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()  # 将 ndarray 转换为列表
    raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')


def test_face_data():
    name_get = request.form.get("name")
    id_get = request.form.get("id")
    print('名字')
    print(name_get)
    return jsonify({"code": 0, "msg": name_get})


def enter_face_data():  #
    name_get = request.form.get("name")
    id_get = request.form.get("id")
    if not name_get:
        return jsonify({"code": -1, "msg": "必填参数不能为空"})
    if not id_get:
        return jsonify({"code": -1, "msg": "必填参数不能为空"})
    file = request.files["file"]
    img = face_recognition.load_image_file(file)
    shape_number = img.shape
    print(shape_number)
    shape_number_str = json.dumps(shape_number)
    print(shape_number_str)
    face_locations = face_recognition.face_locations(img)
    if not face_locations:
        return jsonify({"code": -2, "msg": "识别不成功，脸请靠近一点"})
    if len(face_locations) > 1:
        return jsonify({"code": -3, "msg": "有多个人脸数据，请保证只有一个"})
    face_encodings = face_recognition.face_encodings(img, face_locations)
    face_encoding = face_encodings[0]
    with app.app_context():
        # 检查数据库中是否已经存在用户名
        existing_user = basic_name.query.filter_by(id=id_get).first()
        # 如果 existing_user 不为 None，说明数据库中已经存在该用户
        if existing_user:
            print("用户已经存在")
            return jsonify({"code": -4, "msg": "用户已经存在，不需要再次录入！"})
        else:
            distances = face_recognition.face_distance(face_data["samples"], face_encoding)
            # if not distances:

            if face_data["samples"]:
                min_distance_index = np.argmin(distances)
                if distances[min_distance_index] < 0.39:
                    return jsonify({"code": -5, "msg": "人脸信息已经存在，不需要再次录入！如有问题，请联系管理员删除。"})
                else:
                    # print(shape_number_str)
                    role = basic_name(name=name_get, id=id_get, face_recognition=face_encoding.tobytes(),
                                      image_address=img.tobytes(), image_shape=shape_number_str)
                    db.session.add(role)
                    try:
                        # 尝试执行数据库操作
                        db.session.commit()
                    except Exception as e:
                        # 捕获并处理数据库操作可能发生的错误
                        print(e)
                        return jsonify({"code": 501, "msg": "操作失误，请再次操作"})

                    # db.session.commit()
                    loading_face_data()

                    return jsonify({"code": 200, "msg": "数据录入成功"})
            else:
                # print(shape_number_str)
                role = basic_name(name=name_get, id=id_get,
                                  face_recognition=face_encoding.tobytes(), image_address=img.tobytes(),
                                  image_shape=shape_number_str)
                db.session.add(role)
                try:
                    # 尝试执行数据库操作
                    db.session.commit()
                except Exception as e:
                    # 捕获并处理数据库操作可能发生的错误
                    print(e)
                    return jsonify({"code": 501, "msg": "操作失误，请再次操作"})
                # db.session.commit()
                loading_face_data()
                return jsonify({"code": 200, "msg": "数据录入成功"})


def recognise_face():
    course_get = request.form.get("course")
    file = request.files["file"]
    img = face_recognition.load_image_file(file)
    face_locations = face_recognition.face_locations(img)
    if not face_locations:
        return jsonify({"code": -1, "msg": "识别不成功，脸请靠近一点"})
    face_encoding = face_recognition.face_encodings(img, face_locations)[0]
    distances = face_recognition.face_distance(face_data["samples"], face_encoding)
    min_distance_index = np.argmin(distances)
    if distances[min_distance_index] > 0.39:
        return jsonify({"code": -1, "msg": "人脸数据不存在"})
    else:
        with app.app_context():
            data_id = face_data["ids"][min_distance_index]
            user_name = basic_name.query.get(data_id).name
            beijing_tz = pytz.timezone('Asia/Shanghai')
            sign_time = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M:%S')
            role = record_data(id=data_id, name=user_name,
                               date=sign_time, course=course_get)
            db.session.add(role)
            try:
                # 尝试执行数据库操作
                db.session.commit()
            except Exception as e:
                # 捕获并处理数据库操作可能发生的错误
                return jsonify({"code": 502, "msg": "操作失误，请再次操作"})
            # db.session.commit()
        return jsonify({
            "code": 200,
            "msg": "识别成功",
            "data": {
                "id": face_data["ids"][min_distance_index],
                "name": face_data["names"][min_distance_index],
                "date": sign_time
            }
        })


def information_query():  # 查询
    with app.app_context():
        users = record_data.query.all()  # 执行查询
        if not users:
            return jsonify({
                "code": 505,
                "msg": "记录为空，请进行输入"
            })
        user_list = [
            {'id': user.id, 'date': user.date.strftime('%Y-%m-%d %H:%M:%S'), 'name': user.name, 'course': user.course}
            for user in users]  # 将查询结果转换为字典列表
        return jsonify({
            "code": 200,
            "msg": "查询成功",
            "data": user_list
        })


def information_delete():
    id_get = request.form.get("id")
    with app.app_context():
        try:
            # 尝试执行数据库操作
            user = basic_name.query.get(id_get)
            db.session.delete(user)
            db.session.commit()
        except Exception as e:
            # 捕获并处理数据库操作可能发生的错误
            return jsonify({"code": 503, "msg": "操作失误，请再次操作"})
        # db.session.commit()
    loading_face_data()
    return jsonify({"code": 200, "msg": "删除成功"})


def information_modify():
    with app.app_context():
        id_get = request.form.get("id")
        try:
            # 尝试执行数据库操作
            user = basic_name.query.get(id_get)
            name_get = request.form.get("name")
            if name_get:
                user.name = name_get

            sex_get = request.form.get("sex")
            if sex_get:
                user.sex = sex_get

            major_get = request.form.get("major")
            if major_get:
                user.major = major_get
            major_age = request.form.get("age")
            if major_get:
                user.age = major_age
            db.session.commit()
        except Exception as e:
            # 捕获并处理数据库操作可能发生的错误
            return jsonify({"code": 504, "msg": "操作失误，请再次操作"})
        # db.session.commit()
    loading_face_data()
    return jsonify({"code": 200, "msg": "修改成功"})


def get_student_info():
    with app.app_context():
        students = basic_name.query.all()  # 执行查询
        if not students:
            return jsonify({
                "code": 505,
                "msg": "记录为空，请进行输入"
            })
        student_list = []
        for student in students:
            # face = np.frombuffer(student.face_recognition, dtype=np.float64)
            stored_number_list_str = student.image_shape
            stored_number_list = json.loads(stored_number_list_str)
            # image_data=np.frombuffer(student.image_address, dtype=np.uint8).reshape(stored_number_list)
            student_dict = {
                'id': student.id,
                'name': student.name,
                'sex': student.sex,
                'age': student.age,
                'major': student.major,
                # 'image': image_data

            }
            student_list.append(student_dict)
        print(student_list)
        print(type(student_list))
        # student_list = [{'id': student.id, 'name': student.name,'sex':student.sex,'major':student.major,'image':} for student in
        #                 students]  # 将查询结果转换为字典列表
    try:
        response = Response()
        response.headers['Content-Type'] = 'multipart/form-data'

        return jsonify({
            "code": 200,
            "msg": "查询成功",
            "data": student_list
        })
    except Exception as e:
        # 捕获并处理数据库操作可能发生的错误
        print(e)
        return jsonify({"code": 507, "msg": "返回失败，请再次操作"})


app.add_url_rule('/student/info', 'get_student_info', get_student_info, methods=['GET'])  # 查询学生信息

app.add_url_rule('/enter/face-data', 'enter_face_data', enter_face_data, methods=['POST'])  # 名字
app.add_url_rule('/test/face-data', 'test_face_data', test_face_data, methods=['POST'])  # 名字

app.add_url_rule('/recognise/face', 'recognise_face', recognise_face, methods=['POST'])  # 比较人脸
app.add_url_rule('/information/query', 'information_query', information_query, methods=['GET'])  # 查询信息
app.add_url_rule('/information/delete', 'information_delete', information_delete, methods=['POST'])  # 删除信息
app.add_url_rule('/information/modify', 'information_modify', information_modify, methods=['POST'])  # 修改信息

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    loading_face_data()
    server = pywsgi.WSGIServer(('0.0.0.0', 5010), app)
    server.serve_forever()
