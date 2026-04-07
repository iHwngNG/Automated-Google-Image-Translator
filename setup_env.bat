@echo off
IF NOT EXIST .env (
    copy .env.example .env
    echo Thanh cong! Da tao file .env nguyen mau tu .env.example
) ELSE (
    echo File .env da ton tai san tren may roi!
)
pause
