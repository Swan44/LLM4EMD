import json
def extract_mutation_info(mutant_data):
    # 提取变异体编号
    mutant_id = mutant_data.get("mutant_id", "")

    # 提取差异信息并截取到第一个换行符之前
    difference = mutant_data.get("difference", "")
    if "\n" in difference:
        difference = difference.split("\n")[0]  # 只取第一行

    # 构建结果JSON
    result = {
        "mutant_id": mutant_id,
        "difference": difference
    }
    return json.dumps(result, indent=2)