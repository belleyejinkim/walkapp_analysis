#%%
# import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import platform

# -----------------------------------------------------------------------------
# 1) 한글 폰트 설정 및 전역 스타일
# -----------------------------------------------------------------------------
def apply_korean_font():
    system_os = platform.system()
    if system_os == "Windows":
        plt.rc('font', family='Malgun Gothic')
    elif system_os == "Darwin":
        plt.rc('font', family='AppleGothic')
    else:
        plt.rc('font', family='NanumBarunGothic') 

    plt.rcParams['axes.unicode_minus'] = False 
    plt.rcParams['figure.dpi'] = 120

apply_korean_font()

# -----------------------------------------------------------------------------
# 2) Visualization Design System (VIZ)
# -----------------------------------------------------------------------------
VIZ = {
    "pre": "#BDC3C7",           
    "post_increase": "#2471A3",  
    "post_decrease": "#C0392B",  
    "axis": "#2C3E50",
    "grid": "#F2F4F4",
    "border": "#999999",        
    "lw_connector": 6.0,        
    "ms_pre": 100,              
    "ms_post": 100,             
    "fig_w": 14, 
    "font_title": 18, 
    "font_label": 12, 
    "font_val": 10
}

def color_post(diff_value):
    if diff_value > 0: return VIZ["post_increase"]
    if diff_value < 0: return VIZ["post_decrease"]
    return "#7F8C8D"

# -----------------------------------------------------------------------------
# 3) 데이터 로드 및 전처리
# -----------------------------------------------------------------------------
file_path = "data.xlsx" 
if os.path.exists(file_path):
    df = pd.read_excel(file_path, sheet_name=0)
    pre_cols = [str(i) for i in range(-7, 0)]
    post_cols = ["0"] + [str(i) for i in range(1, 7)]
    all_cols = pre_cols + post_cols
    for c in all_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    df["시작전_평균"] = df[pre_cols].mean(axis=1).round(0).astype(int)
    df["시작후_평균"] = df[post_cols].mean(axis=1).round(0).astype(int)
    df["차이"] = (df["시작후_평균"] - df["시작전_평균"]).astype(int)
    df["변화율"] = ((df["차이"] / df["시작전_평균"]) * 100).round(1)
    df["_id_num"] = df["사용자ID"].astype(str).str.extract(r'(\d+)').astype(int)

# -----------------------------------------------------------------------------
# 4) 시각화 함수 정의
# -----------------------------------------------------------------------------

# A. 수직형 덤벨 플롯 (절대 수치 변화)
def plot_dumbbell_vertical(df):
    plot_df = df.sort_values("차이", ascending=False).copy()
    x_pos = np.arange(len(plot_df))
    
    fig, ax = plt.subplots(figsize=(VIZ["fig_w"], 8))
    
    all_vals = np.concatenate([plot_df["시작전_평균"], plot_df["시작후_평균"]])
    y_min, y_max = all_vals.min(), all_vals.max()
    y_range = y_max - y_min
    
    ax.set_ylim(y_min - y_range * 0.3, y_max + y_range * 0.3)

    for i, row in enumerate(plot_df.itertuples()):
        color = color_post(row.차이)
        ax.vlines(x=i, ymin=min(row.시작전_평균, row.시작후_평균), 
                  ymax=max(row.시작전_평균, row.시작후_평균), 
                  color=color, alpha=0.3, linewidth=VIZ["lw_connector"], zorder=1)
        
        ax.scatter(i, row.시작전_평균, s=VIZ["ms_pre"], color=VIZ["pre"], edgecolor='white', zorder=2)
        ax.scatter(i, row.시작후_평균, s=VIZ["ms_post"], color=color, edgecolor='white', zorder=3)
        
        diff_text = f"{row.차이:+,}"
        ax.text(i, max(row.시작전_평균, row.시작후_평균) + (y_range * 0.05), diff_text, 
                ha='center', va='bottom', fontweight='bold', color=color, fontsize=VIZ["font_val"])

    ax.set_xticks(x_pos)
    ax.set_xticklabels(plot_df["사용자ID"], fontsize=VIZ["font_label"])
    ax.set_ylabel("평균 일일 걸음 수(보)", fontsize=VIZ["font_label"], labelpad=15)
    ax.set_title("참여자 걸음 수 변화", loc='center', pad=30, fontsize=VIZ["font_title"], fontweight='bold')
    
    BORDER_COLOR = "#999999"
    for spine in ["top", "right", "left", "bottom"]:
        ax.spines[spine].set_visible(True)
        ax.spines[spine].set_color(BORDER_COLOR)
        ax.spines[spine].set_linewidth(1.0)
        
    ax.grid(axis='y', color=VIZ["grid"], linestyle='-', alpha=0.6, zorder=0)

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='개입 전', markerfacecolor=VIZ["pre"], markersize=10),
        Line2D([0], [0], marker='o', color='w', label='개입 후(증가)', markerfacecolor=VIZ["post_increase"], markersize=10),
        Line2D([0], [0], marker='o', color='w', label='개입 후(감소)', markerfacecolor=VIZ["post_decrease"], markersize=10)
    ]
    # ✅ 수정됨: loc='upper right' -> loc='lower right'
    ax.legend(handles=legend_elements, loc='lower right', frameon=True, facecolor='white', framealpha=0.8, edgecolor=BORDER_COLOR)

    plt.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.15)
    plt.show()

# B. 수직형 변화율 덤벨 차트
def plot_change_rate_dumbbell_vertical(df):
    plot_df = df.sort_values("_id_num", ascending=False).copy()
    x_pos = np.arange(len(plot_df))
    
    fig, ax = plt.subplots(figsize=(VIZ["fig_w"], 8))
    ax.set_ylim(-60, 80)

    for i, row in enumerate(plot_df.itertuples()):
        color = color_post(row.변화율)
        ax.vlines(x=i, ymin=min(0, row.변화율), ymax=max(0, row.변화율), 
                  color=color, alpha=0.3, linewidth=VIZ["lw_connector"], zorder=1)
        ax.scatter(i, row.변화율, s=VIZ["ms_post"], color=color, edgecolor='white', zorder=3)
        ax.text(i, row.변화율 + (80 * 0.05 if row.변화율 >= 0 else -80 * 0.05), 
                f"{row.변화율:+.1f}%", ha='center', va='bottom' if row.변화율 >= 0 else 'top',
                fontweight='bold', color=color, fontsize=VIZ["font_val"])

    ax.set_xticks(x_pos)
    ax.set_xticklabels(plot_df["사용자ID"], fontsize=VIZ["font_label"])
    ax.set_ylabel("걸음 수 변화율 (%)", fontsize=VIZ["font_label"], labelpad=15)
    ax.set_title("참여자 걸음 수 변화", loc='center', pad=30, fontsize=VIZ["font_title"], fontweight='bold')
    
    BORDER_COLOR = "#999999"
    for spine in ["top", "right", "left", "bottom"]:
        ax.spines[spine].set_visible(True)
        ax.spines[spine].set_color(BORDER_COLOR)
        
    ax.grid(axis='y', color=VIZ["grid"], linestyle='-', alpha=0.6, zorder=0)
    ax.axhline(0, color=BORDER_COLOR, linewidth=1, zorder=1)

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='개입 후(증가)', markerfacecolor=VIZ["post_increase"], markersize=10),
        Line2D([0], [0], marker='o', color='w', label='개입 후(감소)', markerfacecolor=VIZ["post_decrease"], markersize=10)
    ]
    # ✅ 수정됨: loc='upper right' -> loc='lower right'
    ax.legend(handles=legend_elements, loc='lower right', frameon=True, facecolor='white', framealpha=0.8, edgecolor=BORDER_COLOR)

    plt.subplots_adjust(left=0.1, right=0.95, top=0.85, bottom=0.15)
    plt.show()

# -----------------------------------------------------------------------------
# 5) 최종 실행
# -----------------------------------------------------------------------------
plot_dumbbell_vertical(df)
plot_change_rate_dumbbell_vertical(df)
# %%


