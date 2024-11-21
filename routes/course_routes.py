from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Course, Teacher, CourseTeacher, Review
from flask_login import login_required, current_user
from forms import ReviewForm
from sqlalchemy.orm import joinedload
from sqlalchemy import func

course = Blueprint('course', __name__)



@course.route('/courses', methods=['GET'])
def list_courses():
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)  # 默认每页显示10条

    # 构建查询，明确使用 Course 作为 select_from 的起点
    courses_query = db.session.query(
        Course,
        func.count(Review.id).label('review_count')  # 计算每个课程的评论数量
    ).select_from(Course).outerjoin(
        CourseTeacher, CourseTeacher.course_id == Course.id  # 明确连接 CourseTeacher 的条件
    ).outerjoin(
        Review, Review.course_teacher_id == CourseTeacher.id  # 明确连接 Review 的条件
    ).options(
        joinedload(Course.course_teachers).joinedload(CourseTeacher.teacher)
    ).group_by(Course.id)  # 确保 group_by 的对象是明确的

    # 根据搜索条件过滤
    if search_query:
        courses_query = courses_query.filter(
            Course.course_name.ilike(f'%{search_query}%') |
            Course.course_code.ilike(f'%{search_query}%')
        )

    # 按评论数量降序排序，使有评论的课程优先
    courses_query = courses_query.order_by(func.count(Review.id).desc())

    # 对查询结果进行分页
    courses = courses_query.paginate(page=page, per_page=per_page)

    # 预处理教师和学期信息
    processed_courses = []
    for course, review_count in courses.items:
        # 提取教师信息
        teachers = {ct.teacher.name for ct in course.course_teachers}

        # 提取学期信息
        semesters = set()
        for ct in course.course_teachers:
            if ct.semester_info:  # 确保 `semester_info` 存在
                # 如果 `semester_info` 是列表，遍历每个学期
                if isinstance(ct.semester_info, list):
                    for sem_info in ct.semester_info:
                        if 'semester' in sem_info:
                            semesters.add(sem_info['semester'])
                # 如果 `semester_info` 是字典，直接提取学期
                elif isinstance(ct.semester_info, dict) and 'semester' in ct.semester_info:
                    semesters.add(ct.semester_info['semester'])

        # 将处理后的课程信息添加到结果列表
        processed_courses.append({
            'course': course,
            'teachers': ', '.join(teachers),
            'semesters': ', '.join(semesters),
            'review_count': review_count  # 添加评论数量信息
        })

    return render_template(
        'course_list.html',
        courses=processed_courses,
        pagination=courses,
        search_query=search_query,
        per_page=per_page
    )



@course.route('/courses/<int:course_id>', methods=['GET'])
def course_detail(course_id):
    course = Course.query.get_or_404(course_id)
    
    # 获取与该课程相关的教师和学期信息
    course_teachers = CourseTeacher.query.filter_by(course_id=course_id).all()

    # 处理教师和学期信息
    teachers_info = []
    for ct in course_teachers:
        # 确保 `semester_info` 字段存在，如果为空则设为 {}
        semester_info = ct.semester_info or {}

        # 如果 `semester_info` 是列表，遍历列表提取学期名称
        if isinstance(semester_info, list):
            semester_names = [sem.get('semester', '未指定学期') for sem in semester_info if isinstance(sem, dict)]
        # 如果 `semester_info` 是字典，直接提取学期名称
        elif isinstance(semester_info, dict):
            semester_names = [semester_info.get('semester', '未指定学期')]
        else:
            semester_names = ['未指定学期']

        # 输出或保存处理后的学期名称
        print(f"学期名称: {', '.join(semester_names)}")


        # 计算平均评分
        reviews_query = db.session.query(
            func.avg(Review.rating).label('average_rating')
        ).filter_by(course_teacher_id=ct.id).first()

        if reviews_query and reviews_query.average_rating is not None:
            average_rating = round(reviews_query.average_rating, 2)
        else:
            average_rating = '暂无评分'

        review_count = Review.query.filter_by(course_teacher_id=ct.id).count()
        
        # 将裸数组转换成对应的中文名称
        semester_map = {'Fall': '秋', 'Spring': '春', 'Summer': '夏', 'Winter': '冬'}  # 季节转换映射
        semester_str = ', '.join([f"{item.split()[0]}{semester_map[item.split()[1]]}" for item in semester_names])

        teachers_info.append({
            'teacher_id': ct.teacher.id, 
            'teacher_name': ct.teacher.name,
            'teacher_title': ct.teacher.title,
            'semester_name': semester_str,
            'average_rating': average_rating,
            'review_count': review_count
        })

    return render_template('course_detail.html', course=course, teachers_info=teachers_info)




