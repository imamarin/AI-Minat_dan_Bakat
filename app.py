import streamlit as st
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
from fpdf import FPDF
import io

st.set_page_config(page_title="Deteksi Minat & Bakat Siswa", page_icon="🎓")

st.title("📊 Kenan AI - Sistem Deteksi Minat & Bakat Siswa")
st.caption("Aplikasi ini membantu mendeteksi minat dan bakat siswa berdasarkan nilai pelajaran mereka.")

# -----------------------------
# Upload Excel
# -----------------------------
file = st.file_uploader("Upload file Excel nilai siswa", type=["xlsx"])

if file:
    df = pd.read_excel(file)

    if "Nama" not in df.columns:
        st.error("File harus memiliki kolom 'Nama'")
    else:
        # st.subheader("📄 Data Siswa")
        # st.dataframe(df)

        # -----------------------------
        # Normalisasi nilai
        # -----------------------------
        nilai_df = df.drop(columns=["Nama"])
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(nilai_df)

        # -----------------------------
        # KMeans clustering
        # -----------------------------
        kmeans = KMeans(n_clusters=3, random_state=42)
        df["Cluster"] = kmeans.fit_predict(X_scaled)

        # -----------------------------
        # Tentukan label cluster otomatis
        # -----------------------------
        cluster_means = df.groupby("Cluster").mean(numeric_only=True)

        def get_label(row):
            cluster_id = row["Cluster"]
            avg_scores = cluster_means.loc[cluster_id]

            bidang_tertinggi = avg_scores.drop("Cluster", errors="ignore").idxmax()
            if bidang_tertinggi in ["Matematika", "Fisika", "Biologi"]:
                return "Sains & Teknologi"
            elif bidang_tertinggi in ["Seni_Budaya", "Bahasa_Indonesia"]:
                return "Seni & Kreatif"
            elif bidang_tertinggi in ["Ekonomi", "Sosiologi"]:
                return "Sosial & Bisnis"
            else:
                return "Campuran"

        df["Cluster_Label"] = df.apply(get_label, axis=1)

        st.subheader("📌 Hasil Clustering")
        st.dataframe(df[["Nama", "Cluster", "Cluster_Label"]])

        # -----------------------------
        # Visualisasi
        # -----------------------------
        st.subheader("📊 Distribusi Cluster")
        cluster_count = df["Cluster_Label"].value_counts()
        fig, ax = plt.subplots()
        cluster_count.plot(kind='bar', ax=ax)
        plt.xticks(rotation=30)
        st.pyplot(fig)

        # -----------------------------
        # Export ke Excel
        # -----------------------------
        @st.cache_data
        def convert_excel(dataframe):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                dataframe.to_excel(writer, index=False)
            return output.getvalue()

        excel_data = convert_excel(df)
        st.download_button(
            label="⬇️ Download Rekap Excel",
            data=excel_data,
            file_name="hasil_cluster.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        # -----------------------------
        # Export Laporan PDF Individu
        # -----------------------------
        def export_pdf(nama, cluster, label):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)

            pdf.cell(200, 10, txt="Laporan Hasil Deteksi Minat & Bakat", ln=True, align='C')
            pdf.ln(10)
            pdf.cell(200, 10, txt=f"Nama: {nama}", ln=True)
            pdf.cell(200, 10, txt=f"Cluster: {cluster}", ln=True)
            pdf.cell(200, 10, txt=f"Label Minat & Bakat: {label}", ln=True)

            return pdf.output(dest="S").encode("latin-1")

        st.subheader("📑 Export PDF Individu")
        selected_student = st.selectbox("Pilih siswa", df["Nama"].unique())
        if st.button("Download PDF Individu"):
            row = df[df["Nama"] == selected_student].iloc[0]
            pdf_data = export_pdf(row["Nama"], row["Cluster"], row["Cluster_Label"])
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_data,
                file_name=f"laporan_{row['Nama']}.pdf",
                mime="application/pdf"
            )
