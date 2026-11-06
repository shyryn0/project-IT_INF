"""Автоматическая инвентаризация компьютера. Лабораторная работа №4."""

import json
import platform
import socket
from datetime import datetime

import psutil


def get_system_info():
    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "boot_time": datetime.fromtimestamp(
            psutil.boot_time()
        ).strftime("%Y-%m-%d %H:%M"),
    }


def get_cpu_info():
    freq = psutil.cpu_freq()
    return {
        "model": platform.processor() or platform.machine(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "max_freq_mhz": round(freq.max) if freq and freq.max else None,
        "load_percent": psutil.cpu_percent(interval=1),
    }


def get_memory_info():
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / 1024**3, 1),
        "used_percent": mem.percent,
        "available_gb": round(mem.available / 1024**3, 1),
    }


def get_disk_info():
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except (PermissionError, OSError):
            continue

        disks.append({
            "device": part.device,
            "mountpoint": part.mountpoint,
            "fs": part.fstype,
            "total_gb": round(usage.total / 1024**3, 1),
            "used_percent": usage.percent,
        })
    return disks


def get_network_info():
    interfaces = []
    for name, addrs in psutil.net_if_addrs().items():
        ipv4 = None
        netmask = None
        mac = None

        for address in addrs:
            if address.family == socket.AF_INET:
                ipv4 = address.address
                netmask = address.netmask
            elif address.family == psutil.AF_LINK:
                mac = address.address

        # По условию задания интерфейсы без IPv4 пропускаются.
        if ipv4:
            interfaces.append({
                "name": name,
                "ipv4": ipv4,
                "netmask": netmask,
                "mac": mac,
            })
    return interfaces


def analyze(passport):
    recommendations = []
    ram = passport["memory"]["total_gb"]
    cores = passport["cpu"]["physical_cores"] or 0

    if ram < 8:
        recommendations.append(
            "Недостаточно памяти для виртуальных машин и Docker"
        )

    if ram >= 16 and cores >= 6:
        recommendations.append(
            "Подходит для одновременной работы нескольких VM"
        )

    for disk in passport["disks"]:
        if disk["used_percent"] > 85:
            recommendations.append(
                f"Освободить место на диске {disk['mountpoint']}"
            )

    if cores < 4:
        recommendations.append(
            "Процессор может стать узким местом (bottleneck)"
        )

    # Собственное правило: предупреждение при высокой загрузке RAM.
    if passport["memory"]["used_percent"] > 90:
        recommendations.append(
            "Высокая загрузка оперативной памяти"
        )

    if not recommendations:
        recommendations.append(
            "Критических рекомендаций по заданным правилам нет"
        )

    return recommendations


def main():
    passport = {
        "collected_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "system": get_system_info(),
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "disks": get_disk_info(),
        "network": get_network_info(),
    }
    passport["recommendations"] = analyze(passport)

    filename = f"passport_{passport['system']['hostname']}.json"
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(passport, file, indent=2, ensure_ascii=False)

    print(json.dumps(passport, indent=2, ensure_ascii=False))
    print(f"\nПаспорт сохранён в файл {filename}")


if __name__ == "__main__":
    main()
