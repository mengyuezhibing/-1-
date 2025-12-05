@echo off
where python > python_path.txt
python --version > python_version.txt 2>&1
echo 尝试运行Python...
python app.py > output.log 2>&1
echo 退出代码: %ERRORLEVEL%