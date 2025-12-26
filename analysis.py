#%%
# 0) 설치 및 임포트
# 필요한 패키지: pandas, openpyxl, scipy, matplotlib
import os
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

pd.set_option("display.max_columns", 200)
pd.set_option("display.width", 200)


#%%
# 1) 데이터 점검

# 1.1 데이터 로드
file_path = "data.xlsx"

if not os.path.exists(file_path):
    raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

xls = pd.ExcelFile(file_path)
print("시트 목록:", xls.sheet_names)

sheet_to_load = "Raw_Wide" if "Raw_Wide" in xls.sheet_names else xls.sheet_names[0]
df = pd.read_excel(file_path, sheet_name=sheet_to_load)

print("로드한 시트:", sheet_to_load)
display(df.head()) if "display" in globals() else print(df.head())


print("행, 열 개수:", df.shape)
print("\n컬럼 목록:")
print(list(df.columns))

if "사용자ID" in df.columns:
    print("\n참가자 수(고유 사용자ID):", df["사용자ID"].nunique())
    print("사용자ID 목록:", sorted(df["사용자ID"].astype(str).unique()))
else:
    print("\n경고: 사용자ID 컬럼이 없습니다. 사용자 식별값이 있는지 확인하세요.")


# 1.2 결측치, 타입, 중복 점검
print("\n데이터 타입:")
print(df.dtypes)

print("\n결측치 개수(컬럼별):")
print(df.isna().sum())

if "사용자ID" in df.columns:
    dup = df["사용자ID"].duplicated().sum()
    print("\n중복 사용자ID 행 수:", dup)

# 1.3 분석에 사용할 Day 컬럼 정의
# 시작 전: -7 ~ -1 (7일)
# 시작 후: 0 ~ 6 (7일)
pre_days = [str(i) for i in range(-7, 0)]
post_days = ["0"] + [str(i) for i in range(1, 7)]
all_days = pre_days + post_days

missing_pre = [c for c in pre_days if c not in df.columns]
missing_post = [c for c in post_days if c not in df.columns]

if missing_pre or missing_post:
    raise ValueError(
        "필요한 Day 컬럼이 없습니다.\n"
        f"없는 pre 컬럼: {missing_pre}\n"
        f"없는 post 컬럼: {missing_post}\n"
        "엑셀의 컬럼명이 -7,-6,... 형태로 정확한지 확인하세요."
    )

for c in all_days:
    df[c] = pd.to_numeric(df[c], errors="coerce")

print("Day 컬럼 준비 완료:", all_days)


#%%
# 2) Visualization Design System (colors, sizes, lines)

VIZ = {
    # semantic colors
    "pre": "#909090",           # 개입 전(중립)
    "post_increase": "#2F6BFF",  # 개입 후(증가)
    "post_decrease": "#E5484D",  # 개입 후(감소)
    "post_nochange": "#8A8A8A",  # 개입 후(변화없음)

    # general
    "axis": "#4A4A4A",
    "grid": "#E6E6E6",
    "ref_line": "#9AA0A6",

    # linewidths / sizes
    "lw_main": 2,
    "lw_ref": 1,
    "ms_pre": 40,
    "ms_post": 55,

    # figure
    "fig_w": 10,
    "fig_h": 6,
    "dpi": 120,
}

def color_post(diff_value: int) -> str:
    if diff_value > 0:
        return VIZ["post_increase"]
    if diff_value < 0:
        return VIZ["post_decrease"]
    return VIZ["post_nochange"]

def apply_viz_style():
    plt.rcParams["figure.dpi"] = VIZ["dpi"]
    plt.rcParams["axes.edgecolor"] = VIZ["axis"]
    plt.rcParams["axes.labelcolor"] = VIZ["axis"]
    plt.rcParams["xtick.color"] = VIZ["axis"]
    plt.rcParams["ytick.color"] = VIZ["axis"]
    plt.rcParams["grid.color"] = VIZ["grid"]
    plt.rcParams["grid.linewidth"] = VIZ["lw_ref"]
    plt.rcParams["axes.grid"] = True

apply_viz_style()


#%%
# 3) 기술통계
# 3.1. 원시 걸음수 기술통계 요약 (참가자별)
df["전체_평균(-7~6)"] = df[all_days].mean(axis=1).round(1).astype(int)
df["전체_표준편차(-7~6)"] = df[all_days].std(axis=1, ddof=1).round(1).astype(int)
df["전체_최소(-7~6)"] = df[all_days].min(axis=1).astype(int)
df["전체_최대(-7~6)"] = df[all_days].max(axis=1).astype(int)

cols_to_show = (["사용자ID"] if "사용자ID" in df.columns else []) + [
    "전체_평균(-7~6)", "전체_표준편차(-7~6)", "전체_최소(-7~6)", "전체_최대(-7~6)"
]

print(
    df[cols_to_show]
    .sort_values(by="전체_평균(-7~6)")
    .to_string(index=False)
)

# 3.2. 개인 단위 요약 지표 계산 (반올림 → 정수)
df["시작전_평균"] = df[pre_days].mean(axis=1).round(1).astype(int)
df["시작후_평균"] = df[post_days].mean(axis=1).round(1).astype(int)
df["차이"] = (df["시작후_평균"] - df["시작전_평균"]).astype(int)
df["변화율_%"] = ((df["차이"] / df["시작전_평균"]) * 100).round(1).astype(int)

cols = (["사용자ID"] if "사용자ID" in df.columns else []) + [
    "시작전_평균", "시작후_평균", "차이", "변화율_%"
]

print(
    df[cols]
    .sort_values(by="차이")
    .to_string(index=False)
)

diff = df["차이"].dropna()
n = int(diff.shape[0])


#%%
# 4) 시각화 A: Dumbbell plot (여백 개선 버전)

plot_df = df.sort_values("차이").copy()
y = np.arange(len(plot_df))

plt.figure(figsize=(VIZ["fig_w"], VIZ["fig_h"]))

# 🔧 전체 레이아웃 여백
plt.subplots_adjust(left=0.22, right=0.97, top=0.90, bottom=0.12)

# 🔧 x축 범위 먼저 고정
x_min = min(plot_df["시작전_평균"].min(), plot_df["시작후_평균"].max())
x_max = max(plot_df["시작전_평균"].max(), plot_df["시작후_평균"].max())
x_pad = (x_max - x_min) * 0.08
plt.xlim(x_min - x_pad, x_max + x_pad)

text_offset = -x_pad * 0.35

for j, row in enumerate(plot_df.itertuples(index=False)):
    post_c = color_post(int(row.차이))

    plt.plot(
        [row.시작전_평균, row.시작후_평균],
        [j, j],
        color=post_c,
        linewidth=VIZ["lw_main"]
    )

    plt.scatter(row.시작전_평균, j, color=VIZ["pre"], s=VIZ["ms_pre"], zorder=3)
    plt.scatter(row.시작후_평균, j, color=post_c, s=VIZ["ms_post"], zorder=3)

    # 사용자ID 텍스트 (박스 포함)
    text_x = row.시작전_평균 + text_offset if row.차이 >= 0 else row.시작후_평균 + text_offset

    plt.text(
        text_x, j, str(row.사용자ID),
        ha="right", va="center",
        fontsize=9,
        color=VIZ.get("label", "#222"),
        zorder=4,
        bbox=dict(
            boxstyle="round,pad=0.15",
            facecolor="white",
            edgecolor="none",
            alpha=0.75
        )
    )

plt.yticks(y, plot_df["사용자ID"])
plt.xlabel("Average daily steps")
plt.title("Change in average steps (Pre vs Post)")

from matplotlib.lines import Line2D
legend_elements = [
    Line2D([0], [0], color=VIZ["post_increase"], lw=VIZ["lw_main"], label="Increase"),
    Line2D([0], [0], color=VIZ["post_decrease"], lw=VIZ["lw_main"], label="Decrease"),
]
plt.legend(handles=legend_elements)

plt.show()

#%%
# 8) 시각화 B: 개인별 전/후 평균 막대그래프 (후=증가/감소 색상)
plot_df = df.sort_values("차이").copy()
ids = plot_df["사용자ID"]
x = np.arange(len(ids))
width = 0.35

post_colors = [color_post(int(v)) for v in plot_df["차이"]]

plt.figure(figsize=(VIZ["fig_w"], VIZ["fig_h"]))
plt.bar(x - width/2, plot_df["시작전_평균"], width, label="Pre", color=VIZ["pre"])
plt.bar(x + width/2, plot_df["시작후_평균"], width, label="Post", color=post_colors)

plt.xticks(x, ids, rotation=45)
plt.ylabel("Average daily steps")
plt.title("Average daily steps before and after intervention")

from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=VIZ["pre"], label="Pre"),
    Patch(facecolor=VIZ["post_increase"], label="Post (Increase)"),
    Patch(facecolor=VIZ["post_decrease"], label="Post (Decrease)"),
]
plt.legend(handles=legend_elements)
plt.tight_layout()
plt.show()

#%%
# P4,P7,P8,P9,P10,P11,P12,P14
# 8) 시각화 B: 개인별 전/후 평균 막대그래프 (후=증가/감소 색상)
plot_df = df.assign(차이_절대값=df["차이"].abs()) \
             .sort_values("차이_절대값", ascending=False) \
             .copy()

ids = plot_df["사용자ID"]
x = np.arange(len(ids))
width = 0.35

post_colors = [color_post(int(v)) for v in plot_df["차이"]]

plt.figure(figsize=(VIZ["fig_w"], VIZ["fig_h"]))
plt.bar(x - width/2, plot_df["시작전_평균"], width, label="Pre", color=VIZ["pre"])
plt.bar(x + width/2, plot_df["시작후_평균"], width, label="Post", color=post_colors)

plt.xticks(x, ids, rotation=45)
plt.ylabel("Average daily steps")
plt.title("Average daily steps before and after intervention")

from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=VIZ["pre"], label="Pre"),
    Patch(facecolor=VIZ["post_increase"], label="Post (Increase)"),
    Patch(facecolor=VIZ["post_decrease"], label="Post (Decrease)"),
]
plt.legend(handles=legend_elements)
plt.tight_layout()
plt.show()

#%%
# 1) 정규성 검정을 위한 차이값 정의
# H0/H1 검정의 대상은 (개입 후 - 개입 전)

diff = df["차이"].dropna()

print("차이값 요약")
print("표본수 n:", diff.shape[0])
print("평균:", diff.mean())
print("표준편차:", diff.std(ddof=1))

# 2) Shapiro–Wilk 정규성 검정

shapiro_stat, shapiro_p = stats.shapiro(diff)

print("Shapiro–Wilk 통계량:", round(float(shapiro_stat), 3))
print("Shapiro–Wilk p-value:", round(float(shapiro_p), 4))

if shapiro_p >= 0.05:
    print("결론: 차이값은 정규분포를 따른다고 볼 수 있음 (정규성 가정 충족)")
else:
    print("결론: 차이값이 정규분포를 따른다고 보기 어려움 (비모수 검정 고려)")


# 비모수 검정: Wilcoxon signed-rank test (단측)
# H1: 개입 후 걸음수 > 개입 전 걸음수

diff = df["차이"].dropna()

wil_stat, wil_p = stats.wilcoxon(
    diff,
    alternative="greater"  # 단측: post > pre
)

print("Wilcoxon signed-rank stat:", wil_stat)
print("Wilcoxon p-value (one-sided, post > pre):", round(float(wil_p), 4))

if wil_p < 0.05:
    print("결론: 개입 후 걸음수가 개입 전보다 유의하게 큼 (H0 기각)")
else:
    print("결론: 개입 전후 걸음수 차이가 유의하지 않음 (H0 기각 불가)")
# Wilcoxon 효과크기: rank-biserial correlation (근사)

abs_diff = diff.abs()
ranks = stats.rankdata(abs_diff)

W_plus = np.sum(ranks[diff > 0])
W_minus = np.sum(ranks[diff < 0])

r_rb = (W_plus - W_minus) / (W_plus + W_minus)

print("Rank-biserial correlation:", round(float(r_rb), 3))
#%%
# 12) 정규성 검정: Shapiro-Wilk (차이값)
shapiro_stat, shapiro_p = stats.shapiro(diff)
print("Shapiro-Wilk stat:", round(float(shapiro_stat), 3))
print("Shapiro-Wilk p-value:", round(float(shapiro_p), 4))


#%%
# 13) Paired t-test (양측) + 효과크기 + 95% CI
t_stat, t_p = stats.ttest_rel(df["시작후_평균"], df["시작전_평균"], nan_policy="omit")
print("Paired t-test t:", round(float(t_stat), 3))
print("Paired t-test p (two-sided):", round(float(t_p), 4))

mean_diff = float(diff.mean())
sd_diff = float(diff.std(ddof=1))
cohen_dz = (mean_diff / sd_diff) if sd_diff != 0 else np.nan
print("Cohen's dz:", round(float(cohen_dz), 3) if not np.isnan(cohen_dz) else np.nan)

dfree = n - 1
alpha = 0.05
tcrit = stats.t.ppf(1 - alpha/2, dfree)
se = sd_diff / np.sqrt(n) if n > 0 else np.nan
ci_low = mean_diff - tcrit * se
ci_high = mean_diff + tcrit * se
print("Mean difference 95% CI:", (round(ci_low, 1), round(ci_high, 1)))


#%%
# 14) 비모수 검정: Wilcoxon signed-rank (양측) + rank-biserial(근사)
wil_stat, wil_p = stats.wilcoxon(diff, zero_method="wilcox", alternative="two-sided", method="auto")
print("Wilcoxon stat:", round(float(wil_stat), 3))
print("Wilcoxon p (two-sided):", round(float(wil_p), 4))

abs_diff = diff.abs()
ranks = stats.rankdata(abs_diff)
W_plus = float(np.sum(ranks[diff > 0]))
W_minus = float(np.sum(ranks[diff < 0]))
r_rb = (W_plus - W_minus) / (W_plus + W_minus) if (W_plus + W_minus) != 0 else np.nan
print("Rank-biserial correlation (approx):", round(float(r_rb), 3) if not np.isnan(r_rb) else np.nan)


#%%
# 16) 엑셀 저장 (요약 + 검정 결과 + long format)
out_path = "analysis_results_7vs7.xlsx"

base_cols = [c for c in ["사용자ID", "출생년도", "나이"] if c in df.columns]
participant_summary_cols = base_cols + ["시작전_평균", "시작후_평균", "차이", "변화율_%"]
participant_summary = df[participant_summary_cols].copy()

tests = pd.DataFrame({
    "검정": ["Shapiro-Wilk", "Paired t-test", "Wilcoxon"],
    "통계량": [shapiro_stat, t_stat, wil_stat],
    "p값(양측)": [shapiro_p, t_p, wil_p],
})

effect_sizes = pd.DataFrame({
    "지표": ["Cohen's dz", "Mean diff 95% CI low", "Mean diff 95% CI high", "Rank-biserial (approx)"],
    "값": [cohen_dz, ci_low, ci_high, r_rb],
})

df_long = df.melt(
    id_vars=base_cols,
    value_vars=all_days,
    var_name="Day",
    value_name="걸음수"
)
df_long["Day"] = df_long["Day"].astype(int)

with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
    participant_summary.to_excel(writer, sheet_name="Participant_Summary", index=False)
    tests.to_excel(writer, sheet_name="Tests", index=False)
    effect_sizes.to_excel(writer, sheet_name="Effect_Sizes", index=False)
    df_long.to_excel(writer, sheet_name="Long_7vs7", index=False)

print("엑셀 저장 완료:", out_path)
#%%
# 시각화 D: 참여자별 날짜별 걸음수 변화
# - P1, P2, P3, ... 순서 보장
# - point 값 표시
# - y축 여백
# - 개입 전/후 평균선(dashed) 추가

# long format 준비
if "df_long" not in globals():
    df_long = df.melt(
        id_vars=["사용자ID"],
        value_vars=all_days,
        var_name="Day",
        value_name="걸음수"
    )
    df_long["Day"] = df_long["Day"].astype(int)

# 🔑 사용자ID 숫자 추출 → 정렬 키
df_long["_pid_num"] = (
    df_long["사용자ID"]
    .astype(str)
    .str.extract(r"(\d+)", expand=False)
    .astype(int)
)

# 사용자별 차이 매핑 (색상용)
diff_map = dict(zip(df["사용자ID"].astype(str), df["차이"].astype(int)))

# 🔑 숫자 기준 정렬 후 groupby (sort=False 중요)
for pid, g in (
    df_long
    .sort_values(["_pid_num", "Day"])
    .groupby("사용자ID", sort=False)
):
    pid = str(pid)

    line_color = color_post(diff_map.get(pid, 0))

    plt.figure(figsize=(VIZ["fig_w"], VIZ["fig_h"]))

    # ===== 1) 실제 일별 변화 (실선) =====
    plt.plot(
        g["Day"],
        g["걸음수"],
        linewidth=VIZ["lw_main"],
        color=line_color,
        marker="o",
        markersize=5
    )

    # ===== 2) 개입 전 / 후 평균 계산 =====
    pre_mean = g.loc[g["Day"] < 0, "걸음수"].mean()
    post_mean = g.loc[g["Day"] >= 0, "걸음수"].mean()

    # ===== 3) 평균선 (점선) =====
    plt.hlines(
        y=pre_mean,
        xmin=g["Day"].min(),
        xmax=-0.05,
        colors=VIZ["pre"],
        linestyles="dashed",
        linewidth=VIZ["lw_ref"]
    )

    plt.hlines(
        y=post_mean,
        xmin=0.05,
        xmax=g["Day"].max(),
        colors=line_color,
        linestyles="dashed",
        linewidth=VIZ["lw_ref"]
    )

    # ===== 4) y축 여백 =====
    y_min = g["걸음수"].min()
    y_max = g["걸음수"].max()
    y_range = y_max - y_min

    plt.ylim(
        y_min - y_range * 0.05,
        y_max + y_range * 0.15
    )

    # ===== 5) point 위에 값 표시 =====
    for _, r in g.iterrows():
        if pd.notna(r["걸음수"]):
            plt.text(
                r["Day"],
                r["걸음수"] + y_range * 0.03,
                f"{int(r['걸음수'])}",
                ha="center",
                va="bottom",
                fontsize=9,
                color=VIZ["axis"]
            )

    # ===== 6) 개입 시작일 기준선 =====
    plt.axvline(
        x=0,
        color=VIZ["ref_line"],
        linestyle="--",
        linewidth=VIZ["lw_ref"]
    )

    # ===== 7) 전/후 영역 시각적 구분 =====
    plt.axvspan(g["Day"].min(), -0.001, alpha=0.06, color=VIZ["pre"])
    plt.axvspan(0, g["Day"].max(), alpha=0.05, color=line_color)

    plt.xticks(list(range(-7, 7)))
    plt.xlabel("Day (0 = intervention start)")
    plt.ylabel("Daily steps")
    plt.title(f"Daily step trajectory – {pid}")

    plt.tight_layout()
    plt.show()
# %%
#%%
# 시각화 E: 참여자별 요일 기준 걸음수 변화 (1명씩)

# 요일 컬럼 없으면 생성
if "Weekday" not in df_long.columns:
    df_long["Weekday"] = df_long["Day"] % 7

# 사용자ID 숫자 기준 정렬
df_long["_pid_num"] = (
    df_long["사용자ID"]
    .astype(str)
    .str.extract(r"(\d+)")
    .astype(int)
)

diff_map = dict(zip(df["사용자ID"].astype(str), df["차이"].astype(int)))

for pid, g in (
    df_long
    .sort_values("_pid_num")
    .groupby("사용자ID", sort=False)
):
    pid = str(pid)
    g = g.sort_values("Day")

    line_color = color_post(diff_map.get(pid, 0))

    plt.figure(figsize=(VIZ["fig_w"], VIZ["fig_h"]))

    # 개입 전 / 후 분리
    g_pre = g[g["Day"] < 0]
    g_post = g[g["Day"] >= 0]

    # 개입 전 (얇은 선)
    plt.plot(
        g_pre["Weekday"],
        g_pre["걸음수"],
        marker="o",
        linestyle="-",
        linewidth=VIZ["lw_ref"],
        color=VIZ["pre"],
        label="Pre"
    )

    # 개입 후 (굵은 선)
    plt.plot(
        g_post["Weekday"],
        g_post["걸음수"],
        marker="o",
        linestyle="-",
        linewidth=VIZ["lw_main"],
        color=line_color,
        label="Post"
    )

    # point 값 표시
    y_min = g["걸음수"].min()
    y_max = g["걸음수"].max()
    y_range = y_max - y_min

    for _, r in g.iterrows():
        plt.text(
            r["Weekday"],
            r["걸음수"] + y_range * 0.03,
            f"{int(r['걸음수'])}",
            ha="center",
            va="bottom",
            fontsize=9,
            color=VIZ["axis"]
        )

    plt.xticks(range(7), ["0", "1", "2", "3", "4", "5", "6"])
    plt.xlabel("Weekday index (0–6)")
    plt.ylabel("Daily steps")
    plt.title(f"Weekly pattern (Pre vs Post) – {pid}")

    plt.tight_layout()
    plt.show()
# %%
#%%
# 시각화: 요일별 집단 평균 (Pre vs Post)
# 요일 인덱스 생성 (0~6)
if "Weekday" not in df_long.columns:
    df_long["Weekday"] = df_long["Day"] % 7
    
# 개입 전 / 후 구분
df_long["Phase"] = np.where(df_long["Day"] < 0, "Pre", "Post")

weekday_mean = (
    df_long
    .groupby(["Weekday", "Phase"])["걸음수"]
    .mean()
    .reset_index()
)
print(weekday_mean)

plt.figure(figsize=(VIZ["fig_w"], VIZ["fig_h"]))

for phase, color, lw in [
    ("Pre", VIZ["pre"], VIZ["lw_ref"]),
    ("Post", VIZ["post_increase"], VIZ["lw_main"])
]:
    sub = weekday_mean[weekday_mean["Phase"] == phase]
    plt.plot(
        sub["Weekday"],
        sub["걸음수"],
        marker="o",
        linewidth=lw,
        color=color,
        label=phase
    )

plt.xticks(range(7), ["0", "1", "2", "3", "4", "5", "6"])
plt.xlabel("Weekday index (0–6)")
plt.ylabel("Mean daily steps (participants)")
plt.title("Mean steps by weekday (Pre vs Post)")

plt.legend()
plt.tight_layout()
plt.show()
# %%
