#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试脚本 - 验证Open-Meteo API集成
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from core.open_meteo_api import OpenMeteoAPI
from utils.config_manager import ConfigManager

def test_simple():
    """简化测试函数"""
    print("🚀 简化测试Open-Meteo集成...")
    
    try:
        # 初始化
        api = OpenMeteoAPI(ConfigManager())
        print("✅ API初始化成功")
        
        # 城市搜索
        city = "广州"
        city_info = api.search_city(city)
        if not city_info:
            print(f"❌ 城市搜索失败: {city}")
            return False
        
        print(f"✅ 城市信息: {city_info}")
        
        # 设置日期范围
        end_date = datetime.now().date() - timedelta(days=2)
        start_date = end_date - timedelta(days=6)  # 7天历史数据
        print(f"📅 日期范围: {start_date} 到 {end_date}")
        
        # 测试历史天气数据
        print("\n🌡️ 获取历史天气数据...")
        hist_data = api.get_historical_weather(
            city=city,
            days=7  # 使用days参数而非start_date/end_date
        )
        
        if hist_data.empty:
            print("⚠️ 无历史天气数据")
        else:
            print(f"✅ 历史数据: {len(hist_data)} 条记录")
            print("📊 样本数据:")
            print(hist_data.head(3)[['date', 'max_temperature', 'min_temperature']].to_string(index=False))
        
        # 测试预报天气数据
        print("\n🌤️ 获取预报天气数据...")
        forecast_data = api.get_forecast_weather(
            city=city,
            days=7  # 使用days参数
        )
        
        if forecast_data.empty:
            print("⚠️ 无预报天气数据")
        else:
            print(f"✅ 预报数据: {len(forecast_data)} 条记录")
            print("📊 样本数据:")
            print(forecast_data.head(3)[['date', 'max_temperature', 'min_temperature']].to_string(index=False))
        
        # 测试增强天气数据
        print("\n🌈 获取增强天气数据...")
        enhanced_data = api.get_enhanced_weather_data(
            city=city,
            days=7  # 使用days参数
        )
        
        if enhanced_data.empty:
            print("⚠️ 无增强天气数据")
        else:
            print(f"✅ 增强数据: {len(enhanced_data)} 条记录")
            available_cols = [col for col in ['date', 'max_temperature', 'min_temperature', 'precipitation'] if col in enhanced_data.columns]
            if available_cols:
                print("📊 样本数据:")
                print(enhanced_data.head(3)[available_cols].to_string(index=False))
        
        # 检查是否有任何数据获取成功
        success_count = sum([
            not hist_data.empty,
            not forecast_data.empty, 
            not enhanced_data.empty
        ])
        
        if success_count > 0:
            print(f"\n✅ 测试完成！成功获取了 {success_count}/3 种数据")
            return True
        else:
            print("\n❌ 所有数据获取失败")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple()
    if success:
        print("\n🎉 Open-Meteo集成验证完成！")
    else:
        print("\n❌ 需要进一步调试")