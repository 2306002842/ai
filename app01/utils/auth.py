"""认证工具：白名单与接口级权限装饰器。"""
from functools import wraps

from django.shortcuts import redirect

# 无需登录即可访问的路径
WHITE_LIST = ["/login/", "/captcha/", "/403/"]


def permission_required(code):
    """接口级权限校验装饰器（RBAC）。

    - 超级管理员直接放行
    - 其余用户须在会话权限码中包含 code，否则跳转 403 页
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if getattr(request, "is_super", False):
                return view_func(request, *args, **kwargs)
            if code in getattr(request, "perm_codes", set()):
                return view_func(request, *args, **kwargs)
            return redirect("/403/")

        return _wrapped

    return decorator
