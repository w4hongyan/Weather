#!/usr/bin/env python3
"""
增强版安装脚本
自动安装所有优化包和依赖
"""

import subprocess
import sys
import os
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedInstaller:
    """增强版安装器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.python_executable = sys.executable
        
        # 核心依赖
        self.core_packages = [
            "pandas>=1.5.0",
            "numpy>=1.21.0",
            "matplotlib>=3.5.0",
            "seaborn>=0.11.0",
            "scipy>=1.7.0",
            "PyQt5>=5.15.0",
            "requests>=2.25.0",
            "python-dateutil>=2.8.0",
            "holidays>=0.13.0"
        ]
        
        # 优化依赖
        self.enhanced_packages = [
            "qt-material>=2.8.0",
            "qasync>=0.23.0",
            "psutil>=5.8.0",
            "memory-profiler>=0.60.0",
            "pandera>=0.15.0",
            "pydantic>=1.10.0",
            "prophet>=1.1.0",
            "statsmodels>=0.13.0"
        ]
        
        # 可选依赖
        self.optional_packages = [
            "scikit-learn>=1.0.0",
            "tensorflow>=2.8.0",
            "plotly>=5.0.0",
            "dash>=2.0.0",
            "streamlit>=1.0.0"
        ]
    
    def check_pip_version(self):
        """检查pip版本"""
        try:
            result = subprocess.run([
                self.python_executable, '-m', 'pip', '--version'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                version_line = result.stdout.strip()
                logger.info(f"✅ pip版本: {version_line}")
                return True
            else:
                logger.error("❌ pip不可用")
                return False
                
        except Exception as e:
            logger.error(f"❌ pip检查失败: {str(e)}")
            return False
    
    def install_package(self, package_name: str, upgrade: bool = True) -> bool:
        """安装单个包"""
        try:
            cmd = [
                self.python_executable, '-m', 'pip', 'install',
                package_name
            ]
            
            if upgrade:
                cmd.append('--upgrade')
            
            logger.info(f"📦 安装: {package_name}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ 安装成功: {package_name}")
                return True
            else:
                logger.error(f"❌ 安装失败: {package_name}")
                logger.error(result.stderr)
                return False
                
        except Exception as e:
            logger.error(f"❌ 安装异常: {package_name} - {str(e)}")
            return False
    
    def install_packages(self, packages: list, category: str = "") -> bool:
        """安装包列表"""
        logger.info(f"🚀 开始安装{category}包...")
        
        success_count = 0
        for package in packages:
            if self.install_package(package):
                success_count += 1
        
        logger.info(f"📊 {category}包安装完成: {success_count}/{len(packages)}")
        return success_count == len(packages)
    
    def setup_chinese_fonts(self):
        """设置中文字体"""
        try:
            import matplotlib.pyplot as plt
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
            logger.info("✅ 中文字体配置完成")
        except Exception as e:
            logger.warning(f"⚠️  中文字体配置失败: {str(e)}")
    
    def create_requirements_file(self):
        """创建requirements文件"""
        requirements_content = """# 天气数据建模与分析系统 - 依赖列表

# 核心依赖
pandas>=1.5.0
numpy>=1.21.0
matplotlib>=3.5.0
seaborn>=0.11.0
scipy>=1.7.0
PyQt5>=5.15.0
requests>=2.25.0
python-dateutil>=2.8.0
holidays>=0.13.0

# 优化依赖
qt-material>=2.8.0
qasync>=0.23.0
psutil>=5.8.0
memory-profiler>=0.60.0
pandera>=0.15.0
pydantic>=1.10.0
prophet>=1.1.0
statsmodels>=0.13.0

# 可选依赖
scikit-learn>=1.0.0
tensorflow>=2.8.0
plotly>=5.0.0
dash>=2.0.0
streamlit>=1.0.0

# 开发依赖
pytest>=7.0.0
black>=22.0.0
flake8>=4.0.0
mypy>=0.950
"""
        
        try:
            with open(self.project_root / "requirements.txt", "w", encoding="utf-8") as f:
                f.write(requirements_content)
            logger.info("✅ requirements.txt 创建完成")
        except Exception as e:
            logger.error(f"❌ requirements.txt 创建失败: {str(e)}")
    
    def verify_installation(self) -> bool:
        """验证安装"""
        logger.info("🔍 验证安装...")
        
        test_imports = [
            'pandas', 'numpy', 'matplotlib', 'seaborn', 'scipy',
            'PyQt5', 'qt_material', 'qasync', 'psutil', 'prophet'
        ]
        
        failed_imports = []
        for module in test_imports:
            try:
                __import__(module)
                logger.info(f"✅ {module}")
            except ImportError:
                logger.error(f"❌ {module}")
                failed_imports.append(module)
        
        if failed_imports:
            logger.error(f"❌ 验证失败: {failed_imports}")
            return False
        
        logger.info("✅ 所有包验证通过")
        return True
    
    def install_all(self):
        """完整安装"""
        logger.info("🎯 开始增强版安装...")
        
        # 检查pip
        if not self.check_pip_version():
            logger.error("❌ pip检查失败")
            return False
        
        # 创建requirements文件
        self.create_requirements_file()
        
        # 安装核心包
        if not self.install_packages(self.core_packages, "核心"):
            logger.error("❌ 核心包安装失败")
            return False
        
        # 安装优化包
        if not self.install_packages(self.enhanced_packages, "优化"):
            logger.warning("⚠️  部分优化包安装失败")
        
        # 安装可选包
        logger.info("🎪 安装可选包（可选）...")
        for package in self.optional_packages:
            self.install_package(package)
        
        # 设置中文字体
        self.setup_chinese_fonts()
        
        # 验证安装
        if self.verify_installation():
            logger.info("🎉 增强版安装完成！")
            return True
        else:
            logger.error("❌ 安装验证失败")
            return False
    
    def quick_install(self):
        """快速安装"""
        logger.info("⚡ 快速安装模式...")
        
        try:
            # 使用requirements文件
            cmd = [
                self.python_executable, '-m', 'pip', 'install',
                '-r', str(self.project_root / 'requirements.txt')
            ]
            
            logger.info("🚀 执行快速安装...")
            result = subprocess.run(cmd, capture_output=False, text=True)
            
            if result.returncode == 0:
                logger.info("✅ 快速安装完成")
                return True
            else:
                logger.error("❌ 快速安装失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 快速安装异常: {str(e)}")
            return False

def main():
    """主函数"""
    print("\n" + "="*60)
    print("    🌤️  天气数据建模与分析系统 - 增强版安装器")
    print("="*60)
    print()
    
    installer = EnhancedInstaller()
    
    print("安装选项:")
    print("1. 🔧 完整安装（推荐）")
    print("2. ⚡ 快速安装（使用requirements.txt）")
    print("3. 🎯 仅安装缺失包")
    print()
    
    choice = input("请选择安装方式 (1-3): ").strip()
    
    if choice == "1":
        success = installer.install_all()
    elif choice == "2":
        success = installer.quick_install()
    elif choice == "3":
        success = installer.verify_installation()
    else:
        print("❌ 无效选择")
        return
    
    if success:
        print("\n🎉 安装完成！")
        print("\n下一步:")
        print("1. 运行: python enhanced_launch.py")
        print("2. 或双击: enhanced_launch.py")
        print("3. 查看: QUICK_START.md 获取使用指南")
    else:
        print("\n❌ 安装遇到问题")
        print("请查看日志或联系技术支持")

if __name__ == "__main__":
    main()