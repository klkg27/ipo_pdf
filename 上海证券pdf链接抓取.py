import time
import csv
from playwright.sync_api import sync_playwright
from tqdm import tqdm

# 读取 CSV 文件并转换为字典列表
def read_csv_to_dict(filename):
    """
    读取 CSV 文件并将其转换为字典列表
    :param filename: CSV 文件名
    :return: 字典列表，每个字典对应一行数据
    """
    companies = []
    
    # 尝试使用 utf-8 编码读取文件
    try:
        with open(filename, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)  # 使用 DictReader 读取 CSV
            for row in reader:
                companies.append({
                    "name": row["公司名称"],  # 读取“公司名称”列
                    "url": row["链接"]       # 读取“链接”列
                })
    except UnicodeDecodeError:
        # 如果 utf-8 编码失败，尝试使用 gbk 编码
        with open(filename, mode="r", encoding="gbk") as file:
            reader = csv.DictReader(file)  # 使用 DictReader 读取 CSV
            for row in reader:
                companies.append({
                    "name": row["公司名称"],  # 读取“公司名称”列
                    "url": row["链接"]       # 读取“链接”列
                })
    
    return companies

# 提取目标 <td> 中的 href 属性
def get_hrefs(page, url):
    # 导航到目标网页
    page.goto(url)
    
    # 等待目标表格加载完成
    page.wait_for_selector('td.text-nowrap.pr-10:has-text("招股说明书")')
    
    # 定位包含“招股说明书”的 td 元素
    target_td = page.locator('td.text-nowrap.pr-10:has-text("招股说明书")')
    
    # 获取后面的三个 td 元素
    next_tds = target_td.locator('xpath=following-sibling::td[position() <= 3]')
    
    # 提取 href 属性
    hrefs = []
    for i in range(3):  # 确保只取三个
        td = next_tds.nth(i)
        link = td.locator('a')  # 定位 <a> 标签
        if link.count() > 0:  # 检查是否存在 <a> 标签
            href = link.get_attribute('href')
            hrefs.append(href)
        else:
            hrefs.append('-')
    
    return hrefs

# 保存结果到 CSV 文件
def save_to_csv(data, filename="output.csv"):
    # 表头
    headers = ["公司名", "链接", "申报稿", "上会稿", "注册稿"]
    
    # 写入 CSV 文件
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)  # 写入表头
        writer.writerows(data)  # 写入数据

# 主函数
def main():
    # 读取公司名和链接
    companies = read_csv_to_dict("公司信息.csv")
    results = []
    
    with sync_playwright() as p:
        # 启动浏览器
        browser = p.chromium.launch(headless=True)  # headless=False 表示显示浏览器窗口
        page = browser.new_page()
        
        # 遍历公司名和链接
        for company in tqdm(companies):
            print(f"正在处理: {company['name']} - {company['url']}")
            
            try:
                # 获取 hrefs
                hrefs = get_hrefs(page, company['url'])
                
                # 将结果添加到列表中
                results.append([company['name'], company['url'], *hrefs])
            except Exception as e:
                print(f"处理 {company['name']} 时出错: {e}")
                results.append([company['name'], company['url'], '-', '-', '-'])
            
            # 添加一定的 sleep 时间，避免请求过于频繁
            time.sleep(1)
        
        # 关闭浏览器
        browser.close()
    
    # 保存结果到 CSV 文件
    save_to_csv(results)
    print("结果已保存到 output.csv")

# 程序入口
if __name__ == "__main__":
    main()