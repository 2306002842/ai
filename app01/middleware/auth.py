"""
认证与权限中间件。

三层联动（对应 T4 / T5）：
1. 本中间件：未登录访问受保护页面统一重定向到登录页（白名单除外）；
2. 装饰器（app01/utils/auth.py 的 permission_required）：接口级权限校验；
3. 模板：按权限码隐藏功能按钮（templatetags/hrms_perms.py）。
"""
from django.shortcuts import redirect

from app01.utils.auth import WHITE_LIST


class AuthMiddleware:
    """登录拦截 + 权限码注入。"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        # 静态资源、媒体文件与白名单页面不做拦截
        if (path.startswith("/static/") or path.startswith("/media/")
                or path in WHITE_LIST or path.startswith("/api/")):
            request.perm_codes = set()
            request.is_super = False
            return self.get_response(request)

        if not request.user.is_authenticated:
            return redirect(f"/login/?next={path}")

        # 登录用户：从会话取权限码集合（登录成功时写入），供视图与模板使用
        request.perm_codes = set(request.session.get("perm_codes", []))
        request.is_super = bool(request.user.is_superuser)
        return self.get_response(request)
