#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Open-Meteo集成测试脚本
测试Open-Meteo API的集成效果
"""

import os
import sys
from datetime import datetime, timedelta
import pandas as pd

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.core.weather_manager import WeatherManager
from src.utils.config_manager import ConfigManager

def test_basic_functionality():
    """测试基本功能"""
    print("🧪 开始测试Open-Meteo集成...")
    
    try:
        # 初始化配置和天气管理器
        config = ConfigManager()
        weather = WeatherManager(config)
        
        # 测试城市
        test_cities = ["广州", "深圳", "上海"]
        
        for city in test_cities:
            print(f"\n📍 测试城市: {city}")
            
            # 获取历史数据 - 使用过去7天的数据
            end_date = datetime.now().date() - timedelta(days=1)  # 昨天
            start_date = end_date - timedelta(days=7)  # 7天前
            
            print(f"   获取 {start_date} 到 {end_date} 的天气数据...")
            
            data = weather.get_weather_data(
                city=city,
                start_date=start_date,
                end_date=end_date,
                provider="open_meteo"
            )
            
            if data is not None and not data.empty:
                print(f"   ✅ 成功获取 {len(data)} 条记录")
                print(f"   📊 数据列: {list(data.columns)}")
                if 'temperature' in data.columns:
                    print(f"   🌡️ 温度范围: {data['temperature'].min():.1f}°C ~ {data['temperature'].max():.1f}°C")
                
                # 显示前3条记录
                print("\n   前3条记录:")
                print(data.head(3))
            else:
                print("   ❌ 获取数据失败")
                
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False
        
    return True

def test_forecast():
    """测试预测功能"""
    print("\n🔮 测试天气预测...")
    
    try:
        config = ConfigManager()
        weather = WeatherManager(config)
        
        # 获取预测数据
        forecast = weather.get_weather_data(
            city="广州",
            start_date=datetime.now().date(),
            end_date=datetime.now().date() + timedelta(days=3),
            provider="open_meteo",
            include_forecast=True
        )
        
        if forecast is not None and not forecast.empty:
            print(f"   ✅ 成功获取 {len(forecast)} 条预测记录")
            print("   📅 预测日期范围:")
            print(f"   从: {forecast['date'].min()}")
            print(f"   到: {forecast['date'].max()}")
            
            # 显示未来3天的预测
            future = forecast[forecast['date'] > datetime.now().date()]
            if not future.empty:
                print("\n   未来3天预测:")
                for _, row in future.head(3).iterrows():
                    print(f"   {row['date']}: {row['temperature']:.1f}°C, {row['humidity']:.0f}% 湿度")
                    
    except Exception as e:
        print(f"❌ 预测测试失败: {str(e)}")
        return False
        
    return True

def test_data_comparison():
    """测试数据源比较"""
    print("\n🔍 测试数据源比较...")
    
    try:
        config = ConfigManager()
        weather = WeatherManager(config)
        
        # 比较两个数据源
        comparison = weather.compare_data_sources(
            city="广州",
            date=datetime.now().date() - timedelta(days=1),
            variables=["temperature", "humidity", "pressure"]
        )
        
        if comparison:
            print("   ✅ 数据源比较完成")
            for provider, data in comparison.items():
                print(f"   📊 {provider}:")
                for var, value in data.items():
                    print(f"      {var}: {value}")
                    
    except Exception as e:
        print(f"❌ 比较测试失败: {str(e)}")
        return False
        
    return True

def test_cache_functionality():
    """测试缓存功能"""
    print("\n💾 测试缓存功能...")
    
    try:
        config = ConfigManager()
        weather = WeatherManager(config)
        
        start_time = datetime.now()
        
        # 第一次获取（缓存）
        data1 = weather.get_weather_data(
            city="广州",
            start_date=datetime.now().date() - timedelta(days=3),
            end_date=datetime.now().date(),
            provider="open_meteo",
            use_cache=True
        )
        
        first_time = datetime.now() - start_time
        
        # 第二次获取（应该使用缓存）
        start_time = datetime.now()
        data2 = weather.get_weather_data(
            city="广州",
            start_date=datetime.now().date() - timedelta(days=3),
            end_date=datetime.now().date(),
            provider="open_meteo",
            use_cache=True
        )
        
        second_time = datetime.now() - start_time
        
        print(f"   第一次耗时: {first_time.total_seconds():.2f}秒")
        print(f"   第二次耗时: {second_time.total_seconds():.2f}秒")
        
        if second_time < first_time:
            print("   ✅ 缓存功能正常工作")
        else:
            print("   ⚠️ 缓存可能未生效")
            
    except Exception as e:
        print(f"❌ 缓存测试失败: {str(e)}")
        return False
        
    return True

def test_custom_variables():
    """测试自定义变量"""
    print("\n⚙️ 测试自定义变量...")
    
    try:
        from src.core.open_meteo_api import OpenMeteoAPI
        
        api = OpenMeteoAPI()
        
        # 获取可用变量列表
        variables = api.get_available_variables()
        print(f"   ✅ 发现 {len(variables)} 个可用变量")
        
        # 测试特定变量
        custom_vars = [
            "temperature_2m",
            "relativehumidity_2m", 
            "precipitation",
            "windspeed_10m",
            "cloudcover",
            "shortwave_radiation"
        ]
        
        data = api.get_historical_weather(
            city="广州",
            start_date=datetime.now().date() - timedelta(days=2),
            end_date=datetime.now().date(),
            variables=custom_vars
        )
        
        if data is not None:
            print(f"   ✅ 成功获取自定义变量数据")
            print(f"   📊 数据形状: {data.shape}")
            print(f"   🔍 列: {list(data.columns)}")
            
    except Exception as e:
        print(f"❌ 自定义变量测试失败: {str(e)}")
        return False
        
    return True

def run_all_tests():
    """运行所有测试"""
    print("🚀 开始Open-Meteo集成测试...")
    
    tests = [
        ("基本功能", test_basic_functionality),
        ("预测功能", test_forecast),
        ("数据源比较", test_data_comparison),
        ("缓存功能", test_cache_functionality),
        ("自定义变量", test_custom_variables)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*50}")
            print(f"运行测试: {test_name}")
            print('='*50)
            
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name} 测试通过")
            else:
                print(f"❌ {test_name} 测试失败")
                
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {str(e)}")
            results.append((test_name, False))
    
    # 汇总结果
    print(f"\n{'='*60}")
    print("测试结果汇总")
    print('='*60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n📊 总计: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试通过！Open-Meteo集成成功！")
    else:
        print("⚠️ 部分测试失败，请检查配置和网络连接")
        
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n🎊 恭喜！您可以开始使用Open-Meteo天气数据了！")
        print("\n下一步建议:")
        print("1. 在GUI中配置天气数据源")
        print("2. 使用天气管理器获取数据")
        print("3. 查看生成的数据文件")
    else:
        print("\n🔧 请检查以下项目:")
        print("1. 网络连接是否正常")
        print("2. 配置文件是否正确")
        print("3. 依赖库是否安装")

    def test_forecast_functionality(self):
        """测试预报功能"""
        print("\n🔮 测试预报功能...")
        
        cities = ["广州", "上海", "深圳"]
        forecast_days_list = [3, 7, 14]
        
        results = []
        
        for city in cities:
            print(f"\n📍 城市: {city}")
            
            for days in forecast_days_list:
                print(f"📅 预报天数: {days}")
                
                forecast = self.api.get_forecast_weather(
                    city=city,
                    forecast_days=days
                )
                
                if not forecast.empty:
                    print(f"✅ {city} {days}天预报: {len(forecast)} 条记录")
                    print(f"📊 日期范围: {forecast.index[0]} 到 {forecast.index[-1]}")
                    
                    # 验证预报日期范围
                    expected_days = min(days, 16)  # API最大支持16天
                    actual_days = len(forecast)
                    
                    if actual_days == expected_days:
                        print("✅ 预报日期范围正确")
                    else:
                        print(f"⚠️ 期望 {expected_days} 天，实际 {actual_days} 天")
                    
                    results.append({
                        'city': city,
                        'forecast_days': days,
                        'actual_days': actual_days,
                        'success': True
                    })
                else:
                    print(f"❌ {city} {days}天预报获取失败")
                    results.append({
                        'city': city,
                        'forecast_days': days,
                        'actual_days': 0,
                        'success': False
                    })
        
        return results

    def test_data_comparison(self):
        """测试数据源比较"""
        print("\n📊 测试数据源比较...")
        
        city = "广州"
        
        # 使用字符串格式的日期
        end_date = datetime.now().date() - timedelta(days=2)
        start_date = end_date - timedelta(days=7)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 获取历史数据
        historical = self.api.get_historical_weather(
            city=city,
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        # 获取预报数据
        forecast = self.api.get_forecast_weather(
            city=city,
            forecast_days=7
        )
        
        results = []
        
        if not historical.empty and not forecast.empty:
            print(f"✅ 数据源比较测试成功")
            print(f"📊 历史数据: {len(historical)} 条记录")
            print(f"📊 预报数据: {len(forecast)} 条记录")
            
            # 检查数据重叠
            historical_dates = set(historical.index)
            forecast_dates = set(forecast.index)
            overlap = historical_dates.intersection(forecast_dates)
            
            if overlap:
                print(f"⚠️ 数据重叠: {len(overlap)} 天")
            else:
                print("✅ 数据无重叠")
            
            # 检查温度范围合理性
            hist_temp_range = (historical['max_temp'].min(), historical['max_temp'].max())
            forecast_temp_range = (forecast['max_temp'].min(), forecast['max_temp'].max())
            
            print(f"🌡️ 历史温度范围: {hist_temp_range[0]:.1f}°C - {hist_temp_range[1]:.1f}°C")
            print(f"🌡️ 预报温度范围: {forecast_temp_range[0]:.1f}°C - {forecast_temp_range[1]:.1f}°C")
            
            results.append({
                'test': 'data_comparison',
                'historical_records': len(historical),
                'forecast_records': len(forecast),
                'overlap_days': len(overlap),
                'success': True
            })
        else:
            print("❌ 数据源比较测试失败")
            results.append({
                'test': 'data_comparison',
                'success': False,
                'error': '数据获取失败'
            })
        
        return results

    def test_custom_variables(self):
        """测试自定义变量"""
        print("\n⚙️ 测试自定义变量...")
        
        city = "广州"
        
        # 使用字符串格式的日期
        end_date = datetime.now().date() - timedelta(days=2)
        start_date = end_date - timedelta(days=3)
        
        start_date_str = start_date.strftime('%Y-%m-%d')
        end_date_str = end_date.strftime('%Y-%m-%d')
        
        # 测试不同的变量组合
        variable_sets = [
            ['temperature_2m_max', 'temperature_2m_min'],
            ['precipitation_sum', 'relativehumidity_2m_mean'],
            ['temperature_2m_max', 'precipitation_sum', 'windspeed_10m_max']
        ]
        
        results = []
        
        for variables in variable_sets:
            print(f"\n🔍 变量组合: {variables}")
            
            data = self.api.get_historical_weather(
                city=city,
                start_date=start_date_str,
                end_date=end_date_str,
                variables=variables
            )
            
            if not data.empty:
                print(f"✅ 成功获取 {len(variables)} 个变量")
                print(f"📊 实际列: {list(data.columns)}")
                
                # 验证请求的变量都存在
                expected_cols = [self.api._get_friendly_name(var) for var in variables]
                actual_cols = list(data.columns)
                
                missing = [col for col in expected_cols if col not in actual_cols]
                if missing:
                    print(f"⚠️ 缺少变量: {missing}")
                else:
                    print("✅ 所有变量都存在")
                
                results.append({
                    'variables': variables,
                    'columns': list(data.columns),
                    'records': len(data),
                    'success': True
                })
            else:
                print(f"❌ 变量组合 {variables} 获取失败")
                results.append({
                    'variables': variables,
                    'success': False
                })
        
        return results