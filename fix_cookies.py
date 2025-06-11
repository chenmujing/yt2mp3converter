#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复app.py中的cookies设置，避免DPAPI错误
"""

import re

def fix_cookies():
    """修复cookies设置"""
    try:
        # 读取文件
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换cookies设置
        old_pattern = r"'cookiesfrombrowser': \('chrome',\),"
        new_replacement = "# 'cookiesfrombrowser': ('chrome',),"
        
        content = re.sub(old_pattern, new_replacement, content)
        
        # 写回文件
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Cookies设置已禁用，避免DPAPI错误")
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        return False

if __name__ == "__main__":
    fix_cookies() 