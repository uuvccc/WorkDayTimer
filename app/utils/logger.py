import logging
import os
import sys


def _is_packaged():
    """独立副本：Nuitka (__compiled__) 或 PyInstaller (sys.frozen) 打包均可识别。

    utils 包禁止依赖 config，所以这里自维护一份；与 app/config/constants.py
    的 `_is_packaged()` 保持等价即可。"""
    return "__compiled__" in globals() or bool(getattr(sys, "frozen", False))


def get_project_root():
    """项目根目录：打包后为 exe 所在目录，源码运行时为 __file__ 上两级。

    Nuitka standalone 不设置 sys.frozen 且 sys.executable 指向假 python.exe，
    必须用 sys.argv[0] 反推真实 exe 目录。"""
    if _is_packaged():
        if sys.argv and sys.argv[0]:
            argv0 = os.path.abspath(sys.argv[0])
            if argv0.lower().endswith(".exe") and os.path.isfile(argv0):
                return os.path.dirname(argv0)
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def setup_logging(name=__name__, level=logging.DEBUG):
    log_dir = os.path.join(get_project_root(), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'app.log')
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    if logger.handlers:
        logger.handlers.clear()
    
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    
    return logger

logger = setup_logging('MiniTools')