import re

def replace_cpu_core_events(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    
    # 将 cpu_core/{event}/ 替换为 {event}
    # 例如：cpu_core/instructions/ -> instructions
    modified_content = re.sub(r'cpu_core/([^/]*)/(?=,|$)', r'\1', content)
    
    with open(file_path, 'w') as file:
        file.write(modified_content)
    
    print(f"替换完成: {file_path}")

if __name__ == "__main__":
    file_path = "/home/sieni/Desktop/working_doc/project/Zhou_ZJU/bench_test_2/perf.script"
    replace_cpu_core_events(file_path)