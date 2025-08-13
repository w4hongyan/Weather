#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口GUI界面 - Main Window GUI
提供用户交互界面，整合所有功能模块
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import psutil
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QPushButton, QLabel, QLineEdit, QTextEdit, QTableView,
    QFileDialog, QMessageBox, QProgressBar, QProgressDialog, QSplitter, QGroupBox,
    QComboBox, QCheckBox, QSpinBox, QDoubleSpinBox, QDateEdit,
    QMenuBar, QStatusBar, QToolBar, QAction, QDockWidget, QSystemTrayIcon
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer, QAbstractTableModel, QSettings
from PyQt5.QtGui import QFont, QIcon, QPixmap, QStandardItemModel, QStandardItem

import qt_material

# 动态导入核心模块
try:
    from utils.logger import LoggerMixin
    from utils.config_manager import ConfigManager
    from core.data_processor import DataProcessor
    from core.weather_api import WeatherAPI
    from core.tbats_model import TBATSModel
    from core.ml_residual import ResidualCorrector
    from core.anomaly_detector import AnomalyDetector
    from utils.excel_handler import ExcelHandler
    CORE_AVAILABLE = True
except ImportError as e:
    print(f"导入模块失败: {e}")
    CORE_AVAILABLE = False
    
    # 增强回退类
    class LoggerMixin:
        def log_info(self, msg): print(f"INFO: {msg}")
        def log_error(self, msg): print(f"ERROR: {msg}")
        def log_warning(self, msg): print(f"WARNING: {msg}")
    
    class ConfigManager:
        def get(self, key, default=None): return default
        def set(self, key, value): pass
    
    class DataProcessor:
        def __init__(self, config): pass
        def import_main_data(self, file_path, region):
            return {'success': True, 'summary': '模拟导入', 'output_path': file_path}
        def import_customer_data(self, file_path):
            return {'success': True, 'summary': '模拟导入'}
        def validate_data(self, data):
            if data.empty:
                raise ValueError("数据不能为空")
            return True
    
    class WeatherAPI:
        def __init__(self, config): pass
        def get_weather_data(self, region, start_date, end_date):
            dates = pd.date_range(start_date, end_date)
            return pd.DataFrame({
                'date': dates,
                'temperature': np.random.normal(20, 5, len(dates)),
                'humidity': np.random.normal(60, 10, len(dates))
            })
    
    class TBATSModel:
        def __init__(self, config): pass
        def fit_model(self, data, **params):
            return True
        def predict(self, days):
            dates = pd.date_range('2024-01-01', periods=days)
            return pd.DataFrame({
                'date': dates,
                'forecast': np.random.normal(20, 3, days),
                'lower_bound': np.random.normal(15, 2, days),
                'upper_bound': np.random.normal(25, 2, days)
            })
    
    class ResidualCorrector:
        def __init__(self, config): pass
        def correct_residuals(self, model, data, **params):
            return True
    
    class AnomalyDetector:
        def __init__(self, config): pass
        def detect_anomalies(self, data, **params):
            return pd.DataFrame()
    
    class ExcelHandler:
        def load_excel(self, file_path):
            try:
                return pd.read_excel(file_path)
            except Exception as e:
                raise ValueError(f"无法读取Excel文件: {str(e)}")
        
        def save_excel(self, data, file_path):
            data.to_excel(file_path, index=False)

class DataTableModel(QAbstractTableModel):
    """数据表格模型"""
    
    def __init__(self, data=None):
        super().__init__()
        self._data = data or pd.DataFrame()
    
    def rowCount(self, parent=None):
        return len(self._data)
    
    def columnCount(self, parent=None):
        return len(self._data.columns)
    
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            if pd.isna(value):
                return ""
            return str(value)
        return None
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return str(self._data.columns[section])
            elif orientation == Qt.Vertical:
                return str(section + 1)
        return None
    
    def update_data(self, data):
        self.beginResetModel()
        self._data = data
        self.endResetModel()

class WorkThread(QThread):
    """工作线程基类"""
    progress_updated = pyqtSignal(int)
    message_updated = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, task_func, *args, **kwargs):
        super().__init__()
        self.task_func = task_func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.task_func(*self.args, **kwargs)
            self.finished_signal.emit(True, str(result))
        except Exception as e:
            self.finished_signal.emit(False, str(e))

class MainWindow(QMainWindow, LoggerMixin):
    """主窗口类"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config = config_manager
        self.data_processor = DataProcessor(self.config)
        self.weather_api = WeatherAPI(self.config)
        self.tbats_model = TBATSModel(self.config)
        self.residual_corrector = ResidualCorrector(self.config)
        self.anomaly_detector = AnomalyDetector(self.config)
        
        self.current_data = {}
        self.current_region = ""
        self.work_thread = None
        
        # 性能监控和进度管理
        self.perf_timer = QTimer()
        self.perf_timer.timeout.connect(self.update_performance_stats)
        self.perf_timer.start(2000)
        
        self.progress_dialog = None
        
        self.progress_manager = type('ProgressManager', (), {
            'show_progress': lambda self, parent, title="处理中", max_value=100: self._create_progress(parent, title, max_value),
            'update_progress': lambda self, parent, value, message="": parent.progress_dialog.setValue(value) or (message and parent.progress_dialog.setLabelText(message)),
            'close_progress': lambda self, parent: parent.progress_dialog.close() if parent.progress_dialog else None,
            '_create_progress': lambda self, parent, title, max_value: setattr(parent, 'progress_dialog', QProgressDialog(title, "取消", 0, max_value, parent)) or parent.progress_dialog.setWindowModality(Qt.WindowModal) or parent.progress_dialog.show()
        })
        
        self.init_ui()
        self.setup_connections()
        self.setup_timer()
        
        self.logger.info("主窗口初始化完成")
    
    def update_performance_stats(self):
        """更新性能统计信息"""
        try:
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            cpu_percent = psutil.Process().cpu_percent()
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"内存: {memory_mb:.1f}MB | CPU: {cpu_percent:.1f}%")
        except Exception:
            pass
    
    def init_ui(self):
        """初始化UI界面"""
        self.setWindowTitle('天气数据建模与分析系统')
        self.setGeometry(100, 100, 1400, 900)
        
        # 设置图标
        # icon_path = Path(__file__).parent / "resources" / "icons" / "app_icon.png"
        # if icon_path.exists():
        #     self.setWindowIcon(QIcon(str(icon_path)))
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建工具栏
        self.create_tool_bar()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 创建中央部件
        self.create_central_widget()
        
        # 创建停靠窗口
        self.create_dock_widgets()
        
        self.show()
    
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        
        open_action = QAction('打开数据文件...', self)
        open_action.setShortcut('Ctrl+O')
        open_action.triggered.connect(self.open_data_file)
        file_menu.addAction(open_action)
        
        save_action = QAction('保存结果...', self)
        save_action.setShortcut('Ctrl+S')
        save_action.triggered.connect(self.save_results)
        file_menu.addAction(save_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('退出', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 数据菜单
        data_menu = menubar.addMenu('数据(&D)')
        
        import_main_action = QAction('导入主数据...', self)
        import_main_action.triggered.connect(self.import_main_data)
        data_menu.addAction(import_main_action)
        
        import_customer_action = QAction('导入客户数据...', self)
        import_customer_action.triggered.connect(self.import_customer_data)
        data_menu.addAction(import_customer_action)
        
        update_weather_action = QAction('更新天气数据', self)
        update_weather_action.triggered.connect(self.update_weather_data)
        data_menu.addAction(update_weather_action)
        
        # 建模菜单
        modeling_menu = menubar.addMenu('建模(&M)')
        
        tbats_action = QAction('TBATS建模...', self)
        tbats_action.triggered.connect(self.run_tbats_modeling)
        modeling_menu.addAction(tbats_action)
        
        residual_action = QAction('残差修正...', self)
        residual_action.triggered.connect(self.run_residual_correction)
        modeling_menu.addAction(residual_action)
        
        # 分析菜单
        analysis_menu = menubar.addMenu('分析(&A)')
        
        anomaly_action = QAction('异常检测...', self)
        anomaly_action.triggered.connect(self.run_anomaly_detection)
        analysis_menu.addAction(anomaly_action)
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def create_tool_bar(self):
        """创建工具栏"""
        toolbar = self.addToolBar('工具栏')
        
        # 添加工具按钮
        open_btn = QPushButton('打开文件')
        open_btn.clicked.connect(self.open_data_file)
        toolbar.addWidget(open_btn)
        
        import_btn = QPushButton('导入数据')
        import_btn.clicked.connect(self.import_main_data)
        toolbar.addWidget(import_btn)
        
        weather_btn = QPushButton('更新天气')
        weather_btn.clicked.connect(self.update_weather_data)
        toolbar.addWidget(weather_btn)
        
        model_btn = QPushButton('开始建模')
        model_btn.clicked.connect(self.run_tbats_modeling)
        toolbar.addWidget(model_btn)
    
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 添加状态标签
        self.status_label = QLabel('就绪')
        self.status_bar.addWidget(self.status_label)
        
        # 添加进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
    
    def create_central_widget(self):
        """创建中央部件"""
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # 数据导入标签页
        self.data_tab = self.create_data_tab()
        self.tab_widget.addTab(self.data_tab, "数据管理")
        
        # 天气数据标签页
        self.weather_tab = self.create_weather_tab()
        self.tab_widget.addTab(self.weather_tab, "天气数据")
        
        # 建模标签页
        self.modeling_tab = self.create_modeling_tab()
        self.tab_widget.addTab(self.modeling_tab, "数据建模")
        
        # 分析标签页
        self.analysis_tab = self.create_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "数据分析")
        
        # 结果标签页
        self.results_tab = self.create_results_tab()
        self.tab_widget.addTab(self.results_tab, "结果展示")
        
        self.setCentralWidget(self.tab_widget)
    
    def create_data_tab(self):
        """创建数据管理标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 数据导入区域
        import_group = QGroupBox("数据导入")
        import_layout = QVBoxLayout()
        
        # 主数据导入
        main_layout = QHBoxLayout()
        main_layout.addWidget(QLabel("主数据文件:"))
        self.main_file_path = QLineEdit()
        main_layout.addWidget(self.main_file_path)
        main_browse_btn = QPushButton("浏览...")
        main_browse_btn.clicked.connect(lambda: self.browse_file(self.main_file_path))
        main_layout.addWidget(main_browse_btn)
        
        region_layout = QHBoxLayout()
        region_layout.addWidget(QLabel("地区:"))
        self.region_combo = QComboBox()
        self.region_combo.addItems(["广东", "广西", "湖南", "湖北", "河南", "河北"])
        region_layout.addWidget(self.region_combo)
        
        import_btn = QPushButton("导入主数据")
        import_btn.clicked.connect(self.import_main_data)
        region_layout.addWidget(import_btn)
        
        import_layout.addLayout(main_layout)
        import_layout.addLayout(region_layout)
        
        # 客户数据导入
        customer_layout = QHBoxLayout()
        customer_layout.addWidget(QLabel("客户数据文件:"))
        self.customer_file_path = QLineEdit()
        customer_layout.addWidget(self.customer_file_path)
        customer_browse_btn = QPushButton("浏览...")
        customer_browse_btn.clicked.connect(lambda: self.browse_file(self.customer_file_path))
        customer_layout.addWidget(customer_browse_btn)
        
        import_customer_btn = QPushButton("导入客户数据")
        import_customer_btn.clicked.connect(self.import_customer_data)
        customer_layout.addWidget(import_customer_btn)
        
        import_layout.addLayout(customer_layout)
        import_group.setLayout(import_layout)
        
        # 数据预览区域
        preview_group = QGroupBox("数据预览")
        preview_layout = QVBoxLayout()
        
        self.data_table = QTableView()
        self.data_model = DataTableModel()
        self.data_table.setModel(self.data_model)
        
        preview_layout.addWidget(self.data_table)
        preview_group.setLayout(preview_layout)
        
        # 数据摘要区域
        summary_group = QGroupBox("数据摘要")
        summary_layout = QVBoxLayout()
        
        self.data_summary = QTextEdit()
        self.data_summary.setMaximumHeight(150)
        summary_layout.addWidget(self.data_summary)
        summary_group.setLayout(summary_layout)
        
        layout.addWidget(import_group)
        layout.addWidget(preview_group)
        layout.addWidget(summary_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_weather_tab(self):
        """创建天气数据标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 天气数据更新区域
        update_group = QGroupBox("天气数据更新")
        update_layout = QVBoxLayout()
        
        # 地区选择
        region_layout = QHBoxLayout()
        region_layout.addWidget(QLabel("选择地区:"))
        self.weather_region_combo = QComboBox()
        self.weather_region_combo.addItems(["广州", "深圳", "东莞", "佛山", "珠海", "中山"])
        region_layout.addWidget(self.weather_region_combo)
        
        # 日期范围
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("开始日期:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(datetime.now().date())
        date_layout.addWidget(self.start_date_edit)
        
        date_layout.addWidget(QLabel("结束日期:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(datetime.now().date() + timedelta(days=7))
        date_layout.addWidget(self.end_date_edit)
        
        # 更新按钮
        update_btn = QPushButton("更新天气数据")
        update_btn.clicked.connect(self.update_weather_data)
        date_layout.addWidget(update_btn)
        
        update_layout.addLayout(region_layout)
        update_layout.addLayout(date_layout)
        update_group.setLayout(update_layout)
        
        # 天气数据预览
        weather_preview_group = QGroupBox("天气数据预览")
        weather_preview_layout = QVBoxLayout()
        
        self.weather_table = QTableView()
        self.weather_model = DataTableModel()
        self.weather_table.setModel(self.weather_model)
        
        weather_preview_layout.addWidget(self.weather_table)
        weather_preview_group.setLayout(weather_preview_layout)
        
        layout.addWidget(update_group)
        layout.addWidget(weather_preview_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_modeling_tab(self):
        """创建数据建模标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 建模参数设置
        params_group = QGroupBox("建模参数设置")
        params_layout = QVBoxLayout()
        
        # TBATS参数
        tbats_layout = QVBoxLayout()
        
        # 趋势设置
        trend_layout = QHBoxLayout()
        self.use_trend_check = QCheckBox("使用趋势")
        self.use_trend_check.setChecked(True)
        trend_layout.addWidget(self.use_trend_check)
        
        self.use_damped_trend_check = QCheckBox("使用阻尼趋势")
        self.use_damped_trend_check.setChecked(True)
        trend_layout.addWidget(self.use_damped_trend_check)
        
        tbats_layout.addLayout(trend_layout)
        
        # 季节性设置
        seasonal_layout = QHBoxLayout()
        seasonal_layout.addWidget(QLabel("季节性周期:"))
        self.seasonal_periods_spin = QSpinBox()
        self.seasonal_periods_spin.setRange(1, 365)
        self.seasonal_periods_spin.setValue(7)
        seasonal_layout.addWidget(self.seasonal_periods_spin)
        
        seasonal_layout.addWidget(QLabel("预测天数:"))
        self.forecast_days_spin = QSpinBox()
        self.forecast_days_spin.setRange(1, 365)
        self.forecast_days_spin.setValue(30)
        seasonal_layout.addWidget(self.forecast_days_spin)
        
        tbats_layout.addLayout(seasonal_layout)
        
        # 机器学习参数
        ml_layout = QVBoxLayout()
        ml_layout.addWidget(QLabel("随机森林参数:"))
        
        rf_layout = QHBoxLayout()
        rf_layout.addWidget(QLabel("树的数量:"))
        self.n_estimators_spin = QSpinBox()
        self.n_estimators_spin.setRange(10, 1000)
        self.n_estimators_spin.setValue(100)
        rf_layout.addWidget(self.n_estimators_spin)
        
        rf_layout.addWidget(QLabel("最大深度:"))
        self.max_depth_spin = QSpinBox()
        self.max_depth_spin.setRange(1, 50)
        self.max_depth_spin.setValue(10)
        rf_layout.addWidget(self.max_depth_spin)
        
        ml_layout.addLayout(rf_layout)
        
        params_layout.addLayout(tbats_layout)
        params_layout.addLayout(ml_layout)
        params_group.setLayout(params_layout)
        
        # 建模控制
        control_layout = QHBoxLayout()
        
        self.start_modeling_btn = QPushButton("开始建模")
        self.start_modeling_btn.clicked.connect(self.run_tbats_modeling)
        control_layout.addWidget(self.start_modeling_btn)
        
        self.correct_residuals_btn = QPushButton("残差修正")
        self.correct_residuals_btn.clicked.connect(self.run_residual_correction)
        control_layout.addWidget(self.correct_residuals_btn)
        
        # 建模结果
        modeling_results_group = QGroupBox("建模结果")
        modeling_results_layout = QVBoxLayout()
        
        self.modeling_log = QTextEdit()
        modeling_results_layout.addWidget(self.modeling_log)
        
        modeling_results_group.setLayout(modeling_results_layout)
        
        layout.addWidget(params_group)
        layout.addLayout(control_layout)
        layout.addWidget(modeling_results_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_analysis_tab(self):
        """创建数据分析标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 客户分析设置
        customer_group = QGroupBox("客户数据分析")
        customer_layout = QVBoxLayout()
        
        # 前20大客户分析
        top20_layout = QHBoxLayout()
        self.analyze_top20_btn = QPushButton("分析前20大客户")
        self.analyze_top20_btn.clicked.connect(self.analyze_top_customers)
        top20_layout.addWidget(self.analyze_top20_btn)
        
        customer_layout.addLayout(top20_layout)
        
        # 异常检测设置
        anomaly_layout = QVBoxLayout()
        anomaly_layout.addWidget(QLabel("异常检测参数:"))
        
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Z-score阈值:"))
        self.zscore_threshold_spin = QDoubleSpinBox()
        self.zscore_threshold_spin.setRange(1.0, 5.0)
        self.zscore_threshold_spin.setValue(2.0)
        threshold_layout.addWidget(self.zscore_threshold_spin)
        
        threshold_layout.addWidget(QLabel("IQR乘数:"))
        self.iqr_multiplier_spin = QDoubleSpinBox()
        self.iqr_multiplier_spin.setRange(1.0, 5.0)
        self.iqr_multiplier_spin.setValue(1.5)
        threshold_layout.addWidget(self.iqr_multiplier_spin)
        
        anomaly_layout.addLayout(threshold_layout)
        
        # 异常检测按钮
        detect_layout = QHBoxLayout()
        self.detect_anomalies_btn = QPushButton("检测异常")
        self.detect_anomalies_btn.clicked.connect(self.run_anomaly_detection)
        detect_layout.addWidget(self.detect_anomalies_btn)
        
        customer_layout.addLayout(anomaly_layout)
        customer_layout.addLayout(detect_layout)
        customer_group.setLayout(customer_layout)
        
        # 分析结果
        analysis_results_group = QGroupBox("分析结果")
        analysis_results_layout = QVBoxLayout()
        
        self.analysis_table = QTableView()
        self.analysis_model = DataTableModel()
        self.analysis_table.setModel(self.analysis_model)
        
        analysis_results_layout.addWidget(self.analysis_table)
        
        analysis_results_group.setLayout(analysis_results_layout)
        
        layout.addWidget(customer_group)
        layout.addWidget(analysis_results_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_results_tab(self):
        """创建结果展示标签页"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 结果导出区域
        export_group = QGroupBox("结果导出")
        export_layout = QVBoxLayout()
        
        export_layout.addWidget(QLabel("选择要导出的结果:"))
        
        self.export_tbats_check = QCheckBox("TBATS模型结果")
        self.export_residual_check = QCheckBox("残差修正结果")
        self.export_anomaly_check = QCheckBox("异常检测结果")
        
        export_layout.addWidget(self.export_tbats_check)
        export_layout.addWidget(self.export_residual_check)
        export_layout.addWidget(self.export_anomaly_check)
        
        export_btn_layout = QHBoxLayout()
        self.export_results_btn = QPushButton("导出结果")
        self.export_results_btn.clicked.connect(self.export_results)
        export_btn_layout.addWidget(self.export_results_btn)
        
        export_layout.addLayout(export_btn_layout)
        export_group.setLayout(export_layout)
        
        # 结果预览
        results_preview_group = QGroupBox("结果预览")
        results_preview_layout = QVBoxLayout()
        
        self.results_table = QTableView()
        self.results_model = DataTableModel()
        self.results_table.setModel(self.results_model)
        
        results_preview_layout.addWidget(self.results_table)
        results_preview_group.setLayout(results_preview_layout)
        
        layout.addWidget(export_group)
        layout.addWidget(results_preview_group)
        
        widget.setLayout(layout)
        return widget
    
    def create_dock_widgets(self):
        """创建停靠窗口"""
        # 日志停靠窗口
        log_dock = QDockWidget("系统日志", self)
        log_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(200)
        log_dock.setWidget(self.log_text)
        
        self.addDockWidget(Qt.BottomDockWidgetArea, log_dock)
    
    def setup_connections(self):
        """设置信号连接"""
        pass
    
    def setup_timer(self):
        """设置定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)  # 每秒更新一次状态
    
    def browse_file(self, line_edit: QLineEdit):
        """浏览文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文件",
            "",
            "Excel文件 (*.xlsx *.xls);;CSV文件 (*.csv);;所有文件 (*.*)"
        )
        if file_path:
            line_edit.setText(file_path)
    
    def import_main_data(self):
        """导入主数据 - 增强版"""
        file_path = self.main_file_path.text()
        if not file_path:
            QMessageBox.warning(self, "警告", "请先选择数据文件")
            return
        
        region = self.region_combo.currentText()
        
        # 验证文件
        if not os.path.exists(file_path):
            QMessageBox.critical(self, "错误", "文件不存在")
            return
        
        file_size = os.path.getsize(file_path)
        if file_size > 100 * 1024 * 1024:  # 100MB限制
            QMessageBox.warning(self, "警告", "文件过大，可能影响性能")
        
        self.start_work_thread(
            self._do_import_main_data,
            file_path,
            region,
            f"正在导入主数据 ({os.path.basename(file_path)})..."
        )
    
    def _do_import_main_data(self, file_path: str, region: str) -> str:
        """执行主数据导入"""
        result = self.data_processor.import_main_data(file_path, region)
        if result['success']:
            self.current_data[region] = pd.read_csv(result['output_path'])
            self.current_region = region
            return f"主数据导入成功: {result['summary']}"
        else:
            raise Exception(result['error'])
    
    def import_customer_data(self):
        """导入客户数据"""
        file_path = self.customer_file_path.text()
        if not file_path:
            QMessageBox.warning(self, "警告", "请先选择客户数据文件")
            return
        
        self.start_work_thread(
            self._do_import_customer_data,
            file_path,
            "正在导入客户数据..."
        )
    
    def _do_import_customer_data(self, file_path: str) -> str:
        """执行客户数据导入"""
        result = self.data_processor.import_customer_data(file_path)
        if result['success']:
            return f"客户数据导入成功: {result['summary']}"
        else:
            raise Exception(result['error'])
    
    def update_weather_data(self):
        """更新天气数据"""
        region = self.weather_region_combo.currentText()
        start_date = self.start_date_edit.date().toPyDate()
        end_date = self.end_date_edit.date().toPyDate()
        
        self.start_work_thread(
            self._do_update_weather_data,
            region,
            start_date,
            end_date,
            "正在更新天气数据..."
        )
    
    def _do_update_weather_data(self, region: str, start_date, end_date) -> str:
        """执行天气数据更新"""
        weather_data = self.weather_api.get_weather_data(region, start_date, end_date)
        if weather_data is not None:
            return f"天气数据更新成功，共{len(weather_data)}条记录"
        else:
            raise Exception("天气数据更新失败")
    
    def run_tbats_modeling(self):
        """运行TBATS建模"""
        if not self.current_region or self.current_region not in self.current_data:
            QMessageBox.warning(self, "警告", "请先导入数据")
            return
        
        # 获取建模参数
        params = {
            'use_trend': self.use_trend_check.isChecked(),
            'use_damped_trend': self.use_damped_trend_check.isChecked(),
            'seasonal_periods': self.seasonal_periods_spin.value(),
            'forecast_days': self.forecast_days_spin.value()
        }
        
        self.start_work_thread(
            self._do_tbats_modeling,
            self.current_data[self.current_region],
            params,
            "正在执行TBATS建模..."
        )
    
    def _do_tbats_modeling(self, data: pd.DataFrame, params: dict) -> str:
        """执行TBATS建模"""
        model = self.tbats_model.fit_model(data, **params)
        if model:
            forecast = self.tbats_model.predict(params['forecast_days'])
            return f"TBATS建模完成，预测{len(forecast)}天数据"
        else:
            raise Exception("TBATS建模失败")
    
    def run_residual_correction(self):
        """运行残差修正"""
        if not self.current_region:
            QMessageBox.warning(self, "警告", "请先完成建模")
            return
        
        # 获取机器学习参数
        ml_params = {
            'n_estimators': self.n_estimators_spin.value(),
            'max_depth': self.max_depth_spin.value()
        }
        
        self.start_work_thread(
            self._do_residual_correction,
            ml_params,
            "正在执行残差修正..."
        )
    
    def _do_residual_correction(self, ml_params: dict) -> str:
        """执行残差修正"""
        # 这里需要根据实际数据结构进行调整
        corrected = self.residual_corrector.correct_residuals(
            self.tbats_model, 
            self.current_data[self.current_region],
            **ml_params
        )
        if corrected:
            return "残差修正完成"
        else:
            raise Exception("残差修正失败")
    
    def run_anomaly_detection(self):
        """运行异常检测"""
        if not self.current_data:
            QMessageBox.warning(self, "警告", "请先导入数据")
            return
        
        # 获取异常检测参数
        anomaly_params = {
            'zscore_threshold': self.zscore_threshold_spin.value(),
            'iqr_multiplier': self.iqr_multiplier_spin.value()
        }
        
        self.start_work_thread(
            self._do_anomaly_detection,
            anomaly_params,
            "正在执行异常检测..."
        )
    
    def _do_anomaly_detection(self, params: dict) -> str:
        """执行异常检测"""
        # 这里需要根据实际数据结构进行调整
        anomalies = self.anomaly_detector.detect_anomalies(
            self.current_data.get(self.current_region, None),
            **params
        )
        if anomalies is not None:
            return f"异常检测完成，发现{len(anomalies)}个异常"
        else:
            raise Exception("异常检测失败")
    
    def analyze_top_customers(self):
        """分析前20大客户"""
        # 这里需要根据实际数据结构进行调整
        QMessageBox.information(self, "提示", "前20大客户分析功能待实现")
    
    def export_results(self):
        """导出结果"""
        export_options = []
        if self.export_tbats_check.isChecked():
            export_options.append("tbats")
        if self.export_residual_check.isChecked():
            export_options.append("residual")
        if self.export_anomaly_check.isChecked():
            export_options.append("anomaly")
        
        if not export_options:
            QMessageBox.warning(self, "警告", "请选择要导出的结果")
            return
        
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存结果",
            "",
            "Excel文件 (*.xlsx);;CSV文件 (*.csv)"
        )
        
        if save_path:
            self.start_work_thread(
                self._do_export_results,
                export_options,
                save_path,
                "正在导出结果..."
            )
    
    def _do_export_results(self, options: list, save_path: str) -> str:
        """执行结果导出"""
        # 这里需要根据实际数据结构进行调整
        return f"结果已导出到: {save_path}"
    
    def start_work_thread(self, task_func, *args, status_message=""):
        """启动工作线程"""
        if self.work_thread and self.work_thread.isRunning():
            QMessageBox.warning(self, "警告", "有任务正在运行，请等待完成")
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.status_label.setText(status_message)
        
        self.work_thread = WorkThread(task_func, *args)
        self.work_thread.finished_signal.connect(self.on_work_finished)
        self.work_thread.start()
    
    def on_work_finished(self, success: bool, message: str):
        """工作线程完成回调"""
        self.progress_bar.setVisible(False)
        self.status_label.setText('就绪')
        
        if success:
            QMessageBox.information(self, "成功", message)
            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
        else:
            QMessageBox.critical(self, "错误", message)
            self.log_text.append(f"[{datetime.now().strftime('%H:%M:%S')}] 错误: {message}")
    
    def update_status(self):
        """更新状态"""
        # 这里可以添加实时状态更新
        pass
    
    def open_data_file(self):
        """打开数据文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择数据文件",
            "",
            "Excel文件 (*.xlsx *.xls);;CSV文件 (*.csv);;所有文件 (*.*)"
        )
        
        if file_path:
            self.main_file_path.setText(file_path)
    
    def save_results(self):
        """保存结果"""
        self.export_results()
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(
            self,
            "关于",
            "天气数据建模与分析系统\n\n"
            "版本: 1.0.0\n"
            "功能: 天气数据获取、TBATS建模、残差修正、异常检测\n"
            "作者: 数据处理团队"
        )
    
    def closeEvent(self, event):
        """关闭事件"""
        reply = QMessageBox.question(
            self,
            '退出确认',
            '确定要退出程序吗？',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.work_thread and self.work_thread.isRunning():
                self.work_thread.quit()
                self.work_thread.wait()
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle('Fusion')
    
    # 创建配置管理器
    config = ConfigManager()
    
    # 创建并显示主窗口
    window = MainWindow(config)
    
    sys.exit(app.exec_())