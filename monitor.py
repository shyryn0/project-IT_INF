"""Мониторинг ресурсов компьютера. Лабораторная работа №4, вариант 8."""

import csv
import time
from datetime import datetime

import psutil

# Вариант 8
INTERVAL = 3
SAMPLES = 20
THRESHOLDS = {"cpu": 90, "ram": 80, "disk": 80}
LOG_FILE = "monitor_log.csv"


def get_cpu_frequency():
    """Возвращает текущую частоту CPU в МГц; None, если ОС её не сообщает."""
    frequency = psutil.cpu_freq()
    if frequency is None or frequency.current is None:
        return None
    return round(frequency.current, 1)


def take_sample():
    return {
        "time": datetime.now().strftime("%H:%M:%S"),
        "cpu": psutil.cpu_percent(interval=None),
        "ram": psutil.virtual_memory().percent,
        "disk": psutil.disk_usage("/").percent,
        "cpu_freq_mhz": get_cpu_frequency(),
    }


def check_alerts(sample):
    alerts = []
    for metric, limit in THRESHOLDS.items():
        if sample[metric] >= limit:
            alerts.append(
                f"{metric.upper()} = {sample[metric]}% (порог {limit}%)"
            )
    return alerts


def print_statistics(samples):
    print("\nСтатистика измерений:")
    for metric in ("cpu", "ram", "disk"):
        values = [sample[metric] for sample in samples]
        average = sum(values) / len(values)
        print(
            f"{metric.upper()}: среднее = {average:.1f}%, "
            f"максимум = {max(values):.1f}%, "
            f"минимум = {min(values):.1f}%"
        )

    frequencies = [
        sample["cpu_freq_mhz"]
        for sample in samples
        if sample["cpu_freq_mhz"] is not None
    ]
    if frequencies:
        print(
            "CPU frequency: "
            f"среднее = {sum(frequencies) / len(frequencies):.1f} МГц, "
            f"максимум = {max(frequencies):.1f} МГц, "
            f"минимум = {min(frequencies):.1f} МГц"
        )
    else:
        print("CPU frequency: ОС не предоставила данные о частоте.")


def main():
    # Первый вызов нужен для корректного первого измерения CPU.
    psutil.cpu_percent(interval=None)
    samples = []

    fieldnames = [
        "time", "cpu", "ram", "disk", "cpu_freq_mhz", "alert"
    ]

    with open(LOG_FILE, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for number in range(1, SAMPLES + 1):
            time.sleep(INTERVAL)
            sample = take_sample()
            alerts = check_alerts(sample)
            sample["alert"] = "; ".join(alerts)
            writer.writerow(sample)
            file.flush()
            samples.append(sample)

            frequency_text = (
                f"{sample['cpu_freq_mhz']:.1f} МГц"
                if sample["cpu_freq_mhz"] is not None
                else "н/д"
            )
            warning = f" <-- ВНИМАНИЕ: {sample['alert']}" if alerts else ""
            print(
                f"{number:02d}/{SAMPLES} {sample['time']} "
                f"CPU {sample['cpu']:5.1f}% "
                f"RAM {sample['ram']:5.1f}% "
                f"DISK {sample['disk']:5.1f}% "
                f"Частота CPU {frequency_text}{warning}"
            )

    print(f"\nЖурнал сохранён в {LOG_FILE}")
    print_statistics(samples)


if __name__ == "__main__":
    main()
