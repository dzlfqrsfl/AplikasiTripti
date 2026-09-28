from datetime import datetime, timedelta, timezone
import json
import os
from fpdf import FPDF
import pandas as pd
import streamlit as st

# Zona Waktu Indonesia Barat (WIB / UTC+7)
WIB = timezone(timedelta(hours=7))

# --- PENCARIAN FILE LOGO UNTUK TAB BROWSER (FAVICON) ---
favicon_file = "LogoTripti.jpeg"
for nama_file in [
    "LogoTripti.jpeg",
    "LogoTripti.jpg",
    "LogoTripti.PNG",
    "logo_tripti.jpeg",
    "logo_tripti.jpg",
]:
  if os.path.exists(nama_file):
    favicon_file = nama_file
    break

# Konfigurasi Halaman (Wide Layout)
st.set_page_config(
    page_title="Tripti - POS Kasir & Produksi",
    page_icon=favicon_file if os.path.exists(favicon_file) else "🛒",
    layout="wide",
)

# --- CUSTOM CSS KARTU PRODUK & TAMPILAN PROFESIONAL ---
st.markdown(
    """
    <style>
    .stApp { background-color: #f1f5f9; }
    
    /* Styling Kartu Produk Biru Estetik */
    .product-card {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 8px;
    }
    
    div.stButton > button {
        background-color: #f97316;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    div.stButton > button:hover {
        background-color: #ea580c;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- SISTEM PENYIMPANAN LOKAL & FITUR BACKUP/RESTORE ---
DB_FILE = "tripti_database.json"


def load_data():
  if os.path.exists(DB_FILE):
    try:
      with open(DB_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        if "stok_setengah_jadi" not in data:
          data["stok_setengah_jadi"] = []
        if "master_resep" not in data:
          data["master_resep"] = []
        if "bahan_mentah" not in data:
          data["bahan_mentah"] = []
        if "produk_jual" not in data:
          data["produk_jual"] = []
        if "produksi_setengah_jadi" not in data:
          data["produksi_setengah_jadi"] = []
        if "komposisi_produk_jual" not in data:
          data["komposisi_produk_jual"] = {}
        if "tipe_pesanan_list" not in data:
          data["tipe_pesanan_list"] = [
              "Dine In",
              "Takeaway",
              "GoFood",
              "GrabFood",
              "ShopeeFood",
          ]
        if "transaksi" not in data:
          data["transaksi"] = []
        return data
    except Exception:
      pass
  return None


def save_data():
  data = {
      "bahan_mentah": st.session_state.bahan_mentah.to_dict(orient="records"),
      "stok_setengah_jadi": st.session_state.stok_setengah_jadi.to_dict(
          orient="records"
      ),
      "master_resep": st.session_state.master_resep.to_dict(orient="records"),
      "produksi_setengah_jadi": st.session_state.produksi_setengah_jadi.to_dict(
          orient="records"
      ),
      "produk_jual": st.session_state.produk_jual.to_dict(orient="records"),
      "komposisi_produk_jual": st.session_state.komposisi_produk_jual,
      "tipe_pesanan_list": st.session_state.tipe_pesanan_list,
      "transaksi": st.session_state.transaksi,
  }
  with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


# Load data dari file JSON
saved_db = load_data()

# Inisialisasi Session State dengan konversi angka bulat
if "initialized" not in st.session_state:
  if saved_db:
    st.session_state.bahan_mentah = pd.DataFrame(
        saved_db.get("bahan_mentah", []),
        columns=["Nama Bahan", "Stok", "Satuan"],
    )
    if not st.session_state.bahan_mentah.empty:
      st.session_state.bahan_mentah["Stok"] = (
          st.session_state.bahan_mentah["Stok"].astype(float).astype(int)
      )

    st.session_state.stok_setengah_jadi = pd.DataFrame(
        saved_db.get("stok_setengah_jadi", []),
        columns=["Nama Barang Setengah Jadi", "Stok", "Satuan"],
    )
    if not st.session_state.stok_setengah_jadi.empty:
      st.session_state.stok_setengah_jadi["Stok"] = (
          st.session_state.stok_setengah_jadi["Stok"].astype(float).astype(int)
      )

    st.session_state.master_resep = pd.DataFrame(
        saved_db.get("master_resep", []),
        columns=["Nama Resep", "Hasil Jadi", "Satuan Hasil", "Komposisi Bahan"],
    )
    if not st.session_state.master_resep.empty:
      st.session_state.master_resep["Hasil Jadi"] = (
          st.session_state.master_resep["Hasil Jadi"].astype(float).astype(int)
      )

    st.session_state.produksi_setengah_jadi = pd.DataFrame(
        saved_db.get("produksi_setengah_jadi", []),
        columns=[
            "Waktu",
            "Nama Resep / Barang",
            "Jumlah Hasil",
            "Satuan Hasil",
            "Bahan Terpakai",
        ],
    )
    if not st.session_state.produksi_setengah_jadi.empty:
      st.session_state.produksi_setengah_jadi["Jumlah Hasil"] = (
          st.session_state.produksi_setengah_jadi["Jumlah Hasil"]
          .astype(float)
          .astype(int)
      )

    st.session_state.produk_jual = pd.DataFrame(
        saved_db.get("produk_jual", []),
        columns=["Nama Produk", "Harga Jual", "Stok Produk", "SKU"],
    )
    if not st.session_state.produk_jual.empty:
      st.session_state.produk_jual["Harga Jual"] = (
          st.session_state.produk_jual["Harga Jual"].astype(float).astype(int)
      )
      st.session_state.produk_jual["Stok Produk"] = (
          st.session_state.produk_jual["Stok Produk"].astype(float).astype(int)
      )

    st.session_state.komposisi_produk_jual = saved_db.get(
        "komposisi_produk_jual", {}
    )
    st.session_state.tipe_pesanan_list = saved_db.get(
        "tipe_pesanan_list",
        ["Dine In", "Takeaway", "GoFood", "GrabFood", "ShopeeFood"],
    )
    st.session_state.transaksi = saved_db.get("transaksi", [])
  else:
    st.session_state.bahan_mentah = pd.DataFrame(
        columns=["Nama Bahan", "Stok", "Satuan"]
    )
    st.session_state.stok_setengah_jadi = pd.DataFrame(
        columns=["Nama Barang Setengah Jadi", "Stok", "Satuan"]
    )
    st.session_state.master_resep = pd.DataFrame(
        columns=["Nama Resep", "Hasil Jadi", "Satuan Hasil", "Komposisi Bahan"]
    )
    st.session_state.produksi_setengah_jadi = pd.DataFrame(
        columns=[
            "Waktu",
            "Nama Resep / Barang",
            "Jumlah Hasil",
            "Satuan Hasil",
            "Bahan Terpakai",
        ]
    )
    st.session_state.produk_jual = pd.DataFrame(
        columns=["Nama Produk", "Harga Jual", "Stok Produk", "SKU"]
    )
    st.session_state.komposisi_produk_jual = {}
    st.session_state.tipe_pesanan_list = [
        "Dine In",
        "Takeaway",
        "GoFood",
        "GrabFood",
        "ShopeeFood",
    ]
    st.session_state.transaksi = []

  st.session_state.initialized = True

if "cart" not in st.session_state:
  st.session_state.cart = {}
if "last_receipt" not in st.session_state:
  st.session_state.last_receipt = None


# Fungsi Helper Garis Putus-Putus PDF
def draw_dashed_line(pdf, x1, x2, y, dash_length=1.5, space_length=1.0):
  current_x = x1
  while current_x < x2:
    next_x = min(current_x + dash_length, x2)
    pdf.line(current_x, y, next_x, y)
    current_x = next_x + space_length


# Fungsi Struk PDF
def generate_tripti_receipt(
    items_dibeli,
    subtotal,
    diskon,
    packaging_fee,
    order_fee,
    pajak,
    total_bayar,
    waktu,
    no_nota,
    nama_kasir,
    tipe_pesanan,
    nama_pelanggan,
    no_urutan,
):
  pdf = FPDF(orientation="P", unit="mm", format=(80, 235))
  pdf.add_page()
  pdf.set_font("Courier", "B", 10)

  x1, x2 = 5, 75

  pdf.cell(0, 5, "Tripti", 0, 1, "C")
  pdf.set_font("Courier", "", 7)
  pdf.multi_cell(
      0,
      3,
      "Perumahan Legok Permai, Cluster Kaliandra, Blok K2/E4. Kel. Legok,"
      " Kec. Legok, Kab. Tangerang, Banten",
      0,
      "C",
  )

  pdf.ln(2)
  draw_dashed_line(pdf, x1, x2, pdf.get_y())
  pdf.ln(2)

  pdf.set_font("Courier", "B", 8)
  pdf.cell(0, 4, "[ STRUK TAGIHAN PEMBAYARAN ]", 0, 1, "C")

  pdf.ln(2)
  draw_dashed_line(pdf, x1, x2, pdf.get_y())
  pdf.ln(2)

  pdf.set_font("Courier", "", 7)
  pdf.cell(0, 4, f"WAKTU PESANAN : {waktu}", 0, 1, "L")
  pdf.cell(0, 4, f"NO NOTA       : #{no_nota}", 0, 1, "L")
  pdf.cell(0, 4, f"PELANGGAN     : {nama_pelanggan}", 0, 1, "L")
  pdf.cell(0, 4, f"KASIR         : {nama_kasir}", 0, 1, "L")
  pdf.cell(0, 4, f"TIPE          : {tipe_pesanan}", 0, 1, "L")
  pdf.cell(0, 4, f"URUTAN        : {no_urutan}", 0, 1, "L")

  pdf.ln(2)
  draw_dashed_line(pdf, x1, x2, pdf.get_y())
  pdf.ln(2)

  total_qty_produk = 0
  for item in items_dibeli:
    pdf.set_font("Courier", "B", 8)
    pdf.cell(0, 4, item["nama"], 0, 1, "L")
    pdf.set_font("Courier", "", 8)
    pdf.cell(
        0,
        4,
        f"  {item['qty']}x      Rp {int(item['subtotal']):,.0f}".replace(
            ",", "."
        ),
        0,
        1,
        "L",
    )
    pdf.cell(
        0,
        4,
        f"  (@Rp {int(item['harga']):,.0f})".replace(",", "."),
        0,
        1,
        "L",
    )
    total_qty_produk += item["qty"]

  pdf.ln(2)
  draw_dashed_line(pdf, x1, x2, pdf.get_y())
  pdf.ln(2)

  def print_row(label, val):
    pdf.cell(35, 4, label, 0, 0, "L")
    pdf.cell(5, 4, ":", 0, 0, "C")
    pdf.cell(
        0,
        4,
        f"Rp {int(val):,.0f}".replace(",", ".")
        if isinstance(val, (int, float))
        else val,
        0,
        1,
        "R",
    )

  print_row("SUB TOTAL", subtotal)
  pdf.cell(0, 4, f"{total_qty_produk} PRODUK", 0, 1, "L")
  print_row("DISKON (-)", diskon)
  print_row("BIAYA PACKAGING (+)", packaging_fee)
  print_row("ORDER FEE (+)", order_fee)
  print_row("PAJAK (+)", pajak)
  print_row("PEMBULATAN", 0)

  pdf.ln(2)
  draw_dashed_line(pdf, x1, x2, pdf.get_y())
  pdf.ln(2)

  pdf.set_font("Courier", "B", 9)
  print_row("TOTAL TAGIHAN", total_bayar)

  pdf.ln(3)
  draw_dashed_line(pdf, x1, x2, pdf.get_y())
  pdf.ln(2)

  qris_file = "qris.jpeg"
  for q_name in ["qris.jpeg", "qris.jpg", "qris.png", "QRIS.jpeg", "QRIS.jpg"]:
    if os.path.exists(q_name):
      qris_file = q_name
      break

  if os.path.exists(qris_file):
    pdf.set_font("Courier", "B", 8)
    pdf.cell(0, 4, "SCAN QRIS UNTUK PEMBAYARAN", 0, 1, "C")
    pdf.ln(1)
    pdf.image(qris_file, x=22, y=pdf.get_y(), w=36)
    pdf.ln(38)

  pdf.set_font("Courier", "", 7)
  pdf.cell(0, 3, "***", 0, 1, "C")
  pdf.cell(0, 3, "Terima kasih atas pesanan Anda.", 0, 1, "C")
  pdf.cell(0, 3, "Simpan struk ini sebagai bukti tagihan.", 0, 1, "C")
  pdf.cell(0, 3, "***", 0, 1, "C")

  filename = f"struk_{no_nota}.pdf"
  pdf.output(filename)
  return filename


# --- JUDUL UTAMA & SIDEBAR BACKUP ---
st.markdown("### 🏷️ TRIPTI - POS Kasir & Produksi")

with st.sidebar:
  st.markdown("### 💾 Manajemen Database")
  if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
      db_json_bytes = f.read()
    st.download_button(
        label="📥 Download Backup Data",
        data=db_json_bytes,
        file_name="tripti_database.json",
        mime="application/json",
    )

  uploaded_db_file = st.file_uploader(
      "📤 Restore File Backup", type=["json"]
  )
  if uploaded_db_file is not None:
    try:
      restored_data = json.load(uploaded_db_file)
      with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(restored_data, f, ensure_ascii=False, indent=4)
      st.success("Database berhasil dipulihkan! Silakan refresh halaman.")
    except Exception as e:
      st.error(f"Gagal memulihkan file: {e}")

# --- NAVIGASI MENGGUNAKAN TAB HORIZONTAL DI ATAS ---
menu_tabs = st.tabs([
    "POS Kasir Utama",
    "Riwayat Pesanan",
    "Tipe Pesanan",
    "Kelola Produk Jadi",
    "Produksi & Resep",
    "Bahan Mentah",
])

# -------------------------------------------------------------------------
# TAB 1: POS KASIR UTAMA
# -------------------------------------------------------------------------
with menu_tabs[0]:
  st.markdown("### 🛒 POS Kasir Utama")
  col_main, col_cart = st.columns([2, 1])

  with col_main:
    c_srch1, c_srch2, c_srch3 = st.columns([2, 1, 1])
    with c_srch1:
      cari_konsumen = st.text_input("Nama Pelanggan", placeholder="")
    with c_srch2:
      nama_kasir = st.selectbox("Kasir", ["Dzulfiqar", "Nida", "Saeful I"])
    with c_srch3:
      pilih_tipe_pesanan = st.selectbox(
          "Tipe Pesanan", st.session_state.tipe_pesanan_list
      )

    st.markdown("#### Daftar Produk Siap Jual")
    if st.session_state.produk_jual.empty:
      st.info(
          "Belum ada produk. Tambahkan di menu 'Kelola Produk Jadi'."
      )
    else:
      with st.form("form_pembelian_qty"):
        cols = st.columns(2)
        pesanan_input = []
        ada_error_stok = False

        for idx, row in st.session_state.produk_jual.iterrows():
          with cols[idx % 2]:
            st.markdown(
                f"""
                        <div class="product-card">
                            <h3 style="color:white; margin:0;">{row['Nama Produk']}</h3>
                            <p style="margin:5px 0; font-size:12px;">SKU: {row['SKU']} | Stok: {row['Stok Produk']}</p>
                            <h2 style="color:white; margin:5px 0;">Rp {int(row['Harga Jual']):,}</h2>
                        </div>
                        """,
                unsafe_allow_html=True,
            )
            q_input = st.number_input(
                f"Jumlah Beli ({row['Nama Produk']})",
                min_value=0,
                value=0,
                step=1,
                format="%d",
                key=f"input_qty_{idx}",
            )

            if q_input > int(row["Stok Produk"]):
              st.error(
                  f"Stok '{row['Nama Produk']}' tidak cukup! Tersedia:"
                  f" {row['Stok Produk']}"
              )
              ada_error_stok = True
            elif q_input > 0:
              pesanan_input.append({
                  "index": idx,
                  "nama": row["Nama Produk"],
                  "harga": float(row["Harga Jual"]),
                  "qty": int(q_input),
                  "subtotal": float(row["Harga Jual"]) * int(q_input),
              })

          st.markdown("---")

        submitted_input_cart = st.form_submit_button(
            "➕ Masukkan ke Keranjang"
        )

        if submitted_input_cart:
          if ada_error_stok:
            st.error(
                "Tidak dapat memproses karena ada produk yang melebihi stok"
                " tersedia!"
            )
          elif pesanan_input:
            for item in pesanan_input:
              p_name = item["nama"]
              st.session_state.cart[p_name] = {
                  "index": item["index"],
                  "harga": item["harga"],
                  "qty": item["qty"],
              }
            st.success("Produk berhasil dimasukkan ke keranjang!")
            st.rerun()
          else:
            st.warning("Isi jumlah Qty minimal 1 pada produk yang ingin dibeli.")

  with col_cart:
    st.markdown("### 🛒 Keranjang Belanja")

    if not st.session_state.cart:
      st.info("Keranjang kosong. Ketik Qty di bawah produk.")
    else:
      subtotal_cart = 0
      item_list = []

      for p_name, data in list(st.session_state.cart.items()):
        sub = data["harga"] * data["qty"]
        subtotal_cart += sub
        item_list.append({
            "index": data["index"],
            "nama": p_name,
            "harga": data["harga"],
            "qty": data["qty"],
            "subtotal": sub,
        })

        c_k1, c_k2, c_k3 = st.columns([2, 1, 1])
        with c_k1:
          st.write(f"**{p_name}**")
          st.caption(f"Rp {int(data['harga']):,} x {data['qty']}")
        with c_k2:
          if st.button("➕", key=f"plus_{p_name}"):
            idx_p = data["index"]
            stok_s = int(
                st.session_state.produk_jual.loc[idx_p, "Stok Produk"]
            )
            if st.session_state.cart[p_name]["qty"] + 1 > stok_s:
              st.error("Stok tidak mencukupi!")
            else:
              st.session_state.cart[p_name]["qty"] += 1
              st.rerun()
        with c_k3:
          if st.button("➖", key=f"min_{p_name}"):
            st.session_state.cart[p_name]["qty"] -= 1
            if st.session_state.cart[p_name]["qty"] <= 0:
              del st.session_state.cart[p_name]
            st.rerun()

      st.markdown("---")
      diskon = st.number_input(
          "Diskon (Rp)", min_value=0, value=0, step=500, format="%d"
      )
      packaging_fee = st.number_input(
          "Biaya Packaging / Frozen (+)",
          min_value=0,
          value=0,
          step=500,
          format="%d",
      )
      order_fee = st.number_input(
          "Order Fee / Ongkir (+)", min_value=0, value=0, step=500, format="%d"
      )
      pajak = st.number_input(
          "Pajak (+)", min_value=0, value=0, step=500, format="%d"
      )

      total_bayar = (
          subtotal_cart - diskon
      ) + packaging_fee + order_fee + pajak

      st.markdown(
          f"### **Total Tagihan: Rp {int(total_bayar):,}**",
          unsafe_allow_html=True,
      )

      if st.button("💳 PROSES & CETAK STRUK TAGIHAN", key="btn_bayar"):
        stok_cukup = True
        for item in item_list:
          idx_p = item["index"]
          stok_sekarang = int(
              st.session_state.produk_jual.loc[idx_p, "Stok Produk"]
          )
          if stok_sekarang < item["qty"]:
            stok_cukup = False
            st.error(
                f"Stok produk '{item['nama']}' tidak cukup! Tersedia"
                f" {stok_sekarang}, dibeli {item['qty']}."
            )
            break

        if stok_cukup:
          for item in item_list:
            idx_p = item["index"]
            p_name = item["nama"]
            q_qty = item["qty"]

            st.session_state.produk_jual.loc[idx_p, "Stok Produk"] = (
                int(st.session_state.produk_jual.loc[idx_p, "Stok Produk"])
                - q_qty
            )

            if p_name in st.session_state.komposisi_produk_jual:
              for sj_name, sj_need_per_unit in st.session_state.komposisi_produk_jual[
                  p_name
              ].items():
                total_need_sj = sj_need_per_unit * q_qty
                sj_match_idx = st.session_state.stok_setengah_jadi.index[
                    st.session_state.stok_setengah_jadi[
                        "Nama Barang Setengah Jadi"
                    ]
                    == sj_name
                ]
                if not sj_match_idx.empty:
                  current_sj_stok = int(
                      st.session_state.stok_setengah_jadi.loc[
                          sj_match_idx[0], "Stok"
                      ]
                  )
                  st.session_state.stok_setengah_jadi.loc[
                      sj_match_idx[0], "Stok"
                  ] = max(0, current_sj_stok - total_need_sj)

          waktu_str = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
          no_nota = f"PW{datetime.now(WIB).strftime('%d%H%M')}"
          nama_pelanggan_final = (
              cari_konsumen.strip() if cari_konsumen else "Umum"
          )

          pdf_file = generate_tripti_receipt(
              item_list,
              subtotal_cart,
              diskon,
              packaging_fee,
              order_fee,
              pajak,
              total_bayar,
              waktu_str,
              no_nota,
              nama_kasir,
              pilih_tipe_pesanan,
              nama_pelanggan_final,
              1,
          )

          st.session_state.transaksi.append({
              "Waktu": waktu_str,
              "No Nota": no_nota,
              "Kasir": nama_kasir,
              "Konsumen": nama_pelanggan_final,
              "Tipe Pesanan": pilih_tipe_pesanan,
              "Total Bayar": total_bayar,
              "File Struk": pdf_file,
              "Rincian Item": item_list,
          })

          save_data()

          st.session_state.last_receipt = pdf_file
          st.session_state.cart = {}
          st.success(
              "Transaksi Sukses! Stok produk jadi & setengah jadi telah"
              " terpotong."
          )
          st.rerun()

    if st.session_state.last_receipt and os.path.exists(
        st.session_state.last_receipt
    ):
      st.markdown("---")
      with open(st.session_state.last_receipt, "rb") as f:
        st.download_button(
            label="📥 Unduh Struk Tagihan Terakhir",
            data=f,
            file_name=st.session_state.last_receipt,
            mime="application/pdf",
        )

# -------------------------------------------------------------------------
# TAB 2: RIWAYAT & STORY PEMESANAN
# -------------------------------------------------------------------------
with menu_tabs[1]:
  st.header("📜 Riwayat & Story Pemesanan")
  st.info(
      "Daftar transaksi yang berhasil diproses. Anda dapat membatalkan pesanan"
      " untuk mengembalikan stok produk."
  )

  if not st.session_state.transaksi:
    st.info("Belum ada riwayat transaksi yang tercatat.")
  else:
    for i, trx in enumerate(reversed(st.session_state.transaksi)):
      orig_idx = len(st.session_state.transaksi) - 1 - i

      with st.expander(
          f"Nota: #{trx['No Nota']} | {trx['Waktu']} | Pelanggan:"
          f" {trx['Konsumen']} | Rp {int(trx['Total Bayar']):,}"
      ):
        st.write(f"**Nama Konsumen:** {trx['Konsumen']}")
        st.write(f"**Kasir Bertugas:** {trx['Kasir']}")
        st.write(
            f"**Tipe Pesanan:** {trx.get('Tipe Pesanan', 'Dine In')}"
        )
        st.write(f"**Waktu Transaksi:** {trx['Waktu']}")

        st.markdown("#### Daftar Item Dibeli:")
        for itm in trx["Rincian Item"]:
          st.write(
              f"- {itm['nama']} ({itm['qty']}x) @Rp"
              f" {int(itm['harga']):,} = Rp {int(itm['subtotal']):,}"
          )

        st.markdown(f"### **Total: Rp {int(trx['Total Bayar']):,}**")

        c_dl, c_void = st.columns(2)
        with c_dl:
          if os.path.exists(trx["File Struk"]):
            with open(trx["File Struk"], "rb") as f:
              st.download_button(
                  label=f"📥 Unduh Ulang Struk",
                  data=f,
                  file_name=trx["File Struk"],
                  mime="application/pdf",
                  key=f"dl_history_{orig_idx}",
              )

        with c_void:
          if st.button(
              f"❌ Batalkan Transaksi #{trx['No Nota']}",
              key=f"cancel_trx_{orig_idx}",
          ):
            for itm in trx["Rincian Item"]:
              p_name = itm["nama"]
              q_bought = itm["qty"]
              match_idx = st.session_state.produk_jual.index[
                  st.session_state.produk_jual["Nama Produk"] == p_name
              ]
              if not match_idx.empty:
                st.session_state.produk_jual.loc[match_idx[0], "Stok Produk"] = (
                    int(st.session_state.produk_jual.loc[match_idx[0], "Stok Produk"])
                    + q_bought
                )

            if os.path.exists(trx["File Struk"]):
              try:
                os.remove(trx["File Struk"])
              except Exception:
                pass

            st.session_state.transaksi.pop(orig_idx)
            save_data()
            st.success(
                f"Transaksi #{trx['No Nota']} dibatalkan & stok produk"
                " dikembalikan!"
            )
            st.rerun()

# -------------------------------------------------------------------------
# TAB 3: PENGATURAN TIPE PESANAN
# -------------------------------------------------------------------------
with menu_tabs[2]:
  st.header("⚙️ Pengaturan Tipe Pesanan")

  with st.form("form_tambah_tipe"):
    baru_tipe = st.text_input("Nama Tipe Pesanan Baru")
    if st.form_submit_button("Tambah Tipe Pesanan") and baru_tipe:
      if baru_tipe.strip() not in st.session_state.tipe_pesanan_list:
        st.session_state.tipe_pesanan_list.append(baru_tipe.strip())
        save_data()
        st.success(f"Tipe pesanan '{baru_tipe.strip()}' berhasil ditambahkan!")
      else:
        st.warning("Tipe pesanan tersebut sudah ada dalam daftar.")

  st.markdown("---")
  st.subheader("Daftar Tipe Pesanan Saat Ini:")

  tipe_ser = pd.DataFrame(
      st.session_state.tipe_pesanan_list, columns=["Tipe Pesanan"]
  )
  edited_tipe = st.data_editor(
      tipe_ser, num_rows="dynamic", use_container_width=True
  )

  if st.button("💾 Simpan Perubahan Tipe Pesanan"):
    st.session_state.tipe_pesanan_list = edited_tipe[
        "Tipe Pesanan"
    ].dropna().tolist()
    save_data()
    st.success("Daftar tipe pesanan berhasil diperbarui!")

# -------------------------------------------------------------------------
# TAB 4: KELOLA MENU & STOK PRODUK JADI
# -------------------------------------------------------------------------
with menu_tabs[3]:
  st.header("🍽️ Kelola Menu Produk & Stok Jadi")

  with st.form("form_menu"):
    nm = st.text_input("Nama Produk Siap Jual")
    hrg = st.number_input(
        "Harga Jual (Rp)", min_value=0, value=0, step=500, format="%d"
    )
    stk_prod = st.number_input(
        "Jumlah Stok Produk Jadi Ditambahkan",
        min_value=0,
        value=0,
        step=1,
        format="%d",
    )
    sku = st.text_input("Kode SKU")

    st.markdown("---")
    st.markdown("#### Komposisi Barang Setengah Jadi untuk Produk Ini")

    komposisi_produk_input = {}
    if not st.session_state.stok_setengah_jadi.empty:
      for idx_sj, row_sj in st.session_state.stok_setengah_jadi.iterrows():
        qty_butuh_sj = st.number_input(
            f"Jumlah {row_sj['Nama Barang Setengah Jadi']} ({row_sj['Satuan']}) yang dibutuhkan per 1 produk",
            min_value=0,
            value=0,
            step=1,
            format="%d",
            key=f"komp_sj_{idx_sj}",
        )
        if qty_butuh_sj > 0:
          komposisi_produk_input[row_sj["Nama Barang Setengah Jadi"]] = (
              qty_butuh_sj
          )
    else:
      st.warning(
          "Belum ada data Stok Setengah Jadi. Buat dulu di menu 'Produksi &"
          " Resep'."
      )

    if st.form_submit_button("Simpan Produk & Komposisinya") and nm:
      existing_idx = st.session_state.produk_jual.index[
          st.session_state.produk_jual["Nama Produk"].str.lower()
          == nm.strip().lower()
      ]

      if not existing_idx.empty:
        idx_e = existing_idx[0]
        st.session_state.produk_jual.loc[idx_e, "Stok Produk"] = (
            int(st.session_state.produk_jual.loc[idx_e, "Stok Produk"])
            + int(stk_prod)
        )
        st.session_state.produk_jual.loc[idx_e, "Harga Jual"] = int(hrg)
      else:
        new_p = pd.DataFrame(
            [{
                "Nama Produk": nm.strip(),
                "Harga Jual": int(hrg),
                "Stok Produk": int(stk_prod),
                "SKU": sku,
            }]
        )
        st.session_state.produk_jual = pd.concat(
            [st.session_state.produk_jual, new_p], ignore_index=True
        )

      if komposisi_produk_input:
        st.session_state.komposisi_produk_jual[nm.strip()] = (
            komposisi_produk_input
        )

      save_data()
      st.success(f"Produk '{nm}' dan komposisinya berhasil disimpan!")
      st.rerun()

  st.markdown("---")
  st.subheader("📝 Edit atau Hapus Data Produk Jadi")
  if st.session_state.produk_jual.empty:
    st.info("Belum ada data produk.")
  else:
    edited_produk = st.data_editor(
        st.session_state.produk_jual, num_rows="dynamic", use_container_width=True
    )
    if st.button("💾 Simpan Perubahan Produk Jadi"):
      st.session_state.produk_jual = edited_produk
      save_data()
      st.success("Data produk berhasil diperbarui!")

# -------------------------------------------------------------------------
# TAB 5: PRODUKSI & MASTER RESEP BAKU
# -------------------------------------------------------------------------
with menu_tabs[4]:
  st.header("🍳 Master Resep Baku & Produksi Setengah Jadi")

  sub_tabs = st.tabs([
      "Proses Produksi",
      "Kelola Master Resep",
      "Stok & Riwayat Setengah Jadi",
  ])

  with sub_tabs[0]:
    st.subheader("⚡ Eksekusi Produksi dari Resep Baku")
    st.info(
        "Pilih resep baku yang sudah dibuat. Sistem akan otomatis menghitung dan"
        " memotong bahan mentah berdasarkan jumlah batch produksi."
    )

    if st.session_state.master_resep.empty:
      st.warning(
          "Belum ada Master Resep Baku. Buat terlebih dahulu di tab 'Kelola"
          " Master Resep'."
      )
    else:
      with st.form("form_eksekusi_resep"):
        list_resep_nama = st.session_state.master_resep["Nama Resep"].tolist()
        pilih_resep = st.selectbox("Pilih Resep Baku", list_resep_nama)

        multiplier = st.number_input(
            "Jumlah Batch Produksi (Kelipatan Resep)",
            min_value=1,
            value=1,
            step=1,
            format="%d",
        )

        submitted_eksekusi = st.form_submit_button(
            "🚀 Jalankan Produksi (Potong Bahan & Tambah Stok)"
        )

        if submitted_eksekusi:
          resep_row = st.session_state.master_resep.loc[
              st.session_state.master_resep["Nama Resep"] == pilih_resep
          ].iloc[0]
          hasil_per_resep = int(resep_row["Hasil Jadi"])
          satuan_hasil = resep_row["Satuan Hasil"]
          komposisi_str = resep_row["Komposisi Bahan"]

          try:
            komposisi_dict = json.loads(komposisi_str.replace("'", '"'))
          except Exception:
            komposisi_dict = {}

          stok_cukup = True
          bahan_terpakai_real = {}

          for bahan, qty_butuh_per_unit in komposisi_dict.items():
            total_butuh = int(qty_butuh_per_unit) * int(multiplier)
            cek_bahan = st.session_state.bahan_mentah.loc[
                st.session_state.bahan_mentah["Nama Bahan"] == bahan
            ]
            if cek_bahan.empty:
              stok_cukup = False
              st.error(
                  f"Bahan mentah '{bahan}' tidak ditemukan di inventori!"
              )
              break

            stok_sedia = int(cek_bahan["Stok"].values[0])
            satuan_bahan = cek_bahan["Satuan"].values[0]

            if stok_sedia < total_butuh:
              stok_cukup = False
              st.error(
                  f"Stok bahan '{bahan}' tidak cukup! Tersisa {stok_sedia}"
                  f" {satuan_bahan}, butuh {total_butuh} {satuan_bahan}."
              )
              break
            else:
              bahan_terpakai_real[bahan] = (
                  f"{total_butuh} {satuan_bahan}"
              )

          if stok_cukup:
            for bahan, detail_pakai in bahan_terpakai_real.items():
              jml_potong = int(detail_pakai.split()[0])
              current_b_stok = int(
                  st.session_state.bahan_mentah.loc[
                      st.session_state.bahan_mentah["Nama Bahan"] == bahan, "Stok"
                  ].values[0]
              )
              st.session_state.bahan_mentah.loc[
                  st.session_state.bahan_mentah["Nama Bahan"] == bahan, "Stok"
              ] = (
                  current_b_stok - jml_potong
              )

            total_hasil_jadi = hasil_per_resep * int(multiplier)
            existing_s_idx = st.session_state.stok_setengah_jadi.index[
                st.session_state.stok_setengah_jadi["Nama Barang Setengah Jadi"]
                .str.lower()
                == pilih_resep.strip().lower()
            ]

            if not existing_s_idx.empty:
              idx_s = existing_s_idx[0]
              current_sj_stok = int(
                  st.session_state.stok_setengah_jadi.loc[idx_s, "Stok"]
              )
              st.session_state.stok_setengah_jadi.loc[idx_s, "Stok"] = (
                  current_sj_stok + total_hasil_jadi
              )
            else:
              new_stok_sj = pd.DataFrame([{
                  "Nama Barang Setengah Jadi": pilih_resep.strip(),
                  "Stok": total_hasil_jadi,
                  "Satuan": satuan_hasil,
              }])
              st.session_state.stok_setengah_jadi = pd.concat(
                  [st.session_state.stok_setengah_jadi, new_stok_sj],
                  ignore_index=True,
              )

            waktu_prod = datetime.now(WIB).strftime("%Y-%m-%d %H:%M:%S")
            new_record = pd.DataFrame(
                [[
                    waktu_prod,
                    pilih_resep,
                    total_hasil_jadi,
                    satuan_hasil,
                    str(bahan_terpakai_real),
                ]],
                columns=[
                    "Waktu",
                    "Nama Resep / Barang",
                    "Jumlah Hasil",
                    "Satuan Hasil",
                    "Bahan Terpakai",
                ],
            )
            st.session_state.produksi_setengah_jadi = pd.concat(
                [st.session_state.produksi_setengah_jadi, new_record],
                ignore_index=True,
            )

            save_data()
            st.success(
                f"Produksi resep '{pilih_resep}' sukses! Bertambah"
                f" {total_hasil_jadi} {satuan_hasil} ke stok setengah jadi."
            )
            st.rerun()

  with sub_tabs[1]:
    st.subheader("📋 Buat & Kelola Master Resep Baku")
    st.info(
        "Tentukan komposisi bahan mentah tetap untuk satu standar resep."
    )

    with st.form("form_tambah_master_resep"):
      nm_resep = st.text_input("Nama Resep Baku")
      col_r1, col_r2 = st.columns(2)
      with col_r1:
        hasil_jadi_std = st.number_input(
            "Hasil Jadi Standar (Per 1 Resep)",
            min_value=1,
            value=1,
            step=1,
            format="%d",
        )
      with col_r2:
        satuan_hasil_std = st.selectbox(
            "Satuan Hasil Standar", ["pcs", "porsi", "kg", "liter", "bungkus"]
        )

      st.markdown("---")
      st.markdown("#### Takaran Bahan Mentah yang Dibutuhkan (Per 1 Resep):")

      komposisi_input = {}
      if not st.session_state.bahan_mentah.empty:
        for idx, row in st.session_state.bahan_mentah.iterrows():
          qty_pakai = st.number_input(
              f"Takaran {row['Nama Bahan']} ({row['Satuan']})",
              min_value=0,
              value=0,
              step=1,
              format="%d",
              key=f"master_bahan_{idx}",
          )
          if qty_pakai > 0:
            komposisi_input[row["Nama Bahan"]] = qty_pakai
      else:
        st.warning("Belum ada data bahan mentah di inventori.")

      submitted_master = st.form_submit_button("💾 Simpan Master Resep Baku")

      if submitted_master:
        if not nm_resep:
          st.error("Nama resep tidak boleh kosong!")
        elif not komposisi_input:
          st.error("Pilih minimal 1 bahan mentah untuk resep ini!")
        else:
          new_master = pd.DataFrame(
              [{
                  "Nama Resep": nm_resep.strip(),
                  "Hasil Jadi": int(hasil_jadi_std),
                  "Satuan Hasil": satuan_hasil_std,
                  "Komposisi Bahan": str(komposisi_input),
              }]
          )

          existing_m = st.session_state.master_resep.index[
              st.session_state.master_resep["Nama Resep"].str.lower()
              == nm_resep.strip().lower()
          ]
          if not existing_m.empty:
            st.session_state.master_resep.loc[existing_m[0]] = new_master.loc[0]
          else:
            st.session_state.master_resep = pd.concat(
                [st.session_state.master_resep, new_master], ignore_index=True
            )

          save_data()
          st.success(
              f"Master resep baku '{nm_resep}' berhasil disimpan!"
          )
          st.rerun()

    st.markdown("---")
    st.subheader("📝 Edit Takaran Resep yang Sudah Ada")
    if st.session_state.master_resep.empty:
      st.info("Belum ada master resep baku.")
    else:
      pilih_edit_resep = st.selectbox(
          "Pilih Resep yang Ingin Diedit Takarannya",
          st.session_state.master_resep["Nama Resep"].tolist(),
      )

      resep_idx_match = st.session_state.master_resep.index[
          st.session_state.master_resep["Nama Resep"] == pilih_edit_resep
      ][0]
      current_komp_str = st.session_state.master_resep.loc[
          resep_idx_match, "Komposisi Bahan"
      ]

      try:
        current_komp_dict = json.loads(current_komp_str.replace("'", '"'))
      except Exception:
        current_komp_dict = {}

      df_edit_komp = pd.DataFrame([
          {"Nama Bahan": k, "Takaran": v} for k, v in current_komp_dict.items()
      ])

      st.write(f"Tabel Takaran Bahan untuk Resep: **{pilih_edit_resep}**")
      edited_komp_df = st.data_editor(
          df_edit_komp, num_rows="dynamic", use_container_width=True
      )

      if st.button("💾 Simpan Perubahan Takaran Resep Ini"):
        new_komp_dict = {}
        for _, r in edited_komp_df.iterrows():
          b_name = str(r["Nama Bahan"]).strip()
          b_val = int(r["Takaran"])
          if b_name and b_val > 0:
            new_komp_dict[b_name] = b_val

        st.session_state.master_resep.loc[resep_idx_match, "Komposisi Bahan"] = (
            str(new_komp_dict)
        )
        save_data()
        st.success(
            f"Takaran bahan untuk resep '{pilih_edit_resep}' berhasil"
            " diperbarui!"
        )
        st.rerun()

      st.markdown("---")
      st.subheader("📝 Kelola Seluruh Data Master Resep")
      edited_master = st.data_editor(
          st.session_state.master_resep,
          num_rows="dynamic",
          use_container_width=True,
      )
      if st.button("💾 Simpan Perubahan Master Resep Utama"):
        st.session_state.master_resep = edited_master
        save_data()
        st.success("Master resep berhasil diperbarui!")

  with sub_tabs[2]:
    st.subheader("➕ Input Manual Stok Setengah Jadi (Ready Stock)")
    st.info(
        "Gunakan form ini untuk langsung mencatat barang setengah jadi yang"
        " sudah siap di stok."
    )

    with st.form("form_manual_stok_sj"):
      c_m1, c_m2, c_m3 = st.columns([2, 1, 1])
      with c_m1:
        nama_sj_manual = st.text_input("Nama Barang Setengah Jadi")
      with c_m2:
        jumlah_sj_manual = st.number_input(
            "Jumlah Stok", min_value=0, value=0, step=1, format="%d"
        )
      with c_m3:
        satuan_sj_manual = st.selectbox(
            "Satuan Stok", ["pcs", "porsi", "kg", "liter", "bungkus"]
        )

      if st.form_submit_button("➕ Tambah Stok Setengah Jadi Manual") and nama_sj_manual:
        existing_sj = st.session_state.stok_setengah_jadi.index[
            st.session_state.stok_setengah_jadi["Nama Barang Setengah Jadi"]
            .str.lower()
            == nama_sj_manual.strip().lower()
        ]
        if not existing_sj.empty:
          idx_sj = existing_sj[0]
          curr_stk = int(st.session_state.stok_setengah_jadi.loc[idx_sj, "Stok"])
          st.session_state.stok_setengah_jadi.loc[idx_sj, "Stok"] = (
              curr_stk + jumlah_sj_manual
          )
        else:
          new_sj_row = pd.DataFrame([{
              "Nama Barang Setengah Jadi": nama_sj_manual.strip(),
              "Stok": jumlah_sj_manual,
              "Satuan": satuan_sj_manual,
          }])
          st.session_state.stok_setengah_jadi = pd.concat(
              [st.session_state.stok_setengah_jadi, new_sj_row],
              ignore_index=True,
          )

        save_data()
        st.success(
            f"Stok setengah jadi '{nama_sj_manual}' berhasil ditambahkan!"
        )
        st.rerun()

    st.markdown("---")
    st.subheader("📦 Stok Barang Setengah Jadi Saat Ini")
    if st.session_state.stok_setengah_jadi.empty:
      st.info("Belum ada stok barang setengah jadi.")
    else:
      edited_stok_sj = st.data_editor(
          st.session_state.stok_setengah_jadi,
          num_rows="dynamic",
          use_container_width=True,
      )
      if st.button("💾 Simpan Perubahan Stok Setengah Jadi"):
        st.session_state.stok_setengah_jadi = edited_stok_sj
        save_data()
        st.success("Stok barang setengah jadi berhasil diperbarui!")

    st.markdown("---")
    st.subheader("📝 Riwayat Eksekusi Produksi")
    if st.session_state.produksi_setengah_jadi.empty:
      st.info("Belum ada riwayat produksi.")
    else:
      edited_prod = st.data_editor(
          st.session_state.produksi_setengah_jadi,
          num_rows="dynamic",
          use_container_width=True,
      )
      if st.button("💾 Simpan Perubahan Riwayat Produksi"):
        st.session_state.produksi_setengah_jadi = edited_prod
        save_data()
        st.success("Riwayat produksi berhasil diperbarui!")

# -------------------------------------------------------------------------
# TAB 6: INVENTORI BAHAN MENTAH
# -------------------------------------------------------------------------
with menu_tabs[5]:
  st.header("📦 Inventori Bahan Mentah & Penyesuaian Stok")

  with st.expander("➕ Tambah Bahan Mentah Baru Manual"):
    with st.form("form_tambah_bahan"):
      nm_b = st.text_input("Nama Bahan Mentah")
      stk_b = st.number_input(
          "Jumlah Stok Awal", min_value=0, value=0, step=1, format="%d"
      )
      sat_b = st.selectbox("Satuan", ["gram", "ml", "pcs", "kg", "liter"])
      if st.form_submit_button("Simpan Bahan Baru") and nm_b:
        new_bm = pd.DataFrame(
            [[nm_b.strip(), int(stk_b), sat_b]],
            columns=["Nama Bahan", "Stok", "Satuan"],
        )
        st.session_state.bahan_mentah = pd.concat(
            [st.session_state.bahan_mentah, new_bm], ignore_index=True
        )
        save_data()
        st.success(f"Bahan mentah '{nm_b}' berhasil ditambahkan!")

  with st.expander(
      "📥 Upload Data Bahan Mentah via Excel / CSV (Gabung Otomatis)"
  ):
    st.info(
        "File Excel/CSV yang di-upload akan otomatis digabungkan dengan data"
        " bahan mentah yang sudah ada sebelumnya."
    )
    uploaded_file = st.file_uploader(
        "Pilih file (.xlsx / .csv)", type=["xlsx", "csv"], key="upload_bulk_bahan"
    )
    if uploaded_file:
      try:
        df_u = (
            pd.read_csv(uploaded_file)
            if uploaded_file.name.endswith(".csv")
            else pd.read_excel(uploaded_file)
        )

        kolom_wajib = ["Nama Bahan", "Stok", "Satuan"]
        if all(col in df_u.columns for col in kolom_wajib):
          df_u["Stok"] = df_u["Stok"].astype(float).astype(int)
          st.session_state.bahan_mentah = pd.concat(
              [st.session_state.bahan_mentah, df_u[kolom_wajib]],
              ignore_index=True,
          )
          st.session_state.bahan_mentah = (
              st.session_state.bahan_mentah.drop_duplicates(
                  subset=["Nama Bahan"], keep="last"
              ).reset_index(drop=True)
          )

          save_data()
          st.success("Data bahan mentah berhasil di-upload dan digabungkan!")
          st.rerun()
        else:
          st.error(
              "Format kolom file Anda tidak sesuai! Pastikan file memiliki kolom:"
              " Nama Bahan, Stok, dan Satuan."
          )
      except Exception as e:
        st.error(f"Error membaca file: {e}")

  st.markdown("---")
  st.subheader("📝 Edit & Hapus Stok Bahan Mentah")

  if st.session_state.bahan_mentah.empty:
    st.info("Belum ada data bahan mentah.")
  else:
    edited_df = st.data_editor(
        st.session_state.bahan_mentah, num_rows="dynamic", use_container_width=True
    )
    if st.button("💾 Simpan Perubahan Stok Bahan"):
      st.session_state.bahan_mentah = edited_df
      save_data()
      st.success("Stok bahan mentah berhasil diperbarui!")