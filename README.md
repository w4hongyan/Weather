# 🌤️ 天气数据建模与分析系统

## 🎯 项目概述

这是一个功能强大的桌面级天气数据建模与分析系统，集成Open-Meteo API提供全球高精度天气数据，支持多种预测算法和异常检测技术。

### ✨ 核心特性
- **🌐 Open-Meteo集成**: 全球高精度天气数据（历史+预报）
- **🤖 多算法预测**: TBATS、Prophet、ARIMA、LSTM
- **🔍 智能异常检测**: IQR、Z-score、机器学习检测
- **🎨 现代化UI**: qt-material主题，实时性能监控
- **📊 智能数据管理**: Excel/CSV支持，自动验证处理

## 🚀 快速开始

### ⚡ 30秒体验
```bash
# 一键启动演示
python demo_app.py

# 快速查询天气
python -c "
from src.core.open_meteo_api import OpenMeteoAPI
from utils.config_manager import ConfigManager
api = OpenMeteoAPI(ConfigManager())
data = api.get_forecast_weather('广州', days=3)
print(data[['date','max_temperature','min_temperature']])
"
```

### 📥 安装
```bash
# 1. 克隆项目
git clone [项目地址]
cd weather_analysis

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动应用
python run_app.py
```

## 🌡️ Open-Meteo API使用指南

### 🔍 基础使用
```python
from src.core.open_meteo_api import OpenMeteoAPI
from utils.config_manager import ConfigManager

# 初始化
api = OpenMeteoAPI(ConfigManager())

# 城市搜索
city = api.search_city("广州")
# {'name': '广州', 'lat': 23.12, 'lon': 113.25, 'timezone': 'Asia/Shanghai'}

# 获取天气数据
history = api.get_historical_weather("广州", days=7)
forecast = api.get_forecast_weather("广州", days=7)
combined = api.get_enhanced_weather_data("广州", days=14)
```

### 📊 数据格式
```
        date  max_temperature  min_temperature  precipitation
2025-08-11             33.1             26.3            2.3
2025-08-12             32.8             26.2            0.9
```

### 🎯 API方法
| 方法 | 说明 | 示例 |
|------|------|------|
| `search_city()` | 城市搜索 | `api.search_city("北京")` |
| `get_historical_weather()` | 历史天气 | `api.get_historical_weather("上海", days=7)` |
| `get_forecast_weather()` | 天气预报 | `api.get_forecast_weather("深圳", days=7)` |
| `get_enhanced_weather_data()` | 增强数据 | `api.get_enhanced_weather_data("杭州", days=14)` |

## 🛠️ 开发集成

### 批量城市分析
```python
cities = ["北京", "上海", "广州", "深圳"]
api = OpenMeteoAPI(ConfigManager())

for city in cities:
    data = api.get_enhanced_weather_data(city, days=7)
    avg_temp = data['max_temperature'].mean()
    print(f"{city}: {avg_temp:.1f}°C")
```

### 温度趋势分析
```python
data = api.get_historical_weather("广州", days=30)
print(f"30天最高温度: {data['max_temperature'].max():.1f}°C")
print(f"平均降水: {data['precipitation'].mean():.1f}mm")
```

## 📁 项目结构
```
weather_analysis/
├── src/
│   ├── core/
│   │   ├── open_meteo_api.py      # Open-Meteo API集成
│   │   ├── tbats_model.py         # TBATS预测算法
│   │   ├── anomaly_detector.py    # 异常检测
│   │   └── weather_manager.py     # 天气管理
│   ├── gui/
│   │   └── main_window.py         # 用户界面
│   └── utils/
│       ├── config_manager.py      # 配置管理
│       └── logger.py             # 日志系统
├── demo_app.py                   # 演示应用
├── simple_test.py               # 集成测试
├── debug_api.py                 # API调试
└── requirements.txt             # 依赖清单
```

## 🧪 测试验证

### 基础测试
```bash
# API集成测试
python simple_test.py

# 演示应用
python demo_app.py

# API调试
python debug_api.py
```

### 性能指标
- **响应时间**: < 2秒
- **数据精度**: ±0.5°C
- **覆盖范围**: 全球任意地点
- **历史数据**: 1979年至今
- **预报范围**: 1-16天

## 🔧 故障排除

### 常见问题
1. **网络超时**: 检查网络连接
2. **城市找不到**: 尝试英文名称或不同拼写
3. **数据为空**: 检查日期范围是否合理

### 调试命令
```bash
# 检查API连接
python debug_api.py

# 验证集成
python final_test.py
```

## 📋 系统要求
- **Python**: 3.8+
- **内存**: 4GB RAM (推荐8GB+)
- **网络**: 稳定互联网连接
- **系统**: Windows 10/11, macOS, Linux

## 🌐 支持城市
- **中国**: 所有城市（北京、上海、广州、深圳等）
- **国际**: 全球城市（纽约、伦敦、东京、巴黎等）
- **搜索**: 支持中英文、模糊匹配

## 📱 快速命令速查
```bash
# 城市搜索
python -c "from src.core.open_meteo_api import OpenMeteoAPI; from utils.config_manager import ConfigManager; api=OpenMeteoAPI(ConfigManager()); print(api.search_city('北京'))"

# 获取天气
python -c "from src.core.open_meteo_api import OpenMeteoAPI; from utils.config_manager import ConfigManager; api=OpenMeteoAPI(ConfigManager()); print(api.get_forecast_weather('上海', days=3))"
```

## 🤝 贡献
欢迎提交Issue和Pull Request！

---

**🚀 立即开始**: `python demo_app.py` 体验完整功能！