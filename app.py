import streamlit as st
import json
import pandas as pd
from datetime import datetime
import io

# 初始化全局日志状态（跨刷新保留）
if 'logs' not in st.session_state:
    st.session_state.logs = []

def add_log(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.logs.append(f"[{current_time}] {message}")

# 页面配置
st.set_page_config(page_title="文本分类测评系统 v2", page_icon="🏆", layout="wide")
st.title("🏆 违法有害信息文本分类测评系统 (带错题下载功能)")
st.markdown("请分别上传标准答案与预测结果 JSON 文件，系统将自动计算 5 分制得分并生成错题集。")

# 文件上传区
col1, col2 = st.columns(2)
with col1:
    truth_file = st.file_uploader("上传标准答案 JSON (Ground Truth)", type="json")
with col2:
    pred_file = st.file_uploader("上传预测结果 JSON (Prediction)", type="json")

# 评测逻辑
if st.button("开始评测", type="primary"):
    if truth_file is None or pred_file is None:
        st.error("请先上传标准答案和预测结果文件！")
        add_log("错误：用户未完全上传标准答案或预测结果文件。")
    else:
        try:
            add_log("📂 开始读取上传的文件...")
            truth_data = json.load(truth_file)
            pred_data = json.load(pred_file)
            
            truth_results = truth_data.get("results", [])
            pred_results = pred_data.get("results", [])
            
            if not truth_results or not pred_results:
                st.error("JSON 格式错误：未找到必要的 'results' 字段！")
                add_log("错误：解析失败，缺少 results 列表。")
            else:
                # 兼容 sampleld 和 sampleId 两种拼写，统一转换为字符串格式
                truth_dict = {str(item.get("sampleld", item.get("sampleId"))).strip(): str(item.get("answer")).strip() for item in truth_results}
                pred_dict = {str(item.get("sampleld", item.get("sampleId"))).strip(): str(item.get("answer")).strip() for item in pred_results}
                
                correct_count = 0
                error_details = []
                
                # 开始比对
                for sample_id, true_label in truth_dict.items():
                    pred_label = pred_dict.get(sample_id, "⚠️ 缺失预测（未在预测文件中找到该ID）")
                    
                    if pred_label == true_label:
                        correct_count += 1
                    else:
                        error_details.append({
                            "样本 ID": sample_id,
                            "真实标签 (Ground Truth)": true_label,
                            "模型预测标签 (Prediction)": pred_label
                        })
                
                total_samples = len(truth_dict)
                accuracy = correct_count / total_samples if total_samples > 0 else 0
                
                # 算分逻辑：最高分为 5 分
                score = accuracy * 5
                
                # 将本次得分写入日志（最前部或者追加）
                log_summary = f"📈 运行结果 -> 样本总数: {total_samples} | 错误数: {len(error_details)} | 准确率: {accuracy:.2%} | 本次得分: {score:.2f}分 / 5.00分"
                add_log(log_summary)
                
                # 渲染结果面板
                st.divider()
                res_col1, res_col2 = st.columns(2)
                with res_col1:
                    st.metric(label="📊 综合准确率 (Accuracy)", value=f"{accuracy:.2%}")
                with res_col2:
                    st.metric(label="💯 本次评测评分 (满分 5.0)", value=f"{score:.2f} / 5.0分")
                
                # 错题处理板块
                st.subheader("❌ 错题在线预览与下载")
                if error_details:
                    df_errors = pd.DataFrame(error_details)
                    
                    # 1. 在线预览
                    st.write("以下是本次运行的错题明细（可在表格内滚动预览）：")
                    st.dataframe(df_errors, use_container_width=True)
                    
                    # 2. 内存中生成 Excel 文件供下载
                    buffer = io.BytesIO()
                    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                        df_errors.to_excel(writer, index=False, sheet_name='错题集')
                    
                    # 下载按钮
                    current_date = datetime.now().strftime("%m%d_%H%M")
                    st.download_button(
                        label="📥 下载本次错题集 (Excel 格式)",
                        data=buffer.getvalue(),
                        file_name=f"错题反馈_{current_date}_得分_{score:.2f}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.success("🎉 太厉害了！本次预测完全正确，得分：5.0分！没有生成错题集。")
                    
        except Exception as e:
            st.error(f"解析过程中发生错误：{str(e)}")
            add_log(f"💥 系统异常：{str(e)}")

# 日志展示区
st.divider()
st.subheader("📝 系统运行日志（包含历史得分记录）")
# 倒序排列日志，让最新的记录显示在最上面
log_text = "\n".join(reversed(st.session_state.logs))
st.text_area("Logs", value=log_text, height=250, disabled=True, label_visibility="collapsed")
