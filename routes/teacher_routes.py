from flask import Blueprint, render_template, request
from models import Teacher, CourseTeacher, Review, db
from sqlalchemy import func
from sqlalchemy.orm import joinedload


teacher = Blueprint('teacher', __name__)

@teacher.route('/teachers', methods=['GET'])
def list_teachers():
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)  # 默认每页显示10条

    # 构建查询，计算每个教师的评论数量，用于排序
    teachers_query = db.session.query(
        Teacher
    ).outerjoin(CourseTeacher, CourseTeacher.teacher_id == Teacher.id  # 明确连接 CourseTeacher 的条件
    ).outerjoin(Review, Review.course_teacher_id == CourseTeacher.id  # 明确连接 Review 的条件
    ).group_by(Teacher.id)  # 确保分组依据是教师的 ID

    # 根据搜索条件过滤
    if search_query:
        teachers_query = teachers_query.filter(
            Teacher.name.ilike(f'%{search_query}%')
        )

    # 按评论数量降序排序，使有评论的教师优先
    teachers_query = teachers_query.order_by(func.count(Review.id).desc())

    # 对查询结果进行分页
    teachers = teachers_query.paginate(page=page, per_page=per_page)

    # 将数据传递到前端
    return render_template(
        'teacher_list.html',
        teachers=teachers.items,
        pagination=teachers,
        search_query=search_query,
        per_page=per_page
    )

@teacher.route('/teachers/<int:teacher_id>')
def teacher_detail(teacher_id):
    teacher = Teacher.query.get_or_404(teacher_id)
    courses = CourseTeacher.query.filter_by(teacher_id=teacher.id).all()
    return render_template('teacher_detail.html', teacher=teacher, courses=courses)
