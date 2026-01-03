# Скрипт для запуска Monopoly Bot
param(
    [string]$EnvFile = ".env",
    [switch]$Install,
    [switch]$Test
)

Write-Host "🎮 С MONOPOLY BOT" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Gray

# роверка Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python не найден!" -ForegroundColor Red
    exit 1
}

# становка зависимостей
if ($Install) {
    Write-Host "📦 становка зависимостей..." -ForegroundColor Yellow
    if (Test-Path "config/requirements.txt") {
        python -m pip install -r config/requirements.txt
        Write-Host "✅ ависимости установлены" -ForegroundColor Green
    } else {
        Write-Host "❌ айл requirements.txt не найден" -ForegroundColor Red
    }
}

# Тестирование
if ($Test) {
    Write-Host "🧪 Тестирование импортов..." -ForegroundColor Magenta
    python -c "import telegram; import flask; print('✅ се импорты работают')"
}

# роверка .env файла
if (Test-Path $EnvFile) {
    Write-Host "✅ айл окружения найден: $EnvFile" -ForegroundColor Green
} else {
    Write-Host "⚠️  айл окружения не найден" -ForegroundColor Yellow
    Write-Host "ℹ️  Создайте .env файл на основе config/.env.example" -ForegroundColor Gray
    Write-Host "ℹ️  ли используйте: Copy-Item config/.env.example .env" -ForegroundColor Gray
}

# апуск бота
Write-Host "`n🚀 апуск бота..." -ForegroundColor Cyan
Write-Host "🌐 еб-сервер будет доступен на порту 10000" -ForegroundColor Gray
Write-Host "🤖 от начнет опрос Telegram..." -ForegroundColor Gray
Write-Host "`nля остановки нажмите Ctrl+C" -ForegroundColor Yellow

python main.py
