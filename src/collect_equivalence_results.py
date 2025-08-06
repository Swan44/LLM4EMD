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
    log_filename = os.path.join(output_dir, f"{program_name}_results_1.log")

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
    # 禁用HTTP请求日志
    logging.getLogger("http.client").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)


# 调用分析程序并获取结果
#def analyze_mutant(program_path, mutant_info):
    # 这里假设emd_analysis.py接受程序路径和变异体信息作为参数
    # 并返回分析结果（JSON格式或其他可解析格式）
    #cmd = [
        #'python', 'emd_analysis.py',
        #'--program', program_path,
        #'--mutant', json.dumps(mutant_info)
    #]
    #result = subprocess.run(cmd, capture_output=True, text=True)
    #return result.stdout.strip()


# 主函数
def main():
    program_path = "D:\\bishe_code\\progex_benchmark\\mutantbench\\mutantjava\\Mid.java"
    mutants_json_path = "D:\\bishe_code\\progex_benchmark\\mutantbench\\mutantjava\\mutantsDelJson\\Midmutants.json"

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