from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from flask_mail import Message
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from forms import LoginForm, RegistrationForm, RequestResetForm, ResetPasswordForm, VerificationForm, ChangePasswordForm
from app import mail
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import random
from datetime import datetime, timedelta
import pytz

auth = Blueprint('auth', __name__)

EMAIL_SUFFIX = '@shu.edu.cn'  # 上海大学邮箱后缀

verification_codes = {}
# 创建序列化对象，用于生成和验证重置密码的令牌
def generate_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=current_app.config['SECURITY_PASSWORD_SALT'])

def verify_token(token):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt=current_app.config['SECURITY_PASSWORD_SALT'], max_age=3600)  # Token 有效期为 1 小时
        return email
    except (SignatureExpired, BadSignature):
        return None
def generate_verification_code():
    """生成6位数字验证码"""
    return ''.join(random.choices('0123456789', k=6))

# 用户登录
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('登录成功！', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('用户名或密码错误。', 'danger')
    return render_template('login.html', form=form)
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email_prefix.data + EMAIL_SUFFIX

        # 检查该邮箱是否已经注册过
        existing_user = User.query.filter_by(email=email).first()  # 假设 User 是用户模型
        if existing_user:
            flash('该邮箱已被注册，请使用其他邮箱或登录。', 'danger')
            return redirect(url_for('auth.register'))

        # 检查请求验证码的时间间隔
        last_request_time = session.get('last_verification_time', datetime(2000, 1, 1))
        now_utc = datetime.now(pytz.UTC)
        last_request_time = last_request_time.astimezone(pytz.UTC)

        if now_utc < last_request_time + timedelta(minutes=1):
            flash('请求过于频繁，请稍后再试。', 'warning')
            return redirect(url_for('auth.register'))

        # 更新最后请求时间
        session['last_verification_time'] = now_utc

        # 保存注册数据到 session
        registration_data = {
            'email': email,
            'name': form.name.data,
            'password_hash': generate_password_hash(form.password.data)
        }
        session['registration_data'] = registration_data  # 确保保存注册数据到 session
        current_app.logger.info(f"注册数据存储到 session: {registration_data}")

        # 发送验证码
        verification_code = generate_verification_code()
        msg = Message('注册验证码', recipients=[email])
        msg.body = f'您的验证码是: {verification_code}'
        mail.send(msg)

        verification_codes[email] = (verification_code, now_utc)

        flash('验证码已发送到您的邮箱，请输入验证码以完成注册。', 'info')
        return redirect(url_for('auth.verify_email', email=email))
    else:
        # 打印验证失败的字段和错误信息
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text} - {error}", 'danger')
                current_app.logger.error(f"表单验证错误 - {getattr(form, field).label.text}: {error}")

    return render_template('register.html', form=form)


@auth.route('/verify_email', methods=['GET', 'POST'])
def verify_email():
    email = request.args.get('email')
    form = VerificationForm()  # 使用 VerificationForm 表单类

    current_app.logger.info("进入 verify_email 视图函数")  # 调试信息

    if form.validate_on_submit():
        input_code = form.verification_code.data
        current_app.logger.info(f"表单验证通过, 输入的验证码: {input_code}")

        code_info = verification_codes.get(email)
        current_app.logger.info(f"从 verification_codes 获取的 code_info: {code_info}")

        if code_info:
            stored_code, timestamp = code_info
            now_utc = datetime.now(pytz.UTC)
            timestamp = timestamp.astimezone(pytz.UTC)

            current_app.logger.info(f"当前时间 (UTC): {now_utc}, 验证码时间戳 (UTC): {timestamp}")

            if now_utc > timestamp + timedelta(minutes=10):
                flash('验证码已过期，请重新获取。', 'warning')
                verification_codes.pop(email)
                current_app.logger.warning("验证码已过期")
                return redirect(url_for('auth.register'))

            if stored_code == input_code:
                registration_data = session.pop('registration_data', None)
                current_app.logger.info(f"注册数据: {registration_data}")

                if registration_data:
                    try:
                        new_user = User(
                            email=registration_data['email'],
                            name=registration_data['name'],
                            password_hash=registration_data['password_hash']
                        )
                        db.session.add(new_user)
                        db.session.commit()

                        verification_codes.pop(email)
                        flash('您的账户已创建！您现在可以登录了。', 'success')
                        current_app.logger.info("用户注册成功")
                        return redirect(url_for('auth.login'))
                    except Exception as e:
                        db.session.rollback()
                        current_app.logger.error(f"注册用户时发生错误: {e}")
                        flash('注册过程中出现问题，请稍后再试。', 'danger')
                        return redirect(url_for('auth.register'))
            else:
                flash('验证码错误，请重新输入。', 'danger')
                current_app.logger.warning("验证码错误")
                return redirect(url_for('auth.verify_email', email=email))
        else:
            flash('验证码不存在或已过期，请重新获取。', 'danger')
            current_app.logger.warning("验证码信息丢失或过期")
    else:
        current_app.logger.info("表单验证失败")
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text} - {error}", 'danger')
                current_app.logger.error(f"表单验证错误 - {getattr(form, field).label.text}: {error}")

    return render_template('verify_email.html', email=email, form=form)




# 用户注销
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))



# 请求找回密码
@auth.route('/reset_password', methods=['GET', 'POST'])
def request_reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            # 生成令牌并发送重置密码邮件
            token = generate_token(user.email)
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            msg = Message('重置密码请求', recipients=[user.email])
            msg.body = f'请点击以下链接重置您的密码：{reset_url}\n\n如果您没有请求此操作，请忽略此邮件。'
            mail.send(msg)
            
            flash('重置密码的邮件已发送，请检查您的邮箱。', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('该邮箱未注册。', 'danger')
    
    return render_template('request_reset_password.html', form=form)

# 重置密码
@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    email = verify_token(token)
    if not email:
        flash('重置密码链接无效或已过期，请重新请求。', 'warning')
        return redirect(url_for('auth.request_reset_password'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        if user:
            user.password_hash = generate_password_hash(form.password.data)
            db.session.commit()
            flash('您的密码已更新，请使用新密码登录。', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', form=form)

