#!/bin/bash
# deploy_database.sh

# 載入 .env 檔案
if [ -f "../.env" ]; then
    export $(grep -v '^#' ../.env | xargs)
else
    echo ".env 檔案不存在，請確認路徑正確"
    exit 1
fi

# 測試 MySQL 連線
echo "正在測試資料庫連線..."
mysqladmin ping -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASS
if [ $? -ne 0 ]; then
    echo "無法連線到資料庫，請檢查連線資訊！"
    exit 1
fi
echo "資料庫連線成功！"

# 部署資料庫結構
echo "正在部署資料庫結構..."
mysql -h $DB_HOST -P $DB_PORT -u $DB_USER -p$DB_PASS --verbose < ./schema.sql
echo "資料庫結構部署完成！"