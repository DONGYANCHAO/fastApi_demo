#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试执行脚本

功能：
- 运行所有测试
- 运行指定模块测试
- 带覆盖率运行
- 生成测试报告

用法：
    python run_tests.py                    # 运行所有测试
    python run_tests.py --coverage         # 带覆盖率运行
    python run_tests.py --html             # 生成 HTML 覆盖率报告
    python run_tests.py --module auth      # 只运行认证模块测试
    python run_tests.py --verbose          # 详细输出
"""
import argparse
import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path


def run_command(cmd, description):
    """执行命令并打印结果"""
    print(f"\n{'='*60}")
    print(f"执行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=False)
    return result.returncode


def run_tests(args):
    """运行测试"""
    # 基础命令
    cmd = [sys.executable, "-m", "pytest"]
    
    # 详细输出
    if args.verbose:
        cmd.append("-v")
    
    # 指定模块
    if args.module:
        if args.module == "auth":
            cmd.append("tests/test_auth.py")
        elif args.module == "crud":
            cmd.append("tests/test_crud_users.py")
        elif args.module == "router":
            cmd.append("tests/test_routers_users.py")
        else:
            print(f"未知模块: {args.module}")
            print("可用模块: auth, crud, router")
            return 1
    else:
        cmd.append("tests/")
    
    # 覆盖率
    if args.coverage or args.html:
        cmd.extend(["--cov=sql_app", "--cov=routers", "--cov=main"])
        cmd.append("--cov-report=term-missing")
        
        if args.html:
            cmd.append("--cov-report=html")
        
        if args.xml:
            cmd.append("--cov-report=xml")
    
    # 标记过滤
    if args.mark:
        cmd.extend(["-m", args.mark])
    
    # 失败即停止
    if args.failfast:
        cmd.append("-x")
    
    # 执行
    return run_command(cmd, "运行测试")


def generate_report():
    """生成测试报告"""
    print(f"\n{'='*60}")
    print("生成测试报告")
    print('='*60)
    
    # 运行测试并生成 JUnit XML 报告
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--junitxml=test-results.xml",
        "--tb=short"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # 解析结果
    output = result.stdout + result.stderr
    
    # 统计测试数量
    passed = output.count(" PASSED")
    failed = output.count(" FAILED")
    error = output.count(" ERROR")
    skipped = output.count(" SKIPPED")
    
    total = passed + failed + error + skipped
    
    # 生成报告
    report = f"""# 测试执行报告

## 执行时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 测试统计

| 状态 | 数量 |
|------|------|
| 通过 | {passed} |
| 失败 | {failed} |
| 错误 | {error} |
| 跳过 | {skipped} |
| **总计** | **{total}** |

## 通过率
{passed}/{total} ({(passed/max(total, 1)*100):.2f}%)

## 详细输出

```
{output[-2000:]}
```

"""
    
    # 保存报告
    report_file = Path("test_report.md")
    report_file.write_text(report, encoding="utf-8")
    print(f"报告已保存到: {report_file.absolute()}")
    
    return result.returncode


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="FastAPI 项目测试执行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python run_tests.py                    # 运行所有测试
  python run_tests.py --coverage         # 带覆盖率运行
  python run_tests.py --html             # 生成 HTML 覆盖率报告
  python run_tests.py --module auth      # 只运行认证模块
  python run_tests.py --verbose          # 详细输出
  python run_tests.py --report           # 生成测试报告
        """
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="启用覆盖率统计"
    )
    
    parser.add_argument(
        "--html",
        action="store_true",
        help="生成 HTML 覆盖率报告"
    )
    
    parser.add_argument(
        "--xml",
        action="store_true",
        help="生成 XML 覆盖率报告"
    )
    
    parser.add_argument(
        "--module", "-m",
        choices=["auth", "crud", "router"],
        help="指定测试模块 (auth, crud, router)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    parser.add_argument(
        "--mark",
        help="按标记过滤测试 (如: -m 'not slow')"
    )
    
    parser.add_argument(
        "--failfast", "-x",
        action="store_true",
        help="失败即停止"
    )
    
    parser.add_argument(
        "--report", "-r",
        action="store_true",
        help="生成测试报告"
    )
    
    args = parser.parse_args()
    
    # 检查是否在正确目录
    if not Path("tests").exists():
        print("错误: 未找到 tests 目录，请在项目根目录运行此脚本")
        return 1
    
    # 执行测试
    if args.report:
        return generate_report()
    else:
        return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())
