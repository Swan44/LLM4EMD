import json


def filter_mutants_by_id(mutant_ids_file, mutants_json_file, output_file):
    # 读取变异体编号文件
    with open(mutant_ids_file, 'r') as f:
        mutant_ids = [line.strip() for line in f.readlines()]

    # 读取变异体JSON文件
    with open(mutants_json_file, 'r') as f:
        mutants_data = json.load(f)

    # 创建ID到变异体信息的映射字典
    mutant_map = {mutant['mutant_id']: mutant for mutant in mutants_data}

    # 筛选出需要的变异体信息
    filtered_mutants = []
    for mutant_id in mutant_ids:
        if mutant_id in mutant_map:
            filtered_mutants.append(mutant_map[mutant_id])
        else:
            print(f"警告: 未找到变异体 {mutant_id}")

    # 将结果写入新的JSON文件
    with open(output_file, 'w') as f:
        json.dump(filtered_mutants, f, indent=2)

    print(f"成功将 {len(filtered_mutants)} 个变异体信息写入 {output_file}")


# 使用示例
if __name__ == "__main__":
    # 文件路径
    mutant_ids_file = "/Users/swan/bishe/LLM4EMD/QuickSort/fail_list/QuickSortSwap_list"  # 变异体编号文件
    mutants_json_file = "/Users/swan/bishe/progex_benchmark/mutantbench/mutantjava/mutantsAdjDelJson/QuickSortSwapmutants.json"  # 变异体JSON文件
    output_file = "/Users/swan/bishe/LLM4EMD/QuickSort/fail_output/QuickSortSwap_fail_mutants.json"  # 输出文件

    # 执行筛选
    filter_mutants_by_id(mutant_ids_file, mutants_json_file, output_file)