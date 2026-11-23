"""部门管理视图（T2）：新增、查询、编辑、删除。"""
from django.shortcuts import redirect, render

from app01.forms import DepartmentModelForm
from app01.models import Department
from app01.utils import Pagination, permission_required


@permission_required("department:view")
def department_list(request):
    """部门列表：按名称模糊搜索 + 分页。"""
    query = request.GET.get("query", "").strip()
    queryset = Department.objects.all().order_by("id")
    if query:
        queryset = queryset.filter(title__icontains=query)
    pager = Pagination(request, queryset, page_size=10)
    return render(
        request,
        "app01/department_list.html",
        {"pager": pager, "page_objs": pager.object_list, "query": query},
    )


@permission_required("department:add")
def department_add(request):
    """新增部门。"""
    form = DepartmentModelForm()
    if request.method == "POST":
        form = DepartmentModelForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/department/list/")
    return render(request, "app01/department_form.html", {"form": form, "title": "新增部门"})


@permission_required("department:edit")
def department_edit(request, obj_id):
    """编辑部门。"""
    obj = Department.objects.filter(id=obj_id).first()
    if not obj:
        return redirect("/department/list/")
    form = DepartmentModelForm(instance=obj)
    if request.method == "POST":
        form = DepartmentModelForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect("/department/list/")
    return render(request, "app01/department_form.html", {"form": form, "title": "编辑部门"})


@permission_required("department:delete")
def department_delete(request, obj_id):
    """删除部门（POST 确认后执行）。"""
    if request.method == "POST":
        Department.objects.filter(id=obj_id).delete()
    return redirect("/department/list/")
