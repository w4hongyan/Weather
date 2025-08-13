#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气数据建模与分析系统启动脚本
Weather Data Modeling and Analysis System - Startup Script
"""

import os
import sys
import subprocess

def main():
    """启动应用程序"""
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(script_dir, 'src')
    
    if not os.path.exists(src_dir):
        print(f"错误: 找不到src目录: {src_dir}")
        return 1
    
    # 切换到src目录
    os.chdir(src_dir)
    
    # 将src目录添加到Python路径
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    print("正在启动天气数据建模与分析系统...")
    print("工作目录:", os.getcwd())
    print("Python路径:", sys.path[0])
    
    try:
        # 启动应用程序
        result = subprocess.run([sys.executable, 'main.py'], check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        print(f"应用程序启动失败，返回码: {e.returncode}")
        return e.returncode
    except KeyboardInterrupt:
        print("\n应用程序被用户中断")
        return 0
    except Exception as e:
        print(f"启动过程中出现错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())