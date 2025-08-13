#!/usr/bin/env python3
"""
增强版启动脚本
提供美化界面、性能监控、一键优化功能
"""

import sys
import os
import subprocess
import pkg_resources
import logging
from pathlib import Path
import time
import psutil

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedLauncher:
    """增强版启动器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.src_dir = self.project_root / 'src'
        self.requirements_file = self.project_root / 'requirements.txt'
        self.config_file = self.project_root / 'config.json'
        
        # 检查系统要求
        self.check_system_requirements()
    
    def check_system_requirements(self):
        """检查系统要求"""
        logger.info("🔍 检查系统要求...")
        
        # 检查Python版本
        python_version = sys.version_info
        if python_version < (3, 8):
            logger.error("❌ Python版本过低，需要3.8或更高版本")
            sys.exit(1)
        else:
            logger.info(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
        
        # 检查内存
        memory = psutil.virtual_memory()
        if memory.total < 4 * 1024 * 1024 * 1024:  # 4GB
            logger.warning("⚠️  内存较低，可能影响性能")
        else:
            logger.info(f"✅ 内存: {memory.total / 1024**3:.1f}GB")
        
        # 检查磁盘空间
        disk = psutil.disk_usage('/')
        if disk.free < 1 * 1024 * 1024 * 1024:  # 1GB
            logger.warning("⚠️  磁盘空间不足")
        else:
            logger.info(f"✅ 磁盘空间: {disk.free / 1024**3:.1f}GB")
    
    def check_dependencies(self):
        """检查依赖包"""
        logger.info("📦 检查依赖包...")
        
        required_packages = [
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'scipy',
            'PyQt5', 'qt-material', 'qasync', 'psutil', 'memory-profiler',
            'prophet', 'statsmodels', 'pandera', 'pydantic'
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                pkg_resources.get_distribution(package)
                logger.info(f"✅ {package}")
            except pkg_resources.DistributionNotFound:
                missing_packages.append(package)
                logger.error(f"❌ {package}")
        
        if missing_packages:
            logger.warning(f"缺失包: {missing_packages}")
            return False
        
        return True
    
    def install_missing_packages(self):
        """安装缺失的包"""
        logger.info("🚀 安装缺失的包...")
        
        missing_packages = [
            'qt-material', 'qasync', 'psutil', 'memory-profiler',
            'prophet', 'statsmodels', 'pandera', 'pydantic'
        ]
        
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                logger.info(f"✅ 安装成功: {package}")
            except subprocess.CalledProcessError:
                logger.error(f"❌ 安装失败: {package}")
    
    def setup_environment(self):
        """设置环境"""
        logger.info("⚙️  设置环境...")
        
        # 确保src目录在Python路径中
        if str(self.src_dir) not in sys.path:
            sys.path.insert(0, str(self.src_dir))
        
        # 创建必要的目录
        directories = [
            'data', 'logs', 'cache', 'reports', 'models', 'exports'
        ]
        
        for directory in directories:
            dir_path = self.project_root / directory
            dir_path.mkdir(exist_ok=True)
            logger.info(f"✅ 创建目录: {directory}")
        
        # 设置环境变量
        os.environ['PYTHONPATH'] = str(self.src_dir)
        os.environ['QT_QPA_PLATFORM'] = 'windows'  # Windows优化
    
    def show_welcome_banner(self):
        """显示欢迎横幅"""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║    🌤️  天气数据建模与分析系统 - 增强版启动器                                ║
║                                                                              ║
║    ✨  功能特性:                                                            ║
║       • 美观的Material Design界面                                           ║
║       • 实时性能监控和内存使用追踪                                           ║
║       • 多种预测算法支持 (TBATS, Prophet, ARIMA, LSTM)                       ║
║       • 智能异常检测系统                                                     ║
║       • 一键数据导入和导出                                                   ║
║       • 交互式数据可视化                                                     ║
║                                                                              ║
║    🚀  正在启动系统...                                                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def run_system_checks(self):
        """运行系统检查"""
        logger.info("🔧 运行系统检查...")
        
        checks = [
            ("依赖检查", self.check_dependencies),
            ("环境设置", self.setup_environment),
            ("性能测试", self.run_performance_test),
        ]
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                if result is False:
                    logger.warning(f"⚠️  {check_name} 检查未通过")
                else:
                    logger.info(f"✅ {check_name} 检查通过")
            except Exception as e:
                logger.error(f"❌ {check_name} 检查失败: {str(e)}")
    
    def run_performance_test(self):
        """运行性能测试"""
        logger.info("⚡ 运行性能测试...")
        
        # 测试内存使用
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 测试CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        logger.info(f"💾 初始内存使用: {initial_memory:.1f}MB")
        logger.info(f"🔥 CPU使用率: {cpu_percent}%")
        
        return True
    
    def launch_application(self):
        """启动应用程序"""
        try:
            # 显示欢迎横幅
            self.show_welcome_banner()
            
            # 运行系统检查
            self.run_system_checks()
            
            # 启动主应用
            logger.info("🎯 启动主应用程序...")
            
            # 导入并启动主应用
            from PyQt5.QtWidgets import QApplication
            from src.gui.main_window import MainWindow
            from src.utils.config_manager import ConfigManager
            
            app = QApplication(sys.argv)
            config = ConfigManager()
            window = MainWindow(config)
            window.show()
            return app.exec_()
            
        except ImportError as e:
            logger.error(f"❌ 导入错误: {str(e)}")
            logger.info("🔄 尝试安装缺失的包...")
            self.install_missing_packages()
            
            # 重试启动
            try:
                from PyQt5.QtWidgets import QApplication
                from src.gui.main_window import MainWindow
                from src.utils.config_manager import ConfigManager
                
                app = QApplication(sys.argv)
                config = ConfigManager()
                window = MainWindow(config)
                window.show()
                return app.exec_()
            except Exception as e:
                logger.error(f"❌ 启动失败: {str(e)}")
                self.show_troubleshooting_guide()
                return 1
        
        except Exception as e:
            logger.error(f"❌ 启动失败: {str(e)}")
            self.show_troubleshooting_guide()
    
    def show_troubleshooting_guide(self):
        """显示故障排除指南"""
        guide = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                        🆘 故障排除指南                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

常见问题及解决方案:

1. ❌ "ModuleNotFoundError"
   → 运行: pip install -r requirements.txt

2. ❌ "ImportError: DLL load failed"
   → 重新安装PyQt5: pip install --upgrade PyQt5

3. ❌ "MemoryError"
   → 关闭其他应用程序释放内存
   → 减少数据量或增加系统内存

4. ❌ "PermissionError"
   → 以管理员身份运行命令行
   → 检查文件权限

5. ❌ "Qt platform plugin not found"
   → 设置环境变量: set QT_QPA_PLATFORM=windows

如需更多帮助，请查看:
- 📖 QUICK_START.md
- 🔧 OPTIMIZATION_GUIDE.md
- 📋 QUICK_FIXES.md

技术支持: weather-system@support.com
        """
        print(guide)
    
    def create_launch_shortcut(self):
        """创建启动快捷方式"""
        try:
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            path = os.path.join(desktop, "天气分析系统.lnk")
            target = sys.executable
            arguments = str(self.project_root / "enhanced_launch.py")
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(path)
            shortcut.Targetpath = target
            shortcut.Arguments = arguments
            shortcut.WorkingDirectory = str(self.project_root)
            shortcut.IconLocation = str(self.project_root / "assets" / "weather.ico")
            shortcut.save()
            
            logger.info("✅ 创建桌面快捷方式成功")
            
        except Exception as e:
            logger.warning(f"⚠️  创建快捷方式失败: {str(e)}")
    
    def run(self):
        """运行启动器"""
        try:
            self.launch_application()
            
            # 创建快捷方式
            self.create_launch_shortcut()
            
        except KeyboardInterrupt:
            logger.info("\n👋 用户取消启动")
        except Exception as e:
            logger.error(f"❌ 启动器错误: {str(e)}")
            self.show_troubleshooting_guide()

if __name__ == "__main__":
    launcher = EnhancedLauncher()
    launcher.run()