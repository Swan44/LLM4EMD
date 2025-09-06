from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import json
import re
import os
import yaml
from src.extract_mutation_info import extract_mutation_info


def load_deepseek_config(config_path="/Users/swan/bishe/LLM4EMD/configs/llm_configs.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    # return config["deepseek-v3-g"]
    return config["deepseek-v3"]
    # return config["deepseek-v3"]

deepseek_config = load_deepseek_config()

def load_gpt_config(config_path="/Users/swan/bishe/LLM4EMD/configs/llm_configs.yaml"):
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
    template = """
根据提供的控制流图信息和变异体信息，严格按照以下要求提取程序入口到变异节点之前(即执行到变异点但尚未执行变异语句)的可达路径条件组合：
## 注意：可达性路径条件的含义是变异点能否被执行到，而非变异语句条件是否可以满足，所以只需考虑变异点之前的条件能否满足
1. 提取步骤：
   - 首先严格停止在变异语句的【前一条语句执行后】，忽略变异节点与其后的所有节点的控制流信息
   - 之后，提取程序入口开始到变异点位置之前的路径条件组合，无需考虑变异语句本身条件
   - 若无条件，则直接输出NULL
2. 输出格式要求：
   可达性路径条件组合:[路径条件组合]
## 注意：只包含变异点之前语句的条件，排除变异语句本身及之后语句的条件。
控制流图信息:
{cfg_info}
变异体信息:
{mutant_info}
"""

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

    # 提取响应内容
    response_text = response.content if hasattr(response, 'content') else str(response)

    # 正则匹配
    match = re.search(r"可达性路径条件组合:\s*(.*)", response_text)
    return match.group(1).strip() if match else "NULL"

def get_reachability_path(program_name, mutant):
    """直接返回变异体的可达性路径条件组合"""
    # 初始化LLM
    llm = ChatOpenAI(
        api_key=deepseek_config["api_key"],
        model=deepseek_config["model"],
        temperature=0,
        base_url=deepseek_config["base_url"]
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
    base_dir = r"/Users/swan/bishe/progex_benchmark/mutant_programs"
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
    return extract_reachability_path(llm, cfg_info, extract_mutation_info(mutant))

'''
if __name__ == "__main__":
    program_name = "ArrayUtilsLastShort"  # 替换成你的目标程序名
    mutant = {
                       "mutant_id": "MUT_001",
                       "difference": "@@ -8 +8 @@\n-        } else if (startIndex >= array.length) {\n+        } else if (startIndex == array.length) {",
                       "operator": "ROR"
                   }  # 替换成你的变异体 ID

    # 调用函数
    result = get_reachability_path(program_name, mutant)
    print("最终结果:", result)
'''
