# ===== СОХРАНЕНИЕ ВСЕЙ ЛОГИКИ МОНОПОЛИИ =====
# Выполните эту команду, чтобы получить все функции для восстановления

Write-Host "🎮 СОХРАНЕНИЕ ЛОГИКИ MONOPOLY BOT" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Gray

# 1. Проверяем структуру проекта
$projectFiles = Get-ChildItem -Recurse -File -Include "*.py" | 
    Select-Object -ExpandProperty FullName

Write-Host "📁 Найдено файлов: $($projectFiles.Count)" -ForegroundColor Green

# 2. Собираем ВСЕ функции из всех файлов
$allFunctions = @{}
$allClasses = @{}
$allImports = @{}

foreach ($file in $projectFiles) {
    Write-Host "`n📄 Анализ: $(Split-Path $file -Leaf)" -ForegroundColor Yellow
    
    $content = Get-Content $file -Raw
    
    # Ищем функции
    $functionMatches = [regex]::Matches($content, '(?:async\s+)?def\s+(\w+)\s*\([^)]*\)\s*(?:->[^:]+)?:')
    foreach ($match in $functionMatches) {
        $funcName = $match.Groups[1].Value
        $allFunctions[$funcName] = $file
        Write-Host "  📌 Функция: $funcName" -ForegroundColor Gray
    }
    
    # Ищем классы
    $classMatches = [regex]::Matches($content, 'class\s+(\w+)\s*(?:\([^)]*\))?:')
    foreach ($match in $classMatches) {
        $className = $match.Groups[1].Value
        $allClasses[$className] = $file
        Write-Host "  🏛️  Класс: $className" -ForegroundColor Gray
    }
    
    # Ищем импорты (логика игры)
    $importMatches = [regex]::Matches($content, 'import\s+([^\n]+)|\s+from\s+(\w+)\s+import')
    foreach ($match in $importMatches) {
        $import = if ($match.Groups[1].Value) { $match.Groups[1].Value } else { $match.Groups[2].Value }
        $allImports[$import] = $file
    }
}

# 3. Сохраняем структуру в файл
$savePath = "monopoly_logic_backup.txt"
Write-Host "`n💾 Сохраняю логику в файл: $savePath" -ForegroundColor Cyan

$backupContent = @"
==================================================
🎲 ПОЛНАЯ ЛОГИКА МОНОПОЛИИ BOT
==================================================
Дата сохранения: $(Get-Date)
Всего файлов: $($projectFiles.Count)
Всего функций: $($allFunctions.Count)
Всего классов: $($allClasses.Count)

==================================================
📁 СТРУКТУРА ПРОЕКТА:
==================================================
$((Get-ChildItem -Recurse | ForEach-Object {
    $depth = ($_.FullName.Split([IO.Path]::DirectorySeparatorChar)).Count - ($PWD.Path.Split([IO.Path]::DirectorySeparatorChar)).Count
    ("    " * $depth) + $(if ($_.PSIsContainer) {"📁"} else {"📄"}) + " " + $_.Name
}) -join "`n")

==================================================
🔧 ФУНКЦИИ ИГРЫ ($($allFunctions.Count)):
==================================================
$($allFunctions.Keys | Sort-Object | ForEach-Object {
    "• $_ (в $(Split-Path $allFunctions[$_] -Leaf))"
} -join "`n")

==================================================
🏛️  КЛАССЫ ИГРЫ ($($allClasses.Count)):
==================================================
$($allClasses.Keys | Sort-Object | ForEach-Object {
    "• $_ (в $(Split-Path $allClasses[$_] -Leaf))"
} -join "`n")

==================================================
🎮 МЕХАНИКИ ИГРЫ (из data/ файлов):
==================================================
"@

# 4. Сохраняем игровые данные
if (Test-Path "data\board.json") {
    $boardData = Get-Content "data\board.json" -Raw | ConvertFrom-Json
    $backupContent += "`n🎯 ИГРОВОЕ ПОЛЕ ($($boardData.Count) клеток):`n"
    foreach ($cell in $boardData) {
        $backupContent += "• $($cell.name) - $($cell.type) - Цена: $$($cell.price)`n"
    }
}

if (Test-Path "data\chance-cards.json") {
    $cards = Get-Content "data\chance-cards.json" -Raw | ConvertFrom-Json
    $backupContent += "`n🎲 КАРТОЧКИ ШАНСА ($($cards.Count) карт):`n"
    foreach ($card in $cards) {
        $backupContent += "• $($card.description)`n"
    }
}

# 5. Сохраняем обработчики команд
$backupContent += @"

==================================================
🤖 ОБРАБОТЧИКИ КОМАНД:
==================================================
"@

foreach ($file in @("handlers/commands.py", "handlers/game_handlers.py", "handlers/callback_handlers.py")) {
    if (Test-Path $file) {
        $backupContent += "`n📄 $(Split-Path $file -Leaf):`n"
        $content = Get-Content $file | Select-String -Pattern 'def\s+\w+|async\s+def\s+\w+' | ForEach-Object {
            "  - $($_.Line.Trim())"
        }
        $backupContent += $content -join "`n"
    }
}

$backupContent | Out-File -FilePath $savePath -Encoding UTF8

Write-Host "✅ Логика сохранена в файл: $savePath" -ForegroundColor Green
Write-Host "📊 Статистика сохранения:" -ForegroundColor Cyan
Write-Host "• Файлы проекта: $($projectFiles.Count)" -ForegroundColor Gray
Write-Host "• Функции: $($allFunctions.Count)" -ForegroundColor Gray
Write-Host "• Классы: $($allClasses.Count)" -ForegroundColor Gray
Write-Host "`n📋 Теперь отправьте мне содержимое файла $savePath" -ForegroundColor Yellow
Write-Host "Я восстановлю ВСЮ логику на новой библиотеке!" -ForegroundColor Green
