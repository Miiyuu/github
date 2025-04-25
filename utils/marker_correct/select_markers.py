import pandas as pd

df = pd.read_csv(r"D:\0-workingspace\key-marker\output\marker_mygene_status.csv")
false_markers = df[df['in_mygene'] == False]['marker']
false_markers.to_csv(r'output\false_markers.csv', index=False)

print(false_markers.to_list())