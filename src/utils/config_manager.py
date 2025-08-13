#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理器 - Configuration Manager
管理应用程序的所有配置设置
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """配置管理器类 - Configuration manager class"""
    
    def __init__(self, config_dir: str = "../config"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录路径
        """
        self.config_dir = Path(config_dir)
        self.config_file = self.config_dir / "app_config.json"
        self.default_config = self._get_default_config()
        self.config = {}
        
        # 确保配置目录存在
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载配置
        self.load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "app": {
                "name": "天气数据建模分析软件",
                "version": "1.0.0",
                "theme": "light",
                "language": "zh_CN",
                "auto_save": True,
                "auto_backup": True
            },
            "paths": {
                "data_dir": "../data",
                "raw_data_dir": "../data/raw",
                "processed_data_dir": "../data/processed",
                "models_dir": "../data/models",
                "logs_dir": "../logs",
                "backup_dir": "../backups"
            },
            "weather_api": {
                "provider": "openweathermap",
                "api_key": "",
                "base_url": "https://api.openweathermap.org/data/2.5",
                "timeout": 30,
                "retry_count": 3
            },
            "modeling": {
                "tbats": {
                    "use_trend": True,
                    "use_damped_trend": False,
                    "use_arma_errors": True,
                    "seasonal_periods": [7, 365],
                    "confidence_level": 0.95
                },
                "random_forest": {
                    "n_estimators": 100,
                    "max_depth": 10,
                    "min_samples_split": 2,
                    "min_samples_leaf": 1,
                    "random_state": 42
                }
            },
            "data_processing": {
                "date_format": "%Y-%m-%d",
                "time_format": "%H:%M:%S",
                "missing_value_strategy": "interpolate",
                "outlier_threshold": 3.0,
                "smoothing_window": 7
            },
            "anomaly_detection": {
                "enabled": True,
                "sensitivity": "medium",
                "top_customers_count": 20,
                "comparison_periods": ["daily", "weekly"],
                "alert_threshold": 2.0
            },
            "regions": {
                "广东": {
                    "cities": ["广州", "深圳", "东莞", "佛山", "中山", "珠海", "惠州", "江门", "肇庆", "汕头"],
                    "timezone": "Asia/Shanghai"
                },
                "default": {
                    "timezone": "Asia/Shanghai"
                }
            }
        }
    
    def load_config(self) -> None:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和用户配置
                    self.config = self._merge_configs(self.default_config, loaded_config)
            else:
                # 使用默认配置
                self.config = self.default_config.copy()
                self.save_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.config = self.default_config.copy()
    
    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """合并默认配置和用户配置"""
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key_path: 配置的键路径，用点号分隔，如"app.name"
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """
        设置配置值
        
        Args:
            key_path: 配置的键路径
            value: 要设置的值
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        self.save_config()
    
    def get_weather_api_key(self) -> str:
        """获取天气API密钥"""
        return self.get('weather_api.api_key', '')
    
    def set_weather_api_key(self, api_key: str) -> None:
        """设置天气API密钥"""
        self.set('weather_api.api_key', api_key)
    
    def get_data_directory(self) -> Path:
        """获取数据目录路径"""
        data_dir = self.get('paths.data_dir', '../data')
        return Path(data_dir).resolve()
    
    def get_models_directory(self) -> Path:
        """获取模型目录路径"""
        models_dir = self.get('paths.models_dir', '../data/models')
        return Path(models_dir).resolve()
    
    def get_tbats_config(self) -> Dict[str, Any]:
        """获取TBATS配置"""
        return self.get('modeling.tbats', {})
    
    def get_random_forest_config(self) -> Dict[str, Any]:
        """获取随机森林配置"""
        return self.get('modeling.random_forest', {})
    
    def get_regions(self) -> Dict[str, Any]:
        """获取地区配置"""
        return self.get('regions', {})
    
    def add_region(self, region_name: str, cities: list, timezone: str = "Asia/Shanghai") -> None:
        """添加新地区"""
        regions = self.get('regions', {})
        regions[region_name] = {
            'cities': cities,
            'timezone': timezone
        }
        self.set('regions', regions)
    
    def validate_config(self) -> bool:
        """验证配置有效性"""
        required_keys = [
            'weather_api.api_key',
            'paths.data_dir',
            'paths.models_dir'
        ]
        
        for key in required_keys:
            value = self.get(key)
            if not value:
                return False
        
        return True