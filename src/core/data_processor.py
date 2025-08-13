#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据处理核心模块 - Data Processing Core Module
处理数据导入、清洗和预处理
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import hashlib
import json

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.logger import LoggerMixin
from utils.config_manager import ConfigManager
from utils.excel_handler import ExcelHandler

class DataProcessor(LoggerMixin):
    """数据处理核心类"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config = config_manager
        self.excel_handler = ExcelHandler()
        self.processed_data_cache = {}
    
    def import_main_data(
        self,
        file_path: str,
        region: str,
        date_column: str = 'date',
        value_column: str = 'value',
        **kwargs
    ) -> Dict[str, Any]:
        """
        导入主数据（数据A、B、C等）
        
        Args:
            file_path: 文件路径
            region: 地区名称
            date_column: 日期列名
            value_column: 数值列名
            **kwargs: 其他参数
            
        Returns:
            导入结果字典
        """
        try:
            self.logger.info(f"导入{region}地区主数据: {file_path}")
            
            # 验证文件
            is_valid, error_msg = self.excel_handler.validate_file(file_path)
            if not is_valid:
                raise ValueError(error_msg)
            
            # 读取数据
            df = self.excel_handler.read_excel_file(
                file_path, 
                date_columns=[date_column],
                **kwargs
            )
            
            # 数据验证和清洗
            processed_df = self._process_main_data(df, date_column, value_column, region)
            
            # 生成数据摘要
            summary = self._generate_data_summary(processed_df, region)
            
            # 保存处理后的数据
            output_path = self._save_processed_data(processed_df, region, 'main_data')
            
            result = {
                'success': True,
                'region': region,
                'original_rows': len(df),
                'processed_rows': len(processed_df),
                'date_range': {
                    'start': processed_df[date_column].min().strftime('%Y-%m-%d'),
                    'end': processed_df[date_column].max().strftime('%Y-%m-%d')
                },
                'summary': summary,
                'output_path': str(output_path),
                'data_hash': self._calculate_data_hash(processed_df)
            }
            
            self.logger.info(f"{region}地区主数据导入成功，共{len(processed_df)}条记录")
            return result
            
        except Exception as e:
            self.logger.error(f"主数据导入失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def import_customer_data(
        self,
        file_path: str,
        customer_column: str = 'customer_id',
        date_column: str = 'date',
        value_column: str = 'value',
        region_column: str = 'region',
        **kwargs
    ) -> Dict[str, Any]:
        """
        导入客户详细数据
        
        Args:
            file_path: 文件路径
            customer_column: 客户ID列名
            date_column: 日期列名
            value_column: 数值列名
            region_column: 地区列名
            **kwargs: 其他参数
            
        Returns:
            导入结果字典
        """
        try:
            self.logger.info(f"导入客户详细数据: {file_path}")
            
            # 验证文件
            is_valid, error_msg = self.excel_handler.validate_file(file_path)
            if not is_valid:
                raise ValueError(error_msg)
            
            # 读取数据
            df = self.excel_handler.read_excel_file(
                file_path,
                date_columns=[date_column],
                **kwargs
            )
            
            # 数据验证和清洗
            processed_df = self._process_customer_data(
                df, customer_column, date_column, value_column, region_column
            )
            
            # 生成客户数据摘要
            summary = self._generate_customer_summary(processed_df, customer_column, region_column)
            
            # 保存处理后的数据
            output_path = self._save_processed_data(processed_df, 'all', 'customer_data')
            
            result = {
                'success': True,
                'original_rows': len(df),
                'processed_rows': len(processed_df),
                'unique_customers': processed_df[customer_column].nunique(),
                'unique_regions': processed_df[region_column].nunique(),
                'date_range': {
                    'start': processed_df[date_column].min().strftime('%Y-%m-%d'),
                    'end': processed_df[date_column].max().strftime('%Y-%m-%d')
                },
                'summary': summary,
                'output_path': str(output_path),
                'data_hash': self._calculate_data_hash(processed_df)
            }
            
            self.logger.info(f"客户数据导入成功，共{len(processed_df)}条记录，{processed_df[customer_column].nunique()}个客户")
            return result
            
        except Exception as e:
            self.logger.error(f"客户数据导入失败: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def merge_weather_data(
        self,
        main_data: pd.DataFrame,
        weather_data: pd.DataFrame,
        date_column: str = 'date',
        region_column: str = 'region'
    ) -> pd.DataFrame:
        """
        合并天气数据与主数据
        
        Args:
            main_data: 主数据DataFrame
            weather_data: 天气数据DataFrame
            date_column: 日期列名
            region_column: 地区列名
            
        Returns:
            合并后的DataFrame
        """
        try:
            self.logger.info("开始合并天气数据")
            
            # 确保日期格式一致
            main_data[date_column] = pd.to_datetime(main_data[date_column])
            weather_data[date_column] = pd.to_datetime(weather_data[date_column])
            
            # 合并数据
            merged_df = pd.merge(
                main_data,
                weather_data,
                on=[date_column, region_column],
                how='left'
            )
            
            # 处理天气数据缺失值
            weather_columns = ['temperature', 'humidity', 'pressure', 'wind_speed', 'precipitation']
            for col in weather_columns:
                if col in merged_df.columns:
                    merged_df[col] = merged_df[col].interpolate().fillna(method='ffill').fillna(method='bfill')
            
            self.logger.info(f"天气数据合并完成，共{len(merged_df)}条记录")
            return merged_df
            
        except Exception as e:
            self.logger.error(f"合并天气数据失败: {str(e)}")
            raise
    
    def prepare_modeling_data(
        self,
        data: pd.DataFrame,
        date_column: str = 'date',
        value_column: str = 'value',
        region: str = None
    ) -> pd.DataFrame:
        """
        准备建模数据
        
        Args:
            data: 原始数据DataFrame
            date_column: 日期列名
            value_column: 数值列名
            region: 地区名称
            
        Returns:
            建模用DataFrame
        """
        try:
            self.logger.info("准备建模数据")
            
            df = data.copy()
            
            # 确保日期列格式正确
            df[date_column] = pd.to_datetime(df[date_column])
            
            # 检查缺失值
            missing_count = df[value_column].isnull().sum()
            if missing_count > 0:
                self.logger.warning(f"发现{missing_count}个缺失值，将使用插值填充")
                df[value_column] = df[value_column].interpolate()
                df[value_column] = df[value_column].fillna(method='ffill').fillna(method='bfill')
            
            # 检查异常值
            outliers = self._detect_outliers(df[value_column])
            if outliers.sum() > 0:
                self.logger.warning(f"发现{outliers.sum()}个异常值，将使用中位数替换")
                median_val = df[value_column].median()
                df.loc[outliers, value_column] = median_val
            
            # 确保数据连续性
            df = self._ensure_daily_continuity(df, date_column, value_column)
            
            # 添加建模特征
            df = self._add_modeling_features(df, date_column, value_column)
            
            self.logger.info(f"建模数据准备完成，共{len(df)}条记录")
            return df
            
        except Exception as e:
            self.logger.error(f"建模数据准备失败: {str(e)}")
            raise
    
    def _process_main_data(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str,
        region: str
    ) -> pd.DataFrame:
        """处理主数据"""
        try:
            processed_df = df.copy()
            
            # 重命名列
            column_mapping = {
                date_column: 'date',
                value_column: 'value'
            }
            processed_df = processed_df.rename(columns=column_mapping)
            
            # 添加地区信息
            processed_df['region'] = region
            
            # 数据类型转换
            processed_df['date'] = pd.to_datetime(processed_df['date'])
            processed_df['value'] = pd.to_numeric(processed_df['value'], errors='coerce')
            
            # 去除重复值
            processed_df = processed_df.drop_duplicates(subset=['date', 'region'])
            
            # 按日期排序
            processed_df = processed_df.sort_values('date')
            
            return processed_df
            
        except Exception as e:
            self.logger.error(f"主数据处理失败: {str(e)}")
            raise
    
    def _process_customer_data(
        self,
        df: pd.DataFrame,
        customer_column: str,
        date_column: str,
        value_column: str,
        region_column: str
    ) -> pd.DataFrame:
        """处理客户数据"""
        try:
            processed_df = df.copy()
            
            # 重命名列
            column_mapping = {
                customer_column: 'customer_id',
                date_column: 'date',
                value_column: 'value',
                region_column: 'region'
            }
            processed_df = processed_df.rename(columns=column_mapping)
            
            # 数据类型转换
            processed_df['date'] = pd.to_datetime(processed_df['date'])
            processed_df['value'] = pd.to_numeric(processed_df['value'], errors='coerce')
            processed_df['customer_id'] = processed_df['customer_id'].astype(str)
            processed_df['region'] = processed_df['region'].astype(str)
            
            # 去除重复值
            processed_df = processed_df.drop_duplicates(subset=['customer_id', 'date', 'region'])
            
            # 按客户和日期排序
            processed_df = processed_df.sort_values(['customer_id', 'date'])
            
            return processed_df
            
        except Exception as e:
            self.logger.error(f"客户数据处理失败: {str(e)}")
            raise
    
    def _generate_data_summary(self, df: pd.DataFrame, region: str) -> Dict[str, Any]:
        """生成数据摘要"""
        try:
            values = df['value'].dropna()
            
            summary = {
                'region': region,
                'total_records': len(df),
                'date_range': {
                    'start': df['date'].min().strftime('%Y-%m-%d'),
                    'end': df['date'].max().strftime('%Y-%m-%d')
                },
                'value_stats': {
                    'mean': round(values.mean(), 2),
                    'std': round(values.std(), 2),
                    'min': round(values.min(), 2),
                    'max': round(values.max(), 2),
                    'median': round(values.median(), 2)
                },
                'missing_values': df['value'].isnull().sum(),
                'zero_values': (values == 0).sum(),
                'negative_values': (values < 0).sum()
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"生成数据摘要失败: {str(e)}")
            return {}
    
    def _generate_customer_summary(self, df: pd.DataFrame, customer_column: str, region_column: str) -> Dict[str, Any]:
        """生成客户数据摘要"""
        try:
            summary = {
                'total_customers': df[customer_column].nunique(),
                'total_regions': df[region_column].nunique(),
                'customer_distribution': df.groupby(region_column)[customer_column].nunique().to_dict(),
                'value_distribution': df.groupby(region_column)['value'].sum().to_dict(),
                'date_span': {
                    'start': df['date'].min().strftime('%Y-%m-%d'),
                    'end': df['date'].max().strftime('%Y-%m-%d')
                }
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"生成客户摘要失败: {str(e)}")
            return {}
    
    def _detect_outliers(self, series: pd.Series) -> pd.Series:
        """检测异常值"""
        try:
            Q1 = series.quantile(0.25)
            Q3 = series.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            return (series < lower_bound) | (series > upper_bound)
            
        except Exception as e:
            self.logger.error(f"异常值检测失败: {str(e)}")
            return pd.Series([False] * len(series))
    
    def _ensure_daily_continuity(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str
    ) -> pd.DataFrame:
        """确保数据日连续性"""
        try:
            # 创建完整的日期范围
            date_range = pd.date_range(
                start=df[date_column].min(),
                end=df[date_column].max(),
                freq='D'
            )
            
            # 创建完整日期DataFrame
            full_df = pd.DataFrame({date_column: date_range})
            
            # 合并数据
            merged_df = pd.merge(full_df, df, on=date_column, how='left')
            
            # 插值填充缺失值
            if value_column in merged_df.columns:
                merged_df[value_column] = merged_df[value_column].interpolate()
                merged_df[value_column] = merged_df[value_column].fillna(method='ffill').fillna(method='bfill')
            
            return merged_df
            
        except Exception as e:
            self.logger.error(f"数据连续性处理失败: {str(e)}")
            return df
    
    def _add_modeling_features(
        self,
        df: pd.DataFrame,
        date_column: str,
        value_column: str
    ) -> pd.DataFrame:
        """添加建模特征"""
        try:
            # 确保日期列为索引
            if date_column in df.columns:
                df = df.set_index(date_column)
            
            # 添加时间特征
            df['day_of_week'] = df.index.dayofweek
            df['day_of_month'] = df.index.day
            df['month'] = df.index.month
            df['quarter'] = df.index.quarter
            df['is_weekend'] = (df.index.dayofweek >= 5).astype(int)
            
            # 添加滞后特征
            for lag in [1, 2, 3, 7]:
                df[f'lag_{lag}'] = df[value_column].shift(lag)
            
            # 添加滚动统计特征
            for window in [7, 14, 30]:
                if len(df) >= window:
                    df[f'rolling_mean_{window}'] = df[value_column].rolling(window=window).mean()
                    df[f'rolling_std_{window}'] = df[value_column].rolling(window=window).std()
            
            # 重置索引
            df = df.reset_index()
            
            return df
            
        except Exception as e:
            self.logger.error(f"建模特征添加失败: {str(e)}")
            return df
    
    def _save_processed_data(
        self,
        df: pd.DataFrame,
        region: str,
        data_type: str
    ) -> Path:
        """保存处理后的数据"""
        try:
            # 获取保存路径
            processed_dir = Path(self.config.get('paths.processed_data_dir', '../data/processed'))
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{data_type}_{region}_{timestamp}.csv"
            file_path = processed_dir / filename
            
            # 保存数据
            df.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            return file_path
            
        except Exception as e:
            self.logger.error(f"数据保存失败: {str(e)}")
            raise
    
    def _calculate_data_hash(self, df: pd.DataFrame) -> str:
        """计算数据哈希值"""
        try:
            # 将DataFrame转换为字符串并计算哈希
            data_str = df.to_string()
            return hashlib.md5(data_str.encode()).hexdigest()
            
        except Exception as e:
            self.logger.error(f"计算数据哈希失败: {str(e)}")
            return ""
    
    def get_data_quality_report(self, df: pd.DataFrame) -> Dict[str, Any]:
        """获取数据质量报告"""
        try:
            report = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'missing_values': df.isnull().sum().to_dict(),
                'data_types': df.dtypes.astype(str).to_dict(),
                'duplicate_rows': df.duplicated().sum(),
                'memory_usage': df.memory_usage(deep=True).sum()
            }
            
            # 数值列统计
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                report['numeric_summary'] = df[numeric_cols].describe().to_dict()
            
            # 日期列统计
            date_cols = df.select_dtypes(include=['datetime64']).columns
            if len(date_cols) > 0:
                date_stats = {}
                for col in date_cols:
                    date_stats[col] = {
                        'min': df[col].min().strftime('%Y-%m-%d'),
                        'max': df[col].max().strftime('%Y-%m-%d'),
                        'range_days': (df[col].max() - df[col].min()).days
                    }
                report['date_summary'] = date_stats
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成数据质量报告失败: {str(e)}")
            return {}
    
    def validate_data_format(self, df: pd.DataFrame, required_columns: List[str]) -> Dict[str, Any]:
        """验证数据格式"""
        try:
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            validation_result = {
                'is_valid': len(missing_columns) == 0,
                'missing_columns': missing_columns,
                'available_columns': df.columns.tolist(),
                'column_types': df.dtypes.astype(str).to_dict()
            }
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"数据格式验证失败: {str(e)}")
            return {'is_valid': False, 'error': str(e)}

# 使用示例
if __name__ == "__main__":
    from ..utils.config_manager import ConfigManager
    import numpy as np
    
    config = ConfigManager()
    processor = DataProcessor(config)
    
    # 创建测试数据
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    values = 100 + 10 * np.sin(2 * np.pi * np.arange(100) / 7) + np.random.normal(0, 5, 100)
    
    test_data = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    # 测试主数据导入
    result = processor.import_main_data("test_data.xlsx", "广东")
    print("导入结果:", result)
    
    # 测试数据质量报告
    quality_report = processor.get_data_quality_report(test_data)
    print("数据质量报告:", quality_report)