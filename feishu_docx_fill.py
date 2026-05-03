"""飞书文档内容填充工具 — 往已创建的 wiki docx 写入 markdown 内容"""

import json, os, sys, time, requests, re

def get_user_token():
    token_file = os.path.expanduser("~/.claude/feishu_tokens.json")
    if os.path.exists(token_file):
        with open(token_file) as f:
            return json.load(f)["token"]
    return None

def get_app_token():
    settings = json.load(open(os.path.expanduser("~/.claude/settings.json")))
    env = settings.get("env", {})
    resp = requests.post("https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal",
        json={"app_id": env["FEISHU_APP_ID"], "app_secret": env["FEISHU_APP_SECRET"]},
        headers={"Content-Type": "application/json"}, timeout=10)
    return resp.json().get("app_access_token", "")

def rename_doc(doc_token, title, token):
    resp = requests.patch(
        f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}",
        json={"title": title},
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, timeout=10)
    return resp.json().get("code") == 0

def delete_all_children(doc_token, page_token, user_token):
    """清空页面初始空白块"""
    resp = requests.get(
        f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{page_token}/children",
        headers={"Authorization": f"Bearer {user_token}"}, timeout=10)
    children = resp.json().get("data", {}).get("items", [])
    for child in children:
        if child["block_id"] != page_token:
            requests.delete(
                f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{child['block_id']}",
                headers={"Authorization": f"Bearer {user_token}"}, timeout=10)

def parse_markdown_to_blocks(md):
    """将 markdown 转为飞书 docx block 列表 (简化版, 支持标题/正文/表格/列表)"""
    blocks = []
    lines = md.strip().split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 跳过空行
        if not line.strip():
            i += 1
            continue
        
        # H1
        if line.startswith("# ") and not line.startswith("## "):
            blocks.append(make_heading(3, line[2:]))
            i += 1
            continue
        
        # H2
        if line.startswith("## "):
            blocks.append(make_heading(4, line[3:]))
            i += 1
            continue
        
        # H3
        if line.startswith("### "):
            blocks.append(make_heading(5, line[4:]))
            i += 1
            continue
        
        # 表格
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            if len(table_lines) >= 2:
                blocks.append(make_table(table_lines))
            continue
        
        # 无序列表
        if line.strip().startswith("- "):
            list_items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                list_items.append(lines[i].strip()[2:])
                i += 1
            for item in list_items:
                blocks.append(make_bullet(item))
            continue
        
        # 分割线
        if line.strip() == "---":
            blocks.append({"block_type": 19})  # divider
            i += 1
            continue
        
        # 普通文本
        blocks.append(make_text(line.strip()))
        i += 1
    
    return blocks

def make_heading(level, text):
    return {"block_type": level, f"heading{level-2}": make_elements(text)}

def make_text(text):
    return {"block_type": 2, "text": make_elements(text)}

def make_bullet(text):
    return {"block_type": 9, "bullet": make_elements(text)}

def make_elements(text):
    return {"elements": [{"text_run": {"content": text}}]}

def make_table(lines):
    """解析 markdown 表格为飞书 table block"""
    rows = []
    for line in lines:
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(c.replace("-","").replace(":","").strip() == "" for c in cells):
            continue
        rows.append(cells)
    
    if not rows:
        return make_text("(空表格)")
    
    property = {"row_size": len(rows), "column_size": len(rows[0])}
    return {"block_type": 31, "table": {
        "property": property,
        "cells": [[c for c in row] for row in rows]
    }}

def fill_document(doc_token, title, markdown):
    """主函数: 往 wiki docx 写入内容"""
    user_token = get_user_token()
    if not user_token:
        print("ERROR: no user token")
        return False
    
    # 1. 重命名
    rename_doc(doc_token, title, user_token)
    
    # 2. 清空默认空白块
    delete_all_children(doc_token, doc_token, user_token)
    
    # 3. 解析 markdown 为 blocks
    blocks = parse_markdown_to_blocks(markdown)
    
    # 4. 分批写入 (飞书限制每次最多 50 个 block)
    BATCH = 40
    for batch_start in range(0, len(blocks), BATCH):
        batch = blocks[batch_start:batch_start + BATCH]
        resp = requests.post(
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_token}/blocks/{doc_token}/children",
            json={"children": batch, "index": -1},
            headers={"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"},
            timeout=30)
        if resp.json().get("code") != 0:
            print(f"ERROR at batch {batch_start}: {resp.json().get('msg','')}")
            return False
    
    print(f"OK: wrote {len(blocks)} blocks to {doc_token}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python feishu_docx_fill.py <doc_token> <title> [markdown_file]")
        print("  Reads markdown from file or stdin")
        sys.exit(1)
    
    doc_token = sys.argv[1]
    title = sys.argv[2]
    
    if len(sys.argv) >= 4:
        with open(sys.argv[3], 'r', encoding='utf-8') as f:
            markdown = f.read()
    else:
        markdown = sys.stdin.read()
    
    fill_document(doc_token, title, markdown)
