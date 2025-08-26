import json


def compare_equivalence(json_file_path, txt_file_path):
    # 读取JSON文件
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        json_data = json.load(json_file)

    # 读取TXT文件并解析为字典
    txt_data = {}
    with open(txt_file_path, 'r', encoding='utf-8') as txt_file:
        for line in txt_file:
            line = line.strip()
            if line:
                parts = line.split(':')
                if len(parts) == 2:
                    mutant_id = parts[0].strip()
                    equivalence_txt = parts[1].strip().upper()  # 转换为大写确保比较
                    txt_data[mutant_id] = equivalence_txt == 'YES'  # 转换为布尔值

    right_count = 0
    total_mutants = len(json_data)
    mismatched_mutants = []

    # 比较JSON和TXT中的等价性信息
    for mutant in json_data:
        mutant_id = mutant['mutant_id']
        equivalence_json = mutant['equivalence']

        if mutant_id in txt_data:
            equivalence_txt = txt_data[mutant_id]
            if equivalence_json == equivalence_txt:
                right_count += 1
            else:
                mismatched_mutants.append(mutant_id)
        else:
            print(f"警告: 变异体 {mutant_id} 在TXT文件中未找到")

    # 输出结果
    print(f"正确匹配的变异体数量: {right_count}")
    print(f"变异体总数: {total_mutants}")
    print(f"匹配准确率: {right_count / total_mutants * 100:.2f}%")

    if mismatched_mutants:
        print("\n不匹配的变异体编号:")
        for mutant_id in mismatched_mutants:
            print(mutant_id)
    else:
        print("\n所有变异体匹配一致")


json_file_path = 'D:\\bishe_code\\progex_benchmark\\mutantbench\\mutantjava\\mutantsAdjJson\\DefrosterMainmutants.json'  # 替换为你的JSON文件路径
txt_file_path = '/result_output_new/DefrosterMain_results'  # 替换为你的TXT文件路径
compare_equivalence(json_file_path, txt_file_path)