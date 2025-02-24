-- 删除所有现有函数
DROP FUNCTION IF EXISTS get_attention_needed_students(VARCHAR);
DROP FUNCTION IF EXISTS get_common_error_words(VARCHAR);
DROP FUNCTION IF EXISTS get_streak_days(BIGINT);
DROP FUNCTION IF EXISTS get_student_accuracy(BIGINT, TIMESTAMP);
DROP FUNCTION IF EXISTS get_user_progress(BIGINT);
DROP FUNCTION IF EXISTS get_user_error_words(BIGINT, INTEGER); 