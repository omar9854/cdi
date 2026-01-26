#!/bin/bash
#================================================================
# سكربت التثبيت السريع بأمر واحد
# One-Line Installation Script for Nabeeh
#
# الاستخدام على خادمك:
# curl -fsSL https://raw.githubusercontent.com/omar9854/clinical-doc-ai-tool/main/INSTALL_GPU_SERVER.sh | sudo bash
#
# أو:
# wget -qO- https://raw.githubusercontent.com/omar9854/clinical-doc-ai-tool/main/INSTALL_GPU_SERVER.sh | sudo bash
#================================================================

set -e

echo "=========================================="
echo "   🏥 التثبيت السريع لنظام نبيه"
echo "=========================================="

# تحميل وتشغيل السكربت الكامل
curl -fsSL https://raw.githubusercontent.com/omar9854/clinical-doc-ai-tool/main/INSTALL_GPU_SERVER.sh -o /tmp/install_nabeeh.sh
chmod +x /tmp/install_nabeeh.sh
sudo /tmp/install_nabeeh.sh
