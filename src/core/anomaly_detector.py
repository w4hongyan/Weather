#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异常检测模块 - Anomaly Detection Module
检测客户数据的异常现象
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from scipy import stats
import warnings
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.logger import LoggerMixin
from utils.config_manager import ConfigManager

# 算法支持检测
SKLEARN_AVAILABLE = False

try:
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.covariance import EllipticEnvelope
    from sklearn.neighbors import LocalOutlierFactor
    SKLEARN_AVAILABLE = True
except ImportError:
    pass

class AnomalyDetector(LoggerMixin):
    """异常检测器类 - 检测客户数据的异常现象"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config = config_manager
        self.sensitivity = self.config.get('anomaly_detection.sensitivity', 'medium')
        self.top_customers_count = self.config.get('anomaly_detection.top_customers_count', 20)
        self.alert_threshold = self.config.get('anomaly_detection.alert_threshold', 2.0)
        
        # 设置敏感度对应的阈值
        self.sensitivity_thresholds = {
            'low': 3.0,
            'medium': 2.0,
            'high': 1.5
        }
        
        self.current_threshold = self.sensitivity_thresholds.get(self.sensitivity, 2.0)
    
    def analyze_customer_data(
        self,
        customer_data: pd.DataFrame,
        customer_column: str = 'customer_id',
        date_column: str = 'date',
        value_column: str = 'value',
        region_column: str = 'region'
    ) -> Dict[str, Any]:
        """
        分析客户数据并检测异常
        
        Args:
            customer_data: 客户数据DataFrame
            customer_column: 客户ID列名
            date_column: 日期列名
            value_column: 数值列名
            region_column: 地区列名
            
        Returns:
            分析结果字典
        """
        try:
            self.logger.info("开始客户数据分析")
            
            # 数据预处理
            df = customer_data.copy()
            df[date_column] = pd.to_datetime(df[date_column])
            df = df.sort_values([customer_column, date_column])
            
            # 计算前20大客户
            top_customers = self._get_top_customers(df, customer_column, value_column)
            
            # 分析每个大客户的异常
            anomaly_results = {}
            
            for customer_id in top_customers['customer_id']:
                customer_df = df[df[customer_column] == customer_id].copy()
                
                if len(customer_df) >= 7:  # 至少7天数据
                    anomalies = self._detect_customer_anomalies(customer_df, value_column, date_column)
                    anomaly_results[customer_id] = anomalies
            
            # 生成总体报告
            report = self._generate_anomaly_report(
                df, top_customers, anomaly_results, 
                customer_column, value_column, region_column
            )
            
            self.logger.info(f"客户数据分析完成，发现{len([a for a in anomaly_results.values() if a['has_anomaly']])}个客户有异常")
            return report
            
        except Exception as e:
            self.logger.error(f"客户数据分析失败: {str(e)}")
            raise
    
    def _get_top_customers(
        self,
        df: pd.DataFrame,
        customer_column: str,
        value_column: str
    ) -> pd.DataFrame:
        """获取前20大客户"""
        try:
            # 计算每个客户的总数据量
            customer_totals = df.groupby(customer_column)[value_column].sum().reset_index()
            customer_totals.columns = ['customer_id', 'total_value']
            
            # 排序并获取前20
            top_customers = customer_totals.nlargest(self.top_customers_count, 'total_value')
            
            # 计算占比
            total_sum = customer_totals['total_value'].sum()
            top_customers['percentage'] = (top_customers['total_value'] / total_sum * 100).round(2)
            
            return top_customers
            
        except Exception as e:
            self.logger.error(f"获取大客户列表失败: {str(e)}")
            raise
    
    def _detect_customer_anomalies(
        self,
        customer_df: pd.DataFrame,
        value_column: str,
        date_column: str
    ) -> Dict[str, Any]:
        """检测单个客户的异常"""
        try:
            customer_df = customer_df.copy()
            values = customer_df[value_column]
            
            # 基础统计
            mean_val = values.mean()
            std_val = values.std()
            
            # 1. Z-score异常检测
            z_scores = np.abs(stats.zscore(values))
            z_anomalies = z_scores > self.current_threshold
            
            # 2. IQR异常检测
            Q1 = values.quantile(0.25)
            Q3 = values.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            iqr_anomalies = (values < lower_bound) | (values > upper_bound)
            
            # 3. 日环比异常检测
            if len(values) > 1:
                daily_change = values.pct_change()
                daily_anomalies = np.abs(daily_change) > 0.5  # 50%变化
            else:
                daily_anomalies = pd.Series([False] * len(values))
            
            # 4. 周环比异常检测
            if len(values) > 7:
                weekly_change = values.pct_change(periods=7)
                weekly_anomalies = np.abs(weekly_change) > 0.3  # 30%变化
            else:
                weekly_anomalies = pd.Series([False] * len(values))
            
            # 5. 移动平均异常检测
            if len(values) >= 7:
                rolling_mean = values.rolling(window=7).mean()
                rolling_std = values.rolling(window=7).std()
                ma_anomalies = np.abs(values - rolling_mean) > (2 * rolling_std)
            else:
                ma_anomalies = pd.Series([False] * len(values))
            
            # 合并异常结果
            all_anomalies = z_anomalies | iqr_anomalies | daily_anomalies | weekly_anomalies | ma_anomalies
            
            # 获取异常日期和值
            anomaly_dates = customer_df[date_column][all_anomalies]
            anomaly_values = values[all_anomalies]
            
            # 计算异常指标
            anomaly_metrics = {
                'max_z_score': z_scores.max() if len(z_scores) > 0 else 0,
                'max_daily_change': daily_change.abs().max() if len(daily_change) > 0 else 0,
                'max_weekly_change': weekly_change.abs().max() if len(weekly_change) > 0 else 0,
                'anomaly_rate': all_anomalies.sum() / len(all_anomalies) if len(all_anomalies) > 0 else 0
            }
            
            return {
                'has_anomaly': all_anomalies.any(),
                'anomaly_count': all_anomalies.sum(),
                'anomaly_dates': anomaly_dates.tolist(),
                'anomaly_values': anomaly_values.tolist(),
                'mean_value': mean_val,
                'std_value': std_val,
                'anomaly_metrics': anomaly_metrics,
                'last_value': values.iloc[-1],
                'last_date': customer_df[date_column].iloc[-1]
            }
            
        except Exception as e:
            self.logger.error(f"客户异常检测失败: {str(e)}")
            return {'has_anomaly': False, 'error': str(e)}
    
    def _generate_anomaly_report(
        self,
        df: pd.DataFrame,
        top_customers: pd.DataFrame,
        anomaly_results: Dict[str, Any],
        customer_column: str,
        value_column: str,
        region_column: str
    ) -> Dict[str, Any]:
        """生成异常报告"""
        try:
            report = {
                'summary': {
                    'total_customers': len(df[customer_column].unique()),
                    'top_customers_analyzed': len(top_customers),
                    'customers_with_anomalies': len([r for r in anomaly_results.values() if r.get('has_anomaly', False)]),
                    'total_anomalies': sum([r.get('anomaly_count', 0) for r in anomaly_results.values()]),
                    'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'top_customers': top_customers.to_dict('records'),
                'anomaly_details': anomaly_results,
                'regional_summary': self._generate_regional_summary(df, region_column, value_column),
                'alerts': self._generate_alerts(anomaly_results)
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"生成异常报告失败: {str(e)}")
            return {'error': str(e)}
    
    def _generate_regional_summary(
        self,
        df: pd.DataFrame,
        region_column: str,
        value_column: str
    ) -> Dict[str, Any]:
        """生成地区摘要"""
        try:
            regional_summary = {}
            
            for region in df[region_column].unique():
                region_df = df[df[region_column] == region]
                
                regional_summary[region] = {
                    'total_customers': len(region_df['customer_id'].unique()),
                    'total_value': region_df[value_column].sum(),
                    'avg_value': region_df[value_column].mean(),
                    'max_value': region_df[value_column].max(),
                    'min_value': region_df[value_column].min()
                }
            
            return regional_summary
            
        except Exception as e:
            self.logger.error(f"生成地区摘要失败: {str(e)}")
            return {}
    
    def _generate_alerts(self, anomaly_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """生成异常警报"""
        try:
            alerts = []
            
            for customer_id, result in anomaly_results.items():
                if result.get('has_anomaly', False) and result.get('anomaly_count', 0) > 0:
                    # 获取最新异常
                    latest_anomaly_date = max(result['anomaly_dates']) if result['anomaly_dates'] else None
                    latest_anomaly_value = result['anomaly_values'][-1] if result['anomaly_values'] else None
                    
                    # 计算严重程度
                    severity = 'high' if result['anomaly_metrics']['max_z_score'] > 3 else 'medium'
                    severity = 'low' if result['anomaly_metrics']['max_z_score'] < 2 else severity
                    
                    alerts.append({
                        'customer_id': customer_id,
                        'severity': severity,
                        'anomaly_count': result['anomaly_count'],
                        'latest_anomaly_date': latest_anomaly_date,
                        'latest_anomaly_value': latest_anomaly_value,
                        'deviation_from_mean': abs(latest_anomaly_value - result['mean_value']) if latest_anomaly_value else 0,
                        'z_score': result['anomaly_metrics']['max_z_score']
                    })
            
            # 按严重程度排序
            severity_order = {'high': 0, 'medium': 1, 'low': 2}
            alerts.sort(key=lambda x: severity_order.get(x['severity'], 3))
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"生成警报失败: {str(e)}")
            return []
    
    def export_anomaly_report(
        self,
        report: Dict[str, Any],
        output_path: str,
        format: str = 'excel'
    ) -> bool:
        """
        导出异常报告
        
        Args:
            report: 异常报告
            output_path: 输出路径
            format: 输出格式 ('excel' 或 'csv')
            
        Returns:
            是否成功
        """
        try:
            self.logger.info(f"导出异常报告: {output_path}")
            
            # 确保目录存在
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            if format.lower() == 'excel':
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    # 摘要信息
                    summary_df = pd.DataFrame([report['summary']])
                    summary_df.to_excel(writer, sheet_name='摘要', index=False)
                    
                    # 大客户列表
                    top_customers_df = pd.DataFrame(report['top_customers'])
                    top_customers_df.to_excel(writer, sheet_name='大客户列表', index=False)
                    
                    # 异常警报
                    alerts_df = pd.DataFrame(report['alerts'])
                    if not alerts_df.empty:
                        alerts_df.to_excel(writer, sheet_name='异常警报', index=False)
                    
                    # 地区摘要
                    regional_df = pd.DataFrame.from_dict(report['regional_summary'], orient='index')
                    regional_df.to_excel(writer, sheet_name='地区摘要')
                    
            elif format.lower() == 'csv':
                # 导出为多个CSV文件
                base_path = Path(output_path).stem
                
                pd.DataFrame([report['summary']]).to_csv(
                    f"{base_path}_summary.csv", index=False, encoding='utf-8-sig'
                )
                
                pd.DataFrame(report['top_customers']).to_csv(
                    f"{base_path}_top_customers.csv", index=False, encoding='utf-8-sig'
                )
                
                if report['alerts']:
                    pd.DataFrame(report['alerts']).to_csv(
                        f"{base_path}_alerts.csv", index=False, encoding='utf-8-sig'
                    )
            
            self.logger.info("异常报告导出成功")
            return True
            
        except Exception as e:
            self.logger.error(f"导出异常报告失败: {str(e)}")
            return False
    
    def get_real_time_alerts(self, customer_data: pd.DataFrame) -> List[Dict[str, Any]]:
        """获取实时异常警报"""
        try:
            # 只分析最近3天的数据
            latest_date = customer_data['date'].max()
            cutoff_date = latest_date - timedelta(days=3)
            
            recent_data = customer_data[customer_data['date'] >= cutoff_date]
            
            if recent_data.empty:
                return []
            
            # 快速异常检测
            alerts = []
            
            for customer_id in recent_data['customer_id'].unique():
                customer_df = recent_data[recent_data['customer_id'] == customer_id]
                
                if len(customer_df) >= 2:
                    # 简单的异常检测
                    values = customer_df['value']
                    recent_value = values.iloc[-1]
                    
                    if len(values) > 1:
                        mean_val = values.iloc[:-1].mean()
                        std_val = values.iloc[:-1].std()
                        
                        if std_val > 0:
                            z_score = abs(recent_value - mean_val) / std_val
                            
                            if z_score > self.current_threshold:
                                alerts.append({
                                    'customer_id': customer_id,
                                    'alert_type': 'real_time',
                                    'latest_value': recent_value,
                                    'expected_range': f"{mean_val:.2f} ± {2*std_val:.2f}",
                                    'z_score': z_score,
                                    'alert_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                })
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"实时异常检测失败: {str(e)}")
            return []

# 使用示例
if __name__ == "__main__":
    from ..utils.config_manager import ConfigManager
    
    config = ConfigManager()
    detector = AnomalyDetector(config)
    
    # 创建测试数据
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', periods=30, freq='D')
    
    # 生成异常数据
    customer_data = []
    for i in range(25):  # 25个客户
        customer_id = f'CUST_{i+1:03d}'
        base_value = np.random.uniform(100, 1000)
        
        for date in dates:
            value = base_value + np.random.normal(0, base_value * 0.1)
            
            # 添加一些异常
            if np.random.random() < 0.05:  # 5%概率异常
                value *= np.random.uniform(1.5, 3.0)
            
            customer_data.append({
                'customer_id': customer_id,
                'date': date,
                'value': value,
                'region': f'区域_{i % 3 + 1}'
            })
    
    df = pd.DataFrame(customer_data)
    
    # 执行异常检测
    report = detector.analyze_customer_data(df)
    
    print("异常检测摘要:")
    print(f"总客户数: {report['summary']['total_customers']}")
    print(f"异常客户数: {report['summary']['customers_with_anomalies']}")
    print(f"总异常数: {report['summary']['total_anomalies']}")
    
    if report['alerts']:
        print("\n异常警报:")
        for alert in report['alerts'][:5]:  # 显示前5个
            print(f"客户 {alert['customer_id']}: {alert['severity']}级别异常")