
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta

from source.repositories import PersonalQARepository


class PersonalQAService:
    def __init__(self, pqa_repository: PersonalQARepository):
        self.pqa_repository = pqa_repository


    def submit_question(self, user_id: int, question_text: str) -> Dict[str, Any]:
        """
        Обробляє подання нового запитання студентом.

        Args:
            user_id: ID користувача (студента)
            question_text: Текст запитання

        Returns:
            Словник з результатом операції
        """
        if not question_text or len(question_text.strip()) < 10:
            return {
                'success': False,
                'message': 'Запитання повинно містити щонайменше 10 символів'
            }

        try:
            question_id = self.pqa_repository.create_question(user_id, question_text)
            return {
                'success': True,
                'message': 'Запитання успішно створено',
                'question_id': question_id
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Помилка при створенні запитання: {str(e)}'
            }

    def get_pending_questions(self) -> List[Dict[str, Any]]:
        """
        Отримує список невідповідених запитань для працівників деканату.

        Returns:
            Список з інформацією про запитання
        """
        try:
            pending_questions = self.pqa_repository.get_pending_questions()

            # Формуємо скорочений список для відображення
            questions_list = []
            for q in pending_questions:
                # Скорочуємо текст запитання для відображення на кнопці
                short_text = q.Question[:40] + "..." if len(q.Question) > 40 else q.Question

                questions_list.append({
                    'id': q.QuestionID,
                    'short_text': short_text,
                    'timestamp': q.Timestamp
                })

            return questions_list
        except Exception as e:
            return []

    def get_question_details(self, question_id: int) -> Dict[str, Any]:
        """
        Отримує детальну інформацію про запитання для відображення працівнику деканату.

        Args:
            question_id: ID запитання

        Returns:
            Словник з детальною інформацією або None
        """
        try:
            details = self.pqa_repository.get_question_details(question_id)

            if not details:
                return None

            question = details['question']
            user = details['user']
            student_info = details['student_info']

            # Форматуємо дату та час
            formatted_time = question.Timestamp.strftime("%d.%m.%Y %H:%M")

            result = {
                'id': question.QuestionID,
                'question_text': question.Question,
                'timestamp': formatted_time,
                'user_name': user.UserName if user else "Невідомий користувач",
                'telegram_tag': user.TelegramTag if user else "",
            }

            # Додаємо інформацію про групу студента, якщо доступна
            if student_info:
                result['group'] = student_info['group_name']

            return result
        except Exception as e:
            return None

    def answer_question(self, question_id: int, answer_text: str, staff_id: int) -> Dict[str, Any]:
        """
        Зберігає відповідь на запитання.

        Args:
            question_id: ID запитання
            answer_text: Текст відповіді
            staff_id: ID працівника деканату

        Returns:
            Словник з результатом операції
        """
        if not answer_text or len(answer_text.strip()) < 5:
            return {
                'success': False,
                'message': 'Відповідь повинна містити щонайменше 5 символів'
            }

        try:
            # Зберігаємо відповідь
            result = self.pqa_repository.answer_question(question_id, answer_text, staff_id)

            if not result:
                return {
                    'success': False,
                    'message': 'Не вдалося зберегти відповідь'
                }

            # Отримуємо chat_id студента для відправки повідомлення
            student_chat_id = self.pqa_repository.get_student_chat_id(question_id)

            return {
                'success': True,
                'message': 'Відповідь успішно збережена',
                'student_chat_id': student_chat_id
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Помилка при збереженні відповіді: {str(e)}'
            }