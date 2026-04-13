# 测试报告模板

## 测试执行摘要

### 执行信息

| 项目 | 值 |
|------|-----|
| 执行时间 | {{execution_time}} |
| 测试框架 | pytest {{pytest_version}} |
| Python 版本 | {{python_version}} |
| 操作系统 | {{platform}} |

### 测试统计

| 状态 | 数量 | 占比 |
|------|------|------|
| 通过 (Passed) | {{passed}} | {{pass_rate}}% |
| 失败 (Failed) | {{failed}} | {{fail_rate}}% |
| 错误 (Error) | {{error}} | {{error_rate}}% |
| 跳过 (Skipped) | {{skipped}} | {{skip_rate}}% |
| **总计** | **{{total}}** | **100%** |

### 通过率

```
{{pass_bar}}
```

**{{pass_rate}}%** 测试通过

---

## 代码覆盖率

### 总体覆盖率

| 指标 | 覆盖率 | 阈值 | 状态 |
|------|--------|------|------|
| 语句覆盖率 (Statements) | {{statement_cov}}% | 80% | {{statement_status}} |
| 分支覆盖率 (Branches) | {{branch_cov}}% | 70% | {{branch_status}} |
| 函数覆盖率 (Functions) | {{function_cov}}% | 80% | {{function_status}} |
| 行覆盖率 (Lines) | {{line_cov}}% | 80% | {{line_status}} |

### 模块覆盖率详情

| 模块 | 语句 | 未覆盖 | 覆盖率 | 状态 |
|------|------|--------|--------|------|
| sql_app/cruds/users.py | {{crud_stmts}} | {{crud_missing}} | {{crud_cov}}% | {{crud_status}} |
| sql_app/models.py | {{model_stmts}} | {{model_missing}} | {{model_cov}}% | {{model_status}} |
| sql_app/database.py | {{db_stmts}} | {{db_missing}} | {{db_cov}}% | {{db_status}} |
| routers/auth.py | {{auth_stmts}} | {{auth_missing}} | {{auth_cov}}% | {{auth_status}} |
| routers/users.py | {{user_router_stmts}} | {{user_router_missing}} | {{user_router_cov}}% | {{user_router_status}} |

---

## 测试用例详情

### 认证模块 (test_auth.py)

| 测试类 | 用例数 | 通过 | 失败 | 状态 |
|--------|--------|------|------|------|
| TestCreateAccessToken | {{auth_token_cases}} | {{auth_token_pass}} | {{auth_token_fail}} | {{auth_token_status}} |
| TestGetCurrentUser | {{auth_user_cases}} | {{auth_user_pass}} | {{auth_user_fail}} | {{auth_user_status}} |
| TestGetCurrentActiveUser | {{auth_active_cases}} | {{auth_active_pass}} | {{auth_active_fail}} | {{auth_active_status}} |
| TestRoleCheck | {{auth_role_cases}} | {{auth_role_pass}} | {{auth_role_fail}} | {{auth_role_status}} |
| TestRateLimiting | {{auth_rate_cases}} | {{auth_rate_pass}} | {{auth_rate_fail}} | {{auth_rate_status}} |
| TestLogin | {{auth_login_cases}} | {{auth_login_pass}} | {{auth_login_fail}} | {{auth_login_status}} |

### CRUD 模块 (test_crud_users.py)

| 测试类 | 用例数 | 通过 | 失败 | 状态 |
|--------|--------|------|------|------|
| TestPasswordHash | {{crud_pwd_cases}} | {{crud_pwd_pass}} | {{crud_pwd_fail}} | {{crud_pwd_status}} |
| TestGetUser | {{crud_get_cases}} | {{crud_get_pass}} | {{crud_get_fail}} | {{crud_get_status}} |
| TestGetUserByEmail | {{crud_email_cases}} | {{crud_email_pass}} | {{crud_email_fail}} | {{crud_email_status}} |
| TestGetUserByLogin | {{crud_login_cases}} | {{crud_login_pass}} | {{crud_login_fail}} | {{crud_login_status}} |
| TestGetUsers | {{crud_list_cases}} | {{crud_list_pass}} | {{crud_list_fail}} | {{crud_list_status}} |
| TestCreateUser | {{crud_create_cases}} | {{crud_create_pass}} | {{crud_create_fail}} | {{crud_create_status}} |
| TestDeleteUser | {{crud_delete_cases}} | {{crud_delete_pass}} | {{crud_delete_fail}} | {{crud_delete_status}} |
| TestUpdateUser | {{crud_update_cases}} | {{crud_update_pass}} | {{crud_update_fail}} | {{crud_update_status}} |
| TestUpdateUserPassword | {{crud_pass_cases}} | {{crud_pass_pass}} | {{crud_pass_fail}} | {{crud_pass_status}} |

### 路由模块 (test_routers_users.py)

| 测试类 | 用例数 | 通过 | 失败 | 状态 |
|--------|--------|------|------|------|
| TestCreateUser | {{router_create_cases}} | {{router_create_pass}} | {{router_create_fail}} | {{router_create_status}} |
| TestGetUsers | {{router_list_cases}} | {{router_list_pass}} | {{router_list_fail}} | {{router_list_status}} |
| TestGetUserMe | {{router_me_cases}} | {{router_me_pass}} | {{router_me_fail}} | {{router_me_status}} |
| TestGetUserById | {{router_get_cases}} | {{router_get_pass}} | {{router_get_fail}} | {{router_get_status}} |
| TestDeleteUser | {{router_delete_cases}} | {{router_delete_pass}} | {{router_delete_fail}} | {{router_delete_status}} |
| TestUpdateUser | {{router_update_cases}} | {{router_update_pass}} | {{router_update_fail}} | {{router_update_status}} |
| TestUpdateUserPassword | {{router_pass_cases}} | {{router_pass_pass}} | {{router_pass_fail}} | {{router_pass_status}} |
| TestEdgeCases | {{router_edge_cases}} | {{router_edge_pass}} | {{router_edge_fail}} | {{router_edge_status}} |
| TestPermissionMatrix | {{router_perm_cases}} | {{router_perm_pass}} | {{router_perm_fail}} | {{router_perm_status}} |

---

## 权限测试覆盖

### 权限矩阵验证

| 操作 | 公开 | 普通用户 | 管理员 | 已验证 |
|------|------|----------|--------|--------|
| 创建用户 | {{perm_create_public}} | {{perm_create_general}} | {{perm_create_admin}} | {{perm_create_verified}} |
| 获取所有用户 | {{perm_list_public}} | {{perm_list_general}} | {{perm_list_admin}} | {{perm_list_verified}} |
| 获取本人信息 | {{perm_me_public}} | {{perm_me_general}} | {{perm_me_admin}} | {{perm_me_verified}} |
| 获取指定用户 | {{perm_get_public}} | {{perm_get_general}} | {{perm_get_admin}} | {{perm_get_verified}} |
| 更新用户 | {{perm_update_public}} | {{perm_update_general}} | {{perm_update_admin}} | {{perm_update_verified}} |
| 删除用户 | {{perm_delete_public}} | {{perm_delete_general}} | {{perm_delete_admin}} | {{perm_delete_verified}} |
| 修改密码 | {{perm_pass_public}} | {{perm_pass_general}} | {{perm_pass_admin}} | {{perm_pass_verified}} |

### HTTP 状态码覆盖

| 状态码 | 含义 | 覆盖场景 | 已验证 |
|--------|------|----------|--------|
| 200 | OK | 正常请求成功 | {{status_200}} |
| 400 | Bad Request | 重复邮箱、无效数据 | {{status_400}} |
| 401 | Unauthorized | 未认证、无效 Token | {{status_401}} |
| 403 | Forbidden | 权限不足、旧密码错误 | {{status_403}} |
| 404 | Not Found | 用户不存在 | {{status_404}} |
| 422 | Unprocessable Entity | 验证错误 | {{status_422}} |
| 429 | Too Many Requests | 请求频率超限 | {{status_429}} |

---

## 边界条件测试

| 场景 | 测试项 | 状态 |
|------|--------|------|
| 空数据库 | 查询空表 | {{edge_empty_db}} |
| 负数 ID | 查询/删除负数 ID | {{edge_negative_id}} |
| 超长邮箱 | 200+ 字符邮箱 | {{edge_long_email}} |
| 特殊字符 | 邮箱包含特殊字符 | {{edge_special_chars}} |
| 空密码 | 创建/登录空密码 | {{edge_empty_password}} |
| 大小写敏感 | 邮箱大小写 | {{edge_case_sensitive}} |
| 过期 Token | 使用过期 Token | {{edge_expired_token}} |
| 无效 Token | 格式错误 Token | {{edge_invalid_token}} |
| 并发请求 | 频率限制测试 | {{edge_rate_limit}} |

---

## 失败用例详情

{{#failed_tests}}
### {{test_name}}

- **文件**: {{file_path}}
- **函数**: {{function_name}}
- **错误类型**: {{error_type}}
- **错误信息**:
```
{{error_message}}
```

{{/failed_tests}}

{{^failed_tests}}
*所有测试用例均通过*
{{/failed_tests}}

---

## 改进建议

{{#suggestions}}
{{.}}
{{/suggestions}}

{{^suggestions}}
1. 继续保持当前测试覆盖率
2. 定期更新测试用例以覆盖新功能
3. 考虑添加性能测试
4. 考虑添加安全渗透测试
{{/suggestions}}

---

## 附录

### 测试环境

```
pytest: {{pytest_version}}
pytest-asyncio: {{pytest_asyncio_version}}
pytest-cov: {{pytest_cov_version}}
httpx: {{httpx_version}}
fastapi: {{fastapi_version}}
sqlalchemy: {{sqlalchemy_version}}
```

### 执行命令

```bash
# 运行所有测试
pytest tests/ -v

# 带覆盖率运行
pytest tests/ -v --cov=sql_app --cov=routers --cov=main

# 生成 HTML 报告
pytest tests/ -v --cov=sql_app --cov=routers --cov=main --cov-report=html

# 运行指定模块
pytest tests/test_auth.py -v
pytest tests/test_crud_users.py -v
pytest tests/test_routers_users.py -v
```

---

*报告生成时间: {{report_time}}*
