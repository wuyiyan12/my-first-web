# forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional

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