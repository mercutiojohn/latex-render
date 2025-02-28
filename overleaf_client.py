import os
import requests
import json
import time
from typing import Optional
from enum import Enum

class CompilerType(str, Enum):
    """
    支持的编译器类型
    """
    PDFLATEX = "pdflatex"
    XELATEX = "xelatex"
    LUALATEX = "lualatex"
    LATEX = "latex"

class OverleafClient:
    def __init__(self, base_url: str, api_token: Optional[str] = None, email: Optional[str] = None, password: Optional[str] = None):
        """
        初始化 Overleaf 客户端
        
        Args:
            base_url: Overleaf 服务器地址
            api_token: API 令牌（可选）
            email: 用户邮箱（可选）
            password: 用户密码（可选）
            
        注意：
            - 如果提供 api_token，将优先使用 token 认证
            - 如果同时提供 email 和 password，将自动进行登录
            - 如果都未提供，将以未认证状态初始化
        """
        self.base_url = base_url
        self.session = requests.Session()
        self.authenticated = False
        
        # 设置基本请求头
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }
        
        # 优先使用 token 认证
        if api_token:
            self.headers["Authorization"] = f"Bearer {api_token}"
            self.authenticated = True
        # 如果提供邮箱和密码，尝试登录
        elif email and password:
            self.authenticated = self.login(email, password)
            
        self.session.headers.update(self.headers)
    
    def login(self, email: str, password: str) -> bool:
        """
        使用邮箱和密码登录
        
        Args:
            email: 用户邮箱
            password: 用户密码
            
        Returns:
            bool: 登录是否成功
        """
        url = f"{self.base_url}/login"
        data = {
            "email": email,
            "password": password
        }
        response = self.session.post(url, json=data)
        self.authenticated = response.status_code == 200
        
        # 如果登录成功，从响应中获取并设置 token（如果服务器提供）
        if self.authenticated:
            token = response.headers.get("X-Auth-Token") or response.json().get("token")
            if token:
                self.headers["Authorization"] = f"Bearer {token}"
                self.session.headers.update(self.headers)
                
        return self.authenticated
    
    def _ensure_auth(self):
        """
        确保客户端已认证
        
        Raises:
            RuntimeError: 如果客户端未认证
        """
        if not self.authenticated:
            raise RuntimeError("需要先进行认证。请使用 API token 初始化客户端或调用 login() 方法。")
    
    def create_project(self, name: str, template_id: Optional[str] = None) -> dict:
        """
        创建新项目
        
        Args:
            name: 项目名称
            template_id: 模板ID（可选）
            
        Returns:
            dict: 包含项目信息的字典
            
        Raises:
            RuntimeError: 如果客户端未认证
        """
        self._ensure_auth()
        url = f"{self.base_url}/project"
        data = {
            "name": name
        }
        if template_id:
            data["template"] = template_id
            
        response = self.session.post(url, json=data)
        return response.json()

    def upload_file(self, project_id: str, file_path: str, file_name: Optional[str] = None) -> dict:
        """
        上传LaTeX文件
        
        Args:
            project_id: 项目ID
            file_path: 文件路径
            file_name: 文件名（可选，默认使用file_path的文件名）
            
        Returns:
            dict: 上传响应信息
        """
        if not file_name:
            file_name = os.path.basename(file_path)
            
        url = f"{self.base_url}/project/{project_id}/file"
        
        with open(file_path, "rb") as f:
            files = {"file": (file_name, f)}
            response = self.session.post(url, files=files)
            
        return response.json()

    def compile_project(self, project_id: str, compiler: str = CompilerType.PDFLATEX) -> dict:
        """
        编译项目
        
        Args:
            project_id: 项目ID
            compiler: 编译器类型，默认为 pdflatex
            
        Returns:
            dict: 编译响应信息
        """
        if isinstance(compiler, CompilerType):
            compiler = compiler.value
            
        url = f"{self.base_url}/project/{project_id}/compile"
        data = {
            "compiler": compiler
        }
        
        response = self.session.post(url, json=data)
        return response.json()

    def get_pdf(self, project_id: str, output_path: str) -> bool:
        """
        获取编译后的 PDF
        
        Args:
            project_id: 项目ID
            output_path: PDF输出路径
            
        Returns:
            bool: 是否成功获取PDF
        """
        try:
            self._ensure_auth()
            url = f"{self.base_url}/project/{project_id}/output/output.pdf"
            
            response = self.session.get(url, stream=True)
            if response.status_code != 200:
                return False
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            # 分块写入文件
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            return True
        except Exception as e:
            print(f"获取 PDF 失败: {str(e)}")  # 添加日志
            return False

    def wait_for_compile(self, project_id: str, timeout: int = 60) -> bool:
        """
        等待编译完成
        
        Args:
            project_id: 项目ID
            timeout: 超时时间（秒）
            
        Returns:
            bool: 编译是否成功完成
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            status = self.get_compile_status(project_id)
            if status.get("status") == "success":
                return True
            elif status.get("status") == "error":
                return False
            time.sleep(2)
        return False

    def get_compile_status(self, project_id: str) -> dict:
        """
        获取编译状态
        
        Args:
            project_id: 项目ID
            
        Returns:
            dict: 包含编译状态信息的字典
        """
        url = f"{self.base_url}/project/{project_id}/compile/status"
        response = self.session.get(url)
        return response.json()

    def get_project_files(self, project_id: str) -> dict:
        """
        获取项目文件列表
        
        Args:
            project_id: 项目ID
            
        Returns:
            dict: 包含项目文件列表的字典
        """
        try:
            self._ensure_auth()
            url = f"{self.base_url}/project/{project_id}/files"
            response = self.session.get(url)
            response.raise_for_status()  # 抛出非 2xx 响应的异常
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"获取文件列表失败: {str(e)}")  # 添加日志
            raise RuntimeError(f"获取文件列表失败: {str(e)}")

    def update_file(self, project_id: str, file_id: str, content: str) -> dict:
        """
        更新文件内容
        
        Args:
            project_id: 项目ID
            file_id: 文件ID
            content: 新的文件内容
            
        Returns:
            dict: 更新响应信息
        """
        url = f"{self.base_url}/project/{project_id}/file/{file_id}"
        data = {"content": content}
        response = self.session.post(url, json=data)
        return response.json()

    def delete_project(self, project_id: str) -> bool:
        """
        删除项目
        
        Args:
            project_id: 项目ID
            
        Returns:
            bool: 是否成功删除
        """
        url = f"{self.base_url}/project/{project_id}"
        response = self.session.delete(url)
        return response.status_code == 200

    def health_check(self) -> bool:
        """
        检查服务器状态
        
        Returns:
            bool: 服务器是否正常运行
        """
        url = f"{self.base_url}/health"
        response = self.session.get(url)
        return response.status_code == 200
