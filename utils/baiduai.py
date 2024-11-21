from aip import AipContentCensor
from flask import current_app

def get_baidu_client():
    """
    获取百度 AI 客户端实例。
    """
    return AipContentCensor(
        current_app.config['BAIDU_APP_ID'],
        current_app.config['BAIDU_API_KEY'],
        current_app.config['BAIDU_SECRET_KEY']
    )

def validate_comment(content):
    """
    使用百度 AI 审核 API 验证评论是否合法。
    :param content: 评论的文本内容
    :return: True 如果评论合法，否则 False 和错误信息。
    """
    client = get_baidu_client()
    response = client.textCensorUserDefined(content)
    if 'conclusionType' in response and response['conclusionType'] == 1:
        return True, None  # 合法
    else:
        # 获取不合法的原因
        error_message = response.get('data', [{}])[0].get('msg', 'Unknown error')
        return False, error_message
