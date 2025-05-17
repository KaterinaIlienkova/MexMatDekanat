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

    # def update_request_status_with_scan(self, request_id, status):
    #     with self.session_factory() as db:
    #         request = db.query(DocumentRequest).filter(DocumentRequest.RequestID == request_id).first()
    #         if request:
    #             request.Status = status
    #             db.commit()
    #             return request
    #         return None

    # def update_request_status(self, request_id, status):
    #     """Update document request status"""
    #     with self.db_manager.get_session() as session:
    #         try:
    #             request = session.query(DocumentRequest).filter_by(RequestID=request_id).first()
    #             if request:
    #                 request.Status = status
    #                 session.commit()
    #                 return True
    #             return False
    #         except Exception as e:
    #             logger.exception(f"Error updating document request: {e}")
    #             session.rollback()
    #             return False

# class DocumentRequestRepository:
#     """Handles database operations for DocumentRequest entities"""
#
#     def __init__(self, db_manager):
#         self.db_manager = db_manager
#
#     def get_all_document_types(self):
#         """Get all document types"""
#         with self.db_manager.get_session() as session:
#             return session.query(DocumentType).all()
#
#     def create_request(self, student_id, type_id):
#         """Create a new document request"""
#         with self.db_manager.get_session() as session:
#             try:
#                 request = DocumentRequest(
#                     StudentID=student_id,
#                     TypeID=type_id,
#                     Status='pending'
#                 )
#                 session.add(request)
#                 session.commit()
#                 return request
#             except Exception as e:
#                 logger.exception(f"Error creating document request: {e}")
#                 session.rollback()
#                 return None
#
#     def update_request_status(self, request_id, status):
#         """Update document request status"""
#         with self.db_manager.get_session() as session:
#             try:
#                 request = session.query(DocumentRequest).filter_by(RequestID=request_id).first()
#                 if request:
#                     request.Status = status
#                     session.commit()
#                     return True
#                 return False
#             except Exception as e:
#                 logger.exception(f"Error updating document request: {e}")
#                 session.rollback()
#                 return False