from apscheduler.schedulers.blocking import BlockingScheduler
from common.Login import Login
import requests
import json
import urllib
from common.Message import Message
from logzero import logger
from src.common import authCodeUtil
import sys

with open("buildingCodeForGym.json", mode='r') as file:
    data: dict = json.load(file)

# 返回 (buidingcode, kssj, jssj)
flag = False
def pickUp(cookie, buildingCodes: list) -> tuple:

    headers = {
        'Host': 'freshmansno.wh.sdu.edu.cn:9007',
        'Accept-Encoding': 'gzip, deflate',
        'Cookie': cookie,
        'Connection': 'keep-alive',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
        'Referer': 'http://freshmansno.wh.sdu.edu.cn:9007/apply.html',
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
    }

    for buildingCode in buildingCodes:
        logger.info(f"开始尝试预约{buildingCode}...")
        url = f"http://freshmansno.wh.sdu.edu.cn:9007/common/getTimeSetInfo?page=1&limit=10&buildingCode={buildingCode}&sf_request_type=ajax"
        # response 会返回json格式的数据
        response = requests.get(url=url, headers=headers, verify=False)
        # 读取json数据
        try:
            data: list = json.loads(response.text).get("data")
            # 从后向前遍历
            for index in range(len(data)-1, -1, -1):
                item: dict = data[index]
                if (item.get("sfcgqxcs") == "是"):

                    return Message.error("取消次数超过限制")
                if (item.get("sfyyyToday") == 1):
                    return Message.error("今天已经预约过")
                if (item.get("sfyyy") == 1):
                    return Message.error("已经预约过")
                if (item.get("yxrs") - item.get("yyrs") > 0 and item.get("sfgq") == "否"):
                    # 可以预约
                    question = getQuestion(cookie)
                    if question.get('code') == 200:
                        key = question.get('message').get('key')
                        value = question.get('message').get('value')
                        res = bookSimple(cookie, buildingCode, key, value, item.get("kssj"), item.get("jssj"))
                        """
                        没啥用，提示成功的
                        """
                        rescontent = res.content.decode()
                        if 'null' in rescontent:
                            rescontent = rescontent.replace("null", "None")
                        resdict = eval(rescontent)
                        if (resdict.get('code') == 0 and resdict.get('data') == 1):
                            logger.info("预约成功！")
                            flag = True
                            # 成功之后停止定时任务
                            scheduler.remove_job('pickUp')
                            scheduler.shutdown(wait=False)
                            return Message.success((buildingCode, item.get("kssj"), item.get("jssj")))
                    else:
                        logger.error(f"{buildingCode}-{item.get('kssj')}-{item.get('jssj')}获取题目失败")
                else:
                    continue
        except Exception as e:
            print(e)


def getQuestion(cookie):

    questionMessage = authCodeUtil.getTextQuestionOnline(cookie)
    if questionMessage.get('code') == 500:
        return Message.error("获取题目失败")

    message: dict = questionMessage.get("message")
    questionKey = message.get("questionKey")
    questionStr = message.get("question")
    # 从数据库中获取答案
    valueMessage = authCodeUtil.getTextQuestionAnsweFromSQL(questionKey, questionStr)
    # 如果数据库中没有答案,直接退出
    if valueMessage.get('code') == 500:
        return Message.error("获取答案失败")

    value = valueMessage.get('message').get("value")

    return Message.success({"key": questionKey, "value": value})

def bookSimple(cookie, buildingCode, key, value, kssj="19:00", jssj="21:00"):
    # 将上面的转为下面的header
    header = {
        'Host': 'freshmansno.wh.sdu.edu.cn:9007',
        'Accept': '*/*',
        'X-Requested-With': 'XMLHttpRequest',
        'Accept-Language': 'zh-CN,zh-Hans;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'http://freshmansno.wh.sdu.edu.cn:9007',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15',
        'Connection': 'keep-alive',
        'Referer': 'http://freshmansno.wh.sdu.edu.cn:9007/apply.html',
        'Cookie': cookie
    }
    url = "http://freshmansno.wh.sdu.edu.cn:9007/common/submitApply"
    data = f"key={key}&value={urllib.parse.quote(value)}&buildingCode={buildingCode}&kssj={urllib.parse.quote(kssj)}&jssj={urllib.parse.quote(jssj)}"
    res = requests.post(url, data=data, headers=header, verify=False)
    print(res.content.decode())
    return res


scheduler = BlockingScheduler()

# 从txt中获取username和password
with open("bookInformation.txt", "r") as f:
    # 将文件加载为
    bookData: dict = eval(f.read())

def main():
    # 优先使用sys.argv中的参数,如果没有,则使用bookInformation.txt中的参数
    username = sys.argv[1] if len(sys.argv) > 1 else bookData.get("username")
    password = sys.argv[2] if len(sys.argv) > 2 else bookData.get("password")
    # interval如果有sys.argv参数，就用参数，没有使用默认30s
    interval = int(sys.argv[3]) if len(sys.argv) > 3 else 30
    cookie = Login(username, password).getCookies()
    buidingCodes = sys.argv[4:] if len(sys.argv) > 4 else [1003, 1006]
    # 创建一个定时任务，30s执行一次，如果成功则停止
    scheduler.add_job(func=pickUp, args=(cookie, buidingCodes), trigger='interval', seconds=interval, id='pickUp')
    scheduler.start()


if __name__ == '__main__':
    main()