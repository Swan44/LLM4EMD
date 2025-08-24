import re

def extract_results(log_file_path, output_file_path):
    # 读取日志文件
    with open(log_file_path, 'r', encoding='utf-8') as file:
        log_content = file.read()

    # 正则表达式匹配变异体编号和结果
    pattern = r'\{"(MUT_\d{3})":.*?等价变异体判定结果：(\w+)'
    matches = re.findall(pattern, log_content, re.DOTALL)

    # 写入结果到输出文件
    with open(output_file_path, 'w', encoding='utf-8') as file:
        for mut_id, result in matches:
            file.write(f"{mut_id}: {result}\n")

    print(f"结果已保存到 {output_file_path}")

# 使用示例
log_file_path = 'D:\\bishe_code\\LLM4EMD\\outputs_new\\ArrayUtilsToMap_results.log'  # 替换为你的日志文件路径
output_file_path = 'D:\\bishe_code\LLM4EMD\\array_results\\ArrayUtilsToMap_results'  # 替换为输出文件路径
extract_results(log_file_path, output_file_path)

