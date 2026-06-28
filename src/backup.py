# DragonMaster — 备份模块
# 角色 JSON 与世界 SAV 的备份 / 恢复 / 删除 / 重命名

import os
import shutil
import time
import tkinter as tk
from tkinter import ttk, messagebox

from .config import RS_BROWN, RS_GOLD, RS_DARK_TAN, FONT_NAME

# 由 main.py 注入（避免循环导入）
_root = None           # tk.Tk 实例
_style_fn = None       # style_editor_window
_load_char_fn = None   # load_character


def inject(root, style_fn, load_char_fn):
    """main.py 启动时调用，注入依赖。"""
    global _root, _style_fn, _load_char_fn
    _root = root
    _style_fn = style_fn
    _load_char_fn = load_char_fn


# ── 角色备份 ────────────────────────────────────────────────────

def create_backup_controls(parent, file_path):
    """在 parent 内创建备份操作栏（保存/加载/删除/重命名）。"""
    backup_frame = tk.Frame(parent, bg=RS_BROWN)
    backup_frame.pack(fill="x", pady=2)

    save_btn = tk.Button(backup_frame, text="保存备份",
                         command=lambda: save_backup(file_path, backup_dropdown),
                         bg=RS_DARK_TAN, fg=RS_GOLD,
                         font=(FONT_NAME, 10), width=10)
    save_btn.pack(side="left", padx=5)

    backup_var = tk.StringVar()
    backup_dropdown = ttk.Combobox(backup_frame, textvariable=backup_var,
                                   state='readonly', width=20)
    backup_dropdown.pack(side="left", padx=5)

    load_btn = tk.Button(backup_frame, text="加载备份",
                         command=lambda: load_backup(backup_var.get(), file_path, backup_dropdown),
                         bg=RS_DARK_TAN, fg=RS_GOLD,
                         font=(FONT_NAME, 10), width=10)
    load_btn.pack(side="left", padx=5)

    delete_btn = tk.Button(backup_frame, text="删除",
                           command=lambda: delete_backup(file_path, backup_var.get(), backup_dropdown),
                           bg=RS_DARK_TAN, fg=RS_GOLD,
                           font=(FONT_NAME, 10), width=10)
    delete_btn.pack(side="left", padx=5)

    rename_btn = tk.Button(backup_frame, text="重命名",
                           command=lambda: rename_backup(file_path, backup_var.get(), backup_dropdown),
                           bg=RS_DARK_TAN, fg=RS_GOLD,
                           font=(FONT_NAME, 10), width=10)
    rename_btn.pack(side="left", padx=5)

    update_backup_list(file_path, backup_dropdown)
    return backup_frame


def _backup_dir_for(file_path):
    name = os.path.basename(file_path).replace(".json", "")
    return os.path.join(os.path.dirname(file_path), name)


def save_backup(file_path, dropdown):
    try:
        backup_dir = _backup_dir_for(file_path)
        os.makedirs(backup_dir, exist_ok=True)

        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        backup_path = os.path.join(backup_dir, timestamp)
        os.makedirs(backup_path)

        backup_file = os.path.join(backup_path, os.path.basename(file_path))
        shutil.copy2(file_path, backup_file)

        messagebox.showinfo("成功", f"备份已创建: {timestamp}")
        _refresh_dropdown(backup_dir, dropdown, timestamp)
    except Exception as e:
        messagebox.showerror("错误", f"创建备份失败: {e}")


def load_backup(backup_name, file_path, dropdown):
    if not backup_name:
        messagebox.showwarning("提示", "请先选择一个备份。")
        return
    try:
        backup_dir = _backup_dir_for(file_path)
        os.makedirs(backup_dir, exist_ok=True)

        # 先备份当前状态
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        pre_path = os.path.join(backup_dir, f"pre_load_{timestamp}")
        os.makedirs(pre_path)
        shutil.copy2(file_path, os.path.join(pre_path, os.path.basename(file_path)))

        # 恢复选中备份
        selected = os.path.join(backup_dir, backup_name, os.path.basename(file_path))
        if not os.path.exists(selected):
            messagebox.showerror("错误", f"备份文件不存在: {selected}")
            return
        shutil.copy2(selected, file_path)

        _refresh_dropdown(backup_dir, dropdown, backup_name)
        messagebox.showinfo("成功", f"备份已加载。当前状态已自动备份至 {timestamp}")

        if _load_char_fn:
            _load_char_fn(file_path)
    except Exception as e:
        messagebox.showerror("错误", f"加载备份失败: {e}")


def delete_backup(file_path, backup_name, dropdown):
    if not backup_name:
        messagebox.showwarning("提示", "请先选择一个备份。")
        return
    if not messagebox.askyesno("确认删除", f"确定要删除备份 \"{backup_name}\" 吗？"):
        return
    try:
        backup_dir = _backup_dir_for(file_path)
        shutil.rmtree(os.path.join(backup_dir, backup_name))
        messagebox.showinfo("成功", f"备份 \"{backup_name}\" 已删除。")
        _refresh_dropdown(backup_dir, dropdown, None)
    except Exception as e:
        messagebox.showerror("错误", f"删除备份失败: {e}")


def rename_backup(file_path, backup_name, dropdown):
    if not backup_name:
        messagebox.showwarning("提示", "请先选择一个备份。")
        return

    dialog = tk.Toplevel(_root)
    dialog.title("重命名备份")
    dialog.geometry("300x150")
    dialog.transient(_root)
    dialog.grab_set()
    if _style_fn:
        _style_fn(dialog)

    tk.Label(dialog, text="输入新名称:", bg=RS_BROWN, fg=RS_GOLD).pack(pady=10)
    new_name_var = tk.StringVar(value=backup_name)
    tk.Entry(dialog, textvariable=new_name_var, width=30).pack(pady=5)

    def do_rename():
        new_name = new_name_var.get().strip()
        if not new_name:
            messagebox.showwarning("提示", "名称不能为空。")
            return
        try:
            backup_dir = _backup_dir_for(file_path)
            old_path = os.path.join(backup_dir, backup_name)
            new_path = os.path.join(backup_dir, new_name)
            if os.path.exists(new_path):
                messagebox.showerror("错误", f"名称 \"{new_name}\" 已存在。")
                return
            os.rename(old_path, new_path)
            update_backup_list(file_path, dropdown)
            dropdown.set(new_name)
            messagebox.showinfo("成功", f"备份已重命名为 \"{new_name}\"。")
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"重命名失败: {e}")

    btn_frame = tk.Frame(dialog, bg=RS_BROWN)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="重命名", command=do_rename,
              bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10)).pack(side="left", padx=5)
    tk.Button(btn_frame, text="取消", command=dialog.destroy,
              bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10)).pack(side="left", padx=5)


def update_backup_list(file_path, dropdown):
    try:
        backup_dir = _backup_dir_for(file_path)
        _refresh_dropdown(backup_dir, dropdown, None)
    except Exception as e:
        print(f"更新备份列表出错: {e}")


# ── 世界备份 ────────────────────────────────────────────────────

def _world_backup_dir_for(file_path):
    name = os.path.basename(file_path).replace(".sav", "")
    return os.path.join(os.path.dirname(file_path), name)


def create_world_backup_controls(parent, file_path):
    backup_frame = tk.Frame(parent, bg=RS_BROWN)
    backup_frame.pack(fill="x", pady=2)

    save_btn = tk.Button(backup_frame, text="保存备份",
                         command=lambda: save_world_backup(file_path, backup_dropdown),
                         bg=RS_DARK_TAN, fg=RS_GOLD,
                         font=(FONT_NAME, 10), width=10)
    save_btn.pack(side="left", padx=5)

    backup_var = tk.StringVar()
    backup_dropdown = ttk.Combobox(backup_frame, textvariable=backup_var,
                                   state='readonly', width=20)
    backup_dropdown.pack(side="left", padx=5)

    load_btn = tk.Button(backup_frame, text="加载备份",
                         command=lambda: load_world_backup(backup_var.get(), file_path, backup_dropdown),
                         bg=RS_DARK_TAN, fg=RS_GOLD,
                         font=(FONT_NAME, 10), width=10)
    load_btn.pack(side="left", padx=5)

    delete_btn = tk.Button(backup_frame, text="删除",
                           command=lambda: delete_world_backup(file_path, backup_var.get(), backup_dropdown),
                           bg=RS_DARK_TAN, fg=RS_GOLD,
                           font=(FONT_NAME, 10), width=10)
    delete_btn.pack(side="left", padx=5)

    rename_btn = tk.Button(backup_frame, text="重命名",
                           command=lambda: rename_world_backup(file_path, backup_var.get(), backup_dropdown),
                           bg=RS_DARK_TAN, fg=RS_GOLD,
                           font=(FONT_NAME, 10), width=10)
    rename_btn.pack(side="left", padx=5)

    update_world_backup_list(file_path, backup_dropdown)
    return backup_frame


def save_world_backup(file_path, dropdown):
    try:
        backup_dir = _world_backup_dir_for(file_path)
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        backup_path = os.path.join(backup_dir, timestamp)
        os.makedirs(backup_path)
        shutil.copy2(file_path, os.path.join(backup_path, os.path.basename(file_path)))
        messagebox.showinfo("成功", f"世界备份已创建: {timestamp}")
        _refresh_dropdown(backup_dir, dropdown, timestamp)
    except Exception as e:
        messagebox.showerror("错误", f"创建世界备份失败: {e}")


def load_world_backup(backup_name, file_path, dropdown):
    if not backup_name:
        messagebox.showwarning("提示", "请先选择一个备份。")
        return
    try:
        backup_dir = _world_backup_dir_for(file_path)
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
        pre_path = os.path.join(backup_dir, f"pre_load_{timestamp}")
        os.makedirs(pre_path)
        shutil.copy2(file_path, os.path.join(pre_path, os.path.basename(file_path)))

        selected = os.path.join(backup_dir, backup_name, os.path.basename(file_path))
        if not os.path.exists(selected):
            messagebox.showerror("错误", f"备份文件不存在: {selected}")
            return
        shutil.copy2(selected, file_path)

        _refresh_dropdown(backup_dir, dropdown, backup_name)
        messagebox.showinfo("成功", f"世界备份已加载。当前状态已自动备份至 {timestamp}")
    except Exception as e:
        messagebox.showerror("错误", f"加载世界备份失败: {e}")


def delete_world_backup(file_path, backup_name, dropdown):
    if not backup_name:
        messagebox.showwarning("提示", "请先选择一个备份。")
        return
    if not messagebox.askyesno("确认删除", f"确定要删除备份 \"{backup_name}\" 吗？"):
        return
    try:
        backup_dir = _world_backup_dir_for(file_path)
        shutil.rmtree(os.path.join(backup_dir, backup_name))
        messagebox.showinfo("成功", f"备份 \"{backup_name}\" 已删除。")
        _refresh_dropdown(backup_dir, dropdown, None)
    except Exception as e:
        messagebox.showerror("错误", f"删除世界备份失败: {e}")


def rename_world_backup(file_path, backup_name, dropdown):
    if not backup_name:
        messagebox.showwarning("提示", "请先选择一个备份。")
        return

    dialog = tk.Toplevel(_root)
    dialog.title("重命名备份")
    dialog.geometry("300x150")
    dialog.transient(_root)
    dialog.grab_set()
    if _style_fn:
        _style_fn(dialog)

    tk.Label(dialog, text="输入新名称:", bg=RS_BROWN, fg=RS_GOLD).pack(pady=10)
    new_name_var = tk.StringVar(value=backup_name)
    tk.Entry(dialog, textvariable=new_name_var, width=30).pack(pady=5)

    def do_rename():
        new_name = new_name_var.get().strip()
        if not new_name:
            messagebox.showwarning("提示", "名称不能为空。")
            return
        try:
            backup_dir = _world_backup_dir_for(file_path)
            old_path = os.path.join(backup_dir, backup_name)
            new_path = os.path.join(backup_dir, new_name)
            if os.path.exists(new_path):
                messagebox.showerror("错误", f"名称 \"{new_name}\" 已存在。")
                return
            os.rename(old_path, new_path)
            update_world_backup_list(file_path, dropdown)
            dropdown.set(new_name)
            messagebox.showinfo("成功", f"备份已重命名为 \"{new_name}\"。")
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("错误", f"重命名失败: {e}")

    btn_frame = tk.Frame(dialog, bg=RS_BROWN)
    btn_frame.pack(pady=10)
    tk.Button(btn_frame, text="重命名", command=do_rename,
              bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10)).pack(side="left", padx=5)
    tk.Button(btn_frame, text="取消", command=dialog.destroy,
              bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10)).pack(side="left", padx=5)


def update_world_backup_list(file_path, dropdown):
    try:
        backup_dir = _world_backup_dir_for(file_path)
        _refresh_dropdown(backup_dir, dropdown, None)
    except Exception as e:
        print(f"更新世界备份列表出错: {e}")


# ── 内部工具 ────────────────────────────────────────────────────

def _refresh_dropdown(backup_dir, dropdown, select):
    if os.path.exists(backup_dir):
        backups = [d for d in os.listdir(backup_dir)
                   if os.path.isdir(os.path.join(backup_dir, d))]
        backups.sort(reverse=True)
        dropdown['values'] = backups
        if select and select in backups:
            dropdown.set(select)
        elif backups:
            dropdown.set(backups[0])
        else:
            dropdown.set('')
