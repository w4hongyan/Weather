#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel文件处理器 - Excel File Handler
处理Excel文件的读取、写入和验证
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
import logging
from datetime import datetime, timedelta

from .logger import LoggerMixin

class ExcelHandler(LoggerMixin):
    """Excel文件处理器类"""
    
    def __init__(self):
        super().__init__()
        self.supported_extensions = ['.xlsx', '.xls', '.xlsm']
    
    def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """
        验证Excel文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            path = Path(file_path)
            
            # 检查文件是否存在
            if not path.exists():
                return False, f"文件不存在: {file_path}"
            
            # 检查文件扩展名
            if path.suffix.lower() not in self.supported_extensions:
                return False, f"不支持的文件格式: {path.suffix}"
            
            # 尝试读取文件
            pd.read_excel(file_path, nrows=1)
            
            return True, ""
            
        except Exception as e:
            return False, f"文件验证失败: {str(e)}"
    
    def read_excel_file(
        self, 
        file_path: str, 
        sheet_name: Optional[str] = None,
        date_columns: Optional[List[str]] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        读取Excel文件
        
        Args:
            file_path: 文件路径
            sheet_name: 工作表名称，None表示读取第一个工作表
            date_columns: 需要解析为日期的列名列表
            **kwargs: 其他pandas.read_excel参数
            
        Returns:
            DataFrame对象
        """
        try:
            self.logger.info(f"读取Excel文件: {file_path}")
            
            # 设置默认参数
            default_kwargs = {
                'sheet_name': sheet_name or 0,
                'header': 0,
                'index_col': None,
                'parse_dates': bool(date_columns),
                'date_parser': self._parse_dates if date_columns else None
            }
            default_kwargs.update(kwargs)
            
            # 读取文件
            df = pd.read_excel(file_path, **default_kwargs)
            
            # 处理日期列
            if date_columns:
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
            
            self.logger.info(f"成功读取文件，共{len(df)}行{len(df.columns)}列")
            return df
            
        except Exception as e:
            self.logger.error(f"读取Excel文件失败: {str(e)}")
            raise
    
    def write_excel_file(
        self,
        data: pd.DataFrame,
        file_path: str,
        sheet_name: str = "Sheet1",
        include_index: bool = False,
        format_headers: bool = True,
        **kwargs
    ) -> bool:
        """
        写入Excel文件
        
        Args:
            data: 要写入的DataFrame
            file_path: 输出文件路径
            sheet_name: 工作表名称
            include_index: 是否包含索引
            format_headers: 是否格式化表头
            **kwargs: 其他pandas.to_excel参数
            
        Returns:
            是否成功
        """
        try:
            self.logger.info(f"写入Excel文件: {file_path}")
            
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            if format_headers:
                # 使用openpyxl格式化输出
                with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                    data.to_excel(
                        writer, 
                        sheet_name=sheet_name, 
                        index=include_index,
                        **kwargs
                    )
                    
                    # 获取工作表
                    worksheet = writer.sheets[sheet_name]
                    
                    # 格式化表头
                    self._format_worksheet_headers(worksheet, data)
                    
                    # 调整列宽
                    self._adjust_column_widths(worksheet, data)
            else:
                # 简单写入
                data.to_excel(file_path, sheet_name=sheet_name, index=include_index, **kwargs)
            
            self.logger.info("Excel文件写入成功")
            return True
            
        except Exception as e:
            self.logger.error(f"写入Excel文件失败: {str(e)}")
            return False
    
    def append_to_excel(
        self,
        data: pd.DataFrame,
        file_path: str,
        sheet_name: str = "Sheet1"
    ) -> bool:
        """
        追加数据到现有Excel文件
        
        Args:
            data: 要追加的DataFrame
            file_path: 文件路径
            sheet_name: 工作表名称
            
        Returns:
            是否成功
        """
        try:
            self.logger.info(f"追加数据到Excel文件: {file_path}")
            
            if Path(file_path).exists():
                # 读取现有数据
                existing_data = self.read_excel_file(file_path, sheet_name=sheet_name)
                # 合并数据
                combined_data = pd.concat([existing_data, data], ignore_index=True)
            else:
                combined_data = data
            
            # 写入合并后的数据
            return self.write_excel_file(combined_data, file_path, sheet_name)
            
        except Exception as e:
            self.logger.error(f"追加数据失败: {str(e)}")
            return False
    
    def read_multiple_sheets(self, file_path: str) -> Dict[str, pd.DataFrame]:
        """
        读取Excel文件的所有工作表
        
        Args:
            file_path: 文件路径
            
        Returns:
            工作表名称到DataFrame的字典
        """
        try:
            self.logger.info(f"读取多工作表Excel文件: {file_path}")
            
            # 获取所有工作表名称
            excel_file = pd.ExcelFile(file_path)
            sheets = {}
            
            for sheet_name in excel_file.sheet_names:
                sheets[sheet_name] = pd.read_excel(file_path, sheet_name=sheet_name)
            
            self.logger.info(f"成功读取{len(sheets)}个工作表")
            return sheets
            
        except Exception as e:
            self.logger.error(f"读取多工作表失败: {str(e)}")
            raise
    
    def get_excel_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取Excel文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        try:
            self.logger.info(f"获取Excel文件信息: {file_path}")
            
            # 读取文件
            excel_file = pd.ExcelFile(file_path)
            
            info = {
                'file_path': file_path,
                'file_size': Path(file_path).stat().st_size,
                'sheet_names': excel_file.sheet_names,
                'sheets_info': {}
            }
            
            # 获取每个工作表的信息
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                info['sheets_info'][sheet_name] = {
                    'rows': len(df),
                    'columns': len(df.columns),
                    'columns_list': df.columns.tolist(),
                    'memory_usage': df.memory_usage(deep=True).sum()
                }
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取文件信息失败: {str(e)}")
            raise
    
    def create_summary_report(
        self,
        data: pd.DataFrame,
        output_path: str,
        title: str = "数据摘要报告"
    ) -> bool:
        """
        创建数据摘要报告
        
        Args:
            data: 数据DataFrame
            output_path: 输出文件路径
            title: 报告标题
            
        Returns:
            是否成功
        """
        try:
            self.logger.info(f"创建数据摘要报告: {output_path}")
            
            # 创建摘要统计
            summary_stats = data.describe(include='all')
            
            # 创建缺失值统计
            missing_stats = pd.DataFrame({
                'Missing_Count': data.isnull().sum(),
                'Missing_Percentage': (data.isnull().sum() / len(data) * 100).round(2)
            })
            
            # 创建数据类型信息
            dtype_info = pd.DataFrame({
                'Data_Type': data.dtypes.astype(str),
                'Unique_Values': data.nunique()
            })
            
            # 写入Excel
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # 写入数据
                data.to_excel(writer, sheet_name='原始数据', index=False)
                summary_stats.to_excel(writer, sheet_name='统计摘要')
                missing_stats.to_excel(writer, sheet_name='缺失值统计')
                dtype_info.to_excel(writer, sheet_name='数据类型')
                
                # 格式化工作表
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    self._format_worksheet_headers(worksheet, None)
                    self._adjust_column_widths(worksheet, None)
            
            self.logger.info("数据摘要报告创建成功")
            return True
            
        except Exception as e:
            self.logger.error(f"创建摘要报告失败: {str(e)}")
            return False
    
    def _parse_dates(self, date_series):
        """解析日期列"""
        return pd.to_datetime(date_series, errors='coerce')
    
    def _format_worksheet_headers(self, worksheet, df=None):
        """格式化工作表表头"""
        # 设置表头样式
        header_font = Font(
            name='Microsoft YaHei',
            size=11,
            bold=True,
            color='FFFFFF'
        )
        header_fill = PatternFill(
            start_color='366092',
            end_color='366092',
            fill_type='solid'
        )
        header_alignment = Alignment(
            horizontal='center',
            vertical='center',
            wrap_text=True
        )
        
        # 应用表头样式
        for cell in worksheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
    
    def _adjust_column_widths(self, worksheet, df=None):
        """调整列宽"""
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

# 使用示例
if __name__ == "__main__":
    handler = ExcelHandler()
    
    # 创建测试数据
    test_data = pd.DataFrame({
        '日期': pd.date_range('2023-01-01', periods=10),
        '数值': np.random.randn(10),
        '地区': ['广东'] * 10
    })
    
    # 测试写入
    handler.write_excel_file(test_data, "test_output.xlsx")
    
    # 测试读取
    df = handler.read_excel_file("test_output.xlsx")
    print(df.head())