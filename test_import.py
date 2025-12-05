try:
    import app
    print("导入成功！")
except Exception as e:
    import traceback
    print(f"导入失败: {str(e)}")
    print("详细错误信息:")
    traceback.print_exc()