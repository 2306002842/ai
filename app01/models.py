"""
数据模型层：企业员工管理系统全部业务模型。

ER 关系梳理：
- User(用户) 1..* Role(角色) *..* Permission(权限)   —— RBAC 三层
- User 1..1 Employee(员工档案)
- Department(部门) 1..* Employee
- Employee 1..* Attendance(考勤) / Salary(薪资)
- User 1..* Notice(公告，发布人)
- Employee 1..* Task(任务，负责人)
"""
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """自定义用户：继承 AbstractUser，扩展角色关联（RBAC）。"""

    roles = models.ManyToManyField(
        "Role", blank=True, related_name="users", verbose_name="角色"
    )

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = "用户"

    def __str__(self):
        return self.username


class Permission(models.Model):
    """权限：以 code 标识一个可执行的操作（接口级）。"""

    title = models.CharField("权限名称", max_length=32)
    code = models.CharField("权限代码", max_length=64, unique=True)

    class Meta:
        verbose_name = "权限"
        verbose_name_plural = "权限"

    def __str__(self):
        return f"{self.title}({self.code})"


class Role(models.Model):
    """角色：一组权限的集合，用户与权限通过角色关联。"""

    title = models.CharField("角色名称", max_length=32, unique=True)
    permissions = models.ManyToManyField(
        Permission, blank=True, related_name="roles", verbose_name="权限"
    )

    class Meta:
        verbose_name = "角色"
        verbose_name_plural = "角色"

    def __str__(self):
        return self.title


class Department(models.Model):
    """部门。"""

    title = models.CharField("部门名称", max_length=32, unique=True)

    class Meta:
        verbose_name = "部门"
        verbose_name_plural = "部门"

    def __str__(self):
        return self.title


class Employee(models.Model):
    """员工档案。"""

    GENDER_CHOICES = (("male", "男"), ("female", "女"))

    name = models.CharField("姓名", max_length=32)
    age = models.PositiveSmallIntegerField("年龄")
    gender = models.CharField("性别", max_length=8, choices=GENDER_CHOICES, default="male")
    balance = models.DecimalField(
        "账户余额", max_digits=10, decimal_places=2, default=0
    )
    entry_date = models.DateField("入职时间")
    phone = models.CharField(
        "手机号",
        max_length=11,
        unique=True,
        validators=[RegexValidator(r"^1[3-9]\d{9}$", "手机号格式不正确")],
    )
    depart = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
        verbose_name="所属部门",
    )
    avatar = models.ImageField(
        "头像", upload_to="avatar/", null=True, blank=True
    )
    # 关联登录账号：普通员工据此查看自己的档案/考勤/薪资
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee",
        verbose_name="登录账号",
    )

    class Meta:
        verbose_name = "员工"
        verbose_name_plural = "员工"

    def __str__(self):
        return self.name


class Attendance(models.Model):
    """考勤记录：状态由上下班时间自动计算，不允许手工选择。"""

    STATUS_CHOICES = (
        ("on_time", "按时"),
        ("late", "迟到"),
        ("early_leave", "早退"),
        ("absent", "缺勤"),
    )
    # 作息制度常量：9:00 上班、18:00 下班
    WORK_START = (9, 0)
    WORK_END = (18, 0)

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="attendances", verbose_name="员工"
    )
    date = models.DateField("日期")
    clock_in = models.TimeField("上班时间", null=True, blank=True)
    clock_out = models.TimeField("下班时间", null=True, blank=True)
    status = models.CharField(
        "考勤状态", max_length=16, choices=STATUS_CHOICES, blank=True
    )

    class Meta:
        verbose_name = "考勤"
        verbose_name_plural = "考勤"
        unique_together = (("employee", "date"),)
        ordering = ["-date"]

    def __str__(self):
        return f"{self.employee}-{self.date}-{self.get_status_display()}"

    @staticmethod
    def calc_status(clock_in, clock_out):
        """根据上下班时间自动计算考勤状态。

        规则：
        - 上下班均未打卡 -> 缺勤
        - 上班晚于 9:00 -> 迟到
        - 下班早于 18:00 -> 早退
        - 其余 -> 按时
        """
        import datetime

        if not clock_in and not clock_out:
            return "absent"
        start = datetime.time(*Attendance.WORK_START)
        end = datetime.time(*Attendance.WORK_END)
        if clock_in and clock_in > start:
            return "late"
        if clock_out and clock_out < end:
            return "early_leave"
        return "on_time"

    def save(self, *args, **kwargs):
        """保存前兜底重算状态，保证数据一致性。"""
        self.status = self.calc_status(self.clock_in, self.clock_out)
        super().save(*args, **kwargs)


class Salary(models.Model):
    """薪资记录：实发 = 基本工资 + 奖金 - 扣款（由视图层计算后写入）。"""

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="salaries", verbose_name="员工"
    )
    month = models.CharField("月份", max_length=7, help_text="格式：2026-11")
    base = models.DecimalField("基本工资", max_digits=10, decimal_places=2)
    bonus = models.DecimalField("奖金", max_digits=10, decimal_places=2, default=0)
    deduction = models.DecimalField("扣款", max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField("实发工资", max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = "薪资"
        verbose_name_plural = "薪资"
        unique_together = (("employee", "month"),)
        ordering = ["-month", "employee_id"]

    def __str__(self):
        return f"{self.employee}-{self.month}-{self.total}"


class Notice(models.Model):
    """公告：发布时间由 auto_now_add 自动写入。"""

    title = models.CharField("标题", max_length=64)
    content = models.TextField("内容")
    publisher = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, verbose_name="发布人"
    )
    publish_date = models.DateTimeField("发布时间", auto_now_add=True)
    is_pinned = models.BooleanField("是否置顶", default=False)

    class Meta:
        verbose_name = "公告"
        verbose_name_plural = "公告"
        ordering = ["-is_pinned", "-publish_date"]

    def __str__(self):
        return self.title


class Task(models.Model):
    """任务：通过 AJAX 异步提交与编辑。"""

    LEVEL_CHOICES = (("high", "高"), ("medium", "中"), ("low", "低"))

    level = models.CharField("级别", max_length=8, choices=LEVEL_CHOICES, default="low")
    title = models.CharField("标题", max_length=64)
    detail = models.TextField("详情", blank=True)
    owner = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
        verbose_name="负责人",
    )

    class Meta:
        verbose_name = "任务"
        verbose_name_plural = "任务"
        ordering = ["-id"]

    def __str__(self):
        return self.title


# ======================================================================
# AI 助手模块（课程设计 T1-T7 新增）
# ======================================================================

class Knowledge(models.Model):
    """制度知识库（T3）。"""

    title = models.CharField("标题", max_length=200)
    category = models.CharField("分类", max_length=50, default="制度")
    content = models.TextField("内容")
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "知识库条目"
        verbose_name_plural = "知识库条目"
        ordering = ["category", "title"]

    def __str__(self):
        return f"[{self.category}] {self.title}"


class ChatHistory(models.Model):
    """多轮对话历史（T5）。"""

    session_id = models.CharField("会话ID", max_length=64, db_index=True)
    role = models.CharField("角色", max_length=20)  # user / assistant / system
    content = models.TextField("内容")
    created_at = models.DateTimeField("时间", auto_now_add=True)

    class Meta:
        verbose_name = "对话记录"
        verbose_name_plural = "对话记录"
        ordering = ["created_at"]

    def __str__(self):
        return f"[{self.role}] {self.content[:30]}"
