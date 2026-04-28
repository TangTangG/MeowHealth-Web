import json
import re
from typing import Dict, Any, List, Union

def clean_and_parse_json(text: str) -> Union[Dict[str, Any], List[Any]]:
    """鲁棒的 JSON 提取工具，自动剔除 Markdown 块和多余文本"""
    if not text:
        raise ValueError("输入文本为空")
        
    # 移除 markdown 的 ```json 和 ``` 标记
    text = re.sub(r'```(?:json)?\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    
    # 尝试直接解析
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass
        
    # 提取最外层的括号 {} 或 []
    # 通过统计括号层级来找到匹配的最外层
    start_idx = -1
    for i, char in enumerate(text):
        if char in ('{', '['):
            start_idx = i
            break
            
    if start_idx == -1:
        raise ValueError("未找到任何 JSON 起始符号")
        
    end_char = '}' if text[start_idx] == '{' else ']'
    end_idx = text.rfind(end_char)
    
    if end_idx == -1 or end_idx < start_idx:
        raise ValueError("未找到闭合的 JSON 符号")
        
    json_str = text[start_idx:end_idx + 1]
    return json.loads(json_str)