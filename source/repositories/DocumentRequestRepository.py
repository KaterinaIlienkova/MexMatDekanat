from source.config import logger
from source.models import DocumentRequest, DocumentType
from source.repositories.BaseRepository import BaseRepository


class DocumentRequestRepository(BaseRepository):

    def get_pending_requests(self):
        return self.session.query(DocumentRequest).filter(DocumentRequest.Status == 'pending').all()

    def get_request_by_id(self, request_id):
        return self.session.query(DocumentRequest).filter(DocumentRequest.RequestID == request_id).first()

    def create_request(self, student_id, type_id):
            new_request = DocumentRequest(
                StudentID=student_id,
                TypeID=type_id,
                Status='pending'
            )
            self.session.add(new_request)
            self.session.commit()
            self.session.refresh(new_request)
            return new_request

    def update_request_status(self, request_id, status):
            request = self.session.query(DocumentRequest).filter_by(RequestID=request_id).first()
            if not request:
                return None, None
            request.Status = status
            self.session.commit()
            return request.StudentID, request.RequestID

