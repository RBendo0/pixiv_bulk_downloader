from .ui import ui

print("=== Test input_string ===")
print()

value1 = ui.input_string(
    prompt="Archive path",
    default=r"D:\Pixiv\Archive"
)

value2 = ui.input_string(
    prompt="Backup path",
    default=r"E:\Backup\Pixiv"
)

print()
print(f"Archive: {value1}")
print(f"Backup : {value2}")
print("Fine test.")