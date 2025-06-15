import streamlit as st
import pandas as pd

# Настройки страницы
st.set_page_config(page_title="Retention / Churn Rate Анализ")
st.title("📈 Анализ Retention и Churn Rate для групповых занятий")

# Выбор метрики
metric_type = st.selectbox("Выберите метрику для анализа:", ["Retention Rate", "Churn Rate"])

# Загрузка файла
uploaded_file = st.file_uploader("Загрузите выгрузку (.xlsx)", type="xlsx")

if uploaded_file:
    # Чтение Excel файла
    df = pd.read_excel(uploaded_file)

    # Определяем нужные столбцы
    date_col = next((col for col in df.columns if "date" in col.lower()), None)
    name_col = next((col for col in df.columns if "name" in col.lower()), None)
    session_col = next((col for col in df.columns if "group session" in col.lower()), None)

    if not all([date_col, name_col, session_col]):
        st.error("Файл должен содержать столбцы с датой посещения (Date), именем клиента (Name) и типом занятия (Group Session).")
    else:
        # Преобразуем дату
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
        df = df.dropna(subset=[date_col])

        # Только групповые занятия
        group_sessions = ['CROSSFIT', 'CROSSFIT LITE', 'GYM', 'GYMNASTICS', 'THE LONG WOD', 'WEIGHTLIFTING']
        df = df[df[session_col].isin(group_sessions)]

        if df.empty:
            st.warning("Нет данных по групповым занятиям за выбранный период.")
        else:
            df['YearMonth'] = df[date_col].dt.to_period('M')

            # Выбор дат
            min_date = df[date_col].min()
            max_date = df[date_col].max()
            start_date = st.date_input("Начальная дата", min_value=min_date.date(), value=min_date.date())
            end_date = st.date_input("Конечная дата", min_value=min_date.date(), max_value=max_date.date(), value=max_date.date())

            # Фильтрация по выбранному периоду
            mask = (df[date_col] >= pd.to_datetime(start_date)) & (df[date_col] <= pd.to_datetime(end_date))
            filtered_df = df.loc[mask]

            if filtered_df.empty:
                st.warning("Нет данных в выбранном диапазоне дат.")
            else:
                # Группировка по клиенту и месяцу
                visits = filtered_df.groupby([name_col, 'YearMonth']).size().reset_index(name='Visits')
                pivot = visits.pivot(index=name_col, columns='YearMonth', values='Visits').fillna(0)
                pivot = pivot.sort_index(axis=1)

                result = {}
                months = list(pivot.columns)

                for i in range(len(months) - 1):
                    this_month = pivot[months[i]] > 0
                    next_month = pivot[months[i+1]] > 0
                    total_clients = this_month.sum()

                    if total_clients == 0:
                        continue

                    if metric_type == "Retention Rate":
                        retained = (this_month & next_month).sum()
                        value = round((retained / total_clients) * 100, 2)
                    else:
                        churned = (this_month & ~next_month).sum()
                        value = round((churned / total_clients) * 100, 2)

                    result[str(months[i])] = value

                result_df = pd.DataFrame(result.items(), columns=["Месяц", f"{metric_type} (%)"])

                # Сортировка
                if st.checkbox("Сортировать от большего к меньшему"):
                    result_df = result_df.sort_values(by=result_df.columns[1], ascending=False)

                # Вывод результата
                st.subheader(f"📊 {metric_type} по месяцам")
                st.dataframe(result_df)

                # Скачивание результата
                st.download_button(
                    label="📥 Скачать результат в CSV",
                    data=result_df.to_csv(index=False).encode('utf-8'),
                    file_name="retention_churn_result.csv",
                    mime="text/csv"
                )
