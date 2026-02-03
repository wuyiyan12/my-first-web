from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from forms import ContactForm
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'  # 必须设置，用于flash消息加密
# 配置SQLite数据库URI。///是相对路径，db文件将位于项目根目录。
basedir = os.path.abspath(os.path.dirname(__file__)) # 获取当前文件所在目录的绝对路径
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')
# 这样无论项目在哪个服务器、哪个目录下，都能正确定位到 site.db 文件
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库扩展
db = SQLAlchemy(app)

class ContactSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), default='general')
    message = db.Column(db.Text, nullable=False)
    subscribe = db.Column(db.Boolean, default=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<提交来自 "{self.name}">'
    
     
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


@app.route('/')
def home():
    template_data = {
        'page_title': '欢迎来到学习之旅！',
        'dynamic_message': '你已成功掌握了Flask模板继承！',
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    # 渲染继承自 base.html 的 index.html
    return render_template('index.html', **template_data)

@app.route('/about')
def about():
    about_data = {
        'page_title': '关于这个网站',
        'dynamic_message': '此消息证明数据传递在继承体系中完全有效。',
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    }
    # 渲染继承自 base.html 的 about.html
    return render_template('about.html', **about_data)

# 替换原来的 @app.route('/contact', methods=['GET', 'POST']) 及其下方的整个函数
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    # 1. 创建表单实例
    form = ContactForm()
    
    # 2. 判断：如果是表单提交（POST）并且通过了所有验证规则
    if form.validate_on_submit():
        # 3. 数据已验证通过，直接使用 form.字段名.data 获取清洗后的数据
        new_submission = ContactSubmission(
            name=form.name.data,
            email=form.email.data,
            category=form.category.data,
            message=form.message.data,
            subscribe=form.subscribe.data  # 复选框，True 或 False
        )
        
        # 4. 保存到数据库（这部分和以前一样）
        db.session.add(new_submission)
        db.session.commit()
        
        # 5. 成功提示
        flash(f'✅ 感谢 {form.name.data}！您的咨询 (#{new_submission.id}) 已收到。', 'success')
        
        # 6. 重定向到记录页面（防止刷新浏览器导致重复提交）
        return redirect(url_for('submissions'))
    
    # 7. 如果是GET请求，或者表单验证失败，则渲染页面
    #    此时，form对象会自带用户上次输入的数据和错误信息
    page_data = {
        'page_title': '联系我们 (升级版)',
        'dynamic_message': '请填写下方表单，所有字段均为必填。',
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'form': form  # 关键：将表单对象传递给模板
    }
    return render_template('contact_wtf.html', **page_data)

@app.route('/submissions')
def submissions():
    # 从数据库查询所有记录，按提交时间倒序排列
    all_submissions = ContactSubmission.query.order_by(ContactSubmission.submitted_at.desc()).all()
    
    submissions_data = {
        'page_title': '咨询提交记录',
        'dynamic_message': f'共找到 {len(all_submissions)} 条记录。',
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'submissions': all_submissions  # 将查询结果传递给模板
    }
    return render_template('submissions.html', **submissions_data)

@app.route('/submission/<int:id>/delete', methods=['POST']) # 注意：限定为POST方法
def delete_submission(id):
    """
    删除指定ID的记录
    :param id: 要删除的记录ID，从URL中获取
    """
    # 1. 尝试从数据库中找到这条记录
    submission_to_delete = ContactSubmission.query.get(id)
    
    # 2. 如果没找到，给用户一个错误提示
    if not submission_to_delete:
        flash('未找到要删除的记录！', 'error')
        return redirect(url_for('submissions'))
    
    # 3. 找到后，执行删除
    db.session.delete(submission_to_delete)
    db.session.commit()
    
    # 4. 删除成功后，提示用户
    flash(f'记录 #{id} 已被成功删除。', 'success')
    
    # 5. 重定向回记录列表页
    return redirect(url_for('submissions'))

# API 路由：获取所有提交记录
@app.route('/api/submissions', methods=['GET'])
def api_get_submissions():
    """
    GET /api/submissions
    返回所有提交记录的JSON列表。
    用于让其他程序读取数据。
    """
    # 1. 从数据库查询所有记录（和之前一样）
    all_submissions = ContactSubmission.query.order_by(ContactSubmission.submitted_at.desc()).all()
    
    # 2. 将每条记录转换成字典，组成一个列表
    #    这里我们复用之前在 ContactSubmission 模型中定义的 to_dict() 方法
    submissions_list = [sub.to_dict() for sub in all_submissions]
    
    # 3. 构建一个更完整的JSON响应
    response = {
        'status': 'success',
        'message': f'成功获取 {len(submissions_list)} 条记录',
        'count': len(submissions_list),
        'data': submissions_list  # 主要数据在这里
    }
    
    # 4. 使用 jsonify 将Python字典转换为JSON格式的HTTP响应
    return jsonify(response)

# API 路由：创建一条新记录
@app.route('/api/submission', methods=['POST'])
def api_create_submission():
    """
    POST /api/submission
    通过接收JSON数据来创建一条新记录。
    用于让其他程序提交数据。
    """
    # 1. 检查请求是否包含JSON数据
    if not request.is_json:
        return jsonify({
            'status': 'error',
            'message': '请求的内容类型必须是 application/json'
        }), 400  # 400 是客户端错误的状态码
    
    # 2. 获取JSON数据
    data = request.get_json()
    
    # 3. 简单的数据验证（生产环境需要更严格的验证）
    required_fields = ['name', 'email', 'message']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'status': 'error',
                'message': f'缺少必填字段: {field}'
            }), 400
    
    # 4. 创建新记录（忽略我们表单中不需要的字段，如category和subscribe）
    new_submission = ContactSubmission(
        name=data['name'],
        email=data['email'],
        category=data.get('category', 'general'),  # 使用 .get() 提供默认值
        message=data['message'],
        subscribe=data.get('subscribe', False)
    )
    
    # 5. 保存到数据库
    db.session.add(new_submission)
    db.session.commit()
    
    # 6. 返回成功响应，包含新记录的ID
    return jsonify({
        'status': 'success',
        'message': '记录创建成功',
        'id': new_submission.id,
        'data': new_submission.to_dict()  # 返回创建好的完整记录
    }), 201  # 201 是“已创建”的标准状态码

# 创建数据库表（仅在初次运行时或模型变更后）
with app.app_context():
    db.create_all()
    print("✅ 数据库表已就绪！")



if __name__ == '__main__':
    app.run(debug=True) # 这行在本地运行，在服务器上会被忽略