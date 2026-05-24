#!/bin/bash

# Script restore database CMMS từ file .bak
# Sử dụng: ./restore_db.sh

echo "Đang kiểm tra container db..."
if [ "$(docker ps -q -f name=cmms_db)" ]; then
    echo "Đang thực hiện restore database CMMS..."
    
    # Lệnh restore SQL
    docker exec -it cmms_db /opt/mssql-tools/bin/sqlcmd \
       -S localhost -U sa -P "cmms@Admin123" \
       -Q "RESTORE DATABASE CMMS FROM DISK = '/var/opt/mssql/backup/CMMS.bak' WITH MOVE 'CMMS' TO '/var/opt/mssql/data/CMMS.mdf', MOVE 'CMMS_log' TO '/var/opt/mssql/data/CMMS_log.ldf', REPLACE"
       
    if [ $? -eq 0 ]; then
        echo "✅ Restore database thành công!"
    else
        echo "❌ Có lỗi xảy ra trong quá trình restore."
    fi
else
    echo "❌ Lỗi: Container 'cmms_db' chưa chạy. Hãy chạy 'docker-compose up -d' trước."
fi
