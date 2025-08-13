#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open-Meteo集成快速测试脚本
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from core.open_meteo_api import OpenMeteoAPI
from utils.config_manager import ConfigManager

def quick_test():
    """快速测试Open-Meteo集成功能"""
    print("🚀 快速测试Open-Meteo集成...")
    
    try:
        # 初始化配置和API
        config = ConfigManager()
        api = OpenMeteoAPI(config)
        
        # 测试城市
        city = "广州"
        
        # 使用字符串格式的日期
        end_date = datetime.now().date() - timedelta(days=2)
        start_date = end_date - timedelta(days=7)
        
        # 转换为字符串格式
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        print(f"📍 测试城市: {city}")
        print(f"📅 日期范围: {start_date_str} 到 {end_date_str}")
        
        # 测试1: 历史天气数据
        print("🌡️ 获取历史天气数据...")
        historical_data = api.get_historical_weather(
            city=city,
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        if not historical_data.empty:
            print(f"✅ 历史数据获取成功！")
            print(f"📊 数据条数: {len(historical_data)}")
            print(f"🌡️ 温度范围: {historical_data['max_temp'].max():.1f}°C - {historical_data['min_temp'].min():.1f}°C")
            print("\n📋 历史数据样本:")
            print(historical_data.head(3))
        else:
            print("❌ 历史数据获取失败")
        
        # 测试2: 预报天气数据
        print("\n🌤️ 获取预报天气数据...")
        forecast_data = api.get_forecast_weather(city=city, forecast_days=7)
        
        if not forecast_data.empty:
            print(f"✅ 预报数据获取成功！")
            print(f"📊 预报条数: {len(forecast_data)}")
            if len(forecast_data) > 0:
                print(f"🌡️ 未来温度: {forecast_data['max_temp'].iloc[0]:.1f}°C - {forecast_data['min_temp'].iloc[0]:.1f}°C")
            print("\n📋 预报数据样本:")
            print(forecast_data.head(3))
        else:
            print("❌ 预报数据获取失败")
        
        # 测试3: 自定义变量
        print("\n🎯 测试自定义变量...")
        custom_vars = ['temperature_2m_max', 'precipitation_sum']
        custom_data = api.get_historical_weather(
            city=city,
            start_date=start_date_str,
            end_date=end_date_str,
            variables=custom_vars
        )
        
        if not custom_data.empty:
            print(f"✅ 自定义变量获取成功！")
            print(f"📊 变量: {list(custom_data.columns)}")
            print("\n📋 自定义数据样本:")
            print(custom_data.head(2))
        else:
            print("❌ 自定义变量获取失败")
        
        print("\n🎉 快速测试完成！Open-Meteo集成成功！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n🔧 请检查网络连接和配置设置")
        return False

if __name__ == "__main__":
    success = quick_test()
    if success:
        print("\n🎉 所有测试通过！")
    else:
        print("\n💥 测试失败，请查看错误信息")
    
    if success:
        print("\n🎉 快速测试完成！Open-Meteo集成成功！")
        print("\n现在您可以在应用中使用:")
        print("- 高精度历史天气数据")
        print("- 未来天气预报")
        print("- 丰富的气象要素")
        print("- 多城市支持")
    else:
        print("\n🔧 请检查网络连接和配置设置")