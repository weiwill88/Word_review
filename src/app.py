from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from supabase import create_client, Client
from dotenv import load_dotenv
import os
from passlib.hash import pbkdf2_sha256
from datetime import datetime, timedelta
import random

# 加载环境变量
load_dotenv()

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# 初始化Supabase客户端
supabase: Client = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_KEY')
)

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']
        self.role = user_data['role']
        self.class_id = user_data['class_id']

@login_manager.user_loader
def load_user(user_id):
    try:
        user_data = supabase.table('users').select('*').eq('id', user_id).execute()
        if user_data.data:
            return User(user_data.data[0])
    except Exception as e:
        print(f"Error loading user: {e}")
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        try:
            # 查询用户
            user_data = supabase.table('users').select('*').eq('username', username).execute()
            
            if user_data.data and pbkdf2_sha256.verify(password, user_data.data[0]['password_hash']):
                user = User(user_data.data[0])
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('用户名或密码错误')
        except Exception as e:
            flash(f'登录失败: {str(e)}')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        class_id = request.form.get('class_id')
        
        try:
            # 检查用户名是否已存在
            existing_user = supabase.table('users').select('*').eq('username', username).execute()
            if existing_user.data:
                flash('用户名已存在')
                return render_template('register.html')
            
            # 创建新用户
            password_hash = pbkdf2_sha256.hash(password)
            new_user = {
                'username': username,
                'password_hash': password_hash,
                'role': role,
                'class_id': class_id
            }
            
            result = supabase.table('users').insert(new_user).execute()
            flash('注册成功，请登录')
            return redirect(url_for('login'))
            
        except Exception as e:
            flash(f'注册失败: {str(e)}')
    
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'teacher':
        # 获取教师仪表板数据
        try:
            # 获取班级学生数量
            student_count = supabase.table('users').select('count').eq('class_id', current_user.class_id).eq('role', 'student').execute()
            
            # 获取今日活跃学生数
            today = datetime.now().date()
            active_today = supabase.table('learning_records').select('distinct user_id').eq('class_id', current_user.class_id).gte('created_at', today).execute()
            
            # 获取需要关注的学生
            attention_needed = supabase.rpc('get_attention_needed_students', {'teacher_class_id': current_user.class_id}).execute()
            
            # 获取常见错误单词
            common_errors = supabase.rpc('get_common_error_words', {'teacher_class_id': current_user.class_id}).execute()
            
            return render_template('teacher_dashboard.html',
                                student_count=student_count.count,
                                active_today=len(active_today.data),
                                attention_needed=attention_needed.data,
                                common_errors=common_errors.data)
        except Exception as e:
            flash(f'获取数据失败: {str(e)}')
            return render_template('teacher_dashboard.html')
    else:
        # 获取学生仪表板数据
        try:
            # 获取今日学习单词数
            today = datetime.now().date()
            today_words = supabase.table('learning_records').select('count').eq('user_id', current_user.id).gte('created_at', today).execute()
            
            # 获取连续打卡天数
            streak_days = supabase.rpc('get_streak_days', {'student_id': current_user.id}).execute()
            
            # 获取最近7天正确率
            week_ago = datetime.now() - timedelta(days=7)
            accuracy = supabase.rpc('get_student_accuracy', {'student_id': current_user.id, 'start_date': week_ago}).execute()
            
            # 获取最近活动
            activities = supabase.table('learning_records').select('*').eq('user_id', current_user.id).order('created_at', desc=True).limit(5).execute()
            
            return render_template('student_dashboard.html',
                                today_words=today_words.count,
                                streak_days=streak_days.data,
                                accuracy=accuracy.data,
                                activities=activities.data)
        except Exception as e:
            flash(f'获取数据失败: {str(e)}')
            return render_template('student_dashboard.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/word_matching')
@login_required
def word_matching():
    try:
        # 获取用户当前进度
        user_progress = supabase.rpc('get_user_progress', {'user_id': current_user.id}).execute()
        current_level = 1  # 默认级别
        
        if user_progress and user_progress.data:
            # 如果返回的是列表且不为空
            if isinstance(user_progress.data, list) and len(user_progress.data) > 0:
                current_level = user_progress.data[0]['current_level']
            # 如果返回的是字典
            elif isinstance(user_progress.data, dict):
                current_level = user_progress.data['current_level']
        
        # 获取适合用户水平的单词集
        word_set = supabase.table('word_sets')\
            .select('*')\
            .eq('difficulty_level', current_level)\
            .execute()
        
        if not word_set.data:
            flash('没有找到合适的单词集')
            return redirect(url_for('dashboard'))
        
        # 获取单词集中的单词
        words = supabase.table('word_set_items')\
            .select('words(*)')\
            .eq('word_set_id', word_set.data[0]['id'])\
            .execute()
        
        if not words.data:
            flash('单词集中没有单词')
            return redirect(url_for('dashboard'))
        
        # 准备单词数据
        word_pairs = []
        for item in words.data:
            word = item['words']
            word_pairs.append({
                'id': word['id'],
                'english': word['english'],
                'chinese': word['chinese']
            })
        
        return render_template('word_matching.html', 
                            word_set=word_set.data[0],
                            word_pairs=word_pairs)
    except Exception as e:
        app.logger.error(f'加载单词失败: {str(e)}')  # 添加日志记录
        flash(f'加载单词失败: {str(e)}')
        return redirect(url_for('dashboard'))

@app.route('/api/submit_matching', methods=['POST'])
@login_required
def submit_matching():
    try:
        data = request.get_json()
        word_set_id = data.get('word_set_id')
        matches = data.get('matches', [])
        error_count = data.get('error_count', 0)
        time_spent = data.get('time_spent', 0)  # 以秒为单位
        
        # 记录学习记录
        learning_record = {
            'user_id': current_user.id,
            'word_set_id': word_set_id,
            'error_count': error_count,
            'time_spent': time_spent,
            'completion_time': 'now()'
        }
        supabase.table('learning_records').insert(learning_record).execute()
        
        # 记录错误单词
        if error_count > 0:
            for match in matches:
                if not match['correct']:
                    error_record = {
                        'user_id': current_user.id,
                        'word_id': match['word_id']
                    }
                    supabase.table('error_records').insert(error_record).execute()
        
        return jsonify({
            'success': True,
            'message': '提交成功'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'提交失败: {str(e)}'
        })

@app.route('/word_review')
@login_required
def word_review():
    try:
        # 获取用户的错误单词
        error_words = supabase.rpc('get_user_error_words', {
            'user_id': current_user.id,
            'limit_count': 10  # 每次复习10个单词
        }).execute()

        if not error_words.data:
            flash('暂时没有需要复习的单词')
            return redirect(url_for('dashboard'))

        return render_template('word_review.html', words=error_words.data)
    except Exception as e:
        flash(f'加载错误单词失败: {str(e)}')
        return redirect(url_for('dashboard'))

@app.route('/api/submit_review', methods=['POST'])
@login_required
def submit_review():
    try:
        data = request.get_json()
        word_results = data.get('results', [])
        
        # 记录复习结果
        for result in word_results:
            word_id = result.get('word_id')
            is_correct = result.get('correct', False)
            
            if is_correct:
                # 如果正确，从错误记录中删除
                supabase.table('error_records')\
                    .delete()\
                    .eq('user_id', current_user.id)\
                    .eq('word_id', word_id)\
                    .execute()
            else:
                # 如果错误，更新错误次数
                supabase.table('error_records')\
                    .upsert({
                        'user_id': current_user.id,
                        'word_id': word_id,
                        'error_count': 1
                    })\
                    .execute()
        
        return jsonify({
            'success': True,
            'message': '复习记录已保存'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        })

@app.route('/manage_students')
@login_required
def manage_students():
    # TODO: 实现学生管理功能
    return "学生管理功能开发中..."

@app.route('/manage_words')
@login_required
def manage_words():
    # TODO: 实现单词管理功能
    return "单词管理功能开发中..."

@app.route('/learning_reports')
@login_required
def learning_reports():
    # TODO: 实现学习报告功能
    return "学习报告功能开发中..."

# 添加错误处理
@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return render_template('error.html', error=error), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error=error), 404

if __name__ == '__main__':
    # 启用详细的错误日志
    import logging
    logging.basicConfig(level=logging.DEBUG)
    
    # 设置 Werkzeug 日志级别
    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.setLevel(logging.INFO)
    
    app.run(debug=True) 