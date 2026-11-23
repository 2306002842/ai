"""演示数据命令：一键写入部门、员工、考勤、薪资、公告与任务，便于各阶段自测。

用法：python manage.py demo_data
可重复执行：已存在相同姓名/手机号的员工会跳过。
"""
import datetime
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from app01.models import Attendance, Department, Employee, Notice, Role, Salary, Task

DEPARTMENTS = ["研发部", "市场部", "财务部", "人事部", "行政部"]
NAMES = [
    "张伟", "王芳", "李娜", "刘强", "陈静", "杨洋", "赵磊", "黄敏", "周涛", "吴倩",
    "徐勇", "孙丽", "马超", "朱霞", "胡军", "郭婷", "林峰", "何雪", "高鹏", "罗丹",
]
NOTICES = [
    ("关于中秋放假安排的通知", "全体员工：中秋节放假三天，请各部门提前安排好工作交接。", True),
    ("新版考勤制度上线", "自本月起，上班打卡时间为 9:00 前打卡，下班 18:00 后打卡，迟到早退将自动记录。", False),
    ("员工体检福利通知", "公司统一安排年度体检，请在行政部预约具体时间。", False),
    ("信息安全培训", "本周五下午三点于大会议室进行信息安全培训，请全体员工准时参加。", False),
    ("宿舍安全检查", "行政部将于下周一对员工宿舍进行安全检查，请提前整理。", False),
]
TASKS = [
    ("high", "完成季度述职报告", "包含业绩数据与下季度计划"),
    ("high", "系统上线演练", "联合测试环境进行一次完整演练"),
    ("medium", "整理客户档案", "按区域归档并核对联系方式"),
    ("medium", "月度预算核对", "与财务部核对本月开销"),
    ("low", "更新部门知识库", "补充常见问题与解决方案"),
    ("low", "办公用品盘点", "统计库存并提交补货申请"),
]


class Command(BaseCommand):
    """demo_data 命令。"""

    help = "写入演示数据（部门/员工/考勤/薪资/公告/任务），可重复执行"

    def handle(self, *args, **options):
        with transaction.atomic():
            self._create_departments()
            employees = self._create_employees()
            self._create_attendance(employees)
            self._create_salary(employees)
            self._create_notices()
            self._create_tasks(employees)
            self._create_accounts(employees)
        self.stdout.write(self.style.SUCCESS("演示数据写入完成"))

    def _create_departments(self):
        """创建部门。"""
        for title in DEPARTMENTS:
            Department.objects.get_or_create(title=title)
        self.stdout.write(f"部门：{len(DEPARTMENTS)} 个")

    def _create_employees(self):
        """创建员工（跳过已存在的手机号）。"""
        employees = []
        random.seed(42)
        phones = random.sample(range(13300000000, 18999999999), len(NAMES))
        depts = list(Department.objects.all())
        for idx, name in enumerate(NAMES):
            phone = str(phones[idx])[:11]
            if not phone.startswith("1") or phone[1] not in "35789":
                phone = "138" + phone[3:11]
            employee, created = Employee.objects.get_or_create(
                phone=phone,
                defaults={
                    "name": name,
                    "age": random.randint(22, 55),
                    "gender": random.choice(["male", "female"]),
                    "balance": random.randint(0, 20000),
                    "entry_date": datetime.date.today()
                    - datetime.timedelta(days=random.randint(30, 2000)),
                    "depart": random.choice(depts),
                },
            )
            employees.append(employee)
        self.stdout.write(f"员工：{len(employees)} 名")
        return employees

    def _create_attendance(self, employees):
        """创建最近 7 天考勤（每人每天一条）。"""
        today = datetime.date.today()
        count = 0
        for employee in employees[:10]:
            for offset in range(7):
                date = today - datetime.timedelta(days=offset)
                absent = random.random() < 0.1  # 十分之一概率缺勤
                clock_in = None
                clock_out = None
                if not absent and date.weekday() < 5:
                    late = random.random() < 0.15
                    clock_in = datetime.time(9, random.randint(1, 20)) if late else datetime.time(
                        random.randint(8, 8), random.randint(30, 59)
                    )
                    early = random.random() < 0.1
                    clock_out = datetime.time(17, random.randint(10, 45)) if early else datetime.time(
                        random.randint(18, 20), random.randint(0, 59)
                    )
                _, created = Attendance.objects.get_or_create(
                    employee=employee,
                    date=date,
                    defaults={"clock_in": clock_in, "clock_out": clock_out},
                )
                count += 1 if created else 0
        self.stdout.write(f"考勤：新增 {count} 条")

    def _create_salary(self, employees):
        """创建最近 3 个月薪资。"""
        today = datetime.date.today()
        months = []
        for offset in range(3):
            year, month = today.year, today.month - offset
            if month <= 0:
                year, month = year - 1, month + 12
            months.append(f"{year}-{month:02d}")
        count = 0
        for employee in employees:
            base = random.choice([5000, 6500, 8000, 9500, 12000, 15000])
            for month in months:
                bonus = random.randint(0, 3000)
                deduction = random.randint(0, 800)
                _, created = Salary.objects.get_or_create(
                    employee=employee,
                    month=month,
                    defaults={
                        "base": base,
                        "bonus": bonus,
                        "deduction": deduction,
                        "total": base + bonus - deduction,
                    },
                )
                count += 1 if created else 0
        self.stdout.write(f"薪资：新增 {count} 条（月份：{'、'.join(months)}）")

    def _create_notices(self):
        """创建公告。"""
        for title, content, pinned in NOTICES:
            Notice.objects.get_or_create(
                title=title,
                defaults={"content": content, "is_pinned": pinned},
            )
        self.stdout.write(f"公告：{len(NOTICES)} 条")

    def _create_tasks(self, employees):
        """创建任务并随机分配负责人。"""
        for level, title, detail in TASKS:
            Task.objects.get_or_create(
                title=title,
                defaults={
                    "level": level,
                    "detail": detail,
                    "owner": random.choice(employees),
                },
            )
        self.stdout.write(f"任务：{len(TASKS)} 条")

    def _create_accounts(self, employees):
        """创建部门管理员与普通员工测试账号，并关联员工档案。"""
        user_model = get_user_model()
        accounts = [
            ("manager", "部门管理员", employees[0]),
            ("employee", "普通员工", employees[1]),
        ]
        for username, role_title, employee in accounts:
            user, created = user_model.objects.get_or_create(username=username)
            if created:
                user.set_password("123456")
            role = Role.objects.filter(title=role_title).first()
            if role:
                user.roles.set([role])
            user.save()
            # 绑定账号与员工档案（一人一账号）
            if employee.user_id is None:
                employee.user = user
                employee.save(update_fields=["user"])
        self.stdout.write("测试账号：manager / 123456（部门管理员）、employee / 123456（普通员工）")
