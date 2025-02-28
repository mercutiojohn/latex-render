from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Path, Query
from fastapi.responses import FileResponse
import os
import tempfile
from typing import Optional
from enum import Enum

from config import (
    OVERLEAF_BASE_URL,
    # OVERLEAF_API_TOKEN,
    OVERLEAF_EMAIL,
    OVERLEAF_PASSWORD
)
from overleaf_client import OverleafClient

app = FastAPI(
    title="Overleaf API",
    description="Overleaf API 服务，提供 LaTeX 文档编译和管理功能",
    version="1.0.0"
)

# 初始化 Overleaf 客户端
client = OverleafClient(
    base_url=OVERLEAF_BASE_URL,
    # api_token=OVERLEAF_API_TOKEN,
    email=OVERLEAF_EMAIL,
    password=OVERLEAF_PASSWORD
)

class CompilerType(str, Enum):
    """
    支持的编译器类型
    """
    PDFLATEX = "pdflatex"
    XELATEX = "xelatex"
    LUALATEX = "lualatex"
    LATEX = "latex"

@app.get("/health")
async def health_check():
    """
    检查服务健康状态
    """
    if client.health_check():
        return {"status": "healthy", "message": "服务运行正常"}
    raise HTTPException(status_code=503, detail="Overleaf 服务不可用")

@app.post("/projects")
async def create_project(name: str, template_id: Optional[str] = None):
    """
    创建新项目
    """
    try:
        project = client.create_project(name, template_id)
        return project
    except RuntimeError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/{project_id}/files")
async def upload_file(
    project_id: str,
    file: UploadFile = File(...),
    file_name: Optional[str] = Form(None)
):
    """
    上传文件到项目
    """
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name

        try:
            # 上传文件到 Overleaf
            result = client.upload_file(
                project_id=project_id,
                file_path=temp_path,
                file_name=file_name or file.filename
            )
            return result
        finally:
            # 清理临时文件
            os.unlink(temp_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/projects/{project_id}/compile")
async def compile_project(
    project_id: str = Path(..., description="项目ID"),
    compiler: CompilerType = Query(
        default=CompilerType.PDFLATEX,
        description="编译器类型"
    )
):
    """
    编译项目
    
    Args:
        project_id: 项目ID
        compiler: 编译器类型，支持：
                 - pdflatex: 默认编译器
                 - xelatex: 支持更多字体和 Unicode
                 - lualatex: 基于 LuaTeX 引擎
                 - latex: 传统的 LaTeX 编译器
    
    Returns:
        dict: 包含编译结果的字典
    
    Raises:
        HTTPException: 
            - 500: 编译失败
            - 404: 项目不存在
    """
    try:
        # 开始编译
        compile_result = client.compile_project(project_id, compiler.value)
        
        # 等待编译完成
        if not client.wait_for_compile(project_id):
            raise HTTPException(status_code=500, detail="编译失败")
            
        return {
            "status": "success",
            "compiler": compiler.value,
            "compile_result": compile_result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"编译失败: {str(e)}"
        )

@app.get("/projects/{project_id}/pdf")
async def get_pdf(project_id: str):
    """
    获取编译后的 PDF
    """
    temp_file = None
    try:
        # 创建临时文件保存 PDF
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        pdf_path = temp_file.name
        temp_file.close()  # 关闭文件但不删除
        
        # 获取 PDF
        if not client.get_pdf(project_id, pdf_path):
            raise HTTPException(status_code=404, detail="PDF 文件不存在")
        
        # 检查文件是否成功创建
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=500, detail="PDF 文件生成失败")
            
        # 检查文件大小
        if os.path.getsize(pdf_path) == 0:
            raise HTTPException(status_code=500, detail="PDF 文件为空")
            
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"project_{project_id}.pdf",
            background=None  # 同步删除文件
        )
    
    except HTTPException:
        # 重新抛出 HTTP 异常
        raise
    except Exception as e:
        # 处理其他异常
        raise HTTPException(status_code=500, detail=f"获取 PDF 失败: {str(e)}")
    finally:
        # 确保清理临时文件
        if temp_file and os.path.exists(temp_file.name):
            try:
                os.unlink(temp_file.name)
            except Exception:
                pass

@app.get("/projects/{project_id}/files")
async def get_project_files(project_id: str):
    """
    获取项目文件列表
    """
    try:
        files = client.get_project_files(project_id)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/projects/{project_id}/files/{file_id}")
async def update_file_content(
    project_id: str,
    file_id: str,
    content: str = Form(...)
):
    """
    更新文件内容
    """
    try:
        result = client.update_file(project_id, file_id, content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """
    删除项目
    """
    try:
        if client.delete_project(project_id):
            return {"status": "success", "message": "项目已删除"}
        raise HTTPException(status_code=404, detail="项目不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 