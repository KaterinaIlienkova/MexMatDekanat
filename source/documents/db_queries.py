from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from source.database import SessionLocal
from source.models import DocumentRequest, DocumentType
async def confirm_document_request(update: Update, context: CallbackContext):
    """Підтверджує замовлення документа."""
    query = update.callback_query
    await query.answer()

    try:
        # Очікуємо формат: doc_confirm_<typeid>_<studentid>
        parts = query.data.split('_')
        if len(parts) != 4:
            raise ValueError(f"Невірний формат callback_data: {query.data}")

        _, _, document_type_id_str, student_id_str = parts
        document_type_id = int(document_type_id_str)
        student_id = int(student_id_str)

        with SessionLocal() as db:
            new_request = DocumentRequest(
                StudentID=student_id,
                TypeID=document_type_id,
                Status='pending'
            )

            db.add(new_request)
            db.commit()
            db.refresh(new_request)

            document_type = db.query(DocumentType).filter(DocumentType.TypeID == document_type_id).first()

            await query.edit_message_text(
                f"✅ Ваша заявка на документ **'{document_type.TypeName}'** успішно створена!\n"
                f"📄 Номер заявки: {new_request.RequestID}\n"
                f"⏳ Статус: В обробці"
            )

    except Exception as e:
        print(f"❌ Помилка при створенні заявки: {e}")
        await query.edit_message_text(
            "❌ Сталася помилка при створенні заявки. Спробуйте пізніше або зверніться до деканату."
        )
