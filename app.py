# 在 app.py 顶部附近，其他导入语句旁边
from models import db, User, ContactSubmission
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from forms import ContactForm, LoginForm, RegistrationForm
import os
from flask_login import LoginManager
from flask_login import login_user, logout_user, current_user, login_required

app = Flask(__name__)

app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'  # 必须设置，用于flash消息加密
# 配置SQLite数据库URI。///是相对路径，db文件将位于项目根目录。
basedir = os.path.abspath(os.path.dirname(__file__)) # 获取当前文件所在目录的绝对路径
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'site.db')
# 这样无论项目在哪个服务器、哪个目录下，都能正确定位到 site.db 文件
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 1. 初始化扩展
db.init_app(app)  # 注意：因为我们改用了 models.py 中的 db，这里需要用 init_app
login_manager = LoginManager()  # 2. 创建 LoginManager 实例
login_manager.init_app(app)     # 3. 将其与app关联

# 4. 配置 LoginManager
login_manager.login_view = 'login'
login_manager.login_message = '请先登录以访问此页面。'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """必需的：告诉 Flask-Login 如何根据ID加载用户"""
    # 因为此时已导入 User 模型，可以直接使用
    return User.query.get(int(user_id))


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
        
        # 关键：只有已登录用户才能自动关联，匿名用户的 user_id 为 None
        if current_user.is_authenticated:
            new_submission.user_id = current_user.id
        
        # 4. 保存到数据库
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

@app.route('/register', methods=['GET', 'POST'])
def register():
    # 如果用户已登录，则重定向到首页
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # 1. 创建新用户对象
        user = User(username=form.username.data, email=form.email.data)
        # 2. 使用我们定义的 set_password 方法设置哈希后的密码
        user.set_password(form.password.data)
        # 3. 保存到数据库
        db.session.add(user)
        db.session.commit()
        
        flash(f'🎉 恭喜，{user.username}！您的账户已成功创建。', 'success')
        # 4. 注册后自动登录
        login_user(user)
        return redirect(url_for('home'))
    
    page_data = {
        'page_title': '用户注册',
        'form': form
    }
    return render_template('register.html', **page_data)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # 1. 通过邮箱查找用户
        user = User.query.filter_by(email=form.email.data).first()
        # 2. 检查用户是否存在且密码正确
        if user is None or not user.check_password(form.password.data):
            flash('⚠️ 邮箱或密码无效，请重试。', 'danger')
            return redirect(url_for('login'))
        # 3. 登录用户，并可选地“记住”登录状态
        login_user(user, remember=form.remember_me.data)
        flash(f'👋 欢迎回来，{user.username}！', 'success')
        # 4. 如果用户是尝试访问某个受保护页面后被重定向过来的，则跳回原页面，否则跳首页
        next_page = request.args.get('next')
        # 安全检查：确保 next_page 是本站点内部的 URL（防止开放重定向）
        if next_page and next_page.startswith('/'):
            return redirect(next_page)
        return redirect(url_for('home'))
    
    page_data = {
        'page_title': '用户登录',
        'form': form
    }
    return render_template('login.html', **page_data)

@app.route('/logout')
def logout():
    logout_user()
    flash('👋 您已成功退出登录。', 'info')
    return redirect(url_for('home'))


@app.route('/submissions')
@login_required  # 保护此页面，只有登录用户能看
def submissions():
    """
    显示当前登录用户的所有提交记录
    """
    # 通过 user_id 查询属于当前用户的所有提交记录，按时间倒序排列
    user_submissions = ContactSubmission.query.filter_by(user_id=current_user.id).order_by(ContactSubmission.submitted_at.desc()).all()
    
    submissions_data = {
        'page_title': '我的提交记录',
        'dynamic_message': f'你共有 {len(user_submissions)} 条记录。',
        'current_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'submissions': user_submissions  # 传递过滤后的记录
    }
    return render_template('submissions.html', **submissions_data)

@app.route('/submission/<int:id>/delete', methods=['POST'])
def delete_submission(id):
    """
    删除指定ID的记录（仅允许记录所有者删除）
    :param id: 要删除的记录ID，从URL中获取
    """
    # 1. 尝试从数据库中找到这条记录
    submission_to_delete = ContactSubmission.query.get(id)
    
    # 2. 如果没找到，给用户一个错误提示
    if not submission_to_delete:
        flash('未找到要删除的记录！', 'error')
        return redirect(url_for('submissions'))
    
    # 3. 权限检查：仅允许记录所有者删除自己的记录
    if submission_to_delete.user_id != current_user.id:
        flash('⚠️ 您无权删除他人的记录！', 'danger')
        return redirect(url_for('submissions'))
    
    # 4. 找到后，执行删除
    db.session.delete(submission_to_delete)
    db.session.commit()
    
    # 5. 删除成功后，提示用户
    flash(f'记录 #{id} 已被成功删除。', 'success')
    
    # 6. 重定向回记录列表页
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
        subscribe=data.get('subscribe', False),
        user_id=current_user.id if current_user.is_authenticated else None  # 关联当前用户
    )
    
    # 5. 保存到数据库
    db.session.add(new_submission)
    db.session.commit()
    
    # 6. 返回成功响应，包含新记录的ID
    return jsonify({
        'status': 'success',
        'message': '记录创建成功！',
        'data': {
            'id': new_submission.id,
            'name': new_submission.name,
            'category': new_submission.category,
            'message': new_submission.message[:50] + '...' if len(new_submission.message) > 50 else new_submission.message,
            'submitted_at': new_submission.submitted_at.strftime('%Y-%m-%d %H:%M')
        }
    }), 201  # 201 是资源创建成功的状态码   

@app.route('/profile')
@login_required
def profile():
    """用户个人资料页面"""
    # 可以在这里准备更多用户相关的统计数据
    # 例如：计算用户的提交总数
    submission_count = len(current_user.submissions)
    
    profile_data = {
        'page_title': '个人资料',
        'user': current_user,
        'submission_count': submission_count,
        'member_since': current_user.member_since if hasattr(current_user, 'member_since') else '近期'
    }
    return render_template('profile.html', **profile_data)

@app.route('/api/submission/<int:id>', methods=['DELETE'])
@login_required
def api_delete_submission(id):
    """通过API删除记录"""
    submission = ContactSubmission.query.get_or_404(id)
    
    # 权限检查：只能删除自己的记录
    if submission.author != current_user:
        return jsonify({
            'status': 'error',
            'message': '权限不足：您只能删除自己的记录'
        }), 403
    
    db.session.delete(submission)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'message': f'记录 #{id} 已删除'
    })

# 应用启动时初始化数据库
with app.app_context():
    db.create_all()  # 创建所有数据库表（如果不存在）    # 打印已注册的所有路由（调试用）
    registered_endpoints = sorted(app.view_functions.keys())
    print("\n" + "="*60)
    print("✅ Flask 应用已加载，已注册的路由端点：")
    print(registered_endpoints)
    print("="*60 + "\n")

"""
if __name__ == '__main__':
    app.run(debug=True) # 这行在本地运行，在服务器上会被忽略
"""

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    # 开发环境用调试模式，生产环境关闭
#    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
#    app.run(host='0.0.0.0', port=port, debug=debug)
    app.run(host='localhost', port=port, debug=True)  # 本地开发时使用localhost，生产环境改为0.0.0.0
