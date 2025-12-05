@echo off
setlocal enabledelayedexpansion

echo 开始测试Python环境...
echo 当前目录: %cd%
echo.

rem 检查Python是否在PATH中
where python > python_path.txt 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Python路径检测成功:
    type python_path.txt
) else (
    echo 错误: 无法在PATH中找到Python
    echo 错误代码: %ERRORLEVEL%
)
echo.

rem 尝试执行简单的Python命令
python -c "print('Hello from Python'); print('Python版本:', __import__('sys').version)" > python_output.txt 2> python_error.txt

echo Python执行结果:
if exist python_output.txt (
    type python_output.txt
) else (
    echo 没有输出文件
)

echo.
echo Python错误信息:
if exist python_error.txt (
    type python_error.txt
) else (
    echo 没有错误信息
)

echo.
echo 批处理执行完成，退出代码: %ERRORLEVEL%
