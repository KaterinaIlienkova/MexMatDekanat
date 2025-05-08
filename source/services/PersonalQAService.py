
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta

from source.repositories import PersonalQARepository


class PersonalQAService:
    def __init__(self, pqa_repository: PersonalQARepository):
        self.pqa_repository = pqa_repository


    # Методи для студентів
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

    def get_student_questions(self, user_id: int) -> Dict[str, Any]:
        """
        Отримує всі запитання студента з їх статусом.

        Args:
            user_id: ID користувача (студента)

        Returns:
            Словник з результатом операції та списком запитань
        """
        try:
            questions = self.pqa_repository.get_user_questions(user_id)

            # Групуємо запитання за статусом для зручнішого відображення
            pending_questions = []
            answered_questions = []

            for q in questions:
                if q['status'] == 'pending':
                    pending_questions.append(q)
                else:
                    answered_questions.append(q)

            return {
                'success': True,
                'pending_questions': pending_questions,
                'answered_questions': answered_questions,
                'total_count': len(questions)
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Помилка при отриманні запитань: {str(e)}'
            }

    # Методи для працівників деканату
    def get_questions_for_staff(self, page: int = 1, per_page: int = 10) -> Dict[str, Any]:
        """
        Отримує список невідповідених запитань для працівників деканату з пагінацією.

        Args:
            page: Номер сторінки (починається з 1)
            per_page: Кількість запитань на сторінці

        Returns:
            Словник з результатом операції та списком запитань
        """
        try:
            offset = (page - 1) * per_page
            questions, total_count = self.pqa_repository.get_pending_questions(
                limit=per_page,
                offset=offset
            )

            # Додаємо форматування даних для відображення
            for q in questions:
                # Форматуємо timestamp для зручнішого відображення
                q['formatted_date'] = q['timestamp'].strftime('%d.%m.%Y %H:%M')

                # Додаємо скорочений текст запитання для превью
                if len(q['question']) > 100:
                    q['short_question'] = q['question'][:97] + '...'
                else:
                    q['short_question'] = q['question']

            # Розраховуємо кількість сторінок
            total_pages = (total_count + per_page - 1) // per_page

            return {
                'success': True,
                'questions': questions,
                'pagination': {
                    'current_page': page,
                    'total_pages': total_pages,
                    'per_page': per_page,
                    'total_count': total_count
                }
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Помилка при отриманні списку запитань: {str(e)}'
            }

    def provide_answer(self, question_id: int, staff_id: int, answer_text: str) -> Dict[str, Any]:
        """
        Обробляє відповідь на запитання від працівника деканату.

        Args:
            question_id: ID запитання
            staff_id: ID працівника деканату
            answer_text: Текст відповіді

        Returns:
            Словник з результатом операції
        """
        if not answer_text or len(answer_text.strip()) < 5:
            return {
                'success': False,
                'message': 'Відповідь повинна містити щонайменше 5 символів'
            }

        try:
            # Отримуємо деталі запитання перед відповіддю
            question_details = self.pqa_repository.get_question_details(question_id)

            if not question_details:
                return {
                    'success': False,
                    'message': 'Запитання не знайдено'
                }

            if question_details['status'] != 'pending':
                return {
                    'success': False,
                    'message': 'На це запитання вже надано відповідь'
                }

            # Надаємо відповідь
            success = self.pqa_repository.answer_question(question_id, staff_id, answer_text)

            if not success:
                return {
                    'success': False,
                    'message': 'Не вдалося зберегти відповідь'
                }

            # Отримуємо оновлені деталі запитання
            updated_details = self.pqa_repository.get_question_details(question_id)

            return {
                'success': True,
                'message': 'Відповідь успішно надано',
                'question_details': updated_details,
                'student_notification': {
                    'chat_id': question_details['student_chat_id'],
                    'message': f'На ваше запитання надійшла відповідь від деканату!\n\nЗапитання: {question_details["question"][:50]}...\n\nВідповідь: {answer_text[:100]}...'
                }
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Помилка при наданні відповіді: {str(e)}'
            }

    def get_question_with_context(self, question_id: int) -> Dict[str, Any]:
        """
        Отримує запитання з контекстом для відповіді.

        Args:
            question_id: ID запитання

        Returns:
            Словник з деталями запитання та контекстом
        """
        try:
            question = self.pqa_repository.get_question_details(question_id)

            if not question:
                return {
                    'success': False,
                    'message': 'Запитання не знайдено'
                }

            # Визначаємо, чи довго очікує запитання на відповідь
            waiting_time = datetime.now() - question['timestamp']
            is_urgent = waiting_time > timedelta(days=3)

            # Форматуємо час очікування
            days = waiting_time.days
            hours = waiting_time.seconds // 3600
            minutes = (waiting_time.seconds % 3600) // 60

            if days > 0:
                waiting_time_str = f"{days} днів, {hours} годин"
            elif hours > 0:
                waiting_time_str = f"{hours} годин, {minutes} хвилин"
            else:
                waiting_time_str = f"{minutes} хвилин"

            return {
                'success': True,
                'question': question,
                'context': {
                    'waiting_time': waiting_time_str,
                    'is_urgent': is_urgent,
                    'formatted_date': question['timestamp'].strftime('%d.%m.%Y %H:%M')
                }
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Помилка при отриманні запитання: {str(e)}'
            }
