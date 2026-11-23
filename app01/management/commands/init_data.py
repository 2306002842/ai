"""初始化命令：生成权限、默认角色与管理员账号。

用法：python manage.py init_data
可重复执行（幂等），不影响已有数据。
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from app01.models import Permission, Role

# 全部权限码定义（与视图装饰器、模板按钮控制保持一致）
PERMISSIONS = [
    ("department:view", "部门-查看"),
    ("department:add", "部门-新增"), ("department:edit", "部门-编辑"), ("department:delete", "部门-删除"),
    ("employee:view", "员工-查看"),
    ("employee:add", "员工-新增"), ("employee:edit", "员工-编辑"), ("employee:delete", "员工-删除"),
    ("attendance:view", "考勤-查看"),
    ("attendance:add", "考勤-新增"), ("attendance:edit", "考勤-编辑"), ("attendance:delete", "考勤-删除"),
    ("salary:view", "薪资-查看"),
    ("salary:add", "薪资-新增"), ("salary:edit", "薪资-编辑"), ("salary:delete", "薪资-删除"),
    ("notice:add", "公告-发布"), ("notice:edit", "公告-编辑"), ("notice:delete", "公告-删除"), ("notice:pin", "公告-置顶"),
    ("task:add", "任务-新增"), ("task:edit", "任务-编辑"), ("task:delete", "任务-删除"),
    ("rbac:user", "系统-用户管理"), ("rbac:role", "系统-角色管理"), ("rbac:permission", "系统-权限管理"),
]

# 默认角色及其权限码：部门管理员可查看并管理本部门员工、考勤与薪资
EMPLOYEE_ALL = [c for c, _ in PERMISSIONS if c.split(":")[0] in ("employee", "attendance", "salary")]
ROLES = [
    ("超级管理员", "all"),
    ("部门管理员", EMPLOYEE_ALL),
    ("普通员工", []),
]


class Command(BaseCommand):
    """init_data 命令。"""

    help = "初始化权限、默认角色与管理员账号（幂等）"

    def handle(self, *args, **options):
        user_model = get_user_model()

        # 1. 权限
        for code, title in PERMISSIONS:
            Permission.objects.update_or_create(code=code, defaults={"title": title})
        self.stdout.write(f"权限已就绪：{len(PERMISSIONS)} 项")

        # 2. 角色
        for title, perm_codes in ROLES:
            role, _ = Role.objects.update_or_create(title=title)
            if perm_codes == "all":
                role.permissions.set(Permission.objects.all())
            else:
                role.permissions.set(Permission.objects.filter(code__in=perm_codes))
        self.stdout.write(f"角色已就绪：{len(ROLES)} 个")

        # 3. 超级管理员账号
        admin, created = user_model.objects.update_or_create(
            username="admin",
            defaults={"is_staff": True, "is_superuser": True, "is_active": True},
        )
        if created:
            admin.set_password("admin123")
            admin.save()
        admin.roles.set([Role.objects.get(title="超级管理员")])
        self.stdout.write(self.style.SUCCESS("管理员账号：admin / admin123"))
        self.stdout.write(self.style.SUCCESS("初始化完成"))
