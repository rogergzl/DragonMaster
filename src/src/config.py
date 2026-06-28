# DragonMaster — 配置模块
# 颜色常量 · 存档路径 · .env 加载

import os

# ── RuneScape 风格颜色 ──────────────────────────────────────────
RS_BROWN        = '#2B1810'   # 深棕背景
RS_GOLD         = '#FFD700'   # 金色强调文字
RS_TAN          = '#D2B48C'   # 棕褐面板背景
RS_DARK_TAN     = '#8B4513'   # 深棕按钮
RS_LIGHT_TAN    = '#F5DEB3'   # 浅棕输入框
RS_RED          = '#8B0000'   # 深红 / 警告
RS_GREEN        = '#006400'   # 深绿 / 成功
RS_EMPTY_BORDER = '#8B0000'   # 空格边框色（红）
RS_FILLED_BORDER = '#556B2F'  # 已填充边框色（绿）
RS_SELECTED_BORDER = '#FFD700'  # 选中边框色（金）

FONT_NAME = 'RuneScape UF'


def _load_dotenv():
    """从 main.py 同目录的 .env 加载 KEY=VALUE 到 os.environ。
    总是覆盖已有值 —— .env 是唯一配置来源。"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # _load_dotenv 在 config.py 中，main.py 在上级目录
    parent_dir = os.path.dirname(script_dir)
    dotenv_path = os.path.join(parent_dir, ".env")
    if not os.path.isfile(dotenv_path):
        return
    try:
        with open(dotenv_path, "r", encoding="utf-8") as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key:
                    os.environ[key] = value
        print(f"[config] Loaded .env from {dotenv_path}")
    except OSError as e:
        print(f"[config] Failed to read .env: {e}")


_load_dotenv()


def get_save_path(subfolder):
    """
    解析存档目录。优先级：.env → 默认路径。
    subfolder: "SaveCharacters" 或 "SaveGames"
    """
    env_map = {
        "SaveCharacters": "RSDW_SAVECHARACTERS_DIR",
        "SaveGames":      "RSDW_SAVEGAMES_DIR",
    }
    # 1. 子目录专属 key
    env_var = env_map.get(subfolder)
    if env_var:
        env_path = os.environ.get(env_var)
        if env_path:
            env_path = os.path.normpath(env_path)
            print(f"[config] Using env {env_var}: {env_path}")
            return env_path

    # 2. 基础 Saved 目录
    base_saved = os.environ.get("RSDW_SAVED_DIR")
    if base_saved:
        full_path = os.path.join(os.path.normpath(base_saved), subfolder)
        print(f"[config] Using env RSDW_SAVED_DIR + {subfolder}: {full_path}")
        return full_path

    # 3. 默认
    home_dir = os.path.expanduser("~")
    default_path = os.path.join(home_dir, "AppData", "Local", "RSDragonwilds", "Saved", subfolder)
    print(f"[config] Using default: {default_path}")
    return default_path


def get_default_save_path():
    """兼容包装：角色存档路径"""
    return get_save_path("SaveCharacters")
