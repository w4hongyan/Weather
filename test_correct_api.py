#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用正确参数测试Open-Meteo API
"""

import requests
import pandas as pd
from datetime import datetime, timedelta

def test_correct_api():
    """使用正确参数测试API"""
    print("🔍 使用正确参数测试Open-Meteo API...")
    
    # 广州坐标
    lat, lon = 23.1291, 113.2644
    
    # 使用正确的日期 - 使用过去的数据
    end_date = datetime(2024, 8, 10).date()
    start_date = datetime(2024, 8, 3).date()
    
    # 测试单个变量
    variables = ["temperature_2m"]
    
    # 历史API
    historical_url = "https://archive-api.open-meteo.com/v1/era5"
    
    # 方法一：使用逗号分隔的字符串
    params1 = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'daily': 'temperature_2m_max,temperature_2m_min,temperature_2m_mean',
        'timezone': 'Asia/Shanghai'
    }
    
    # 方法二：使用标准变量名
    params2 = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'daily': 'temperature_2m_max',
        'timezone': 'Asia/Shanghai'
    }
    
    print("🧪 测试方法一：逗号分隔字符串")
    print(f"参数: {params1}")
    
    try:
        response = requests.get(historical_url, params=params1)
        print(f"响应状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ 成功")
            print(f"字段: {list(data.get('daily', {}).keys())}")
            if 'daily' in data:
                daily = data['daily']
                print(f"数据长度: {len(daily.get('time', []))}")
                print(f"示例温度: {daily.get('temperature_2m_max', [])[:3]}")
        else:
            print(f"❌ 失败: {response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    print("\n🧪 测试方法二：单个变量")
    print(f"参数: {params2}")
    
    try:
        response = requests.get(historical_url, params=params2)
        print(f"响应状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ 成功")
            print(f"字段: {list(data.get('daily', {}).keys())}")
            if 'daily' in data:
                daily = data['daily']
                print(f"数据长度: {len(daily.get('time', []))}")
                print(f"示例温度: {daily.get('temperature_2m_max', [])[:3]}")
        else:
            print(f"❌ 失败: {response.text}")
    except Exception as e:
        print(f"❌ 错误: {e}")
    
    # 测试预报API
    forecast_url = "https://api.open-meteo.com/v1/forecast"
    forecast_params = {
        'latitude': lat,
        'longitude': lon,
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
        'forecast_days': 7,
        'timezone': 'Asia/Shanghai'
    }
    
    print("\n🧪 测试预报API")
    print(f"参数: {forecast_params}")
    
    try:
        response = requests.get(forecast_url, params=forecast_params)
        print(f"响应状态: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("✅ 预报成功")
            print(f"字段: {list(data.get('daily', {}).keys())}")
            if 'daily' in data:
                daily = data['daily']
                print(f"预报时间: {daily.get('time', [])}")
                print(f"最高温度: {daily.get('temperature_2m_max', [])}")
        else:
            print(f"❌ 预报失败: {response.text}")
    except Exception as e:
        print(f"❌ 预报错误: {e}")

if __name__ == "__main__":
    test_correct_api()