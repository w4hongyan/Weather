#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
机器学习残差修正模块 - Machine Learning Residual Correction Module
使用随机森林修正TBATS模型残差
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from typing import Dict, List, Optional, Any, Tuple
import joblib
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.logger import LoggerMixin
from utils.config_manager import ConfigManager

class ResidualCorrector(LoggerMixin):
    """残差修正器类 - 使用随机森林修正TBATS模型残差"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config = config_manager
        self.model = None
        self.scaler = StandardScaler()
        self.feature_importance = None
        self.is_trained = False
        
        # 获取随机森林配置
        self.rf_config = self.config.get_random_forest_config()
    
    def prepare_features(
        self,
        data: pd.DataFrame,
        target_column: str,
        weather_data: pd.DataFrame = None,
        include_lag_features: bool = True,
        include_rolling_stats: bool = True,
        include_date_features: bool = True,
        include_weather_features: bool = True
    ) -> pd.DataFrame:
        """
        准备特征数据
        
        Args:
            data: 原始数据DataFrame
            target_column: 目标列名
            weather_data: 天气数据DataFrame
            include_lag_features: 是否包含滞后特征
            include_rolling_stats: 是否包含滚动统计特征
            include_date_features: 是否包含日期特征
            include_weather_features: 是否包含天气特征
            
        Returns:
            特征DataFrame
        """
        try:
            self.logger.info("准备机器学习特征")
            
            df = data.copy()
            
            # 确保日期列为索引
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
            
            features_df = pd.DataFrame(index=df.index)
            
            # 1. 日期特征
            if include_date_features:
                features_df['day_of_week'] = df.index.dayofweek
                features_df['day_of_month'] = df.index.day
                features_df['month'] = df.index.month
                features_df['quarter'] = df.index.quarter
                features_df['is_weekend'] = (df.index.dayofweek >= 5).astype(int)
                features_df['is_holiday'] = self._get_holiday_features(df.index)
                
                # 周期性特征
                features_df['day_sin'] = np.sin(2 * np.pi * df.index.dayofyear / 365.25)
                features_df['day_cos'] = np.cos(2 * np.pi * df.index.dayofyear / 365.25)
                features_df['week_sin'] = np.sin(2 * np.pi * df.index.dayofweek / 7)
                features_df['week_cos'] = np.cos(2 * np.pi * df.index.dayofweek / 7)
            
            # 2. 滞后特征
            if include_lag_features:
                for lag in [1, 2, 3, 7, 14, 30]:
                    if len(df) > lag:
                        features_df[f'lag_{lag}'] = df[target_column].shift(lag)
            
            # 3. 滚动统计特征
            if include_rolling_stats:
                windows = [3, 7, 14, 30]
                for window in windows:
                    if len(df) > window:
                        features_df[f'rolling_mean_{window}'] = df[target_column].rolling(window=window).mean()
                        features_df[f'rolling_std_{window}'] = df[target_column].rolling(window=window).std()
                        features_df[f'rolling_min_{window}'] = df[target_column].rolling(window=window).min()
                        features_df[f'rolling_max_{window}'] = df[target_column].rolling(window=window).max()
            
            # 4. 天气特征
            if include_weather_features and weather_data is not None:
                weather_features = self._prepare_weather_features(weather_data, df.index)
                features_df = pd.concat([features_df, weather_features], axis=1)
            
            # 5. 趋势特征
            features_df['trend'] = np.arange(len(df))
            features_df['trend_squared'] = features_df['trend'] ** 2
            
            # 处理缺失值
            features_df = features_df.fillna(method='ffill').fillna(0)
            
            self.logger.info(f"特征准备完成，共{len(features_df.columns)}个特征")
            return features_df
            
        except Exception as e:
            self.logger.error(f"特征准备失败: {str(e)}")
            raise
    
    def train_residual_model(
        self,
        features: pd.DataFrame,
        residuals: pd.Series,
        test_size: float = 0.2,
        perform_grid_search: bool = False
    ) -> Dict[str, float]:
        """
        训练残差修正模型
        
        Args:
            features: 特征DataFrame
            residuals: 残差Series
            test_size: 测试集比例
            perform_grid_search: 是否执行网格搜索
            
        Returns:
            模型性能指标
        """
        try:
            self.logger.info("开始训练残差修正模型")
            
            # 确保索引对齐
            common_index = features.index.intersection(residuals.index)
            X = features.loc[common_index]
            y = residuals.loc[common_index]
            
            # 处理缺失值
            X = X.fillna(0)
            y = y.fillna(0)
            
            # 分割训练测试集
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42
            )
            
            # 标准化特征
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # 初始化随机森林模型
            self.model = RandomForestRegressor(
                n_estimators=self.rf_config.get('n_estimators', 100),
                max_depth=self.rf_config.get('max_depth', 10),
                min_samples_split=self.rf_config.get('min_samples_split', 2),
                min_samples_leaf=self.rf_config.get('min_samples_leaf', 1),
                random_state=42,
                n_jobs=-1
            )
            
            # 网格搜索优化
            if perform_grid_search:
                param_grid = {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [5, 10, 15, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                }
                
                grid_search = GridSearchCV(
                    self.model, param_grid, cv=5, 
                    scoring='neg_mean_squared_error', n_jobs=-1
                )
                grid_search.fit(X_train_scaled, y_train)
                self.model = grid_search.best_estimator_
                
                self.logger.info(f"网格搜索完成，最佳参数: {grid_search.best_params_}")
            else:
                # 直接训练
                self.model.fit(X_train_scaled, y_train)
            
            # 预测
            y_train_pred = self.model.predict(X_train_scaled)
            y_test_pred = self.model.predict(X_test_scaled)
            
            # 计算性能指标
            metrics = {
                'train_mse': mean_squared_error(y_train, y_train_pred),
                'test_mse': mean_squared_error(y_test, y_test_pred),
                'train_mae': mean_absolute_error(y_train, y_train_pred),
                'test_mae': mean_absolute_error(y_test, y_test_pred),
                'train_r2': r2_score(y_train, y_train_pred),
                'test_r2': r2_score(y_test, y_test_pred),
                'train_rmse': np.sqrt(mean_squared_error(y_train, y_train_pred)),
                'test_rmse': np.sqrt(mean_squared_error(y_test, y_test_pred))
            }
            
            # 特征重要性
            self.feature_importance = pd.DataFrame({
                'feature': X.columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            self.is_trained = True
            
            self.logger.info(f"残差修正模型训练完成，测试RMSE: {metrics['test_rmse']:.4f}")
            return metrics
            
        except Exception as e:
            self.logger.error(f"模型训练失败: {str(e)}")
            raise
    
    def correct_predictions(
        self,
        original_predictions: pd.Series,
        features: pd.DataFrame
    ) -> pd.Series:
        """
        修正预测结果
        
        Args:
            original_predictions: 原始预测值
            features: 特征DataFrame
            
        Returns:
            修正后的预测值
        """
        try:
            self.logger.info("开始修正预测结果")
            
            if not self.is_trained or self.model is None:
                raise ValueError("请先训练残差修正模型")
            
            # 确保索引对齐
            common_index = original_predictions.index.intersection(features.index)
            pred_aligned = original_predictions.loc[common_index]
            features_aligned = features.loc[common_index]
            
            # 处理缺失值
            features_aligned = features_aligned.fillna(0)
            
            # 标准化特征
            features_scaled = self.scaler.transform(features_aligned)
            
            # 预测残差
            predicted_residuals = self.model.predict(features_scaled)
            
            # 修正预测
            corrected_predictions = pred_aligned + pd.Series(predicted_residuals, index=common_index)
            
            self.logger.info("预测修正完成")
            return corrected_predictions
            
        except Exception as e:
            self.logger.error(f"预测修正失败: {str(e)}")
            raise
    
    def save_model(self, file_path: str) -> bool:
        """保存模型"""
        try:
            self.logger.info(f"保存残差修正模型: {file_path}")
            
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_importance': self.feature_importance,
                'is_trained': self.is_trained,
                'config': self.rf_config
            }
            
            joblib.dump(model_data, file_path)
            return True
            
        except Exception as e:
            self.logger.error(f"保存模型失败: {str(e)}")
            return False
    
    def load_model(self, file_path: str) -> bool:
        """加载模型"""
        try:
            self.logger.info(f"加载残差修正模型: {file_path}")
            
            if not Path(file_path).exists():
                self.logger.warning(f"模型文件不存在: {file_path}")
                return False
            
            model_data = joblib.load(file_path)
            
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_importance = model_data['feature_importance']
            self.is_trained = model_data['is_trained']
            
            return True
            
        except Exception as e:
            self.logger.error(f"加载模型失败: {str(e)}")
            return False
    
    def get_feature_importance(self) -> pd.DataFrame:
        """获取特征重要性"""
        return self.feature_importance
    
    def _prepare_weather_features(self, weather_data: pd.DataFrame, target_index: pd.DatetimeIndex) -> pd.DataFrame:
        """准备天气特征"""
        try:
            weather_df = weather_data.copy()
            
            # 确保日期列为索引
            if 'date' in weather_df.columns:
                weather_df['date'] = pd.to_datetime(weather_df['date'])
                weather_df = weather_df.set_index('date')
            
            # 重采样到日级别
            daily_weather = weather_df.resample('D').agg({
                'temperature': 'mean',
                'humidity': 'mean',
                'pressure': 'mean',
                'wind_speed': 'mean',
                'precipitation': 'sum'
            })
            
            # 对齐索引
            weather_features = daily_weather.reindex(target_index)
            
            # 处理缺失值
            weather_features = weather_features.fillna(method='ffill').fillna(method='bfill')
            
            # 重命名列
            weather_features.columns = [f'weather_{col}' for col in weather_features.columns]
            
            return weather_features
            
        except Exception as e:
            self.logger.warning(f"天气特征准备失败: {str(e)}")
            return pd.DataFrame(index=target_index)
    
    def _get_holiday_features(self, dates: pd.DatetimeIndex) -> pd.Series:
        """获取节假日特征"""
        try:
            import holidays
            
            # 中国节假日
            china_holidays = holidays.China(years=dates.year.unique())
            
            # 创建节假日特征
            holiday_series = pd.Series(index=dates, data=0)
            for date in dates:
                if date.date() in china_holidays:
                    holiday_series[date] = 1
            
            return holiday_series
            
        except Exception as e:
            self.logger.warning(f"节假日特征获取失败: {str(e)}")
            return pd.Series(index=dates, data=0)

# 使用示例
if __name__ == "__main__":
    from ..utils.config_manager import ConfigManager
    
    config = ConfigManager()
    corrector = ResidualCorrector(config)
    
    # 创建测试数据
    dates = pd.date_range('2023-01-01', periods=100, freq='D')
    values = 100 + 10 * np.sin(2 * np.pi * np.arange(100) / 7) + np.random.normal(0, 5, 100)
    residuals = np.random.normal(0, 2, 100)
    
    data = pd.DataFrame({
        'date': dates,
        'value': values
    })
    
    # 准备特征
    features = corrector.prepare_features(data, 'value')
    
    # 训练模型
    metrics = corrector.train_residual_model(features, pd.Series(residuals, index=dates))
    print("模型性能:", metrics)
    
    # 特征重要性
    importance = corrector.get_feature_importance()
    print("特征重要性:")
    print(importance.head())