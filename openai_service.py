"""Сервис для работы с OpenAI"""
import json
import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from config import settings


class OpenAIService:
    """Сервис для проверки сообщений через OpenAI"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"
        # Семафор для ограничения параллельных запросов (можно настроить)
        self.semaphore = asyncio.Semaphore(10)  # Максимум 10 параллельных запросов
    
    async def check_message(
        self,
        name: str,
        age: Optional[int],
        gender: Optional[str],
        mood: Optional[str],
        previous_messages: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Проверить сообщение через OpenAI используя эндпоинт /v1/responses
        
        Returns:
            {
                'response': str,  # Ответ от OpenAI
                'status': str     # 'ok' или 'restricted'
            }
        """
        async with self.semaphore:  # Ограничение параллельных запросов
            try:
                gender_normalized = (gender or "").strip().lower()
                if gender_normalized in {"женщина", "female", "woman", "girl", "f"}:
                    gender_value = "женщина"
                elif gender_normalized in {"мужчина", "male", "man", "boy", "m"}:
                    gender_value = "мужчина"
                else:
                    gender_value = "не указан"

                age_value = str(age) if age is not None else "не указан"

                mood_normalized = (mood or "").strip().lower()
                if mood_normalized in {"плохое", "плохой", "bad", "sad", "низкое"}:
                    mood_value = "плохое"
                elif mood_normalized in {"среднее", "нормальное", "normal", "okay", "ok"}:
                    mood_value = "среднее"
                elif mood_normalized in {"отличное", "хорошее", "great", "excellent", "perfect"}:
                    mood_value = "отличное"
                else:
                    mood_value = "не указано"

                # Формируем запрос к OpenAI API
                # Используем стандартный эндпоинт chat/completions с JSON schema
                previous_messages_list = previous_messages or []
                if previous_messages_list:
                    previous_messages_text = "\n".join(
                        f"{idx + 1}. {msg}" for idx, msg in enumerate(previous_messages_list)
                    )
                else:
                    previous_messages_text = "Сообщения отсутствуют."
                print(f"[OpenAIService] Previous approved messages:\n{previous_messages_text}")

                if previous_messages_list:
                    previous_messages_for_user = "\n".join(previous_messages_list)
                    previous_messages_user_section = (
                        f"\nПредыдущие сообщения для справки (не повторяй их):\n{previous_messages_for_user}"
                    )
                else:
                    previous_messages_user_section = ""

                payload = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                f"Предыдущие одобренные сообщения:\n{previous_messages_text}\n\n"
                                "Ты — модератор платформы творческого контента. "
                                "Отвечай строго в формате JSON с полями \"status\" и \"response\".\n\n"
                                "Правила модерации:\n"
                                "1. Если имя, пол или возраст содержат мат, ругательства, оскорбления, политику, "
                                "упоминания Украины, Крыма, темы СВО, войны, солдат, территориальной принадлежности — "
                                "сообщение отклоняется. В этом случае ответ:\n"
                                "{\n"
                                "  \"status\": \"restricted\",\n"
                                "  \"response\": \"Сообщение не прошло модерацию.\"\n"
                                "}\n"
                                "2. Если нарушений нет — сообщение одобряется, статус \"ok\". "
                                "В поле \"response\" сгенерируй обращение от Прохора согласно списку шаблонов.\n"
                                "Используй пол и настроение. Если пол или настроение не распознаны, выбери любой "
                                "подходящий шаблон и подстрой фразу под указанные данные. Важно! Немного измени фразу шаблона, но чтобы она была также коротка, была такой же темы, просто по-дргому сформулирована.\n"
                                "Важно! Не повторяй тексты предыдущих сообщений, подбирай свежую формулировку.\n\n"
                                "Шаблоны ответов:\n"
                                "### Женщины — плохое настроение\n"
                                "- [Имя], выключи тоску — у неё плохой вкус. Ваш Прохор.\n"
                                "- [Имя], выдохни и поправь корону. Ваш Прохор.\n"
                                "- [Имя], оформи отпуск — душе нужны каникулы. Ваш Прохор.\n"
                                "- [Имя], сегодня просто живи красиво — без объяснений. Ваш Прохор.\n"
                                "- [Имя], улыбнись — чудеса уже на подходе. Ваш Прохор.\n\n"
                                "### Женщины — среднее настроение\n"
                                "- [Имя], запланируй отпуск — и забудь пароль от почты. Ваш Прохор.\n"
                                "- [Имя], не спеши, звезда всегда появляется эффектно. Ваш Прохор.\n"
                                "- [Имя], сделай себе комплимент — он будет точнее всех. Ваш Прохор.\n"
                                "- [Имя], живи с изяществом, как ты умеешь. Ваш Прохор.\n"
                                "- [Имя], день серый? Надень настроение поярче. Ваш Прохор.\n"
                                "- [Имя], просто свети, даже без причин. Ваш Прохор.\n\n"
                                "### Женщины — отличное настроение\n"
                                "- [Имя], ты сегодня — праздник без повода. Ваш Прохор.\n"
                                "- [Имя], даже солнце взяло твой автограф. Ваш Прохор.\n"
                                "- [Имя], не скромничай — скромность скучна. Ваш Прохор.\n"
                                "- [Имя], держи темп — публика не дышит. Ваш Прохор.\n"
                                "- [Имя], блеск зафиксирован, не выключай. Ваш Прохор.\n"
                                "- [Имя], настроение божественное — оставь так. Ваш Прохор.\n\n"
                                "### Мужчины — плохое настроение\n"
                                "- [Имя], отдохни — подвиги подождут. Ваш Прохор.\n"
                                "- [Имя], грусть тебе не идёт — верни улыбку. Ваш Прохор.\n"
                                "- [Имя], всё пройдёт, даже дедлайн. Ваш Прохор.\n"
                                "- [Имя], сними тревогу и добавь уверенности. Ваш Прохор.\n"
                                "- [Имя], даже супергероям нужно полежать. Ваш Прохор.\n\n"
                                "### Мужчины — среднее настроение\n"
                                "- [Имя], живи красиво, даже без повода. Ваш Прохор.\n"
                                "- [Имя], добавь харизмы — день станет лучше. Ваш Прохор.\n"
                                "- [Имя], улыбнись, жизнь наблюдает. Ваш Прохор.\n"
                                "- [Имя], меньше дел, больше блеска. Ваш Прохор.\n"
                                "- [Имя], добавь света — миру понравится. Ваш Прохор.\n\n"
                                "### Мужчины — отличное настроение\n"
                                "- [Имя], ты сегодня — премьера, без дублей. Ваш Прохор.\n"
                                "- [Имя], блеск на максимуме — не ослепи зал. Ваш Прохор.\n"
                                "- [Имя], не скромничай — это не твой жанр. Ваш Прохор.\n"
                                "- [Имя], ты великолепен, без комментариев. Ваш Прохор.\n\n"
                                "Всегда подставляй имя пользователя на место [Имя]. "
                                "Если пол или настроение не указаны или не распознаны, выбери любой подходящий шаблон."
                            )
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Имя пользователя: {name}\n"
                                f"Пол: {gender_value}\n"
                                f"Возраст: {age_value}\n"
                                f"Настроение: {mood_value}"
                                f"{previous_messages_user_section}"
                            )
                        }
                    ],
                    "response_format": {
                        "type": "json_schema",
                        "json_schema": {
                            "name": "moderation_result",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "response": {
                                        "type": "string",
                                        "description": "Brief explanation of the moderation decision"
                                    },
                                    "status": {
                                        "type": "string",
                                        "enum": ["ok", "restricted"],
                                        "description": "Moderation status: 'ok' if message is approved, 'restricted' if rejected"
                                    }
                                },
                                "required": ["response", "status"],
                                "additionalProperties": False
                            },
                            "strict": True
                        }
                    }
                }
                
                # Отправляем запрос к OpenAI API
                async with aiohttp.ClientSession() as session:
                    headers = {
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                    
                    async with session.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    ) as response:
                        response_text = await response.text()
                        
                        if response.status != 200:
                            # Логируем ошибку для отладки
                            print(f"OpenAI API error: Status {response.status}")
                            print(f"Response: {response_text}")
                            raise Exception(f"OpenAI API error: {response.status} - {response_text}")
                        
                        try:
                            data = await response.json()
                        except json.JSONDecodeError:
                            # Если ответ не JSON, логируем и возвращаем ошибку
                            print(f"OpenAI API returned non-JSON response: {response_text}")
                            raise Exception(f"OpenAI API returned non-JSON response: {response_text}")
                        
                        # Извлекаем результат из стандартного ответа chat/completions
                        # Структура: data['choices'][0]['message']['content']
                        try:
                            content = data['choices'][0]['message']['content']
                            result = json.loads(content)
                        except (KeyError, IndexError, json.JSONDecodeError) as e:
                            # Логируем структуру ответа для отладки
                            print(f"Error parsing OpenAI response: {e}")
                            print(f"Response structure: {data}")
                            raise Exception(f"Failed to parse OpenAI response: {e}. Response: {data}")
                        
                        # Валидация структуры ответа
                        if result is None or not isinstance(result, dict):
                            raise ValueError(f"Invalid response format from OpenAI. Response: {data}")
                        
                        if 'response' not in result or 'status' not in result:
                            raise ValueError(f"Invalid response structure from OpenAI. Missing 'response' or 'status'. Got: {result}")
                        
                        if result['status'] not in ['ok', 'restricted']:
                            raise ValueError(f"Invalid status: {result['status']}. Expected 'ok' or 'restricted'")
                        
                        return result
                
            except json.JSONDecodeError as e:
                # Если OpenAI вернул не JSON, возвращаем ошибку
                return {
                    'response': f'Ошибка парсинга ответа: {str(e)}',
                    'status': 'restricted'
                }
            except Exception as e:
                # Обработка других ошибок
                return {
                    'response': f'Ошибка при проверке сообщения: {str(e)}',
                    'status': 'restricted'
                }


# Глобальный экземпляр сервиса
openai_service = OpenAIService(settings.openai_api_key)

