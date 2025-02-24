-- 首先删除有外键关联的表数据
DELETE FROM word_set_items;
DELETE FROM learning_records;
DELETE FROM words;
DELETE FROM word_sets;

-- 重置自增ID（如果需要）
ALTER SEQUENCE word_sets_id_seq RESTART WITH 1;
ALTER SEQUENCE words_id_seq RESTART WITH 1;
ALTER SEQUENCE word_set_items_id_seq RESTART WITH 1;

-- 插入单词集
INSERT INTO word_sets (name, description, difficulty_level) VALUES
('五年级自然地理单词', '包含山川、地理等自然相关的单词', 3),
('五年级日常生活单词', '日常生活中常用的单词', 3),
('五年级形容词', '常用形容词', 3);

-- 插入地理相关单词
INSERT INTO words (english, chinese, unit_id, difficulty_level) VALUES
('mystery', '奥秘', 1, 3),
('cliff', '悬崖', 1, 3),
('field', '田野', 1, 3),
('island', '岛', 1, 3),
('lake', '湖', 1, 3),
('mountain', '高山', 1, 3),
('hill', '小山', 1, 3),
('river', '河', 1, 3),
('snow', '雪', 1, 3),
('water', '水', 1, 3),
('deep', '深的', 1, 3),
('high', '高的', 1, 3),
('long', '长的', 1, 3),
('wide', '宽的', 1, 3),
('explore', '探险、探索', 1, 3),
('explorer', '探险家、探索者', 1, 3);


-- 插入日常生活单词
INSERT INTO words (english, chinese, unit_id, difficulty_level) VALUES
('breakfast', '早餐', 3, 3),
('classroom', '教室', 3, 3),
('computer', '电脑', 3, 3),
('dictionary', '字典', 3, 3),
('exercise', '运动', 3, 3),
('furniture', '家具', 3, 3),
('hospital', '医院', 3, 3),
('library', '图书馆', 3, 3),
('restaurant', '餐厅', 3, 3),
('telephone', '电话', 3, 3);

-- 插入形容词
INSERT INTO words (english, chinese, unit_id, difficulty_level) VALUES
('beautiful', '美丽的', 4, 3),
('careful', '小心的', 4, 3),
('dangerous', '危险的', 4, 3),
('excited', '兴奋的', 4, 3),
('friendly', '友好的', 4, 3),
('helpful', '有帮助的', 4, 3),
('important', '重要的', 4, 3),
('nervous', '紧张的', 4, 3),
('popular', '受欢迎的', 4, 3),
('successful', '成功的', 4, 3);

-- 关联单词集和单词
WITH word_sets_data AS (
    SELECT id as set_id, name FROM word_sets
)
INSERT INTO word_set_items (word_set_id, word_id)
SELECT 
    word_sets.id,
    words.id
FROM words
JOIN word_sets ON 
    (words.unit_id = 1 AND word_sets.name = '五年级自然地理单词') OR
    (words.unit_id = 3 AND word_sets.name = '五年级日常生活单词') OR
    (words.unit_id = 4 AND word_sets.name = '五年级形容词'); 