import openai
import time
from config import Config
import logging
openai.api_type = Config.AZURE_OPENAI_API_TYPE
openai.api_key = Config.AZURE_OPENAI_API_KEY
openai.api_base = Config.AZURE_OPENAI_ENDPOINT
openai.api_version = Config.AZURE_OPENAI_API_VERSION



# 设置日志记录
logging.basicConfig(level=logging.INFO)
def generate_detailed_summary(review_texts, teacher_name, course_name):
    """生成详细的课程评价总结，包括各方面的评价、总体评价和选课建议。"""
    combined_reviews = " ".join(review_texts)
    prompt = (
        f"请根据以下评论内容，生成课程的详细评价，包括课程内容质量、教师教学、学习体验、学生收获、对教师期末给分的评价、总体评价和选课建议。"
        f"请按标准化格式输出，并确保每部分换行。\n\n评论内容：\n\n{combined_reviews}\n\n"
        f"{teacher_name}老师的{course_name}课程评价\n"
        f"课程内容质量：\n[内容评价]\n\n"
        f"教师教学：\n[教学评价]\n\n"
        f"学习体验：\n[体验评价]\n\n"
        f"学生收获：\n[收获评价]\n\n"
        f"期末给分：\n[给分评价]\n\n"
        f"总体评价：\n[总体评价]\n\n"+
        f"选课建议：\n[建议]\n\n"
    )

    for attempt in range(3):  # 尝试最多3次
        try:
            response = openai.ChatCompletion.create(
                engine='newgpt',  # 部署名称
                messages=[
                    {"role": "system", "content": "你是一个可以总结课程评价的助手，请用中文回答。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except openai.error.RateLimitError as e:
            logging.warning(f"Rate limit exceeded, retrying... (attempt {attempt + 1})")
            time.sleep(10 * (2 ** attempt))  # 指数退避
        except Exception as e:
            logging.error(f"An error occurred while generating summary: {e}")
            return "生成总结时出现错误。"
    return "生成总结时出现错误。"

