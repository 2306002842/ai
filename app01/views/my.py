"""我的（普通员工只读视角）：查看自己的档案、考勤与薪资。"""
from django.shortcuts import redirect, render

from app01.models import Attendance, Salary
from app01.utils import Pagination


def _my_employee(request):
    """获取当前登录账号关联的员工档案。"""
    return getattr(request.user, "employee", None)


def my_profile(request):
    """我的档案。"""
    return render(request, "app01/my/profile.html", {"employee": _my_employee(request)})


def my_attendance(request):
    """我的考勤（只读）。"""
    employee = _my_employee(request)
    if not employee:
        return redirect("/my/profile/")
    queryset = Attendance.objects.filter(employee=employee).order_by("-date")
    pager = Pagination(request, queryset, page_size=15)
    return render(
        request,
        "app01/my/attendance.html",
        {"pager": pager, "page_objs": pager.object_list},
    )


def my_salary(request):
    """我的薪资（只读）。"""
    employee = _my_employee(request)
    if not employee:
        return redirect("/my/profile/")
    queryset = Salary.objects.filter(employee=employee).order_by("-month")
    pager = Pagination(request, queryset, page_size=15)
    return render(
        request,
        "app01/my/salary.html",
        {"pager": pager, "page_objs": pager.object_list},
    )
