import re
from typing import List

# --- 配置 ---
INPUT_RULES_FILE = "autoproxy.txt"
INPUT_TEMPLATE_FILE = "quanx_template.conf"
OUTPUT_CONFIG_FILE = "quanx.conf"
PLACEHOLDER = "## AUTOPROXY_RULES_PLACEHOLDER ##"

# --- QX 策略名称 (根据您的模板配置修改) ---
PROXY_POLICY = "proxy"   # 走代理的策略名称
DIRECT_POLICY = "direct" # 直连的策略名称

def read_rules(file_path: str) -> List[str]:
    """读取本地 AutoProxy 规则文件"""
    print(f"-> 正在读取规则文件: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().splitlines()
    except FileNotFoundError:
        print(f"错误：未找到文件 {file_path}，请创建该文件。")
        return []

def convert_autoproxy_to_quanx(rules: List[str]) -> str:
    """将 AutoProxy 规则转换为 Quantumult X (QX) 规则片段"""
    
    quanx_rules = []
    
    for rule in rules:
        rule = rule.strip()
        
        # 忽略空行、注释、标题
        if not rule or rule.startswith('!') or rule.startswith('['):
            continue

        # 1. 白名单 (@@) -> DIRECT 策略
        if rule.startswith('@@'):
            # 去掉 @@ 和前缀 || 或 |
            clean_rule = rule[2:].lstrip('|').lstrip('.')
            policy = DIRECT_POLICY
        
        # 2. 黑名单 (默认) -> PROXY 策略
        else:
            # 清理前缀 || 或 |
            clean_rule = rule.lstrip('|').lstrip('.')
            policy = PROXY_POLICY

        # 移除 URL 路径，只保留域名部分（如果包含 / 且不是 CIDR 格式）
        # 检查是否是 IP CIDR 格式 (如 192.168.0.0/16 或 /91.108.56.0/24)
        print(f"转换规则: {rule} -> {clean_rule} 使用策略: {policy}")
        
        # 修改正则表达式以支持以斜杠开头的CIDR格式
        cidr_pattern = r'(?:^|\/)(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\/\d{1,2})'
        cidr_match = re.search(cidr_pattern, clean_rule)
        
        if cidr_match:
            # 提取IP CIDR规则
            ip_cidr_rule = cidr_match.group(1)
            print(f"识别为 IP-CIDR 规则: {ip_cidr_rule}")
            # 添加 IP-CIDR 类型规则
            quanx_rules.append(f"IP-CIDR, {ip_cidr_rule}, {policy}")
        else:
            print(f"识别为 普通域名 规则: {clean_rule}")
            # 普通域名规则，移除 URL 路径部分
            if '/' in clean_rule:
                domain_rule = clean_rule.split('/')[0]
            else:
                domain_rule = clean_rule

            # 简单校验并格式化为 HOST-SUFFIX 规则
            # 使用 HOST-SUFFIX 匹配域名及其子域名
            if domain_rule and re.match(r'^[a-zA-Z0-9.-]+$', domain_rule):
                quanx_rules.append(f"HOST-SUFFIX, {domain_rule}, {policy}")
        
    # 转换为 Quantumult X 格式的注释，提高可读性
    return "\n".join(f"# {r}" if r.startswith('#') else r for r in quanx_rules)

def insert_rules_into_template(template_path: str, rules_snippet: str) -> str:
    """读取模板文件，并用转换后的规则替换占位符"""
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
            
        if PLACEHOLDER not in template_content:
            print(f"警告：模板中未找到占位符 '{PLACEHOLDER}'。规则将追加到文件末尾。")
            return template_content + "\n" + rules_snippet
            
        # 替换占位符
        return template_content.replace(PLACEHOLDER, rules_snippet)
        
    except FileNotFoundError:
        print(f"错误：未找到模板文件 {template_path}。")
        return ""

if __name__ == "__main__":
    
    # 1. 读取 AutoProxy 规则
    autoproxy_rules = read_rules(INPUT_RULES_FILE)
    if not autoproxy_rules:
        exit()
        
    # 2. 转换规则为 QX 片段
    quanx_snippet = convert_autoproxy_to_quanx(autoproxy_rules)
    
    # 3. 插入到 QX 模板中
    final_config = insert_rules_into_template(INPUT_TEMPLATE_FILE, quanx_snippet)
    
    if final_config:
        # 4. 保存最终的 QX 配置文件
        with open(OUTPUT_CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(final_config)
            
        print("-" * 50)
        print(f"✅ 转换完成！Quantumult X 配置文件已保存到：{OUTPUT_CONFIG_FILE}")
        print(f"已转换的规则条数 (估算)：{len(quanx_snippet.splitlines())}")