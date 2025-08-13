#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理器测试文件
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import tempfile
import os
import sys

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.data_processor import DataProcessor
from utils.config_manager import ConfigManager

class TestDataProcessor(unittest.TestCase):
    """测试数据处理器"""
    
    def setUp(self):
        """测试前设置"""
        self.config = ConfigManager()
        self.processor = DataProcessor(self.config)
        
        # 创建测试数据
        self.create_test_data()
    
    def create_test_data(self):
        """创建测试数据"""
        # 创建主数据
        dates = pd.date_range('2023-01-01', periods=100, freq='D')
        values = 100 + 10 * np.sin(2 * np.pi * np.arange(100) / 7) + np.random.normal(0, 5, 100)
        
        self.test_main_data = pd.DataFrame({
            'date': dates,
            'value': values,
            'region': '广东'
        })
        
        # 创建客户数据
        customers = [f'CUST_{i:03d}' for i in range(1, 21)]
        customer_data = []
        
        for customer in customers:
            for i in range(30):
                date = dates[i]
                value = np.random.normal(50, 10)
                customer_data.append({
                    'customer_id': customer,
                    'date': date,
                    'value': value,
                    'region': '广东'
                })
        
        self.test_customer_data = pd.DataFrame(customer_data)
    
    def test_import_main_data(self):
        """测试主数据导入"""
        # 创建临时Excel文件
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            self.test_main_data.to_excel(tmp.name, index=False)
            tmp_path = tmp.name
        
        try:
            result = self.processor.import_main_data(tmp_path, "广东")
            
            self.assertTrue(result['success'])
            self.assertEqual(result['region'], "广东")
            self.assertIn('summary', result)
            self.assertIn('output_path', result)
            
        finally:
            os.unlink(tmp_path)
    
    def test_import_customer_data(self):
        """测试客户数据导入"""
        # 创建临时Excel文件
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            self.test_customer_data.to_excel(tmp.name, index=False)
            tmp_path = tmp.name
        
        try:
            result = self.processor.import_customer_data(tmp_path)
            
            self.assertTrue(result['success'])
            self.assertIn('unique_customers', result)
            self.assertIn('unique_regions', result)
            self.assertIn('summary', result)
            
        finally:
            os.unlink(tmp_path)
    
    def test_merge_weather_data(self):
        """测试天气数据合并"""
        # 创建天气数据
        weather_data = pd.DataFrame({
            'date': self.test_main_data['date'],
            'region': '广东',
            'temperature': np.random.normal(25, 5, len(self.test_main_data)),
            'humidity': np.random.normal(70, 10, len(self.test_main_data)),
            'pressure': np.random.normal(1013, 20, len(self.test_main_data))
        })
        
        merged = self.processor.merge_weather_data(
            self.test_main_data,
            weather_data
        )
        
        self.assertEqual(len(merged), len(self.test_main_data))
        self.assertIn('temperature', merged.columns)
        self.assertIn('humidity', merged.columns)
        self.assertIn('pressure', merged.columns)
    
    def test_prepare_modeling_data(self):
        """测试建模数据准备"""
        prepared = self.processor.prepare_modeling_data(
            self.test_main_data
        )
        
        self.assertIsInstance(prepared, pd.DataFrame)
        self.assertIn('day_of_week', prepared.columns)
        self.assertIn('month', prepared.columns)
        self.assertIn('lag_1', prepared.columns)
        self.assertIn('rolling_mean_7', prepared.columns)
    
    def test_detect_outliers(self):
        """测试异常值检测"""
        # 创建包含异常值的数据
        data = pd.Series([1, 2, 3, 4, 5, 100, 2, 3, 4, 5])
        outliers = self.processor._detect_outliers(data)
        
        self.assertTrue(outliers.iloc[5])  # 100应该是异常值
        self.assertEqual(outliers.sum(), 1)
    
    def test_data_quality_report(self):
        """测试数据质量报告"""
        report = self.processor.get_data_quality_report(self.test_main_data)
        
        self.assertIn('total_rows', report)
        self.assertIn('total_columns', report)
        self.assertIn('missing_values', report)
        self.assertIn('numeric_summary', report)
        self.assertEqual(report['total_rows'], len(self.test_main_data))
    
    def test_validate_data_format(self):
        """测试数据格式验证"""
        required_columns = ['date', 'value']
        validation = self.processor.validate_data_format(
            self.test_main_data,
            required_columns
        )
        
        self.assertTrue(validation['is_valid'])
        self.assertEqual(validation['missing_columns'], [])
        
        # 测试缺失列的情况
        incomplete_data = self.test_main_data.drop(columns=['value'])
        validation = self.processor.validate_data_format(
            incomplete_data,
            required_columns
        )
        
        self.assertFalse(validation['is_valid'])
        self.assertIn('value', validation['missing_columns'])

class TestExcelHandler(unittest.TestCase):
    """测试Excel处理器"""
    
    def setUp(self):
        """测试前设置"""
        from utils.excel_handler import ExcelHandler
        self.excel_handler = ExcelHandler()
    
    def test_validate_file(self):
        """测试文件验证"""
        # 创建临时文件
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            # 创建有效Excel文件
            df = pd.DataFrame({'A': [1, 2, 3], 'B': [4, 5, 6]})
            df.to_excel(tmp_path, index=False)
            
            is_valid, error_msg = self.excel_handler.validate_file(tmp_path)
            self.assertTrue(is_valid)
            self.assertEqual(error_msg, "")
            
        finally:
            os.unlink(tmp_path)
        
        # 测试无效文件
        is_valid, error_msg = self.excel_handler.validate_file("nonexistent.xlsx")
        self.assertFalse(is_valid)
        self.assertNotEqual(error_msg, "")
    
    def test_read_excel_file(self):
        """测试读取Excel文件"""
        # 创建测试数据
        df = pd.DataFrame({
            'date': pd.date_range('2023-01-01', periods=10),
            'value': range(10),
            'category': ['A', 'B'] * 5
        })
        
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            df.to_excel(tmp.name, index=False)
            tmp_path = tmp.name
        
        try:
            read_df = self.excel_handler.read_excel_file(tmp_path)
            
            self.assertEqual(len(read_df), len(df))
            self.assertListEqual(list(read_df.columns), list(df.columns))
            
        finally:
            os.unlink(tmp_path)

if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)