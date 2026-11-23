"""认证相关视图：登录（含图片验证码）、注销、403 页。"""
from io import BytesIO

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.shortcuts import HttpResponse, redirect, render

from app01.utils.captcha import generate_captcha_image, random_code


def _collect_perm_codes(user):
    """汇总用户全部权限码（登录成功时调用，写入会话）。"""
    codes = set()
    for role in user.roles.all():
        codes.update(role.permissions.values_list("code", flat=True))
    return sorted(codes)


def login_view(request):
    """登录页：用户名 + 密码 + 图片验证码（点击图片刷新）。"""
    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        captcha = request.POST.get("captcha", "").strip()

        # 1. 校验验证码（不区分大小写，一次性使用）
        session_code = request.session.get("captcha_code", "")
        request.session.pop("captcha_code", None)
        if not session_code or captcha.upper() != session_code.upper():
            error = "验证码错误"
        else:
            # 2. 校验用户名密码（Django 安全哈希校验）
            user = authenticate(request, username=username, password=password)
            if not user:
                error = "用户名或密码错误"
            elif not user.is_active:
                error = "账号已被禁用"
            else:
                # 3. 维持会话并写入权限码
                auth_login(request, user)
                request.session["perm_codes"] = _collect_perm_codes(user)
                next_url = request.GET.get("next") or "/"
                return redirect(next_url if next_url.startswith("/") else "/")

    return render(request, "app01/login.html", {"error": error})


def captcha_view(request):
    """输出验证码图片，并将明文存入会话供 POST 校验。"""
    code = random_code()
    request.session["captcha_code"] = code
    image_bytes = generate_captcha_image(code)
    return HttpResponse(BytesIO(image_bytes), content_type="image/png")


def logout_view(request):
    """注销：清除会话并回到登录页。"""
    auth_logout(request)
    return redirect("/login/")


def forbidden(request):
    """无权限提示页。"""
    return render(request, "app01/403.html")
