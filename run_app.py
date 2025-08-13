#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气数据建模与分析系统 - 简化启动脚本
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# 设置环境变量
os.environ['PYTHONPATH'] = str(project_root / "src")

def main():
    """主函数"""
    try:
        # 导入必要的模块
        from PyQt5.QtWidgets import QApplication
        from src.gui.main_window import MainWindow
        from src.utils.config_manager import ConfigManager
        
        # 创建应用程序
        app = QApplication(sys.argv)
        
        # 初始化配置
        config = ConfigManager()
        
        # 创建主窗口
        window = MainWindow(config)
        window.show()
        
        # 运行应用
        return app.exec_()
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("尝试修复路径...")
        
        # 尝试另一种导入方式
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
            from PyQt5.QtWidgets import QApplication
            from gui.main_window import MainWindow
            from utils.config_manager import ConfigManager
            
            app = QApplication(sys.argv)
            config = ConfigManager()
            window = MainWindow(config)
            window.show()
            return app.exec_()
            
        except Exception as e2:
            print(f"启动失败: {e2}")
            import traceback
            traceback.print_exc()
            return 1
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())