"""薪资管理视图（T7）：CRUD，实发工资自动计算，支持月份/员工筛选与总额统计。"""
from django.db.models import Sum
from django.shortcuts import redirect, render

from app01.forms import SalaryModelForm
from app01.models import Employee, Salary
from app01.utils import Pagination, permission_required


@permission_required("salary:view")
def salary_list(request):
    """薪资列表：月份 + 员工筛选，统计选定月份实发总额。"""
    month = request.GET.get("month", "").strip()
    emp_id = request.GET.get("employee", "")

    queryset = Salary.objects.select_related("employee").all()
    if month:
        queryset = queryset.filter(month=month)
    if emp_id.isdigit():
        queryset = queryset.filter(employee_id=int(emp_id))

    # 选定月份的薪资总额统计（未选月份则统计全部）
    total = queryset.aggregate(sum_total=Sum("total"))["sum_total"] or 0

    pager = Pagination(request, queryset, page_size=10)
    return render(
        request,
        "app01/salary_list.html",
        {
            "pager": pager,
            "page_objs": pager.object_list,
            "month": month,
            "emp_id": emp_id,
            "total": total,
            "employees": Employee.objects.all(),
        },
    )


@permission_required("salary:add")
def salary_add(request):
    """新增薪资：实发 = 基本工资 + 奖金 - 扣款（视图层计算后再保存）。"""
    form = SalaryModelForm()
    if request.method == "POST":
        form = SalaryModelForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.total = obj.base + obj.bonus - obj.deduction
            obj.save()
            return redirect("/salary/list/")
    return render(request, "app01/salary_form.html", {"form": form, "title": "新增薪资"})


@permission_required("salary:edit")
def salary_edit(request, obj_id):
    """编辑薪资：重新计算实发工资。"""
    obj = Salary.objects.filter(id=obj_id).first()
    if not obj:
        return redirect("/salary/list/")
    form = SalaryModelForm(instance=obj)
    if request.method == "POST":
        form = SalaryModelForm(request.POST, instance=obj)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.total = obj.base + obj.bonus - obj.deduction
            obj.save()
            return redirect("/salary/list/")
    return render(request, "app01/salary_form.html", {"form": form, "title": "编辑薪资"})


@permission_required("salary:delete")
def salary_delete(request, obj_id):
    """删除薪资。"""
    if request.method == "POST":
        Salary.objects.filter(id=obj_id).delete()
    return redirect("/salary/list/")
