"""
表单层：所有业务表单统一使用 ModelForm 校验。

要点：
- Bootstrap 3 样式通过给 widget 统一追加 form-control 实现
- 员工表单：姓名长度、年龄范围、手机号正则与唯一性（编辑时自动排除自身）
- 任务表单：由 AJAX 提交，错误以 JSON 返回并回显
"""
import django.forms as forms

from app01.models import (
    Attendance,
    Department,
    Employee,
    Notice,
    Role,
    Permission,
    Salary,
    Task,
)


class BootStrapFormMixin:
    """给除 Checkbox 外的所有控件套上 Bootstrap 3 的 form-control 样式。"""

    EXCLUDE_STYLE_FIELDS = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if name in self.EXCLUDE_STYLE_FIELDS:
                continue
            widget = field.widget
            if isinstance(widget, (forms.CheckboxInput, forms.CheckboxSelectMultiple)):
                continue
            classes = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{classes} form-control".strip()
            if isinstance(widget, forms.DateInput):
                widget.attrs["placeholder"] = "YYYY-MM-DD"
            if isinstance(widget, forms.TimeInput):
                widget.attrs["placeholder"] = "HH:MM"


class DepartmentModelForm(BootStrapFormMixin, forms.ModelForm):
    """部门表单。"""

    class Meta:
        model = Department
        fields = ["title"]


class EmployeeModelForm(BootStrapFormMixin, forms.ModelForm):
    """员工表单：含姓名 / 年龄 / 手机号校验。"""

    class Meta:
        model = Employee
        fields = [
            "name", "age", "gender", "balance", "entry_date",
            "phone", "depart", "avatar", "user",
        ]
        widgets = {
            "entry_date": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_name(self):
        """姓名长度 2-10 位。"""
        name = self.cleaned_data.get("name", "").strip()
        if not 2 <= len(name) <= 10:
            raise forms.ValidationError("姓名长度须为 2-10 个字符")
        return name

    def clean_age(self):
        """年龄范围 16-70。"""
        age = self.cleaned_data.get("age")
        if age is not None and not 16 <= age <= 70:
            raise forms.ValidationError("年龄须在 16-70 岁之间")
        return age

    def clean_phone(self):
        """手机号正则 ^1[3-9]\\d{9}$，唯一性由 unique=True 校验（编辑自动排除自身）。"""
        phone = self.cleaned_data.get("phone", "").strip()
        return phone


class AttendanceModelForm(BootStrapFormMixin, forms.ModelForm):
    """考勤表单：不提供状态字段，状态由上下班时间自动计算。"""

    class Meta:
        model = Attendance
        fields = ["employee", "date", "clock_in", "clock_out"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "clock_in": forms.TimeInput(attrs={"type": "time"}),
            "clock_out": forms.TimeInput(attrs={"type": "time"}),
        }


class SalaryModelForm(BootStrapFormMixin, forms.ModelForm):
    """薪资表单：不提供实发工资字段，由视图层计算。"""

    class Meta:
        model = Salary
        fields = ["employee", "month", "base", "bonus", "deduction"]
        widgets = {
            "month": forms.TextInput(attrs={"placeholder": "例如 2026-11"}),
        }

    def clean_month(self):
        """校验月份格式。"""
        import re

        month = self.cleaned_data.get("month", "").strip()
        if not re.match(r"^\d{4}-(0[1-9]|1[0-2])$", month):
            raise forms.ValidationError("月份格式不正确，应为 2026-11 这种格式")
        return month


class NoticeModelForm(BootStrapFormMixin, forms.ModelForm):
    """公告表单。"""

    class Meta:
        model = Notice
        fields = ["title", "content", "is_pinned"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 6}),
        }


class TaskModelForm(BootStrapFormMixin, forms.ModelForm):
    """任务表单（AJAX 提交）。"""

    class Meta:
        model = Task
        fields = ["level", "title", "detail", "owner"]
        widgets = {
            "detail": forms.Textarea(attrs={"rows": 4}),
        }


class RoleModelForm(BootStrapFormMixin, forms.ModelForm):
    """角色表单：勾选权限。"""

    EXCLUDE_STYLE_FIELDS = ["permissions"]

    class Meta:
        model = Role
        fields = ["title", "permissions"]
        widgets = {
            "permissions": forms.CheckboxSelectMultiple,
        }


class PermissionModelForm(BootStrapFormMixin, forms.ModelForm):
    """权限表单。"""

    class Meta:
        model = Permission
        fields = ["title", "code"]


class UserRoleForm(forms.Form):
    """用户角色分配表单。"""

    roles = forms.ModelMultipleChoiceField(
        queryset=Role.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        label="角色",
        required=False,
    )


class UserResetPwdForm(forms.Form):
    """管理员重置用户密码表单。"""

    password = forms.CharField(
        label="新密码",
        min_length=6,
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
