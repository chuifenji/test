import streamlit as st
import json
import pandas as pd
from datetime import datetime

# 初始化日志状态
if 'logs' not in st.session_state:
    st.session_state.logs = []


def add_log(message):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.logs.append(f"[{current_time}] {message}")


# 页面配置
st.set_page_config(page_title="文本分类测评系统", page_icon="🏆", layout="wide")
st.title("🏆 违法有害信息文本分类测评系统")
st.markdown("请分别上传包含 `results` 字段的标准答案与预测结果 JSON 文件。")

# 文件上传区
col1, col2 = st.columns(2)
with col1:
    truth_file = st.file_uploader("上传标准答案 JSON (Ground Truth)", type="json")
with col2:
    pred_file = st.file_uploader("上传预测结果 JSON (Prediction)", type="json")

# 评测逻辑
if st.button("开始评测", type="primary"):
    st.session_state.logs = []  # 清空历史日志

    if truth_file is None or pred_file is None:
        st.error("请先上传标准答案和预测结果文件！")
        add_log("错误：文件未完全上传。")
    else:
        try:
            add_log("文件读取成功，开始解析 JSON...")
            truth_data = json.load(truth_file)
            pred_data = json.load(pred_file)

            truth_results = truth_data.get("results", [])
            pred_results = pred_data.get("results", [])

            if not truth_results or not pred_results:
                st.error("JSON 格式错误：未找到 'results' 字段！")
                add_log("错误：解析失败，缺少必要的 results 字段。")
            else:
                add_log(f"解析完成：标准答案 {len(truth_results)} 条，预测结果 {len(pred_results)} 条。")

                # 将数据转换为字典以便比对
                truth_dict = {item.get("sampleld", item.get("sampleId")): str(item.get("answer")) for item in
                              truth_results}
                pred_dict = {item.get("sampleld", item.get("sampleId")): str(item.get("answer")) for item in
                             pred_results}

                correct_count = 0
                error_details = []

                add_log("开始进行数据比对...")
                for sample_id, true_label in truth_dict.items():
                    pred_label = pred_dict.get(sample_id, "缺失")

                    if pred_label == true_label:
                        correct_count += 1
                    else:
                        error_details.append({
                            "样本 ID": sample_id,
                            "真实标签": true_label,
                            "预测标签": pred_label
                        })

                total_samples = len(truth_dict)
                accuracy = correct_count / total_samples if total_samples > 0 else 0

                add_log(f"评测完成。比对样本总数：{total_samples}，正确数：{correct_count}。")

                # 展示结果
                st.divider()
                st.metric(label="📊 综合准确率 (Accuracy)", value=f"{accuracy:.2%}")

                st.subheader("❌ 错误数据明细")
                if error_details:
                    df_errors = pd.DataFrame(error_details)
                    st.dataframe(df_errors, use_container_width=True)
                else:
                    st.success("恭喜！所有预测完全正确。")

        except Exception as e:
            st.error(f"发生错误：{str(e)}")
            add_log(f"系统异常：{str(e)}")

# 日志展示区
st.divider()
st.subheader("📝 系统运行日志")
log_text = "\n".join(st.session_state.logs)
st.text_area("Logs", value=log_text, height=200, disabled=True, label_visibility="collapsed")