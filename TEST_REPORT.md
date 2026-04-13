# 测试报告

## 测试摘要

| 项目 | 数值 |
|------|------|
| 测试时间 | 2026-04-13 12:17:38 |
| 总测试用例数 | 90 |
| ✅ 通过 | 90 |
| ❌ 失败 | 0 |
| ⚠️ 错误 | 0 |
| ⏭️ 跳过 | 0 |
| 📊 通过率 | 100.00% |
| ⏱️ 执行时间 | 33.12 秒 |
| 📈 代码覆盖率 | 73.02% |
| 📝 覆盖行数 | 295/404 |

## 测试模块覆盖

### 1. CRUD 单元测试 (`test_crud_users.py`)
- 密码哈希与验证
- 用户查询（ID、邮箱、登录）
- 用户列表与分页
- 用户创建、更新、删除
- 密码修改流程

### 2. 用户路由集成测试 (`test_routers_users.py`)
- 用户创建接口
- 用户列表查询（管理员权限）
- 个人信息查询
- ID查询（权限控制）
- 用户删除（权限控制）
- 用户更新（权限控制）
- 密码修改（权限控制）

### 3. 认证模块测试 (`test_auth.py`)
- JWT Token 生成与验证
- 登录接口
- Token 有效性校验（有效/无效/过期）
- 未激活用户拦截
- 角色权限校验
- 请求限流

## 权限测试覆盖

| 场景 | 普通用户 | 管理员 | 未登录 |
|------|---------|--------|--------|
| 创建用户 | ✅ | ✅ | ✅ |
| 查询所有用户 | ❌ 403 | ✅ | ❌ 401 |
| 查询本人信息 | ✅ | ✅ | ❌ 401 |
| 查询他人信息 | ❌ 403 | ✅ | ❌ 401 |
| 删除本人 | ✅ | ✅ | ❌ 401 |
| 删除他人 | ❌ 403 | ✅ | ❌ 401 |
| 更新本人 | ✅ | ✅ | ❌ 401 |
| 更新他人 | ❌ 403 | ✅ | ❌ 401 |
| 修改本人密码 | ✅ | ✅ | ❌ 401 |
| 修改他人密码 | ❌ 403 | ❌ 403 | ❌ 401 |

## HTTP 状态码覆盖

- ✅ **200** - 请求成功
- ✅ **400** - 请求参数错误/用户未激活
- ✅ **401** - 未认证/Token无效
- ✅ **403** - 权限不足
- ✅ **404** - 资源不存在
- ✅ **422** - 请求参数验证失败
- ✅ **429** - 请求限流

## 边界测试覆盖场景

| 测试类别 | 覆盖场景 | 测试状态 |
|---------|---------|---------|
| **用户查询边界** | 负ID查询 (-1) | ✅ 已覆盖 |
| | 不存在用户ID (9999) | ✅ 已覆盖 |
| | 空数据库查询 | ✅ 已覆盖 |
| | skip超过数据总量 | ✅ 已覆盖 |
| | limit = 0 | ✅ 已覆盖 |
| **邮箱边界** | 空邮箱字符串 | ✅ 已覆盖 |
| | 不存在邮箱 | ✅ 已覆盖 |
| | 超长邮箱 (50字符+) | ✅ 已覆盖 |
| | 大小写敏感校验 | ✅ 已覆盖 |
| | 非法格式邮箱 | ✅ 已覆盖 |
| **密码边界** | 空密码 | ✅ 已覆盖 |
| | 错误旧密码 | ✅ 已覆盖 |
| | 超长密码截断处理 | ✅ 已覆盖 |
| | 密码哈希唯一性验证 | ✅ 已覆盖 |
| **权限边界** | 普通用户查询所有用户列表 | ✅ 已覆盖 |
| | 普通用户查询他人信息 | ✅ 已覆盖 |
| | 普通用户修改他人信息 | ✅ 已覆盖 |
| | 普通用户删除他人账号 | ✅ 已覆盖 |
| | 普通用户修改他人密码 | ✅ 已覆盖 |
| **Token边界** | 无效Token格式 | ✅ 已覆盖 |
| | 过期Token | ✅ 已覆盖 |
| | 无subject Token | ✅ 已覆盖 |
| | 用户不存在的Token | ✅ 已覆盖 |

## 配置文件说明

### 📄 pytest.ini 配置说明

```ini
[pytest]
testpaths = tests                 # 测试文件目录
python_files = test_*.py          # 测试文件命名模式
python_classes = Test*            # 测试类命名模式
python_functions = test_*         # 测试函数命名模式
addopts =
    -v                            # 详细输出
    --strict-markers              # 严格标记检查
    --tb=short                    # 简短错误回溯
    --cov=.                       # 启用覆盖率统计
    --cov-report=term-missing     # 终端显示未覆盖行
    --cov-report=html:htmlcov     # HTML覆盖率报告
    --cov-report=xml:coverage.xml # XML覆盖率报告
    --cov-config=.coveragerc      # 覆盖率配置文件
    --junitxml=pytest-report.xml  # JUnit XML报告
markers =
    unit: Unit tests              # 单元测试标记
    integration: Integration tests # 集成测试标记
    auth: Authentication tests     # 认证测试标记
    crud: CRUD operations tests    # CRUD测试标记
    permission: Permission tests   # 权限测试标记
filterwarnings =
    ignore::DeprecationWarning     # 忽略弃用警告
```

**使用方式：**
```bash
# 运行所有测试
pytest

# 只运行单元测试
pytest -m unit

# 只运行权限测试
pytest -m permission

# 生成覆盖率报告
pytest --cov=.
```

---

### 📄 .coveragerc 配置说明

```ini
[run]
source = .                        # 统计根目录
omit =
    tests/*                       # 排除测试文件
    */__init__.py                 # 排除初始化文件
    setup.py                      # 排除安装脚本
    conftest.py                   # 排除pytest配置
    utils/*                       # 排除工具类
    venv/*                        # 排除虚拟环境
    __pycache__/*                 # 排除缓存

[report]
show_missing = True               # 显示未覆盖的行
skip_covered = False              # 不跳过已覆盖文件
skip_empty = True                 # 跳过空文件
precision = 2                     # 小数精度
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

**覆盖率报告输出格式：**
- `term` - 终端文本报告
- `html` - HTML交互式报告 (htmlcov/index.html)
- `xml` - Cobertura格式XML报告 (coverage.xml)

---

### 📄 执行脚本 (run_tests.bat) 说明

**功能：**
1. ✅ 自动检测Python环境
2. ✅ 自动安装测试依赖 (pytest, pytest-cov, httpx)
3. ✅ 执行所有测试用例
4. ✅ 自动生成覆盖率报告
5. ✅ 调用 generate_report.py 生成 Markdown 摘要
6. ✅ 显示所有报告文件路径

**执行方式：**
```bash
# Windows 双击直接运行
.un_tests.bat

# 或在命令行执行
run_tests
```

**手动执行等效命令：**
```bash
pip install pytest pytest-cov httpx
pytest --cov=. --cov-report=html --cov-report=xml
python generate_report.py
```

---

### 📄 generate_report.py 说明

**功能：**
1. 解析 `pytest-report.xml` 获取测试结果统计
2. 解析 `coverage.xml` 获取代码覆盖率数据
3. 自动生成结构化的 Markdown 测试报告
4. 包含：通过率、覆盖率、模块覆盖、权限矩阵、边界场景覆盖等

**生成的报告文件：** `TEST_REPORT.md`


## ⚠️ 改进建议

1. **代码覆盖率较低**
   - 建议增加边缘场景测试
   - 检查异常分支是否覆盖

