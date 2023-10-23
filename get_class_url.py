import re
import requests
from bs4 import BeautifulSoup
import csv

course_names = []
ms = []
hrefs = []
names = []
# 读取保存内容的txt文件
with open('raw.txt', 'r', encoding='utf-8') as file:
    content = file.read()

# 使用正则表达式匹配包含链接和课程名称的行
pattern = r'<a\s+href="(https://course.ucas.ac.cn/portal/site/\d+)"\s+title="([^"]+)">'
matches = re.findall(pattern, content)

with open('user_agent.txt', 'r',encoding='utf-8') as file:
    headers = {
        'User-Agent': file.read(),
    }

with open('cookies.txt', 'r',encoding='utf-8') as file:
    cookies = {
        'cookie_name': file.read(),
    }




for link, course_name in matches:
    # 发送HTTP请求，获取网页内容
    response = requests.get(link, headers=headers, cookies=cookies)

    # 使用Beautiful Soup解析HTML内容
    soup = BeautifulSoup(response.content, 'html.parser')

    # 使用选择器筛选出包含特定title文本的a标签，然后获取href属性
    # print(soup)
    target_title = "作业 - 在线发布、提交和批改作业"
    links = soup.find_all('a', {'title': target_title})
    if links == []:
        print("Try using target: 作业")
        links = soup.find_all('a', {'title': "作业"})
    # 输出匹配到的链接
    for link in links:
        href = link['href']
        print('课程:',course_name)
        print('链接:', href)
        homework_response = requests.get(href, headers=headers, cookies=cookies)
        soup_homework = BeautifulSoup(homework_response.content, 'html.parser')
        # print(soup_homework)
        pattern = re.compile(
            r'<td headers="dueDate">\s*<span class="highlight">(.*?)</span>\s*</td>',
            re.DOTALL)
        matches = re.findall(pattern, str(soup_homework))
        print(matches)
        target_elements = soup.find_all('a', {'name': 'asnActionLink'})

        for match, element in zip(matches, target_elements):
            due_date = match.strip()
            element_href = element['href']
            course_names.append(course_name)
            ms.append(due_date)
            hrefs.append(element_href)
            names.append(element.text)

with open('output.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['课程名称','作业标题', '截止时间', '对应链接']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    # 写入CSV文件的表头
    writer.writeheader()
    # 写入内容
    for c, match, name, element_href in zip(course_names, ms, names, hrefs):
        due_date = match
        print(f'{name}截止时间：', due_date)
        print('对应链接:', element_href)
        # 将内容写入CSV文件
        writer.writerow({'课程名称': c,'作业标题': name, '截止时间': due_date, '对应链接': element_href})

import pandas as pd

# 读取CSV文件
df = pd.read_csv('output.csv')

# 创建一个ExcelWriter对象，并设置参数engine='openpyxl'用于支持xlsx格式
with pd.ExcelWriter('output.xlsx', engine='openpyxl') as writer:
    # 将数据保存为Excel文件
    df.to_excel(writer, index=False, sheet_name='Sheet1')

    # 获取当前活动的工作表
    worksheet = writer.sheets['Sheet1']

    # 自动调整列宽
    for column in worksheet.columns:
        max_length = 0
        column = column[0].column_letter  # Get the column name
        for cell in worksheet[column]:
            try:  # Necessary to avoid error on empty cells
                if len(str(cell.value)) > max_length:
                    max_length = len(cell.value)
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2  # Adding a little extra width for padding
        worksheet.column_dimensions[column].width = adjusted_width

import datetime

df = pd.read_excel("output.xlsx")

# 获取当前时间
current_time = datetime.datetime.now()

# 筛选截止时间晚于当前时间的行
filtered_df = df[pd.to_datetime(df['截止时间'], format='%Y-%m-%d %H:%M') >= current_time]

# 按照截止时间的升序排列
sorted_df = filtered_df.sort_values(by='截止时间')

# 将筛选后的DataFrame写入新的xlsx文件
sorted_df.to_excel("output.xlsx", index=False)

sorted_df.to_csv("output.csv")