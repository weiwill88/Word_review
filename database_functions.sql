-- 获取需要关注的学生
-- 标准：
-- 1. 7天内未登录
-- 2. 正确率低于60%
-- 3. 学习进度落后（完成度低于平均值的50%）
CREATE OR REPLACE FUNCTION get_attention_needed_students(teacher_class_id VARCHAR)
RETURNS TABLE (
    student_id BIGINT,
    name VARCHAR,
    status TEXT,
    last_active TIMESTAMP,
    accuracy NUMERIC,
    progress NUMERIC
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH student_stats AS (
        -- 计算每个学生的统计数据
        SELECT 
            u.id,
            u.username as name,
            MAX(lr.created_at) as last_active,
            COALESCE(
                (SUM(CASE WHEN lr.error_count = 0 THEN 1 ELSE 0 END)::FLOAT / 
                NULLIF(COUNT(*), 0) * 100),
                0
            ) as accuracy,
            COALESCE(
                (COUNT(DISTINCT ws.word_id)::FLOAT / 
                (SELECT COUNT(*) FROM words) * 100),
                0
            ) as progress
        FROM users u
        LEFT JOIN learning_records lr ON u.id = lr.user_id
        LEFT JOIN word_set_items ws ON lr.word_set_id = ws.word_set_id
        WHERE u.class_id = teacher_class_id
        AND u.role = 'student'
        GROUP BY u.id, u.username
    )
    SELECT 
        ss.id,
        ss.name,
        CASE 
            WHEN ss.last_active < NOW() - INTERVAL '7 days' THEN '7天未活跃'
            WHEN ss.accuracy < 60 THEN '正确率过低'
            WHEN ss.progress < (SELECT AVG(progress) * 0.5 FROM student_stats) THEN '进度落后'
        END as status,
        ss.last_active,
        ss.accuracy,
        ss.progress
    FROM student_stats ss
    WHERE 
        ss.last_active < NOW() - INTERVAL '7 days'
        OR ss.accuracy < 60
        OR ss.progress < (SELECT AVG(progress) * 0.5 FROM student_stats);
END;
$$;

-- 获取常见错误单词
-- 返回错误次数最多的前10个单词
CREATE OR REPLACE FUNCTION get_common_error_words(teacher_class_id VARCHAR)
RETURNS TABLE (
    word_id BIGINT,
    english VARCHAR,
    chinese VARCHAR,
    count BIGINT
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT 
        w.id as word_id,
        w.english,
        w.chinese,
        COUNT(er.id) as count
    FROM words w
    JOIN error_records er ON w.id = er.word_id
    JOIN users u ON er.user_id = u.id
    WHERE u.class_id = teacher_class_id
    GROUP BY w.id, w.english, w.chinese
    ORDER BY count DESC
    LIMIT 10;
END;
$$;

-- 获取学生连续打卡天数
CREATE OR REPLACE FUNCTION get_streak_days(student_id BIGINT)
RETURNS INTEGER LANGUAGE plpgsql AS $$
DECLARE
    streak INTEGER := 0;
    check_date DATE := CURRENT_DATE;
    last_active_date DATE;
BEGIN
    -- 从最近的一天开始往前查找连续学习的天数
    SELECT DATE(created_at) INTO last_active_date
    FROM learning_records
    WHERE user_id = student_id
    ORDER BY created_at DESC
    LIMIT 1;

    -- 如果今天没有学习，从昨天开始计算
    IF last_active_date < check_date THEN
        check_date := check_date - INTERVAL '1 day';
    END IF;

    WHILE EXISTS (
        SELECT 1
        FROM learning_records
        WHERE user_id = student_id
        AND DATE(created_at) = check_date
    ) LOOP
        streak := streak + 1;
        check_date := check_date - INTERVAL '1 day';
    END LOOP;

    RETURN streak;
END;
$$;

-- 获取学生正确率
CREATE OR REPLACE FUNCTION get_student_accuracy(
    student_id BIGINT,
    start_date TIMESTAMP
) RETURNS NUMERIC LANGUAGE plpgsql AS $$
DECLARE
    total_attempts INTEGER;
    correct_attempts INTEGER;
BEGIN
    -- 获取总尝试次数和正确次数
    SELECT 
        COUNT(*),
        SUM(CASE WHEN error_count = 0 THEN 1 ELSE 0 END)
    INTO total_attempts, correct_attempts
    FROM learning_records
    WHERE user_id = student_id
    AND created_at >= start_date;

    -- 计算正确率
    IF total_attempts = 0 THEN
        RETURN 0;
    ELSE
        RETURN (correct_attempts::NUMERIC / total_attempts * 100);
    END IF;
END;
$$;

-- 获取用户当前进度
CREATE OR REPLACE FUNCTION get_user_progress(user_id BIGINT)
RETURNS TABLE (
    current_level INTEGER,
    total_words INTEGER,
    completed_words INTEGER,
    accuracy NUMERIC
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    WITH user_stats AS (
        SELECT 
            COALESCE(
                CEIL(AVG(ws.difficulty_level))::INTEGER,
                1
            ) as avg_difficulty,
            COUNT(DISTINCT wsi.word_id) as total_completed,
            COALESCE(
                (SUM(CASE WHEN lr.error_count = 0 THEN 1 ELSE 0 END)::FLOAT / 
                NULLIF(COUNT(*), 0) * 100),
                0
            ) as avg_accuracy
        FROM learning_records lr
        JOIN word_sets ws ON lr.word_set_id = ws.id
        JOIN word_set_items wsi ON ws.id = wsi.word_set_id
        WHERE lr.user_id = user_id
    )
    SELECT 
        CASE 
            WHEN us.avg_accuracy >= 80 AND us.avg_difficulty < 5 THEN us.avg_difficulty + 1
            WHEN us.avg_accuracy < 60 AND us.avg_difficulty > 1 THEN us.avg_difficulty - 1
            ELSE COALESCE(us.avg_difficulty, 1)
        END as current_level,
        (SELECT COUNT(*) FROM words) as total_words,
        COALESCE(us.total_completed, 0) as completed_words,
        COALESCE(us.avg_accuracy, 0) as accuracy
    FROM user_stats us;
END;
$$;

-- 获取用户需要复习的错误单词
CREATE OR REPLACE FUNCTION get_user_error_words(
    user_id BIGINT,
    limit_count INTEGER DEFAULT 10
)
RETURNS TABLE (
    word_id BIGINT,
    english VARCHAR,
    chinese VARCHAR,
    error_count INTEGER,
    last_error_time TIMESTAMP
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT 
        w.id as word_id,
        w.english,
        w.chinese,
        er.error_count,
        er.created_at as last_error_time
    FROM error_records er
    JOIN words w ON er.word_id = w.id
    WHERE er.user_id = user_id
    ORDER BY er.error_count DESC, er.created_at DESC
    LIMIT limit_count;
END;
$$; 