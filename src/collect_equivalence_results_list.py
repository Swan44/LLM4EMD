import json
import time
import subprocess
import os
import logging
from datetime import datetime
from emd_analysis import analyze_mutant


# 配置日志
def setup_logging(program_path):
    # 创建输出目录（如果不存在）
    output_dir = r"D:\bishe_code\LLM4EMD\outputs_new"
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
def main(program_paths, mutants_json_paths):
    # program_path = "D:\\bishe_code\\progex_benchmark\\mutantbench\\mutantjava\\Triangle.java"
    # mutants_json_path = "D:\\bishe_code\\progex_benchmark\\mutantbench\\mutantjava\\mutantsDelJson\\Trianglemutants201.json"

    # 确保两个列表长度相同
    assert len(program_paths) == len(mutants_json_paths), "程序路径列表和变异体JSON路径列表长度必须相同"
    # 遍历每个程序及其对应的变异体JSON
    for program_path, mutants_json_path in zip(program_paths, mutants_json_paths):
        setup_logging(program_path)
        logging.info(f"开始处理程序: {program_path}")
        # 读取变异体JSON文件
        with open(mutants_json_path, 'r', encoding='utf-8') as f:
            mutants = json.load(f)

        # 遍历每个变异体
        for mutant in mutants:
            mutant_id = mutant["mutant_id"]
            logging.info(f"开始分析变异体 {mutant_id}...")
            # 记录开始时间
            start_time = time.time()

            try:
                # 调用分析程序
                analysis_result = analyze_mutant(program_path, mutant)
                # 计算耗时（保留4位小数）
                time_cost = round(time.time() - start_time, 4)  # 关键行：计算耗时
                # 存储结果
                # results[mutant_id] = analysis_result
                # 立即写入日志
                logging.info(json.dumps({mutant_id: analysis_result}, ensure_ascii=False))
                logging.info(f"完成变异体 {mutant_id} 的分析, 耗时: {time_cost:.4f} 秒\n")

            except Exception as e:
                time_cost = round(time.time() - start_time, 4)
                error_msg = str(e)

                logging.error(f"变异体 {mutant_id} 分析失败！耗时: {time_cost:.4f} 秒，错误: {error_msg}")

                # 可以选择存储错误信息，方便后续排查
                # results[mutant_id] = {"error": error_msg}
                continue  # 继续下一个 mutant

if __name__ == "__main__":
    # 示例调用方式
    program_paths = [
        "D:\\bishe_code\\progex_benchmark\\mutantbench\\mutantjava\\Insert.java",
        "D:\\bishe_code\\progex_benchmark\\mutantbench\\mutantjava\\Mid.java"
        "D:\\bishe_code\\progex_benchmark\\mutantbench\\mutantjava\\Min.java",
        "D:\\bishe_code\\progex_benchmark\\mutantbench\\mutantjava\\Prime_num.java"
    ]
    mutants_json_paths = [
        "D:\\bishe_code\\progex_benchmark\\mutantbench\\mutantjava\\mutantsDelJson\\Insertmutants.json",
        "D:\\bishe_code\\progex_benchmark\\mutantbench\\mutantjava\\mutantsDelJson\\Midmutants.json",
        "D:\\bishe_code\\progex_benchmark\\mutantbench\\mutantjava\\mutantsDelJson\\Minmutants.json",
        "D:\\bishe_code\\progex_benchmark\\mutantbench\\mutantjava\\mutantsDelJson\\Prime_nummutants.json"
    ]
    main(program_paths, mutants_json_paths)