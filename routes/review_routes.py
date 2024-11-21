from flask import Blueprint, render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from models import db, Review, CourseTeacher, Course, Teacher, ReviewLike, UserCourseTeacher
from forms import ReviewForm, ProfileForm, ChangePasswordForm
from sqlalchemy import func
from utils.baiduai import validate_comment

review = Blueprint('review', __name__)


@review.route('/courses/<int:course_id>/teachers/<int:teacher_id>/reviews', methods=['GET', 'POST'])
@login_required
def course_teacher_reviews(course_id, teacher_id):
    # 获取课程和教师对象
    course = Course.query.get_or_404(course_id)
    teacher = Teacher.query.get_or_404(teacher_id)
    
    # 获取课程-教师关联的对象
    course_teacher = CourseTeacher.query.filter_by(course_id=course_id, teacher_id=teacher_id).first_or_404()

    # 创建评论表单
    form = ReviewForm()

    # 获取评论的平均评分
    reviews_query = db.session.query(
        func.avg(Review.rating).label('average_rating')
    ).filter_by(course_teacher_id=course_teacher.id).first()

    average_rating = round(reviews_query.average_rating, 2) if reviews_query and reviews_query.average_rating is not None else '暂无评分'

    # 按点赞数降序获取评论，包含用户信息
    reviews = Review.query.filter_by(course_teacher_id=course_teacher.id).order_by(Review.likes.desc()).all()

    # 如果是 POST 请求，处理课程添加到用户的课程列表
    if request.method == 'POST':
        # 检查用户是否已经添加了该课程
        existing_course = UserCourseTeacher.query.filter_by(user_id=current_user.id, course_teacher_id=course_teacher.id).first()
        if existing_course:
            flash('该课程已经在您的课程列表中。', 'warning')
        else:
            # 如果课程未添加，则添加课程
            new_user_course = UserCourseTeacher(
                user_id=current_user.id,
                course_teacher_id=course_teacher.id
            )
            db.session.add(new_user_course)
            db.session.commit()
            flash('课程已成功添加到您的课程列表。', 'success')
        return redirect(url_for('review.course_teacher_reviews', course_id=course_id, teacher_id=teacher_id))

    # 返回模板并传递相关数据
    return render_template(
        'course_teacher_reviews.html',
        course=course,
        teacher=teacher,
        course_teacher=course_teacher,
        reviews=reviews,
        average_rating=average_rating,
        form=form
    )


# 点赞功能的路由
@review.route('/reviews/<int:review_id>/like', methods=['POST'])
@login_required
def toggle_like_review(review_id):
    review = Review.query.get_or_404(review_id)

    # 检查当前用户是否已经点赞
    existing_like = db.session.query(ReviewLike).filter_by(review_id=review_id, user_id=current_user.id).first()

    if existing_like:
        # 如果已经点赞，则取消点赞
        db.session.delete(existing_like)
        review.likes -= 1
        action = 'unliked'  # 标记为取消点赞
    else:
        # 如果没有点赞，则添加点赞
        new_like = ReviewLike(review_id=review_id, user_id=current_user.id)
        db.session.add(new_like)
        review.likes += 1
        action = 'liked'  # 标记为点赞

    db.session.commit()

    return jsonify({'likes': review.likes, 'action': action})



@review.route('/courses/<int:course_id>/teachers/<int:teacher_id>/submit', methods=['POST'])
@login_required
def submit_review(course_id, teacher_id):
    course_teacher = CourseTeacher.query.filter_by(course_id=course_id, teacher_id=teacher_id).first_or_404()

    form = ReviewForm()
    if form.validate_on_submit():
        # 检查是否已有评价
        existing_review = Review.query.filter_by(user_id=current_user.id, course_teacher_id=course_teacher.id).first()
        if existing_review:
            flash('您已经为该课程和教师提交过评价。', 'warning')
            return redirect(url_for('review.course_teacher_reviews', course_id=course_id, teacher_id=teacher_id))
        
        # 获取评论内容
        comment_content = form.comment.data

        # 调用审核 API 审核评论内容
        is_valid, error_message = validate_comment(comment_content)
        if not is_valid:
            flash(f'评论内容不合法: {error_message}', 'danger')
            return redirect(url_for('review.course_teacher_reviews', course_id=course_id, teacher_id=teacher_id))

        # 评论通过审核，保存到数据库
        new_review = Review(
            user_id=current_user.id,
            course_teacher_id=course_teacher.id,
            rating=form.rating.data,
            comment=comment_content,
            likes=0  # 初始化点赞数为 0
        )
        db.session.add(new_review)
        db.session.commit()
        flash('您的评价已成功提交。', 'success')
        return redirect(url_for('review.course_teacher_reviews', course_id=course_id, teacher_id=teacher_id))
    else:
        flash('提交过程中出现错误。请检查表单并重试。', 'danger')

    return redirect(url_for('review.course_teacher_reviews', course_id=course_id, teacher_id=teacher_id))






@review.route('/reviews/<int:review_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    # 检查是否有权限编辑评论
    if review.user_id != current_user.id:
        flash('您没有权限编辑评论', 'danger')
        return redirect(url_for('main.index'))

    form = ReviewForm()
    
    if form.validate_on_submit():
        # 获取评论内容
        comment_content = form.comment.data
        
        # 调用审核 API 审核评论内容
        is_valid, error_message = validate_comment(comment_content)
        if not is_valid:
            flash(f'评论内容不合法: {error_message}', 'danger')
            return render_template('edit_review.html', form=form, review=review)
        
        # 更新评论内容
        review.rating = form.rating.data
        review.comment = comment_content  # 更新评论内容
        db.session.commit()
        flash('您的评价已成功提交。', 'success')
        return redirect(url_for('review.course_teacher_reviews', 
                                course_id=review.course_teacher.course_id, 
                                teacher_id=review.course_teacher.teacher_id))

    # 预填现有的评论数据
    form.rating.data = review.rating
    form.comment.data = review.comment
    
    # 渲染模板并传递评论对象
    return render_template('edit_review.html', form=form, review=review)


@review.route('/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    if review.user_id != current_user.id:
        flash('您没有权限删除评论', 'danger')
        return redirect(url_for('main.index'))

    # 使用 review.course_teacher_id 查询 CourseTeacher
    course_teacher = CourseTeacher.query.get_or_404(review.course_teacher_id)

    db.session.delete(review)
    db.session.commit()
    flash('您的评价已成功删除。', 'success')
    return redirect(url_for('review.course_teacher_reviews', 
                            course_id=course_teacher.course_id, 
                            teacher_id=course_teacher.teacher_id))


