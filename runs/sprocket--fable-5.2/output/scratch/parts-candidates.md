# Candidate parts (key: manufacturer, MPN, role)

## Group A: ICs, connectors, electromechanical

- usbc: GCT, USB4105-GF-A, USB-C 2.0 receptacle 16-pin
- usblc6: STMicroelectronics, USBLC6-2SC6, USB ESD protection SOT-23-6
- bq24074: Texas Instruments, BQ24074RGTR, LiPo charger with power path VQFN-16
- ldo: Texas Instruments, TLV75733PDBVR, 3.3 V 1 A LDO SOT-23-5
- rp2350: Raspberry Pi, RP2350A (QFN-60; find the exact orderable codes, e.g. SC1512 / RP2350A0A4 and the current stepping A4), MCU
- flash: Winbond, W25Q128JVPIQ, 128 Mbit QSPI flash WSON-8 6x5 mm
- psram: AP Memory, APS6404L-3SQR-SN, 64 Mbit QSPI PSRAM SOIC-8
- rm2: Raspberry Pi, RMC20452T (SC1169), Wi-Fi/BLE module. Already verified: DigiKey 2648-SC1169CT-ND, Mouser 358-SC1169. Only look up LCSC.
- usd: Hirose, DM3AT-SF-PEJM5, microSD push-push socket
- sw: C&K, PTS810 SJM 250 SMTR LFS, tactile switch (KiCad footprint SW_SPST_PTS810)
- jst_ph: JST, S2B-PH-SM4-TB, 2-pin PH side-entry SMD
- jst_sh4: JST, SM04B-SRSS-TB, 4-pin SH side-entry SMD
- jst_sh3: JST, SM03B-SRSS-TB, 3-pin SH side-entry SMD
- hdr: any major brand, 1x12 2.54 mm vertical through-hole pin header, 6 mm pins (e.g. Wurth 61301211121 or Sullins PRPC012SAAN-RC)
- rgb: Worldsemi, WS2812B-2020, addressable RGB LED 2.0x2.0 mm (KiCad footprint LED_WS2812B-2020_PLCC4_2.0x2.0mm)

## Group B: passives, LEDs, crystal, inductor

- xtal: Abracon, ABM8-272-T3, 12 MHz crystal 3.2x2.5 mm (Raspberry Pi reference part)
- ind: Abracon, AOTA-B201610S3R3-101-T, 3.3 uH polarised inductor 2016 (Raspberry Pi reference part)
- led_g: Wurth, 150060GS75000, green 0603 LED (or a better-stocked equivalent)
- led_a: Wurth, 150060AS75000, amber 0603 LED (or equivalent)
- r5k1: Yageo, RC0402FR-075K1L
- r27: Yageo, RC0402FR-0727RL
- r33: Yageo, RC0402FR-0733RL
- r470: Yageo, RC0402FR-07470RL
- r1k: Yageo, RC0402FR-071KL
- r1k5: Yageo, RC0402FR-071K5L
- r1k8: Yageo, RC0402FR-071K8L
- r2k2: Yageo, RC0402FR-072K2L
- r10k: Yageo, RC0402FR-0710KL
- r100k: Yageo, RC0402FR-07100KL
- c15p: Murata, GRM1555C1H150JA01D, 15 pF C0G 50 V 0402
- c100n: Murata, GRM155R71C104KA88D, 100 nF X7R 16 V 0402
- c1u: Murata, GRM155R61A105KE15D, 1 uF X5R 10 V 0402
- c4u7: Murata, GRM155R60J475ME47D, 4.7 uF X5R 6.3 V 0402
- c10u25: Murata, GRM188R61E106MA73D, 10 uF X5R 25 V 0603
