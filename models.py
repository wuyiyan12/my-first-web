# models.py
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# 注意：这里先声明 db，但暂时不初始化
db = SQLAlchemy()

class User(db.Model, UserMixin):
    """用户模型"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    # 重点：密码散列值，不存储明文密码！
    password_hash = db.Column(db.String(256), nullable=False)
    # 新增字段：注册时间
    member_since = db.Column(db.DateTime, default=datetime.utcnow)
    # 建立与“联系提交记录”的一对多关系
    # 'backref' 会在 ContactSubmission 模型中添加一个 `.author` 属性，指向所属用户
    submissions = db.relationship('ContactSubmission', backref='author', lazy=True)

    def set_password(self, password):
        """接收明文密码，计算其哈希值并存储"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """验证输入的密码是否与存储的哈希值匹配"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<用户 {self.username}>'

class ContactSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), default='general')
    message = db.Column(db.Text, nullable=False)
    subscribe = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    # 外键：关联到 User 模型，允许为空（未登录用户也可提交）
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def __repr__(self):
         # 微调显示，更清晰
        return f'<提交记录 {self.id} 来自用户 {self.user_id}>'
#        return f'<提交来自 "{self.name}">'
    
     
    def to_dict(self):
        """将模型实例转换为字典，用于表单预填充或API"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'category': self.category,
            'message': self.message,
            'subscribe': self.subscribe,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }
