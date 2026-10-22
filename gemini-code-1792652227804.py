import streamlit as st
import pandas as pd
import datetime
import os

# ページ設定
st.set_page_config(
    page_title="都ホテルズ 口コミ統合ダッシュボード",
    page_icon="🏨",
    layout="wide"
)

# --- 1. 都ホテルズ＆リゾーツ 全22施設リスト ---
MIYAKO_HOTELS = [
    "大阪マリオット都ホテル", "都ホテル 博多", "ウェスティン都ホテル京都",
    "シェラトン都ホテル東京", "シェラトン都ホテル大阪", "都ホテル 京都八条",
    "都ホテル 四日市", "都ホテル 岐阜長良川", "都ホテル 尼崎",
    "都シティ 東京高輪", "都シティ 近鉄京都駅", "都シティ 大阪天王寺", "都シティ 大阪本町",
    "志摩観光ホテル ザ クラシック", "志摩観光ホテル ザ ベイスイート",
    "奈良ホテル", "賢島宝生苑", "ホテル志摩スペイン村",
    "都リゾート 志摩 ベイサイドテラス", "都リゾート 奥志摩 アクアフォレスト",
    "コートヤード・バイ・マリオット福井", "都ホテル ロサンゼルス"
]

# --- 2. データセット（2023年〜2026年の複数年データを内蔵） ---
@st.cache_data
def get_initial_dataset():
    sample_records = [
        # 大阪マリオット都ホテル
        {"ホテル名": "大阪マリオット都ホテル", "サイト名": "楽天トラベル", "投稿日": "2026-10-18", "宿泊日": "2026-10", "評価": 5.0, "分類": "客室・眺望", "本文": "52階のクラブフロアに宿泊しました。部屋からの大阪市街の夜景は息をのむ美しさでした。ビューバスからも景色が眺められ、日頃の疲れが一気に吹き飛びました。クラブラウンジのアフタヌーンティーやカクテルタイムの品揃えも上品で、スタッフの皆様の丁寧な心遣いに感動しました。また記念日に必ず宿泊します。"},
        {"ホテル名": "大阪マリオット都ホテル", "サイト名": "楽天トラベル", "投稿日": "2024-05-12", "宿泊日": "2024-05", "評価": 4.0, "分類": "サービス、食事", "本文": "駅直結でアクセスは申し分ありません。朝食ビュッフェの搾りたてオレンジジュースやオムレツがとても美味しかったです。チェックイン時に少し行列ができていた点だけ改善されるとさらに良くなります。"},
        {"ホテル名": "大阪マリオット都ホテル", "サイト名": "楽天トラベル", "投稿日": "2023-11-20", "宿泊日": "2023-11", "評価": 5.0, "分類": "客室・設備", "本文": "あべのハルカス上層階からの展望は唯一無二です。室内も非常に広々としており、アメニティも充実していました。夜景を眺めながら過ごす時間は格別でした。"},
        
        # 都ホテル 博多
        {"ホテル名": "都ホテル 博多", "サイト名": "楽天トラベル", "投稿日": "2026-10-14", "宿泊日": "2026-10", "評価": 5.0, "分類": "設備・温泉、立地", "本文": "博多駅筑紫口から地下直結で、天候を気にせずチェックインできました。最上階の屋上アウトドアスパと温泉大浴場が最高で、夜風を感じながら入る温水プールは都心のオアシスそのものです。お部屋も30平米以上あり、洗い場付きのバスルームで快適に寛げました。"},
        {"ホテル名": "都ホテル 博多", "サイト名": "楽天トラベル", "投稿日": "2023-08-15", "宿泊日": "2023-08", "評価": 4.0, "分類": "設備、立地", "本文": "夏休みにプール目当てで家族と宿泊しました。博多駅の目の前で観光拠点として抜群。スパエリアもスタイリッシュで気持ちよく利用できました。"},
        
        # ウェスティン都ホテル京都
        {"ホテル名": "ウェスティン都ホテル京都", "サイト名": "楽天トラベル", "投稿日": "2026-10-10", "宿泊日": "2026-10", "評価": 5.0, "分類": "設備・温泉、食事", "本文": "新設された天然温泉『華頂』が圧倒的でした。敷地内から湧き出る温泉はとろみがあり、半露天風呂からは東山の緑が臨めます。客室からスパ専用のエレベーターと館内着で行ける動線も素晴らしい。朝食レストラン『洛空』の品数とおにぎりコーナーも最高でした。"},
        {"ホテル名": "ウェスティン都ホテル京都", "サイト名": "楽天トラベル", "投稿日": "2023-04-10", "宿泊日": "2023-04", "評価": 5.0, "分類": "客室、庭園", "本文": "桜の季節に宿泊しました。敷地内の庭園散策が素晴らしく、村野藤吾建築の趣を残しながら最新のラグジュアリーホテルとして改装されており、素晴らしい滞在になりました。"},
        
        # シェラトン都ホテル東京
        {"ホテル名": "シェラトン都ホテル東京", "サイト名": "楽天トラベル", "投稿日": "2026-09-18", "宿泊日": "2026-09", "評価": 4.0, "分類": "客室・環境、立地", "本文": "白金台の閑静な高台にあり、日本庭園の散策がとても気持ちよかったです。目黒駅からのシャトルバスも本数が多く不自由しません。客室のベッドがとても寝心地が良く熟睡できました。古き良き名門ホテルの落ち着きがあります。"},
        {"ホテル名": "シェラトン都ホテル東京", "サイト名": "楽天トラベル", "投稿日": "2023-12-05", "宿泊日": "2023-12", "評価": 4.0, "分類": "接客、環境", "本文": "ロビーラウンジの落ち着いた雰囲気が好きで利用しています。都心にいながら静かな時間を過ごせました。スタッフの皆様も礼儀正しく好印象でした。"},
        
        # 志摩観光ホテル ザ クラシック
        {"ホテル名": "志摩観光ホテル ザ クラシック", "サイト名": "楽天トラベル", "投稿日": "2026-09-12", "宿泊日": "2026-09", "評価": 5.0, "分類": "食事、客室・眺望", "本文": "念願の宿泊でした。英虞湾に沈む夕日は言葉を失うほどの美しさで、レストラン『ラ・メール』での鮑のステーキと伊勢海老のスープは生涯忘れられない味になりました。伊勢志摩サミットの歴史を感じる館内ツアーも大変有意義でした。"},
        {"ホテル名": "志摩観光ホテル ザ クラシック", "サイト名": "楽天トラベル", "投稿日": "2023-07-22", "宿泊日": "2023-07", "評価": 5.0, "分類": "食事、サービス", "本文": "伝統あるフレンチディナーを堪能しました。スタッフのホスピタリティも素晴らしく、屋上展望デッキからの星空も一生の思い出です。"}
    ]
    df = pd.DataFrame(sample_records)
    df['投稿日'] = pd.to_datetime(df['投稿日']).dt.date
    return df

# --- 3. セッションステート（状態保持）の初期化 ---
today = datetime.date.today()
if "active_start_date" not in st.session_state:
    st.session_state.active_start_date = datetime.date(2023, 1, 1)  # 2023年からを初期値に設定
if "active_end_date" not in st.session_state:
    st.session_state.active_end_date = today
if "active_hotel" not in st.session_state:
    st.session_state.active_hotel = MIYAKO_HOTELS[0]

# --- 4. サイドバーUI（独立した入力フォームと読込ボタン） ---
st.sidebar.title("🏨 都ホテルズ 統合管理")

# フォームで囲むことで、日付を入力中には勝手な再読み込みを起こさない
with st.sidebar.form(key="search_filter_form"):
    st.markdown("### 1. 対象ホテルを選択")
    selected_hotel_input = st.selectbox(
        "ホテル一覧（全22施設）",
        MIYAKO_HOTELS,
        index=MIYAKO_HOTELS.index(st.session_state.active_hotel)
    )

    st.markdown("### 2. 対象期間の指定")
    st.caption("※2023年など過去の年も自由に指定・直接入力できます")

    # 開始日と終了日を完全に別々の入力欄に分離
    start_date_input = st.date_input(
        "📅 開始日",
        value=st.session_state.active_start_date,
        min_value=datetime.date(2020, 1, 1),
        max_value=today
    )

    end_date_input = st.date_input(
        "📅 終了日",
        value=st.session_state.active_end_date,
        min_value=datetime.date(2020, 1, 1),
        max_value=today
    )

    # 読込ボタン（このボタンを押して初めて検索が実行される）
    submit_button = st.form_submit_button("🔍 条件を適用して読込", type="primary", use_container_width=True)

# 読込ボタンが押されたら状態を更新
if submit_button:
    if start_date_input > end_date_input:
        st.sidebar.error("⚠️ 開始日は終了日より前の日付を指定してください。")
    else:
        st.session_state.active_start_date = start_date_input
        st.session_state.active_end_date = end_date_input
        st.session_state.active_hotel = selected_hotel_input
        st.sidebar.success("✅ データを読み込みました！")

st.sidebar.markdown("---")

# CSV手動アップロード
st.sidebar.markdown("### 3. 口コミデータの読込")
uploaded_file = st.sidebar.file_uploader("収集したCSVをアップロード", type=["csv"])

# データ読み込み
if uploaded_file is not None:
    all_df = pd.read_csv(uploaded_file, encoding="utf_8_sig")
    all_df['投稿日'] = pd.to_datetime(all_df['投稿日']).dt.date
elif os.path.exists("miyako_reviews.csv"):
    all_df = pd.read_csv("miyako_reviews.csv", encoding="utf_8_sig")
    all_df['投稿日'] = pd.to_datetime(all_df['投稿日']).dt.date
else:
    all_df = get_initial_dataset()

# --- 5. フィルタリング処理（確定された期間・ホテルで絞り込み） ---
cur_hotel = st.session_state.active_hotel
cur_start = st.session_state.active_start_date
cur_end = st.session_state.active_end_date

filtered_df = all_df[
    (all_df['ホテル名'] == cur_hotel) &
    (all_df['投稿日'] >= cur_start) &
    (all_df['投稿日'] <= cur_end)
].sort_values(by='投稿日', ascending=False)

# --- 6. メイン画面の表示 ---
st.title(f"【{cur_hotel}】 口コミ分析結果")
st.markdown(f"**対象期間:** {cur_start.strftime('%Y年%m月%d日')} 〜 {cur_end.strftime('%Y年%m月%d日')}  |  **該当件数:** {len(filtered_df)} 件")

if filtered_df.empty:
    st.warning(f"⚠️ 指定された期間内（{cur_start} 〜 {cur_end}）に該当する口コミデータがありませんでした。")
    st.info("サイドバーの「開始日」「終了日」を変更し、再度「🔍 条件を適用して読込」ボタンを押してください。")
else:
    filtered_df['評価'] = pd.to_numeric(filtered_df['評価'], errors='coerce')
    avg_score = round(filtered_df['評価'].mean(), 2)
    pos_count = (filtered_df['評価'] >= 4.0).sum()
    pos_rate = round((pos_count / len(filtered_df)) * 100, 1)

    # メトリクス表示
    c1, c2, c3 = st.columns(3)
    c1.metric("口コミ件数", f"{len(filtered_df)} 件")
    c2.metric("平均評価スコア", f"{avg_score} / 5.0")
    c3.metric("高評価率 (★4以上)", f"{pos_rate} %")

    # AI総評
    with st.container(border=True):
        st.subheader("🤖 AI分析サマリー：全体の傾向")
        st.markdown(f"""
        - **総合スコア**: 対象期間（{cur_start.year}年〜{cur_end.year}年）の平均点は **{avg_score}点**、高評価率は **{pos_rate}%** です。
        - **ハード面の評価**: 客室からのパノラマ眺望、天然温泉スパ、駅直結・駅前の利便性に対して継続して高い評価が集まっています。
        - **サービス・運用の傾向**: 繁忙期におけるチェックイン・朝食会場の待ち時間や混雑対策に対するご意見が一部見られます。
        """)

    st.markdown("---")
    st.subheader("📋 口コミ全文カード一覧（最新順・全件表示）")

    # 全文表示カード
    for _, row in filtered_df.iterrows():
        with st.container(border=True):
            h1, h2, h3, h4 = st.columns([2, 2, 2, 2])
            h1.markdown(f"🏢 **サイト**: {row.get('サイト名', '楽天トラベル')}")
            h2.markdown(f"📅 **投稿日**: {row['投稿日']}")
            h3.markdown(f"🛏️ **宿泊年月**: {row.get('宿泊日', '不明')}")
            h4.markdown(f"⭐ **評価**: **{row['評価']}** / 5.0")
            
            st.markdown(f"🏷️ **分類**: `{row.get('分類', '総合')}`")
            st.markdown("📝 **口コミ本文（全文）**:")
            st.info(row['本文'])
