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


def get_data_info():
    # 初始化LLM
    llm = ChatOpenAI(
        openai_api_key=deepseek_config["api_key"],
        model="deepseek-chat",
        temperature=0,
        openai_api_base=deepseek_config["base_url"],
    )

    # 示例路径
    mutants_dir = r"D:\bishe_code\progex_benchmark\mutant_programs\Min\mutants"
    # data_path = r"D:\bishe_code\progex_benchmark\mutant_programs\Insert\mutants\mutant_001\outdir\Insert-PDG-DATA.json"
    mutant_json_path = r"D:\bishe_code\progex_benchmark\mutantbench\mutantjava\mutantsDelJson\Minmutants.json"

    # 读取变异体JSON文件获取所有变异体ID
    with open(mutant_json_path, 'r') as f:
        mutants_data = json.load(f)

    # 遍历每个变异体
    # results = []
    for mutant in mutants_data:
        mutant_id = mutant.get("mutant_id")  # 例如 "MUT_001"
        if not mutant_id:
            continue

        # 从MUT_001提取数字部分
        mutant_number = mutant_id.split('_')[-1].zfill(3)
        mutant_dir = f"mutant_{mutant_number}"

        # 构建data路径
        data_path = os.path.join(mutants_dir, mutant_dir, "outdir", "Min-PDG-DATA.json")

        if not os.path.exists(data_path):
            print(f"未找到变异体 {mutant_id} 的PDG-DATA文件: {data_path}")
            continue

        # 提取信息
        data_info = extract_data_info(data_path)

        # 返回可达性路径
        result = extract_data_path(llm, data_info, mutant)
        print(result)
        # results.append(f"{mutant_id} 的可达性路径条件组合: {result}")

if __name__ == "__main__":
    get_data_info()