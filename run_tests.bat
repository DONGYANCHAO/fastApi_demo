@echo off
echo ========================================
echo  FastAPI 项目测试执行脚本
echo ========================================

echo.
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

echo.
echo [2/4] 安装测试依赖...
pip install pytest pytest-cov httpx -q >nul 2>&1

echo.
echo [3/4] 运行所有测试并生成覆盖率报告...
pytest

echo.
echo [4/4] 生成测试摘要报告...
python generate_report.py

echo.
echo ========================================
echo  测试完成！
echo ========================================
echo.
echo  覆盖率报告: htmlcov/index.html
echo  XML报告: coverage.xml, pytest-report.xml
echo  测试摘要: TEST_REPORT.md
echo.
pause
