#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主程序入口文件 - Main Application Entry Point
启动天气数据建模与分析系统
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

def main():
    """主函数"""
    try:
        # 设置高DPI支持
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # 创建应用程序
        app = QApplication(sys.argv)
        
        # 设置中文字体
        font = QFont("Microsoft YaHei", 10)
        app.setFont(font)
        
        # 设置应用程序信息
        app.setApplicationName("天气数据建模与分析系统")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("数据处理团队")
        
        # 延迟导入以避免循环导入
        try:
            from utils.config_manager import ConfigManager
            from utils.logger import setup_logger
            from gui.main_window import MainWindow
        except ImportError as e:
            print(f"导入模块失败: {e}")
            print("请检查模块路径")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        
        # 初始化配置管理器
        config_manager = ConfigManager()
        
        # 设置日志系统
        setup_logger(
            log_level=config_manager.get('logging.level', 'INFO'),
            log_dir=config_manager.get('paths.logs_dir', './logs')
        )
        
        # 创建并显示主窗口
        main_window = MainWindow(config_manager)
        main_window.show()
        
        # 运行应用程序
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"启动应用程序失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()