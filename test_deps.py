import sys
print("Python version:", sys.version)

try:
    import aiogram
    print("✅ aiogram импортирован, версия:", aiogram.__version__)
except ImportError as e:
    print("❌ aiogram НЕ импортирован:", e)
    
try:
    import aiohttp
    print("✅ aiohttp импортирован")
except ImportError:
    print("❌ aiohttp НЕ импортирован")
