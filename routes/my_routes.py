from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Review, CourseTeacher, UserCourseTeacher, Course, Teacher
from forms import ProfileForm, ReviewForm, UploadPDFForm, SearchCourseForm, ChangePasswordForm
from utils.pdf_parser import parse_pdf_by_columns
from utils.baiduai import validate_comment
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy import func

# 创建蓝图
my = Blueprint('my', __name__, url_prefix='/my')

@my.route('/', methods=['GET'])
@login_required
def index():
    # 获取一些概览信息，如课程数量、评价数量
    course_count = UserCourseTeacher.query.filter_by(user_id=current_user.id).count()
    review_count = Review.query.filter_by(user_id=current_user.id).count()

    # 其他概览数据可以在此处添加，如最近的活动、通知等

    return render_template(
        'my_index.html',  # 模板文件 my_index.html
        course_count=course_count,
        review_count=review_count
    )

@my.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    profile_form = ProfileForm()
    change_password_form = ChangePasswordForm()

    if profile_form.validate_on_submit():
        # 更新用户信息
        current_user.name = profile_form.name.data
        db.session.commit()
        flash('个人信息已更新！', 'success')
        return redirect(url_for('my.profile'))

    # 预填当前用户信息
    profile_form.name.data = current_user.name

    return render_template(
        'profile.html',
        profile_form=profile_form,
        change_password_form=change_password_form
    )

@my.route('/profile/change_password', methods=['POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        # 检查当前密码是否正确
        if not current_user.check_password(form.current_password.data):
            flash('当前密码不正确，请重试。', 'danger')
            return redirect(url_for('my.profile'))

        # 检查新密码和确认密码是否一致
        if form.new_password.data != form.confirm_new_password.data:
            flash('新密码与确认密码不一致，请重试。', 'danger')
            return redirect(url_for('my.profile'))

        # 更新密码
        current_user.set_password(form.new_password.data)
        db.session.commit()
        flash('密码已成功更新。', 'success')
        return redirect(url_for('my.profile'))

    # 如果表单验证失败
    flash('修改密码过程中出现错误，请重试。', 'danger')
    return redirect(url_for('my.profile'))

@my.route('/courses', methods=['GET'])
@login_required
def my_courses():
    # 获取用户的课程列表
    user_courses = db.session.query(CourseTeacher).join(UserCourseTeacher).filter(
        UserCourseTeacher.user_id == current_user.id
    ).all()
    upload_form = UploadPDFForm()
    search_form = SearchCourseForm()

    return render_template(
        'my_courses.html',
        user_courses=user_courses,
        upload_form=upload_form,
        search_form=search_form
    )

@my.route('/courses/import', methods=['GET', 'POST'])
@login_required
def import_courses():
    upload_form = UploadPDFForm()
    search_form = SearchCourseForm()

    if upload_form.validate_on_submit():
        pdf_file = upload_form.pdf_file.data
        try:
            # 调用解析函数
            basic_info, courses = parse_pdf_by_columns(pdf_file)
            
            # 处理个人信息（如果需要）
            # 处理课程信息并存储到数据库
            for course in courses:
                course_code = course['课程号']
                course_name = course['课程名']
                teacher_name = course['教师姓名']

                # 查找课程
                course = Course.query.filter_by(course_code=course_code).first()
                if not course:
                    # 如果课程不存在，舍弃此数据
                    print(f"课程不存在: {course_code}, 跳过")
                    return

                # 查找教师
                teacher = Teacher.query.filter_by(name=teacher_name).first()
                if not teacher:
                    # 如果教师不存在，舍弃此数据
                    print(f"教师不存在: {teacher_name}, 跳过")
                    return

                # 查找课程-教师关联
                existing_course_teacher = CourseTeacher.query.filter_by(course_id=course.id, teacher_id=teacher.id).first()
                if not existing_course_teacher:
                    # 如果课程-教师关联不存在，舍弃此数据
                    print(f"课程-教师关联不存在: 课程 {course_code}, 教师 {teacher_name}, 跳过")
                    return

                # 如果课程、教师和课程-教师关联都存在，创建用户课程关联
                existing_user_course = UserCourseTeacher.query.filter_by(
                    user_id=current_user.id, 
                    course_teacher_id=existing_course_teacher.id
                ).first()

                # 如果用户尚未关联此课程教师，添加关联
                if not existing_user_course:
                    new_user_course = UserCourseTeacher(
                        user_id=current_user.id,
                        course_teacher_id=existing_course_teacher.id
                    )
                    db.session.add(new_user_course)
                    db.session.commit()
                    print(f"成功关联课程: 课程 {course_code}, 教师 {teacher_name}")
                else:
                    print(f"用户已关联此课程: 课程 {course_code}, 教师 {teacher_name}")

            flash('课程表已成功导入！', 'success')
        except Exception as e:
            flash(f'导入课程表时出现问题: {str(e)}', 'danger')
    # 获取用户的课程列表
    user_courses = db.session.query(CourseTeacher).join(UserCourseTeacher).filter(
        UserCourseTeacher.user_id == current_user.id
    ).all()
    return render_template('my_courses.html', user_courses=user_courses, upload_form=upload_form)

@my.route('/courses/<int:course_teacher_id>/delete', methods=['POST'])
@login_required
def delete_course(course_teacher_id):
    # 查询用户课程的关联
    user_course = UserCourseTeacher.query.filter_by(user_id=current_user.id, course_teacher_id=course_teacher_id).first_or_404()

    # 从数据库中删除该课程关联
    db.session.delete(user_course)
    db.session.commit()

    flash('课程已从您的课程列表中删除。', 'success')
    return redirect(url_for('my.my_courses'))


@my.route('/reviews', methods=['GET'])
@login_required
def my_reviews():
    reviews = Review.query.filter_by(user_id=current_user.id).all()
    form = ReviewForm()
    return render_template('my_reviews.html', reviews=reviews, form=form)

@my.route('/reviews/<int:review_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)

    # 检查权限
    if review.user_id != current_user.id:
        flash('您没有权限编辑此评论', 'danger')
        return redirect(url_for('my.my_reviews'))

    form = ReviewForm()

    if form.validate_on_submit():
        comment_content = form.comment.data
        is_valid, error_message = validate_comment(comment_content)
        if not is_valid:
            flash(f'评论内容不合法: {error_message}', 'danger')
            return render_template('edit_review.html', form=form, review=review)

        review.rating = form.rating.data
        review.comment = comment_content
        db.session.commit()
        flash('您的评价已成功更新。', 'success')
        return redirect(url_for('my.my_reviews'))

    # 预填表单数据
    form.rating.data = review.rating
    form.comment.data = review.comment

    return render_template('edit_review.html', form=form, review=review)

@my.route('/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)

    # 检查权限
    if review.user_id != current_user.id:
        flash('您没有权限删除此评论', 'danger')
        return redirect(url_for('my.my_reviews'))

    course_teacher = CourseTeacher.query.get_or_404(review.course_teacher_id)

    db.session.delete(review)
    db.session.commit()
    flash('您的评价已成功删除。', 'success')
    return redirect(url_for('my.my_reviews'))
