from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.core.exceptions import APIException
from app.api.main import api_router


app = FastAPI(
    title="PTMT-Agent API",
    description="Paper-based Teaching Material Agent API",
    version="0.1.0"
)

# API 라우터 등록
app.include_router(api_router)


# 커스텀 예외 핸들러
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )


@app.get("/")
async def root():
    return {"message": "PTMT-Agent API", "version": "0.1.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
