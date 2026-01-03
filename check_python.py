#!/usr/bin/env python3
"""
Проверка совместимости зависимостей
"""

import sys

print(f"Python version: {sys.version}")
print(f"Python version info: {sys.version_info}")

# Проверяем что Python 3.10-3.11
if sys.version_info.major == 3 and sys.version_info.minor >= 10 and sys.version_info.minor <= 11:
    print("✅ Python version compatible with aiogram")
else:
    print(f"⚠️  Warning: Python {sys.version_info.major}.{sys.version_info.minor} may have issues")
    print("Recommended: Python 3.10.x or 3.11.x")
