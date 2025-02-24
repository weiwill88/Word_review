from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from supabase import create_client, Client
from dotenv import load_dotenv
import os
import random
import logging

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

app = Flask(__name__, 
    template_folder='templates',
    static_folder='static',
    static_url_path='/static'
)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# 添加自定义过滤器
def shuffle_filter(seq):
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except:
        return seq

app.jinja_env.filters['shuffle'] = shuffle_filter

# 初始化Supabase客户端
try:
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase配置缺失")
    
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("Supabase客户端初始化成功")
except Exception as e:
    logger.error(f"Supabase客户端初始化失败: {str(e)}")
    raise

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, user_data):
        self.id = user_data['id']
        self.username = user_data['username']  # 用户真实姓名
        self.role = user_data.get('role', 'student')  # 默认为学生

@login_manager.user_loader
def load_user(user_id):
    try:
        # 处理教师特殊ID
        if user_id == '0':
            return User({
                'id': '0',
                'username': '我是老师',
                'role': 'teacher'
            })
        
        user_data = supabase.table('users').select('*').eq('id', user_id).execute()
        if user_data.data:
            return User(user_data.data[0])
    except Exception as e:
        logger.error(f"Error loading user: {e}")
    return None

@app.route('/')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        
        try:
            # 隐藏的教师登录入口
            if username == "我是老师":
                user = User({
                    'id': '0',
                    'username': '我是老师',
                    'role': 'teacher'
                })
                login_user(user)
                return redirect(url_for('word_matching'))
            
            # 查询学生用户
            user_data = supabase.table('users').select('*').eq('username', username).execute()
            
            if user_data.data:
                user = User(user_data.data[0])
                login_user(user)
                return redirect(url_for('word_matching'))
            else:
                flash('姓名不存在，请先注册')
        except Exception as e:
            flash(f'登录失败: {str(e)}')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')  # 获取用户输入的真实姓名
        
        try:
            # 防止注册特殊用户名
            if username == "我是老师":
                flash('该姓名不能使用')
                return render_template('register.html')
            
            # 检查用户名是否已存在
            existing_user = supabase.table('users').select('*').eq('username', username).execute()
            if existing_user.data:
                flash('该姓名已被注册')
                return render_template('register.html')
            
            # 创建新用户，默认为学生角色
            new_user = {
                'username': username,
                'role': 'student'
            }
            
            result = supabase.table('users').insert(new_user).execute()
            if result.data:
                # 自动登录新用户
                user = User(result.data[0])
                login_user(user)
                return redirect(url_for('word_matching'))
            else:
                flash('注册失败，请重试')
            
        except Exception as e:
            flash(f'注册失败: {str(e)}')
    
    return render_template('register.html')

@app.route('/word_matching')
@login_required
def word_matching():
    try:
        logger.info(f"用户 {current_user.id} 访问单词配对页面")
        
        # 获取所有单词集
        word_sets = supabase.table('word_sets').select('*').execute()
        
        if not word_sets.data:
            logger.warning("未找到任何单词集")
            flash('没有找到单词集')
            return redirect(url_for('login'))
        
        # 随机选择一个单词集
        word_set = random.choice(word_sets.data)
        logger.debug(f"选择的单词集: {word_set}")
        
        # 获取单词集中的单词
        word_items = supabase.table('word_set_items')\
            .select('word_id')\
            .eq('word_set_id', word_set['id'])\
            .execute()
        
        if not word_items.data:
            logger.warning(f"单词集 {word_set['id']} 中没有单词")
            flash('单词集中没有单词')
            return redirect(url_for('login'))
        
        # 获取单词详细信息
        word_ids = [item['word_id'] for item in word_items.data]
        words = supabase.table('words')\
            .select('*')\
            .in_('id', word_ids)\
            .execute()
        
        if not words.data:
            logger.warning(f"未找到单词集中的单词信息")
            flash('无法加载单词信息')
            return redirect(url_for('login'))
        
        # 准备单词数据
        word_pairs = []
        for word in words.data:
            word_pairs.append({
                'id': word['id'],
                'english': word['english'],
                'chinese': word['chinese']
            })
        
        # 随机打乱单词顺序
        random.shuffle(word_pairs)
        
        logger.info(f"成功加载 {len(word_pairs)} 个单词")
        return render_template('word_matching.html', 
                            word_set=word_set,
                            word_pairs=word_pairs)
    except Exception as e:
        logger.error(f"加载单词失败: {str(e)}", exc_info=True)
        flash(f'加载单词失败: {str(e)}')
        return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/save_learning_record', methods=['POST'])
def save_learning_record():
    if not current_user.is_authenticated:
        return jsonify({'error': '未登录'}), 401
    
    try:
        data = request.get_json()
        record = {
            'user_id': current_user.id,
            'word_set_id': data['word_set_id'],
            'total_words': data['total_words'],
            'error_count': data['error_count'],
            'time_spent': data['time_spent']
        }
        
        result = supabase.table('learning_records').insert(record).execute()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"保存学习记录失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/teacher_dashboard')
@login_required
def teacher_dashboard():
    if current_user.role != 'teacher':
        flash('权限不足')
        return redirect(url_for('word_matching'))
    
    try:
        # 获取学生进度数据
        progress = supabase.table('student_progress').select('*').execute()
        return render_template('teacher_dashboard.html', progress=progress.data)
    except Exception as e:
        logger.error(f"获取学生进度失败: {str(e)}")
        flash('获取数据失败')
        return redirect(url_for('word_matching'))

if __name__ == '__main__':
    app.run(debug=True) 