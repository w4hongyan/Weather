#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气数据管理器
智能选择和整合多个天气数据源
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import time
from pathlib import Path

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.logger import LoggerMixin
from utils.config_manager import ConfigManager
from core.weather_api import WeatherAPI
from core.open_meteo_api import OpenMeteoAPI

class WeatherManager(LoggerMixin):
    """天气数据管理器 - 整合多个数据源"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config = config_manager
        self.weather_api = WeatherAPI(config_manager)
        self.open_meteo_api = OpenMeteoAPI(config_manager)
        
        # 从配置中选择默认的API提供商
        self.default_provider = self.config.get('weather_api.provider', 'open_meteo')
        
        # 缓存管理
        self.cache_dir = Path(self.config.get('data.cache_dir', './cache'))
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_expiry_days = self.config.get('weather_api.cache_expiry_days', 7)
    
    def get_weather_data(
        self,
        city: str,
        start_date: datetime,
        end_date: datetime,
        provider: Optional[str] = None,
        include_forecast: bool = True,
        forecast_days: int = 7,
        use_cache: bool = True,
        variables: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        智能获取天气数据
        
        Args:
            city: 城市名称
            start_date: 开始日期
            end_date: 结束日期
            provider: 指定数据源 ('open_meteo', 'openweathermap', 'auto')
            include_forecast: 是否包含未来预测
            forecast_days: 预测天数
            use_cache: 是否使用缓存
            variables: 指定天气要素
            
        Returns:
            整合后的天气数据DataFrame
        """
        try:
            self.logger.info(f"获取{city}的天气数据: {start_date} 到 {end_date}")
            
            # 确定使用的提供商
            if provider is None or provider == 'auto':
                provider = self.default_provider
            
            # 检查缓存
            if use_cache:
                cached_data = self._get_cached_weather(city, start_date, end_date, provider)
                if cached_data is not None:
                    self.logger.info(f"使用缓存的天气数据: {len(cached_data)}条记录")
                    return cached_data
            
            # 根据提供商获取数据
            if provider == 'open_meteo':
                weather_data = self.open_meteo_api.get_enhanced_weather_data(
                    city=city,
                    start_date=start_date,
                    end_date=end_date,
                    include_forecast=include_forecast,
                    forecast_days=forecast_days
                )
            elif provider == 'openweathermap':
                historical_data = self.weather_api.get_historical_weather(
                    city=city,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if include_forecast:
                    forecast_data = self.weather_api.get_forecast_weather(
                        city=city,
                        days=forecast_days
                    )
                    
                    # 合并数据
                    complete_data = pd.concat([historical_data, forecast_data], ignore_index=True)
                    complete_data = complete_data.drop_duplicates(subset=['date'], keep='first')
                    complete_data = complete_data.sort_values('date').reset_index(drop=True)
                    weather_data = complete_data
                else:
                    weather_data = historical_data
            else:
                raise ValueError(f"不支持的天气数据源: {provider}")
            
            # 标准化数据格式
            weather_data = self._standardize_weather_data(weather_data, provider)
            
            # 缓存数据
            if use_cache:
                self._cache_weather_data(city, start_date, end_date, provider, weather_data)
            
            self.logger.info(f"成功获取{city}的天气数据: {len(weather_data)}条记录")
            return weather_data
            
        except Exception as e:
            self.logger.error(f"获取天气数据失败: {str(e)}")
            
            # 故障转移：如果一个API失败，尝试另一个
            if provider != 'auto':
                self.logger.info("尝试故障转移到备用数据源...")
                fallback_provider = 'openweathermap' if provider == 'open_meteo' else 'open_meteo'
                try:
                    return self.get_weather_data(
                        city=city,
                        start_date=start_date,
                        end_date=end_date,
                        provider=fallback_provider,
                        include_forecast=include_forecast,
                        forecast_days=forecast_days,
                        use_cache=False  # 避免缓存故障数据
                    )
                except:
                    pass
            
            raise
    
    def get_multi_city_weather(
        self,
        cities: List[str],
        start_date: datetime,
        end_date: datetime,
        **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """
        批量获取多个城市的天气数据
        
        Args:
            cities: 城市列表
            start_date: 开始日期
            end_date: 结束日期
            **kwargs: 其他参数
            
        Returns:
            城市到天气数据的映射字典
        """
        results = {}
        
        for city in cities:
            try:
                city_data = self.get_weather_data(city, start_date, end_date, **kwargs)
                results[city] = city_data
                self.logger.info(f"成功获取{city}的天气数据")
                
                # 添加延迟避免API限制
                time.sleep(0.5)
                
            except Exception as e:
                self.logger.error(f"获取{city}天气数据失败: {str(e)}")
                results[city] = pd.DataFrame()  # 返回空DataFrame
        
        return results
    
    def compare_data_sources(
        self,
        city: str,
        date: datetime,
        variables: List[str] = ['temperature', 'humidity', 'pressure']
    ) -> Dict[str, Dict]:
        """
        比较不同数据源的数据差异
        
        Args:
            city: 城市名称
            date: 比较日期
            variables: 比较的变量列表
            
        Returns:
            数据源比较结果
        """
        try:
            comparison = {}
            
            # 获取Open-Meteo数据
            try:
                om_data = self.open_meteo_api.get_historical_weather(city, date, date)
                if not om_data.empty:
                    comparison['open_meteo'] = {
                        var: om_data.iloc[0].get(var, None) 
                        for var in variables if var in om_data.columns
                    }
            except Exception as e:
                comparison['open_meteo'] = {'error': str(e)}
            
            # 获取OpenWeatherMap数据
            try:
                ow_data = self.weather_api.get_historical_weather(city, date, date)
                if not ow_data.empty:
                    comparison['openweathermap'] = {
                        var: ow_data.iloc[0].get(var, None) 
                        for var in variables if var in ow_data.columns
                    }
            except Exception as e:
                comparison['openweathermap'] = {'error': str(e)}
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"数据源比较失败: {str(e)}")
            return {}
    
    def get_weather_summary(
        self,
        city: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        获取天气数据摘要统计
        
        Args:
            city: 城市名称
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            天气摘要统计信息
        """
        try:
            weather_data = self.get_weather_data(city, start_date, end_date)
            
            if weather_data.empty:
                return {}
            
            summary = {
                'city': city,
                'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'total_days': len(weather_data),
                'temperature': {
                    'mean': weather_data['temperature'].mean(),
                    'min': weather_data['temperature'].min(),
                    'max': weather_data['temperature'].max(),
                    'std': weather_data['temperature'].std()
                },
                'humidity': {
                    'mean': weather_data['humidity'].mean(),
                    'min': weather_data['humidity'].min(),
                    'max': weather_data['humidity'].max()
                },
                'precipitation': {
                    'total': weather_data['precipitation'].sum(),
                    'max_daily': weather_data['precipitation'].max(),
                    'rainy_days': (weather_data['precipitation'] > 0).sum()
                },
                'data_completeness': 1 - (weather_data.isnull().sum().max() / len(weather_data))
            }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"获取天气摘要失败: {str(e)}")
            return {}
    
    def _get_cached_weather(
        self, 
        city: str, 
        start_date: datetime, 
        end_date: datetime, 
        provider: str
    ) -> Optional[pd.DataFrame]:
        """从缓存获取天气数据"""
        try:
            cache_file = self.cache_dir / f"weather_{city}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{provider}.parquet"
            
            if cache_file.exists():
                # 检查缓存是否过期
                file_age = (datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)).days
                if file_age <= self.cache_expiry_days:
                    return pd.read_parquet(cache_file)
            
            return None
            
        except Exception as e:
            self.logger.warning(f"缓存读取失败: {str(e)}")
            return None
    
    def _cache_weather_data(
        self, 
        city: str, 
        start_date: datetime, 
        end_date: datetime, 
        provider: str, 
        data: pd.DataFrame
    ):
        """缓存天气数据"""
        try:
            cache_file = self.cache_dir / f"weather_{city}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}_{provider}.parquet"
            data.to_parquet(cache_file)
            
        except Exception as e:
            self.logger.warning(f"缓存写入失败: {str(e)}")
    
    def _standardize_weather_data(self, data: pd.DataFrame, provider: str) -> pd.DataFrame:
        """标准化不同数据源的数据格式"""
        try:
            # 确保标准列存在
            standard_columns = [
                'city', 'date', 'temperature', 'humidity', 'pressure', 
                'wind_speed', 'precipitation', 'cloud_cover',
                'is_holiday', 'is_weekend', 'data_source'
            ]
            
            # 创建标准格式的DataFrame
            standardized = pd.DataFrame()
            
            for col in standard_columns:
                if col in data.columns:
                    standardized[col] = data[col]
                else:
                    # 尝试映射相似的列名
                    if col == 'temperature' and 'temperature_2m' in data.columns:
                        standardized[col] = data['temperature_2m']
                    elif col == 'humidity' and 'relativehumidity_2m' in data.columns:
                        standardized[col] = data['relativehumidity_2m']
                    elif col == 'pressure' and 'pressure_msl' in data.columns:
                        standardized[col] = data['pressure_msl']
                    elif col == 'wind_speed' and 'windspeed_10m' in data.columns:
                        standardized[col] = data['windspeed_10m']
                    elif col == 'cloud_cover' and 'cloudcover' in data.columns:
                        standardized[col] = data['cloudcover']
                    else:
                        standardized[col] = None
            
            # 添加数据源标识
            standardized['data_source'] = provider
            
            return standardized
            
        except Exception as e:
            self.logger.error(f"数据标准化失败: {str(e)}")
            return data

# 测试函数
def test_weather_manager():
    """测试天气管理器"""
    try:
        from utils.config_manager import ConfigManager
        
        config = ConfigManager()
        manager = WeatherManager(config)
        
        print("🌤️ 正在测试天气管理器...")
        
        # 测试单城市数据获取
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now() - timedelta(days=1)
        
        print("\n📊 测试单城市数据获取...")
        data = manager.get_weather_data("广州", start_date, end_date)
        print(f"✅ 数据条数: {len(data)}")
        print(f"✅ 数据源: {data['data_source'].iloc[0]}")
        
        # 测试多城市数据获取
        print("\n🌍 测试多城市数据获取...")
        cities = ["广州", "深圳", "上海"]
        multi_data = manager.get_multi_city_weather(cities, start_date, end_date)
        for city, city_data in multi_data.items():
            print(f"✅ {city}: {len(city_data)}条记录")
        
        # 测试数据源比较
        print("\n🔍 测试数据源比较...")
        comparison = manager.compare_data_sources("广州", start_date)
        print(f"✅ 比较结果: {comparison}")
        
        # 测试天气摘要
        print("\n📈 测试天气摘要...")
        summary = manager.get_weather_summary("广州", start_date, end_date)
        print(f"✅ 摘要信息: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

if __name__ == "__main__":
    test_weather_manager()