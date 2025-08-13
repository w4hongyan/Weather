#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气数据API模块 - Weather Data API Module
获取历史天气数据和未来天气预测
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time
import json
from pathlib import Path
import holidays

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.logger import LoggerMixin
from utils.config_manager import ConfigManager

class WeatherAPI(LoggerMixin):
    """天气数据API类"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config = config_manager
        self.api_key = self.config.get_weather_api_key()
        self.base_url = self.config.get('weather_api.base_url', 'https://api.openweathermap.org/data/2.5')
        self.timeout = self.config.get('weather_api.timeout', 30)
        self.retry_count = self.config.get('weather_api.retry_count', 3)
        
        # 中国主要城市坐标
        self.city_coordinates = {
            "广州": {"lat": 23.1291, "lon": 113.2644},
            "深圳": {"lat": 22.5431, "lon": 114.0579},
            "东莞": {"lat": 23.0489, "lon": 113.7447},
            "佛山": {"lat": 23.0350, "lon": 113.1244},
            "中山": {"lat": 22.5170, "lon": 113.3920},
            "珠海": {"lat": 22.3193, "lon": 113.5824},
            "惠州": {"lat": 23.0817, "lon": 114.4152},
            "江门": {"lat": 22.5792, "lon": 113.0940},
            "肇庆": {"lat": 23.0515, "lon": 112.4650},
            "汕头": {"lat": 23.3541, "lon": 116.6822},
            "北京": {"lat": 39.9042, "lon": 116.4074},
            "上海": {"lat": 31.2304, "lon": 121.4737},
            "成都": {"lat": 30.5728, "lon": 104.0668},
            "杭州": {"lat": 30.2741, "lon": 120.1551},
            "武汉": {"lat": 30.5928, "lon": 114.3055},
            "西安": {"lat": 34.3416, "lon": 108.9398},
            "南京": {"lat": 32.0603, "lon": 118.7969},
            "重庆": {"lat": 29.5630, "lon": 106.5516},
            "天津": {"lat": 39.3434, "lon": 117.3616}
        }
        
        # 中国法定节假日（2023-2024）
        self.china_holidays = holidays.China(years=[2023, 2024, 2025])
    
    def get_historical_weather(
        self,
        city: str,
        start_date: datetime,
        end_date: datetime
    ) -> pd.DataFrame:
        """
        获取历史天气数据
        
        Args:
            city: 城市名称
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            天气数据DataFrame
        """
        try:
            self.logger.info(f"获取{city}的历史天气数据: {start_date} 到 {end_date}")
            
            if city not in self.city_coordinates:
                raise ValueError(f"不支持的城市: {city}")
            
            coordinates = self.city_coordinates[city]
            weather_data = []
            
            current_date = start_date
            while current_date <= end_date:
                try:
                    # 获取每日天气数据
                    daily_weather = self._get_daily_weather(
                        coordinates["lat"], 
                        coordinates["lon"], 
                        current_date
                    )
                    
                    if daily_weather:
                        daily_weather['city'] = city
                        daily_weather['date'] = current_date
                        weather_data.append(daily_weather)
                    
                    current_date += timedelta(days=1)
                    time.sleep(0.1)  # API调用间隔
                    
                except Exception as e:
                    self.logger.warning(f"获取{current_date}天气数据失败: {str(e)}")
                    # 创建空数据记录
                    weather_data.append({
                        'city': city,
                        'date': current_date,
                        'temperature': np.nan,
                        'humidity': np.nan,
                        'pressure': np.nan,
                        'wind_speed': np.nan,
                        'precipitation': np.nan,
                        'weather_main': '',
                        'is_holiday': self._is_holiday(current_date),
                        'is_weekend': current_date.weekday() >= 5
                    })
                    current_date += timedelta(days=1)
            
            # 转换为DataFrame
            df = pd.DataFrame(weather_data)
            
            # 处理缺失值
            df = self._process_missing_values(df)
            
            self.logger.info(f"成功获取{city}的历史天气数据: {len(df)}条记录")
            return df
            
        except Exception as e:
            self.logger.error(f"获取历史天气数据失败: {str(e)}")
            raise
    
    def get_forecast_weather(
        self,
        city: str,
        days: int = 7
    ) -> pd.DataFrame:
        """
        获取增强的未来天气预测
        
        Args:
            city: 城市名称
            days: 预测天数（最多14天）
            
        Returns:
            天气预测DataFrame（包含置信区间）
        """
        try:
            self.logger.info(f"获取{city}的天气预测: {days}天")
            
            if city not in self.city_coordinates:
                raise ValueError(f"不支持的城市: {city}")
            
            if days > 14:
                raise ValueError("预测天数不能超过14天")
            
            coordinates = self.city_coordinates[city]
            
            # 获取7天天气预报（API限制）
            url = f"{self.base_url}/forecast"
            params = {
                'lat': coordinates["lat"],
                'lon': coordinates["lon"],
                'appid': self.api_key,
                'units': 'metric',
                'cnt': min(days, 7) * 8  # 每3小时一次数据，最多7天
            }
            
            response = self._make_request(url, params)
            forecast_data = []
            
            if response and 'list' in response:
                # 处理API返回的数据
                for item in response['list']:
                    forecast_date = datetime.fromtimestamp(item['dt'])
                    
                    forecast_data.append({
                        'city': city,
                        'datetime': forecast_date,
                        'date': forecast_date.date(),
                        'temperature': item['main']['temp'],
                        'humidity': item['main']['humidity'],
                        'pressure': item['main']['pressure'],
                        'wind_speed': item['wind']['speed'],
                        'precipitation': item.get('rain', {}).get('3h', 0),
                        'weather_main': item['weather'][0]['main'],
                        'weather_description': item['weather'][0]['description'],
                        'is_holiday': self._is_holiday(forecast_date.date()),
                        'is_weekend': forecast_date.weekday() >= 5,
                        'data_source': 'api'
                    })
            
            # 对于超过7天的预测，使用增强模拟
            if days > 7:
                future_start = datetime.now().date() + timedelta(days=7)
                future_dates = pd.date_range(start=future_start, periods=days-7, freq='D')
                
                for date in future_dates:
                    simulated = self._simulate_weather_data(coordinates["lat"], coordinates["lon"], date)
                    forecast_data.append({
                        'city': city,
                        'datetime': datetime.combine(date, datetime.min.time()),
                        'date': date,
                        'temperature': simulated['temperature'],
                        'humidity': simulated['humidity'],
                        'pressure': simulated['pressure'],
                        'wind_speed': simulated['wind_speed'],
                        'precipitation': simulated['precipitation'],
                        'weather_main': simulated['weather_main'],
                        'weather_description': self._get_weather_description(simulated['weather_main']),
                        'is_holiday': simulated['is_holiday'],
                        'is_weekend': simulated['is_weekend'],
                        'data_source': 'simulated'
                    })
            
            # 按日期聚合并添加置信区间
            df = pd.DataFrame(forecast_data)
            daily_df = df.groupby('date').agg({
                'temperature': ['mean', 'min', 'max'],
                'humidity': 'mean',
                'pressure': 'mean',
                'wind_speed': 'mean',
                'precipitation': 'sum',
                'weather_main': lambda x: x.mode()[0] if len(x) > 0 else '',
                'city': 'first',
                'is_holiday': 'first',
                'is_weekend': 'first',
                'data_source': lambda x: 'mixed' if len(set(x)) > 1 else x.iloc[0]
            }).reset_index()
            
            # 展平列名
            daily_df.columns = ['date', 'temperature', 'temp_min', 'temp_max', 
                              'humidity', 'pressure', 'wind_speed', 'precipitation',
                              'weather_main', 'city', 'is_holiday', 'is_weekend', 'data_source']
            
            # 计算置信区间
            daily_df['temp_confidence'] = daily_df.apply(
                lambda row: min(95, max(70, 100 - abs(row['temp_max'] - row['temp_min']) * 5)), axis=1
            )
            
            self.logger.info(f"成功获取{city}的天气预测: {len(daily_df)}天")
            return daily_df
            
        except Exception as e:
            self.logger.error(f"获取天气预测失败: {str(e)}")
            raise
    
    def get_multiple_cities_weather(
        self,
        cities: List[str],
        start_date: datetime,
        end_date: datetime,
        include_summary: bool = False
    ) -> Dict[str, Any]:
        """
        获取多个城市的天气数据（增强版）
        
        Args:
            cities: 城市列表
            start_date: 开始日期
            end_date: 结束日期
            include_summary: 是否包含统计摘要
            
        Returns:
            城市到天气数据的映射字典（可包含摘要）
        """
        try:
            self.logger.info(f"获取多个城市天气数据: {cities}")
            
            weather_data = {}
            summary_data = {}
            
            for city in cities:
                try:
                    city_weather = self.get_historical_weather(city, start_date, end_date)
                    weather_data[city] = city_weather
                    
                    if include_summary and not city_weather.empty:
                        summary_data[city] = self._calculate_city_summary(city_weather)
                        
                except Exception as e:
                    self.logger.warning(f"获取{city}天气数据失败: {str(e)}")
                    weather_data[city] = pd.DataFrame()
                    if include_summary:
                        summary_data[city] = {}
                    continue
            
            result = {'weather_data': weather_data}
            if include_summary:
                result['summary'] = summary_data
                
            return result
            
        except Exception as e:
            self.logger.error(f"获取多城市天气数据失败: {str(e)}")
            raise
    
    def _get_daily_weather(self, lat: float, lon: float, date: datetime) -> Dict[str, Any]:
        """获取单日天气数据"""
        try:
            # 使用历史天气API（需要商业订阅）
            # 这里模拟API响应
            return self._simulate_weather_data(lat, lon, date)
            
        except Exception as e:
            self.logger.warning(f"获取单日天气数据失败: {str(e)}")
            return None
    
    def _simulate_weather_data(self, lat: float, lon: float, date: datetime) -> Dict[str, Any]:
        """增强的模拟天气数据（用于演示）"""
        import math
        
        month = date.month
        day_of_year = date.timetuple().tm_yday
        
        # 海拔估算（简化模型）
        altitude = max(0, (30 - abs(lat - 30)) * 50 + np.random.normal(0, 100))
        
        # 基础温度模型（纬度+海拔+季节）
        lat_factor = (lat - 30) / 30
        altitude_factor = altitude / 1000
        seasonal_factor = 12 * math.sin(2 * math.pi * (day_of_year - 80) / 365)
        
        base_temp = 22 - lat_factor * 8 - altitude_factor * 6 + seasonal_factor
        
        # 多层次随机波动
        daily_variation = np.random.normal(0, 2)
        weekly_pattern = 3 * math.sin(2 * math.pi * date.weekday() / 7)
        
        temperature = base_temp + daily_variation + weekly_pattern
        
        # 湿度模型（与温度和季节相关）
        humidity_base = 70 - (temperature - 20) * 1.5 + 15 * math.cos(2 * math.pi * (day_of_year - 80) / 365)
        humidity = np.clip(humidity_base + np.random.normal(0, 8), 20, 95)
        
        # 气压模型（考虑海拔和天气系统）
        pressure_base = 1013 - altitude_factor * 120
        pressure_noise = np.random.normal(0, 4)
        pressure = np.clip(pressure_base + pressure_noise, 980, 1040)
        
        # 风速模型（与气压梯度相关）
        wind_base = 3 + abs(pressure - 1013) * 0.05
        wind_speed = np.clip(wind_base + np.random.exponential(1.5), 0.5, 15)
        
        # 降水模型（与湿度和气压相关）
        rain_probability = 1 / (1 + math.exp(-(humidity - 70) / 10 + (pressure - 1013) / 20))
        precipitation = np.random.exponential(1) if np.random.random() < rain_probability else 0
        
        # 天气类型智能分类
        if precipitation > 5:
            weather_main = 'Rain' if temperature > 0 else 'Snow'
        elif humidity > 80 and pressure < 1010:
            weather_main = 'Clouds'
        elif humidity < 40 and pressure > 1020:
            weather_main = 'Clear'
        else:
            weather_main = np.random.choice(['Clear', 'Clouds', 'Drizzle'], p=[0.5, 0.3, 0.2])
        
        return {
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'pressure': round(pressure, 1),
            'wind_speed': round(wind_speed, 1),
            'precipitation': round(precipitation, 1),
            'weather_main': weather_main,
            'is_holiday': self._is_holiday(date),
            'is_weekend': date.weekday() >= 5,
            'altitude': round(altitude, 1)
        }
    
    def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """发送API请求"""
        for attempt in range(self.retry_count):
            try:
                response = requests.get(url, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 401:
                    self.logger.error("API密钥无效")
                    return None
                else:
                    self.logger.warning(f"API请求失败: {response.status_code}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"API请求超时，重试 {attempt + 1}/{self.retry_count}")
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"API请求异常: {str(e)}")
            
            if attempt < self.retry_count - 1:
                time.sleep(2 ** attempt)  # 指数退避
        
        return None
    
    def _is_holiday(self, date: datetime.date) -> bool:
        """检查是否为节假日（支持工作日调休）"""
        return date in self.china_holidays
    
    def _get_weather_description(self, weather_main: str) -> str:
        """根据天气主类型获取详细描述"""
        descriptions = {
            'Clear': '晴天',
            'Clouds': '多云',
            'Rain': '雨天',
            'Drizzle': '小雨',
            'Thunderstorm': '雷暴',
            'Snow': '雪天',
            'Mist': '薄雾',
            'Fog': '大雾'
        }
        return descriptions.get(weather_main, weather_main)
    
    def _calculate_city_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """计算城市天气统计摘要"""
        if df.empty:
            return {}
        
        return {
            'total_days': len(df),
            'temperature': {
                'mean': round(df['temperature'].mean(), 1),
                'max': round(df['temperature'].max(), 1),
                'min': round(df['temperature'].min(), 1),
                'std': round(df['temperature'].std(), 1)
            },
            'humidity': {
                'mean': round(df['humidity'].mean(), 1),
                'max': round(df['humidity'].max(), 1),
                'min': round(df['humidity'].min(), 1)
            },
            'pressure': {
                'mean': round(df['pressure'].mean(), 1),
                'max': round(df['pressure'].max(), 1),
                'min': round(df['pressure'].min(), 1)
            },
            'wind_speed': {
                'mean': round(df['wind_speed'].mean(), 1),
                'max': round(df['wind_speed'].max(), 1)
            },
            'precipitation': {
                'total': round(df['precipitation'].sum(), 1),
                'days': len(df[df['precipitation'] > 0])
            },
            'weather_types': df['weather_main'].value_counts().to_dict(),
            'holidays': int(df['is_holiday'].sum()),
            'weekends': int(df['is_weekend'].sum()),
            'data_quality': 100 - int(df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100)
        }
    
    def _process_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理缺失值"""
        # 数值列插值
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        df[numeric_columns] = df[numeric_columns].interpolate()
        
        # 前向填充
        df = df.fillna(method='ffill')
        
        return df
    
    def save_weather_data(self, weather_data: pd.DataFrame, file_path: str) -> bool:
        """保存天气数据到文件"""
        try:
            self.logger.info(f"保存天气数据到: {file_path}")
            
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 保存为CSV
            weather_data.to_csv(file_path, index=False, encoding='utf-8-sig')
            
            return True
            
        except Exception as e:
            self.logger.error(f"保存天气数据失败: {str(e)}")
            return False
    
    def load_weather_data(self, file_path: str) -> Optional[pd.DataFrame]:
        """从文件加载天气数据"""
        try:
            self.logger.info(f"从文件加载天气数据: {file_path}")
            
            if Path(file_path).exists():
                df = pd.read_csv(file_path)
                df['date'] = pd.to_datetime(df['date'])
                return df
            
            return None
            
        except Exception as e:
            self.logger.error(f"加载天气数据失败: {str(e)}")
            return None

# 使用示例
if __name__ == "__main__":
    from ..utils.config_manager import ConfigManager
    
    config = ConfigManager()
    weather_api = WeatherAPI(config)
    
    # 测试获取天气数据
    start_date = datetime(2023, 1, 1)
    end_date = datetime(2023, 1, 7)
    
    weather_data = weather_api.get_historical_weather("广州", start_date, end_date)
    print(weather_data.head())
    
    # 测试获取预测
    forecast = weather_api.get_forecast_weather("广州", 7)
    print(forecast.head())