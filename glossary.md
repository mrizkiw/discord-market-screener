# 📚 KAMUS TRADING BOT SCREENER 📚
*Panduan untuk membaca dan memahami sinyal dari Bot Market Screener.*

### 📊 1. VOLUME PROFILE (Analisis Area Volume)
Volume Profile menunjukkan **di harga berapa** transaksi paling banyak terjadi (bukan kapan).

*   **`POC` (Point of Control):** Level harga dengan volume transaksi paling besar. Ini adalah "magnet harga". Sering bertindak sebagai Support atau Resistance yang **sangat kuat**.
*   **`VAH` (Value Area High):** Batas *atas* dari area di mana 70% total transaksi terjadi. Jika harga tembus ke atas VAH, tren sangat Bullish (naik). Jika harga mantul ke bawah dari VAH, ini adalah area Resistance (jual).
*   **`VAL` (Value Area Low):** Batas *bawah* dari area di mana 70% total transaksi terjadi. Sering digunakan sebagai level Support yang kuat (area pantulan untuk beli).
*   **`Value Area` (VA):** Rentang harga di antara VAL dan VAH. Pasar menganggap harga di dalam area ini adalah harga yang "wajar".

### 📈 2. MARKET STRUCTURE (Struktur Harga)
Membaca ke mana arah tren utama sedang bergerak berdasarkan pergerakan harga mentah (Price Action).

*   **`Swing High` (SH):** Titik puncak harga tertinggi sementara sebelum harga kembali turun. (Puncak bukit).
*   **`Swing Low` (SL):** Titik lembah harga terendah sementara sebelum harga kembali naik. (Dasar jurang).
*   **`BOS` (Break of Structure):** Konfirmasi tren berlanjut. Terjadi jika harga berhasil menembus *Swing High* sebelumnya (saat tren naik).
*   **`CHoCH` (Change of Character):** Peringatan dini perubahan tren! Terjadi jika harga yang awalnya turun tiba-tiba berbalik arah menembus *Swing High* terakhir (atau sebaliknya).
*   **`Breakout`:** Harga berhasil menjebol level penting (Resistance/Support) dengan kuat, biasanya diikuti volume besar. Tanda dimulainya pergerakan besar.

### 🎯 3. TRADING ZONES & SIGNALS (Sinyal & Level)

*   **`Entry Zone`:** Area rentang harga paling optimal untuk membeli (Buy/Long). Bot mencari area ini berdasarkan pertemuan banyak indikator kuat.
*   **`TP` (Take Profit):** Target harga atas untuk menjual aset dan mengamankan keuntungan.
*   **`SL` (Stop Loss):** Sabuk pengaman! Batas harga bawah untuk memotong kerugian (Cut Loss) jika market tiba-tiba berbalik arah. **Wajib dipasang!**
*   **`RR` (Risk/Reward):** Rasio perbandingan antara risiko (SL) vs potensi profit (TP). *RR 1:2* artinya Anda merisikokan 1% modal untuk mengejar untung 2%.
*   **`MTF Confluence` (Multi-Timeframe):** Keadaan super valid di mana beberapa timeframe sekaligus (misal 1 Jam, 4 Jam, 1 Hari) menunjukkan sinyal searah/kompak. Jika bot bilang ada MTF Confluence, probabilitas menangnya sangat tinggi!
