# 小学英语单词学习系统

## 项目简介
这是一个面向小学生的英语单词学习系统，旨在帮助学生进行课后单词复习。系统采用游戏化的方式，通过单词配对练习来提高学习兴趣和效果。

## 项目结构
```
English_learning/
├── src/                      # 源代码目录
│   ├── templates/            # HTML模板文件
│   │   ├── base.html        # 基础模板
│   │   ├── index.html       # 首页
│   │   ├── login.html       # 登录页
│   │   ├── register.html    # 注册页
│   │   ├── dashboard.html   # 仪表板
│   │   ├── word_matching.html # 单词配对页面
│   │   └── word_review.html  # 错词复习页面
│   ├── static/              # 静态资源
│   │   ├── css/            # CSS文件
│   │   └── js/             # JavaScript文件
│   └── app.py              # 主应用程序
├── database.sql            # 数据库结构
├── requirements.txt        # 项目依赖
├── .env                    # 环境变量配置
├── .gitignore             # Git忽略文件
├── vercel.json            # Vercel部署配置
└── README.md              # 项目说明文档
```

## 技术栈
- 后端：Python Flask
- 数据库：Supabase (PostgreSQL)
- 前端：HTML/CSS/JavaScript
- 认证：Flask-Login
- 部署：Vercel

## 本地开发环境搭建

### 1. 环境准备
- Python 3.8+
- pip (Python包管理器)
- Git

### 2. 克隆项目
```bash
git clone <your-repository-url>
cd English_learning
```

### 3. 创建虚拟环境
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 4. 安装依赖
```bash
pip install -r requirements.txt
```

### 5. 环境变量配置
创建 `.env` 文件并配置以下环境变量：
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
FLASK_SECRET_KEY=your_secret_key
```

### 6. 运行项目
```bash
python src/app.py
```
访问 http://localhost:5000 即可看到项目运行效果。

## Supabase数据库配置

### 1. 创建Supabase项目
1. 访问 [Supabase](https://supabase.com) 并登录
2. 创建新项目
3. 获取项目URL和anon key（用于.env配置）

### 2. 创建数据库表
在Supabase的SQL编辑器中执行 `database.sql` 中的建表语句：

1. 用户表 (users)
```sql
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('student', 'teacher')),
    class_id VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

2. 单词表 (words)
```sql
CREATE TABLE words (
    id BIGSERIAL PRIMARY KEY,
    english VARCHAR(255) NOT NULL,
    chinese VARCHAR(255) NOT NULL,
    unit_id INTEGER NOT NULL,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

3. 学习记录表 (learning_records)
```sql
CREATE TABLE learning_records (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    word_set_id INTEGER NOT NULL,
    completion_time TIMESTAMP WITH TIME ZONE,
    error_count INTEGER DEFAULT 0,
    time_spent INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

4. 错误记录表 (error_records)
```sql
CREATE TABLE error_records (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    word_id BIGINT REFERENCES words(id),
    error_count INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 3. 创建存储过程
在Supabase的SQL编辑器中执行 `database_functions.sql` 中的所有函数定义。

## Vercel部署步骤

### 1. 准备工作
1. 确保项目已推送到GitHub
2. 在Vercel上注册账号并连接GitHub

### 2. 部署配置
1. 在Vercel中导入GitHub项目
2. 配置环境变量（与.env文件相同）:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `FLASK_SECRET_KEY`
3. 确保项目根目录包含 `vercel.json`:
```json
{
    "version": 2,
    "builds": [
        {
            "src": "src/app.py",
            "use": "@vercel/python"
        }
    ],
    "routes": [
        {
            "src": "/(.*)",
            "dest": "src/app.py"
        }
    ]
}
```

### 3. 部署注意事项
- Vercel支持Python后端应用部署，但有一些限制：
  - 单个函数执行时间不能超过10秒
  - 需要使用无状态设计
  - 文件系统是只读的
- Supabase作为数据库服务是完全兼容的
- 建议在部署前先在本地完成充分测试

## 功能特点

### 学生端功能
1. **用户系统**
   - 登录/注册功能
   - 个人学习数据统计
   - 学习进度追踪

2. **单词学习模块**
   - 单词配对练习
   - 实时错误提示
   - 学习时间统计
   - 练习完成度展示
   - 错误单词复习功能

3. **个人中心**
   - 学习历史记录
   - 错误单词本
   - 学习进度展示
   - 个人成绩统计

### 教师端功能
1. **数据监控中心**
   - 班级整体学习情况统计
   - 单个学生学习进度追踪
   - 高频错误单词分析
   - 学生参与度统计

2. **单词管理**
   - 单词库管理
   - 课程单元划分
   - 难度等级设置

3. **报告生成**
   - 学生学习报告
   - 班级整体报告
   - 错误词汇分析报告

## 技术架构

### 前端技术
- HTML5/CSS3/JavaScript
- iOS风格UI设计
- 响应式布局
- 动画效果优化

### 后端技术
- Python
- Supabase (数据库和认证)
- RESTful API

### 数据库设计
1. **用户表** (users)
   - user_id
   - username
   - password_hash
   - role (student/teacher)
   - class_id
   - created_at

2. **学习记录表** (learning_records)
   - record_id
   - user_id
   - word_set_id
   - completion_time
   - error_count
   - time_spent
   - created_at

3. **错误记录表** (error_records)
   - error_id
   - user_id
   - word_id
   - error_count
   - created_at

4. **单词表** (words)
   - word_id
   - english
   - chinese
   - unit_id
   - difficulty_level

## 界面设计
- 简约现代的iOS风格
- 适合儿童的色彩搭配
- 清晰的视觉层次
- 友好的操作反馈
- 生动的动画效果

## 开发计划

### 第一阶段：基础功能实现
1. 用户系统搭建
2. 基础单词配对功能
3. 数据库结构设计

### 第二阶段：教师端开发
1. 教师管理界面
2. 数据统计功能
3. 报告生成系统

### 第三阶段：功能优化
1. UI/UX改进
2. 性能优化
3. 单词库扩充

### 第四阶段：测试与部署
1. 功能测试
2. 性能测试
3. 系统部署

## 安装与使用
（待开发完成后补充）

## 贡献指南
1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证
MIT License 