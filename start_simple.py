#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版启动脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from PyQt5.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.utils.config_manager import ConfigManager

def main():
    """主函数"""
    app = QApplication(sys.argv)
    config = ConfigManager()
    window = MainWindow(config)
    window.show()
    return app.exec_()

if __name__ == "__main__":
    main()