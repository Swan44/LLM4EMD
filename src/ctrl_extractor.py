from langchain_core.runnables import RunnablePassthrough
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
import json
import re
import os
import yaml

def load_deepseek_config(config_path="D:\\bishe_code\LLM4EMD\configs\llm_config.yaml"):
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


def extract_ctrl_info(ctrl_json_path):
    """从PDG ctrl JSON文件中提取信息"""
    with open(ctrl_json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_reachability_path(llm, ctrl_info, mutant_info):
    """使用LLM提取控制依赖信息"""
    template = """请根据提供的PDG控制依赖图和变异体信息，严格按照以下要求提取变异语句的控制依赖路径：
1. 提取范围：
   - 从变异语句开始
   - 到程序输出语句结束，不要扩展无关分支
   - 若无到输出语句的控制依赖，则提取到终止节点的完整路径
2. 输出格式要求：
   [路径编号]. [完整条件链] → … → [返回/输出语句]
   其中：
   - 条件链格式：if (条件)→ 分支方向(True/False) → ...
   - 语句必须包含原始代码
3. 示例格式：
控制依赖路径信息：
1. (16: if (a >= c)) --True--> (18: mid = c) -- --> (23: return mid)
2. (16: if (a >= c)) --False--> (20: mid = a) -- --> (23: return mid)
4. 特殊处理：
   - 对复合条件语句，需展开所有可能路径
   - 对循环依赖，标注循环起点和终点
   - 对并行路径，分别独立列出
5. 最终输出：
   - 每条路径独立编号
   - 只输出依赖路径信息即可，无需做路径说明

控制依赖信息:
{ctrl_info}

变异体信息:
{mutant_info}
"""

    prompt = PromptTemplate(
        input_variables=["ctrl_info", "mutant_info"],
        template=template
    )

    #chain = LLMChain(llm=llm, prompt=prompt)
    #result = chain.run(cfg_info=json.dumps(cfg_info, indent=2),
                       #mutant_info=json.dumps(mutant_info, indent=2))
    # 使用新的 Runnable 语法
    chain = (
            {"ctrl_info": RunnablePassthrough(), "mutant_info": RunnablePassthrough()}
            | prompt
            | llm
    )

    # 获取 AI 响应对象
    response = chain.invoke({
        "ctrl_info": json.dumps(ctrl_info, indent=2),
        "mutant_info": json.dumps(mutant_info, indent=2)
    })

    # 提取响应内容（关键修复）
    # response_text = response.content if hasattr(response, 'content') else str(response)

    # 正则匹配
    # match = re.search(r"可达性路径条件组合:\s*(.*)", response_text)
    # return match.group(1).strip() if match else "NULL"
    return response.content if hasattr(response, 'content') else str(response)


def main():
    # 初始化LLM
    llm = ChatOpenAI(
        openai_api_key=deepseek_config["api_key"],
        model="deepseek-chat",
        temperature=0,
        openai_api_base=deepseek_config["base_url"],
    )

    # 示例路径
    ctrl_path = r"D:\bishe_code\progex_benchmark\mutant_programs\Insert\mutants\mutant_001\outdir\Insert-PDG-CTRL.json"
    mutant_json_path = r"D:\bishe_code\progex_benchmark\mutantbench\mutantjava\mutantsIDJson\Insertmutants.json"

    # 从ctrl路径中提取变异体编号
    mutant_number = os.path.basename(os.path.dirname(os.path.dirname(ctrl_path))).split('_')[-1]

    # 提取信息
    mutant_info = extract_mutant_info(mutant_json_path, mutant_number)
    ctrl_info = extract_ctrl_info(ctrl_path)

    if not mutant_info:
        print(f"未找到变异体 MUT_{mutant_number.zfill(3)} 的信息")
        return

    # 提取数据依赖信息
    ctrl_path = extract_reachability_path(llm, ctrl_info, mutant_info)

    # print("可达性路径条件组合:")
    print(ctrl_path)


if __name__ == "__main__":
    main()