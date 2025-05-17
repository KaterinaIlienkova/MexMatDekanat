from datetime import datetime
from sqlalchemy import desc, func
from typing import List, Optional, Tuple
from source.models import PersonalQuestion, User, StudentGroup, Student
from source.repositories.BaseRepository import BaseRepository


class PersonalQARepository(BaseRepository):


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


            new_question = PersonalQuestion(
                UserID=user_id,
                Question=question_text,
                Status='pending',
                Timestamp=datetime.now()
            )
            self.session.add(new_question)
            self.session.commit()
            return new_question.QuestionID

    # Методи для працівників деканату
    def get_pending_questions(self):
        """
        Отримує список всіх невідповідених запитань.

        Returns:
            Список об'єктів PersonalQuestion зі статусом 'pending'
        """
        pending_questions = self.session.query(PersonalQuestion).filter_by(Status='pending').all()
        return pending_questions

    def get_question_details(self, question_id: int):
            """
            Отримує детальну інформацію про запитання, включаючи дані про студента.

            Args:
                question_id: ID запитання

            Returns:
                Словник з інформацією про запитання та студента
            """
            question = self.session.query(PersonalQuestion).filter_by(QuestionID=question_id).first()

            if not question:
                return None

            # Отримуємо інформацію про користувача
            user = self.session.query(User).filter_by(UserID=question.UserID).first()

            # Якщо це студент, отримуємо додаткову інформацію
            student_info = None
            if user and user.Role == 'student':
                student = self.session.query(Student).filter_by(UserID=user.UserID).first()
                if student:
                    group = self.session.query(StudentGroup).filter_by(GroupID=student.GroupID).first()
                    student_info = {
                        'student_id': student.StudentID,
                        'group_name': group.GroupName if group else 'Невідома група'
                    }

            return {
                'question': question,
                'user': user,
                'student_info': student_info
            }

    def answer_question(self, question_id: int, answer_text: str, answered_by_id: int):
        """
        Зберігає відповідь на запитання та змінює його статус.

        Args:
            question_id: ID запитання
            answer_text: Текст відповіді
            answered_by_id: ID користувача, який відповідає

        Returns:
            True у разі успіху, False у разі невдачі
        """
        try:
                question = self.session.query(PersonalQuestion).filter_by(QuestionID=question_id).first()

                if not question:
                    return False

                question.Answer = answer_text
                question.Status = 'answered'
                question.AnsweredBy = answered_by_id

                self.session.commit()
                return True
        except Exception:
            return False

    def get_student_chat_id(self, question_id: int):
            """
            Отримує chat_id студента, який задав запитання, для відправки йому відповіді.

            Args:
                question_id: ID запитання

            Returns:
                chat_id студента або None
            """
            question = self.session.query(PersonalQuestion).filter_by(QuestionID=question_id).first()

            if not question:
                return None

            user = self.session.query(User).filter_by(UserID=question.UserID).first()

            if user and user.ChatID:
                return user.ChatID

            return None