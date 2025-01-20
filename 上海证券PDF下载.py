import csv
import os
import requests
from urllib.parse import urljoin

# 下载 PDF 文件
def download_pdf(url, save_path):
    """
    下载 PDF 文件并保存到指定路径
    :param url: PDF 文件的 URL
    :param save_path: 保存路径
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()  # 检查请求是否成功
        with open(save_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        print(f"已下载: {save_path}")
    except Exception as e:
        print(f"下载失败: {url} - {e}")

# 主函数
def main():
    # 读取 output.csv 文件
    input_file = "output.csv"
    output_dir = "./ipo_pdfs"
    
    # 创建保存 PDF 的文件夹
    os.makedirs(output_dir, exist_ok=True)
    
    with open(input_file, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)  # 使用 DictReader 读取 CSV
        for row in reader:
            company_name = row["公司名"]
            base_url = 'https:'
            
            # 按优先级检查并下载 PDF
            if row["注册稿"] != '-':
                pdf_url = urljoin(base_url, row["注册稿"])
                pdf_name = f"{company_name}-注册稿.pdf"
            elif row["上会稿"] != '-':
                pdf_url = urljoin(base_url, row["上会稿"])
                pdf_name = f"{company_name}-上会稿.pdf"
            elif row["申报稿"] != '-':
                pdf_url = urljoin(base_url, row["申报稿"])
                pdf_name = f"{company_name}-申报稿.pdf"
            else:
                print(f"{company_name} 没有可下载的 PDF 文件")
                continue
            
            # 下载 PDF 文件
            pdf_path = os.path.join(output_dir, pdf_name)
            download_pdf(pdf_url, pdf_path)

# 程序入口
if __name__ == "__main__":
    main()