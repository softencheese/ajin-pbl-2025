from sqlalchemy import create_engine
import pandas as pd
engine = create_engine('mysql+pymysql://root:root@127.0.0.1:3306/ajin')
df = pd.read_sql('SELECT * FROM lot_genealogy', engine)
print("genealogy:")
print(df)
df2 = pd.read_sql('SELECT id, lot_number, item_id, quantity, initial_quantity, status, process_id FROM lots', engine)
print("lots:")
print(df2)
df3 = pd.read_sql('SELECT id, pallet_no, lot_id, status, quantity FROM pallets', engine)
print("pallets:")
print(df3)
