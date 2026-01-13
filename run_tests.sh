# run_tests.sh
#!/bin/bash
# Скрипт для запуска тестов

cd "$(dirname "$0")"

echo "=========================================="
echo "  SignalPro Ultra - Test Suite"
echo "=========================================="
echo ""

# Активируем виртуальное окружение
source .venv/bin/activate

# Устанавливаем test dependencies если нужно
if ! python -c "import pytest" 2>/dev/null; then
    echo "📦 Installing test dependencies..."
    pip install -r requirements_test.txt
fi

echo "🧪 Running tests..."
echo ""

# Запускаем pytest
pytest

echo ""
echo "=========================================="
echo "  Test run complete!"
echo "  Coverage report: htmlcov/index.html"
echo "=========================================="
