import cmd
import os
import sys
from typing import List, Dict, Tuple, Optional

class VeEditor(cmd.Cmd):
    """基于终端的文本编辑器，实现ve命令集"""
    
    prompt = 've> '
    intro = 've文本编辑器 - 输入 help 查看命令帮助'
    
    def __init__(self):
        super().__init__()
        # 编辑器状态
        self.state = {
            'is_active': False,         # 编辑器是否激活
            'current_file': None,       # 当前编辑的文件
            'content': [],              # 文件内容行数组
            'cursor': {
                'row': 0,               # 光标行号（0-based）
                'col': 0                # 光标列号（0-based）
            },
            'clipboard': ''             # 剪贴板内容
        }
        
        # 存储原始stdout用于重定向
        self.original_stdout = sys.stdout
    
    def preloop(self):
        """循环开始前的准备工作"""
        self.clear_screen()
    
    def clear_screen(self):
        """清空屏幕"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def do_open(self, arg):
        """打开文件进行编辑: open <文件名>"""
        if not arg:
            print("请指定文件名: open <文件名>")
            return
        
        filename = arg.strip()
        self.state['current_file'] = filename
        
        try:
            # 尝试打开现有文件
            with open(filename, 'r', encoding='utf-8') as f:
                self.state['content'] = f.readlines()
                # 移除每行末尾的换行符，保持与JS版本一致的处理方式
                self.state['content'] = [line.rstrip('\n') for line in self.state['content']]
            print(f"已打开文件: {filename}")
        except FileNotFoundError:
            # 创建新文件
            print(f"文件 {filename} 不存在，创建新文件")
            self.state['content'] = ['']  # 初始化至少有一行空内容
        
        # 初始化光标位置
        self.state['cursor'] = {'row': 0, 'col': 0}
        self.state['is_active'] = True
        self.state['clipboard'] = ''
        
        self.render_editor()
    
    def do_move(self, arg):
        """移动光标: 
        move left/right [数量]（默认1格）
        move start - 移动到当前行首
        move end - 移动到当前行尾"""
        if not self.state['is_active']:
            print("请先使用 open <文件名> 打开一个文件")
            return
            
        args = arg.split()
        if not args:
            print("请指定方向: move left/right [数量] 或 move start/end")
            return
        
        direction = args[0].lower()
        
        # 处理移动到行首或行尾的情况
        if direction == 'start':
            self.state['cursor']['col'] = 0
            self.render_editor()
            return
        elif direction == 'end':
            # 检查内容是否为空
            if not self.state['content']:
                self.state['cursor']['col'] = 0
            else:
                current_line = self.state['content'][self.state['cursor']['row']]
                self.state['cursor']['col'] = len(current_line)
            self.render_editor()
            return
        
        # 处理左右移动的情况
        count = int(args[1]) if len(args) > 1 else 1
        
        if count <= 0:
            print("数量必须是正整数")
            return
        
        # 检查内容是否为空
        if not self.state['content']:
            print("文件为空，无法移动光标")
            return
            
        current_line = self.state['content'][self.state['cursor']['row']]
        
        if direction == 'left':
            self.state['cursor']['col'] = max(0, self.state['cursor']['col'] - count)
        elif direction == 'right':
            self.state['cursor']['col'] = min(len(current_line), self.state['cursor']['col'] + count)
        else:
            print("方向必须是 left, right, start 或 end")
            return
        
        self.render_editor()
    
    def do_line(self, arg):
        """将光标移动到指定行: 
        line <行号> - 将光标移动到指定行
        line start - 将光标移动到第一行
        line end - 将光标移动到最后一行"""
        if not self.state['is_active']:
            print("请先使用 open <文件名> 打开一个文件")
            return
            
        # 检查内容是否为空
        if not self.state['content']:
            print("文件为空，没有可移动的行")
            return
            
        if not arg:
            print("请指定行号或位置: line <行号> 或 line start/end")
            return
        
        # 处理移动到第一行或最后一行
        if arg.lower() == 'start':
            self.state['cursor']['row'] = 0
            # 调整列位置到有效范围内
            line_length = len(self.state['content'][0])
            self.state['cursor']['col'] = min(self.state['cursor']['col'], line_length)
            self.render_editor()
            return
        elif arg.lower() == 'end':
            self.state['cursor']['row'] = len(self.state['content']) - 1
            # 调整列位置到有效范围内
            line_length = len(self.state['content'][self.state['cursor']['row']])
            self.state['cursor']['col'] = min(self.state['cursor']['col'], line_length)
            self.render_editor()
            return
        
        # 处理移动到指定行号
        try:
            line_num = int(arg.strip())
            if line_num < 1 or line_num > len(self.state['content']):
                print(f"行号必须在 1 到 {len(self.state['content'])} 之间")
                return
            
            # 转换为0-based索引
            self.state['cursor']['row'] = line_num - 1
            # 将光标移动到该行的最大可能位置
            line_length = len(self.state['content'][self.state['cursor']['row']])
            self.state['cursor']['col'] = min(self.state['cursor']['col'], line_length)
            
            self.render_editor()
        except ValueError:
            print("无效的命令参数，使用 line <行号> 或 line start/end")
    
    def do_break(self, arg):
        """在光标位置换行: break"""
        if not self.state['is_active']:
            print("请先使用 open <文件名> 打开一个文件")
            return
        
        # 检查内容是否为空，如果为空则添加一行
        if not self.state['content']:
            self.state['content'] = ['']
            self.state['cursor'] = {'row': 0, 'col': 0}
        
        current_row = self.state['cursor']['row']
        current_col = self.state['cursor']['col']
        
        # 确保当前行索引有效
        if current_row < 0 or current_row >= len(self.state['content']):
            print("光标位置无效")
            return
            
        current_line = self.state['content'][current_row]
        
        # 分割当前行
        line_part1 = current_line[:current_col]
        line_part2 = current_line[current_col:]
        
        # 更新内容
        self.state['content'][current_row] = line_part1
        self.state['content'].insert(current_row + 1, line_part2)
        
        # 移动光标到新行的开头
        self.state['cursor']['row'] = current_row + 1
        self.state['cursor']['col'] = 0
        
        self.render_editor()
    
    def do_write(self, arg):
        """在光标前写入内容: write <内容>"""
        if not self.state['is_active']:
            print("请先使用 open <文件名> 打开一个文件")
            return
            
        if not arg:
            print("请指定要写入的内容: write <内容>")
            return
        
        # 检查内容是否为空，如果为空则添加一行
        if not self.state['content']:
            self.state['content'] = ['']
            self.state['cursor'] = {'row': 0, 'col': 0}
        
        text = arg
        current_row = self.state['cursor']['row']
        current_col = self.state['cursor']['col']
        current_line = self.state['content'][current_row]
        
        # 在光标位置插入文本
        new_line = current_line[:current_col] + text + current_line[current_col:]
        self.state['content'][current_row] = new_line
        
        # 移动光标
        self.state['cursor']['col'] += len(text)
        
        self.render_editor()
    
    def do_space(self, arg):
        """插入空格: space [数量]（默认1个空格）"""
        if not self.state['is_active']:
            print("请先使用 open <文件名> 打开一个文件")
            return
            
        # 检查内容是否为空，如果为空则添加一行
        if not self.state['content']:
            self.state['content'] = ['']
            self.state['cursor'] = {'row': 0, 'col': 0}
        
        # 确定要插入的空格数量，默认为1
        try:
            count = int(arg.strip()) if arg else 1
            if count <= 0:
                print("数量必须是正整数")
                return
        except ValueError:
            print("无效的参数，使用 space [数量]（数量必须是正整数）")
            return
        
        # 生成指定数量的空格
        spaces = ' ' * count
        
        current_row = self.state['cursor']['row']
        current_col = self.state['cursor']['col']
        current_line = self.state['content'][current_row]
        
        # 在光标位置插入空格
        new_line = current_line[:current_col] + spaces + current_line[current_col:]
        self.state['content'][current_row] = new_line
        
        # 移动光标
        self.state['cursor']['col'] += count
        
        self.render_editor()
    
    def do_del(self, arg):
        """删除操作:
        del [数量] - 删除光标前指定数量字符（默认1个）
        del range all - 删除全部内容
        del range <开始> <结束> - 删除指定范围内容"""
        if not self.state['is_active']:
            print("请先使用 open <文件名> 打开一个文件")
            return
            
        # 检查内容是否为空
        if not self.state['content']:
            print("文件为空，没有可删除的内容")
            return
            
        args = arg.split()
        if not args:
            # 默认删除光标前一个字符
            self.delete_chars(1)
            return
        
        if args[0] == 'range':
            if len(args) < 2:
                print("请指定删除范围: del range <开始> <结束> 或 del range all")
                return
            
            if args[1] == 'all':
                # 删除全部内容
                self.state['content'] = ['']
                self.state['cursor'] = {'row': 0, 'col': 0}
                self.render_editor()
                return
            
            # 处理范围删除
            try:
                if len(args) == 3:
                    # 解析开始和结束列
                    start_col = int(args[1]) - 1  # 转换为0-based
                    end_col = int(args[2]) - 1
                    
                    if start_col < 0 or end_col < start_col:
                        print("无效的范围参数")
                        return
                    
                    current_row = self.state['cursor']['row']
                    current_line = self.state['content'][current_row]
                    
                    if end_col >= len(current_line):
                        print("结束位置超出行长度")
                        return
                    
                    # 删除范围内的字符
                    new_line = current_line[:start_col] + current_line[end_col+1:]
                    self.state['content'][current_row] = new_line
                    
                    # 调整光标位置
                    self.state['cursor']['col'] = min(start_col, len(new_line))
                else:
                    # 跨多行范围
                    # 解析开始位置 "行,列"
                    start_pos = args[1].split(',')
                    start_row = int(start_pos[0]) - 1
                    start_col = int(start_pos[1]) - 1
                    
                    # 解析结束位置 "行,列"
                    end_pos = args[2].split(',')
                    end_row = int(end_pos[0]) - 1
                    end_col = int(end_pos[1]) - 1
                    
                    if (start_row < 0 or end_row < start_row or 
                        end_row >= len(self.state['content'])):
                        print("无效的范围参数")
                        return
                    
                    # 处理单行范围
                    if start_row == end_row:
                        current_line = self.state['content'][start_row]
                        if (start_col < 0 or end_col < start_col or 
                            end_col >= len(current_line)):
                            print("无效的列范围")
                            return
                        
                        new_line = current_line[:start_col] + current_line[end_col+1:]
                        self.state['content'][start_row] = new_line
                        self.state['cursor'] = {'row': start_row, 'col': start_col}
                    else:
                        # 处理多行范围
                        # 1. 处理起始行
                        start_line = self.state['content'][start_row]
                        self.state['content'][start_row] = start_line[:start_col]
                        
                        # 2. 处理结束行
                        end_line = self.state['content'][end_row]
                        remaining_end_line = end_line[end_col+1:]
                        
                        # 3. 合并起始行和结束行剩余部分
                        self.state['content'][start_row] += remaining_end_line
                        
                        # 4. 删除中间行和结束行
                        del self.state['content'][start_row+1:end_row+1]
                        
                        # 5. 调整光标位置
                        self.state['cursor'] = {'row': start_row, 'col': start_col}
                
                self.render_editor()
            except (ValueError, IndexError):
                print("无效的范围参数格式")
            return
        
        # 处理删除指定数量的字符
        try:
            count = int(args[0])
            if count <= 0:
                print("数量必须是正整数")
                return
            
            self.delete_chars(count)
        except ValueError:
            print("数量必须是整数")
    
    def delete_chars(self, count: int):
        """删除光标前指定数量的字符"""
        current_row = self.state['cursor']['row']
        current_col = self.state['cursor']['col']
        
        if current_col == 0:
            # 光标在行首，合并到上一行
            if current_row == 0:
                print('已在文件开头，无法删除')
                return
            
            # 获取上一行内容
            prev_row = current_row - 1
            prev_line = self.state['content'][prev_row]
            current_line = self.state['content'][current_row]
            
            # 合并行
            self.state['content'][prev_row] = prev_line + current_line
            # 删除当前行
            del self.state['content'][current_row]
            # 移动光标到上一行末尾
            self.state['cursor'] = {
                'row': prev_row,
                'col': len(prev_line)
            }
        else:
            # 正常删除字符
            current_line = self.state['content'][current_row]
            delete_count = min(count, current_col)
            new_line = current_line[:current_col-delete_count] + current_line[current_col:]
            self.state['content'][current_row] = new_line
            self.state['cursor']['col'] -= delete_count
        
        self.render_editor()
    
    def do_copy(self, arg):
        """复制操作:
        copy - 复制全部内容
        copy range <开始> <结束> - 复制指定范围内容"""
        if not self.state['is_active']:
            print("请先使用 open <文件名> 打开一个文件")
            return
            
        # 检查内容是否为空
        if not self.state['content']:
            print("文件为空，没有可复制的内容")
            self.state['clipboard'] = ''
            return
            
        args = arg.split()
        if not args:
            # 复制全部内容
            self.state['clipboard'] = '\n'.join(self.state['content'])
            print('已复制全部内容到剪贴板')
            self.render_editor()
            return
        
        if args[0] == 'range' and len(args) >= 3:
            # 复制指定范围
            try:
                start_row, start_col, end_row, end_col = 0, 0, 0, 0
                
                if len(args) == 3:
                    # 同一行内的范围
                    start_row = self.state['cursor']['row']
                    end_row = self.state['cursor']['row']
                    start_col = int(args[1]) - 1
                    end_col = int(args[2]) - 1
                else:
                    # 跨多行范围
                    start_pos = args[1].split(',')
                    start_row = int(start_pos[0]) - 1
                    start_col = int(start_pos[1]) - 1
                    
                    end_pos = args[2].split(',')
                    end_row = int(end_pos[0]) - 1
                    end_col = int(end_pos[1]) - 1
                
                if (start_row < 0 or end_row < start_row or 
                    end_row >= len(self.state['content'])):
                    raise ValueError('无效的范围参数')
                
                copy_content = []
                
                if start_row == end_row:
                    # 单行复制
                    line = self.state['content'][start_row]
                    if start_col < 0 or end_col < start_col or end_col >= len(line):
                        raise ValueError('无效的列范围')
                    copy_content.append(line[start_col:end_col+1])
                else:
                    # 多行复制
                    # 起始行
                    start_line = self.state['content'][start_row]
                    copy_content.append(start_line[start_col:])
                    
                    # 中间行
                    for i in range(start_row + 1, end_row):
                        copy_content.append(self.state['content'][i])
                    
                    # 结束行
                    end_line = self.state['content'][end_row]
                    copy_content.append(end_line[:end_col+1])
                
                self.state['clipboard'] = '\n'.join(copy_content)
                print('已复制指定范围内容到剪贴板')
                self.render_editor()
            except (ValueError, IndexError):
                print('复制失败: 无效的范围参数')
            return
        
        print('无效的复制命令，使用 copy 或 copy range <范围>')
    
    def do_paste(self, arg):
        """粘贴操作:
        paste - 在光标前粘贴内容
        paste range <开始> <结束> - 剪切指定范围并粘贴"""
        if not self.state['is_active']:
            print("请先使用 open <文件名> 打开一个文件")
            return
            
        if not self.state['clipboard']:
            print('剪贴板为空')
            return
            
        # 检查内容是否为空，如果为空则添加一行
        if not self.state['content']:
            self.state['content'] = ['']
            self.state['cursor'] = {'row': 0, 'col': 0}
            
        args = arg.split()
        if not args:
            # 简单粘贴
            self.paste_content(self.state['clipboard'])
            return
            
        if args[0] == 'range' and len(args) >= 3:
            # 剪切指定范围并粘贴
            try:
                start_row, start_col, end_row, end_col = 0, 0, 0, 0
                
                if len(args) == 3:
                    # 同一行内的范围
                    start_row = self.state['cursor']['row']
                    end_row = self.state['cursor']['row']
                    start_col = int(args[1]) - 1
                    end_col = int(args[2]) - 1
                else:
                    # 跨多行范围
                    start_pos = args[1].split(',')
                    start_row = int(start_pos[0]) - 1
                    start_col = int(start_pos[1]) - 1
                    
                    end_pos = args[2].split(',')
                    end_row = int(end_pos[0]) - 1
                    end_col = int(end_pos[1]) - 1
                
                # 先保存要剪切的内容
                cut_content = []
                if start_row == end_row:
                    line = self.state['content'][start_row]
                    cut_content.append(line[start_col:end_col+1])
                else:
                    start_line = self.state['content'][start_row]
                    cut_content.append(start_line[start_col:])
                    
                    for i in range(start_row + 1, end_row):
                        cut_content.append(self.state['content'][i])
                    
                    end_line = self.state['content'][end_row]
                    cut_content.append(end_line[:end_col+1])
                
                cut_text = '\n'.join(cut_content)
                
                # 删除指定范围内容
                if start_row == end_row:
                    line = self.state['content'][start_row]
                    self.state['content'][start_row] = line[:start_col] + line[end_col+1:]
                    self.state['cursor'] = {'row': start_row, 'col': start_col}
                else:
                    start_line = self.state['content'][start_row]
                    self.state['content'][start_row] = start_line[:start_col]
                    
                    end_line = self.state['content'][end_row]
                    remaining_end_line = end_line[end_col+1:]
                    
                    self.state['content'][start_row] += remaining_end_line
                    del self.state['content'][start_row+1:end_row+1]
                    
                    self.state['cursor'] = {'row': start_row, 'col': start_col}
                
                # 粘贴剪切的内容
                self.state['clipboard'] = cut_text
                self.paste_content(cut_text)
                
                print('已剪切并粘贴指定范围内容')
                self.render_editor()
            except (ValueError, IndexError):
                print('剪切粘贴失败: 无效的范围参数')
            return
        
        print('无效的粘贴命令，使用 paste 或 paste range <范围>')
    
    def paste_content(self, content: str):
        """粘贴内容到光标位置"""
        lines = content.split('\n')
        current_row = self.state['cursor']['row']
        current_col = self.state['cursor']['col']
        current_line = self.state['content'][current_row]
        
        if len(lines) == 1:
            # 单行内容，直接插入
            new_line = current_line[:current_col] + lines[0] + current_line[current_col:]
            self.state['content'][current_row] = new_line
            self.state['cursor']['col'] += len(lines[0])
        else:
            # 多行内容，需要拆分处理
            # 1. 处理当前行
            first_line = lines[0]
            remaining_lines = lines[1:]
            new_current_line = current_line[:current_col] + first_line
            self.state['content'][current_row] = new_current_line
            
            # 2. 插入剩余行
            for i, line in enumerate(reversed(remaining_lines)):
                self.state['content'].insert(current_row + 1, line)
            
            # 3. 调整光标位置
            self.state['cursor']['row'] = current_row + len(remaining_lines)
            self.state['cursor']['col'] = len(remaining_lines[-1]) if remaining_lines else current_col + len(first_line)
        
        self.render_editor()
    
    def do_s(self, arg):
        """保存文件: s"""
        if not self.state['is_active']:
            print("请先使用 open <文件名> 打开一个文件")
            return
            
        if not self.state['current_file']:
            print('没有打开的文件')
            return
        
        try:
            with open(self.state['current_file'], 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.state['content']))
            print(f'文件 {self.state["current_file"]} 已保存')
            self.render_editor()
        except IOError as e:
            print(f'无法保存文件 {self.state["current_file"]}: {str(e)}')
    
    def do_q(self, arg):
        """退出编辑器（不保存）: q"""
        if not self.state['is_active']:
            print("没有打开的编辑器")
            return
            
        print("已退出编辑器，未保存的更改将丢失")
        self.state['is_active'] = False
        self.state['current_file'] = None
        self.prompt = 've> '
    
    def do_qs(self, arg):
        """保存并退出: qs"""
        if self.state['is_active']:
            # 保存文件
            try:
                with open(self.state['current_file'], 'w', encoding='utf-8') as f:
                    f.write('\n'.join(self.state['content']))
                print(f'文件 {self.state["current_file"]} 已保存')
            except IOError as e:
                print(f'无法保存文件 {self.state["current_file"]}: {str(e)}')
                return
                
            # 退出编辑器
            print("已保存并退出编辑器")
            self.state['is_active'] = False
            self.state['current_file'] = None
            self.prompt = 've> '
        else:
            print("没有打开的编辑器")
    
    def do_help(self, arg):
        """显示帮助信息: help"""
        print('=== ve编辑器命令帮助 ===')
        print('open <文件名>         - 打开文件进行编辑')
        print('move left/right [数量] - 移动光标（默认1格）')
        print('move start            - 移动光标到当前行首')
        print('move end              - 移动光标到当前行尾')
        print('line <行号>           - 将光标移动到指定行')
        print('line start            - 将光标移动到第一行')
        print('line end              - 将光标移动到最后一行')
        print('break                 - 在光标位置换行')
        print('write <内容>          - 在光标前写入内容')
        print('space [数量]          - 插入空格（默认1个）')
        print('del [数量]            - 删除光标前指定数量字符（默认1个）')
        print('del range all         - 删除全部内容')
        print('del range <开始> <结束> - 删除指定范围内容')
        print('copy                  - 复制全部内容')
        print('copy range <开始> <结束> - 复制指定范围内容')
        print('paste                 - 在光标前粘贴内容')
        print('paste range <开始> <结束> - 剪切指定范围并粘贴')
        print('q                     - 退出编辑器（不保存）')
        print('s                     - 保存文件')
        print('qs                    - 保存并退出')
        print('exit                  - 退出ve程序')
        
        if self.state['is_active']:
            self.render_editor()
    
    def do_exit(self, arg):
        """退出ve程序"""
        print("退出ve编辑器")
        return True
    
    def render_editor(self):
        """渲染编辑器界面"""
        if not self.state['is_active']:
            return
        
        self.clear_screen()
        
        # 显示文件名
        print(f"正在编辑: {self.state['current_file']}")
        print("-" * 40)
        
        # 计算最大行号的位数，用于对齐
        max_line_num = len(self.state['content'])
        max_digits = len(str(max_line_num)) if max_line_num > 0 else 1
        
        # 显示内容和行号
        for row_idx, line in enumerate(self.state['content']):
            # 行号显示，使用格式化确保对齐
            line_num = f"[{row_idx + 1:>{max_digits}}] "
            # 光标所在行
            if row_idx == self.state['cursor']['row']:
                # 插入光标
                cursor_pos = self.state['cursor']['col']
                line_with_cursor = line[:cursor_pos] + '█' + line[cursor_pos:]
                print(f"\033[94m{line_num}\033[0m{line_with_cursor}")  # 蓝色行号
            else:
                print(f"\033[94m{line_num}\033[0m{line}")  # 蓝色行号
        
        print("-" * 40)
        # 显示光标位置提示
        print(f"光标位置: 行 {self.state['cursor']['row'] + 1}, 列 {self.state['cursor']['col'] + 1} | 输入 help 查看命令")
        print(self.prompt, end='', flush=True)
    
    # 处理未知命令
    def default(self, line):
        print(f"未知命令: {line}")
        print("输入 help 查看可用命令")
        if self.state['is_active']:
            self.render_editor()

if __name__ == '__main__':
    editor = VeEditor()
    editor.cmdloop()
