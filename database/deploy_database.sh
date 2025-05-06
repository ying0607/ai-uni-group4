#!/bin/bash
# deploy_database.sh

# 資料庫連線資訊
DB_HOST="125.228.146.37"
DB_PORT="3306"
DB_USER="root"
DB_PASS="aiuniversity"
DB_NAME="113_2"

# 部署結構 (使用 schema.sql)
echo "部署資料庫結構..."
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p $DB_PASS < database/schema.sql

# 執行遷移 (如果使用遷移工具)
echo "執行資料庫遷移..."
# 這裡可以加入遷移命令，如 alembic upgrade head

# 載入種子資料 (可選，依據環境決定)
if [ "$1" == "with-seeds" ]; then
    echo "載入種子資料..."
    for seed_file in database/seeds/*.sql; do
        echo "載入: $seed_file"
        mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASS $DB_NAME < $seed_file
    done
fi

echo "資料庫部署完成"