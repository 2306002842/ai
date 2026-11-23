"""考勤管理视图（T6）：CRUD，状态由上下班时间自动计算。"""
from django.shortcuts import redirect, render

from app01.forms import AttendanceModelForm
from app01.models import Attendance, Employee
from app01.utils import Pagination, permission_required


@permission_required("attendance:view")
def attendance_list(request):
    """考勤列表：按员工姓名搜索 + 状态筛选 + 分页。"""
    query = request.GET.get("query", "").strip()
    status = request.GET.get("status", "")
    queryset = Attendance.objects.select_related("employee").order_by("-date", "employee_id")
    if query:
        queryset = queryset.filter(employee__name__icontains=query)
    if status in dict(Attendance.STATUS_CHOICES):
        queryset = queryset.filter(status=status)
    pager = Pagination(request, queryset, page_size=10)
    return render(
        request,
        "app01/attendance_list.html",
        {
            "pager": pager,
            "page_objs": pager.object_list,
            "query": query,
            "status": status,
            "status_choices": Attendance.STATUS_CHOICES,
        },
    )


@permission_required("attendance:add")
def attendance_add(request):
    """新增考勤：状态由 calc_status 自动计算，不允许手工选择。"""
    form = AttendanceModelForm()
    if request.method == "POST":
        form = AttendanceModelForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.status = Attendance.calc_status(obj.clock_in, obj.clock_out)
            obj.save()
            return redirect("/attendance/list/")
    return render(request, "app01/attendance_form.html", {"form": form, "title": "新增考勤"})


@permission_required("attendance:edit")
def attendance_edit(request, obj_id):
    """编辑考勤：重新按时间计算状态。"""
    obj = Attendance.objects.filter(id=obj_id).first()
    if not obj:
        return redirect("/attendance/list/")
    form = AttendanceModelForm(instance=obj)
    if request.method == "POST":
        form = AttendanceModelForm(request.POST, instance=obj)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.status = Attendance.calc_status(obj.clock_in, obj.clock_out)
            obj.save()
            return redirect("/attendance/list/")
    return render(request, "app01/attendance_form.html", {"form": form, "title": "编辑考勤"})


@permission_required("attendance:delete")
def attendance_delete(request, obj_id):
    """删除考勤。"""
    if request.method == "POST":
        Attendance.objects.filter(id=obj_id).delete()
    return redirect("/attendance/list/")
