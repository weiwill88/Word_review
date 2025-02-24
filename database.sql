-- 首先删除所有现有表（注意删除顺序，先删除有外键依赖的表）
DROP TABLE IF EXISTS word_set_items CASCADE;
DROP TABLE IF EXISTS error_records CASCADE;
DROP TABLE IF EXISTS learning_records CASCADE;
DROP TABLE IF EXISTS word_sets CASCADE;
DROP TABLE IF EXISTS words CASCADE;
DROP TABLE IF EXISTS classes CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 创建用户表
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,  -- 用户真实姓名
    role VARCHAR(50) NOT NULL DEFAULT 'student',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建单词表
CREATE TABLE words (
    id BIGSERIAL PRIMARY KEY,
    english VARCHAR(255) NOT NULL,
    chinese VARCHAR(255) NOT NULL,
    unit_id INTEGER NOT NULL,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建单词集表
CREATE TABLE word_sets (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建单词集-单词关联表
CREATE TABLE word_set_items (
    id BIGSERIAL PRIMARY KEY,
    word_set_id BIGINT REFERENCES word_sets(id),
    word_id BIGINT REFERENCES words(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 创建学习记录表
CREATE TABLE learning_records (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id),
    word_set_id BIGINT REFERENCES word_sets(id),
    total_words INTEGER NOT NULL,
    error_count INTEGER NOT NULL DEFAULT 0,
    completion_time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    time_spent INTEGER NOT NULL  -- 以秒为单位
);

-- 创建用于教师查看的视图
CREATE VIEW student_progress AS
SELECT 
    u.username,
    COUNT(DISTINCT lr.word_set_id) as completed_sets,
    SUM(lr.total_words) as total_words_practiced,
    SUM(lr.error_count) as total_errors,
    CASE 
        WHEN SUM(lr.total_words) = 0 THEN 0
        ELSE ROUND(CAST(SUM(lr.error_count) * 100.0 / SUM(lr.total_words) AS NUMERIC), 2)
    END as error_rate,
    MAX(lr.completion_time) as last_practice_time
FROM users u
LEFT JOIN learning_records lr ON u.id = lr.user_id
WHERE u.role = 'student'
GROUP BY u.id, u.username; 