import time
import requests
from logzero import logger
from requests import RequestException
from PIL import Image
import base64
import re
import ddddocr
from io import BytesIO
import sqlite3
from common.Message import Message

# 这其中包括了对于之前的图片验证码那识别和对于问题的获取以及通过数据库进行问题的存储
def getGifOnline(cookies):
    url = 'http://freshmansno.wh.sdu.edu.cn:9007/common/code'
    headers = {
        'Host': 'freshmansno.wh.sdu.edu.cn:9007',
        "Connection": "keep-alive",
        "Content-Length": "0",
        "Accept": "*/*",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "http://freshmansno.wh.sdu.edu.cn:9007",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        'Referer': 'http://freshmansno.wh.sdu.edu.cn:9007/apply.html',
        'Cookie': cookies
    }

    try:
        res = requests.post(url, headers=headers)
        if res.status_code == 200:
            if res.json()['code'] == 0:
                logger.info("获取图片成功, 准备识别...")
                imgKey = res.json()['data']['key']
                imgBase64 = res.json()['data']['base64']
                return imgKey, imgBase64
            else:
                logger.info(res.json()['msg'])
                time.sleep(1)
        else:
            logger.info(res.status_code)
    except RequestException as e:
        logger.error({e})

    return "", ""


def getAuthCodeNoCache(imgBase64):
    # 前半部分decode参考: https://blog.51cto.com/u_13567403/5019004
    # 1、信息提取
    result = re.search(
        "data:image/(?P<ext>.*?);base64,(?P<data>.*)", imgBase64, re.DOTALL)
    if result:
        ext = result.groupdict().get("ext")
        data = result.groupdict().get("data")

    else:
        raise Exception("Do not parse!")

    # 2、base64解码
    img = base64.urlsafe_b64decode(data)

    # 3、二进制文件保存
    filename = "img/{}.gif".format("authcode")
    with open(filename, "wb") as f:
        f.write(img)

    # 4、提取gif
    gif = Image.open(filename)
    bytesPngList = []

    try:
        # gif.save(f"img/authcode-{gif.tell()}.png")
        stream = BytesIO()
        gif.save(stream, format="png")
        bytesIO = stream.getvalue()
        bytesPng = bytes(bytesIO)
        bytesPngList.append(bytesPng)
        stream.close()
        while True:
            gif.seek(gif.tell() + 1)
            # gif.save(f'img/authcode-{gif.tell()}.png')
            stream = BytesIO()
            gif.save(stream, format="png")
            bytesIO = stream.getvalue()
            bytesPng = bytes(bytesIO)
            bytesPngList.append(bytesPng)
            stream.close()
    except Exception as e:
        print("处理结束")

    ocr = ddddocr.DdddOcr(show_ad=False)
    resList = []
    for bytesPng in bytesPngList:
        resList.append(ocr.classification(bytesPng))

    try:
        res = (resList[4][0] + resList[3][1] + resList[2][2] + resList[1][3] + resList[0][3]).lower()
    except Exception as e:
        print("部分验证码超出限制, 请重新获取!")
        res = ""
    logger.info("验证码识别完成! 识别结果: {}".format(res))
    return res

def getTextQuestionOnline(cookies):
    url = 'http://freshmansno.wh.sdu.edu.cn:9007/common/question'
    headers = {
        'Host': 'freshmansno.wh.sdu.edu.cn:9007',
        "Connection": "keep-alive",
        "Content-Length": "0",
        "Accept": "*/*",
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
        "X-Requested-With": "XMLHttpRequest",
        "Origin": "http://freshmansno.wh.sdu.edu.cn:9007",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
        'Referer': 'http://freshmansno.wh.sdu.edu.cn:9007/apply.html',
        'Cookie': cookies
    }

    try:
        res = requests.post(url, headers=headers)
        if res.status_code == 200:
            if res.json()['code'] == 0:
                logger.info("获取问题成功, 准备处理...")
                questionID = res.json()['data']['id']
                question = res.json()['data']['tm']
                questionMessage = {"questionKey": questionID, "question": question}
                return Message.success(questionMessage)
            else:
                logger.info(res.json()['msg'])
        else:
            logger.info(res.status_code)
    except RequestException as e:
        logger.error({e})

    return Message.error("获取问题失败")

def getTextQuestionAnsweFromSQL(questionKey, questionStr):
    db = sqlite3.connect("../freshmansno.db")
    # 查询sql
    sql = f'select questionKey, question, questionValue from questionAnswer where questionKey = "{questionKey}" or question like "%{questionStr}%"'
    try:
        response = db.execute(sql)
        datas = response.fetchall()
        if len(datas) >= 1:
            logger.info("获取问题成功, 准备处理...")
            data = datas[0]
            key = data[0]
            value = data[2]

            logger.info(f"key: {key}, value: {value}")

            # questionAnswerStr = f"key={key}&value={urllib.parse.quote(value)}"
            message = {"key": key, "value": value}
            return Message.success(message)
        else:
            logger.info("问题不在数据库中, 准备加入数据库, 记得完善答案...")
            # 添加到数据库
            sql = f'insert into questionAnswer (questionKey, question, questionValue) values ("{questionKey}", "{questionStr}", "")'
            insertRes = db.execute(sql)
            db.commit()
            return Message.error("问题不在数据库中, 准备加入数据库, 记得完善答案...")
    except Exception as e:
        logger.error(e)
        db.rollback()
        return Message.error("数据库错误, 请联系管理员!")


# sqllite 与 mysql 相互迁移数据
#
# def sqliteToMysql(sqlliteDB, mysqlHost, mysqlUser, mysqlPassword, mysqlDB):
#     db = pymysql.connect(
#         host=mysqlHost,
#         port=3306,
#         user=mysqlUser,
#         password=mysqlPassword,
#         database=mysqlDB
#     )
#     cursor = db.cursor()
#     sqllite = sqlite3.connect(sqlliteDB)
#     sql = "select * from questionAnswer"
#     try:
#         response = sqllite.execute(sql)
#         if response >= 1:
#             data = response.fetchall()
#             for item in data:
#                 key = item[0]
#                 question = item[1]
#                 value = item[2]
#                 sql = f'insert into questionAnswer (`key`, question, `value`) values ("{key}", {question}, "{value}")'
#                 insertRes = cursor.execute(sql)
#                 db.commit()
#
#     except Exception as e:
#         logger.error(e)
#         db.rollback()




