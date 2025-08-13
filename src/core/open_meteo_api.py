#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open-Meteo天气数据API模块
提供高精度的天气因素数据获取
支持历史数据、预报数据、和多种气象要素
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

class OpenMeteoAPI(LoggerMixin):
    """Open-Meteo天气数据API类"""
    
    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config = config_manager
        
        # API端点
        self.forecast_url = "https://api.open-meteo.com/v1/forecast"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        self.historical_url = "https://archive-api.open-meteo.com/v1/era5"
        
        self.timeout = self.config.get('open_meteo.timeout', 30)
        self.retry_count = self.config.get('open_meteo.retry_count', 3)
        
        # 扩展的城市坐标数据库
        self.city_coordinates = {
            # 广东省
            "广州": {"lat": 23.1291, "lon": 113.2644, "timezone": "Asia/Shanghai"},
            "深圳": {"lat": 22.5431, "lon": 114.0579, "timezone": "Asia/Shanghai"},
            "东莞": {"lat": 23.0489, "lon": 113.7447, "timezone": "Asia/Shanghai"},
            "佛山": {"lat": 23.0350, "lon": 113.1244, "timezone": "Asia/Shanghai"},
            "中山": {"lat": 22.5170, "lon": 113.3920, "timezone": "Asia/Shanghai"},
            "珠海": {"lat": 22.3193, "lon": 113.5824, "timezone": "Asia/Shanghai"},
            "惠州": {"lat": 23.0817, "lon": 114.4152, "timezone": "Asia/Shanghai"},
            "江门": {"lat": 22.5792, "lon": 113.0940, "timezone": "Asia/Shanghai"},
            "肇庆": {"lat": 23.0515, "lon": 112.4650, "timezone": "Asia/Shanghai"},
            "汕头": {"lat": 23.3541, "lon": 116.6822, "timezone": "Asia/Shanghai"},
            
            # 其他主要城市
            "北京": {"lat": 39.9042, "lon": 116.4074, "timezone": "Asia/Shanghai"},
            "上海": {"lat": 31.2304, "lon": 121.4737, "timezone": "Asia/Shanghai"},
            "成都": {"lat": 30.5728, "lon": 104.0668, "timezone": "Asia/Shanghai"},
            "杭州": {"lat": 30.2741, "lon": 120.1551, "timezone": "Asia/Shanghai"},
            "武汉": {"lat": 30.5928, "lon": 114.3055, "timezone": "Asia/Shanghai"},
            "西安": {"lat": 34.3416, "lon": 108.9398, "timezone": "Asia/Shanghai"},
            "南京": {"lat": 32.0603, "lon": 118.7969, "timezone": "Asia/Shanghai"},
            "重庆": {"lat": 29.5630, "lon": 106.5516, "timezone": "Asia/Shanghai"},
            "天津": {"lat": 39.3434, "lon": 117.3616, "timezone": "Asia/Shanghai"},
            "长沙": {"lat": 28.2282, "lon": 112.9388, "timezone": "Asia/Shanghai"},
            "青岛": {"lat": 36.0671, "lon": 120.3826, "timezone": "Asia/Shanghai"},
            "大连": {"lat": 38.9140, "lon": 121.6147, "timezone": "Asia/Shanghai"},
            "厦门": {"lat": 24.4798, "lon": 118.0894, "timezone": "Asia/Shanghai"},
            "苏州": {"lat": 31.2990, "lon": 120.5853, "timezone": "Asia/Shanghai"}
        }
        
        # 中国法定节假日
        self.china_holidays = holidays.China(years=[2023, 2024, 2025])
        
        # 天气要素映射
        self.weather_variables = [
            "temperature_2m",           # 2米温度
            "relativehumidity_2m",        # 2米相对湿度
            "dewpoint_2m",               # 2米露点温度
            "apparent_temperature",       # 体感温度
            "pressure_msl",              # 海平面气压
            "surface_pressure",          # 地表气压
            "precipitation",             # 降水量
            "rain",                      # 降雨量
            "snowfall",                  # 降雪量
            "cloudcover",                # 云量
            "cloudcover_low",            # 低云量
            "cloudcover_mid",            # 中云量
            "cloudcover_high",           # 高云量
            "windspeed_10m",             # 10米风速
            "windspeed_80m",             # 80米风速
            "windspeed_120m",            # 120米风速
            "winddirection_10m",         # 10米风向
            "winddirection_80m",         # 80米风向
            "winddirection_120m",          # 120米风向
            "shortwave_radiation",       # 短波辐射
            "direct_radiation",          # 直接辐射
            "diffuse_radiation",         # 散射辐射
            "vapor_pressure_deficit",    # 水汽压差
            "evapotranspiration",        # 蒸散发
            "et0_fao_evapotranspiration", # FAO参考蒸散发
            "soil_temperature_0_to_7cm",  # 0-7cm土壤温度
            "soil_temperature_7_to_28cm", # 7-28cm土壤温度
            "soil_temperature_28_to_100cm", # 28-100cm土壤温度
            "soil_moisture_0_to_7cm",     # 0-7cm土壤湿度
            "soil_moisture_7_to_28cm",    # 7-28cm土壤湿度
            "soil_moisture_28_to_100cm"   # 28-100cm土壤湿度
        ]
    
    def search_city(self, city_name: str) -> Optional[Dict]:
        """搜索城市坐标"""
        try:
            params = {
                'name': city_name,
                'count': 1,
                'language': 'zh',
                'format': 'json'
            }
            
            response = self._make_request(self.geocoding_url, params)
            if response and 'results' in response and response['results']:
                result = response['results'][0]
                return {
                    'name': result.get('name', city_name),
                    'lat': result['latitude'],
                    'lon': result['longitude'],
                    'timezone': result.get('timezone', 'Asia/Shanghai')
                }
            return None
            
        except Exception as e:
            self.logger.error(f"搜索城市失败: {str(e)}")
            return None
    
    def get_historical_weather(self, city: str, days: int = 7) -> pd.DataFrame:
        """获取历史天气数据"""
        try:
            coords = self.search_city(city)
            if not coords:
                raise ValueError(f"未找到城市: {city}")
            
            end_date = datetime.now().date() - timedelta(days=2)
            start_date = end_date - timedelta(days=days-1)
            
            params = {
                'latitude': coords['lat'],
                'longitude': coords['lon'],
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
                'timezone': coords['timezone']
            }
            
            response = requests.get(self.historical_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'daily' not in data:
                raise ValueError("API响应格式错误")
            
            daily_data = data['daily']
            df = pd.DataFrame(daily_data)
            
            # 重命名列以保持一致性
            column_mapping = {
                'time': 'date',
                'temperature_2m_max': 'max_temperature',
                'temperature_2m_min': 'min_temperature',
                'precipitation_sum': 'precipitation'
            }
            df = df.rename(columns=column_mapping)
            
            # 确保日期格式正确
            df['date'] = pd.to_datetime(df['date'])
            df['city'] = city
            
            return df
            
        except Exception as e:
            print(f"获取历史天气数据失败: {e}")
            return pd.DataFrame()

    def get_forecast_weather(self, city: str, days: int = 7) -> pd.DataFrame:
        """获取预报天气数据"""
        try:
            coords = self.search_city(city)
            if not coords:
                raise ValueError(f"未找到城市: {city}")
            
            params = {
                'latitude': coords['lat'],
                'longitude': coords['lon'],
                'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
                'forecast_days': days,
                'timezone': coords['timezone']
            }
            
            response = requests.get(self.forecast_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'daily' not in data:
                raise ValueError("API响应格式错误")
            
            daily_data = data['daily']
            df = pd.DataFrame(daily_data)
            
            # 重命名列以保持一致性
            column_mapping = {
                'time': 'date',
                'temperature_2m_max': 'max_temperature',
                'temperature_2m_min': 'min_temperature',
                'precipitation_sum': 'precipitation'
            }
            df = df.rename(columns=column_mapping)
            
            # 确保日期格式正确
            df['date'] = pd.to_datetime(df['date'])
            df['city'] = city
            df['data_type'] = 'forecast'
            
            return df
            
        except Exception as e:
            print(f"获取预报天气数据失败: {e}")
            return pd.DataFrame()

    def get_enhanced_weather_data(self, city: str, days: int = 7) -> pd.DataFrame:
        """获取增强天气数据（历史和预报合并）"""
        try:
            # 获取历史数据（最近3天）
            historical_days = min(3, days)  # 限制历史数据为最近3天
            hist_data = self.get_historical_weather(city, days=historical_days)
            
            # 获取预报数据（剩余天数）
            forecast_days = max(1, days - historical_days)
            forecast_data = self.get_forecast_weather(city, days=forecast_days)
            
            # 合并数据
            if not hist_data.empty and not forecast_data.empty:
                # 确保列名一致
                common_cols = ['date', 'max_temperature', 'min_temperature', 'precipitation']
                hist_cols = [col for col in common_cols if col in hist_data.columns]
                forecast_cols = [col for col in common_cols if col in forecast_data.columns]
                
                # 合并数据
                combined_data = pd.concat([
                    hist_data[hist_cols],
                    forecast_data[forecast_cols]
                ], ignore_index=True)
                
                # 按日期排序并去重
                combined_data = combined_data.sort_values('date').drop_duplicates(subset=['date'])
                combined_data['city'] = city
                
                return combined_data
            elif not hist_data.empty:
                return hist_data
            elif not forecast_data.empty:
                return forecast_data
            else:
                return pd.DataFrame()
                
        except Exception as e:
            print(f"获取增强天气数据失败: {e}")
            return pd.DataFrame()

    def _make_request(self, url: str, params: Dict[str, Any]) -> Optional[Dict]:
        """
        发送HTTP请求并处理响应
        
        Args:
            url: 请求URL
            params: 请求参数
            
        Returns:
            JSON响应数据
        """
        for attempt in range(self.retry_count):
            try:
                self.logger.debug(f"请求URL: {url}")
                self.logger.debug(f"请求参数: {params}")
                
                response = requests.get(url, params=params, timeout=self.timeout)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    self.logger.warning(f"请求失败 (尝试 {attempt+1}/{self.retry_count}): {response.status_code} {response.reason}")
                    
            except Exception as e:
                self.logger.warning(f"请求失败 (尝试 {attempt+1}/{self.retry_count}): {str(e)}")
                if attempt == self.retry_count - 1:
                    self.logger.error(f"所有请求尝试都失败: {str(e)}")
                    return None
                
            time.sleep(1)
        
        return None
    
    def get_available_variables(self) -> List[str]:
        """获取可用的天气要素列表"""
        return self.weather_variables.copy()
    
    def get_city_list(self) -> List[str]:
        """获取支持的城市列表"""
        return list(self.city_coordinates.keys())
    
    def add_custom_city(self, city_name: str, lat: float, lon: float, timezone: str = "Asia/Shanghai"):
        """添加自定义城市"""
        self.city_coordinates[city_name] = {
            "lat": lat,
            "lon": lon,
            "timezone": timezone
        }
        self.logger.info(f"添加自定义城市: {city_name} ({lat}, {lon})")