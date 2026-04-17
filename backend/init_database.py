#!/usr/bin/env python3
"""
MeowHealth 数据库初始化脚本
运行: python init_database.py
"""

import sys
import os

# 添加 backend 目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_db


def main():
    print("🐱 MeowHealth Database Initialization")
    print("=" * 40)
    
    try:
        init_db()
        print("\n✅ All tables created successfully!")
        print("\nCreated tables:")
        print("  - cats (猫咪主档案)")
        print("  - health_records (健康记录流水)")
        print("  - health_indicators (健康指标明细)")
        print("  - report_attachments (报告附件)")
        print("  - weight_logs (体重记录)")
        print("  - feeding_logs (喂食记录)")
        print("  - reminders (提醒/待办事项)")
        print("  - ai_chat_messages (AI 对话上下文)")
        print("  - cat_foods (猫粮数据库)")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
