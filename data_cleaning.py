import pandas as pd

df = pd.read_csv("redditposts.csv")

df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce').dt.strftime('%Y-%m-%d')
df = df.drop(columns=['year'], errors='ignore')

academic_keywords      = r'\b(JEE|NEET|exam|college|placement|boards)\b'
family_keywords        = r'\b(parents|mom|dad|mother|father|brother|sister|sibling|family|toxic household|relatives|cousin)\b'
vulnerability_keywords = r'\b(abuse|abusive|hitting|beating|trauma|alone|lonely|isolation|crying|depressed|hopeless|suicidal|anxiety)\b'
corporate_keywords     = r'\b(job|boss|salary|increment|hike|burnout)\b'
romantic_keywords      = r'\b(gf|bf|girlfriend|boyfriend|spouse|wife|husband|fiance|fiancee|partner|breakup|dating|relationship)\b'

df['flag_academic']      = df['text'].str.contains(academic_keywords     , case=False, na=False, regex=True).astype(int)
df['flag_family']        = df['text'].str.contains(family_keywords       , case=False, na=False, regex=True).astype(int)
df['flag_vulnerability'] = df['text'].str.contains(vulnerability_keywords, case=False, na=False, regex=True).astype(int)
df['flag_corporate']     = df['text'].str.contains(corporate_keywords    , case=False, na=False, regex=True).astype(int)
df['flag_romantic']      = df['text'].str.contains(romantic_keywords     , case=False, na=False, regex=True).astype(int)


df.to_csv("redditposts_cleaned.csv", index=False)