import json
import yaml
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI


# 1. 加载配置文件
def load_config(config_path="llm_config.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 2. 提取原程序代码
def extract_program_code(program_path):
    with open(program_path, "r", encoding="utf-8") as f:
        return f.read()


# 3. 提取变异体信息
def extract_mutant_info(mutant_json_path, mutant_id):
    with open(mutant_json_path, "r", encoding="utf-8") as f:
        mutants = json.load(f)
    for mutant in mutants:
        if mutant["mutant_id"] == mutant_id:
            return mutant
    return None


# 4. 构建分析链
def build_analysis_chain(llm):
    template = """## 背景知识
（此处插入背景知识内容...）

## 待识别变异体信息
原程序：
{PROGRAM}

变异体信息：
{MUTANT_INFORMATION}

1. 可达性：程序到变异语句的路径条件组合为{REACHABILITY_CONSTRAINT}
2. 必要性：原程序与变异体语句为{DIFFERENCE}
3. 数据依赖：变异语句到输出语句的数据依赖路径为{DATA_DEPENDENCY}
4. 控制依赖：变异语句到输出语句的控制依赖路径为{CTRL_DEPENDENCY}

请按照以下步骤分析该变异体是否为等价变异体：
{analysis_steps}"""

    prompt = PromptTemplate.from_template(template)

    return (
            {
                "PROGRAM": RunnablePassthrough(),
                "MUTANT_INFORMATION": RunnablePassthrough(),
                "REACHABILITY_CONSTRAINT": RunnablePassthrough(),
                "DIFFERENCE": RunnablePassthrough(),
                "DATA_DEPENDENCY": RunnablePassthrough(),
                "CTRL_DEPENDENCY": RunnablePassthrough(),
                "analysis_steps": RunnablePassthrough()
            }
            | prompt
            | llm
    )


# 5. 主函数
def main():
    # 加载配置
    config = load_config()

    # 初始化LLM
    llm = ChatOpenAI(
        api_key=config["deepseek"]["api_key"],
        base_url=config["deepseek"]["base_url"],
        model="deepseek-chat",
        temperature=0
    )

    # 提取数据
    program_code = extract_program_code(
        r"D:\bishe_code\progex_benchmark\mutantbench\mutantjava\Insert.java"
    )

    mutant_info = extract_mutant_info(
        r"D:\bishe_code\progex_benchmark\mutantbench\mutantjava\mutantsIDJson\Insertmutants.json",
        "MUT_001"
    )

    # 假设这些是从其他模块获取的结果
    reachability_constraint = "无条件直接可达"  # 来自reachability_extractor.py
    data_dependency = "a[i] → System.out"  # 来自data_extractor.py
    ctrl_dependency = "无控制依赖"  # 来自ctrl_extractor.py

    # 构建分析步骤
    analysis_steps = """
1. 可达性分析：判断变异语句是否可达
2. 必要性分析：分析变异是否改变程序状态  
3. 数据依赖分析：检查变异影响是否传播到输出
4. 控制依赖分析：检查控制流影响
5. 状态覆盖分析：检查错误状态是否被覆盖"""

    # 构建并执行分析链
    analysis_chain = build_analysis_chain(llm)
    result = analysis_chain.invoke({
        "PROGRAM": program_code,
        "MUTANT_INFORMATION": json.dumps(mutant_info, indent=2),
        "REACHABILITY_CONSTRAINT": reachability_constraint,
        "DIFFERENCE": mutant_info["difference"],
        "DATA_DEPENDENCY": data_dependency,
        "CTRL_DEPENDENCY": ctrl_dependency,
        "analysis_steps": analysis_steps
    })

    print("=== 变异体等价性分析结果 ===")
    print(result.content)


if __name__ == "__main__":
    main()