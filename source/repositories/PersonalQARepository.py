from datetime import datetime
from sqlalchemy import desc, func
from typing import List, Optional, Tuple
from source.models import PersonalQuestion, User

class PersonalQARepository:
    def __init__(self, get_session):
        self.get_session = get_session

    # Методи для студентів
    def create_question(self, user_id: int, question_text: str) -> int:
        """
        Створює нове персональне запитання від студента.

        Args:
            user_id: ID користувача, який створює запитання
            question_text: Текст запитання

        Returns:
            ID створеного запитання
        """


        with self.get_session() as session:
            new_question = PersonalQuestion(
                UserID=user_id,
                Question=question_text,
                Status='pending',
                Timestamp=datetime.now()
            )
            session.add(new_question)
            session.commit()
            return new_question.QuestionID

    def get_user_questions(self, user_id: int) -> List[dict]:
        """
        Отримує всі запитання конкретного користувача.

        Args:
            user_id: ID користувача

        Returns:
            Список запитань користувача з їх статусом та відповідями
        """


        with self.get_session() as session:
            questions = session.query(
                PersonalQuestion,
                User.UserName.label('answered_by_name')
            ).outerjoin(
                User,
                PersonalQuestion.AnsweredBy == User.UserID
            ).filter(
                PersonalQuestion.UserID == user_id
            ).order_by(
                desc(PersonalQuestion.Timestamp)
            ).all()

            result = []
            for q, answered_by in questions:
                result.append({
                    'question_id': q.QuestionID,
                    'question': q.Question,
                    'answer': q.Answer,
                    'status': q.Status,
                    'timestamp': q.Timestamp,
                    'answered_by': answered_by
                })

            return result

    # Методи для працівників деканату
    def get_pending_questions(self, limit: int = 50, offset: int = 0) -> Tuple[List[dict], int]:
        """
        Отримує список невідповідених запитань.

        Args:
            limit: Максимальна кількість запитань для повернення
            offset: Зміщення для пагінації

        Returns:
            Кортеж (список запитань, загальна кількість)
        """


        with self.get_session() as session:
            # Отримуємо загальну кількість запитань зі статусом 'pending'
            total_count = session.query(func.count(PersonalQuestion.QuestionID)) \
                .filter(PersonalQuestion.Status == 'pending') \
                .scalar()

            # Отримуємо запитання з обмеженням та зміщенням
            pending_questions = session.query(
                PersonalQuestion,
                User.UserName.label('student_name'),
                User.TelegramTag.label('student_telegram')
            ).join(
                User,
                PersonalQuestion.UserID == User.UserID
            ).filter(
                PersonalQuestion.Status == 'pending'
            ).order_by(
                PersonalQuestion.Timestamp
            ).limit(limit).offset(offset).all()

            result = []
            for q, student_name, student_telegram in pending_questions:
                result.append({
                    'question_id': q.QuestionID,
                    'student_id': q.UserID,
                    'student_name': student_name,
                    'student_telegram': student_telegram,
                    'question': q.Question,
                    'timestamp': q.Timestamp
                })

            return result, total_count

    def answer_question(self, question_id: int, staff_id: int, answer_text: str) -> bool:
        """
        Відповідає на запитання студента.

        Args:
            question_id: ID запитання
            staff_id: ID працівника деканату, який відповідає
            answer_text: Текст відповіді

        Returns:
            True якщо відповідь успішно збережена, False в іншому випадку
        """


        with self.get_session() as session:
            question = session.query(PersonalQuestion) \
                .filter(PersonalQuestion.QuestionID == question_id) \
                .first()

            if not question or question.Status != 'pending':
                return False

            question.Answer = answer_text
            question.Status = 'answered'
            question.AnsweredBy = staff_id
            session.commit()
            return True

    def get_question_details(self, question_id: int) -> Optional[dict]:
        """
        Отримує детальну інформацію про конкретне запитання.

        Args:
            question_id: ID запитання

        Returns:
            Деталі запитання або None, якщо запитання не знайдено
        """


        with self.get_session() as session:
            result = session.query(
                PersonalQuestion,
                User.UserName.label('student_name'),
                User.TelegramTag.label('student_telegram'),
                User.ChatID.label('student_chat_id')
            ).join(
                User,
                PersonalQuestion.UserID == User.UserID
            ).filter(
                PersonalQuestion.QuestionID == question_id
            ).first()

            if not result:
                return None

            question, student_name, student_telegram, student_chat_id = result

            # Отримуємо інформацію про працівника, який відповів (якщо є)
            answered_by_name = None
            if question.AnsweredBy:
                staff = session.query(User.UserName) \
                    .filter(User.UserID == question.AnsweredBy) \
                    .first()
                if staff:
                    answered_by_name = staff[0]

            return {
                'question_id': question.QuestionID,
                'student_id': question.UserID,
                'student_name': student_name,
                'student_telegram': student_telegram,
                'student_chat_id': student_chat_id,
                'question': question.Question,
                'answer': question.Answer,
                'status': question.Status,
                'timestamp': question.Timestamp,
                'answered_by_id': question.AnsweredBy,
                'answered_by_name': answered_by_name
            }