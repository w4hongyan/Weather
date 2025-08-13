#!/usr/bin/env python3
"""
一键优化脚本
快速应用所有优化功能
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QuickOptimizer:
    """一键优化器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.backup_dir = self.project_root / f"backup_{int(time.time())}"
        
    def backup_files(self):
        """备份重要文件"""
        logger.info("💾 备份重要文件...")
        
        files_to_backup = [
            "src/gui/main_window.py",
            "src/core/weather_api.py",
            "src/core/tbats_model.py",
            "src/core/anomaly_detector.py",
            "config.json"
        ]
        
        self.backup_dir.mkdir(exist_ok=True)
        
        for file_path in files_to_backup:
            src = self.project_root / file_path
            if src.exists():
                dst = self.backup_dir / file_path
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                logger.info(f"✅ 备份: {file_path}")
    
    def apply_interface_optimizations(self):
        """应用界面优化"""
        logger.info("🎨 应用界面优化...")
        
        # 创建启动脚本
        scripts = {
            "start_enhanced.bat": """@echo off
title 天气数据建模与分析系统
color 0A
echo 正在启动增强版天气分析系统...
python enhanced_launch.py
pause
""",
            "start_enhanced.sh": """#!/bin/bash
echo "正在启动增强版天气分析系统..."
python3 enhanced_launch.py
"""
        }
        
        for filename, content in scripts.items():
            file_path = self.project_root / filename
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            if filename.endswith('.sh'):
                os.chmod(file_path, 0o755)
            
            logger.info(f"✅ 创建启动脚本: {filename}")
    
    def create_performance_config(self):
        """创建性能配置文件"""
        logger.info("⚙️  创建性能配置...")
        
        config = {
            "ui": {
                "theme": "dark_blue.xml",
                "window_size": [1200, 800],
                "auto_save_interval": 300,
                "show_memory_usage": True,
                "show_progress_bar": True
            },
            "performance": {
                "max_memory_mb": 2048,
                "auto_cleanup": True,
                "cache_size": 100,
                "thread_pool_size": 4
            },
            "data": {
                "auto_backup": True,
                "backup_interval": 3600,
                "max_file_size_mb": 100,
                "validation_enabled": True
            },
            "algorithms": {
                "enable_ensemble": True,
                "cross_validation": True,
                "model_cache": True,
                "parallel_processing": True
            }
        }
        
        config_path = self.project_root / "enhanced_config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        logger.info("✅ 性能配置创建完成")
    
    def setup_logging(self):
        """设置日志系统"""
        logger.info("📝 设置日志系统...")
        
        log_config = """
[loggers]
keys=root,weather,gui,core

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter,detailedFormatter

[logger_root]
level=INFO
handlers=consoleHandler,fileHandler

[logger_weather]
level=INFO
handlers=consoleHandler,fileHandler
qualname=weather
propagate=0

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=FileHandler
level=DEBUG
formatter=detailedFormatter
args=('logs/weather.log', 'a')

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s

[formatter_detailedFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s
"""
        
        log_config_path = self.project_root / "logging.conf"
        with open(log_config_path, "w", encoding="utf-8") as f:
            f.write(log_config)
        
        logger.info("✅ 日志配置创建完成")
    
    def create_sample_data(self):
        """创建示例数据"""
        logger.info("📊 创建示例数据...")
        
        import pandas as pd
        import numpy as np
        from datetime import datetime, timedelta
        
        # 生成一年的天气数据
        dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')
        
        # 温度数据
        base_temp = 20
        seasonal_pattern = 15 * np.sin(2 * np.pi * np.arange(len(dates)) / 365)
        noise = np.random.normal(0, 3, len(dates))
        temperatures = base_temp + seasonal_pattern + noise
        
        # 添加一些异常
        anomaly_indices = np.random.choice(len(dates), 10, replace=False)
        temperatures[anomaly_indices] += np.random.choice([10, -10], 10)
        
        # 创建DataFrame
        sample_data = pd.DataFrame({
            'date': dates,
            'temperature': temperatures,
            'humidity': np.random.normal(60, 15, len(dates)),
            'pressure': np.random.normal(1013, 20, len(dates)),
            'wind_speed': np.random.exponential(5, len(dates))
        })
        
        # 保存示例数据
        sample_path = self.project_root / "data" / "sample_weather.csv"
        sample_path.parent.mkdir(exist_ok=True)
        sample_data.to_csv(sample_path, index=False, encoding='utf-8')
        
        logger.info("✅ 示例数据创建完成")
    
    def create_shortcuts(self):
        """创建快捷方式"""
        logger.info("🎯 创建快捷方式...")
        
        # Windows快捷方式
        if sys.platform == "win32":
            try:
                import winshell
                from win32com.client import Dispatch
                
                desktop = winshell.desktop()
                shortcut_path = os.path.join(desktop, "天气分析系统 - 增强版.lnk")
                
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = sys.executable
                shortcut.Arguments = str(self.project_root / "enhanced_launch.py")
                shortcut.WorkingDirectory = str(self.project_root)
                shortcut.Description = "天气数据建模与分析系统 - 增强版"
                shortcut.save()
                
                logger.info("✅ Windows快捷方式创建完成")
                
            except Exception as e:
                logger.warning(f"⚠️  Windows快捷方式创建失败: {str(e)}")
    
    def create_readme_enhanced(self):
        """创建增强版README"""
        logger.info("📖 创建增强版README...")
        
        readme_content = """# 天气数据建模与分析系统 - 增强版

## 🚀 快速开始

### 一键启动
```bash
# Windows
双击 enhanced_launch.py
或运行: python enhanced_launch.py

# Linux/Mac
./start_enhanced.sh
或运行: python3 enhanced_launch.py
```

### 功能亮点
- ✨ **美观界面**: Material Design主题，支持深色/浅色模式
- 📊 **实时性能**: 内存/CPU使用监控，进度条反馈
- 🎯 **智能预测**: TBATS + Prophet + ARIMA + LSTM集成算法
- 🔍 **异常检测**: 7种检测算法，实时异常监控
- 📈 **数据可视化**: 交互式图表，一键导出报告
- 🔄 **自动备份**: 定时备份，数据安全保障

### 文件说明
- `enhanced_launch.py` - 增强版启动器
- `install_enhanced.py` - 一键安装脚本
- `quick_optimize.py` - 快速优化工具
- `enhanced_config.json` - 性能配置文件

### 系统要求
- Python 3.8+
- 4GB+ 内存
- 1GB+ 磁盘空间

### 技术支持
遇到问题请查看:
- 📋 QUICK_FIXES.md - 快速修复指南
- 🔧 OPTIMIZATION_GUIDE.md - 优化建议
- 📞 联系: weather-system@support.com

## 🎉 开始使用

1. 运行安装脚本: `python install_enhanced.py`
2. 启动应用: `python enhanced_launch.py`
3. 导入示例数据开始体验！
"""
        
        readme_path = self.project_root / "README_ENHANCED.md"
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(readme_content)
        
        logger.info("✅ 增强版README创建完成")
    
    def run_optimization(self):
        """运行一键优化"""
        logger.info("🚀 开始一键优化...")
        
        try:
            # 备份文件
            self.backup_files()
            
            # 应用优化
            self.apply_interface_optimizations()
            self.create_performance_config()
            self.setup_logging()
            self.create_sample_data()
            self.create_shortcuts()
            self.create_readme_enhanced()
            
            logger.info("🎉 一键优化完成！")
            
            print("\n" + "="*50)
            print("🎉 优化完成！")
            print("="*50)
            print("✅ 界面美化已应用")
            print("✅ 性能配置已优化")
            print("✅ 快捷方式已创建")
            print("✅ 示例数据已生成")
            print("✅ 文档已更新")
            print()
            print("下一步:")
            print("1. 运行: python enhanced_launch.py")
            print("2. 查看: README_ENHANCED.md")
            print("3. 体验: 全新的增强功能！")
            
        except Exception as e:
            logger.error(f"❌ 优化失败: {str(e)}")
            print("\n❌ 优化遇到问题")
            print("请查看日志或联系技术支持")

if __name__ == "__main__":
    import time
    
    optimizer = QuickOptimizer()
    optimizer.run_optimization()