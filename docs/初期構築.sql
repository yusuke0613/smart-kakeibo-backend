-- サンプルデータの挿入
INSERT INTO kakeibo.user_levels (level_name, required_points)
VALUES
    ('ビギナー', 0),
    ('レギュラー', 100),
    ('シルバー', 300),
    ('ゴールド', 600),
    ('プラチナ', 1000),
    ('ダイヤモンド', 1500),
    ('マスター', 2500),
    ('グランドマスター', 4000),
    ('レジェンド', 6000),
    ('ファイナンシャルエキスパート', 10000);



INSERT INTO major_categories (user_id, name, type, is_fixed) VALUES
(1, '住居費', 'EXPENSE', FALSE),
(1, '光熱費', 'EXPENSE', FALSE),
(1, '通信費', 'EXPENSE', FALSE),
(1, '食費', 'EXPENSE', FALSE),
(1, '日用品', 'EXPENSE', FALSE),
(1, '交通費', 'EXPENSE', FALSE),
(1, '保険', 'EXPENSE', FALSE),
(1, '医療・美容', 'EXPENSE', FALSE),
(1, '教育費', 'EXPENSE', FALSE),
(1, '娯楽・趣味', 'EXPENSE', FALSE),
(1, '交際費', 'EXPENSE', FALSE),
(1, 'サブスク', 'EXPENSE', FALSE),
(1, 'その他(雑費)', 'EXPENSE', FALSE);

-- 小カテゴリ (支出)
INSERT INTO minor_categories (major_category_id, user_id, name) VALUES
((SELECT major_category_id FROM major_categories WHERE name = '住居費' AND user_id = 1), 1, '家賃／住宅ローン'),
((SELECT major_category_id FROM major_categories WHERE name = '住居費' AND user_id = 1), 1, '管理費・修繕積立金'),
((SELECT major_category_id FROM major_categories WHERE name = '住居費' AND user_id = 1), 1, '住宅修繕・リフォーム'),
((SELECT major_category_id FROM major_categories WHERE name = '光熱費' AND user_id = 1), 1, '電気代'),
((SELECT major_category_id FROM major_categories WHERE name = '光熱費' AND user_id = 1), 1, 'ガス代'),
((SELECT major_category_id FROM major_categories WHERE name = '光熱費' AND user_id = 1), 1, '水道代'),
((SELECT major_category_id FROM major_categories WHERE name = '通信費' AND user_id = 1), 1, 'インターネット(光回線など)'),
((SELECT major_category_id FROM major_categories WHERE name = '通信費' AND user_id = 1), 1, '携帯電話料金'),
((SELECT major_category_id FROM major_categories WHERE name = '通信費' AND user_id = 1), 1, 'サーバ代・プロバイダ料金'),
((SELECT major_category_id FROM major_categories WHERE name = '食費' AND user_id = 1), 1, '食材（スーパー・コンビニ等）'),
((SELECT major_category_id FROM major_categories WHERE name = '食費' AND user_id = 1), 1, '外食（レストラン・カフェ等）'),
((SELECT major_category_id FROM major_categories WHERE name = '日用品' AND user_id = 1), 1, '消耗品（洗剤・トイレットペーパー等）'),
((SELECT major_category_id FROM major_categories WHERE name = '日用品' AND user_id = 1), 1, '雑貨・掃除用品'),
((SELECT major_category_id FROM major_categories WHERE name = '交通費' AND user_id = 1), 1, '定期券'),
((SELECT major_category_id FROM major_categories WHERE name = '交通費' AND user_id = 1), 1, 'ガソリン代・駐車場代'),
((SELECT major_category_id FROM major_categories WHERE name = '交通費' AND user_id = 1), 1, 'タクシー・バス代'),
((SELECT major_category_id FROM major_categories WHERE name = '保険' AND user_id = 1), 1, '生命保険・医療保険'),
((SELECT major_category_id FROM major_categories WHERE name = '保険' AND user_id = 1), 1, '自動車保険'),
((SELECT major_category_id FROM major_categories WHERE name = '医療・美容' AND user_id = 1), 1, '病院・薬代'),
((SELECT major_category_id FROM major_categories WHERE name = '医療・美容' AND user_id = 1), 1, '理容・美容院'),
((SELECT major_category_id FROM major_categories WHERE name = '教育費' AND user_id = 1), 1, '学費・塾・習い事'),
((SELECT major_category_id FROM major_categories WHERE name = '教育費' AND user_id = 1), 1, '教材・参考書・文具'),
((SELECT major_category_id FROM major_categories WHERE name = '娯楽・趣味' AND user_id = 1), 1, '趣味・レジャー関連'),
((SELECT major_category_id FROM major_categories WHERE name = '娯楽・趣味' AND user_id = 1), 1, '書籍・雑誌'),
((SELECT major_category_id FROM major_categories WHERE name = '娯楽・趣味' AND user_id = 1), 1, 'スポーツ・ジム'),
((SELECT major_category_id FROM major_categories WHERE name = '交際費' AND user_id = 1), 1, '飲み会・交際費'),
((SELECT major_category_id FROM major_categories WHERE name = '交際費' AND user_id = 1), 1, '冠婚葬祭'),
((SELECT major_category_id FROM major_categories WHERE name = 'サブスク' AND user_id = 1), 1, '動画配信サービス（Netflix等）'),
((SELECT major_category_id FROM major_categories WHERE name = 'サブスク' AND user_id = 1), 1, '音楽配信サービス（Spotify等）'),
((SELECT major_category_id FROM major_categories WHERE name = 'その他(雑費)' AND user_id = 1), 1, 'ペット関連費用'),
((SELECT major_category_id FROM major_categories WHERE name = 'その他(雑費)' AND user_id = 1), 1, 'ギフト・プレゼント'),
((SELECT major_category_id FROM major_categories WHERE name = 'その他(雑費)' AND user_id = 1), 1, '未分類 (一時的)');

-- 大カテゴリ (収入)
INSERT INTO major_categories (user_id, name, type, is_fixed) VALUES
(1, '給与所得', 'INCOME', FALSE),
(1, '事業／副業', 'INCOME', FALSE),
(1, '投資収入', 'INCOME', FALSE),
(1, '公的給付', 'INCOME', FALSE),
(1, 'その他収入', 'INCOME', FALSE);


-- 小カテゴリ (収入)
INSERT INTO minor_categories (major_category_id, user_id, name) VALUES
((SELECT major_category_id FROM major_categories WHERE name = '給与所得' AND user_id = 1), 1, '基本給'),
((SELECT major_category_id FROM major_categories WHERE name = '給与所得' AND user_id = 1), 1, '残業代／手当'),
((SELECT major_category_id FROM major_categories WHERE name = '給与所得' AND user_id = 1), 1, 'ボーナス'),
((SELECT major_category_id FROM major_categories WHERE name = '事業／副業' AND user_id = 1), 1, '副業収入（フリーランス他）'),
((SELECT major_category_id FROM major_categories WHERE name = '投資収入' AND user_id = 1), 1, '配当金／株式売買益'),
((SELECT major_category_id FROM major_categories WHERE name = '投資収入' AND user_id = 1), 1, '仮想通貨・FX益'),
((SELECT major_category_id FROM major_categories WHERE name = '公的給付' AND user_id = 1), 1, '児童手当'),
((SELECT major_category_id FROM major_categories WHERE name = '公的給付' AND user_id = 1), 1, '年金'),
((SELECT major_category_id FROM major_categories WHERE name = 'その他収入' AND user_id = 1), 1, 'お祝い金・お小遣い'),
((SELECT major_category_id FROM major_categories WHERE name = 'その他収入' AND user_id = 1), 1, '不用品販売');



-- 2024年10月から2025年2月までの日付を生成するための関数 (PostgreSQL固有)
CREATE OR REPLACE FUNCTION generate_date_series(start_date DATE, end_date DATE)
RETURNS SETOF DATE AS $$
BEGIN
  RETURN QUERY SELECT generate_series(start_date, end_date, '1 day'::interval)::date;
END;
$$ LANGUAGE plpgsql;

-- ダミーデータの挿入
INSERT INTO transactions (user_id, major_category_id, minor_category_id, amount, transaction_date, description, created_at, updated_at)
SELECT
    1,  -- user_id (固定で1)
    CASE
        WHEN random() < 0.2 THEN 1  -- 20%の確率でmajor_category_id = 1
        WHEN random() < 0.4 THEN 2  -- 20%の確率でmajor_category_id = 2
        WHEN random() < 0.6 THEN 3  -- 20%の確率でmajor_category_id = 3
        WHEN random() < 0.8 THEN 4  -- 20%の確率でmajor_category_id = 4
        ELSE 5                      -- 残りはmajor_category_id = 5
    END,
    CASE
        WHEN random() < 0.33 THEN 1
        WHEN random() < 0.66 THEN 2
        ELSE 3
    END, -- ランダムなminor_category_id (1, 2, 3 のいずれか)　画像にあるminor_category_idを利用する場合は画像のテーブルからランダムに抽出するように修正
    ROUND(random() * 10000),  -- ランダムな金額 (0から10000の間)
    dates.dt,  -- ランダムな日付 (2024年10月から2025年2月)
    'ダミー取引', -- description (固定)
    NOW(),  -- created_at (現在時刻)
    NOW()   -- updated_at (現在時刻)
FROM generate_date_series('2024-10-01', '2025-02-28') AS dates(dt);