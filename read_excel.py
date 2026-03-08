import pandas as pd
xl = pd.ExcelFile(r'c:\Users\HP\Documents\projects]\Event Managment\Full_Event_Management_System_Features.xlsx')
print('Sheets:', xl.sheet_names)
for sheet in xl.sheet_names:
    print(f"\n=== {sheet} ===")
    df = pd.read_excel(xl, sheet_name=sheet)
    print(df.to_string())