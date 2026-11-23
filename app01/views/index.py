"""首页仪表盘：展示关键统计与最新公告。"""
from django.db.models import Count, Sum
from django.shortcuts import render

from app01.models import Attendance, Employee, Notice, Salary, Task


def dashboard(request):
    """首页。"""
    context = {
        "emp_count": Employee.objects.count(),
        "dept_count": Employee.objects.values("depart").distinct().count(),
        "attendance_count": Attendance.objects.count(),
        "task_count": Task.objects.count(),
        "salary_total": Salary.objects.aggregate(t=Sum("total"))["t"] or 0,
        "notices": Notice.objects.all()[:5],
        "tasks": Task.objects.all()[:5],
    }
    return render(request, "app01/index.html", context)
