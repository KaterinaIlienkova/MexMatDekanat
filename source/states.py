# states.py
from aiogram.fsm.state import State, StatesGroup

class UserRegistration(StatesGroup):
    waiting_for_role = State()
    waiting_for_details = State()

class FAQ(StatesGroup):
    waiting_for_question = State()
    waiting_for_answer = State()
    waiting_for_edit_answer = State()

class Announcement(StatesGroup):
    waiting_for_text = State()
