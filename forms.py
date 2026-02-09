# forms.py
from models import User  # 现在从 models 导入，而不是 app
from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, TextAreaField, 
                     SelectField, BooleanField, SubmitField)
from wtforms.validators import (DataRequired, Email, Length, Optional, 
                                ValidationError, EqualTo)





class ContactForm(FlaskForm):

    """
    联系表单类
    每个类变量代表表单中的一个字段。
    """
    # 参数1: 字段的标签 (label)
    # validators: 验证器列表，DataRequired()表示必填
    name = StringField('姓名', validators=[
        DataRequired(message='⚠️ 请告诉我您的称呼')
    ])
    
    # Email() 验证器会检查基本的邮箱格式（是否包含@等）
    email = StringField('电子邮箱', validators=[
        DataRequired(message='⚠️ 邮箱是联系您的关键'),
        Email(message='⚠️ 这看起来不是一个有效的邮箱地址')
    ])
    
    # SelectField 下拉选择框，choices是选项列表（值, 显示文本）
    category = SelectField('咨询类型', 
                          choices=[
                              ('general', '一般咨询'),
                              ('technical', '技术问题'),
                              ('feedback', '反馈建议'),
                              ('other', '其他')
                          ],
                          default='general')
    
    # TextAreaField 多行文本框，Length可以限制文本长度
    message = TextAreaField('留言内容', validators=[
        DataRequired(message='⚠️ 请写下您想说的话'),
        Length(min=10, max=500, message='⚠️ 留言内容请控制在10到500个字符之间')
    ])
    
    # BooleanField 复选框
    subscribe = BooleanField('订阅项目更新通知')
    
    # SubmitField 提交按钮
    submit = SubmitField('提交信息')



class RegistrationForm(FlaskForm):
    """用户注册表单"""
    username = StringField('用户名', validators=[
        DataRequired(message='用户名不能为空'),
        Length(min=3, max=64, message='用户名长度应在3到64个字符之间')
    ])
    email = StringField('电子邮箱', validators=[
        DataRequired(message='邮箱不能为空'),
        Email(message='请输入有效的邮箱地址'),
        Length(max=120)
    ])
    password = PasswordField('密码', validators=[
        DataRequired(message='密码不能为空'),
        Length(min=6, message='密码至少需要6个字符')
    ])
    password2 = PasswordField('确认密码', validators=[
        DataRequired(message='请确认密码'),
        EqualTo('password', message='两次输入的密码必须一致')
    ])
    submit = SubmitField('注册')

    # 自定义验证器：检查用户名是否已存在
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('该用户名已被使用，请换一个。')

    # 自定义验证器：检查邮箱是否已存在
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('该邮箱已被注册，请使用其他邮箱或尝试登录。')

class LoginForm(FlaskForm):
    """用户登录表单"""
    email = StringField('电子邮箱', validators=[
        DataRequired(message='请输入注册邮箱'),
        Email(message='邮箱格式无效')
    ])
    password = PasswordField('密码', validators=[DataRequired(message='请输入密码')])
    remember_me = BooleanField('记住我')
    submit = SubmitField('登录')