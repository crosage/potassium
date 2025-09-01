import pandas as pd
import docx
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

# --- 1. 设置文件和文件夹路径 ---
csv_path = r'D:\code\polyline\output\per_row_errors.csv'
image_folder = r'D:\code\polyline\output\ditch_PAEK_SM2_5000'
# 修改输出文件名以区分
output_word_path = r'D:\code\polyline\output\compact_ditch_report.docx'

# --- 2. 读取并排序CSV数据 ---
try:
    print(f"正在读取CSV文件: {csv_path}")
    df = pd.read_csv(csv_path)
    sort_column = '绝对百分比误差(%)'
    if sort_column not in df.columns:
        raise ValueError(f"错误: CSV文件中未找到排序列 '{sort_column}'")
    df_sorted = df.sort_values(by=sort_column, ascending=False)
    print("CSV文件读取并排序成功。")

except FileNotFoundError:
    print(f"错误: 找不到CSV文件，请检查路径: {csv_path}")
    exit()
except Exception as e:
    print(f"读取或排序CSV时发生错误: {e}")
    exit()

# --- 3. 创建Word文档 ---
doc = docx.Document()
# 设置默认字体和段落间距，让文档更紧凑
style = doc.styles['Normal']
font = style.font
font.name = 'Calibri'  # 或者 '等线'
font.size = Pt(10.5)
style.paragraph_format.space_before = Pt(0)
style.paragraph_format.space_after = Pt(8)

doc.add_heading('清沟误差分析报告 (精简版)', level=0)
doc.add_paragraph(f"报告生成于: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

# --- 4. 遍历数据并写入Word (精简版) ---
for index, row in df_sorted.iterrows():
    try:
        ditch_name = row['清沟名称(name)']
        ditch_code = row['CODE']

        print(f"正在处理: {ditch_name}, CODE: {ditch_code}")

        # 添加标题
        doc.add_heading(f"清沟: {ditch_name} (CODE: {ditch_code})", level=2)

        # 使用表格展示关键数据，更紧凑
        table = doc.add_table(rows=3, cols=2)
        table.style = 'Table Grid'  # 使用带边框的表格样式

        # 表格内容
        keys_to_show = {
            '算法计算长度': f"{row['算法计算长度']:.2f}",
            '人工测算长度': f"{row['人工测算长度']:.2f}",
            '误差(%)': f"{row['绝对百分比误差(%)']:.2f} %"
        }

        # 填充表格
        cells = table.rows
        i = 0
        for key, value in keys_to_show.items():
            cells[i].cells[0].text = key
            cells[i].cells[1].text = value
            i += 1

        # 构建图片文件名并插入
        image_name = f"ditch__{ditch_name}__{ditch_code}__proj.png"
        image_path = os.path.join(image_folder, image_name)

        if os.path.exists(image_path):
            # 添加一个空段落来与表格隔开一点距离
            doc.add_paragraph()
            doc.add_picture(image_path, width=Inches(5.5))  # 图片宽度可适当调整
            print(f"  - 图片 '{image_name}' 已添加。")
        else:
            p = doc.add_paragraph(f"警告: 未找到对应的图片文件 '{image_name}'")
            p.runs[0].font.color.rgb = docx.shared.RGBColor(255, 0, 0)  # 警告文字设为红色
            print(f"  - 警告: 未找到图片 '{image_path}'")

        # 添加一个分隔符，代替分页符
        doc.add_paragraph("----------------------------------------------------")

    except Exception as e:
        print(f"处理行 {index} 时发生错误: {e}")
        continue

# --- 5. 保存Word文档 ---
try:
    doc.save(output_word_path)
    print("\n-----------------------------------------")
    print(f"处理完成！精简版报告已成功保存到: {output_word_path}")
    print("-----------------------------------------")
except Exception as e:
    print(f"\n保存Word文档时发生错误: {e}")