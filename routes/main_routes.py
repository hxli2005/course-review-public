from flask import Blueprint, render_template
from models import CourseTeacher, Review, db
from sqlalchemy import func


main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index():
    # 获取每门课程的平均评分和评论数量
    courses_with_reviews = db.session.query(
        CourseTeacher,
        func.round(func.avg(Review.rating), 2).label('average_rating'),  # 保留两位小数的平均评分
        func.count(Review.id).label('review_count')  # 计算评论数量
    ).join(Review).group_by(CourseTeacher).all()

    # 计算综合评分，并按综合评分排序
    # 设置评分权重为0.7，评论数量权重为0.3，可以根据需求调整
    courses_with_scores = [
        {
            'course_teacher': course_teacher,
            'average_rating': float(average_rating),  # 将 Decimal 转为 float
            'review_count': review_count,
            'composite_score': (float(average_rating) * 0.7) + (review_count * 0.3)  # 综合评分
        }
        for course_teacher, average_rating, review_count in courses_with_reviews  # 注意这里解包三个变量
    ]

    # 按综合评分排序，取前5名作为热门课程
    popular_courses = sorted(courses_with_scores, key=lambda x: x['composite_score'], reverse=True)[:5]

    return render_template('index.html', popular_courses=popular_courses)



@main.route('/about')
def about():
    return render_template('about.html')
