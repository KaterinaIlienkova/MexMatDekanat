
from sqlalchemy.exc import SQLAlchemyError

from source.config import logger
from source.models import User, StudentGroup, Student, Department, Teacher, Specialty, DocumentRequest, CourseEnrollment
from typing import Optional, List


class AuthRepository:
    def __init__(self, get_session):
        self.get_session = get_session

    def get_user_by_telegram_tag(self, telegram_tag: str) -> User | None:
        try:
            with self.get_session() as session:
                return session.query(User).filter_by(TelegramTag=telegram_tag).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error when fetching user by tag: {e}")
            return None

    def get_user_by_chat_id(self, chat_id: int) -> User | None:
        try:
            with self.get_session() as session:
                return session.query(User).filter_by(ChatID=chat_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error when fetching user by chat_id: {e}")
            return None

    def update_chat_id(self, user: User, chat_id: int) -> None:
        try:
            with self.get_session() as session:
                user_in_db = session.query(User).filter_by(UserID=user.UserID).first()
                if user_in_db:
                    user_in_db.ChatID = chat_id
                    session.commit()
        except SQLAlchemyError as e:
            logger.error(f"Database error when updating chat ID: {e}")

    def add_user(self, username: str, telegram_tag: str, role: str, phone_number: str,
                 chat_id: Optional[int] = None, is_confirmed: bool = False) -> Optional[User]:
        """Додає нового користувача в базу даних."""
        try:
            with self.get_session() as session:
                existing_user = session.query(User).filter_by(TelegramTag=telegram_tag).first()
                if existing_user:
                    return None  # Користувач вже існує

                new_user = User(
                    UserName=username,
                    TelegramTag=telegram_tag,
                    Role=role,
                    PhoneNumber=phone_number,
                    ChatID=chat_id,
                    IsConfirmed=is_confirmed
                )

                session.add(new_user)
                session.flush()  # Отримуємо UserID не комітячи

                # Create a copy of relevant information to return
                user_copy = User(
                    UserID=new_user.UserID,
                    UserName=new_user.UserName,
                    TelegramTag=new_user.TelegramTag,
                    Role=new_user.Role,
                    PhoneNumber=new_user.PhoneNumber,
                    ChatID=new_user.ChatID,
                    IsConfirmed=new_user.IsConfirmed
                )

                session.commit()
                return user_copy
        except SQLAlchemyError as e:
            logger.error(f"Database error when adding user: {e}")
            return None


    def get_specialty_by_name(self, specialty_name: str) -> Optional[Specialty]:
        """Отримує спеціальність за назвою."""
        try:
            with self.get_session() as session:
                return session.query(Specialty).filter_by(Name=specialty_name).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting specialty by name: {e}")
            return None

    def add_specialty(self, specialty_name: str) -> Optional[Specialty]:
        """Додає нову спеціальність."""
        try:
            with self.get_session() as session:
                new_specialty = Specialty(Name=specialty_name)
                session.add(new_specialty)
                session.commit()
                return new_specialty
        except SQLAlchemyError as e:
            logger.error(f"Database error when adding specialty: {e}")
            return None

    def get_student_group_by_name(self, group_name: str) -> Optional[StudentGroup]:
        """Отримує групу за назвою."""
        try:
            with self.get_session() as session:
                return session.query(StudentGroup).filter_by(GroupName=group_name).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting student group by name: {e}")
            return None

    def get_student_by_user_id(self, user_id: int) -> Optional[Student]:
        """Отримує запис студента за ID користувача."""
        try:
            with self.get_session() as session:
                return session.query(Student).filter_by(UserID=user_id).first()
        except SQLAlchemyError as e:
            logger.exception(f"Помилка при отриманні студента: {e}")
            return None


    def add_student_group(self, group_name: str, specialty_id: int) -> Optional[int]:
        """Додає нову групу та повертає її ID."""
        try:
            with self.get_session() as session:
                new_group = StudentGroup(
                    GroupName=group_name,
                    SpecialtyID=specialty_id
                )
                session.add(new_group)
                session.commit()
                session.refresh(new_group)  # щоб отримати GroupID
                return new_group.GroupID
        except SQLAlchemyError as e:
            logger.error(f"Database error when adding student group: {e}")
            return None


    def add_student(self, user_id: int, group_id: int, admission_year: int) -> Optional[Student]:
        """Додає запис студента для існуючого користувача."""
        try:
            with self.get_session() as session:
                # Перевіряємо чи існує користувач
                user = session.query(User).filter_by(UserID=user_id).first()
                if not user:
                    logger.error(f"User with ID {user_id} not found")
                    return None

                # Перевіряємо чи вже є запис студента
                existing_student = session.query(Student).filter_by(UserID=user_id).first()
                if existing_student:
                    logger.warning(f"Student record already exists for user ID {user_id}")
                    return existing_student

                # Створюємо запис студента
                new_student = Student(
                    UserID=user_id,
                    GroupID=group_id,
                    AdmissionYear=admission_year
                )

                session.add(new_student)
                session.commit()
                return new_student
        except SQLAlchemyError as e:
            logger.error(f"Database error when adding student: {e}")
            return None

    def get_department_by_name(self, department_name: str) -> Optional[Department]:
        """Отримує департамент за назвою."""
        try:
            with self.get_session() as session:
                return session.query(Department).filter_by(Name=department_name).first()
        except SQLAlchemyError as e:
            logger.error(f"Database error when getting department by name: {e}")
            return None

    def add_department(self, department_name: str) -> Optional[Department]:
        """Додає новий департамент."""
        try:
            with self.get_session() as session:
                new_department = Department(Name=department_name)
                session.add(new_department)
                session.commit()
                return new_department
        except SQLAlchemyError as e:
            logger.error(f"Database error when adding department: {e}")
            return None

    def add_teacher(self, user_id: int, email: str, department_id: int) -> Optional[Teacher]:
        """Додає запис викладача для існуючого користувача."""
        try:
            with self.get_session() as session:
                # Перевіряємо чи існує користувач
                user = session.query(User).filter_by(UserID=user_id).first()
                if not user:
                    logger.error(f"User with ID {user_id} not found")
                    return None

                # Перевіряємо чи вже є запис викладача
                existing_teacher = session.query(Teacher).filter_by(UserID=user_id).first()
                if existing_teacher:
                    logger.warning(f"Teacher record already exists for user ID {user_id}")
                    return existing_teacher

                # Створюємо запис викладача
                new_teacher = Teacher(
                    UserID=user_id,
                    Email=email,
                    DepartmentID=department_id
                )

                session.add(new_teacher)
                session.commit()
                return new_teacher
        except SQLAlchemyError as e:
            logger.error(f"Database error when adding teacher: {e}")
            return None




    def update_user_field(self, telegram_tag, field, new_value):
        """Оновлює вказане поле користувача."""
        with self.get_session() as session:
            try:
                user = session.query(User).filter_by(TelegramTag=telegram_tag).first()
                if not user:
                    return False, "Користувача не знайдено"

                if field == "name":
                    user.UserName = new_value
                elif field == "phone":
                    user.PhoneNumber = new_value
                elif field == "year":
                    student = session.query(Student).filter_by(UserID=user.UserID).first()
                    if student:
                        try:
                            year = int(new_value)
                            student.AdmissionYear = year
                        except ValueError:
                            return False, "Рік вступу повинен бути числом"
                    else:
                        return False, "Цей користувач не є студентом"
                elif field == "group":
                    student = session.query(Student).filter_by(UserID=user.UserID).first()
                    if student:
                        # Спочатку перевіряємо, чи існує група з таким ім'ям
                        group = session.query(StudentGroup).filter_by(GroupName=new_value).first()
                        if group:
                            student.GroupID = group.GroupID
                        else:
                            # Якщо введено ID групи замість назви
                            try:
                                group_id = int(new_value)
                                group = session.query(StudentGroup).filter_by(GroupID=group_id).first()
                                if group:
                                    student.GroupID = group_id
                                else:
                                    return False, f"Групу з ID {group_id} не знайдено"
                            except ValueError:
                                return False, "Такої групи не існує"
                    else:
                        return False, "Цей користувач не є студентом"
                else:
                    return False, f"Невідоме поле: {field}"

                session.commit()
                return True, "Поле успішно оновлено"
            except SQLAlchemyError as e:
                session.rollback()
                return False, str(e)

    def get_student_info(self, user_id):
        """Отримує інформацію про студента."""
        with self.get_session() as session:
            student = session.query(Student).filter_by(UserID=user_id).first()
            if student:
                group = session.query(StudentGroup).filter_by(GroupID=student.GroupID).first()
                group_name = group.GroupName if group else "Невідома"

                # Отримуємо спеціальність через зв'язок групи
                specialty_name = "Невідома"
                if group and group.specialty:
                    specialty_name = group.specialty.Name

                return {
                    'group_name': group_name,
                    'admission_year': student.AdmissionYear,
                    'specialty': specialty_name
                }
            return None



    def get_unconfirmed_users(self, role=None):
            """Отримує список непідтверджених користувачів з можливістю фільтрації за роллю."""
            with self.get_session() as session:
                query = session.query(User).filter(User.IsConfirmed == False)

                if role:
                    query = query.filter(User.Role == role)

                users = query.all()
                return users

    def get_unconfirmed_students_with_details(self):
        """Отримує список непідтверджених студентів з детальною інформацією."""
        with self.get_session() as session:
            result = session.query(
                User,
                Student,
                StudentGroup
            ).join(
                Student, User.UserID == Student.UserID
            ).join(
                StudentGroup, Student.GroupID == StudentGroup.GroupID
            ).filter(
                User.IsConfirmed == False,
                User.Role == 'student'
            ).all()

            return result

    def confirm_user(self, user_id):
        """Підтверджує користувача."""
        with self.get_session() as session:
            user = session.query(User).filter(User.UserID == user_id).first()
            if user:
                user.IsConfirmed = True
                session.commit()
                return True
            return False

    def delete_user(self, user_id):
        """Видаляє користувача."""
        with self.get_session() as session:
            user = session.query(User).filter(User.UserID == user_id).first()
            if user:
                # Якщо це студент, спочатку видалимо пов'язані записи
                if user.Role == 'student':
                    student = session.query(Student).filter(Student.UserID == user_id).first()
                    if student:
                        # Видалення пов'язаних записів курсів та заявок на документи
                        session.query(CourseEnrollment).filter(CourseEnrollment.StudentID == student.StudentID).delete()
                        session.query(DocumentRequest).filter(DocumentRequest.StudentID == student.StudentID).delete()
                        session.delete(student)

                # Якщо це викладач, видалимо його записи
                elif user.Role == 'teacher':
                    teacher = session.query(Teacher).filter(Teacher.UserID == user_id).first()
                    if teacher:
                        session.delete(teacher)

                # Видаляємо основний запис користувача
                session.delete(user)
                session.commit()
                return True
            return False

    def update_student_info(self, user_id, update_data):
        """Оновлює інформацію про студента."""
        with self.get_session() as session:
            try:
                # Оновлюємо основну інформацію користувача
                user = session.query(User).filter(User.UserID == user_id).first()
                if not user or user.Role != 'student':
                    return False

                if 'username' in update_data:
                    user.UserName = update_data['username']
                if 'phone_number' in update_data:
                    user.PhoneNumber = update_data['phone_number']
                if 'telegram_tag' in update_data:
                    # Перевірка унікальності telegram_tag
                    existing_user = session.query(User).filter(
                        User.TelegramTag == update_data['telegram_tag'],
                        User.UserID != user_id
                    ).first()

                    if existing_user:
                        return False
                    user.TelegramTag = update_data['telegram_tag']

                # Оновлюємо інформацію студента
                student = session.query(Student).filter(Student.UserID == user_id).first()
                if student:
                    if 'group_id' in update_data:
                        student.GroupID = update_data['group_id']
                    if 'admission_year' in update_data:
                        student.AdmissionYear = update_data['admission_year']

                session.commit()
                return True
            except Exception as e:
                session.rollback()
                logger.error(f"Error updating student info: {e}")
                return False


    def get_student_groups(self):
        """Отримує список всіх груп студентів."""
        with self.get_session() as session:
            groups = session.query(StudentGroup).all()
            return groups

    def get_admission_years(self):
        """Отримує список унікальних років вступу студентів."""
        with self.get_session() as session:
            years = session.query(Student.AdmissionYear).distinct().all()
            return [year[0] for year in years]

    def get_groups_by_admission_year(self, admission_year):
        """Отримує список груп студентів за роком вступу."""
        with self.get_session() as session:
            groups = session.query(StudentGroup.GroupName) \
                .join(Student, Student.GroupID == StudentGroup.GroupID) \
                .filter(Student.AdmissionYear == admission_year) \
                .distinct() \
                .all()
            return [group[0] for group in groups]

    def get_departments(self):
        """Отримує список всіх кафедр."""
        with self.get_session() as session:
            departments = session.query(Department.Name).all()
            return [dept[0] for dept in departments]

    def get_teachers_by_department(self, department_name):
        """Отримує список викладачів із конкретної кафедри."""
        with self.get_session() as session:
            teachers = session.query(User.UserID, User.UserName, User.PhoneNumber, Teacher.Email) \
                .join(Teacher, User.UserID == Teacher.UserID) \
                .join(Department, Teacher.DepartmentID == Department.DepartmentID) \
                .filter(Department.Name == department_name) \
                .all()

            result = []
            for teacher in teachers:
                result.append({
                    'user_id': teacher[0],
                    'name': teacher[1],
                    'phone': teacher[2],
                    'email': teacher[3]
                })
            return result

    def get_students_by_group_and_course(self, group_name, admission_year):
        """Отримує список студентів із конкретної групи та року вступу."""
        with self.get_session() as session:
            students = session.query(User.UserID, User.UserName, User.PhoneNumber) \
                .join(Student, User.UserID == Student.UserID) \
                .join(StudentGroup, Student.GroupID == StudentGroup.GroupID) \
                .filter(StudentGroup.GroupName == group_name, Student.AdmissionYear == admission_year) \
                .all()

            result = []
            for student in students:
                result.append({
                    'user_id': student[0],
                    'name': student[1],
                    'phone': student[2]
                })
            return result

    def get_user_info(self, user_id):
        """Отримує детальну інформацію про користувача (студента або викладача)."""
        with self.get_session() as session:
            # Спочатку отримуємо базову інформацію про користувача
            user = session.query(User).filter(User.UserID == user_id).first()

            if not user:
                return None

            result = {
                'user_id': user.UserID,
                'name': user.UserName,
                'phone': user.PhoneNumber,
                'telegram_tag': user.TelegramTag,
                'role': user.Role
            }

            # Додаємо специфічну інформацію в залежності від ролі
            if user.Role == 'student':
                student_info = session.query(Student, StudentGroup) \
                    .join(StudentGroup, Student.GroupID == StudentGroup.GroupID) \
                    .filter(Student.UserID == user_id) \
                    .first()

                if student_info:
                    student, group = student_info
                    result.update({
                        'student_id': student.StudentID,
                        'group': group.GroupName,
                        'course': student.AdmissionYear
                    })

            elif user.Role == 'teacher':
                teacher_info = session.query(Teacher, Department) \
                    .join(Department, Teacher.DepartmentID == Department.DepartmentID) \
                    .filter(Teacher.UserID == user_id) \
                    .first()

                if teacher_info:
                    teacher, department = teacher_info
                    result.update({
                        'teacher_id': teacher.TeacherID,
                        'email': teacher.Email,
                        'department': department.Name
                    })

            return result