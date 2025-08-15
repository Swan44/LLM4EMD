from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import json
import re
import os
import yaml

def load_deepseek_config(config_path="D:\\bishe_code\LLM4EMD\configs\llm_configs.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config["deepseek-v3-g"]

deepseek_config = load_deepseek_config()

def load_gpt_config(config_path="D:\\bishe_code\LLM4EMD\configs\llm_configs.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config["gpt-3.5-turbo"]

gpt_config = load_gpt_config()

def extract_cfg_info(cfg_json_path):
    """从CFG JSON文件中提取信息"""
    with open(cfg_json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_reachability_path(llm, cfg_info, mutant_info):
    """使用LLM提取可达性路径条件组合"""
    template = """根据提供的控制流图信息和变异体信息，严格按照以下要求提取程序入口到变异点的可达路径条件组合：
1. 提取范围：
   - 从程序入口开始
   - 到变异点结束，不要扩展无关分支，注意该可达路径条件组合只包含变异语句之前的条件，不包含变异语句本身条件
   - 若无条件，则直接输出NULL
2. 输出格式要求：
   可达性路径条件组合:
   [路径条件组合]/NULL

控制流图信息:
{cfg_info}

变异体信息:
{mutant_info}

请提取可达性路径条件组合:"""

    prompt = PromptTemplate(
        input_variables=["cfg_info", "mutant_info"],
        template=template
    )

    # 使用新的 Runnable 语法
    chain = (
            {"cfg_info": RunnablePassthrough(), "mutant_info": RunnablePassthrough()}
            | prompt
            | llm
    )

    # 获取 AI 响应对象
    response = chain.invoke({
        "cfg_info": json.dumps(cfg_info, indent=2),
        "mutant_info": json.dumps(mutant_info, indent=2)
    })

    # 提取响应内容（关键修复）
    response_text = response.content if hasattr(response, 'content') else str(response)

    # 正则匹配
    match = re.search(r"可达性路径条件组合:\s*(.*)", response_text)
    return match.group(1).strip() if match else "NULL"

def get_reachability_path(program_name, mutant):
    """直接返回变异体的可达性路径条件组合"""
    # 初始化LLM
    llm = ChatOpenAI(
        openai_api_key=deepseek_config["api_key"],
        model="deepseek-chat",
        temperature=0,
        openai_api_base=deepseek_config["base_url"]
    )
    '''
    llm = ChatOpenAI(
        openai_api_key=gpt_config["api_key"],
        model="gpt-3.5-turbo",
        temperature=0,
        openai_api_base=gpt_config["base_url"]
    )
    '''

    # 示例路径
    # mutants_dir = r"D:\bishe_code\progex_benchmark\mutant_programs\Min\mutants"
    base_dir = r"D:\bishe_code\progex_benchmark\mutant_programs"
    mutants_dir = os.path.join(base_dir, program_name, "mutants")

    mutant_id = mutant.get("mutant_id")  # 例如 "MUT_001"

    # 从MUT_001提取数字部分
    mutant_number = mutant_id.split('_')[-1].zfill(3)
    mutant_dir = f"mutant_{mutant_number}"

    # 构建CFG路径
    cfg_path = os.path.join(mutants_dir, mutant_dir, "outdir", f"{program_name}-CFG.json")

    # 提取信息
    cfg_info = extract_cfg_info(cfg_path)

    # 返回可达性路径
    result = extract_reachability_path(llm, cfg_info, mutant)
    return result
