import json
import os
import sys
import tkinter as tk
import secrets
from tkinter import filedialog, messagebox
from tkinter import ttk
import glob
import time

# 确保 src/ 在路径中（支持直接双击运行）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


from src.data    import (item_name_map, gear_name_map, rune_name_map,
                         skill_name_map, combined_map,
                         regular_items, gear_items, rune_items)
from src.config  import (RS_BROWN, RS_GOLD, RS_TAN, RS_DARK_TAN, RS_LIGHT_TAN,
                         RS_RED, RS_GREEN, RS_EMPTY_BORDER, RS_FILLED_BORDER,
                         RS_SELECTED_BORDER, FONT_NAME,
                         get_save_path, get_default_save_path)
from src.i18n    import T
from src.backup  import (create_backup_controls, create_world_backup_controls,
                         save_backup, load_backup, delete_backup, rename_backup,
                         update_backup_list,
                         save_world_backup, load_world_backup,
                         delete_world_backup, rename_world_backup,
                         update_world_backup_list,
                         inject as backup_inject)




# -- 全局状态（数据映射已迁移到 src/data.py）-------------------
json_files = []
current_inventory_data = {}
current_file_path = None
slot_entries = []
rune_entries = []
skill_labels = []
slot_checkboxes = []
loadout_entries = []

def update_slot_border(slot_frame, regular_var, gear_var):
    # Get the current item (gear takes precedence)
    current_item = gear_var.get() if gear_var.get() != "空" else regular_var.get()
    
    # Update border color based on whether slot has an item
    if current_item != "空":
        slot_frame.configure(bg=RS_FILLED_BORDER)
    else:
        slot_frame.configure(bg=RS_EMPTY_BORDER)

def update_current_item_label(label, regular_var, gear_var):
    # Get the current item (gear takes precedence)
    current_item = gear_var.get() if gear_var.get() != "空" else regular_var.get()
    label.configure(text=current_item)

def on_item_select(event, regular_var, gear_var, slot_frame, is_regular=True):
    # Clear the other dropdown when one is selected
    if is_regular:
        if regular_var.get() != "空":
            gear_var.set("空")
    else:
        if gear_var.get() != "空":
            regular_var.set("空")
    
    # Update the slot border
    update_slot_border(slot_frame, regular_var, gear_var)

def update_rune_slot_border(slot_frame, rune_var):
    # Update border color based on whether slot has a rune
    if rune_var.get() != "空":
        slot_frame.configure(bg=RS_FILLED_BORDER)
    else:
        slot_frame.configure(bg=RS_EMPTY_BORDER)

def update_current_rune_label(label, rune_var):
    label.configure(text=rune_var.get())

def on_rune_select(event, rune_var, slot_frame, current_rune_label):
    # Update the current rune label
    update_current_rune_label(current_rune_label, rune_var)
    # Update the slot border
    update_rune_slot_border(slot_frame, rune_var)

def load_json():
    show_character_selection()
