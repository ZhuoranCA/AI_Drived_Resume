import os
from fastapi import UploadFile

# Define the upload directory
UPLOAD_DIR = "uploads/resumes"

def save_upload_file(upload_file: UploadFile) -> str:
    """
    Save the uploaded file to 'uploads/resumes' folder.
    Returns the full file path.
    """
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)

    file_path = os.path.join(UPLOAD_DIR, upload_file.filename)

    # 重要：先读取文件内容后写入（UploadFile.file 是一个 SpooledTemporaryFile）
    with open(file_path, "wb") as buffer:
        buffer.write(upload_file.file.read())

    return file_path


def read_file_content(file_path: str) -> str:
    """
    Read and return the content of the uploaded Markdown file.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()
