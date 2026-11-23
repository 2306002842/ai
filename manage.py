#!/usr/bin/env python
"""Django 命令行管理工具。"""
import os
import sys


def main():
    """启动管理入口，默认指向 hrms 配置模块。"""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hrms.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "无法导入 Django，请确认已安装依赖：pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
