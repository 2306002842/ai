"""任务管理视图（T9）：AJAX 异步提交，返回 JSON，前端回显校验错误。"""
from django.http import JsonResponse
from django.shortcuts import render

from app01.forms import TaskModelForm
from app01.models import Employee, Task
from app01.utils import Pagination, permission_required


def _form_errors_json(form):
    """把 ModelForm 校验错误整理为 {字段: [错误信息]} 结构。"""
    return {field: [str(err) for err in errors] for field, errors in form.errors.items()}


def task_list(request):
    """任务列表：级别筛选 + 分页。"""
    level = request.GET.get("level", "")
    queryset = Task.objects.select_related("owner").all()
    if level in dict(Task.LEVEL_CHOICES):
        queryset = queryset.filter(level=level)
    pager = Pagination(request, queryset, page_size=10)
    return render(
        request,
        "app01/task_list.html",
        {
            "pager": pager,
            "page_objs": pager.object_list,
            "level": level,
            "level_choices": Task.LEVEL_CHOICES,
            "employees": Employee.objects.all(),
        },
    )


@permission_required("task:add")
def task_add(request):
    """AJAX 新增任务：成功返回新数据，失败返回逐字段错误。"""
    form = TaskModelForm(data=request.POST)
    if form.is_valid():
        obj = form.save()
        return JsonResponse({"status": True, "msg": "创建成功"})
    return JsonResponse({"status": False, "errors": _form_errors_json(form)})


@permission_required("task:edit")
def task_edit(request, obj_id):
    """AJAX 编辑任务。"""
    obj = Task.objects.filter(id=obj_id).first()
    if not obj:
        return JsonResponse({"status": False, "msg": "任务不存在"})
    form = TaskModelForm(data=request.POST, instance=obj)
    if form.is_valid():
        form.save()
        return JsonResponse({"status": True, "msg": "保存成功"})
    return JsonResponse({"status": False, "errors": _form_errors_json(form)})


@permission_required("task:delete")
def task_delete(request, obj_id):
    """AJAX 删除任务。"""
    if request.method == "POST":
        Task.objects.filter(id=obj_id).delete()
        return JsonResponse({"status": True, "msg": "删除成功"})
    return JsonResponse({"status": False, "msg": "请求方式错误"})
