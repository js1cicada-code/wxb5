#!/bin/bash

echo "=== 比分直播爬虫安装脚本 ==="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python3"
    exit 1
fi

echo "Python版本:"
python3 --version
echo ""

# 安装Selenium
echo "正在安装 Selenium..."
pip3 install selenium --user

# 尝试安装webdriver-manager
echo ""
echo "正在安装 webdriver-manager (自动管理ChromeDriver)..."
pip3 install webdriver-manager --user 2>/dev/null || echo "webdriver-manager 安装失败，请手动配置ChromeDriver"

# 检查Chrome
echo ""
if command -v google-chrome &> /dev/null; then
    echo "Chrome已安装"
    google-chrome --version
elif command -v "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" &> /dev/null; then
    echo "Chrome已安装 (macOS)"
elif [ -d "/Applications/Google Chrome.app" ]; then
    echo "Chrome已安装 (macOS)"
else
    echo "警告: 未检测到Chrome浏览器，请确保已安装Chrome"
fi

# 检查ChromeDriver
echo ""
if command -v chromedriver &> /dev/null; then
    echo "ChromeDriver已安装:"
    chromedriver --version
else
    echo "ChromeDriver未安装"
    echo ""
    echo "=== 安装ChromeDriver ==="
    echo ""
    echo "macOS用户:"
    echo "  brew install chromedriver"
    echo ""
    echo "或者手动下载:"
    echo "  1. 查看Chrome版本: chrome://settings/help"
    echo "  2. 下载对应版本: https://chromedriver.chromium.org/downloads"
    echo "  3. 将chromedriver放到PATH中或项目目录"
    echo ""
fi

# 验证安装
echo ""
echo "=== 验证安装 ==="
python3 -c "
try:
    import selenium
    print(f'✓ Selenium {selenium.__version__} 安装成功')
except ImportError:
    print('✗ Selenium 安装失败')

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    options = Options()
    options.add_argument('--headless')
    print('✓ 可以创建Chrome WebDriver')
except Exception as e:
    print(f'✗ WebDriver配置有问题: {e}')
"

echo ""
echo "=== 安装完成 ==="
echo ""
echo "运行爬虫:"
echo "  python3 live_selenium_crawler.py"