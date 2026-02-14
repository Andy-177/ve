#!/usr/bin/env python3
"""
VisualEditor (ve) - 基于Textual 7.3.0的文本编辑器
"""

import sys
from pathlib import Path
from textual import on
from textual.app import App, ComposeResult
from textual.widgets import (
    Header, Footer, TextArea, Input
)
import asyncio


class VisualEditor(App):
    """VisualEditor 主应用"""

    TITLE = "未命名"
    SUB_TITLE = "编辑器"
    CSS = """
    #command-input {
        width: 100%;
        display: none;
        margin: 0 1;
    }
    #editor {
        width: 100%;
    }
    """
    BINDINGS = [
        ("ctrl+s", "save_file", "保存文件"),
        ("ctrl+t", "command_input", "命令框"),
        ("ctrl+l", "command_input", "命令框"),
        ("ctrl+q", "quit_app", "直接退出(不保存)"),
        ("shift+ctrl+q", "save_and_quit", "保存并退出"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_file: Path | None = None
        self.is_modified = False
        self.original_content = ""
        self.check_modified_task = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Input(id="command-input", placeholder="输入命令...")
        yield TextArea.code_editor(
            "",
            id="editor",
            show_line_numbers=True
        )
        yield Footer()

    def on_mount(self) -> None:
        self.editor = self.query_one("#editor", TextArea)
        self.command_input = self.query_one("#command-input", Input)
        self.original_content = self.editor.text

        if self.current_file:
            self.load_or_create_file(self.current_file)

        self.update_title()
        self.check_modified_task = asyncio.create_task(self.check_content_modified())

    async def check_content_modified(self):
        """定期检查内容是否被修改"""
        try:
            while True:
                await asyncio.sleep(0.5)
                current_content = self.editor.text
                if current_content != self.original_content:
                    if not self.is_modified:
                        self.is_modified = True
                        self.update_title()
                else:
                    if self.is_modified:
                        self.is_modified = False
                        self.update_title()
        except asyncio.CancelledError:
            pass

    def update_title(self):
        """只显示文件名，不显示路径"""
        if self.current_file:
            filename = self.current_file.name
            self.title = f"{filename}{'*' if self.is_modified else ''}"
        else:
            self.title = f"未命名{'*' if self.is_modified else ''}"
        self.sub_title = "编辑器"
        self.refresh()

    def load_or_create_file(self, file_path: Path) -> None:
        """加载已有文件或创建新文件"""
        try:
            abs_path = file_path.expanduser().resolve()

            if abs_path.exists() and abs_path.is_file():
                with open(abs_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.editor.text = content
                self.notify(f"已打开文件: {abs_path}", severity="success")
            else:
                self.editor.text = ""
                self.notify(f"已创建新文件: {abs_path}", severity="success")

            self.current_file = abs_path
            self.original_content = self.editor.text
            self.is_modified = False
            self.update_title()

        except Exception as e:
            self.notify(f"操作文件失败: {e}", severity="error")

    async def action_save_file(self) -> None:
        """保存当前文件"""
        if self.current_file is None:
            self.notify("请先通过 open 命令打开/创建文件或使用 save <path> 另存为", severity="warning")
            return

        try:
            self.current_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.current_file, "w", encoding="utf-8") as f:
                f.write(self.editor.text)
            self.is_modified = False
            self.original_content = self.editor.text
            self.update_title()
            self.notify(f"已保存文件: {self.current_file}", severity="success")
        except Exception as e:
            self.notify(f"保存失败: {e}", severity="error")

    async def save_as_file(self, file_path: Path) -> None:
        """另存为（直接覆盖）"""
        try:
            save_path = file_path.expanduser().resolve()
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(self.editor.text)

            self.current_file = save_path
            self.is_modified = False
            self.original_content = self.editor.text
            self.update_title()
            self.notify(f"已另存为: {save_path}", severity="success")
        except Exception as e:
            self.notify(f"另存为失败: {e}", severity="error")

    async def action_quit_app(self) -> None:
        """直接退出，不保存"""
        if self.check_modified_task:
            self.check_modified_task.cancel()
        self.exit()

    async def action_save_and_quit(self) -> None:
        """保存并退出"""
        if self.current_file is not None:
            await self.action_save_file()
        if self.check_modified_task:
            self.check_modified_task.cancel()
        self.exit()

    async def action_command_input(self) -> None:
        """显示/隐藏命令输入框"""
        if self.command_input.display:
            self.command_input.display = False
        else:
            self.command_input.display = True
            self.command_input.focus()

    @on(Input.Submitted, "#command-input")
    async def handle_command(self) -> None:
        """处理命令输入"""
        command_text = self.command_input.value.strip()
        self.command_input.value = ""
        if not command_text:
            return

        parts = command_text.split(maxsplit=1)
        command = parts[0].lower()

        if command == "open":
            if len(parts) < 2:
                self.notify("用法: open <path>", severity="warning")
                return
            file_path = Path(parts[1])
            self.load_or_create_file(file_path)

        elif command == "save":
            if len(parts) < 2:
                await self.action_save_file()
            else:
                await self.save_as_file(Path(parts[1]))

        elif command == "quit":
            await self.action_quit_app()

        else:
            self.notify(f"未知命令: {command}", severity="error")

def main():
    """主函数"""
    current_file = None
    if len(sys.argv) > 1:
        current_file = Path(sys.argv[1])

    app = VisualEditor()
    app.current_file = current_file
    app.run()

if __name__ == "__main__":
    main()
