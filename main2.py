import requests
from urllib.parse import urlencode
import pandas as pd
from io import BytesIO
import plotly.express as px
import streamlit as st
import xlrd

# アプリケーションID
APP_ID = "8a64000813bc1bef3d6bb0bc345cb487873861ec"
# API URL
API_URL = "http://api.e-stat.go.jp/rest/2.0/app/json/getStatsData"
# 統計表ID
statsDataId = "C0020050213000"
# コード
cdCat01 = "#A03503"

# パラメータを設定
params = {
    "appId": APP_ID,
    "statsDataId": statsDataId,
    "cdCat01": cdCat01
}

# URLエンコード
GET_URL = f"{API_URL}?{urlencode(params)}"

# APIリクエストを送信
response = requests.get(GET_URL)

def create_dataframe(url, year, nrows):
    # リクエストを送信してExcelファイルをダウンロード
    response = requests.get(url)
    response.raise_for_status()
    # ダウンロードしたファイルをDataFrameに読み込む
    df = pd.read_excel(BytesIO(response.content), skiprows=9, nrows=nrows)  
    # カラム名を再定義
    df.columns = ['都道府県名', '空欄','計', '小計', '農業組合法人', '株式会社', '合同会社', 'その他','非法人']
    #いらないカラムを消します。
    df = df.drop(columns=['空欄', '計', '小計'])
    # 西暦というカラムを作り、指定された year で埋める
    df['西暦'] = year
    df = df.replace("-", 0)
    # NaN を 0 に置き換える
    df = df.fillna(0)
    # 数値型のカラムのみ選択し、整数に変換
    df[df.select_dtypes(include=['number']).columns] = df.select_dtypes(include=['number']).astype(int)
    return df

# Cache the entire data processing step
@st.cache_data
def process_all_data(statInfId):
    # 最終的な結果を格納するための DataFrame を定義
    df_all = pd.DataFrame()

    # キーと値の両方を取得
    for year, value in statInfId.items():

        # ExcelファイルのURL
        url = f"https://www.e-stat.go.jp/stat-search/file-download?statInfId={value}&fileKind=0"

        # DataFrame を作成
        df = create_dataframe(url, year, 59)

        # 北海道と都府県の数値カラムのみを合計
        df_sum = df[df['都道府県名'].isin(['北海道', '都府県'])].sum(numeric_only=True)

        # 合計行に必要なカラムを追加
        df_sum['都道府県名'] = '合計'
        df_sum['西暦'] = year  # 年を適用する

        # 合計行を1行のDataFrameに変換
        df_sum = pd.DataFrame([df_sum], columns=df.columns)

        # 最終結果の DataFrame に合計行を追加
        df = pd.concat([df, df_sum], ignore_index=True)
        df_all = pd.concat([df_all, df], ignore_index=True)

    return df_all

# 作物統計調査_令和5年産市町村別データ
statInfId = {
    2013:"000023280346",2014:"000027235935",2015:"000031319124",2016:"000031523033",
    2017:"000031633213",2018:"000031759839",2019:"000031874921",2020:"000032014479",
    2021:"000032129452",2022:"000032247665",2023:"000040110138"
}

# データの処理
df = process_all_data(statInfId)

# 元のリスト
prefectures = [
    "北海道", "都府県", "東北", "北陸", "関東・東山", "東海", "近畿", "中国", "四国", "九州", "沖縄", 
    "青森", "岩　手", "宮城", "秋　田", "山　形", "福　島", "茨　城", "栃　木", "群　馬", 
    "埼　玉", "千 葉", "東京", "神 奈 川", "新 潟", "富 山", "石川", "福 井", "山　梨", "長 野", "岐阜", 
    "静岡", "愛知", "三重", "滋 賀", "京都", "大 阪", "兵 庫", "奈 良", "和 歌 山", "鳥 取", "島 根", 
    "岡山", "広 島", "山 口", "徳 島", "香 川", "愛 媛", "高 知", "福 岡", "佐 賀", "長 崎", "熊本", 
    "大 分", "宮 崎", "鹿 児 島", "合計", "岩手", "秋田", "山形", 
    "福島", "茨城", "栃木", "群馬", "埼玉", "千葉", "神奈川", "新潟", "富山", "福井", "山梨", "長野", 
    "滋賀", "大阪", "兵庫", "奈良", "和歌山", "鳥取", "島根", "広島", "山口", "徳島", "香川", "愛媛", 
    "高知", "福岡", "佐賀", "長崎", "大分", "宮崎"
]

# 都道府県名が指定されたリスト内にある行だけをフィルタリング
df = df[df['都道府県名'].isin(prefectures)]

# セレクトボックスの作成
select = st.selectbox(
    '都道府県を選択してください', 
    df['都道府県名'].unique()  # 都道府県名のユニークな値を取得
)

# '合計' 行のみを抽出
df_ = df[df['都道府県名'] == select]

# '都道府県名' を除くカラムを選択
df_ = df_.drop(columns=['都道府県名'])

# データを長形式に変換
df_long = df_.melt(id_vars='西暦', var_name='法人の種類', value_name='数')

# 積み上げ棒グラフの作成
fig = px.bar(
    df_long,
    x='西暦',
    y='数',
    color='法人の種類',
    title='集落営農の形態別の推移',
    labels={'数': '数', '法人の種類': '形態別'},
    text='数'  # 各バーに値を表示
)

# グラフのレイアウトを調整
fig.update_layout(
    barmode='stack',  # 積み上げ棒グラフ
    xaxis_title='西暦',
    yaxis_title='数',
    legend_title_text='法人の種類'
)

# グラフを表示
st.plotly_chart(fig)  # streamlitでPlotlyグラフを表示