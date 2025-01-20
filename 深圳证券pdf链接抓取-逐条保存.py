from playwright.sync_api import sync_playwright
from datetime import datetime
import csv
import concurrent.futures
import queue

# 全局队列，用于存储待处理的任务
task_queue = queue.Queue()

# 全局锁，用于确保 CSV 文件的线程安全写入
import threading
csv_lock = threading.Lock()

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

def get_latest_href(td):
    """
    从 <td> 中提取最新的 href。
    如果有多个 <a> 标签，选择日期最新的一个。
    如果没有 <a> 标签，返回 '--'。
    """
    # 使用 evaluate 提取单个 <td> 中的所有 <a> 标签
    links = td.evaluate('''td => {
        return Array.from(td.querySelectorAll('a')).map(a => ({
            date: a.innerText.trim(),
            href: a.href
        }));
    }''')
    
    if not links:
        return '--'
    
    # 解析日期并选择最新的链接
    link_data = []
    for link in links:
        date_text = link['date']
        href = link['href']
        try:
            # 将日期字符串转换为 datetime 对象
            date = datetime.strptime(date_text, '%Y-%m-%d')
            link_data.append((date, href))
        except ValueError:
            # 如果日期格式不匹配，跳过
            continue
    
    if not link_data:
        return '--'
    
    # 选择日期最新的链接
    latest_date, latest_href = max(link_data, key=lambda x: x[0])
    return latest_href

def process_task(page, company_name, url):
    """
    处理单个任务：提取数据并实时保存到 CSV 文件
    """
    try:
        # 导航到目标网页
        page.goto(url)
        
        # 等待目标表格加载完成
        page.wait_for_selector('td:has-text("招股说明书")')
        
        # 定位包含“招股说明书”的 td 元素
        target_td = page.locator('td:has-text("招股说明书")')
        
        # 获取后面的三个 td 元素
        next_tds = target_td.locator('xpath=following-sibling::td[position() <= 3]')
        
        # 提取 href 属性
        hrefs = []
        for i in range(3):  # 确保只取三个
            td = next_tds.nth(i)
            href = get_latest_href(td)
            hrefs.append(href)
            page.wait_for_timeout(1000)  # 每个 <td> 提取后等待 1 秒
        
        # 实时保存到 CSV 文件
        with csv_lock:
            with open('szse_ipo_pdf.csv', mode='a', newline='', encoding='utf_8_sig') as file:
                writer = csv.DictWriter(file, fieldnames=['公司名称', '链接', '申报稿', '上会稿', '注册稿'])
                writer.writerow({
                    '公司名称': company_name,
                    '链接': url,
                    '申报稿': hrefs[0],
                    '上会稿': hrefs[1],
                    '注册稿': hrefs[2]
                })
        print(f"已保存: {company_name}")
    except Exception as e:
        print(f"处理 {company_name} 时出错: {e}")

def worker():
    """
    工作线程函数：从队列中获取任务并处理
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)  # 无头模式
        page = browser.new_page()
        
        while not task_queue.empty():
            company_name, url = task_queue.get()
            process_task(page, company_name, url)
            task_queue.task_done()
        
        browser.close()

def main():
    # 初始化任务队列
    all_data = read_csv_to_dict('szse_ipo_data_all.csv')
    print(f"共有 {len(all_data)} 条数据")
    for data in all_data:
        task_queue.put((data['name'], data['url']))
    
  # 初始化 CSV 文件并写入表头（仅在文件不存在时写入表头）
    try:
        with open('szse_ipo_pdf.csv', mode='r', encoding='utf_8_sig') as file:
            pass  # 如果文件存在，跳过表头写入
    except FileNotFoundError:
        with open('szse_ipo_pdf.csv', mode='w', newline='', encoding='utf_8_sig') as file:
            writer = csv.DictWriter(file, fieldnames=['公司名称', '链接', '申报稿', '上会稿', '注册稿'])
            writer.writeheader()
    
    # 启动多线程处理
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:  # 4 个线程
        futures = [executor.submit(worker) for _ in range(4)]
        concurrent.futures.wait(futures)

if __name__ == '__main__':
    main()