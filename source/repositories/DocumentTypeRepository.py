from source.models import DocumentRequest, DocumentType
from source.repositories.BaseRepository import BaseRepository


class DocumentTypeRepository(BaseRepository):

    def get_all_document_types(self):
        return self.session.query(DocumentType).all()

    def get_document_type_by_id(self, type_id):
        return self.session.query(DocumentType).filter(DocumentType.TypeID == type_id).first()
