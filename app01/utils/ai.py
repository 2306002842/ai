"""
T1: LLMClient 统一封装 - OpenAI 兼容接口
对外方法:
  chat(prompt, system=None) -> str          单轮对话
  chat_with_history(messages) -> str        多轮对话（T5）
  chat_stream(prompt, system=None)          流式生成器（T7）
所有配置从 settings 读取（环境变量），禁止硬编码。
任何异常都返回友好提示，不抛出（T6 健壮性）。
"""
import json
import time
import requests
from django.conf import settings


class LLMClient:
    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL.rstrip('/')
        self.model = settings.LLM_MODEL
        self.timeout = settings.LLM_TIMEOUT

    def _post(self, url, headers, payload, stream=False, retries=3):
        """上游 5xx 多为瞬时过载，做有限次退避重试"""
        last = None
        for attempt in range(retries):
            resp = requests.post(url, headers=headers, json=payload,
                                 timeout=self.timeout, stream=stream)
            if resp.status_code < 500:
                return resp
            last = resp
            if stream:
                resp.close()
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
        return last

    @staticmethod
    def _err(resp):
        try:
            body = resp.text[:200].replace('\n', ' ')
        except Exception:
            body = ''
        return f'❌ 大模型服务返回 {resp.status_code}（已重试 3 次）：{body}'

    # ---------- T1: 基础单轮 ----------
    def chat(self, prompt: str, system: str = None) -> str:
        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})
        return self.chat_with_history(messages)

    # ---------- T5: 多轮对话 ----------
    def chat_with_history(self, messages: list) -> str:
        if not self.api_key:
            return '⚠️ 未配置 LLM_API_KEY，请在 .env 文件中填写后重试。'

        url = f'{self.base_url}/chat/completions'
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': 0.7,
        }

        try:
            resp = self._post(url, headers, payload)
            if resp.status_code >= 500:
                return self._err(resp)
            resp.raise_for_status()
            data = resp.json()
            return data['choices'][0]['message']['content'].strip()
        except requests.exceptions.Timeout:
            return f'⏰ 请求超时（{self.timeout}s），请稍后再试。'
        except requests.exceptions.ConnectionError:
            return '🌐 无法连接到大模型服务，请检查网络或 BASE_URL 配置。'
        except requests.exceptions.HTTPError as e:
            return f'❌ API 返回错误: {e.response.status_code} {e.response.reason}'
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            return f'❌ 解析 API 响应失败: {e}'
        except Exception as e:
            return f'❌ 未知错误: {e}'

    # ---------- T7: SSE 流式 ----------
    def chat_stream(self, prompt: str, system: str = None):
        if not self.api_key:
            yield '⚠️ 未配置 LLM_API_KEY。'
            return

        messages = []
        if system:
            messages.append({'role': 'system', 'content': system})
        messages.append({'role': 'user', 'content': prompt})

        url = f'{self.base_url}/chat/completions'
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
        }
        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': 0.7,
            'stream': True,
        }

        try:
            resp = self._post(url, headers, payload, stream=True)
            if resp.status_code >= 500:
                yield self._err(resp)
                return
            resp.raise_for_status()
            # 上游 SSE 响应头未带 charset，requests 会默认按 ISO-8859-1 解码导致中文乱码
            resp.encoding = 'utf-8'
            for raw_line in resp.iter_lines(decode_unicode=True):
                if not raw_line or not raw_line.startswith('data:'):
                    continue
                data_str = raw_line[5:].strip()
                if data_str == '[DONE]':
                    break
                try:
                    data = json.loads(data_str)
                    delta = data['choices'][0].get('delta', {})
                    chunk = delta.get('content', '')
                    if chunk:
                        yield chunk
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
        except requests.exceptions.Timeout:
            yield f'\n⏰ 请求超时（{self.timeout}s）。'
        except requests.exceptions.ConnectionError:
            yield '\n🌐 网络连接失败。'
        except requests.exceptions.HTTPError as e:
            yield '\n' + self._err(e.response)
        except Exception as e:
            yield f'\n❌ 流式请求失败: {e}'


LLM_CLIENT = LLMClient()
