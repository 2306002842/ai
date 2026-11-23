"""通用分页组件：基于 Django Paginator，保留查询参数并生成 Bootstrap 3 分页条。"""
from django.core.paginator import Paginator
from django.http import QueryDict


class Pagination:
    """列表页通用分页。

    用法：
        pager = Pagination(request, queryset, page_size=10)
        page_objs = pager.object_list
        模板中 {{ pager.html|safe }} 渲染分页条。
    """

    def __init__(self, request, queryset, page_size=10, max_show=7):
        self.request = request
        self.queryset = queryset
        self.page_size = page_size
        self.max_show = max_show

        # 每页条数支持通过 size 参数调整，限制范围防止异常值
        try:
            self.page_size = min(max(int(request.GET.get("size", page_size)), 5), 100)
        except (TypeError, ValueError):
            pass

        paginator = Paginator(queryset, self.page_size)
        try:
            page_number = int(request.GET.get("page", "1"))
        except (TypeError, ValueError):
            page_number = 1
        self.page = paginator.get_page(page_number)
        self.object_list = self.page.object_list
        self.paginator = paginator

    @property
    def html(self):
        """生成 Bootstrap 3 分页条 HTML，自动携带当前查询条件。"""
        total = self.paginator.num_pages
        if total <= 1:
            return ""

        current = self.page.number
        start = max(current - self.max_show // 2, 1)
        end = min(start + self.max_show - 1, total)
        start = max(min(start, end - self.max_show + 1), 1)

        base_params = self.request.GET.copy()
        links = []
        if current > 1:
            links.append(self._build_link(base_params, current - 1, "上一页"))
        for num in range(start, end + 1):
            active = " active" if num == current else ""
            links.append(f'<li class="{active.strip()}"><a href="{self._url(base_params, num)}">{num}</a></li>')
        if current < total:
            links.append(self._build_link(base_params, current + 1, "下一页"))
        return (
            '<nav><ul class="pagination pagination-sm">'
            + "".join(links)
            + "</ul></nav>"
        )

    def _build_link(self, base_params, page_num, text):
        return f'<li><a href="{self._url(base_params, page_num)}">{text}</a></li>'

    @staticmethod
    def _url(base_params: QueryDict, page_num: int) -> str:
        params = base_params.copy()
        params["page"] = str(page_num)
        return f"?{params.urlencode()}"
