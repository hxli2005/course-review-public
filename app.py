from flask import Flask
from flask_wtf.csrf import CSRFProtect
from models import db, login_manager, User, CourseTeacher, Review
from config import Config
from flask_mail import Mail
from flask_apscheduler import APScheduler
from utils.openai import  generate_detailed_summary
from utils.selection import select_comments
from sqlalchemy import func
import openai
import time
from pytz import timezone
from datetime import datetime, timedelta
from flask_talisman import Talisman

# 初始化 Flask 扩展
mail = Mail()
scheduler = APScheduler()

last_update_time = None


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app():
    app = Flask(__name__)
    Talisman(app, force_https=True)

    app.config.from_object(Config)
    csrf = CSRFProtect(app)

    # Initialize the extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    # Initialize and start APScheduler
 
    

    @scheduler.task('cron', id='update_summaries', hour=12, minute=30, timezone=timezone('Asia/Shanghai'))
    def update_course_teacher_summaries():
        """定时任务：更新评论数超过15的课程-教师的评价总结。"""

        global last_update_time
        current_time = datetime.now()

        # 如果上次更新时间距离现在不足1小时，跳过本次更新
        if last_update_time and current_time - last_update_time < timedelta(minutes=1):
            print("Skipped update: Task already ran recently.")
            return
        last_update_time = current_time


        with scheduler.app.app_context():
            print ("Updating course teacher summaries...")
            # 查询评论数超过15的课程-教师
            course_teachers = CourseTeacher.query.join(Review).group_by(CourseTeacher.id).having(func.count(Review.id) >= 5).all()

            for course_teacher in course_teachers:
                # 获取所有相关的评论
                reviews = Review.query.filter_by(course_teacher_id=course_teacher.id).all()
                selected_comments = select_comments(reviews, 10)  # 使用筛选算法
                review_texts = [review.comment for review in reviews] #不筛选

                if review_texts:
                    retry_attempts = 5  # 最大重试次数
                    attempt = 0  # 初始化重试计数器
                    while attempt < retry_attempts:
                        try:
                            # 生成总结
                            formatted_summary = generate_detailed_summary(
                                review_texts, 
                                course_teacher.teacher.name, 
                                course_teacher.course.course_name
                            )
                            
                            # 更新总结数据到数据库
                            course_teacher.summary_data = formatted_summary
                            db.session.commit()
                            print(f"Updated summaries for CourseTeacher {course_teacher.id}: {formatted_summary}")
                            break  # 成功后跳出循环
                        except openai.error.RateLimitError as e:
                            print(f"Rate limit exceeded: {e}. Retrying in 10 seconds...")
                            time.sleep(10)  # 等待 10 秒后重试
                            attempt += 1  # 增加重试计数器
                        except Exception as e:
                            print(f"An error occurred while generating summary: {e}")
                            break  # 其他错误不再重试

    # Ensure APScheduler starts with the app
    scheduler.init_app(app)
    scheduler.start()
    print(scheduler.get_jobs())
    # Set the login view to redirect unauthorized users to the login page
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "请先登录以访问此页面。"
    login_manager.login_message_category = "warning"

    # Register Blueprints
    from routes.auth_routes import auth
    from routes.course_routes import course
    from routes.review_routes import review
    from routes.main_routes import main
    from routes.teacher_routes import teacher
    from routes.my_routes import my

    app.register_blueprint(auth)
    app.register_blueprint(course)
    app.register_blueprint(review)
    app.register_blueprint(main)
    app.register_blueprint(teacher)
    app.register_blueprint(my)

    openai.api_type = app.config['AZURE_OPENAI_API_TYPE']
    openai.api_key = app.config['AZURE_OPENAI_API_KEY']
    openai.api_base = app.config['AZURE_OPENAI_ENDPOINT']
    openai.api_version = app.config['AZURE_OPENAI_API_VERSION']

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True,use_reloader=False)
