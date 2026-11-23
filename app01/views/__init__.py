"""视图包：按业务模块拆分。"""
from app01.views import (
    account, attendance, department, employee, index, my, notice, rbac, salary, task,
)

__all__ = [
    "account", "attendance", "department", "employee", "index",
    "my", "notice", "rbac", "salary", "task",
]
