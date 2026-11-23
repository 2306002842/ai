"""系统管理视图（T5 RBAC）：用户角色分配、角色管理、权限管理。"""
from django.contrib.auth.hashers import make_password
from django.shortcuts import redirect, render

from app01.forms import PermissionModelForm, RoleModelForm, UserResetPwdForm, UserRoleForm
from app01.models import Permission, Role, User
from app01.utils import Pagination, permission_required


def _sync_user_session_perms(user):
    """角色变动后同步该用户在线会话中的权限码，使调整立即生效。"""
    from django.contrib.sessions.models import Session
    from django.utils import timezone

    codes = sorted(set(user.roles.values_list("permissions__code", flat=True)))
    for session in Session.objects.filter(expire_date__gte=timezone.now()):
        data = session.get_decoded()
        if data.get("_auth_user_id") == str(user.id):
            session.session_data = session.encode({**data, "perm_codes": codes})
            session.save()
            break


@permission_required("rbac:user")
def user_list(request):
    """用户列表：搜索 + 分页。"""
    query = request.GET.get("query", "").strip()
    queryset = User.objects.all().order_by("id")
    if query:
        queryset = queryset.filter(username__icontains=query)
    pager = Pagination(request, queryset, page_size=10)
    return render(
        request,
        "app01/rbac/user_list.html",
        {"pager": pager, "page_objs": pager.object_list, "query": query},
    )


@permission_required("rbac:user")
def user_roles(request, obj_id):
    """分配用户角色。"""
    user = User.objects.filter(id=obj_id).first()
    if not user:
        return redirect("/rbac/user/list/")
    if request.method == "POST":
        form = UserRoleForm(request.POST)
        if form.is_valid():
            user.roles.set(form.cleaned_data["roles"])
            _sync_user_session_perms(user)
            return redirect("/rbac/user/list/")
    else:
        form = UserRoleForm(initial={"roles": user.roles.all()})
    return render(
        request,
        "app01/rbac/user_roles.html",
        {"form": form, "user_obj": user},
    )


@permission_required("rbac:user")
def user_reset_pwd(request, obj_id):
    """管理员重置用户密码（make_password 安全哈希）。"""
    user = User.objects.filter(id=obj_id).first()
    if not user:
        return redirect("/rbac/user/list/")
    error = ""
    if request.method == "POST":
        form = UserResetPwdForm(request.POST)
        if form.is_valid():
            user.password = make_password(form.cleaned_data["password"])
            user.save(update_fields=["password"])
            return redirect("/rbac/user/list/")
        error = " ".join(form.errors.get("password", []))
    return render(request, "app01/rbac/user_reset_pwd.html", {"user_obj": user, "error": error})


@permission_required("rbac:user")
def user_delete(request, obj_id):
    """删除用户（不允许删除自己与超级管理员账号）。"""
    if request.method == "POST":
        user = User.objects.filter(id=obj_id).first()
        if user and not user.is_superuser and user != request.user:
            user.delete()
    return redirect("/rbac/user/list/")


@permission_required("rbac:role")
def role_list(request):
    """角色列表。"""
    queryset = Role.objects.all().order_by("id")
    pager = Pagination(request, queryset, page_size=10)
    return render(
        request,
        "app01/rbac/role_list.html",
        {"pager": pager, "page_objs": pager.object_list},
    )


@permission_required("rbac:role")
def role_add(request):
    """新增角色：勾选权限。"""
    form = RoleModelForm()
    if request.method == "POST":
        form = RoleModelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/rbac/role/list/")
    return render(request, "app01/rbac/role_form.html", {"form": form, "title": "新增角色"})


@permission_required("rbac:role")
def role_edit(request, obj_id):
    """编辑角色。"""
    obj = Role.objects.filter(id=obj_id).first()
    if not obj:
        return redirect("/rbac/role/list/")
    form = RoleModelForm(instance=obj)
    if request.method == "POST":
        form = RoleModelForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect("/rbac/role/list/")
    return render(request, "app01/rbac/role_form.html", {"form": form, "title": "编辑角色"})


@permission_required("rbac:role")
def role_delete(request, obj_id):
    """删除角色。"""
    if request.method == "POST":
        Role.objects.filter(id=obj_id).delete()
    return redirect("/rbac/role/list/")


@permission_required("rbac:permission")
def permission_list(request):
    """权限列表。"""
    queryset = Permission.objects.all().order_by("id")
    pager = Pagination(request, queryset, page_size=15)
    return render(
        request,
        "app01/rbac/permission_list.html",
        {"pager": pager, "page_objs": pager.object_list},
    )


@permission_required("rbac:permission")
def permission_add(request):
    """新增权限。"""
    form = PermissionModelForm()
    if request.method == "POST":
        form = PermissionModelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/rbac/permission/list/")
    return render(request, "app01/rbac/permission_form.html", {"form": form, "title": "新增权限"})


@permission_required("rbac:permission")
def permission_edit(request, obj_id):
    """编辑权限。"""
    obj = Permission.objects.filter(id=obj_id).first()
    if not obj:
        return redirect("/rbac/permission/list/")
    form = PermissionModelForm(instance=obj)
    if request.method == "POST":
        form = PermissionModelForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect("/rbac/permission/list/")
    return render(request, "app01/rbac/permission_form.html", {"form": form, "title": "编辑权限"})


@permission_required("rbac:permission")
def permission_delete(request, obj_id):
    """删除权限。"""
    if request.method == "POST":
        Permission.objects.filter(id=obj_id).delete()
    return redirect("/rbac/permission/list/")
