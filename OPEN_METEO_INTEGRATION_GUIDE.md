# 🌤️ Open-Meteo 集成指南

## 📋 概述

本指南介绍如何将高精度的Open-Meteo天气数据API集成到现有的天气数据建模与分析系统中。Open-Meteo提供比传统API更丰富的气象要素和更高的数据精度。

## 🎯 新增功能

### ✅ 支持的数据源
- **Open-Meteo (推荐)**: 免费、高精度、多要素
- **OpenWeatherMap**: 传统数据源
- **智能切换**: 自动故障转移

### 📊 新增气象要素
- 2米温度、湿度、露点温度
- 体感温度、海平面气压
- 降水量、降雨量、降雪量
- 云量（低、中、高云）
- 风速（10米、80米、120米）
- 太阳辐射（短波、直接、散射）
- 土壤温度（0-7cm、7-28cm、28-100cm）
- 土壤湿度（多层）
- 蒸散发、水汽压差

## 🚀 快速集成

### 1. 配置文件更新
```json
{
  "weather_api": {
    "provider": "open_meteo",
    "timeout": 30,
    "retry_count": 3
  },
  "open_meteo": {
    "base_url": "https://api.open-meteo.com/v1/forecast",
    "archive_url": "https://archive-api.open-meteo.com/v1/era5",
    "timeout": 30,
    "retry_count": 3
  }
}
```

### 2. 代码集成示例

#### 基础使用
```python
from core.weather_manager import WeatherManager
from utils.config_manager import ConfigManager

# 初始化
config = ConfigManager()
weather = WeatherManager(config)

# 获取天气数据
data = weather.get_weather_data(
    city="广州",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    provider="open_meteo",  # 指定数据源
    include_forecast=True,
    forecast_days=7
)
```

#### 多城市批量获取
```python
cities = ["广州", "深圳", "上海"]
multi_data = weather.get_multi_city_weather(
    cities=cities,
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)
```

#### 数据源比较
```python
comparison = weather.compare_data_sources(
    city="广州",
    date=datetime(2024, 1, 15),
    variables=["temperature", "humidity", "pressure"]
)
```

## 🔧 高级功能

### 自定义天气要素
```python
# 指定需要的天气要素
variables = [
    "temperature_2m",
    "relativehumidity_2m",
    "precipitation",
    "windspeed_10m",
    "cloudcover",
    "shortwave_radiation"
]

data = weather.open_meteo_api.get_historical_weather(
    city="广州",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    variables=variables
)
```

### 添加自定义城市
```python
# 添加不在内置列表的城市
weather.open_meteo_api.add_custom_city(
    city_name="三亚",
    lat=18.2528,
    lon=109.5120,
    timezone="Asia/Shanghai"
)
```

### 缓存管理
```python
# 启用缓存（默认启用）
data = weather.get_weather_data(
    city="广州",
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31),
    use_cache=True,
    cache_expiry_days=7
)
```

## 📈 性能优化

### 批量处理优化
```python
# 批量获取多个时间段
def get_batch_weather(cities, date_ranges):
    results = {}
    for city in cities:
        city_data = []
        for start, end in date_ranges:
            data = weather.get_weather_data(city, start, end)
            city_data.append(data)
        results[city] = pd.concat(city_data)
    return results
```

### 错误处理和重试
```python
try:
    data = weather.get_weather_data(city, start_date, end_date)
except Exception as e:
    print(f"获取天气数据失败: {e}")
    # 自动故障转移到备用数据源
    data = weather.get_weather_data(city, start_date, end_date, provider="openweathermap")
```

## 🎨 UI集成示例

### 天气数据源选择器
```python
# 在GUI中添加数据源选择
self.weather_provider_combo = QComboBox()
self.weather_provider_combo.addItems(["自动选择", "Open-Meteo", "OpenWeatherMap"])

# 根据选择获取数据
provider_map = {
    "自动选择": "auto",
    "Open-Meteo": "open_meteo",
    "OpenWeatherMap": "openweathermap"
}

selected_provider = provider_map[self.weather_provider_combo.currentText()]
data = weather.get_weather_data(city, start_date, end_date, provider=selected_provider)
```

### 天气要素选择器
```python
# 多选天气要素
self.weather_variables_list = QListWidget()
variables = weather.open_meteo_api.get_available_variables()
self.weather_variables_list.addItems(variables)

# 获取选中的要素
selected_vars = [item.text() for item in self.weather_variables_list.selectedItems()]
```

## 🔍 数据验证

### 数据质量检查
```python
def validate_weather_data(data):
    """验证天气数据质量"""
    checks = {
        'total_records': len(data),
        'missing_values': data.isnull().sum().to_dict(),
        'date_range': (data['date'].min(), data['date'].max()),
        'temperature_range': (data['temperature'].min(), data['temperature'].max()),
        'data_completeness': 1 - (data.isnull().sum().max() / len(data))
    }
    return checks

# 使用示例
validation = validate_weather_data(data)
print(f"数据完整性: {validation['data_completeness']:.2%}")
```

## 📊 数据导出

### 多种格式支持
```python
# 导出为标准格式
weather.save_weather_data(data, "weather_data.csv")
weather.save_weather_data(data, "weather_data.xlsx")

# 导出为JSON
import json
with open("weather_data.json", "w", encoding="utf-8") as f:
    json.dump(data.to_dict(orient="records"), f, ensure_ascii=False, indent=2)
```

## 🚀 开始使用

### 1. 运行测试
```bash
# 测试Open-Meteo集成
python src/core/open_meteo_api.py

# 测试天气管理器
python src/core/weather_manager.py
```

### 2. 更新现有代码
```python
# 替换原有的WeatherAPI调用
# 从:
from core.weather_api import WeatherAPI
weather = WeatherAPI(config)

# 到:
from core.weather_manager import WeatherManager
weather = WeatherManager(config)
```

### 3. 验证集成
```python
# 快速验证
def quick_test():
    from core.weather_manager import WeatherManager
    from datetime import datetime
    
    weather = WeatherManager(ConfigManager())
    data = weather.get_weather_data("广州", datetime(2024, 1, 1), datetime(2024, 1, 7))
    print(f"成功获取{len(data)}条天气记录")
    print(data.head())

if __name__ == "__main__":
    quick_test()
```

## 📞 技术支持

### 常见问题
1. **API限制**: Open-Meteo免费版有调用限制，建议添加缓存
2. **数据精度**: 历史数据使用ERA5再分析数据，精度较高
3. **城市支持**: 支持全球城市，可动态搜索添加

### 获取帮助
- 查看完整文档: `docs/open_meteo_guide.md`
- 运行示例代码: `python src/core/open_meteo_api.py`
- 检查配置: `python system_check.py`

---

**🎉 恭喜！您现在可以使用高精度的Open-Meteo天气数据来增强您的天气建模分析了！**