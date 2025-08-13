#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TBATS时间序列建模模块 - TBATS Time Series Modeling Module
实现TBATS模型拟合和预测功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import json
from pathlib import Path
import logging
from functools import lru_cache

# TBATS建模相关导入
TBATS_AVAILABLE = False
PROPHET_AVAILABLE = False
ARIMA_AVAILABLE = False

# 日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from tbats import TBATS
    TBATS_AVAILABLE = True
    logger.info("✅ TBATS库已安装")
except ImportError:
    logger.warning("❌ TBATS库未安装")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
    logger.info("✅ Prophet库已安装")
except ImportError:
    logger.warning("❌ Prophet库未安装")

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    ARIMA_AVAILABLE = True
    logger.info("✅ ARIMA库已安装")
except ImportError:
    logger.warning("❌ ARIMA库未安装")

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.logger import LoggerMixin
from utils.config_manager import ConfigManager

class TBATSModel(LoggerMixin):
    """TBATS时间序列建模类"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config = config_manager
        self.model = None
        self.model_summary = {}
        self.fitted_values = None
        self.residuals = None
        
        if not TBATS_AVAILABLE:
            self.logger.warning("TBATS库不可用，将使用模拟建模")
    
    def fit_model(
        self,
        data: pd.DataFrame,
        target_column: str,
        date_column: str = 'date',
        use_trend: Optional[bool] = None,
        use_damped_trend: Optional[bool] = None,
        use_arma_errors: Optional[bool] = None,
        seasonal_periods: Optional[List[int]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        拟合TBATS模型
        
        Args:
            data: 输入数据DataFrame
            target_column: 目标列名
            date_column: 日期列名
            use_trend: 是否使用趋势组件
            use_damped_trend: 是否使用阻尼趋势
            use_arma_errors: 是否使用ARMA误差
            seasonal_periods: 季节性周期列表
            **kwargs: 其他TBATS参数
            
        Returns:
            模型摘要字典
        """
        try:
            self.logger.info(f"开始拟合TBATS模型，目标列: {target_column}")
            
            # 获取配置参数
            tbats_config = self.config.get_tbats_config()
            
            # 合并参数
            use_trend = use_trend if use_trend is not None else tbats_config.get('use_trend', True)
            use_damped_trend = use_damped_trend if use_damped_trend is not None else tbats_config.get('use_damped_trend', False)
            use_arma_errors = use_arma_errors if use_arma_errors is not None else tbats_config.get('use_arma_errors', True)
            seasonal_periods = seasonal_periods or tbats_config.get('seasonal_periods', [7, 365])
            
            # 准备数据
            df = data.copy()
            df[date_column] = pd.to_datetime(df[date_column])
            df = df.sort_values(date_column)
            df = df.set_index(date_column)
            
            # 检查缺失值
            if df[target_column].isnull().any():
                self.logger.warning("目标列存在缺失值，将使用前向填充")
                df[target_column] = df[target_column].fillna(method='ffill')
            
            # 确保数据是数值类型
            y = pd.to_numeric(df[target_column], errors='coerce')
            
            if y.isnull().any():
                self.logger.error("目标列包含非数值数据")
                raise ValueError("目标列必须全部为数值类型")
            
            if not TBATS_AVAILABLE:
                # 模拟TBATS建模
                self.model_summary = self._simulate_tbats_fit(y, use_trend, use_damped_trend, seasonal_periods)
                self.fitted_values = self._simulate_fitted_values(y)
                self.residuals = y - self.fitted_values
            else:
                # 实际TBATS建模
                estimator = TBATS(
                    seasonal_periods=seasonal_periods,
                    use_trend=use_trend,
                    use_damped_trend=use_damped_trend,
                    use_arma_errors=use_arma_errors,
                    **kwargs
                )
                
                self.model = estimator.fit(y)
                self.fitted_values = self.model.y_hat
                self.residuals = self.model.resid
                
                # 生成模型摘要
                self.model_summary = self._generate_model_summary()
            
            self.logger.info("TBATS模型拟合完成")
            return self.model_summary
            
        except Exception as e:
            self.logger.error(f"TBATS模型拟合失败: {str(e)}")
            raise
    
    def predict(
        self,
        steps: int,
        confidence_level: Optional[float] = None
    ) -> pd.DataFrame:
        """
        进行预测
        
        Args:
            steps: 预测步数
            confidence_level: 置信水平
            
        Returns:
            预测结果DataFrame
        """
        try:
            self.logger.info(f"开始TBATS模型预测，步数: {steps}")
            
            if not self.model and not self.model_summary:
                raise ValueError("请先拟合模型")
            
            confidence_level = confidence_level or self.config.get('modeling.tbats.confidence_level', 0.95)
            
            if not TBATS_AVAILABLE:
                # 模拟预测
                forecast = self._simulate_forecast(steps, confidence_level)
            else:
                # 实际预测
                forecast = self.model.forecast(steps=steps, confidence_level=confidence_level)
                
                # 创建预测DataFrame
                last_date = self.fitted_values.index[-1] if hasattr(self.fitted_values, 'index') else datetime.now()
                forecast_dates = pd.date_range(
                    start=last_date + timedelta(days=1),
                    periods=steps,
                    freq='D'
                )
                
                forecast_df = pd.DataFrame({
                    'date': forecast_dates,
                    'forecast': forecast['mean'] if isinstance(forecast, dict) else forecast,
                    'lower_bound': forecast['lower_bound'] if isinstance(forecast, dict) else None,
                    'upper_bound': forecast['upper_bound'] if isinstance(forecast, dict) else None
                })
                
                forecast = forecast_df
            
            self.logger.info("TBATS模型预测完成")
            return forecast
            
        except Exception as e:
            self.logger.error(f"TBATS模型预测失败: {str(e)}")
            raise
    
    def get_model_summary(self) -> Dict[str, Any]:
        """获取模型摘要"""
        return self.model_summary
    
    def get_residuals(self) -> pd.Series:
        """获取残差"""
        return self.residuals
    
    def get_fitted_values(self) -> pd.Series:
        """获取拟合值"""
        return self.fitted_values
    
    def save_model(self, file_path: str) -> bool:
        """保存模型"""
        try:
            self.logger.info(f"保存TBATS模型: {file_path}")
            
            model_data = {
                'model_summary': self.model_summary,
                'fitted_values': self.fitted_values.tolist() if self.fitted_values is not None else None,
                'residuals': self.residuals.tolist() if self.residuals is not None else None,
                'config': {
                    'use_trend': self.model_summary.get('use_trend'),
                    'use_damped_trend': self.model_summary.get('use_damped_trend'),
                    'seasonal_periods': self.model_summary.get('seasonal_periods')
                }
            }
            
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(model_data, f, ensure_ascii=False, indent=2, default=str)
            
            return True
            
        except Exception as e:
            self.logger.error(f"保存模型失败: {str(e)}")
            return False
    
    def load_model(self, file_path: str) -> bool:
        """加载模型"""
        try:
            self.logger.info(f"加载TBATS模型: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                model_data = json.load(f)
            
            self.model_summary = model_data['model_summary']
            
            if model_data['fitted_values']:
                self.fitted_values = pd.Series(model_data['fitted_values'])
            
            if model_data['residuals']:
                self.residuals = pd.Series(model_data['residuals'])
            
            return True
            
        except Exception as e:
            self.logger.error(f"加载模型失败: {str(e)}")
            return False
    
    def evaluate_model(self, test_data: pd.DataFrame = None) -> Dict[str, float]:
        """
        评估模型性能
        
        Args:
            test_data: 测试数据DataFrame
            
        Returns:
            评估指标字典
        """
        try:
            self.logger.info("评估TBATS模型性能")
            
            if self.residuals is None:
                raise ValueError("请先拟合模型")
            
            residuals = self.residuals.dropna()
            
            # 计算评估指标
            mse = np.mean(residuals ** 2)
            rmse = np.sqrt(mse)
            mae = np.mean(np.abs(residuals))
            mape = np.mean(np.abs(residuals / self.fitted_values.dropna())) * 100
            
            # 计算残差统计
            residual_std = np.std(residuals)
            residual_mean = np.mean(residuals)
            
            evaluation = {
                'rmse': round(rmse, 4),
                'mse': round(mse, 4),
                'mae': round(mae, 4),
                'mape': round(mape, 2),
                'residual_std': round(residual_std, 4),
                'residual_mean': round(residual_mean, 4),
                'aic': self.model_summary.get('aic', 0),
                'bic': self.model_summary.get('bic', 0)
            }
            
            if test_data is not None:
                # 计算测试集指标
                test_residuals = test_data - self.fitted_values[-len(test_data):]
                test_rmse = np.sqrt(np.mean(test_residuals ** 2))
                evaluation['test_rmse'] = round(test_rmse, 4)
            
            self.logger.info("模型评估完成")
            return evaluation
            
        except Exception as e:
            self.logger.error(f"模型评估失败: {str(e)}")
            raise
    
    def plot_results(self, save_path: str = None) -> bool:
        """
        绘制建模结果
        
        Args:
            save_path: 保存路径
            
        Returns:
            是否成功
        """
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            plt.style.use('seaborn-v0_8')
            fig, axes = plt.subplots(2, 2, figsize=(15, 10))
            
            # 原始数据和拟合值
            if self.fitted_values is not None:
                axes[0, 0].plot(self.fitted_values.index, self.fitted_values.values, label='Fitted', color='red')
                axes[0, 0].set_title('TBATS Model Fitting')
                axes[0, 0].legend()
            
            # 残差图
            if self.residuals is not None:
                axes[0, 1].plot(self.residuals.index, self.residuals.values, color='green')
                axes[0, 1].axhline(y=0, color='black', linestyle='--')
                axes[0, 1].set_title('Residuals')
            
            # 残差分布
            if self.residuals is not None:
                axes[1, 0].hist(self.residuals.dropna(), bins=30, edgecolor='black')
                axes[1, 0].set_title('Residual Distribution')
            
            # ACF图
            if self.residuals is not None:
                from statsmodels.graphics.tsaplots import plot_acf
                plot_acf(self.residuals.dropna(), lags=20, ax=axes[1, 1])
                axes[1, 1].set_title('ACF of Residuals')
            
            plt.tight_layout()
            
            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                self.logger.info(f"建模结果图已保存: {save_path}")
            
            plt.show()
            return True
            
        except Exception as e:
            self.logger.error(f"绘制结果图失败: {str(e)}")
            return False
    
    def _generate_model_summary(self) -> Dict[str, Any]:
        """生成模型摘要"""
        if not TBATS_AVAILABLE:
            return self._simulate_model_summary()
        
        try:
            return {
                'aic': self.model.aic,
                'bic': self.model.bic,
                'parameters_count': len(self.model.params),
                'seasonal_periods': self.model.seasonal_periods,
                'use_trend': self.model.use_trend,
                'use_damped_trend': self.model.use_damped_trend,
                'fitted_length': len(self.fitted_values),
                'residual_std': np.std(self.residuals) if self.residuals is not None else 0,
                'model_type': 'TBATS'
            }
        except Exception as e:
            self.logger.error(f"生成模型摘要失败: {str(e)}")
            return {}
    
    def _simulate_tbats_fit(self, y: pd.Series, use_trend: bool, use_damped_trend: bool, seasonal_periods: List[int]) -> Dict[str, Any]:
        """模拟TBATS拟合结果"""
        return {
            'aic': np.random.uniform(100, 200),
            'bic': np.random.uniform(110, 210),
            'parameters_count': np.random.randint(5, 15),
            'seasonal_periods': seasonal_periods,
            'use_trend': use_trend,
            'use_damped_trend': use_damped_trend,
            'fitted_length': len(y),
            'residual_std': np.std(y) * 0.1,
            'model_type': 'TBATS (Simulated)'
        }
    
    def _simulate_fitted_values(self, y: pd.Series) -> pd.Series:
        """模拟拟合值"""
        # 添加一些噪声和趋势
        trend = np.linspace(0, len(y) * 0.01, len(y))
        seasonal = 0.1 * np.sin(2 * np.pi * np.arange(len(y)) / 7)
        noise = np.random.normal(0, 0.05, len(y))
        
        fitted = y * (1 + trend + seasonal + noise)
        return pd.Series(fitted, index=y.index)
    
    def _simulate_forecast(self, steps: int, confidence_level: float) -> pd.DataFrame:
        """模拟预测结果"""
        # 生成未来日期
        last_date = datetime.now()
        forecast_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=steps,
            freq='D'
        )
        
        # 模拟预测值
        base_value = 100
        trend = np.linspace(0, steps * 0.01, steps)
        seasonal = 0.1 * np.sin(2 * np.pi * np.arange(steps) / 7)
        
        forecast_values = base_value * (1 + trend + seasonal)
        
        # 计算置信区间
        std_dev = 0.05 * forecast_values
        lower_bound = forecast_values - 1.96 * std_dev
        upper_bound = forecast_values + 1.96 * std_dev
        
        return pd.DataFrame({
            'date': forecast_dates,
            'forecast': forecast_values,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound
        })
    
    def _simulate_model_summary(self) -> Dict[str, Any]:
        """模拟模型摘要"""
        return {
            'aic': 150.5,
            'bic': 165.2,
            'parameters_count': 8,
            'seasonal_periods': [7, 365],
            'use_trend': True,
            'use_damped_trend': False,
            'fitted_length': 365,
            'residual_std': 5.2,
            'model_type': 'TBATS (Simulated)'
        }

# 使用示例
if __name__ == "__main__":
    from ..utils.config_manager import ConfigManager
    import matplotlib.pyplot as plt
    
    config = ConfigManager()
    model = TBATSModel(config)
    
    # 创建测试数据
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    values = 100 + 10 * np.sin(2 * np.pi * np.arange(100) / 7) + np.random.normal(0, 5, 100)
    
    data = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    # 拟合模型
    summary = model.fit_model(data, 'value')
    print("模型摘要:", summary)
    
    # 预测
    forecast = model.predict(steps=30)
    print("预测结果:", forecast.head())
    
    # 评估模型
    evaluation = model.evaluate_model()
    print("模型评估:", evaluation)