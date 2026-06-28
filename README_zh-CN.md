# DragonMaster v0.3

RS:DragonWilds 存档管理器（角色 + 世界管理）

## 功能

- 📦 **背包编辑** — 108种物品 + 82种装备，中文名称下拉选择，支持批量填入
- 🔮 **符文管理** — 7种符文，一键快速符文包
- ⚔️ **装备栏配置** — 头盔/身体/腿甲/披风/饰品 5槽位
- 📊 **技能修改** — 9项技能经验值，一键MAX
- 💾 **备份系统** — 角色JSON + 世界SAV 备份/恢复/删除/重命名
- 🌍 **世界存档** — 浏览和备份世界存档文件
- 🎨 **RuneScape风格界面** — 经典棕金配色

## 使用方法

### 方式一：直接运行 exe（推荐）

下载 `dist/DragonMaster v0.3.exe`，双击运行。

### 方式二：Python 源码运行

```bash
pip install tkinter  # 通常 Python 自带
python main.py
```

### 操作步骤

1. 启动后自动弹出角色选择窗口，选择要编辑的角色 JSON 文件
   - 默认路径：`C:\Users\<用户名>\AppData\Local\RSDragonwilds\Saved\SaveCharacters`
   - 也可以点击"浏览存档文件夹"手动选择
2. 在背包/符文/装备栏标签页中编辑物品
3. 点击"💾 更新背包文件"保存
4. **⚠️ 必须在角色离线状态下操作！**

## 自定义存档路径

在 `main.py` 同目录创建 `.env` 文件：

```env
# 世界存档目录
RSDW_SAVEGAMES_DIR=D:\MySaves\SaveGames

# 角色存档目录
RSDW_SAVECHARACTERS_DIR=D:\MySaves\SaveCharacters

# 或统一指定根目录
RSDW_SAVED_DIR=E:\RSDragonwilds\Saved
```

## 备份说明

每个角色/世界都有独立的备份系统：
- **保存备份**：创建带时间戳的备份
- **加载备份**：恢复之前的备份（自动备份当前状态）
- **删除/重命名**：管理备份文件

## 注意事项

- ⚠️ **角色必须离线时编辑！**
- ⚠️ **使用前请备份存档文件！**
- 本工具仅修改本地 JSON 文件，不涉及网络操作

## 项目结构

```
DragonMaster/
├── main.py          # 主入口
├── .env             # 存档路径配置（可选）
├── src/
│   ├── data.py      # 物品/装备/符文/技能数据映射
│   ├── config.py    # 颜色常量 + 路径配置
│   ├── i18n.py      # 汉化字符串
│   └── backup.py    # 备份功能模块
├── dist/            # 编译后的 exe
└── README.md
```

## 致谢

- 原作者：[xxmowgli](https://github.com/xxmowgli)
- Discord：https://discord.gg/TeZvrV8728
- 捐赠：https://www.xxmowgli.co.uk
