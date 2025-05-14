import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Load and inspect
df = pd.read_csv("/home/mor/Desktop/israel_day_AI/web_scrap/output/Auto.csv")
print(df.info())
print(df.describe())
print(df.isnull().sum())

# Histogram of CTR
sns.histplot(df["URL CTR"], kde=True)
plt.title("Distribution of CTR")
plt.show()

# Scatter plot: title length vs CTR
df["title_length"] = df["title"].str.len()
sns.scatterplot(x="title_length", y="URL CTR", data=df)
plt.title("CTR vs Title Length")
plt.show()
