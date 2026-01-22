from fastapi import HTTPException, status


class APIException(HTTPException):
    """기본 API 예외 클래스"""
    def __init__(self, error_code: str, message: str, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR):
        self.error_code = error_code
        super().__init__(status_code=status_code, detail={"error_code": error_code, "message": message})


class MissingSourceDataException(APIException):
    """소스 데이터 누락 예외"""
    def __init__(self, message: str = "pdf_text, weblink, paper_title 중 하나는 필수입니다."):
        super().__init__(
            error_code="MISSING_SOURCE_DATA",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class InvalidFormatException(APIException):
    """유효성 검증 실패 예외"""
    def __init__(self, message: str = "데이터 형식이 올바르지 않아 분석할 수 없습니다."):
        super().__init__(
            error_code="INVALID_FORMAT",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


class MissingTraitsException(APIException):
    """사용자 특성 정보 누락 예외"""
    def __init__(self, message: str = "user_traits의 필수항목들을 입력해야 합니다."):
        super().__init__(
            error_code="MISSING_TRAITS",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class AnalysisNotFoundException(APIException):
    """분석 데이터 없음 예외"""
    def __init__(self, message: str = "해당 analysis_id에 연결된 데이터를 찾을 수 없습니다."):
        super().__init__(
            error_code="ANALYSIS_NOT_FOUND",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND
        )


class GenerationFailedException(APIException):
    """커리큘럼 생성 실패 예외"""
    def __init__(self, message: str = "커리큘럼을 생성하는 도중 오류가 발생했습니다."):
        super().__init__(
            error_code="GENERATION_FAILED",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class InternalServerErrorException(APIException):
    """서버 내부 오류 예외"""
    def __init__(self, message: str = "서버 오류가 발생했습니다."):
        super().__init__(
            error_code="INTERNAL_SERVER_ERROR",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
