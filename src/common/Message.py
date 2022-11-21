# 主要用于统一返回消息格式
class Message:
    @staticmethod
    def success(message):
        return {
            "code": 200,
            "message": message
        }
    @staticmethod
    def error(message):
        return {
            "code": 500,
            "message": message
        }
