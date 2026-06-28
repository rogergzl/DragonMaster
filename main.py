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
