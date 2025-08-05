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
    return config["deepseek-v3"]

deepseek_config = load_deepseek_config()

def extract_mutant_info(mutant_json_path, mutant_number):
    """从变异体JSON文件中提取指定变异体编号的信息"""
    with open(mutant_json_path, 'r', encoding='utf-8') as f:
        mutants = json.load(f)

    # 构造完整的变异体ID，如"MUT_001"
    target_id = f"MUT_{mutant_number.zfill(3)}"

    for mutant in mutants:
        if mutant['mutant_id'] == target_id:
            return mutant

    return None


def extract_cfg_info(cfg_json_path):
    """从CFG JSON文件中提取信息"""
    with open(cfg_json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_reachability_path(llm, cfg_info, mutant_info):
    """使用LLM提取可达性路径条件组合"""
    template = """根据提供的控制流图信息和变异体信息，严格按照以下要求提取程序入口到变异点的可达路径条件组合：
1. 提取范围：
   - 从程序入口开始
   - 到变异点结束，不要扩展无关分支
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

    #chain = LLMChain(llm=llm, prompt=prompt)
    #result = chain.run(cfg_info=json.dumps(cfg_info, indent=2),
                       #mutant_info=json.dumps(mutant_info, indent=2))
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



'''
def main():
    # 初始化LLM
    llm = ChatOpenAI(
        openai_api_key=deepseek_config["api_key"],
        model="deepseek-chat",
        temperature=0,
        openai_api_base=deepseek_config["base_url"],
    )

    # 示例路径
    cfg_path = r"D:\bishe_code\progex_benchmark\mutant_programs\Insert\mutants\mutant_001\outdir\Insert-CFG.json"
    mutant_json_path = r"D:\bishe_code\progex_benchmark\mutantbench\mutantjava\mutantsIDJson\Insertmutants.json"

    # 从CFG路径中提取变异体编号
    mutant_number = os.path.basename(os.path.dirname(os.path.dirname(cfg_path))).split('_')[-1]

    # 提取信息
    mutant_info = extract_mutant_info(mutant_json_path, mutant_number)
    cfg_info = extract_cfg_info(cfg_path)

    if not mutant_info:
        print(f"未找到变异体 MUT_{mutant_number.zfill(3)} 的信息")
        return

    # 提取可达性路径条件组合
    reachability_path = extract_reachability_path(llm, cfg_info, mutant_info)

    print("可达性路径条件组合:")
    print(reachability_path)


if __name__ == "__main__":
    main()
'''


def get_reachability_path():
    """直接返回变异体的可达性路径条件组合"""
    # 初始化LLM
    llm = ChatOpenAI(
        openai_api_key=deepseek_config["api_key"],
        model="deepseek-chat",
        temperature=0,
        openai_api_base=deepseek_config["base_url"],
    )

    # 示例路径
    cfg_path = r"D:\bishe_code\progex_benchmark\mutant_programs\Insert\mutants\mutant_001\outdir\Insert-CFG.json"
    mutant_json_path = r"D:\bishe_code\progex_benchmark\mutantbench\mutantjava\mutantsIDJson\Insertmutants.json"

    # 从CFG路径中提取变异体编号
    mutant_number = os.path.basename(os.path.dirname(os.path.dirname(cfg_path))).split('_')[-1]

    # 提取信息
    mutant_info = extract_mutant_info(mutant_json_path, mutant_number)
    cfg_info = extract_cfg_info(cfg_path)

    if not mutant_info:
        print(f"未找到变异体 MUT_{mutant_number.zfill(3)} 的信息")
        return

    # 返回可达性路径
    result = extract_reachability_path(llm, cfg_info, mutant_info)
    return f"可达性路径条件组合: {result}"
