"""模板标签：按权限码控制前端按钮显隐（RBAC 前端联动）。"""
from django import template

register = template.Library()


@register.filter
def has_perm(request, code):
    """判断当前请求是否拥有指定权限码。

    用法：{% if request|has_perm:"department:add" %} ... {% endif %}
    """
    if getattr(request, "is_super", False):
        return True
    return code in getattr(request, "perm_codes", set())
