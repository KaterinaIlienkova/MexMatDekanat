from sqlalchemy import Column, Integer, String, ForeignKey, Enum, BigInteger, Text, TIMESTAMP, Boolean
from sqlalchemy.orm import relationship
from source.database import Base


class User(Base):
    __tablename__ = 'users'

    UserID = Column(Integer, primary_key=True, autoincrement=True)
    UserName = Column(String(100), nullable=False)
    TelegramTag = Column(String(50), nullable=False, unique=True)
    Role = Column(Enum('student', 'teacher', 'dean_office'), nullable=False)
    PhoneNumber = Column(String(15), nullable=True)
    ChatID = Column(BigInteger, nullable=True)
    IsConfirmed = Column(Boolean, default=False)

    students = relationship("Student", back_populates="user", uselist=False)
    teachers = relationship("Teacher", back_populates="user", uselist=False)
    dean_office_staff = relationship("DeanOfficeStaff", back_populates="user", uselist=False)


class Student(Base):
    __tablename__ = 'students'

    StudentID = Column(Integer, primary_key=True, autoincrement=True)
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    GroupID = Column(Integer, ForeignKey('studentgroups.GroupID'), nullable=False)
    AdmissionYear = Column(Integer, nullable=False)

    user = relationship("User", back_populates="students")
    group = relationship("StudentGroup", back_populates="students")
    document_requests = relationship("DocumentRequest", back_populates="student")
    course_enrollments = relationship("CourseEnrollment", back_populates="student")


class Teacher(Base):
    __tablename__ = 'teachers'

    TeacherID = Column(Integer, primary_key=True, autoincrement=True)
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    Email = Column(String(100), nullable=False)
    DepartmentID = Column(Integer, ForeignKey('departments.DepartmentID'))

    user = relationship("User", back_populates="teachers")
    department = relationship("Department", back_populates="teachers")


class DeanOfficeStaff(Base):
    __tablename__ = 'deanofficestaff'

    StaffID = Column(Integer, primary_key=True, autoincrement=True)
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    Position = Column(String(100), nullable=False)

    user = relationship("User", back_populates="dean_office_staff")


class Department(Base):
    __tablename__ = 'departments'

    DepartmentID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String(100), nullable=False)

    teachers = relationship("Teacher", back_populates="department")


class StudentGroup(Base):
    __tablename__ = 'studentgroups'

    GroupID = Column(Integer, primary_key=True, autoincrement=True)
    GroupName = Column(String(50), nullable=False, unique=True)
    SpecialtyID = Column(Integer, ForeignKey('specialties.SpecialtyID'))

    specialty = relationship("Specialty", back_populates="groups")
    students = relationship("Student", back_populates="group")


class Specialty(Base):
    __tablename__ = 'specialties'

    SpecialtyID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String(100), nullable=False)

    groups = relationship("StudentGroup", back_populates="specialty")


class Course(Base):
    __tablename__ = 'courses'

    CourseID = Column(Integer, primary_key=True, autoincrement=True)
    Name = Column(String(100), nullable=False)
    StudyPlatform = Column(String(100), nullable=True)
    MeetingLink = Column(String(255), nullable=True)
    TeacherID = Column(Integer, ForeignKey('teachers.TeacherID'))
    IsActive = Column(Boolean, default=True)

    teacher = relationship("Teacher", backref="courses")  # Відношення до викладача
    enrollments = relationship("CourseEnrollment", back_populates="course")  # Зв'язок зі студентами через CourseEnrollment


class CourseEnrollment(Base):
    __tablename__ = 'courseenrollments'

    CourseID = Column(Integer, ForeignKey('courses.CourseID'), primary_key=True)
    StudentID = Column(Integer, ForeignKey('students.StudentID'), primary_key=True)

    course = relationship("Course", back_populates="enrollments")
    student = relationship("Student", back_populates="course_enrollments")


class PersonalQuestion(Base):
    __tablename__ = 'personalquestions'

    QuestionID = Column(Integer, primary_key=True, autoincrement=True)
    UserID = Column(Integer, ForeignKey('users.UserID'), nullable=False)
    Question = Column(Text, nullable=False)
    Answer = Column(Text, nullable=True)
    Status = Column(Enum('pending', 'answered'), nullable=False, default='pending')
    AnsweredBy = Column(Integer, ForeignKey('users.UserID'), nullable=True)
    Timestamp = Column(TIMESTAMP, nullable=False)


class FAQ(Base):
    __tablename__ = 'faqs'

    FAQID = Column(Integer, primary_key=True, autoincrement=True)
    Question = Column(Text, nullable=False)
    Answer = Column(Text, nullable=False)


class DocumentType(Base):
    __tablename__ = 'documenttypes'

    TypeID = Column(Integer, primary_key=True, autoincrement=True)
    TypeName = Column(String(100), nullable=False)

    requests = relationship("DocumentRequest", back_populates="document_type")


class DocumentRequest(Base):
    __tablename__ = 'documentrequests'

    RequestID = Column(Integer, primary_key=True, autoincrement=True)
    StudentID = Column(Integer, ForeignKey('students.StudentID'), nullable=False)
    TypeID = Column(Integer, ForeignKey('documenttypes.TypeID'), nullable=False)
    Status = Column(Enum('pending', 'approved', 'rejected'), nullable=False, default='pending')

    student = relationship("Student", back_populates="document_requests")
    document_type = relationship("DocumentType", back_populates="requests")
