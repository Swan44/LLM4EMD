from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import json
import re
import os
import yaml

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

def extract_data_info(data_json_path):
    """从PDG DATA JSON文件中提取信息"""
    with open(data_json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_data_path(llm, data_info, mutant_info):
    """使用LLM提取数据依赖信息"""
    template = """根据提供的PDG数据依赖图和变异体信息，首先分析变异影响的变量，再严格按照以下要求提取变量的数据依赖路径：
1. 提取范围：
   - 从变异语句开始
   - 到程序输出语句结束，不要扩展无关分支
   - 若无到输出的数据依赖，则提取到终止节点的完整路径
2. 输出格式要求：
   [变量名] 的数据依赖路径:
   [路径编号]. [路径链]
   其中：
   - 语句必须包含原始代码和行号
3. 示例格式：
变异影响的变量为：a
   变量a的数据依赖路径:
   1. (line 16: if (a >= c)) → if True: (line 16) --[Control True]--> (line 17: mid = c) --[Flows mid]--> (line 25: return mid)→ if False: (line 16) --[Control False]--> (line 19: mid = a) --[Flows mid]--> (line 25: return mid)
4. 特殊处理：
   - 对复合条件语句，需展开所有可能路径
   - 对循环依赖，标注循环起点和终点
   - 对并行路径，分别独立列出
5. 最终输出：
   - 按变量分组
   - 每条路径独立编号
   - 只输出依赖路径信息即可，无需做路径说明

数据依赖信息:
{data_info}

变异体信息:
{mutant_info}
"""

    prompt = PromptTemplate(
        input_variables=["data_info", "mutant_info"],
        template=template
    )

    # 使用新的 Runnable 语法
    chain = (
            {"data_info": RunnablePassthrough(), "mutant_info": RunnablePassthrough()}
            | prompt
            | llm
    )

    # 获取 AI 响应对象
    response = chain.invoke({
        "data_info": json.dumps(data_info, indent=2),
        "mutant_info": json.dumps(mutant_info, indent=2)
    })

    return response.content if hasattr(response, 'content') else str(response)


def get_data_info(program_name, mutant):
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
    # mutants_dir = r"D:\bishe_code\progex_benchmark\mutant_programs\Min\mutants"
    # base_dir = r"D:\bishe_code\progex_benchmark\mutant_programs"
    base_dir = r"/Users/swan/bishe/progex_benchmark/mutant_programs"
    mutants_dir = os.path.join(base_dir, program_name, "mutants")

    mutant_id = mutant.get("mutant_id")  # 例如 "MUT_001"

    # 从MUT_001提取数字部分
    mutant_number = mutant_id.split('_')[-1].zfill(3)
    mutant_dir = f"mutant_{mutant_number}"

    # 构建data路径
    data_path = os.path.join(mutants_dir, mutant_dir, "outdir", f"{program_name}-PDG-DATA.json")

    # 提取信息
    data_info = extract_data_info(data_path)

    # 返回数据依赖路径
    result = extract_data_path(llm, data_info, mutant)
    return result

'''
if __name__ == "__main__":
    program_name = "Triangle"  # 替换成你的目标程序名
    mutant = {"mutant_id": "MUT_001"}  # 替换成你的变异体 ID

    # 调用函数
    result = get_data_info(program_name, mutant)
    print("最终结果:", result)
'''