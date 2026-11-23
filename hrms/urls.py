"""根路由：统一引入 app01 的业务路由。"""
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve as media_serve

from hrms import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("app01.urls")),
    # 开发环境直接由 Django 托管媒体文件（头像等上传内容）
    path("media/<path:path>", media_serve, {"document_root": settings.MEDIA_ROOT}),
]
