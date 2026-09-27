from datetime import datetime
import json
import os
from fpdf import FPDF
import pandas as pd
import streamlit as st

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

# Konfigurasi Halaman
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

# --- SISTEM PENYIMPANAN PERMANEN (LOCAL JSON DATABASE) ---
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
      "tipe_pesanan_list": st.session_state.tipe_pesanan_list,
      "transaksi": st.session_state.transaksi,
  }
  with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


# Load data dari file JSON
saved_db = load_data()

# Inisialisasi Session State
if "initialized" not in st.session_state:
  if saved_db:
    st.session_state.bahan_mentah = pd.DataFrame(
        saved_db.get("bahan_mentah", [])
    )
    st.session_state.stok_setengah_jadi = pd.DataFrame(
        saved_db.get("stok_setengah_jadi", [])
    )
    st.session_state.master_resep = pd.DataFrame(
        saved_db.get("master_resep", [])
    )
    st.session_state.produksi_setengah_jadi = pd.DataFrame(
        saved_db.get("produksi_setengah_jadi", [])
    )
    st.session_state.produk_jual = pd.DataFrame(saved_db.get("produk_jual", []))
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
    order_fee,
    pajak,
    total_bayar,
    waktu,
    no_nota,
    nama_kasir,
    tipe_pesanan,
    no_urutan,
):
  pdf = FPDF(orientation="P", unit="mm", format=(80, 200))
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
  pdf.cell(0, 4, "[ NON PAID ORDER ]", 0, 1, "C")

  pdf.ln(2)
  draw_dashed_line(pdf, x1, x2, pdf.get_y())
  pdf.ln(2)

  pdf.set_font("Courier", "", 7)
  pdf.cell(0, 4, f"WAKTU PESANAN : {waktu}", 0, 1, "L")
  pdf.cell(0, 4, f"NO NOTA       : #{no_nota}", 0, 1, "L")
  pdf.cell(0, 4, f"CABANG        : Cabang Pusat", 0, 1, "L")
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
        f"  {item['qty']}x      Rp {item['subtotal']:,.0f}".replace(",", "."),
        0,
        1,
        "L",
    )
    pdf.cell(
        0,
        4,
        f"  (@Rp {item['harga']:,.0f})".replace(",", "."),
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
        f"Rp {val:,.0f}".replace(",", ".") if isinstance(val, (int, float)) else val,
        0,
        1,
        "R",
    )

  print_row("SUB TOTAL", subtotal)
  pdf.cell(0, 4, f"{total_qty_produk} PRODUK", 0, 1, "L")
  print_row("DISKON (-)", diskon)
  print_row("ORDER FEE (+)", order_fee)
  print_row("PAJAK (+)", pajak)
  print_row("PEMBULATAN", 0)

  pdf.ln(2)
  draw_dashed_line(pdf, x1, x2, pdf.get_y())
  pdf.ln(2)

  pdf.set_font("Courier", "B", 9)
  print_row("TOTAL BAYAR", total_bayar)

  pdf.ln(3)
  pdf.set_font("Courier", "", 7)
  pdf.cell(0, 3, "***", 0, 1, "C")
  pdf.cell(0, 3, "Terima kasih.", 0, 1, "C")
  pdf.cell(0, 3, "STRUK UNTUK KONSUMEN", 0, 1, "C")
  pdf.cell(0, 3, "BUKAN STRUK PEMBAYARAN", 0, 1, "C")
  pdf.cell(0, 3, "***", 0, 1, "C")

  filename = f"struk_{no_nota}.pdf"
  pdf.output(filename)
  return filename


# Navigasi Utama
st.markdown("### 🏷️ TRIPTI - POS Kasir & Produksi")
menu = st.selectbox(
    "Pilih Menu Utama",
    [
        "1. POS Kasir Utama",
        "2. Riwayat & Story Pemesanan",
        "3. Pengaturan Tipe Pesanan (Custom)",
        "4. Kelola Menu & Stok Produk Jadi (Edit)",
        "5. Tab Produksi & Resep Baku (Edit)",
        "6. Inventori Bahan Mentah (Edit)",
    ],
)
st.markdown("---")

# -------------------------------------------------------------------------
# 1. POS KASIR UTAMA
# -------------------------------------------------------------------------
if menu == "1. POS Kasir Utama":
  col_main, col_cart = st.columns([2, 1])

  with col_main:
    c_srch1, c_srch2, c_srch3 = st.columns([2, 1, 1])
    with c_srch1:
      cari_konsumen = st.text_input(
          "Cari Konsumen...", placeholder="Nama Konsumen..."
      )
    with c_srch2:
      nama_kasir = st.text_input("Kasir", value="Saeful I")
    with c_srch3:
      pilih_tipe_pesanan = st.selectbox(
          "Tipe Pesanan", st.session_state.tipe_pesanan_list
      )

    st.markdown("#### Daftar Produk Siap Jual (Ketik Qty Langsung)")
    if st.session_state.produk_jual.empty:
      st.info(
          "Belum ada produk. Tambahkan di menu 'Kelola Menu & Stok Produk Jadi'."
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
                            <h2 style="color:white; margin:5px 0;">Rp {row['Harga Jual']:,}</h2>
                        </div>
                        """,
                unsafe_allow_html=True,
            )
            q_input = st.number_input(
                f"Jumlah Beli ({row['Nama Produk']})",
                min_value=0,
                value=0,
                step=1,
                key=f"input_qty_{idx}",
            )

            if q_input > row["Stok Produk"]:
              st.error(
                  f"Stok '{row['Nama Produk']}' tidak cukup! Tersedia:"
                  f" {row['Stok Produk']}"
              )
              ada_error_stok = True
            elif q_input > 0:
              pesanan_input.append({
                  "index": idx,
                  "nama": row["Nama Produk"],
                  "harga": row["Harga Jual"],
                  "qty": q_input,
                  "subtotal": row["Harga Jual"] * q_input,
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
          st.caption(f"Rp {data['harga']:,} x {data['qty']}")
        with c_k2:
          if st.button("➕", key=f"plus_{p_name}"):
            idx_p = data["index"]
            stok_s = st.session_state.produk_jual.loc[idx_p, "Stok Produk"]
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
      diskon = st.number_input("Diskon (Rp)", min_value=0, value=0, step=500)
      order_fee = st.number_input(
          "Order Fee / Ongkir (+)", min_value=0, value=0, step=500
      )
      pajak = st.number_input("Pajak (+)", min_value=0, value=0, step=500)

      total_bayar = (subtotal_cart - diskon) + order_fee + pajak

      st.markdown(
          f"### **Total Bayar: Rp {total_bayar:,}**", unsafe_allow_html=True
      )

      if st.button("💳 PROSES PEMBAYARAN & CETAK STRUK", key="btn_bayar"):
        stok_cukup = True
        for item in item_list:
          idx_p = item["index"]
          stok_sekarang = st.session_state.produk_jual.loc[
              idx_p, "Stok Produk"
          ]
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
            st.session_state.produk_jual.loc[idx_p, "Stok Produk"] -= item[
                "qty"
            ]

          waktu_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
          no_nota = f"PW{datetime.now().strftime('%d%H%M')}"

          pdf_file = generate_tripti_receipt(
              item_list,
              subtotal_cart,
              diskon,
              order_fee,
              pajak,
              total_bayar,
              waktu_str,
              no_nota,
              nama_kasir,
              pilih_tipe_pesanan,
              1,
          )

          st.session_state.transaksi.append({
              "Waktu": waktu_str,
              "No Nota": no_nota,
              "Kasir": nama_kasir,
              "Konsumen": cari_konsumen if cari_konsumen else "Umum",
              "Tipe Pesanan": pilih_tipe_pesanan,
              "Total Bayar": total_bayar,
              "File Struk": pdf_file,
              "Rincian Item": item_list,
          })

          save_data()

          st.session_state.last_receipt = pdf_file
          st.session_state.cart = {}
          st.success("Transaksi Sukses! Stok produk jadi telah terpotong.")
          st.rerun()

    if st.session_state.last_receipt and os.path.exists(
        st.session_state.last_receipt
    ):
      st.markdown("---")
      with open(st.session_state.last_receipt, "rb") as f:
        st.download_button(
            label="📥 Unduh Struk PDF Terakhir",
            data=f,
            file_name=st.session_state.last_receipt,
            mime="application/pdf",
        )

# -------------------------------------------------------------------------
# 2. RIWAYAT & STORY PEMESANAN
# -------------------------------------------------------------------------
elif menu == "2. Riwayat & Story Pemesanan":
  st.header("📜 Riwayat & Story Pemesanan (Log Transaksi)")
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
          f"Nota: #{trx['No Nota']} | {trx['Waktu']} | Rp"
          f" {trx['Total Bayar']:,} ({trx.get('Tipe Pesanan', 'Dine In')})"
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
              f" {itm['harga']:,} = Rp {itm['subtotal']:,}"
          )

        st.markdown(f"### **Total: Rp {trx['Total Bayar']:,}**")

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
                st.session_state.produk_jual.loc[match_idx[0], "Stok Produk"] += (
                    q_bought
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
# 3. PENGATURAN TIPE PESANAN
# -------------------------------------------------------------------------
elif menu == "3. Pengaturan Tipe Pesanan (Custom)":
  st.header("⚙️ Pengaturan Tipe Pesanan (Custom)")

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
# 4. KELOLA MENU & STOK PRODUK JADI (DENGAN POTONG STOK SETENGAH JADI)
# -------------------------------------------------------------------------
elif menu == "4. Kelola Menu & Stok Produk Jadi (Edit)":
  st.header("🍽️ Kelola Menu Produk & Stok Jadi")

  with st.form("form_menu"):
    nm = st.text_input("Nama Produk Siap Jual (Cth: Siomay Ikan Tenggiri)")
    hrg = st.number_input("Harga Jual (Rp)", min_value=0, step=500)
    stk_prod = st.number_input(
        "Jumlah Stok Produk Jadi yang Ditambahkan", min_value=0, value=0, step=1
    )
    sku = st.text_input("Kode SKU (Cth: SIT-9872PJ)")

    st.markdown("---")
    st.markdown(
        "*(Opsional)* Pilih Barang Setengah Jadi yang Dipotong untuk Stok Ini:"
    )

    pilih_setengah_jadi = "Tidak Ada"
    jml_potong_sj = 0.0
    if not st.session_state.stok_setengah_jadi.empty:
      list_opsi_sj = ["Tidak Ada"] + st.session_state.stok_setengah_jadi[
          "Nama Barang Setengah Jadi"
      ].tolist()
      pilih_setengah_jadi = st.selectbox(
          "Barang Setengah Jadi Terpakai", list_opsi_sj
      )
      if pilih_setengah_jadi != "Tidak Ada":
        jml_potong_sj = st.number_input(
            "Jumlah Setengah Jadi yang Dipotong",
            min_value=0.0,
            value=0.0,
            step=1.0,
        )
    else:
      st.info(
          "Belum ada stok barang setengah jadi. Buat dulu di 'Tab Produksi &"
          " Resep Baku'."
      )

    if st.form_submit_button("Simpan Produk & Potong Stok Setengah Jadi") and nm:
      bisa_simpan = True
      if pilih_setengah_jadi != "Tidak Ada" and jml_potong_sj > 0:
        stok_sj_row = st.session_state.stok_setengah_jadi.loc[
            st.session_state.stok_setengah_jadi["Nama Barang Setengah Jadi"]
            == pilih_setengah_jadi
        ]
        if not stok_sj_row.empty:
          stok_sj_tersedia = float(stok_sj_row["Stok"].values[0])
          if stok_sj_tersedia < jml_potong_sj:
            bisa_simpan = False
            st.error(
                f"Stok barang setengah jadi '{pilih_setengah_jadi}' tidak cukup!"
                f" Tersisa {stok_sj_tersedia}, anda butuh {jml_potong_sj}."
            )

      if bisa_simpan:
        if pilih_setengah_jadi != "Tidak Ada" and jml_potong_sj > 0:
          idx_sj = st.session_state.stok_setengah_jadi.index[
              st.session_state.stok_setengah_jadi["Nama Barang Setengah Jadi"]
              == pilih_setengah_jadi
          ][0]
          st.session_state.stok_setengah_jadi.loc[idx_sj, "Stok"] -= (
              jml_potong_sj
          )

        existing_idx = st.session_state.produk_jual.index[
            st.session_state.produk_jual["Nama Produk"].str.lower()
            == nm.strip().lower()
        ]

        if not existing_idx.empty:
          idx_e = existing_idx[0]
          st.session_state.produk_jual.loc[idx_e, "Stok Produk"] += stk_prod
          st.session_state.produk_jual.loc[idx_e, "Harga Jual"] = hrg
          save_data()
          st.success(
              f"Produk '{nm}' diperbarui. Stok bertambah {stk_prod} (Total"
              f" stok: {st.session_state.produk_jual.loc[idx_e, 'Stok Produk']})."
          )
        else:
          new_p = pd.DataFrame(
              [{
                  "Nama Produk": nm.strip(),
                  "Harga Jual": hrg,
                  "Stok Produk": stk_prod,
                  "SKU": sku,
              }]
          )
          st.session_state.produk_jual = pd.concat(
              [st.session_state.produk_jual, new_p], ignore_index=True
          )
          save_data()
          st.success(f"Produk baru '{nm}' berhasil ditambahkan!")
        st.rerun()

  st.markdown("---")
  st.subheader("📝 Edit atau Hapus Data Produk Jadi")
  if st.session_state.produk_jual.empty:
    st.info("Belum ada data produk.")
  else:
    edited_produk = st.data_editor(
        st.session_state.produk_jual, num_rows="dynamic", use_container_width=True
    )
    if st.button("💾 Simpan Perubahan Produk"):
      st.session_state.produk_jual = edited_produk
      save_data()
      st.success("Data produk berhasil diperbarui!")

# -------------------------------------------------------------------------
# 5. TAB PRODUKSI & MASTER RESEP BAKU
# -------------------------------------------------------------------------
elif menu == "5. Tab Produksi & Resep Baku (Edit)":
  st.header("🍳 Master Resep Baku & Produksi Setengah Jadi")

  tab_prod1, tab_prod2, tab_prod3 = st.tabs([
      "1. Proses Produksi (Eksekusi Resep)",
      "2. Kelola Master Resep Baku",
      "3. Stok & Riwayat Setengah Jadi",
  ])

  # --- TAB 1: EKSEKUSI PRODUKSI BERDASARKAN MASTER RESEP ---
  with tab_prod1:
    st.subheader("⚡ Eksekusi Produksi dari Resep Baku")
    st.info(
        "Pilih resep baku yang sudah dibuat. Sistem akan otomatis menghitung dan"
        " memotong bahan mentah berdasarkan jumlah batch produksi."
    )

    if st.session_state.master_resep.empty:
      st.warning(
          "Belum ada Master Resep Baku. Buat terlebih dahulu di tab 'Kelola"
          " Master Resep Baku'."
      )
    else:
      with st.form("form_eksekusi_resep"):
        list_resep_nama = st.session_state.master_resep["Nama Resep"].tolist()
        pilih_resep = st.selectbox("Pilih Resep Baku", list_resep_nama)

        multiplier = st.number_input(
            "Jumlah Batch Produksi (Kelipatan Resep)",
            min_value=1.0,
            value=1.0,
            step=1.0,
        )

        submitted_eksekusi = st.form_submit_button(
            "🚀 Jalankan Produksi (Potong Bahan & Tambah Stok)"
        )

        if submitted_eksekusi:
          # Ambil data resep terpilih
          resep_row = st.session_state.master_resep.loc[
              st.session_state.master_resep["Nama Resep"] == pilih_resep
          ].iloc[0]
          hasil_per_resep = float(resep_row["Hasil Jadi"])
          satuan_hasil = resep_row["Satuan Hasil"]
          komposisi_str = resep_row["Komposisi Bahan"]

          # Parse komposisi bahan dari string dictionary
          try:
            komposisi_dict = json.loads(komposisi_str.replace("'", '"'))
          except Exception:
            komposisi_dict = {}

          # Validasi ketersediaan stok bahan mentah
          stok_cukup = True
          bahan_terpakai_real = {}

          for bahan, qty_butuh_per_unit in komposisi_dict.items():
            total_butuh = float(qty_butuh_per_unit) * multiplier
            # Cek apakah bahan ada di inventori
            cek_bahan = st.session_state.bahan_mentah.loc[
                st.session_state.bahan_mentah["Nama Bahan"] == bahan
            ]
            if cek_bahan.empty:
              stok_cukup = False
              st.error(
                  f"Bahan mentah '{bahan}' tidak ditemukan di inventori!"
              )
              break

            stok_sedia = float(cek_bahan["Stok"].values[0])
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
            # 1. Potong stok bahan mentah
            for bahan, detail_pakai in bahan_terpakai_real.items():
              jml_potong = float(detail_pakai.split()[0])
              st.session_state.bahan_mentah.loc[
                  st.session_state.bahan_mentah["Nama Bahan"] == bahan, "Stok"
              ] -= jml_potong

            # 2. Tambah stok setengah jadi
            total_hasil_jadi = hasil_per_resep * multiplier
            existing_s_idx = st.session_state.stok_setengah_jadi.index[
                st.session_state.stok_setengah_jadi["Nama Barang Setengah Jadi"]
                .str.lower()
                == pilih_resep.strip().lower()
            ]

            if not existing_s_idx.empty:
              idx_s = existing_s_idx[0]
              st.session_state.stok_setengah_jadi.loc[idx_s, "Stok"] += (
                  total_hasil_jadi
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

            # 3. Catat riwayat produksi
            waktu_prod = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
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

  # --- TAB 2: KELOLA MASTER RESEP BAKU ---
  with tab_prod2:
    st.subheader("📋 Buat & Kelola Master Resep Baku")
    st.info(
        "Tentukan komposisi bahan mentah tetap untuk satu standar resep."
    )

    with st.form("form_tambah_master_resep"):
      nm_resep = st.text_input(
          "Nama Resep Baku (Cth: Adonan Siomay Standar)"
      )
      col_r1, col_r2 = st.columns(2)
      with col_r1:
        hasil_jadi_std = st.number_input(
            "Hasil Jadi Standar (Per 1 Resep)", min_value=1.0, value=80.0
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
              min_value=0.0,
              value=0.0,
              step=1.0,
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
                  "Hasil Jadi": hasil_jadi_std,
                  "Satuan Hasil": satuan_hasil_std,
                  "Komposisi Bahan": str(komposisi_input),
              }]
          )

          # Cek jika resep sudah ada, update; jika belum, tambahkan
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
    st.subheader("📝 Daftar Master Resep Tersimpan")
    if st.session_state.master_resep.empty:
      st.info("Belum ada master resep baku.")
    else:
      edited_master = st.data_editor(
          st.session_state.master_resep,
          num_rows="dynamic",
          use_container_width=True,
      )
      if st.button("💾 Simpan Perubahan Master Resep"):
        st.session_state.master_resep = edited_master
        save_data()
        st.success("Master resep berhasil diperbarui!")

  # --- TAB 3: STOK & RIWAYAT SETENGAH JADI ---
  with tab_prod3:
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
# 6. INVENTORI BAHAN MENTAH
# -------------------------------------------------------------------------
elif menu == "6. Inventori Bahan Mentah (Edit)":
  st.header("📦 Inventori Bahan Mentah & Penyesuaian Stok")

  with st.expander("➕ Tambah Bahan Mentah Baru Manual"):
    with st.form("form_tambah_bahan"):
      nm_b = st.text_input("Nama Bahan Mentah (Cth: Ikan Tenggiri Giling)")
      stk_b = st.number_input("Jumlah Stok Awal", min_value=0.0, step=1.0)
      sat_b = st.selectbox("Satuan", ["gram", "ml", "pcs", "kg", "liter"])
      if st.form_submit_button("Simpan Bahan Baru") and nm_b:
        new_bm = pd.DataFrame(
            [[nm_b, stk_b, sat_b]], columns=["Nama Bahan", "Stok", "Satuan"]
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