#%% 
# 0) 설치 및 임포트
import os
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import platform

# Pandas 출력 설정
pd.set_option("display.max_columns", 200)
pd.set_option("display.width", 200)

# -----------------------------------------------------------------------------
# 1) 한글 폰트 설정 및 전역 스타일 (깨짐 방지)
# -----------------------------------------------------------------------------
def apply_korean_font():
    plt.rc('font', family='Pretendard')
    plt.rcParams['axes.unicode_minus'] = False # 마이너스 기호 깨짐 방지
    plt.rcParams['figure.dpi'] = 120

apply_korean_font()

# -----------------------------------------------------------------------------
# 2) Visualization Design System (VIZ)
# -----------------------------------------------------------------------------
VIZ = {
    "pre": "#BDC3C7",           # 개입 전 (회색)
    "post_increase": "#2471A3",  # 증가 (진한 파랑)
    "post_decrease": "#C0392B",  # 감소 (진한 빨강)
    "axis": "#2C3E50",
    "grid": "#F2F4F4",
    "lw_main": 2.5,             
    "lw_connector": 12.0,        
    "lw_ref": 1.2,              
    "ms_pre": 202,               
    "ms_post": 200,             
    "fig_w": 16, "fig_h": 4,
    "font_title": 22,
    "font_label": 16,
    "font_value_main": 18,        # 그래프 주요값(예: pre/post 수치)용
    "font_value_secondary": 16    # 그래프 보조값/작은값(예: 변화율, 라벨 등)용
}

def color_post(diff_value: int) -> str:
    if diff_value > 0: return VIZ["post_increase"]
    if diff_value < 0: return VIZ["post_decrease"]
    return "#7F8C8D"

#%%
# 3) 데이터 로드 및 전처리
file_path = "data.xlsx" 

if not os.path.exists(file_path):
    # 파일이 없을 경우 테스트용 더미 데이터 생성
    data = {"사용자ID": [f"P{i}" for i in range(1, 15)]}
    for d in range(-7, 7): data[str(d)] = np.random.randint(4000, 12000, 14)
    df = pd.DataFrame(data)
else:
    df = pd.read_excel(file_path, sheet_name=0)

# 전처리
pre_days = [str(i) for i in range(-7, 0)]
post_days = ["0"] + [str(i) for i in range(1, 7)]
all_days = pre_days + post_days

for c in all_days:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df["시작전_평균"] = df[pre_days].mean(axis=1).round(0).astype(int)
df["시작후_평균"] = df[post_days].mean(axis=1).round(0).astype(int)
df["차이"] = (df["시작후_평균"] - df["시작전_평균"]).astype(int)
df["변화율"] = ((df["차이"] / df["시작전_평균"]) * 100).round(1)

# ID 자연 정렬용 숫자 추출
df["_id_num"] = df["사용자ID"].astype(str).str.extract(r'(\d+)').astype(int)

#%%
# -----------------------------------------------------------------------------
# 4) 시각화 함수 정의
# -----------------------------------------------------------------------------
def plot_dumbbell(df):
    # ✅ 수정됨: 개입 후 걸음 수 높은 순서대로 정렬 (낮은 순을 원하시면 ascending=True)
    plot_df = df.sort_values("차이", ascending=True).copy()
    y_pos = np.arange(len(plot_df))
    
    # 텍스트가 길어지므로 좌우 여백 확보를 위해 figsize 조절
    fig, ax = plt.subplots(figsize=(VIZ["fig_w"], len(plot_df)*0.6 + 2))
    
    all_vals = np.concatenate([plot_df["시작전_평균"], plot_df["시작후_평균"]])
    x_min, x_max = all_vals.min(), all_vals.max()
    x_range = x_max - x_min
    
    # ✅ 수정됨: 텍스트가 표시될 공간 확보를 위해 x축 범위를 더 넓게 설정 (우측 35% 여유)
    ax.set_xlim(x_min - x_range * 0.1, x_max + x_range * 0.35)

    for i, row in enumerate(plot_df.itertuples()):
        color = color_post(row.차이)
        
        # 커넥터 라인
        ax.hlines(y=i, xmin=min(row.시작전_평균, row.시작후_평균), 
                  xmax=max(row.시작전_평균, row.시작후_평균), 
                  color=color, alpha=0.3, linewidth=VIZ["lw_connector"], zorder=1)
        
        # 점 시각화
        ax.scatter(row.시작전_평균, i, s=VIZ["ms_pre"], color=VIZ["pre"], edgecolor='white', zorder=2)
        ax.scatter(row.시작후_평균, i, s=VIZ["ms_post"], color=color, edgecolor='white', zorder=3)
        
        # ✅ 수정됨: 차이와 변화율을 함께 표시 (예: +1,200 (+15.4%))
        # f-string을 사용하여 차이에는 천 단위 콤마와 부호를, 변화율에는 소수점 첫째자리와 부호를 넣었습니다.
        label_text = f"{row.차이:+,} ({row.변화율:+.1f}%)"
        
        ax.text(max(row.시작전_평균, row.시작후_평균) + (x_range * 0.03), i, label_text, 
                va='center', fontweight='normal', color=color, fontsize=VIZ["font_value_secondary"])

    ax.set_yticks(y_pos)
    ax.set_yticklabels(plot_df["사용자ID"], fontsize=VIZ["font_label"])
    ax.set_xlabel("평균 일일 걸음 수(단위: 보)", fontsize=VIZ["font_label"], labelpad=15)
    ax.tick_params(axis='x', labelsize=VIZ["font_label"])
    ax.tick_params(axis='y', labelsize=VIZ["font_label"])
    
    # 제목
    #ax.set_title("참여자별 걸음 수 변화 및 변화율", loc='center', pad=30, fontsize=VIZ["font_title"], fontweight='bold')
    # fontweight='bold' 또는 weight='bold' 사용
    ax.set_title("참여자 걸음 수 변화", 
             loc='center', 
             pad=30, 
             fontsize=VIZ["font_title"], 
             fontweight='bold') # 이 부분이 핵심입니다.
    
    # 테두리 설정
    BORDER_COLOR = "#999999"
    for spine in ["top", "right", "left", "bottom"]:
        ax.spines[spine].set_visible(True)
        ax.spines[spine].set_color(BORDER_COLOR) 
        ax.spines[spine].set_linewidth(1.0)
        
    ax.grid(axis='x', color=VIZ["grid"], linestyle='-', alpha=0.6, zorder=0)

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='개입 전', markerfacecolor=VIZ["pre"], markersize=12),
        Line2D([0], [0], marker='o', color='w', label='개입 후(증가)', markerfacecolor=VIZ["post_increase"], markersize=12),
        Line2D([0], [0], marker='o', color='w', label='개입 후(감소)', markerfacecolor=VIZ["post_decrease"], markersize=12)
    ]
    
    ax.legend(handles=legend_elements, loc='lower right', frameon=True, 
              facecolor='white', framealpha=0.8, edgecolor=BORDER_COLOR,
              fontsize=VIZ["font_label"])

    plt.subplots_adjust(left=0.1, right=0.9, top=0.85, bottom=0.15)
    plt.show()
#%%
# -----------------------------------------------------------------------------
# 5) 최종 실행
# -----------------------------------------------------------------------------
# Long format 및 매핑 준비
df_long = df.melt(id_vars=["사용자ID"], value_vars=all_days, var_name="Day", value_name="걸음수")
df_long["Day"] = df_long["Day"].astype(int)
diff_map = dict(zip(df["사용자ID"].astype(str), df["차이"].astype(int)))

# 덤벨 플롯 출력
plot_dumbbell(df)
# %%
