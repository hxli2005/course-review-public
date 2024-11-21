from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB


db = SQLAlchemy()
login_manager = LoginManager()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='student')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    reviews = db.relationship('Review', back_populates='user')
    review_likes = db.relationship('ReviewLike', back_populates='user', cascade='all, delete-orphan')
    user_courses = db.relationship('UserCourseTeacher', back_populates='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(50), nullable=False)
    course_name = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    credit = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    teachers = db.relationship('Teacher', secondary='course_teacher', back_populates='courses', overlaps="course_teachers,teacher_courses")
    course_teachers = db.relationship('CourseTeacher', back_populates='course', overlaps="teachers")

class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    courses = db.relationship('Course', secondary='course_teacher', back_populates='teachers', overlaps="course_teachers,teacher_courses")
    teacher_courses = db.relationship('CourseTeacher', back_populates='teacher', overlaps="courses")

class CourseTeacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    semester_info = db.Column(JSONB, nullable=True)  # 使用 JSONB 字段存储学期信息
    summary_data = db.Column(JSONB, nullable=True)  # 使用 JSONB 字段存储总结信息
    position = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 关系
    course = db.relationship('Course', back_populates='course_teachers', overlaps="teachers,courses")
    teacher = db.relationship('Teacher', back_populates='teacher_courses', overlaps="courses,teachers")
    reviews = db.relationship('Review', back_populates='course_teacher')

class Review(db.Model):
    __tablename__ = 'review'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_teacher_id = db.Column(db.Integer, db.ForeignKey('course_teacher.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    likes = db.Column(db.Integer, default=0)
    likes_relation = db.relationship('ReviewLike', back_populates='review', cascade='all, delete-orphan')# 关系定义：与 ReviewLike 的关联
    course_teacher = db.relationship('CourseTeacher', back_populates='reviews')
    user = db.relationship('User', back_populates='reviews')

class ReviewLike(db.Model):
    __tablename__ = 'review_likes'

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 关系定义
    review = db.relationship('Review', back_populates='likes_relation')
    user = db.relationship('User', back_populates='review_likes')
    # 确保同一用户只能对同一条评论点一次赞
    __table_args__ = (db.UniqueConstraint('review_id', 'user_id', name='_user_review_uc'),)

class UserCourseTeacher(db.Model):
    __tablename__ = 'user_course_teacher'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    course_teacher_id = db.Column(db.Integer, db.ForeignKey('course_teacher.id'), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关系定义
    user = db.relationship('User', back_populates='user_courses')
    course_teacher = db.relationship('CourseTeacher')

    # 确保每个用户的课程-教师关联是唯一的
    __table_args__ = (db.UniqueConstraint('user_id', 'course_teacher_id', name='_user_course_teacher_uc'),)
