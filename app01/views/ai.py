"""
AI 助手视图 - 集成到现有 HRMS
================================================
T2  generate_jd        → 智能生成招聘 JD（三段式提示词 + AJAX）
T3  knowledge_qa       → 制度知识库问答（SQL 关键词检索 + 上下文注入）
T4  data_review        → 数据智能点评（考勤/薪资数据注入提示词）
T5+T7 chat_page/api_chat/api_chat_stream → 多轮对话 + SSE 流式
"""
import json
import uuid
from django.http import JsonResponse, StreamingHttpResponse
from django.shortcuts import render
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from app01.utils.ai import LLM_CLIENT
from app01.models import Employee, Attendance, Salary, Knowledge, ChatHistory


# ============================================================
# T2: 智能生成招聘 JD
# ============================================================
def generate_jd(request):
    """页面: 输入岗位 → 三段式提示词生成 JD"""
    return render(request, 'app01/ai/generate_jd.html')


@csrf_exempt
def api_generate_jd(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'msg': '仅支持 POST'})
    position = request.POST.get('position', '').strip()
    if not position:
        return JsonResponse({'ok': False, 'msg': '请输入岗位名称'})
    if len(position) > 50:
        position = position[:50]

    # ---------- 三段式提示词 ----------
    system_prompt = (
        "你是一名资深的人力资源专家，擅长撰写专业、清晰、有吸引力的"
        "中文招聘 JD（职位描述）。请使用简洁的中文表达。"
    )
    user_prompt = f"""
【岗位名称】{position}

请按以下格式输出结构化的招聘 JD，每个模块都要有实质内容：

## 一、岗位职责
（列出 4-6 条该岗位的核心职责）

## 二、任职要求
（列出学历、经验、技能、软素质等要求，区分"必须"和"优先"）

## 三、薪资范围
（给出一个合理的月薪区间，说明是否包含绩效/年终奖）

## 四、加分项
（有哪些条件会让候选人更有竞争力）
"""
    reply = LLM_CLIENT.chat(user_prompt.strip(), system=system_prompt)
    return JsonResponse({'ok': True, 'position': position, 'jd': reply})


# ============================================================
# T3: 制度知识库问答
# ============================================================
def knowledge_qa(request):
    """页面: 展示知识库 + 问答入口"""
    kws = Knowledge.objects.all().order_by('category')
    return render(request, 'app01/ai/knowledge_qa.html', {'knowledges': kws})


@csrf_exempt
def api_knowledge_qa(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'msg': '仅支持 POST'})
    question = request.POST.get('question', '').strip()
    if not question:
        return JsonResponse({'ok': False, 'msg': '请输入问题'})
    if len(question) > 300:
        question = question[:300]

    # ---------- SQL 关键词检索（中文 n-gram 滑窗） ----------
    from django.db.models import Q
    keywords = []
    tokens = question.replace('？', ' ').replace('?', ' ') \
                     .replace('，', ' ').replace(',', ' ') \
                     .replace('。', ' ').replace('.', ' ') \
                     .replace('！', ' ').replace('!', ' ') \
                     .replace('：', ' ').replace(':', ' ') \
                     .split()
    for tok in tokens:
        tok = tok.strip()
        if len(tok) >= 2:
            keywords.append(tok)
        for n in (2, 3):
            for i in range(0, len(tok) - n + 1):
                sub = tok[i:i+n]
                if len(sub) >= 2 and sub not in keywords:
                    keywords.append(sub)

    qs = Knowledge.objects.none()
    if keywords:
        for kw in keywords:
            qs = qs | Knowledge.objects.filter(
                Q(title__icontains=kw) | Q(content__icontains=kw) | Q(category__icontains=kw)
            )
        qs = qs.distinct()[:5]

    if not qs.exists():
        return JsonResponse({
            'ok': True,
            'answer': '抱歉，我在公司制度知识库中没有找到相关内容，请咨询人力资源部。',
            'sources': [],
        })

    context_parts = []
    for i, k in enumerate(qs, 1):
        context_parts.append(f'[{i}. {k.category} - {k.title}]\n{k.content}')
    context_text = '\n\n'.join(context_parts)

    system_prompt = (
        "你是公司的员工手册问答助手。请严格根据下方【参考资料】回答员工的问题。"
        "如果参考资料中没有能够回答问题的内容，必须回答："
        "\"抱歉，当前知识库中暂无相关规定，请咨询人力资源部。\""
        "禁止编造资料中没有的信息。"
    )
    user_prompt = f"""
【参考资料】
{context_text}

【员工问题】{question}

请用简洁的中文回答。
"""
    answer = LLM_CLIENT.chat(user_prompt.strip(), system=system_prompt)
    return JsonResponse({
        'ok': True,
        'answer': answer,
        'sources': [{'category': k.category, 'title': k.title} for k in qs],
    })


# ============================================================
# T4: 数据智能点评
# ============================================================
def data_review(request):
    emps = Employee.objects.all().order_by('depart', 'name')
    months = Salary.objects.values_list('month', flat=True).distinct().order_by('-month')
    return render(request, 'app01/ai/data_review.html', {
        'employees': emps, 'months': months,
    })


@csrf_exempt
def api_data_review(request):
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'msg': '仅支持 POST'})
    emp_id = request.POST.get('employee_id', '')
    month = request.POST.get('month', '')
    if not emp_id or not month:
        return JsonResponse({'ok': False, 'msg': '请选择员工和月份'})
    try:
        emp = Employee.objects.get(pk=int(emp_id))
    except (Employee.DoesNotExist, ValueError):
        return JsonResponse({'ok': False, 'msg': '员工不存在'})

    # ---------- 考勤 ----------
    atts = Attendance.objects.filter(employee=emp, date__month=int(month.split('-')[1]))
    if atts.exists():
        status_count = {}
        for a in atts:
            key = a.get_status_display()
            status_count[key] = status_count.get(key, 0) + 1
        att_text = f"考勤状态分布: {status_count}，总打卡 {atts.count()} 天"
    else:
        att_text = '（该月暂无考勤记录）'

    # ---------- 薪资 ----------
    try:
        sal = Salary.objects.get(employee=emp, month=month)
        sal_text = (f"基本工资 {sal.base}，奖金 {sal.bonus}，扣款 {sal.deduction}，"
                    f"实发合计 {sal.total}")
    except Salary.DoesNotExist:
        sal_text = '（该月暂无薪资记录）'

    system_prompt = (
        "你是公司的 HR 数据分析师。请根据员工的考勤和薪资数据，"
        "用友好、专业、鼓励性的语气给出一句简短的数据点评或改进建议（50-100字）。"
        "不要使用生硬的套话，要具体、有针对性。"
    )
    user_prompt = f"""
【员工】{emp.name}，{emp.depart} / {emp.phone}
【月份】{month}
【考勤数据】{att_text}
【薪资数据】{sal_text}

请给出一句简洁的点评或改进建议。
"""
    reply = LLM_CLIENT.chat(user_prompt.strip(), system=system_prompt)
    return JsonResponse({
        'ok': True,
        'employee': emp.name,
        'month': month,
        'attendance': att_text,
        'salary': sal_text,
        'review': reply,
    })


# ============================================================
# T5+T7: 多轮对话
# ============================================================
def chat_page(request):
    return render(request, 'app01/ai/chat.html')


def _get_or_create_session(request):
    sid = request.COOKIES.get('chat_session') or request.GET.get('sid')
    if not sid:
        sid = uuid.uuid4().hex[:16]
    return sid


@csrf_exempt
def api_chat(request):
    """普通多轮对话"""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'msg': '仅支持 POST'})
    data = json.loads(request.body.decode('utf-8'))
    sid = data.get('session_id') or _get_or_create_session(request)
    user_msg = (data.get('message') or '').strip()
    if not user_msg:
        return JsonResponse({'ok': False, 'msg': '请输入消息'})
    if len(user_msg) > settings.LLM_MAX_INPUT_LEN:
        user_msg = user_msg[:settings.LLM_MAX_INPUT_LEN]

    history = list(ChatHistory.objects.filter(session_id=sid).order_by('created_at')[:20])
    system = ("你是公司的智能员工助手。可以回答公司制度、考勤、薪资、"
              "招聘 JD 生成等问题。回答要简洁、专业。")
    messages = [{'role': 'system', 'content': system}]
    for h in history:
        messages.append({'role': h.role, 'content': h.content})
    messages.append({'role': 'user', 'content': user_msg})

    reply = LLM_CLIENT.chat_with_history(messages)

    ChatHistory.objects.create(session_id=sid, role='user', content=user_msg)
    ChatHistory.objects.create(session_id=sid, role='assistant', content=reply)

    resp = JsonResponse({'ok': True, 'session_id': sid, 'reply': reply})
    resp.set_cookie('chat_session', sid, max_age=7 * 24 * 3600)
    return resp


@csrf_exempt
def api_chat_stream(request):
    """SSE 流式多轮对话（T7）"""
    if request.method != 'POST':
        return JsonResponse({'ok': False, 'msg': '仅支持 POST'})
    data = json.loads(request.body.decode('utf-8'))
    sid = data.get('session_id') or _get_or_create_session(request)
    user_msg = (data.get('message') or '').strip()
    if not user_msg:
        return JsonResponse({'ok': False, 'msg': '请输入消息'})
    if len(user_msg) > settings.LLM_MAX_INPUT_LEN:
        user_msg = user_msg[:settings.LLM_MAX_INPUT_LEN]

    history = list(ChatHistory.objects.filter(session_id=sid).order_by('created_at')[:20])
    system = ("你是公司的智能员工助手。可以回答公司制度、考勤、薪资、"
              "招聘 JD 生成等问题。回答要简洁、专业。")
    messages = [{'role': 'system', 'content': system}]
    for h in history:
        messages.append({'role': h.role, 'content': h.content})
    messages.append({'role': 'user', 'content': user_msg})

    ChatHistory.objects.create(session_id=sid, role='user', content=user_msg)

    def event_stream():
        full_reply = []
        prompt_for_stream = '\n\n'.join(
            f"【{m['role']}】{m['content']}" for m in messages[1:]
        )
        prompt_for_stream = f"{system}\n\n历史对话:\n{prompt_for_stream}\n\n最新用户:{user_msg}"
        for chunk in LLM_CLIENT.chat_stream(prompt_for_stream):
            full_reply.append(chunk)
            yield f"data: {json.dumps({'text': chunk}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True, 'session_id': sid}, ensure_ascii=False)}\n\n"
        ChatHistory.objects.create(
            session_id=sid, role='assistant', content=''.join(full_reply)
        )

    resp = StreamingHttpResponse(event_stream(),
                                 content_type='text/event-stream; charset=utf-8')
    resp['Cache-Control'] = 'no-cache'
    resp['X-Accel-Buffering'] = 'no'
    resp.set_cookie('chat_session', sid, max_age=7 * 24 * 3600)
    return resp
