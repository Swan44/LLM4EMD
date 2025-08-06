# coding=utf-8
import json
import yaml
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from reachability_extractor import get_reachability_path
from data_extractor import get_data_info
from ctrl_extractor import get_ctrl_info

# 1. 示例代码和变异体信息（提取为变量）
EXAMPLE1_PROGRAM = """
public class Mid {
    public static int main(int a, int b, int c) {
        int mid;
        if (a < b) {
            if (c < b) {
                if (a < c) {
                    mid = c;
                } else {
                    mid = a;
                }
            } else {
                mid = b;
            }
        } else {
            if (c > b) {
                if (a > c) {
                    mid = c;
                } else {
                    mid = a;
                }
            } else {
                mid = b;
            }
        }
        return mid;
    }
}
"""

EXAMPLE1_MUTANT = """{
    "difference": "@@ -16 +16 @@\\n-\\t\\t\\t\\tif (a > c) {{\\n+\\t\\t\\t\\tif (a >= c) {{",
    "equivalence": True,
    "operator": "ROR"
}"""

EXAMPLE2_PROGRAM = """
public static int classify(int a, int b, int c) {
    int trian;
    if (a <= 0 || b <= 0 || c <= 0) {
        return INVALID;
    }
    trian = 0;
    if (a == b) {
        trian = trian + 1;
    }
    if (a == c) {
        trian = trian + 2;
    }
    if (b == c) {
        trian = trian + 3;
    }
    if (trian == 0) {
        if (a + b < c || a + c < b || b + c < a) {
            return INVALID;
        } else {
            return SCALENE;
        }
    }
    if (trian > 3) {
        return EQUILATERAL;
    }
    if (trian == 1 && a + b > c) {
        return ISOSCELES;
    } else {
        if (trian == 2 && a + c > b) {
            return ISOSCELES;
        } else {
            if (trian == 3 && b + c > a) {
                return ISOSCELES;
            }
        }
    }
    return INVALID;
}
"""

EXAMPLE2_MUTANT = """{
    "difference": "@@ -32 +32 @@\\n-            if (a + b < c || a + c < b || b + c < a) {{\\n+            if (a + b < c || a + c < b-- || b + c < a) {{",
    "equivalence": False,
    "operator": "AOIS"
}"""

# 1. 加载配置文件
def load_config(config_path="D:\\bishe_code\LLM4EMD\configs\llm_configs.yaml"):
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 2. 提取原程序代码
def extract_program_code(program_path):
    with open(program_path, "r", encoding="utf-8") as f:
        return f.read()


# 3. 提取变异体信息
#def extract_mutant_info(mutant_json_path, mutant_id):
    #with open(mutant_json_path, "r", encoding="utf-8") as f:
       # mutants = json.load(f)
    #for mutant in mutants:
        #if mutant["mutant_id"] == mutant_id:
            #return mutant
    #return None



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

1. 可达性：程序到变异语句的路径条件组合为{REACHABILITY_CONSTRAINT}，请分析该变异语句是否可达。
2. 必要性：原程序与变异体语句为{DIFFERENCE}，请分析在变异语句可达情况下，结合其路径约束判断该变异是否实际改变了程序状态。
3. 数据依赖：变异语句到输出语句的数据依赖路径为{DATA_DEPENDENCY}，请分析变异影响的变量是否通过数据依赖链传播到程序输出节点。
4. 控制依赖：变异语句到输出语句的控制依赖路径为{CTRL_DEPENDENCY}，请分析变异语句是否通过控制流影响输出语句。
5. 状态覆盖：请结合以上信息与分析结论，分析变异引入的错误状态是否在后续执行中被修正或抵消，从而导致程序最终输出未受影响。

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
                # "analysis_steps": RunnablePassthrough()
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
        api_key=config["deepseek-v3"]["api_key"],
        base_url=config["deepseek-v3"]["base_url"],
        model="deepseek-chat",
        temperature=0
    )

    # 提取数据
    program_code = extract_program_code(
        # r"D:\bishe_code\progex_benchmark\mutantbench\mutantjava\Insert.java"
        program_path
    )

    #mutant_info = extract_mutant_info(
        #r"D:\bishe_code\progex_benchmark\mutantbench\mutantjava\mutantsIDJson\Insertmutants.json",
        #"MUT_001"
    #)

    # 假设这些是从其他模块获取的结果
    reachability_constraint = get_reachability_path()  # 来自reachability_extractor.py
    data_dependency = get_data_info()  # 来自data_extractor.py
    ctrl_dependency = get_ctrl_info()  # 来自ctrl_extractor.py


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
        # "analysis_steps": analysis_steps
    })

    # print("=== 变异体等价性分析结果 ===")
    return result.content


#if __name__ == "__main__":
    #main()

'''
=== 变异体等价性分析结果 ===
### 等价变异体分析步骤

#### 1. 可达性分析
- **变异语句**：`System.out.printf("%6d", a[i]++);`
- **路径条件组合**：`[number >= end, i < 4]`
- **分析**：
  - 变异语句位于循环`for (i = 0; i < 4; i++)`中，循环条件是`i < 4`，因此当`i`取值0、1、2、3时，变异语句可达。
  - 前置条件`number >= end`仅影响是否执行插入逻辑，不影响输出循环的可达性。
- **结论**：变异语句可达。

#### 2. 必要性分析
- **原始表达式**：`System.out.printf("%6d", a[i]);`
- **变异表达式**：`System.out.printf("%6d", a[i]++);`
- **分析**：
  - 变异将`a[i]`改为`a[i]++`，即先输出`a[i]`的值，然后对`a[i]`自增1。
  - 输出语句的功能是打印数组元素的值，而自增操作会修改数组元素的值。
  - 由于输出语句在循环的最后一步，且后续没有其他操作使用`a[i]`，自增操作不会影响程序的其他部分。
  - 输出的值仍然是`a[i]`的原始值（因为`a[i]++`是先取值后自增），因此输出结果不变。
- **结论**：变异未改变程序的可观察输出，属于非必要性变异。

#### 3. 数据依赖分析
- **变异影响的变量**：`a[i]`
- **数据依赖路径**：
  1. `a[i]`在输出语句中被读取并自增。
  2. 自增后的`a[i]`未被后续代码使用（循环结束后程序终止）。
- **分析**：
  - 虽然`a[i]`的值被修改，但修改后的值未传播到程序的输出或其他关键部分。
  - 输出语句依赖的是`a[i]`的原始值，自增操作不影响输出。
- **结论**：数据依赖缺失，变异未传播到程序输出。

#### 4. 控制依赖分析
- **控制依赖路径**：
  - 输出语句依赖于循环条件`i < 4`，但变异语句本身不控制任何分支。
- **分析**：
  - 变异语句是输出语句，不通过控制流影响其他语句。
  - 循环的控制流不受变异影响。
- **结论**：控制依赖缺失。

#### 5. 执行状态覆盖
- **分析**：
  - 变异引入的自增操作会修改`a[i]`的值，但修改后的值未被使用。
  - 程序的输出仅依赖于`a[i]`的原始值，因此变异的状态改变被覆盖。
- **结论**：错误状态被覆盖，不影响输出。

### 最终结论
该变异体满足以下等价变异体条件：
1. 非必要性：变异未改变程序的可观察输出。
2. 数据依赖缺失：变异影响的变量未传播到输出。
3. 状态覆盖：变异引入的状态改变被覆盖。

**等价变异体判定结果：YES**。
'''

'''
=== 变异体等价性分析结果 ===
### 步骤1：可达性分析
说明理由：变异语句位于程序的输出循环中，路径条件组合为`[number >= end, i < 4]/[number < end, i < 3, a[i] > number, j < 4, i < 4]`。这些条件在程序执行过程中是可满足的，例如当`number >= end`且`i < 4`时，变异语句会被执行。因此，变异语句是可达的。

分析结论：变异语句可达。

### 步骤2：必要性分析
说明理由：原程序语句为`System.out.printf("%6d", a[i]);`，变异体语句为`System.out.printf("%6d", a[i]++);`。变异体在输出`a[i]`的同时对`a[i]`进行了自增操作。虽然`a[i]`的值被修改，但输出的是自增前的值，因此输出的结果与原程序相同。然而，`a[i]`的状态确实被改变，但这种改变是否影响程序输出需要进一步分析。

分析结论：变异语句改变了程序状态（`a[i]`的值被修改），但这种改变是否影响输出需要看后续步骤。

### 步骤3：数据依赖分析
说明理由：变异影响的变量是数组`a`。数据依赖路径显示`a`的值被修改后，可能会影响后续的输出。然而，由于输出的是自增前的值，且后续的输出语句（`System.out.printf("%6d", a[i]++)`）在循环中，每次输出的`a[i]`都是当前值自增前的值。因此，虽然`a[i]`的值被修改，但输出的内容与原程序一致。

分析结论：变异影响的变量`a`的数据依赖路径存在，但输出的内容不受影响。

### 步骤4：控制依赖分析
说明理由：变异语句位于循环中，控制依赖路径显示其输出语句依赖于循环条件。变异语句的执行不会改变循环的控制流，也不会影响后续的输出语句的执行。因此，变异语句的控制依赖路径不影响程序输出。

分析结论：变异语句的控制依赖路径不影响程序输出。

### 步骤5：状态覆盖分析
说明理由：虽然变异语句修改了`a[i]`的值，但输出的内容是自增前的值，因此程序的可观察输出（即打印的内容）与原程序完全一致。变异引入的状态改变（`a[i]`的自增）被后续的输出逻辑所覆盖，未影响最终输出。

分析结论：变异引入的状态改变被覆盖，不影响程序输出。

### 最终结论
等价变异体判定结果：YES。
'''