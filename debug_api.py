#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API调试脚本 - 检查Open-Meteo API参数和响应
"""

import sys
import os
import requests
from datetime import datetime, timedelta
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def debug_api_calls():
    """调试API调用"""
    print("🔍 调试Open-Meteo API调用...")
    
    # 测试参数
    city = "广州"
    lat = 23.1291
    lon = 113.2644
    
    # 历史天气API
    historical_url = "https://archive-api.open-meteo.com/v1/era5"
    
    # 设置日期
    end_date = datetime.now().date() - timedelta(days=2)
    start_date = end_date - timedelta(days=3)
    
    print(f"📅 日期: {start_date} 到 {end_date}")
    print(f"📍 坐标: {lat}, {lon}")
    
    # 测试历史天气参数 - 使用正确的变量名
    params = {
        'latitude': lat,
        'longitude': lon,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
        'timezone': 'Asia/Shanghai'
    }
    
    print(f"\n🔗 历史天气URL: {historical_url}")
    print(f"📋 参数: {json.dumps(params, indent=2)}")
    
    try:
        response = requests.get(historical_url, params=params, timeout=10)
        print(f"\n📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功获取数据")
            if 'daily' in data:
                daily_data = data['daily']
                print(f"📊 数据条数: {len(daily_data.get('time', []))}")
                print(f"🌡️ 最高温度: {daily_data.get('temperature_2m_max', [])[:3]}")
        else:
            print(f"❌ 错误响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    # 测试预报天气参数 - 使用正确的变量名
    forecast_url = "https://api.open-meteo.com/v1/forecast"
    forecast_params = {
        'latitude': lat,
        'longitude': lon,
        'daily': 'temperature_2m_max,temperature_2m_min,precipitation_sum',
        'forecast_days': 7,
        'timezone': 'Asia/Shanghai'
    }
    
    print(f"\n🔗 预报天气URL: {forecast_url}")
    print(f"📋 参数: {json.dumps(forecast_params, indent=2)}")
    
    try:
        response = requests.get(forecast_url, params=forecast_params, timeout=10)
        print(f"\n📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功获取预报数据")
            if 'daily' in data:
                daily_data = data['daily']
                print(f"📊 预报条数: {len(daily_data.get('time', []))}")
                print(f"🌡️ 预报温度: {daily_data.get('temperature_2m_max', [])}")
        else:
            print(f"❌ 错误响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")

if __name__ == "__main__":
    debug_api_calls()