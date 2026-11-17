from pathlib import Path
import sys
from cad import kicad_pcb
from cad.kicad import route

ROOT = Path(__file__).resolve().parents[1]
GROUPS = {
    'memory': ['QSPI_CLK_SRC', 'QSPI_CLK', 'QSPI_IO0', 'QSPI_IO1', 'QSPI_IO2', 'QSPI_IO3', 'FLASH_CS', 'PSRAM_CS'],
    'analog': ['MAIN_FB', 'MAIN_VAUX', 'CORE_FB', 'ADC_AVDD', 'BAT_SENSE', 'BAT_BUF', 'BAT_ADC', 'BAT_TS', 'CHG_ISET', 'CHG_ILIM', 'VBUS_ADC'],
    'power': ['+1V1', '+3V3', 'VSYS', 'VBAT', 'VBUS', 'VBUS_RAW', 'MAIN_PG', 'PWR_EN', 'PWR_SWITCH'],
    'interfaces': ['USB_CC1', 'USB_CC2', 'SD_CLK', 'SD_MOSI', 'SD_MISO', 'SD_CS', 'SD_DAT1', 'SD_DAT2', 'SD_DETECT', 'I2C_SDA', 'I2C_SCL', 'RGB_DATA', 'RGB_DIN'],
    'wireless': ['WIFI_TX', 'WIFI_RX', 'WIFI_CTS', 'WIFI_RTS', 'ESP_EN', 'ESP_BOOT', 'ESP_EN_CTRL', 'ESP_BOOT_CTRL', 'ESP_STRAP2', 'ESP_STRAP8', 'ESP_PROG_TX', 'ESP_PROG_RX'],
    'control': ['RUN', 'BOOT_SWITCH', 'SWCLK', 'SWDIO', 'CHARGE_N', 'POWERGOOD_N', 'USB_500_EN', 'USB_SUSPEND_EN', 'GPIO1', 'GPIO2', 'GPIO3', 'GPIO6', 'GPIO7', 'GPIO8', 'GPIO9', 'GPIO28_ADC2', 'GPIO29_ADC3'],
}

with kicad_pcb.edit(str(ROOT / 'Atlas2350.kicad_pcb')) as board:
    available = {net.name for net in board.get_nets()}
    group = sys.argv[1]
    entries = []
    for net in GROUPS[group]:
        if net not in available:
            continue
        width = 0.3 if net in {'+3V3', '+1V1', 'VSYS', 'VBAT', 'VBUS', 'VBUS_RAW'} else 0.15
        entries.append({'net': net, 'layers': ['F.Cu', 'B.Cu'], 'width': width})
    result = route(board, entries, layers=['F.Cu', 'B.Cu'], via_cost=2)
    print('\n'.join(result.human_lines()))
    board.refill_zones()
