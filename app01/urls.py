"""业务路由。"""
from django.urls import path

from app01.views import (
    account, attendance, department, employee, index, my, notice, rbac, salary, task,
    ai as ai_view,
)

urlpatterns = [
    # 首页
    path("", index.dashboard, name="index"),
    # 认证（白名单，无需登录）
    path("login/", account.login_view, name="login"),
    path("logout/", account.logout_view, name="logout"),
    path("captcha/", account.captcha_view, name="captcha"),
    # 无权限页
    path("403/", account.forbidden, name="forbidden"),
    # 部门
    path("department/list/", department.department_list, name="department_list"),
    path("department/add/", department.department_add, name="department_add"),
    path("department/edit/<int:obj_id>/", department.department_edit, name="department_edit"),
    path("department/delete/<int:obj_id>/", department.department_delete, name="department_delete"),
    # 员工
    path("employee/list/", employee.employee_list, name="employee_list"),
    path("employee/add/", employee.employee_add, name="employee_add"),
    path("employee/edit/<int:obj_id>/", employee.employee_edit, name="employee_edit"),
    path("employee/delete/<int:obj_id>/", employee.employee_delete, name="employee_delete"),
    # 考勤
    path("attendance/list/", attendance.attendance_list, name="attendance_list"),
    path("attendance/add/", attendance.attendance_add, name="attendance_add"),
    path("attendance/edit/<int:obj_id>/", attendance.attendance_edit, name="attendance_edit"),
    path("attendance/delete/<int:obj_id>/", attendance.attendance_delete, name="attendance_delete"),
    # 薪资
    path("salary/list/", salary.salary_list, name="salary_list"),
    path("salary/add/", salary.salary_add, name="salary_add"),
    path("salary/edit/<int:obj_id>/", salary.salary_edit, name="salary_edit"),
    path("salary/delete/<int:obj_id>/", salary.salary_delete, name="salary_delete"),
    # 公告
    path("notice/list/", notice.notice_list, name="notice_list"),
    path("notice/<int:obj_id>/", notice.notice_detail, name="notice_detail"),
    path("notice/add/", notice.notice_add, name="notice_add"),
    path("notice/edit/<int:obj_id>/", notice.notice_edit, name="notice_edit"),
    path("notice/delete/<int:obj_id>/", notice.notice_delete, name="notice_delete"),
    path("notice/pin/<int:obj_id>/", notice.notice_pin, name="notice_pin"),
    # 任务（新增/编辑为 AJAX）
    path("task/list/", task.task_list, name="task_list"),
    path("task/add/", task.task_add, name="task_add"),
    path("task/edit/<int:obj_id>/", task.task_edit, name="task_edit"),
    path("task/delete/<int:obj_id>/", task.task_delete, name="task_delete"),
    # RBAC 系统管理
    path("rbac/user/list/", rbac.user_list, name="user_list"),
    path("rbac/user/<int:obj_id>/roles/", rbac.user_roles, name="user_roles"),
    path("rbac/user/<int:obj_id>/reset-pwd/", rbac.user_reset_pwd, name="user_reset_pwd"),
    path("rbac/user/<int:obj_id>/delete/", rbac.user_delete, name="user_delete"),
    path("rbac/role/list/", rbac.role_list, name="role_list"),
    path("rbac/role/add/", rbac.role_add, name="role_add"),
    path("rbac/role/edit/<int:obj_id>/", rbac.role_edit, name="role_edit"),
    path("rbac/role/delete/<int:obj_id>/", rbac.role_delete, name="role_delete"),
    path("rbac/permission/list/", rbac.permission_list, name="permission_list"),
    path("rbac/permission/add/", rbac.permission_add, name="permission_add"),
    path("rbac/permission/edit/<int:obj_id>/", rbac.permission_edit, name="permission_edit"),
    path("rbac/permission/delete/<int:obj_id>/", rbac.permission_delete, name="permission_delete"),
    # 我的（普通员工只读视角）
    path("my/profile/", my.my_profile, name="my_profile"),
    path("my/attendance/", my.my_attendance, name="my_attendance"),
    path("my/salary/", my.my_salary, name="my_salary"),
    # ==================== AI 助手模块（课程设计 T1-T7） ====================
    path("ai/generate-jd/", ai_view.generate_jd, name="ai_generate_jd"),
    path("api/ai/generate-jd/", ai_view.api_generate_jd, name="api_ai_generate_jd"),
    path("ai/knowledge-qa/", ai_view.knowledge_qa, name="ai_knowledge_qa"),
    path("api/ai/knowledge-qa/", ai_view.api_knowledge_qa, name="api_ai_knowledge_qa"),
    path("ai/data-review/", ai_view.data_review, name="ai_data_review"),
    path("api/ai/data-review/", ai_view.api_data_review, name="api_ai_data_review"),
    path("ai/chat/", ai_view.chat_page, name="ai_chat"),
    path("api/ai/chat/", ai_view.api_chat, name="api_chat"),
    path("api/ai/chat/stream/", ai_view.api_chat_stream, name="api_chat_stream"),
]
