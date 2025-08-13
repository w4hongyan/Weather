#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统 - Logging System
提供统一的日志记录功能
"""

import logging
import os
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

def setup_logger(
    name: str = "weather_analysis",
    log_level: int = logging.INFO,
    log_dir: str = "../logs",
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    设置和配置日志系统
    
    Args:
        name: 日志器名称
        log_level: 日志级别
        log_dir: 日志文件目录
        max_file_size: 单个日志文件最大大小
        backup_count: 保留的日志文件数量
        
    Returns:
        配置好的日志器实例
    """
    
    # 创建日志目录
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    # 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 如果日志器已经有处理器，先清除它们
    logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 创建文件处理器（按大小轮转）
    file_handler = RotatingFileHandler(
        filename=log_path / f"{name}.log",
        maxBytes=max_file_size,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 创建每日日志处理器
    daily_handler = TimedRotatingFileHandler(
        filename=log_path / f"{name}_daily.log",
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8'
    )
    daily_handler.setLevel(log_level)
    daily_handler.setFormatter(formatter)
    daily_handler.suffix = "%Y-%m-%d"
    logger.addHandler(daily_handler)
    
    # 创建错误日志处理器
    error_handler = logging.FileHandler(
        filename=log_path / "error.log",
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    return logger

class LoggerMixin:
    """日志混入类，为其他类提供日志功能"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

def log_function_call(logger: logging.Logger = None):
    """
    函数调用日志装饰器
    
    Args:
        logger: 日志器实例，如果为None则使用默认日志器
    """
    if logger is None:
        logger = logging.getLogger("weather_analysis")
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"调用函数: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"函数 {func.__name__} 执行成功")
                return result
            except Exception as e:
                logger.error(f"函数 {func.__name__} 执行失败: {str(e)}")
                raise
        return wrapper
    return decorator

class LogContext:
    """上下文管理器，用于临时设置日志上下文"""
    
    def __init__(self, logger_name: str, level: int = logging.DEBUG):
        self.logger_name = logger_name
        self.level = level
        self.original_level = None
    
    def __enter__(self):
        logger = logging.getLogger(self.logger_name)
        self.original_level = logger.level
        logger.setLevel(self.level)
        return logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        logger = logging.getLogger(self.logger_name)
        logger.setLevel(self.original_level)

# 创建全局日志器
logger = setup_logger()

# 使用示例
if __name__ == "__main__":
    # 测试日志系统
    logger.info("日志系统测试")
    logger.debug("调试信息")
    logger.warning("警告信息")
    logger.error("错误信息")
    
    # 测试混入类
    class TestClass(LoggerMixin):
        def test_method(self):
            self.logger.info("测试日志混入类")
    
    test = TestClass()
    test.test_method()
    
    # 测试装饰器
    @log_function_call()
    def test_function():
        return "测试成功"
    
    result = test_function()
    print(result)