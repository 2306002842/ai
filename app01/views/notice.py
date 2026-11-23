"""公告管理视图（T8）：发布、列表、置顶、搜索、分页。"""
from django.shortcuts import redirect, render

from app01.forms import NoticeModelForm
from app01.models import Notice
from app01.utils import Pagination, permission_required


def notice_list(request):
    """公告列表：置顶优先，按发布时间倒序，标题模糊搜索 + 分页。"""
    query = request.GET.get("query", "").strip()
    queryset = Notice.objects.select_related("publisher").all()
    if query:
        queryset = queryset.filter(title__icontains=query)
    pager = Pagination(request, queryset, page_size=10)
    return render(
        request,
        "app01/notice_list.html",
        {"pager": pager, "page_objs": pager.object_list, "query": query},
    )


def notice_detail(request, obj_id):
    """公告详情。"""
    obj = Notice.objects.filter(id=obj_id).select_related("publisher").first()
    return render(request, "app01/notice_detail.html", {"obj": obj})


@permission_required("notice:add")
def notice_add(request):
    """发布公告：发布时间 auto_now_add 自动写入，发布人取当前登录用户。"""
    form = NoticeModelForm()
    if request.method == "POST":
        form = NoticeModelForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.publisher = request.user
            obj.save()
            return redirect("/notice/list/")
    return render(request, "app01/notice_form.html", {"form": form, "title": "发布公告"})


@permission_required("notice:edit")
def notice_edit(request, obj_id):
    """编辑公告。"""
    obj = Notice.objects.filter(id=obj_id).first()
    if not obj:
        return redirect("/notice/list/")
    form = NoticeModelForm(instance=obj)
    if request.method == "POST":
        form = NoticeModelForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect("/notice/list/")
    return render(request, "app01/notice_form.html", {"form": form, "title": "编辑公告"})


@permission_required("notice:delete")
def notice_delete(request, obj_id):
    """删除公告。"""
    if request.method == "POST":
        Notice.objects.filter(id=obj_id).delete()
    return redirect("/notice/list/")


@permission_required("notice:pin")
def notice_pin(request, obj_id):
    """置顶 / 取消置顶（POST 切换）。"""
    if request.method == "POST":
        obj = Notice.objects.filter(id=obj_id).first()
        if obj:
            obj.is_pinned = not obj.is_pinned
            obj.save(update_fields=["is_pinned"])
    return redirect("/notice/list/")
