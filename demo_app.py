#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open-Meteo API演示应用
无需GUI，直接展示API集成效果
"""

import sys
import os
from datetime import datetime
import pandas as pd

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from core.open_meteo_api import OpenMeteoAPI
from utils.config_manager import ConfigManager

def demo_weather_app():
    """演示天气应用"""
    print("🌤️ Open-Meteo API 天气演示")
    print("=" * 50)
    
    try:
        # 初始化API
        print("🔧 初始化Open-Meteo API...")
        api = OpenMeteoAPI(ConfigManager())
        print("✅ API初始化成功")
        
        # 演示城市
        cities = ["广州", "北京", "上海"]
        
        for city in cities:
            print(f"\n📍 {city}天气信息")
            print("-" * 30)
            
            # 城市搜索
            city_info = api.search_city(city)
            if not city_info:
                print(f"⚠️ 找不到{city}")
                continue
                
            print(f"坐标: {city_info['lat']:.2f}, {city_info['lon']:.2f}")
            
            # 获取增强天气数据
            weather_data = api.get_enhanced_weather_data(city, days=5)
            
            if weather_data.empty:
                print("⚠️ 暂无天气数据")
                continue
            
            # 显示天气信息
            print(f"📊 获取到{len(weather_data)}天数据")
            
            # 显示最近3天
            display_data = weather_data.tail(3)[['date', 'max_temperature', 'min_temperature', 'precipitation']]
            
            for _, row in display_data.iterrows():
                date_str = row['date'].strftime('%m-%d')
                max_temp = row['max_temperature']
                min_temp = row['min_temperature']
                precip = row['precipitation']
                
                weather_icon = "☀️" if precip == 0 else "🌧️" if precip > 5 else "⛅"
                
                print(f"{weather_icon} {date_str}: {max_temp:.1f}°C/{min_temp:.1f}°C "
                      f"(降水: {precip:.1f}mm)")
        
        print("\n" + "=" * 50)
        print("🎉 演示完成！Open-Meteo API集成成功")
        
        # 提供交互式查询
        print("\n🔍 交互式查询")
        while True:
            city = input("\n请输入城市名称(或输入q退出): ").strip()
            if city.lower() == 'q':
                break
            
            if not city:
                continue
            
            city_info = api.search_city(city)
            if not city_info:
                print(f"⚠️ 找不到{city}")
                continue
            
            print(f"📍 {city_info['name']} ({city_info['lat']:.2f}, {city_info['lon']:.2f})")
            
            # 获取天气数据
            forecast = api.get_forecast_weather(city, days=3)
            if not forecast.empty:
                print("🌤️ 未来3天预报:")
                for _, day in forecast.iterrows():
                    date_str = day['date'].strftime('%m-%d')
                    print(f"  {date_str}: {day['max_temperature']:.1f}°C/{day['min_temperature']:.1f}°C")
            else:
                print("⚠️ 无法获取天气数据")
        
    except KeyboardInterrupt:
        print("\n👋 感谢使用！")
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    demo_weather_app()