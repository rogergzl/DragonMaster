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

def set_all_slots():
    editor = tk.Toplevel(root)
    editor.title("Set All Slots")
    editor.geometry("300x250")
    style_editor_window(editor)

    combined_map = {**item_name_map, **gear_name_map}

    tk.Label(editor, text="统一设置所有格子", font=("Arial", 12, "bold")).pack(pady=5)

    tk.Label(editor, text="物品:").pack()
    item_var = tk.StringVar()
    item_choices = list(combined_map.values())
    item_dropdown = tk.OptionMenu(editor, item_var, *item_choices)
    item_dropdown.pack()

    tk.Label(editor, text="数量/耐久:").pack()
    count_entry = tk.Entry(editor)
    count_entry.pack()

    # Set default values
    item_var.set(item_choices[0])
    count_entry.insert(0, "1")

    def apply_all():
        item_name = item_var.get()
        count = count_entry.get()
        try:
            count = int(count)
        except:
            messagebox.showerror("Error", "Count must be a number.")
            return

        item_id = next((k for k, v in combined_map.items() if v == item_name), None)
        if not item_id:
            messagebox.showerror("Error", "Item not found.")
            return

        for i in range(32):
            guid = secrets.token_urlsafe(16)
            slot_key = str(i)
            if item_id in gear_name_map:
                current_inventory_data.setdefault("Inventory", {})[slot_key] = {
                    "GUID": guid,
                    "ItemData": item_id,
                    "Durability": count,
                    "VitalShield": 0
                }
            else:
                current_inventory_data.setdefault("Inventory", {})[slot_key] = {
                    "GUID": guid,
                    "ItemData": item_id,
                    "Count": count
                }

        editor.destroy()
        refresh_display()

    tk.Button(editor, text="✅ 应用到全部格子", command=apply_all).pack(pady=10)

def save_inventory_to_file():
    if not current_file_path or not current_inventory_data:
        messagebox.showwarning("No file", "No JSON file loaded.")
        return

    # Clear existing inventory data
    current_inventory_data["Inventory"] = {}
    
    # Save inventory entries (slots 0-31)
    for i, (regular_var, gear_var, count_entry, current_item_label) in enumerate(slot_entries):
        regular_item = regular_var.get()
        gear_item = gear_var.get()
        count_text = count_entry.get()
        
        # Determine which item to use (gear takes precedence if both are set)
        item_name = gear_item if gear_item != "空" else regular_item
        
        if item_name and item_name != "空":
            try:
                # Convert count to integer and ensure it's at least 1
                count = max(1, int(count_text))
                
                # Find the item ID from the name
                item_id = None
                if item_name in gear_name_map.values():
                    item_id = next((k for k, v in gear_name_map.items() if v.lower() == item_name.lower()), None)
                else:
                    item_id = next((k for k, v in item_name_map.items() if v.lower() == item_name.lower()), None)
                
                if item_id:
                    guid = secrets.token_urlsafe(16)
                    if item_id in gear_name_map:
                        current_inventory_data["Inventory"][str(i)] = {
                            "GUID": guid,
                            "ItemData": item_id,
                            "Durability": count,
                            "VitalShield": 0
                        }
                    else:
                        current_inventory_data["Inventory"][str(i)] = {
                            "GUID": guid,
                            "ItemData": item_id,
                            "Count": count
                        }
            except ValueError:
                continue

    # Save rune entries (slots 32-63)
    for i, (rune_var, count_entry, current_rune_label) in enumerate(rune_entries):
        rune_name = rune_var.get()
        count_text = count_entry.get()
        
        if rune_name and rune_name != "空":
            try:
                # Convert count to integer and ensure it's at least 1
                count = max(1, int(count_text))
                
                # Find the rune ID from the name
                rune_id = next((k for k, v in rune_name_map.items() if v.lower() == rune_name.lower()), None)
                
                if rune_id:
                    guid = secrets.token_urlsafe(16)
                    # Add VitalShield for Fire and Air runes
                    if rune_name in ["Fire Rune", "Air Rune"]:
                        current_inventory_data["Inventory"][str(i + 32)] = {
                            "GUID": guid,
                            "ItemData": rune_id,
                            "Count": count,
                            "VitalShield": 0
                        }
                    else:
                        current_inventory_data["Inventory"][str(i + 32)] = {
                            "GUID": guid,
                            "ItemData": rune_id,
                            "Count": count
                        }
            except ValueError:
                continue

    # Initialize Loadout if it doesn't exist
    if "Loadout" not in current_inventory_data:
        current_inventory_data["Loadout"] = {}
    
    print("\nSaving loadout items:")  # Debug print
    # Save loadout entries (slots 0-4)
    for i, (item_var, count_entry, current_item_label) in enumerate(loadout_entries):
        item_name = item_var.get()
        count_text = count_entry.get()
        
        print(f"Processing loadout slot {i}: {item_name}")  # Debug print
        
        if item_name and item_name != "空":
            try:
                # Convert count to integer and ensure it's at least 1
                count = max(1, int(count_text))
                
                # Find the item ID from the name (case-insensitive)
                item_id = next((k for k, v in gear_name_map.items() if v.lower() == item_name.lower()), None)
                
                if item_id:
                    guid = secrets.token_urlsafe(16)
                    current_inventory_data["Loadout"][str(i)] = {
                        "GUID": guid,
                        "ItemData": item_id,
                        "Durability": count,
                        "VitalShield": 0
                    }
                    print(f"Saved loadout slot {i} with item {item_name} (ID: {item_id})")  # Debug print
                else:
                    print(f"Could not find item ID for {item_name}")  # Debug print
            except ValueError as e:
                print(f"Error saving loadout slot {i}: {e}")  # Debug print
                continue
        else:
            # If slot is empty, remove it from the loadout data
            if str(i) in current_inventory_data["Loadout"]:
                del current_inventory_data["Loadout"][str(i)]
            print(f"Loadout slot {i} is empty")  # Debug print
    
    # Set MaxSlotIndex for loadout
    current_inventory_data["Loadout"]["MaxSlotIndex"] = 4

    # Find max slot index by checking all inventory slots
    max_slot_index = -1
    for slot_key in current_inventory_data["Inventory"].keys():
        try:
            slot_index = int(slot_key)
            if slot_index > max_slot_index:
                max_slot_index = slot_index
        except ValueError:
            continue

    print(f"Max slot index found: {max_slot_index}")  # Debug print

    # Set the MaxSlotIndex inside the Inventory object
    current_inventory_data["Inventory"]["MaxSlotIndex"] = max_slot_index

    # Save skills data
    if "Skills" not in current_inventory_data:
        current_inventory_data["Skills"] = {"Skills": []}
    else:
        current_inventory_data["Skills"]["Skills"] = []

    # ID to Name mapping for skills
    skill_names = {
        "Wf3i7Ha-B06DH719j1vtBw": "Artisan",
        "4pefO9k1lUqfA6mvHNi1SA": "Attack",
        "waK-8EyQFQ2xEjCGYmuTRQ": "Construction",
        "Tn7t6DQyX0-Q0cM5K7B90A": "Cooking",
        "0hreSMRVXUihq9qjDO2CFA": "Magic/Ranged",
        "jqX0Gh6QI0GFFPCDFK_CJQ": "Mining",
        "heq7u88Q2UuLXFqLGTVwQw": "Magic/Ranged",
        "NOqC-z-2ckqi0El22qMFlw": "Runecrafting",
        "4zYUGF5u_0KbMLkWJmmBbQ": "Woodcutting"
    }

    # Save current skills state from UI
    for row_frame in skill_labels:
        name_label = row_frame.winfo_children()[0]
        xp_entry = row_frame.winfo_children()[1]
        
        skill_name = name_label.cget("text").rstrip(":")
        xp_text = xp_entry.get()
        
        try:
            xp = int(xp_text)
            # For Magic/Ranged, save both IDs
            if skill_name == "Magic/Ranged":
                current_inventory_data["Skills"]["Skills"].extend([
                    {"Id": "0hreSMRVXUihq9qjDO2CFA", "Xp": xp},
                    {"Id": "heq7u88Q2UuLXFqLGTVwQw", "Xp": xp}
                ])
            else:
                # Find the skill ID from the name for other skills
                skill_id = next((k for k, v in skill_names.items() if v == skill_name), None)
                if skill_id:
                    current_inventory_data["Skills"]["Skills"].append({
                        "Id": skill_id,
                        "Xp": xp
                    })
        except ValueError:
            continue

    print("\nFinal loadout data:")  # Debug print
    print(json.dumps(current_inventory_data["Loadout"], indent=2))  # Debug print

    try:
        with open(current_file_path, 'w') as f:
            json.dump(current_inventory_data, f, indent=4)
        messagebox.showinfo("Success", "Inventory, runes, and skills updated and saved.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save file: {e}")

def save_preset():
    # Create a new data structure from current UI state
    preset_data = {
        "Inventory": {},
        "Loadout": {},
        "Skills": {"Skills": []}
    }
    
    # ID to Name mapping for skills
    skill_names = {
        "Wf3i7Ha-B06DH719j1vtBw": "Artisan",
        "4pefO9k1lUqfA6mvHNi1SA": "Attack",
        "waK-8EyQFQ2xEjCGYmuTRQ": "Construction",
        "Tn7t6DQyX0-Q0cM5K7B90A": "Cooking",
        "0hreSMRVXUihq9qjDO2CFA": "Magic/Ranged",
        "jqX0Gh6QI0GFFPCDFK_CJQ": "Mining",
        "heq7u88Q2UuLXFqLGTVwQw": "Magic/Ranged",
        "NOqC-z-2ckqi0El22qMFlw": "Runecrafting",
        "4zYUGF5u_0KbMLkWJmmBbQ": "Woodcutting"
    }
    
    # Save current inventory state from UI
    for i, (regular_var, gear_var, count_entry, current_item_label) in enumerate(slot_entries):
        regular_item = regular_var.get()
        gear_item = gear_var.get()
        count_text = count_entry.get()
        
        # Determine which item to use (gear takes precedence if both are set)
        item_name = gear_item if gear_item != "空" else regular_item
        
        if item_name and item_name != "空":
            try:
                count = int(count_text)
                # Find the item ID from the name
                item_id = None
                if item_name in gear_name_map.values():
                    item_id = next((k for k, v in gear_name_map.items() if v.lower() == item_name.lower()), None)
                else:
                    item_id = next((k for k, v in item_name_map.items() if v.lower() == item_name.lower()), None)
                
                if item_id:
                    guid = secrets.token_urlsafe(16)
                    if item_id in gear_name_map:
                        preset_data["Inventory"][str(i)] = {
                            "GUID": guid,
                            "ItemData": item_id,
                            "Durability": count,
                            "VitalShield": 0
                        }
                    else:
                        preset_data["Inventory"][str(i)] = {
                            "GUID": guid,
                            "ItemData": item_id,
                            "Count": count
                        }
            except ValueError:
                continue

    # Save current loadout state from UI
    for i, (item_var, count_entry, current_item_label) in enumerate(loadout_entries):
        item_name = item_var.get()
        count_text = count_entry.get()
        
        if item_name and item_name != "空":
            try:
                count = int(count_text)
                # Find the item ID from the name (case-insensitive)
                item_id = next((k for k, v in gear_name_map.items() if v.lower() == item_name.lower()), None)
                
                if item_id:
                    guid = secrets.token_urlsafe(16)
                    preset_data["Loadout"][str(i)] = {
                        "GUID": guid,
                        "ItemData": item_id,
                        "Durability": count,
                        "VitalShield": 0
                    }
            except ValueError:
                continue
    
    # Set MaxSlotIndex for loadout
    preset_data["Loadout"]["MaxSlotIndex"] = 4

    # Save current skills state from UI
    for row_frame in skill_labels:
        name_label = row_frame.winfo_children()[0]
        xp_entry = row_frame.winfo_children()[1]
        
        skill_name = name_label.cget("text").rstrip(":")
        xp_text = xp_entry.get()
        
        try:
            xp = int(xp_text)
            # For Magic/Ranged, save both IDs
            if skill_name == "Magic/Ranged":
                preset_data["Skills"]["Skills"].extend([
                    {"Id": "0hreSMRVXUihq9qjDO2CFA", "Xp": xp},
                    {"Id": "heq7u88Q2UuLXFqLGTVwQw", "Xp": xp}
                ])
            else:
                # Find the skill ID from the name for other skills
                skill_id = next((k for k, v in skill_names.items() if v == skill_name), None)
                if skill_id:
                    preset_data["Skills"]["Skills"].append({
                        "Id": skill_id,
                        "Xp": xp
                    })
        except ValueError:
            continue

    # Ask user where to save the preset
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        title="Save Preset"
    )
    
    if not file_path:
        return

    try:
        with open(file_path, 'w') as f:
            json.dump(preset_data, f, indent=4)
        messagebox.showinfo("Success", "Preset saved successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save preset: {e}")

def load_preset():
    # Ask user to select a preset file
    file_path = filedialog.askopenfilename(
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        title="Load Preset"
    )
    
    if not file_path:
        return

    try:
        # Load the preset data
        with open(file_path, 'r') as f:
            preset_data = json.load(f)
        
        # ID to Name mapping for skills
        skill_names = {
            "Wf3i7Ha-B06DH719j1vtBw": "Artisan",
            "4pefO9k1lUqfA6mvHNi1SA": "Attack",
            "waK-8EyQFQ2xEjCGYmuTRQ": "Construction",
            "Tn7t6DQyX0-Q0cM5K7B90A": "Cooking",
            "0hreSMRVXUihq9qjDO2CFA": "Magic/Ranged",
            "jqX0Gh6QI0GFFPCDFK_CJQ": "Mining",
            "heq7u88Q2UuLXFqLGTVwQw": "Magic/Ranged",
            "NOqC-z-2ckqi0El22qMFlw": "Runecrafting",
            "4zYUGF5u_0KbMLkWJmmBbQ": "Woodcutting"
        }
        
        # Clear current UI state and set all borders to red
        for i, (regular_var, gear_var, count_entry, current_item_label) in enumerate(slot_entries):
            regular_var.set("空")
            gear_var.set("空")
            count_entry.delete(0, tk.END)
            count_entry.insert(0, "0")
            current_item_label.configure(text="空")
            
            # Set all slot borders to red initially
            slot_frame = inventory_frame.grid_slaves(row=i // 8, column=i % 8)[0]
            slot_frame.configure(bg=RS_EMPTY_BORDER)
        
        # Clear loadout entries
        for item_var, count_entry, current_item_label in loadout_entries:
            item_var.set("空")
            count_entry.delete(0, tk.END)
            count_entry.insert(0, "0")
            current_item_label.configure(text="空")
            
            # Set all loadout slot borders to red initially
            slot_frame = loadout_frame.grid_slaves(row=loadout_entries.index((item_var, count_entry, current_item_label)) // 3, 
                                                 column=loadout_entries.index((item_var, count_entry, current_item_label)) % 3)[0]
            slot_frame.configure(bg=RS_EMPTY_BORDER)
        
        # Load inventory data to UI
        for slot_str, item in preset_data.get("Inventory", {}).items():
            try:
                slot_index = int(slot_str)
                if 0 <= slot_index < 32:
                    item_id = item.get("ItemData", "Unknown ID")
                    item_name = None
                    
                    # Find item name from ID
                    if item_id in gear_name_map:
                        item_name = gear_name_map[item_id]
                    elif item_id in item_name_map:
                        item_name = item_name_map[item_id]
                    
                    if item_name:
                        regular_var, gear_var, count_entry, current_item_label = slot_entries[slot_index]
                        
                        # Set the appropriate dropdown based on item type
                        if item_id in gear_name_map:
                            gear_var.set(item_name)
                            regular_var.set("空")
                            count_entry.delete(0, tk.END)
                            count_entry.insert(0, str(item.get("Durability", 0)))
                        else:
                            regular_var.set(item_name)
                            gear_var.set("空")
                            count_entry.delete(0, tk.END)
                            count_entry.insert(0, str(item.get("Count", 0)))
                        
                        # Update the current item label
                        current_item_label.configure(text=item_name)
                        
                        # Update the slot border to green for filled slots
                        slot_frame = inventory_frame.grid_slaves(row=slot_index // 8, column=slot_index % 8)[0]
                        slot_frame.configure(bg=RS_FILLED_BORDER)
            except Exception as e:
                print(f"Error loading slot {slot_str}: {e}")
                continue
        
        # Load loadout data to UI
        for slot_str, item in preset_data.get("Loadout", {}).items():
            try:
                slot_index = int(slot_str)
                if 0 <= slot_index < 5:  # Loadout slots 0-4
                    item_id = item.get("ItemData", "Unknown ID")
                    item_name = gear_name_map.get(item_id, f"Unknown Item ({item_id})")
                    
                    item_var, count_entry, current_item_label = loadout_entries[slot_index]
                    item_var.set(item_name)
                    
                    durability = item.get("Durability", "???")
                    count_entry.delete(0, tk.END)
                    count_entry.insert(0, str(durability))
                    
                    current_item_label.configure(text=item_name)
                    
                    # Update the slot border
                    slot_frame = loadout_frame.grid_slaves(row=slot_index // 3, column=slot_index % 3)[0]
                    slot_frame.configure(bg=RS_FILLED_BORDER)
            except ValueError as e:
                if slot_str != "MaxSlotIndex":  # Skip MaxSlotIndex as it's not a slot
                    print(f"Error loading loadout slot {slot_str}: {e}")
                continue
        
        # Load skills data to UI
        for skill in preset_data.get("Skills", {}).get("Skills", []):
            skill_id = skill.get("Id")
            xp = skill.get("Xp", 0)
            
            # Find the skill row with matching ID
            for row_frame in skill_labels:
                name_label = row_frame.winfo_children()[0]
                xp_entry = row_frame.winfo_children()[1]
                
                # Check both Magic/Ranged IDs
                if (skill_names.get(skill_id) == name_label.cget("text").rstrip(":") or
                    (skill_id in ["0hreSMRVXUihq9qjDO2CFA", "heq7u88Q2UuLXFqLGTVwQw"] and 
                     name_label.cget("text").rstrip(":") == "Magic/Ranged")):
                    xp_entry.delete(0, tk.END)
                    xp_entry.insert(0, str(xp))
                    break
        
        messagebox.showinfo("Success", "Preset loaded successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load preset: {e}")

def refresh_display():
    combined_map = {**item_name_map, **gear_name_map}
    
    # Clear all entries and update borders
    for i, (regular_var, gear_var, count_entry, current_item_label) in enumerate(slot_entries):
        regular_var.set("空")
        gear_var.set("空")
        count_entry.delete(0, tk.END)
        count_entry.insert(0, "0")
        current_item_label.configure(text="空")
        
        # Update the slot border to red for empty slots
        slot_frame = inventory_frame.grid_slaves(row=i // 8, column=i % 8)[0]
        slot_frame.configure(bg=RS_EMPTY_BORDER)
    
    # Clear rune entries
    for rune_var, count_entry, current_rune_label in rune_entries:
        rune_var.set("空")
        count_entry.delete(0, tk.END)
        count_entry.insert(0, "0")
        current_rune_label.configure(text="空")
        
        # Update the slot border to red for empty slots
        slot_frame = rune_frame.grid_slaves(row=rune_entries.index((rune_var, count_entry, current_rune_label)) // 8, 
                                          column=rune_entries.index((rune_var, count_entry, current_rune_label)) % 8)[0]
        slot_frame.configure(bg=RS_EMPTY_BORDER)

    # Clear loadout entries
    for item_var, count_entry, current_item_label in loadout_entries:
        item_var.set("空")
        count_entry.delete(0, tk.END)
        count_entry.insert(0, "0")
        current_item_label.configure(text="空")
        
        # Update the slot border to red for empty slots
        slot_frame = loadout_frame.grid_slaves(row=loadout_entries.index((item_var, count_entry, current_item_label)) // 3, 
                                             column=loadout_entries.index((item_var, count_entry, current_item_label)) % 3)[0]
        slot_frame.configure(bg=RS_EMPTY_BORDER)

    # Update inventory entries
    for slot_str, item in current_inventory_data.get("Inventory", {}).items():
        try:
            slot_index = int(slot_str)
            if 0 <= slot_index < 32:  # Regular inventory slots
                item_id = item.get("ItemData", "Unknown ID")
                item_name = combined_map.get(item_id, f"Unknown Item ({item_id})")
                
                regular_var, gear_var, count_entry, current_item_label = slot_entries[slot_index]
                
                # Set the appropriate dropdown based on item type
                if item_id in gear_name_map:
                    gear_var.set(item_name)
                    regular_var.set("空")
                else:
                    regular_var.set(item_name)
                    gear_var.set("空")
                
                # Update the current item label
                current_item_label.configure(text=item_name)
                
                # Update the slot border to green for filled slots
                slot_frame = inventory_frame.grid_slaves(row=slot_index // 8, column=slot_index % 8)[0]
                slot_frame.configure(bg=RS_FILLED_BORDER)

                if item_id in gear_name_map:
                    durability = item.get("Durability", "???")
                    count_entry.delete(0, tk.END)
                    count_entry.insert(0, str(durability))
                else:
                    count = item.get("Count", 0)
                    count_entry.delete(0, tk.END)
                    count_entry.insert(0, str(count))
            elif 32 <= slot_index < 64:  # Rune slots
                item_id = item.get("ItemData", "Unknown ID")
                rune_name = rune_name_map.get(item_id, f"Unknown Rune ({item_id})")
                count = item.get("Count", 0)
                
                rune_index = slot_index - 32
                if 0 <= rune_index < len(rune_entries):
                    rune_var, count_entry, current_rune_label = rune_entries[rune_index]
                    rune_var.set(rune_name)
                    count_entry.delete(0, tk.END)
                    count_entry.insert(0, str(count))
                    current_rune_label.configure(text=rune_name)
                    
                    # Update the slot border
                    slot_frame = rune_frame.grid_slaves(row=rune_index // 8, column=rune_index % 8)[0]
                    slot_frame.configure(bg=RS_FILLED_BORDER)
        except Exception as e:
            print(f"Error updating slot {slot_str}: {e}")
            continue

    # Update loadout entries
    for slot_str, item in current_inventory_data.get("Loadout", {}).items():
        try:
            slot_index = int(slot_str)
            if 0 <= slot_index < 5:  # Loadout slots 0-4
                item_id = item.get("ItemData", "Unknown ID")
                item_name = gear_name_map.get(item_id, f"Unknown Item ({item_id})")
                
                item_var, count_entry, current_item_label = loadout_entries[slot_index]
                item_var.set(item_name)
                
                durability = item.get("Durability", "???")
                count_entry.delete(0, tk.END)
                count_entry.insert(0, str(durability))
                
                current_item_label.configure(text=item_name)
                
                # Update the slot border
                slot_frame = loadout_frame.grid_slaves(row=slot_index // 3, column=slot_index % 3)[0]
                slot_frame.configure(bg=RS_FILLED_BORDER)
                
                print(f"Updated loadout slot {slot_index} with {item_name}")  # Debug print
        except ValueError as e:
            if slot_str != "MaxSlotIndex":  # Skip MaxSlotIndex as it's not a slot
                print(f"Error updating loadout slot {slot_str}: {e}")
            continue
    
    # Refresh skills display
    refresh_skills_display()

def refresh_skills_display():
    for label in skill_labels:
        label.destroy()
    skill_labels.clear()

    for widget in skills_display_frame.winfo_children():
        widget.destroy()

    # Get skills data from current_inventory_data
    skills_data = current_inventory_data.get("Skills", {}).get("Skills", [])

    # ID to Name mapping
    skill_names = {
        "Wf3i7Ha-B06DH719j1vtBw": "Artisan",
        "4pefO9k1lUqfA6mvHNi1SA": "Attack",
        "waK-8EyQFQ2xEjCGYmuTRQ": "Construction",
        "Tn7t6DQyX0-Q0cM5K7B90A": "Cooking",
        "0hreSMRVXUihq9qjDO2CFA": "Magic/Ranged",
        "jqX0Gh6QI0GFFPCDFK_CJQ": "Mining",
        "heq7u88Q2UuLXFqLGTVwQw": "Magic/Ranged",
        "NOqC-z-2ckqi0El22qMFlw": "Runecrafting",
        "4zYUGF5u_0KbMLkWJmmBbQ": "Woodcutting"
    }

    # Track which skills we've displayed
    displayed_skills = set()

    # Display all skills
    for skill in skills_data:
        skill_id = skill.get("Id", "Unknown")
        xp = skill.get("Xp", 0)
        skill_name = skill_names.get(skill_id, "Unknown")

        # Skip if we've already displayed this skill (except for Magic/Ranged)
        if skill_name in displayed_skills and skill_id not in ["0hreSMRVXUihq9qjDO2CFA", "heq7u88Q2UuLXFqLGTVwQw"]:
            continue

        # For Magic/Ranged, only skip if we've already displayed both IDs
        if skill_id in ["0hreSMRVXUihq9qjDO2CFA", "heq7u88Q2UuLXFqLGTVwQw"]:
            if "0hreSMRVXUihq9qjDO2CFA" in displayed_skills and "heq7u88Q2UuLXFqLGTVwQw" in displayed_skills:
                continue

        displayed_skills.add(skill_id)

        row_frame = tk.Frame(skills_display_frame, bg=RS_LIGHT_TAN)
        row_frame.pack(fill="x", pady=2)

        # Skill name label
        name_label = tk.Label(row_frame, text=f"{skill_name}:", 
                            width=15, anchor="w",
                            bg=RS_LIGHT_TAN, fg='black',
                            font=(FONT_NAME, 9))
        name_label.pack(side="left")

        # XP entry
        xp_entry = tk.Entry(row_frame, width=10,
                          bg=RS_LIGHT_TAN, fg='black',
                          font=(FONT_NAME, 9))
        xp_entry.insert(0, str(xp))
        xp_entry.pack(side="left", padx=5)

        # MAX button
        def set_max_xp(entry=xp_entry):
            entry.delete(0, tk.END)
            entry.insert(0, "55000")

        max_button = tk.Button(row_frame, text=T["btn_max"],
                             command=lambda e=xp_entry: set_max_xp(e),
                             bg=RS_DARK_TAN, fg=RS_GOLD,
                             font=(FONT_NAME, 8, 'bold'),
                             width=4)
        max_button.pack(side="left", padx=2)

        skill_labels.append(row_frame)

def style_editor_window(window):
    window.configure(bg=RS_BROWN)
    for widget in window.winfo_children():
        if isinstance(widget, tk.Label):
            widget.configure(bg=RS_BROWN, fg=RS_GOLD, font=(FONT_NAME, 10))
        elif isinstance(widget, tk.Button):
            widget.configure(bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10, 'bold'))
        elif isinstance(widget, tk.Entry):
            widget.configure(bg=RS_LIGHT_TAN, fg='black', font=(FONT_NAME, 10))
        elif isinstance(widget, tk.OptionMenu):
            widget.configure(bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10))

def insert_to_checked_slots():
    # Get the selected item and count from the combobox
    item_name = item_dropdown.get()  # Changed from item_var.get() to item_dropdown.get()
    count_text = count_var.get()
    
    print(f"\nSelected item: '{item_name}'")  # Debug print with quotes to see spaces
    print(f"Selected count: {count_text}")  # Debug print
    
    if item_name == "空":
        messagebox.showerror("Error", "Please select an item from the dropdown.")
        return
    
    try:
        count = int(count_text)
    except ValueError:
        messagebox.showerror("Error", "Count must be a number.")
        return
    
    # Find the item ID from the name (case-insensitive)
    item_id = None
    
    # Debug prints for item lookup
    print("\nChecking gear_name_map:")
    print("Available gear items:")
    for k, v in gear_name_map.items():
        print(f"  '{v}'")
        if v.lower() == item_name.lower():
            print(f"Found match: '{v}' -> {k}")
            item_id = k
            break
    
    if not item_id:
        print("\nChecking item_name_map:")
        print("Available regular items:")
        for k, v in item_name_map.items():
            print(f"  '{v}'")
            if v.lower() == item_name.lower():
                print(f"Found match: '{v}' -> {k}")
                item_id = k
                break
    
    if not item_id:
        print(f"\nNo match found for '{item_name}'")
        messagebox.showerror("Error", f"Item not found: '{item_name}'")
        return
    
    print(f"\nFound item_id: {item_id}")
    
    # Update all checked slots
    checked_count = 0
    for i, (checkbox, slot_frame) in enumerate(zip(slot_checkboxes, inventory_frame.grid_slaves())):
        if checkbox.get():
            checked_count += 1
            print(f"Updating checked slot {i}")
            regular_var, gear_var, count_entry, current_item_label = slot_entries[i]
            
            # Get the exact name from the map to ensure case matches
            exact_name = gear_name_map.get(item_id) if item_id in gear_name_map else item_name_map.get(item_id)
            if not exact_name:
                print(f"Warning: Could not find exact name for item_id {item_id}")
                exact_name = item_name
            
            if item_id in gear_name_map:
                gear_var.set(exact_name)
                regular_var.set("空")
                print(f"Set as gear item: '{exact_name}'")
            else:
                regular_var.set(exact_name)
                gear_var.set("空")
                print(f"Set as regular item: '{exact_name}'")
            
            count_entry.delete(0, tk.END)
            count_entry.insert(0, str(count))
            current_item_label.configure(text=exact_name)
            
            # Update the slot border
            slot_frame.configure(bg=RS_FILLED_BORDER)
    
    print(f"Updated {checked_count} slots")

def toggle_checkbox(slot_frame, checkbox_var):
    # Toggle the checkbox state
    checkbox_var.set(not checkbox_var.get())
    
    # Get the slot index from the frame's grid info
    grid_info = slot_frame.grid_info()
    slot_index = grid_info['row'] * 8 + grid_info['column']
    
    # Get the current item state from slot_entries
    regular_var, gear_var, _, _ = slot_entries[slot_index]
    regular_item = regular_var.get()
    gear_item = gear_var.get()
    current_item = gear_item if gear_item != "空" else regular_item
    
    # Debug print
    print(f"Toggle Slot {slot_index}: Regular={regular_item}, Gear={gear_item}, Current={current_item}")
    
    # Update the border color based on selection and item state
    if checkbox_var.get():
        slot_frame.configure(bg=RS_SELECTED_BORDER)
        print(f"Setting slot {slot_index} to gold (selected)")
    else:
        # Set border color based on whether slot is empty
        if current_item != "空":
            slot_frame.configure(bg=RS_FILLED_BORDER)
            print(f"Setting slot {slot_index} to green (filled)")
        else:
            slot_frame.configure(bg=RS_EMPTY_BORDER)
            print(f"Setting slot {slot_index} to red (empty)")

def clear_all_selections():
    # Clear all checkboxes and reset borders
    for i in range(32):  # We know we have 32 slots
        checkbox_var = slot_checkboxes[i]
        checkbox_var.set(False)
        
        # Get the slot frame directly using grid coordinates
        slot_frame = inventory_frame.grid_slaves(row=i // 8, column=i % 8)[0]
        
        # Get the current item state
        regular_var, gear_var, _, _ = slot_entries[i]
        regular_item = regular_var.get()
        gear_item = gear_var.get()
        current_item = gear_item if gear_item != "空" else regular_item
        
        # Debug print
        print(f"Slot {i}: Regular={regular_item}, Gear={gear_item}, Current={current_item}")
        
        # Set border color based on whether slot is empty
        if current_item != "空":
            slot_frame.configure(bg=RS_FILLED_BORDER)
            print(f"Setting slot {i} to green (filled)")
        else:
            slot_frame.configure(bg=RS_EMPTY_BORDER)
            print(f"Setting slot {i} to red (empty)")

def load_rune_pack():
    # Define rune slots in order (only the ones we want to load)
    rune_order = [
        "Air Rune",
        "Water Rune",
        "Earth Rune",
        "Fire Rune",
        "Nature Rune",
        "Law Rune",
        "Astral Rune"
    ]
    
    # Clear existing runes first
    for rune_var, count_entry, _ in rune_entries:
        rune_var.set("空")
        count_entry.delete(0, tk.END)
        count_entry.insert(0, "0")
    
    # Set each rune slot
    for i, rune_name in enumerate(rune_order):
        if i < len(rune_entries):
            rune_var, count_entry, current_rune_label = rune_entries[i]
            rune_var.set(rune_name)
            count_entry.delete(0, tk.END)
            count_entry.insert(0, "9999")
            current_rune_label.configure(text=rune_name)
            
            # Update the slot border
            slot_frame = rune_frame.grid_slaves(row=i // 8, column=i % 8)[0]
            slot_frame.configure(bg=RS_FILLED_BORDER)

def clear_all_runes():
    for i, (rune_var, count_entry, current_rune_label) in enumerate(rune_entries):
        rune_var.set("空")
        count_entry.delete(0, tk.END)
        count_entry.insert(0, "0")
        current_rune_label.configure(text="空")
        
        # Update the slot border
        slot_frame = rune_frame.grid_slaves(row=i // 8, column=i % 8)[0]
        slot_frame.configure(bg=RS_EMPTY_BORDER)

def clear_all_backpack_slots():
    for i, (regular_var, gear_var, count_entry, current_item_label) in enumerate(slot_entries):
        regular_var.set("空")
        gear_var.set("空")
        count_entry.delete(0, tk.END)
        count_entry.insert(0, "0")
        current_item_label.configure(text="空")
        
        # Update the slot border
        slot_frame = inventory_frame.grid_slaves(row=i // 8, column=i % 8)[0]
        slot_frame.configure(bg=RS_EMPTY_BORDER)

# Add this after the imports but before the item maps


def show_character_selection():
    # Create a new window for character selection
    selection_window = tk.Toplevel(root)
    selection_window.title("Select Character")
    selection_window.geometry("600x600")
    selection_window.transient(root)
    selection_window.grab_set()
    style_editor_window(selection_window)
    
    # Add a title label
    title_label = tk.Label(selection_window, 
                          text=T["select_char"],
                          font=(FONT_NAME, 16, 'bold'),
                          bg=RS_BROWN,
                          fg=RS_GOLD)
    title_label.pack(pady=10)
    
    # Create a canvas with scrollbar
    canvas = tk.Canvas(selection_window, bg=RS_BROWN)
    scrollbar = ttk.Scrollbar(selection_window, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=RS_BROWN)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Pack the canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True, padx=20, pady=10)
    scrollbar.pack(side="right", fill="y")
    
    # Add browse button at the top
    browse_button = tk.Button(scrollable_frame,
                            text=T["btn_browse_folder"],
                            command=lambda: browse_for_folder(scrollable_frame),
                            bg=RS_DARK_TAN,
                            fg=RS_GOLD,
                            font=(FONT_NAME, 12, 'bold'),
                            width=25,
                            height=2)
    browse_button.pack(pady=10)
    
    # Try to load files from default location
    default_path = get_default_save_path()
    if os.path.exists(default_path):
        # Find all JSON files in the default path, excluding copies
        json_files = [f for f in glob.glob(os.path.join(default_path, "*.json")) 
                     if not any(copy_text in f.lower() for copy_text in ["- copy", "-copy"])]
        json_files.sort(key=os.path.getmtime, reverse=True)
        
        # Add a button for each file
        for file in json_files:
            # Create a frame for the character button and backup controls
            char_frame = tk.Frame(scrollable_frame, bg=RS_BROWN)
            char_frame.pack(fill="x", pady=5)
            
            # Character button
            file_name = os.path.basename(file).replace(".json", "")
            btn = tk.Button(char_frame,
                          text=file_name,
                          command=lambda f=file: load_character(f),
                          bg=RS_DARK_TAN,
                          fg=RS_GOLD,
                          font=(FONT_NAME, 12),
                          width=30,
                          height=2)
            btn.pack(pady=5)
            
            # Add backup controls
            create_backup_controls(char_frame, file)


def browse_for_folder(scrollable_frame):
    """Let the user pick a folder and reload the character list from it."""
    folder = filedialog.askdirectory(title="Select SaveCharacters Folder")
    if not folder:
        return

    # Clear existing file entries (keep the browse button 鈥?it's the first child)
    children = list(scrollable_frame.winfo_children())
    for child in children[1:]:  # skip browse_button at index 0
        child.destroy()

    if not os.path.exists(folder):
        return

    json_files = [f for f in glob.glob(os.path.join(folder, "*.json"))
                  if not any(copy_text in f.lower() for copy_text in ["- copy", "-copy"])]
    json_files.sort(key=os.path.getmtime, reverse=True)

    for file in json_files:
        char_frame = tk.Frame(scrollable_frame, bg=RS_BROWN)
        char_frame.pack(fill="x", pady=5)

        file_name = os.path.basename(file).replace(".json", "")
        btn = tk.Button(char_frame,
                        text=file_name,
                        command=lambda f=file: load_character(f),
                        bg=RS_DARK_TAN,
                        fg=RS_GOLD,
                        font=(FONT_NAME, 12),
                        width=30,
                        height=2)
        btn.pack(pady=5)

        create_backup_controls(char_frame, file)


def show_world_backups():
    # Create a new window for world backup selection
    world_window = tk.Toplevel(root)
    world_window.title(T["world_backups"])
    world_window.geometry("600x600")
    world_window.transient(root)
    world_window.grab_set()
    style_editor_window(world_window)
    
    # Add a title label
    title_label = tk.Label(world_window, 
                          text=T["world_backups"],
                          font=(FONT_NAME, 16, 'bold'),
                          bg=RS_BROWN,
                          fg=RS_GOLD)
    title_label.pack(pady=10)
    
    # Create a canvas with scrollbar
    canvas = tk.Canvas(world_window, bg=RS_BROWN)
    scrollbar = ttk.Scrollbar(world_window, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=RS_BROWN)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    # Pack the canvas and scrollbar
    canvas.pack(side="left", fill="both", expand=True, padx=20, pady=10)
    scrollbar.pack(side="right", fill="y")
    
    # Get the world save path (env-var aware)
    default_path = get_save_path("SaveGames")
    
    if os.path.exists(default_path):
        # Find all SAV files in the default path, excluding EnhancedInputUsersettings (case-insensitive)
        sav_files = [f for f in glob.glob(os.path.join(default_path, "*.sav")) 
                    if "enhancedinputusersettings" not in f.lower()]
        sav_files.sort(key=os.path.getmtime, reverse=True)
        
        # Add a label for each file
        for file in sav_files:
            # Create a frame for the world label and backup controls
            world_frame = tk.Frame(scrollable_frame, bg=RS_BROWN)
            world_frame.pack(fill="x", pady=5)
            
            # World label
            file_name = os.path.basename(file).replace(".sav", "")
            label = tk.Label(world_frame,
                           text=file_name,
                           bg=RS_DARK_TAN,
                           fg=RS_GOLD,
                           font=(FONT_NAME, 12),
                           width=30,
                           height=2)
            label.pack(pady=5)
            
            # Add backup controls
            create_world_backup_controls(world_frame, file)

# Create the main window and set up the UI
root = tk.Tk()
root.title(T["app_title"])
root.geometry("1500x900")
root.configure(bg=RS_BROWN)


# Show character selection window when the app starts, but after a short delay
root.after(100, lambda: root.withdraw())  # Hide the main window
root.after(200, lambda: (show_character_selection(), root.deiconify()))  # Show character selection, then show main window


# ── tkinter 样式（颜色从 src/config.py 导入）────────────────────
style = ttk.Style()
style.configure('RS.TButton', 
    background=RS_DARK_TAN,
    foreground=RS_GOLD,
    font=(FONT_NAME, 10, 'bold'),
    padding=5
)

# Top Control Panel
control_frame = tk.Frame(root, bg=RS_BROWN)
control_frame.pack(fill=tk.X, pady=5)

# Style the buttons
load_btn = tk.Button(control_frame, text=T["btn_load_json"], command=load_json,
                    bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10, 'bold'),
                    relief='raised', borderwidth=2)
load_btn.pack(side=tk.LEFT, padx=5)

save_btn = tk.Button(control_frame, text=T["btn_save_inv"], command=save_inventory_to_file,
                    bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10, 'bold'),
                    relief='raised', borderwidth=2)
save_btn.pack(side=tk.LEFT, padx=5)

save_preset_btn = tk.Button(control_frame, text=T["btn_save_preset"], command=save_preset,
                    bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10, 'bold'),
                    relief='raised', borderwidth=2)
save_preset_btn.pack(side=tk.LEFT, padx=5)

load_preset_btn = tk.Button(control_frame, text=T["btn_load_preset"], command=load_preset,
                    bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10, 'bold'),
                    relief='raised', borderwidth=2)
load_preset_btn.pack(side=tk.LEFT, padx=5)

# Add this after the control_frame creation but before the load_btn
world_backup_btn = tk.Button(control_frame, text=T["btn_world_backups"], command=show_world_backups,
                    bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10, 'bold'),
                    relief='raised', borderwidth=2)
world_backup_btn.pack(side=tk.LEFT, padx=5)

# Main Top Frame for two boxes
top_frame = tk.Frame(root, bg=RS_BROWN)
top_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# Left Box (Equipment)
box1 = tk.Frame(top_frame, bg=RS_TAN, bd=2, relief='ridge')
box1.pack(side="left", expand=False, fill="both", padx=5)

# Right Box (Skills Pane)
skills_pane = tk.Frame(top_frame, bg=RS_TAN, bd=2, relief='ridge')
skills_pane.pack(side="left", expand=True, fill="both", padx=5)

# Skills Display Inside Skills Pane
skills_display_frame = tk.Frame(skills_pane, bg=RS_LIGHT_TAN, bd=2, relief='groove')
skills_display_frame.pack(padx=10, pady=10, fill="both", expand=True)

# Inventory Bar
inventory_container = tk.Frame(root, bg=RS_BROWN)
inventory_container.pack(side="bottom", fill="x", padx=10, pady=10)

# Style the notebook
style = ttk.Style()
style.theme_use('default')  # Reset to default theme first
style.configure('TNotebook', background=RS_BROWN)
style.configure('TNotebook.Tab', 
    background=RS_BROWN,
    foreground=RS_GOLD,
    padding=[10, 2],
    font=(FONT_NAME, 10, 'bold'))
style.map('TNotebook.Tab',
    background=[('selected', RS_RED), ('!selected', RS_BROWN)],
    foreground=[('selected', RS_GOLD), ('!selected', RS_GOLD)],
    lightcolor=[('selected', RS_RED), ('!selected', RS_BROWN)],
    darkcolor=[('selected', RS_RED), ('!selected', RS_BROWN)],
    bordercolor=[('selected', RS_RED), ('!selected', RS_BROWN)])

# Create the notebook (tabbed interface) for inventory
notebook = ttk.Notebook(inventory_container)
notebook.pack(fill=tk.BOTH, expand=True)

# Create three frames for the inventory tabs
inventory_tab = tk.Frame(notebook, bg=RS_BROWN)
tab2 = tk.Frame(notebook, bg=RS_BROWN)
tab3 = tk.Frame(notebook, bg=RS_BROWN)

# Add the tabs to the notebook
notebook.add(inventory_tab, text='📦 背包')
notebook.add(tab2, text='📦 符文')
notebook.add(tab3, text='📦 装备栏')

# Create bulk insert control panel for inventory
bulk_insert_frame = tk.Frame(inventory_tab, bg=RS_BROWN)
bulk_insert_frame.pack(fill=tk.X, pady=5)

# Create variables for bulk insert
item_var = tk.StringVar(value="空")
count_var = tk.StringVar(value="1")

# Create dropdown and entry for bulk insert
item_label = tk.Label(bulk_insert_frame, text=T["lbl_item"], bg=RS_BROWN, fg=RS_GOLD, font=(FONT_NAME, 10))
item_label.pack(side=tk.LEFT, padx=5)

item_dropdown = ttk.Combobox(bulk_insert_frame, textvariable=item_var, values=regular_items + gear_items, width=20, state='readonly')
item_dropdown.pack(side=tk.LEFT, padx=5)

count_label = tk.Label(bulk_insert_frame, text=T["lbl_count"], bg=RS_BROWN, fg=RS_GOLD, font=(FONT_NAME, 10))
count_label.pack(side=tk.LEFT, padx=5)

count_entry = tk.Entry(bulk_insert_frame, textvariable=count_var, width=6, bg=RS_LIGHT_TAN, fg='black', font=(FONT_NAME, 10))
count_entry.pack(side=tk.LEFT, padx=5)

insert_btn = tk.Button(bulk_insert_frame, text=T["btn_insert_checked"], command=insert_to_checked_slots,
                      bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10, 'bold'),
                      relief='raised', borderwidth=2)
insert_btn.pack(side=tk.LEFT, padx=5)

clear_selections_btn = tk.Button(bulk_insert_frame, text=T["btn_clear_selections"], command=clear_all_selections,
                               bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10, 'bold'),
                               relief='raised', borderwidth=2)
clear_selections_btn.pack(side=tk.LEFT, padx=5)

# Add clear slots button to the bulk insert frame
clear_slots_btn = tk.Button(bulk_insert_frame, text=T["btn_clear_slots"], command=clear_all_backpack_slots,
                           bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10, 'bold'),
                           relief='raised', borderwidth=2)
clear_slots_btn.pack(side=tk.LEFT, padx=5)

# Inventory Grid for first tab
inventory_frame = tk.Frame(inventory_tab, bg=RS_BROWN)
inventory_frame.pack()

# Create a frame for the inventory grid title
inventory_title_frame = tk.Frame(inventory_tab, bg=RS_BROWN)
inventory_title_frame.pack()
inventory_label = tk.Label(inventory_title_frame, text=T["lbl_backpack"], 
                         bg=RS_BROWN, fg=RS_GOLD, 
                         font=(FONT_NAME, 12, 'bold'))
inventory_label.pack()

# Create rune grid for second tab
rune_frame = tk.Frame(tab2, bg=RS_BROWN)
rune_frame.pack()

# Create a frame for the rune grid title
rune_title_frame = tk.Frame(tab2, bg=RS_BROWN)
rune_title_frame.pack()
rune_label = tk.Label(rune_title_frame, text=T["lbl_runes"], 
                     bg=RS_BROWN, fg=RS_GOLD, 
                     font=(FONT_NAME, 12, 'bold'))
rune_label.pack()

# Create rune slots (from slot 32 onwards)
for i in range(32, 64):  # Create slots 32-63
    # Create a frame for each rune slot
    slot_frame = tk.Frame(rune_frame, bg=RS_EMPTY_BORDER, relief='ridge', bd=2)
    slot_frame.grid(row=(i-32) // 8, column=(i-32) % 8, padx=1, pady=1)
    
    # Inner frame for content
    inner_frame = tk.Frame(slot_frame, bg=RS_TAN)
    inner_frame.pack(fill='both', expand=True, padx=1, pady=1)
    
    # Slot number label
    slot_label = tk.Label(inner_frame, 
                         text=f"格 {i}",
                         bg=RS_TAN,
                         fg='black',
                         font=(FONT_NAME, 8))
    slot_label.pack(anchor='nw')
    
    # Create variables for the rune slot
    rune_var = tk.StringVar(value="空")
    
    # Rune combobox
    rune_combo = ttk.Combobox(inner_frame, 
                             textvariable=rune_var,
                             values=rune_items,
                             width=10,
                             state='readonly')
    rune_combo.pack(fill='x', padx=1)
    
    # Current rune label
    current_rune_label = tk.Label(inner_frame,
                                 text="空",
                                 bg=RS_TAN,
                                 fg='black',
                                 font=(FONT_NAME, 8),
                                 wraplength=90)
    current_rune_label.pack(fill='x', padx=1)
    
    # Count entry
    count_entry = tk.Entry(inner_frame,
                          width=6,
                          bg=RS_LIGHT_TAN,
                          fg='black',
                          font=(FONT_NAME, 8))
    count_entry.pack(fill='x', padx=1)
    
    # Bind events
    rune_combo.bind('<<ComboboxSelected>>', 
                   lambda e, r=rune_var, s=slot_frame, l=current_rune_label: 
                   on_rune_select(e, r, s, l))
    
    # Update current rune label when selection changes
    def update_current_rune(*args):
        update_current_rune_label(current_rune_label, rune_var)
        update_rune_slot_border(slot_frame, rune_var)
    
    rune_var.trace('w', update_current_rune)
    
    # Add to rune entries list
    rune_entries.append((rune_var, count_entry, current_rune_label))

# Now create the slots after all frames are defined
for i in range(32):
    # Create a frame for each slot
    slot_frame = tk.Frame(inventory_frame, bg=RS_EMPTY_BORDER, relief='ridge', bd=2)
    slot_frame.grid(row=i // 8, column=i % 8, padx=1, pady=1)
    
    # Inner frame for content
    inner_frame = tk.Frame(slot_frame, bg=RS_TAN)
    inner_frame.pack(fill='both', expand=True, padx=1, pady=1)
    
    # Create a frame for the checkbox and label
    checkbox_frame = tk.Frame(inner_frame, bg=RS_TAN)
    checkbox_frame.pack(anchor='nw', fill='x')
    
    # Checkbox for bulk operations
    checkbox_var = tk.BooleanVar(value=False)
    checkbox = tk.Checkbutton(checkbox_frame, variable=checkbox_var, bg=RS_TAN)
    checkbox.pack(side='left')
    slot_checkboxes.append(checkbox_var)
    
    # Slot number label
    slot_label = tk.Label(checkbox_frame, 
                         text=T["lbl_slot"].format(i+1),
                         bg=RS_TAN,
                         fg='black',
                         font=(FONT_NAME, 8))
    slot_label.pack(side='left')
    
    # Make both the checkbox frame and its contents clickable
    def make_clickable(widget, sf=slot_frame, cv=checkbox_var):
        widget.bind('<Button-1>', lambda e, s=sf, c=cv: toggle_checkbox(s, c))
    
    make_clickable(checkbox_frame)
    make_clickable(checkbox)
    make_clickable(slot_label)
    
    # Create a frame for the dropdowns
    dropdown_frame = tk.Frame(inner_frame, bg=RS_TAN)
    dropdown_frame.pack(fill='x', padx=1)
    
    # Create both variables first
    regular_var = tk.StringVar(value="空")
    gear_var = tk.StringVar(value="空")
    
    # Regular items combobox
    regular_combo = ttk.Combobox(dropdown_frame, 
                                textvariable=regular_var,
                                values=regular_items,
                                width=10,
                                state='readonly')
    regular_combo.pack(side='left', fill='x', expand=True, padx=1)
    
    # Gear items combobox
    gear_combo = ttk.Combobox(dropdown_frame, 
                             textvariable=gear_var,
                             values=gear_items,
                             width=10,
                             state='readonly')
    gear_combo.pack(side='left', fill='x', expand=True, padx=1)
    
    # Current item label
    current_item_label = tk.Label(inner_frame,
                                 text="空",
                                 bg=RS_TAN,
                                 fg='black',
                                 font=(FONT_NAME, 8),
                                 wraplength=90)
    current_item_label.pack(fill='x', padx=1)
    
    # Bind events after both comboboxes are created
    regular_combo.bind('<<ComboboxSelected>>', 
                      lambda e, r=regular_var, g=gear_var, s=slot_frame, l=current_item_label: 
                      (on_item_select(e, r, g, s, True), update_current_item_label(l, r, g)))
    gear_combo.bind('<<ComboboxSelected>>', 
                   lambda e, r=regular_var, g=gear_var, s=slot_frame, l=current_item_label: 
                   (on_item_select(e, r, g, s, False), update_current_item_label(l, r, g)))
    
    # Update current item label when selection changes
    def update_current_item(*args):
        update_current_item_label(current_item_label, regular_var, gear_var)
        update_slot_border(slot_frame, regular_var, gear_var)
    
    regular_var.trace('w', update_current_item)
    gear_var.trace('w', update_current_item)
    
    # Count entry
    count_entry = tk.Entry(inner_frame,
                          width=6,
                          bg=RS_LIGHT_TAN,
                          fg='black',
                          font=(FONT_NAME, 8))
    count_entry.pack(fill='x', padx=1)
    
    slot_entries.append((regular_var, gear_var, count_entry, current_item_label))

# Configure ttk style for comboboxes
style = ttk.Style()
style.configure('TCombobox', 
                fieldbackground=RS_LIGHT_TAN,
                background=RS_LIGHT_TAN,
                foreground='black',
                arrowcolor='black',
                selectbackground=RS_DARK_TAN,
                selectforeground=RS_GOLD)

# Modify the rune tab section to add the new buttons
# Find the rune_title_frame section and add after it:
rune_control_frame = tk.Frame(tab2, bg=RS_BROWN)
rune_control_frame.pack(pady=5)

load_rune_pack_btn = tk.Button(rune_control_frame, text=T["btn_rune_pack"], command=load_rune_pack,
                              bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10, 'bold'),
                              relief='raised', borderwidth=2)
load_rune_pack_btn.pack(side=tk.LEFT, padx=5)

clear_runes_btn = tk.Button(rune_control_frame, text=T["btn_clear_runes"], command=clear_all_runes,
                           bg=RS_DARK_TAN, fg=RS_GOLD, font=(FONT_NAME, 10, 'bold'),
                           relief='raised', borderwidth=2)
clear_runes_btn.pack(side=tk.LEFT, padx=5)

# Add contact section at the bottom
contact_frame = tk.Frame(root, bg=RS_BROWN)
contact_frame.pack(side="bottom", fill="x", pady=5)

# Create a frame for the contact info
contact_info_frame = tk.Frame(contact_frame, bg=RS_BROWN)
contact_info_frame.pack(side="right", padx=10)

# Discord link
discord_frame = tk.Frame(contact_info_frame, bg=RS_BROWN)
discord_frame.pack(side="left", padx=5)

discord_icon = tk.Label(discord_frame, text="💬", 
                       bg=RS_BROWN, fg=RS_GOLD,
                       font=(FONT_NAME, 12))
discord_icon.pack(side="left", padx=2)

discord_text = tk.Label(discord_frame, text="Discord",
                       bg=RS_BROWN, fg=RS_GOLD,
                       font=(FONT_NAME, 10))
discord_text.pack(side="left")

# GitHub link
github_frame = tk.Frame(contact_info_frame, bg=RS_BROWN)
github_frame.pack(side="left", padx=5)

github_icon = tk.Label(github_frame, text="🐙", 
                      bg=RS_BROWN, fg=RS_GOLD,
                      font=(FONT_NAME, 12))
github_icon.pack(side="left", padx=2)

github_text = tk.Label(github_frame, text="GitHub",
                      bg=RS_BROWN, fg=RS_GOLD,
                      font=(FONT_NAME, 10))
github_text.pack(side="left")

# Donation link
donation_frame = tk.Frame(contact_info_frame, bg=RS_BROWN)
donation_frame.pack(side="left", padx=5)

donation_icon = tk.Label(donation_frame, text="❤️", 
                        bg=RS_BROWN, fg=RS_GOLD,
                        font=(FONT_NAME, 12))
donation_icon.pack(side="left", padx=2)

donation_text = tk.Label(donation_frame, text="Donate",
                        bg=RS_BROWN, fg=RS_GOLD,
                        font=(FONT_NAME, 10))
donation_text.pack(side="left")

# Make the contact sections clickable
def open_discord(event):
    import webbrowser
    webbrowser.open("https://discord.gg/TeZvrV8728")

def open_github(event):
    import webbrowser
    webbrowser.open("https://github.com/xxmowgli/DragonMaster")

def open_donation(event):
    import webbrowser
    webbrowser.open("https://www.xxmowgli.co.uk")

# Bind click events
discord_icon.bind('<Button-1>', open_discord)
discord_text.bind('<Button-1>', open_discord)
github_icon.bind('<Button-1>', open_github)
github_text.bind('<Button-1>', open_github)
donation_icon.bind('<Button-1>', open_donation)
donation_text.bind('<Button-1>', open_donation)

# Add these after the existing item maps but before the UI creation

# Loadout slot item lists
loadout_hat_items = [
    "空",
    "圣骑士头盔",
    "强化头盔",
    "硬皮头巾",
    "钉皮头巾",
    "皮头巾",
    "巫师帽",
    "学徒帽",
    "龙族法师兜帽",
    "暗黑法师兜帽"
]

loadout_body_items = [
    "空",
    "圣骑士胸甲",
    "强化胸甲",
    "硬皮胸甲",
    "钉皮胸甲",
    "皮胸甲",
    "巫师袍",
    "学徒袍",
    "龙族法师袍",
    "暗黑法师袍"
]

loadout_legs_items = [
    "空",
    "圣骑士护腿",
    "强化护腿",
    "硬皮护腿",
    "钉皮护腿",
    "皮护腿",
    "巫师护腿",
    "学徒护腿",
    "龙族法师护腿",
    "暗黑法师护腿"
]

loadout_cape_items = [
    "空",
    "碎裂披风"
]

loadout_jewelry_items = [
    "空"
]

# Add this function after the existing functions but before the UI creation
def update_loadout_slot_border(slot_frame, item_var):
    if item_var.get() != "空":
        slot_frame.configure(bg=RS_FILLED_BORDER)
    else:
        slot_frame.configure(bg=RS_EMPTY_BORDER)

def on_loadout_item_select(event, item_var, slot_frame, current_item_label):
    update_loadout_item_label(current_item_label, item_var)
    update_loadout_slot_border(slot_frame, item_var)

# Add this after creating the notebook tabs but before creating the inventory grid
# Create loadout grid for third tab
loadout_frame = tk.Frame(tab3, bg=RS_BROWN)
loadout_frame.pack()

# Create a frame for the loadout grid title
loadout_title_frame = tk.Frame(tab3, bg=RS_BROWN)
loadout_title_frame.pack()
loadout_label = tk.Label(loadout_title_frame, text=T["lbl_loadout"], 
                        bg=RS_BROWN, fg=RS_GOLD, 
                        font=(FONT_NAME, 12, 'bold'))
loadout_label.pack()

# Create loadout slots (5 slots)
loadout_entries = []
slot_names = ["头盔", "身体", "腿甲", "披风", "饰品"]
slot_items = [loadout_hat_items, loadout_body_items, loadout_legs_items, 
              loadout_cape_items, loadout_jewelry_items]

for i in range(5):
    # Create a frame for each loadout slot
    slot_frame = tk.Frame(loadout_frame, bg=RS_EMPTY_BORDER, relief='ridge', bd=2)
    slot_frame.grid(row=i // 3, column=i % 3, padx=1, pady=1)
    
    # Inner frame for content
    inner_frame = tk.Frame(slot_frame, bg=RS_TAN)
    inner_frame.pack(fill='both', expand=True, padx=1, pady=1)
    
    # Slot name label
    slot_label = tk.Label(inner_frame, 
                         text=f"{slot_names[i]}",
                         bg=RS_TAN,
                         fg='black',
                         font=(FONT_NAME, 8))
    slot_label.pack(anchor='nw')
    
    # Create variables for the loadout slot
    item_var = tk.StringVar(value="空")
    
    # Item combobox
    item_combo = ttk.Combobox(inner_frame, 
                             textvariable=item_var,
                             values=slot_items[i],
                             width=15,
                             state='readonly')
    item_combo.pack(fill='x', padx=1)
    
    # Current item label
    current_item_label = tk.Label(inner_frame,
                                 text="空",
                                 bg=RS_TAN,
                                 fg='black',
                                 font=(FONT_NAME, 8),
                                 wraplength=90)
    current_item_label.pack(fill='x', padx=1)
    
    # Durability entry
    count_entry = tk.Entry(inner_frame,
                          width=6,
                          bg=RS_LIGHT_TAN,
                          fg='black',
                          font=(FONT_NAME, 8))
    count_entry.pack(fill='x', padx=1)
    
    # Bind events
    item_combo.bind('<<ComboboxSelected>>', 
                   lambda e, v=item_var, s=slot_frame, l=current_item_label: 
                   on_loadout_item_select(e, v, s, l))
    
    # Update current item label when selection changes
    def update_current_item(*args):
        update_loadout_item_label(current_item_label, item_var)
        update_loadout_slot_border(slot_frame, item_var)
    
    item_var.trace('w', update_current_item)
    
    # Add to loadout entries list
    loadout_entries.append((item_var, count_entry, current_item_label))

# Add this after the update_current_item_label function
def update_loadout_item_label(label, item_var):
    # Get the current item
    current_item = item_var.get()
    label.configure(text=current_item)


def load_character(file_path):
    global current_inventory_data, current_file_path
    
    try:
        # Load the JSON file
        with open(file_path, 'r') as f:
            current_inventory_data = json.load(f)
        
        # Store the current file path
        current_file_path = file_path
        
        # Update the window title with the character name
        character_name = os.path.basename(file_path).replace(".json", "")
        root.title(f"DragonMaster v0.1.2 May 2025 - {character_name}")
        
        # Refresh the display
        refresh_display()
        
        # Close the character selection window
        for widget in root.winfo_children():
            if isinstance(widget, tk.Toplevel):
                widget.destroy()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load character: {e}")

# 注入依赖到备份模块（必须在所有函数定义之后）
backup_inject(root, style_editor_window, load_character)

root.mainloop()
