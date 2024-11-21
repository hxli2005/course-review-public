import pdfplumber
import re

def parse_pdf_by_columns(file_path):
    with pdfplumber.open(file_path) as pdf:
        first_page = pdf.pages[0]
        # 提取表格数据
        table = first_page.extract_table()

        # 打印表格用于调试
        for row in table:
            print(row)

        # 提取个人基本信息
        basic_info = table[0][0]  # 第一行的第一个单元格包含全部个人信息
        student_id = re.search(r"学号：(\d+)", basic_info).group(1)
        name = re.search(r"姓名：(\S+)", basic_info).group(1)
        gender = re.search(r"性别：(\S+)", basic_info).group(1)
        grade = re.search(r"年级：(\d+)", basic_info).group(1)
        faculty = re.search(r"学院：(\S+)", basic_info).group(1)
        campus = re.search(r"校区：(\S+)", basic_info).group(1)

        # 保存个人信息到变量
        basic_info_dict = {
            '学号': student_id,
            '姓名': name,
            '性别': gender,
            '年级': grade,
            '学院': faculty,
            '校区': campus
        }

        # 提取课程信息
        courses = []
        current_course = {}

        for row in table[3:]:  # 从第4行开始解析课程信息
            if row[0] == '#':  # 如果遇到标题行，跳过
                continue
            if any("合计学分" in cell for cell in row if cell):
                break

            course_code = row[1]
            course_name = row[3]
            teacher_name = row[9]

            # 去除换行符和多余空格，并确保教师姓名没有空格
            if course_name:
                course_name = re.sub(r'\s+', '', course_name)  # 移除所有空格
            if teacher_name:
                teacher_name = re.sub(r'\s+', '', teacher_name)  # 移除所有空格

            if course_code:  # 如果课程号不为空，开始新课程的解析
                if current_course:  # 如果当前课程已存在，则保存它
                    courses.append(current_course)
                current_course = {
                    '课程号': course_code.strip(),
                    '课程名': course_name.strip(),
                    '教师姓名': teacher_name
                }
            else:  # 如果课程号为空，表示是前一课程的信息延续
                current_course['课程名'] += " " + course_name.strip()
                current_course['教师姓名'] += teacher_name

        if current_course:  # 添加最后一门课程
            courses.append(current_course)

        # 打印或使用这些变量
        print(f"学号: {student_id}")
        print(f"姓名: {name}")
        print(f"性别: {gender}")
        print(f"年级: {grade}")
        print(f"学院: {faculty}")
        print(f"校区: {campus}")

        for course in courses:
            print(f"课程号: {course['课程号']}, 课程名: {course['课程名']}, 教师姓名: {course['教师姓名']}")

        return basic_info_dict, courses

# 测试代码
if __name__ == '__main__':
    file_path = "打印页.pdf"  # 确保路径正确
    basic_info, courses = parse_pdf_by_columns(file_path)

    # 输出信息验证
    print("\n个人信息:")
    print(basic_info)

    print("\n课程信息:")
    for course in courses:
        print(course)
