import asyncio
from playwright.async_api import async_playwright
import pandas as pd

async def scrape_szse_ipo():
    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # 导航到目标页面
        await page.goto('http://listing.szse.cn/projectdynamic/ipo/index.html')

        # 点击“终止(627)”筛选按钮
        await page.click('span[onclick="changeProjectDynamicStage(50)"]')
        await page.wait_for_load_state('networkidle')

        data = []
        page_num = 1

        while True:
            print(f"正在抓取第 {page_num} 页...")

            # 获取表格中的所有行
            rows = await page.query_selector_all('tbody.projectdynamic-tbody-con tr')

            for row in rows:
                # 提取每一行的信息
                cells = await row.query_selector_all('td')
                row_data = {
                    '序号': await cells[0].inner_text(),
                    '公司名称': await cells[1].inner_text(),
                    '链接': 'http://listing.szse.cn' + await (await cells[1].query_selector('a')).get_attribute('href'),
                    '板块': await cells[2].inner_text(),
                    '状态': await cells[3].inner_text(),
                    '地区': await cells[4].inner_text(),
                    '行业': await cells[5].inner_text(),
                    '保荐机构': await cells[6].inner_text(),
                    '律师事务所': await cells[7].inner_text(),
                    '会计师事务所': await cells[8].inner_text(),
                    '受理日期': await cells[9].inner_text(),
                    '更新日期': await cells[10].inner_text(),
                }
                data.append(row_data)

            # 检查是否有下一页
            next_button = await page.query_selector('li.next[data-show="next"]')
            if not next_button or 'disabled' in await next_button.get_attribute('class'):
                break

            # 点击下一页
            await next_button.click()
            await page.wait_for_load_state('networkidle')
            page_num += 1

        # 关闭浏览器
        await browser.close()

        # 将数据保存到 DataFrame
        df = pd.DataFrame(data)
        olddata = pd.read_csv('szse_ipo_data.csv')
        df = pd.concat([olddata, df], ignore_index=True)
        df.to_csv('szse_ipo_data_all.csv', index=False, encoding='utf_8_sig')
        print("数据已保存到 szse_ipo_data_all.csv")

# 运行异步任务
asyncio.run(scrape_szse_ipo())