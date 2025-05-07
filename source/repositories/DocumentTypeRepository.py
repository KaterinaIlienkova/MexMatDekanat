from source.models import DocumentRequest, DocumentType


class DocumentTypeRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def get_all_document_types(self):
        with self.session_factory() as db:
            return db.query(DocumentType).all()

    def get_document_type_by_id(self, type_id):
        with self.session_factory() as db:
            return db.query(DocumentType).filter(DocumentType.TypeID == type_id).first()
