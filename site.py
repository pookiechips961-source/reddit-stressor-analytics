import pymysql
import pandas as pd
import streamlit as st
import plotlyexpress as px


def get_data(query_string):
    conn = pymysql.connect(
        host=st.secrets["db_host"],
        port=int(st.secrets["db_port"]),
        user=st.secrets["db_user"],
        password=st.secrets["db_password"],
        database=st.secrets["db_name"],
        ssl={"ssl": {}},
    )
    df = pd.read_sql(query_string, conn)
    conn.close()
    return df

categories = ['Academic', 'Family', 'Vulnerability', 'Corporate', 'Relationship']

master_query = "SELECT " \
               "YEAR(date) AS Year, " \
               "MONTH(date) AS Month, " \
               "COUNT(*) AS Total, " \
               "SUM(flag_academic) AS Academic, " \
               "SUM(flag_family) AS Family, " \
               "SUM(flag_vulnerability) as Vulnerability, " \
               "SUM(flag_corporate) AS Corporate, " \
               "SUM(flag_relationship) AS Relationship " \
               "FROM maintable " \
               "GROUP BY Year, Month " \
               "ORDER BY Year ASC, Month ASC;"

correlation_query = "SELECT " \
                "SUM(flag_academic AND flag_family) AS Academic_Family," \
                "SUM(flag_academic AND flag_vulnerability) AS Academic_Vulnerability," \
                "SUM(flag_academic AND flag_corporate) AS Academic_Corporate, " \
                "SUM(flag_academic AND flag_relationship) AS Academic_Relationship," \
                "SUM(flag_family AND flag_vulnerability) AS Family_Vulnerability," \
                "SUM(flag_family AND flag_corporate) AS Family_Corporate," \
                "SUM(flag_family AND flag_relationship) AS Family_Relationship," \
                "SUM(flag_vulnerability AND flag_corporate) AS Vulnerability_Corporate," \
                "SUM(flag_vulnerability AND flag_relationship) AS Vulnerability_Relationship," \
                "SUM(flag_corporate AND flag_relationship) AS Corporate_Relationship " \
                "FROM maintable;"

df = get_data(master_query)
total_posts_all_time = df['Total'].sum()
category_sums = df[categories].sum()
max_stressor_name = category_sums.idxmax()
max_stressor_value = (category_sums.max() / total_posts_all_time).round(2)
min_year = int(df['Year'].min())
max_year = int(df['Year'].max())


st.set_page_config(
    page_title = "Data analysis",
    layout = "wide"
)

st.title("Visualising And Interpreting The Data")

st.markdown(
    "This dashboard helps track and analyze different types of stressors over time based on forum posts. "
    "By looking at trends across years, monthly changes, and connections between topics, we can better understand "
    "what issues are driving the community discussion."
)
st.markdown("---")

st.subheader("Key Metrics Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        label = "Posts Analysed", 
        value = f"{total_posts_all_time:,d}",
        help = "The net summation of all valid text records processed within the maintable dataset index."
    )
with col2:
    st.metric(
        label = "Dominant Driver", 
        value = max_stressor_name,
        help = "The type of post(s) with the highest average frequency as a fraction of the total posts over the years."
    )
with col3:
    st.metric(
        label = "Mean Density", 
        value = f"{max_stressor_value:.2f} per post",
        help = "The probabilistic density of the dominant driver, as total category flags divided by total observations."
    )


st.markdown("---")


st.subheader("Relative Composition Analysis")

st.markdown(
    "This chart tracks how the proportion of each stressor has changed over the years. "
    "Because the numbers are showing the percentage share rather than the raw count, "
    "it lets you see which topics are becoming more or less important relative to each other, "
    "even if the overall number of posts on the platform fluctuates."
)

selected_years = st.slider(
        label = "Select Analysis Window (Years)",
        min_value = min_year,
        max_value = max_year,
        value = (2015, max_year),
        step = 1
    )

df1 = df[(df['Year'] >= selected_years[0]) & (df['Year'] <= selected_years[1])].drop('Month', axis = 1).groupby('Year').sum()
df1  =  df1.div(df1['Total'], axis = 0).reset_index()

fig_share = px.area(
    df1,
    x = "Year",
    y = categories,
    title = "Stressor Topic Share Over Time (Normalized)",
    labels = {"value": "Percentage Share", "Year": "Year", "variable": "Topic"}
)

fig_share.update_layout(
    hovermode = "x unified",
    legend_title_text = "Stressor Categories",
    margin = dict(l = 40, r = 40, t = 60, b = 40),
    xaxis = dict(tickmode = "linear", dtick = 1),
    yaxis = dict(tickformat = ".0%")
)

st.plotly_chart(fig_share, use_container_width = True)


st.subheader("Relative Growth Analysis")

st.markdown(
    "This section shows whether a specific stressor is growing faster or slower than the rest of the forum. "
    "A value of 0% means the topic is growing at the exact same rate as the community baseline. "
    "Lines that climb above 0% mean that specific stressor is outpacing the general growth trend of the group, "
    "making it a rapidly expanding concern."
)

df2 = df[(df['Year'] >=  selected_years[0]-1) & (df['Year'] <=  selected_years[1])]
df2 = df2.drop('Month', axis = 1).groupby('Year').sum().pct_change()
for cat in categories:
    df2[f'{cat}'] = df2[f'{cat}'] - df2['Total']
df2 = df2.drop('Total', axis = 1).drop(index = [2010, 2011], errors = 'ignore').dropna().reset_index()

fig_relgrowth  =  px.line(
    df2,
    x = 'Year',
    y = categories,
    title = "Year-over-Year Growth Rate Relative to Forum Baseline",
    labels = {"value": "Growth Delta vs Baseline", "Year": "Year", "variable": "Topic"}
)

fig_relgrowth.update_layout(
    hovermode = "x unified",
    legend_title_text = "Stressor Categories",
    margin = dict(l = 40, r = 40, t = 60, b = 40),
    xaxis = dict(tickmode = "linear", dtick = 1),
    yaxis = dict(tickformat = "+.1%")
)

st.plotly_chart(fig_relgrowth, use_container_width = True)


st.subheader("Intra-Year Seasonality and Volatility")

st.markdown(
    "This line graph highlights the regular seasonal patterns that occur throughout a single year. "
    "The 0% line represents the monthly average for that year. Points above or below the line show "
    "when conversations spike or dip during particular months, which can help pinpoint recurring stress periods."
)

col_widget, col_buffer = st.columns([1, 3])
available_years = sorted(df['Year'].unique(), reverse = True)
if available_years:
    with col_widget:
        selected_vol_year  =  st.selectbox(
            label = "Select Target Year",
            options = available_years,
            index = 0
        )

df3 = df.copy()
df3 = df3[df3['Year'] == selected_vol_year].groupby('Month').sum().drop(['Total', 'Year'], axis = 1)
df3 = (df3 - df3.mean()) / df3.mean()
df3 = df3.reset_index()

fig_volatility  =  px.line(
    df3,
    x = 'Month',
    y = categories,
    title = f"Monthly Variations and Deviations for Calendar Year {selected_vol_year}",
    labels = {"value": "Deviation From Annual Average", "Month": "Month of Year", "variable": "Topic"}
)

fig_volatility.update_layout(
    hovermode = "x unified",
    legend_title_text = "Stressor Categories",
    margin = dict(l = 40, r = 40, t = 60, b = 40),
    xaxis = dict(tickmode = "linear", dtick = 1),
    yaxis = dict(tickformat = "+.1%")
)

st.plotly_chart(fig_volatility, use_container_width = True)


st.subheader("Interconnection and Co-occurrence Strengths")

st.markdown(
    "This heatmap focuses on overlap, displaying how often multiple stressors show up inside the exact same post. "
    "The diagonal values represent the absolute grand totals for each separate category. "
    "The intersections off the diagonal reveal connections—the higher the number where two topics cross, "
    "the more frequently users discuss those two stressors together."
)

df4 = get_data(correlation_query)
data = {
    'Academic': [
        category_sums['Academic'], 
        df4['Academic_Family'][0], 
        df4['Academic_Vulnerability'][0], 
        df4['Academic_Corporate'][0], 
        df4['Academic_Relationship'][0]
    ],
    'Family': [
        df4['Academic_Family'][0], 
        category_sums['Family'], 
        df4['Family_Vulnerability'][0], 
        df4['Family_Corporate'][0], 
        df4['Family_Relationship'][0]
    ],
    'Vulnerability': [
        df4['Academic_Vulnerability'][0], 
        df4['Family_Vulnerability'][0], 
        category_sums['Vulnerability'], 
        df4['Vulnerability_Corporate'][0], 
        df4['Vulnerability_Relationship'][0]
    ],
    'Corporate': [
        df4['Academic_Corporate'][0], 
        df4['Family_Corporate'][0], 
        df4['Vulnerability_Corporate'][0], 
        category_sums['Corporate'], 
        df4['Corporate_Relationship'][0]
    ],
    'Relationship': [
        df4['Academic_Relationship'][0], 
        df4['Family_Relationship'][0], 
        df4['Vulnerability_Relationship'][0], 
        df4['Corporate_Relationship'][0], 
        category_sums['Relationship']
    ]
}

fig_heatmap = px.imshow(
    pd.DataFrame(data, index = categories),
    aspect = "auto",
    title = "Overlap Intensity Grid between Core Categories",
    labels = dict(x = "Stressor Category", y = "Stressor Category", color = "Post Overlap Count"),
    color_continuous_scale = px.colors.sequential.Viridis
)

fig_heatmap.update_layout(
    margin = dict(l = 40, r = 40, t = 60, b = 40)
)
st.plotly_chart(fig_heatmap, use_container_width = True)


st.subheader("Some Posts having all the flags")
st.markdown(
    "This section displays a curated snapshot of 5 posts which triggred all the flags."
)

try:
    with open("posts.txt", "r", encoding="utf-8") as f:
        file_content = f.read().strip()
    post_blocks = file_content.split("---")
    
    for block in post_blocks:
        block_clean = block.strip()
        if not block_clean:
            continue
        
        all_lines = block_clean.split("\n")
        
        if len(all_lines) >= 3:
            date_text = all_lines[0].replace("Date:", "").strip()
            title_text = all_lines[1].replace("Title:", "").strip()
            
            body_text = "\n".join(all_lines[2:]).strip()
            
            with st.container(border = True):
                meta_col1, meta_col2 = st.columns([4, 1])
                with meta_col1:
                    st.caption(f"Date: {date_text}")
            
                st.markdown(f"### {title_text}")
                st.markdown(body_text)

except FileNotFoundError:
    st.error("Missing Source Document: Please verify that 'posts.txt' is located within your root application directory.")
except Exception as e:
    st.error("Parsing Error: Could not interpret the file layout. Please verify the structural boundaries match your standard format.")
st.markdown("---")