# coding=utf-8
import json
import os
import yaml
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from reachability_extractor import get_reachability_path
from data_extractor import get_data_info
from ctrl_extractor import get_ctrl_info

# 1. 示例代码和变异体信息（提取为变量）
EXAMPLE1_PROGRAM = """
public class Mid {public static int main(int a, int b, int c) {int mid;if (a < b) {if (c < b) {if (a < c) {mid = c;} else {mid = a;}} else {mid = b;}} else {if (c > b) {if (a > c) {mid = c;} else {mid = a;}} else {mid = b;}}return mid;}}
"""
EXAMPLE1_MUTANT = """{
    "difference": "@@ -16 +16 @@\\n-\\t\\t\\t\\tif (a > c) {{\\n+\\t\\t\\t\\tif (a >= c) {{",
    "equivalence": True,
    "operator": "ROR"
}"""
EXAMPLE2_PROGRAM = """
public static int classify(int a, int b, int c) {int trian;if (a <= 0 || b <= 0 || c <= 0) {return INVALID;}trian = 0;if (a == b) {trian = trian + 1;}if (a == c) {trian = trian + 2;}if (b == c) {trian = trian + 3;}if (trian == 0) {if (a + b < c || a + c < b || b + c < a) {return INVALID;} else {return SCALENE;}}if (trian > 3) {return EQUILATERAL;}if (trian == 1 && a + b > c) {return ISOSCELES;} else {if (trian == 2 && a + c > b) {return ISOSCELES;} else {if (trian == 3 && b + c > a) {return ISOSCELES;}}}return INVALID;}
"""
EXAMPLE2_MUTANT = """{
    "difference": "@@ -32 +32 @@\\n-            if (a + b < c || a + c < b || b + c < a) {{\\n+            if (a + b < c || a + c < b-- || b + c < a) {{",
    "equivalence": False,
    "operator": "AOIS"
}"""

# 1. 加载配置文件
def load_config(config_path="/Users/swan/bishe/LLM4EMD/configs/llm_configs.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 2. 提取原程序代码
def extract_program_code(program_path):
    with open(program_path, "r", encoding="utf-8") as f:
        return f.read()

# 4. 构建分析链
def build_analysis_chain(llm):

    template = """
## 背景知识
变异测试通过对程序源代码引入小幅语法修改模拟潜在缺陷。这些经过修改的程序版本称为变异体。等价变异体指与原程序语法不同，但语义相同的变异体，没有任何测试输入可以区分它们与原程序的行为差异。
## 等价变异体判定步骤
一个变异体仅当满足以下三个条件时才能被杀死：1.可达性：变异语句能够被执行到；2.感染：变异操作导致程序状态改变；3.传播：状态改变必须影响到程序输出。
基于上述规则，可从以下五个步骤详细分析该变异体是否满足以下任意条件，若满足，则为等价变异体：
1.不可达性：判断变异语句的路径条件组合是否逻辑上不可满足。例如，若变异语句依赖条件如 (a > 0 && a < 0)，该条件恒为假，路径不可达，无任何输入可触发该变异语句，属于等价变异体。
2.非必要性：检查变异是否实际改变了程序语义。即使变异语句可达，若变异与原表达式在当前路径下语义等价，不影响程序状态，则属于等价变异体。例如，if(a % 2 >= 0)下的a % 2 == 0与a % 2 <= 0在执行路径上表现一致，未改变程序状态，属于等价变异体。
3.数据依赖缺失：判断变异影响的变量是否通过数据依赖链传播到程序输出节点。例如，原程序：x = a + b; return x;变异体：x = a++ + b; return x;被变异影响的传播变量a未被后续return语句使用，无传播变量相关的数据依赖边（即变量a的定义-使用链）连接变异节点与输出节点，将变异节点的错误状态传递至输出，数据依赖缺失，属于等价变异体。
4.控制依赖缺失：分析变异语句是否通过控制流影响输出语句。例如原程序：x = a + b; a = a - 1; return x;变异体：x = a + b; a = a + 1; return x;其中，变异语句a = a + 1;独立于x，变异效果无法通过控制流传递到返回语句。即从变异节点出发，无控制依赖边到达任意输出节点的路径，控制依赖缺失，属于等价变异体。
5.执行状态覆盖：判断变异引入的错误状态是否在后续执行中被修正或抵消。例如，原程序：if(a>b){{return a;}}return b; 变异体if(a>=b){{return a;}}return b; 在 a == b 时变异语句触发错误状态，改变控制流，但仍输出与原程序等价的值b，说明错误状态被覆盖，不影响输出，属于等价变异体。
## 少样本示例
以下是一个等价变异体和一个非等价变异体的分析示例。每个示例都包含原程序的完整类/方法代码、变异体信息、等价性分析及结论。
## 等价变异体示例
原程序：
{example1_program}
变异体信息：
{example1_mutant}
等价性分析：
1. 可达性分析：变异体的控制流图分析显示，从程序入口到该变异语句的路径满足以下条件组合：
- if (a < b) == False 
- if (c > b) == True
分析得，该路径条件可满足，即变异点可达。
2. 必要性分析：
原始表达式：a > c  
变异表达式：a >= c  
该语句可达路径上的变量约束为：a < b == false 且 c > b == true  
分析得，在这些约束下，存在a=c的输入使原表达式a>c和变异表达式a>=c的取值不同，存在程序状态改变，满足必要性。
3. 数据依赖分析：
传播变量 a 的数据依赖路径如下：
a: (line 16: if (a >= c)) → if True: (line 16) --[Control True]--> (line 17: mid = c) --[Flows mid]--> (line 25: return mid)→ if False: (line 16) --[Control False]--> (line 19: mid = a) --[Flows mid]--> (line 25: return mid)
传播变量 c 的数据依赖路径如下：
c: (line 16: if (a >= c)) → if True: (line 16) --[Control True]--> (line 17: mid = c) --[Flows mid]--> (line 25: return mid)
分析得，变量a和c的值会直接影响mid的值，变异语句控制的分支决定了mid的赋值来源，而mid作为函数返回值输出，因此变异所引入的状态差异可以通过数据依赖链传播到程序输出，存在数据依赖条件。
4. 控制依赖分析：
控制依赖路径：(16: if (a >= c)) --True--> (18: mid = c) -- --> (23: return mid);
(16: if (a >= c)) --False--> (20: mid = a) -- --> (23: return mid)
分析得，变异语句控制了程序分支的走向，而程序的输出语句控制依赖于变异语句的真假结果，即变异语句决定了mid的赋值来源，进而影响最终的返回值。变异语句与输出语句存在控制依赖路径，变异语句影响输出语句的执行，故变异效果可以传递至输出。
5. 状态覆盖分析：
基于前述分析，变异体满足可达性、必要性，数据依赖与控制依赖路径均存在。然而，在特定输入条件a==c下，虽然原程序与变异体执行的分支不同，原程序执行mid=a，变异体执行mid=c，但由于a=c，两者赋值效果完全相同，因此程序最终返回值mid保持一致。因此，尽管变异体在执行中确实引入了不同的中间状态，并通过依赖路径传递到输出语句，但由于其效果在具体执行条件下被逻辑赋值行为所抵消，最终程序的可观察输出未发生改变。
这说明程序在此路径下存在状态覆盖现象，变异所引入的错误状态被抵消，故该变异体属于等价变异体。
结论：等价变异体判定结果：YES。
## 非等价变异体示例
原程序：
{example2_program}

变异体信息：
{example2_mutant}
等价性分析：
1. 可达性分析：变异体的控制流图分析显示，从程序入口到该变异语句的路径满足以下条件组合：
a > 0 && b > 0 && c > 0 && a != b && a != c && b != c
分析得，该路径条件可满足，即变异点可达。
2. 必要性分析：
原始表达式：if (a + b < c || a + c < b || b + c < a) {{  
变异表达式：if (a + b < c || a + c < b-- || b + c < a) {{  
该语句可达路径上的变量约束为：a > 0 && b > 0 && c > 0 && a != b && a != c && b != c
分析得，在这些约束下，存在{{a=3, b=2, c=1}}的输入使原表达式值为false，变异表达式值为true，取值不同，存在程序状态改变，满足必要性。
3. 数据依赖分析：
变量b的数据依赖路径:
1.(line 32: if (a + b < c || a + c < b-- || b + c < a)) → if True: (line 32) --[Control True]--> (line 33: return INVALID)
2.(line 32: if (a + b < c || a + c < b-- || b + c < a)) → if False: (line 32) --[Control False]--> (line 35: return SCALENE)
分析得，该变异b—改变了b的值，使得a+c<b—的判定结果可能发生变化，而改变会通过条件判断直接影响程序的返回值，因此变异所引入的状态差异可以通过数据依赖链传播到程序输出，存在数据依赖条件。
4. 控制依赖分析：
控制依赖路径信息：
(19: if (a + b < c || a + c < b-- || b + c < a)) --True--> (21: return INVALID;)
(19: if (a + b < c || a + c < b-- || b + c < a)) --False--> (23: return SCALENE;)
分析得，变异语句控制了程序分支的走向，而程序的输出语句控制依赖于变异语句的真假结果，进而影响最终的返回值。变异语句与输出语句存在控制依赖路径，变异语句影响输出语句的执行，故变异效果可以传递至输出。
5. 状态覆盖分析：
基于前述分析，变异体满足可达性、必要性、数据依赖与控制依赖路径均存在，且变异体造成的程序状态改变均可直接传递至输出，不存在状态覆盖现象，故该变异体属于非等价变异体。
结论：等价变异体判定结果：NO。
## 待识别变异体信息
请基于以下信息与分析步骤判断该变异体是否为等价变异体，并输出每步分析与结论。
注意：若某一步已足以判断该变异体为等价变异体，则不再继续后续分析步骤，直接给出最终结论。
原程序：
{PROGRAM}
变异体信息：
{MUTANT_INFORMATION}
1. 可达性：程序到变异语句前的路径条件组合为{REACHABILITY_CONSTRAINT}，请分析该变异语句是否可达（而非变异语句是否可满足）。
2. 必要性：原程序与变异体语句为{DIFFERENCE}，请分析在变异语句可达情况下，结合其路径约束判断该变异是否实际改变了程序状态。
3. 数据依赖：变异语句到输出语句的数据依赖路径为{DATA_DEPENDENCY}，请分析变异影响的变量是否通过数据依赖链传播到程序输出节点。
4. 控制依赖：变异语句到输出语句的控制依赖路径为{CTRL_DEPENDENCY}，请分析变异语句是否通过控制流影响输出语句。
5. 状态覆盖：请结合以上信息与分析结论，分析变异引入的错误状态是否在后续执行中被修正或抵消，从而导致程序最终输出未受影响。
## 注意：删除类型的变异算子是针对原程序的删除，而非对变异语句的删除。
## 输出格式要求
每个步骤输出如下：
步骤[name]：
说明理由： 
分析结论： 
……
最终结论：等价变异体判定结果：YES或等价变异体判定结果：NO。
"""

    prompt = PromptTemplate.from_template(template)

    return (
            {
                "example1_program": RunnablePassthrough(),
                "example1_mutant": RunnablePassthrough(),
                "example2_program": RunnablePassthrough(),
                "example2_mutant": RunnablePassthrough(),
                "PROGRAM": RunnablePassthrough(),
                "MUTANT_INFORMATION": RunnablePassthrough(),
                "REACHABILITY_CONSTRAINT": RunnablePassthrough(),
                "DIFFERENCE": RunnablePassthrough(),
                "DATA_DEPENDENCY": RunnablePassthrough(),
                "CTRL_DEPENDENCY": RunnablePassthrough(),
            }
            | prompt
            | llm
    )


# 5. 主函数
def analyze_mutant(program_path, mutant):
    # 加载配置
    config = load_config()

    # 初始化LLM
    llm = ChatOpenAI(
        api_key=config["deepseek-v3-g"]["api_key"],
        base_url=config["deepseek-v3-g"]["base_url"],
        model="deepseek-chat",
        # api_key=config["gpt-3.5-turbo"]["api_key"],
        # base_url=config["gpt-3.5-turbo"]["base_url"],
        # model="gpt-3.5-turbo",
        temperature=0
    )

    # 提取数据
    program_code = extract_program_code(program_path)

    program_name = os.path.splitext(os.path.basename(program_path))[0]

    # 假设这些是从其他模块获取的结果
    reachability_constraint = get_reachability_path(program_name, mutant)  # 来自reachability_extractor.py
    data_dependency = get_data_info(program_name, mutant)  # 来自data_extractor.py
    ctrl_dependency = get_ctrl_info(program_name, mutant)  # 来自ctrl_extractor.py

    # 构建并执行分析链
    analysis_chain = build_analysis_chain(llm)
    result = analysis_chain.invoke({
        "example1_program": EXAMPLE1_PROGRAM,
        "example1_mutant": EXAMPLE1_MUTANT,
        "example2_program": EXAMPLE2_PROGRAM,
        "example2_mutant": EXAMPLE2_MUTANT,
        "PROGRAM": program_code,
        "MUTANT_INFORMATION": json.dumps(mutant, indent=2),
        "REACHABILITY_CONSTRAINT": reachability_constraint,
        "DIFFERENCE": mutant["difference"],
        "DATA_DEPENDENCY": data_dependency,
        "CTRL_DEPENDENCY": ctrl_dependency,
    })
    return result.content

'''
if __name__ == "__main__":
    result = analyze_mutant("/Users/swan/bishe/progex_benchmark/mutantbench/mutantjava/mutantjavadiv/ArrayUtilsLastShort.java",
                            {
                                "mutant_id": "MUT_001",
                                "difference": "@@ -8 +8 @@\n-        } else if (startIndex >= array.length) {\n+        } else if (startIndex == array.length) {",
                                "operator": "ROR"
                            }
                   )
    print(result)
'''