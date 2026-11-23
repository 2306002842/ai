"""员工管理视图（T3）：CRUD + 校验 + 搜索筛选 + 分页 + 头像上传。"""
from django.shortcuts import redirect, render

from app01.forms import EmployeeModelForm
from app01.models import Department, Employee
from app01.utils import Pagination, permission_required


@permission_required("employee:view")
def employee_list(request):
    """员工列表：姓名模糊搜索 + 部门筛选 + 分页。"""
    query = request.GET.get("query", "").strip()
    depart_id = request.GET.get("depart", "")
    queryset = Employee.objects.all().order_by("id")
    if query:
        queryset = queryset.filter(name__icontains=query)
    if depart_id.isdigit():
        queryset = queryset.filter(depart_id=int(depart_id))
    pager = Pagination(request, queryset, page_size=10)
    return render(
        request,
        "app01/employee_list.html",
        {
            "pager": pager,
            "page_objs": pager.object_list,
            "query": query,
            "depart_id": depart_id,
            "departments": Department.objects.all(),
        },
    )


@permission_required("employee:add")
def employee_add(request):
    """新增员工（ModelForm 校验 + 头像上传）。"""
    form = EmployeeModelForm()
    if request.method == "POST":
        form = EmployeeModelForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            form.save()
            return redirect("/employee/list/")
    return render(request, "app01/employee_form.html", {"form": form, "title": "新建员工"})


@permission_required("employee:edit")
def employee_edit(request, obj_id):
    """编辑员工：手机号唯一性校验自动排除自身。"""
    obj = Employee.objects.filter(id=obj_id).first()
    if not obj:
        return redirect("/employee/list/")
    form = EmployeeModelForm(instance=obj)
    if request.method == "POST":
        form = EmployeeModelForm(data=request.POST, files=request.FILES, instance=obj)
        if form.is_valid():
            form.save()
            return redirect("/employee/list/")
    return render(request, "app01/employee_form.html", {"form": form, "title": "编辑员工"})


@permission_required("employee:delete")
def employee_delete(request, obj_id):
    """删除员工。"""
    if request.method == "POST":
        Employee.objects.filter(id=obj_id).delete()
    return redirect("/employee/list/")
