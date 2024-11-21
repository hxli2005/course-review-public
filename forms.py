from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError, NumberRange, Optional
from models import User
from flask_wtf.file import FileAllowed, FileField

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    email_prefix = StringField('邮箱前缀', validators=[DataRequired()])
    name = StringField('用户名', validators=[DataRequired()])
    password = PasswordField('密码', validators=[DataRequired()])
    confirm_password = PasswordField('确认密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('注册')

    def validate_email_prefix(self, email_prefix):
        full_email = email_prefix.data + '@shu.ehu.cn'  # 拼接完整的邮箱地址
        user = User.query.filter_by(email=full_email).first()
        if user:
            raise ValidationError('该邮箱已被使用，请选择一个不同的邮箱。')

class ReviewForm(FlaskForm):
    rating = IntegerField('Rating (1-5)', validators=[DataRequired(), NumberRange(min=1, max=5)])
    comment = TextAreaField('Comment', validators=[DataRequired()])
    submit = SubmitField('Submit Review')

class RequestResetForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Email()])
    submit = SubmitField('请求重置密码')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('新密码', validators=[DataRequired(), Length(min=6, max=20)])
    confirm_password = PasswordField('确认新密码', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('重置密码')

class VerificationForm(FlaskForm):
    verification_code = StringField('验证码', validators=[DataRequired()])
    submit = SubmitField('提交')

class ProfileForm(FlaskForm):
    name = StringField('昵称', validators=[DataRequired(), Length(min=2, max=50)])
    
    # 密码是可选项，如果用户希望修改密码才会填写
    password = PasswordField('新密码', validators=[Optional(), Length(min=6)])
    confirm_password = PasswordField('确认新密码', validators=[
        Optional(),
        EqualTo('password', message='两次输入的密码必须一致')
    ])
    
    submit = SubmitField('保存修改')

class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('当前密码', validators=[DataRequired(), Length(min=6, message="密码至少需要6个字符")])
    new_password = PasswordField('新密码', validators=[
        DataRequired(), 
        Length(min=6, message="密码至少需要6个字符")
    ])
    confirm_new_password = PasswordField('确认新密码', validators=[
        DataRequired(), 
        EqualTo('new_password', message="两次输入的密码必须一致")
    ])
    submit = SubmitField('修改密码')

    # 上传 PDF 表单
class UploadPDFForm(FlaskForm):
    pdf_file = FileField('上传课程表 (PDF)', validators=[
        DataRequired(),
        FileAllowed(['pdf'], '只允许上传 PDF 文件')
    ])
    submit = SubmitField('导入课程表')

class SearchCourseForm(FlaskForm):
    course_name = StringField('课程名', validators=[DataRequired()])
    course_code = StringField('课程号', validators=[DataRequired()])
    teacher_name = StringField('教师姓名', validators=[DataRequired()])
    submit = SubmitField('搜索')