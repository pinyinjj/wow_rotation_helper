import os
import subprocess
import pipreqs.pipreqs

# 替换原来的 read_file_content 方法，使其使用 'latin-1' 编码读取文件
def read_file_content(file_name, encoding='latin-1'):
    with open(file_name, 'r', encoding=encoding) as f:
        return f.read()

# 将 pipreqs 的 read_file_content 方法替换为我们自定义的方法
pipreqs.pipreqs.read_file_content = read_file_content

# 指定项目根目录
project_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# 递归遍历项目根目录，找出所有的 .py 文件
py_files = []
for root, dirs, files in os.walk(project_dir):
    for file in files:
        if file.endswith(".py"):
            py_files.append(os.path.join(root, file))

# 打印找到的 Python 文件
print("Found Python files:")
for py_file in py_files:
    print(py_file)

# 打印项目根目录，确认它是我们期望的目录
print(f"Project root directory: {project_dir}")

# 调用 pipreqs 来生成 requirements.txt 文件，并通过代理
result = subprocess.run(
    ["pipreqs", project_dir, "--force", "--proxy=http://127.0.0.1:7891"],
    capture_output=True, text=True
)

# 打印 pipreqs 的输出
print(result.stdout)
print(result.stderr)
