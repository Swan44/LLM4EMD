import json

def process_mutants(mutant_list_file, test_result_file, truth_file, output_file):
    # 读取变异体编号列表
    with open(mutant_list_file, 'r') as f:
        mutant_ids = [line.strip() for line in f.readlines() if line.strip()]

    # 读取测试结果文件
    test_results = {}
    with open(test_result_file, 'r') as f:
        for line in f:
            if ':' in line:
                parts = line.strip().split(':')
                if len(parts) >= 2:
                    mutant_id = parts[0].strip()
                    result = parts[1].strip()
                    test_results[mutant_id] = result

    # 读取真实变异体信息文件
    truth_data = {}
    with open(truth_file, 'r') as f:
        data = json.load(f)
        for item in data:
            mutant_id = item['mutant_id']
            equivalence = item['equivalence']
            truth_data[mutant_id] = equivalence

    # 匹配结果并输出
    results = []
    for mutant_id in mutant_ids:
        if mutant_id in test_results and mutant_id in truth_data:
            test_result = test_results[mutant_id]
            truth_equivalence = str(truth_data[mutant_id]).lower()
            result_line = f"{mutant_id}: {truth_equivalence}->{test_result}"
            results.append(result_line)

    # 写入输出文件
    with open(output_file, 'w') as f:
        for result in results:
            f.write(result + '\n')

    print(f"处理完成！共匹配 {len(results)} 个变异体")
    print("结果已保存到:", output_file)


# 示例使用
if __name__ == "__main__":
    # 文件路径（请根据实际情况修改）
    mutant_list_file = "/Users/swan/bishe/LLM4EMD/mutant_list/ArrayUtils_list"  # 包含变异体编号的文件
    test_result_file = "/Users/swan/bishe/LLM4EMD/array_results/ArrayUtils_results"  # 测试结果文件
    truth_file = "/Users/swan/bishe/progex_benchmark/mutantbench/mutantjava/mutantsIDJson/ArrayUtilsmutants.json"  # 真实变异体信息文件
    output_file = "/Users/swan/bishe/LLM4EMD/process_results/ArrayUtils.txt"  # 输出文件

    process_mutants(mutant_list_file, test_result_file, truth_file, output_file)