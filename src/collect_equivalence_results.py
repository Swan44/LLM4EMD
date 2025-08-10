import json
import subprocess
import os
import logging
from datetime import datetime
from emd_analysis import analyze_mutant


# 配置日志
def setup_logging(program_path):
    # 创建输出目录（如果不存在）
    output_dir = r"D:\bishe_code\LLM4EMD\outputs"
    os.makedirs(output_dir, exist_ok=True)

    # 从程序路径中提取原程序名称
    program_name = os.path.splitext(os.path.basename(program_path))[0]
    log_filename = os.path.join(output_dir, f"{program_name}_results.log")

    # 清除所有现有的handlers
    logging.getLogger().handlers = []

    # 创建文件处理器，设置UTF-8编码
    file_handler = logging.FileHandler(log_filename, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(message)s'))

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # 配置根logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler],
        format='%(message)s'
    )

# 主函数
def main():
    program_path = "D:\\bishe_code\\progex_benchmark\\mutantbench\\mutantjava\\Triangle.java"
    mutants_json_path = "D:\\bishe_code\\progex_benchmark\\mutantbench\\mutantjava\\mutantsDelJson\\Trianglemutants.json"

    setup_logging(program_path)

    # 读取变异体JSON文件
    with open(mutants_json_path, 'r', encoding='utf-8') as f:
        mutants = json.load(f)

    results = {}

    # 遍历每个变异体
    for mutant in mutants:
        mutant_id = mutant["mutant_id"]
        logging.info(f"开始分析变异体 {mutant_id}...")

        # 调用分析程序
        analysis_result = analyze_mutant(program_path, mutant)

        # 存储结果
        results[mutant_id] = analysis_result

        # 立即写入日志
        logging.info(json.dumps({mutant_id: analysis_result}, ensure_ascii=False))

        logging.info(f"完成变异体 {mutant_id} 的分析\n")

    # 返回所有结果（可选）
    return results


if __name__ == "__main__":
    main()