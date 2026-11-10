#!/usr/bin/env python3
"""Portuguese, read-only graphical planning wizard for Smart TV OS."""
from __future__ import annotations

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QSpinBox, QStackedWidget,
    QVBoxLayout, QWidget,
)

from installer.disk_layout import inspect_free_regions
from installer.disk_plan import GIB, InstallPlan, UnsafeInstallPlan, validate_install_plan
from installer.smarttv_installer import inspect_system


STYLE = """
QMainWindow, QWidget { background: #101522; color: #f4f6fb; font-family: 'Noto Sans', sans-serif; }
QLabel#eyebrow { color: #7fb8ff; font-size: 13px; font-weight: 700; letter-spacing: 2px; }
QLabel#title { color: #ffffff; font-size: 30px; font-weight: 700; }
QLabel#subtitle { color: #b6c1d2; font-size: 16px; }
QFrame#card { background: #1a2435; border: 1px solid #2b3a52; border-radius: 18px; }
QLabel#cardTitle { font-size: 19px; font-weight: 700; color: #ffffff; }
QLabel#body { color: #c8d2e1; font-size: 15px; }
QLabel#warning { color: #ffd27a; font-size: 14px; }
QLabel#status { color: #9fe4c1; font-size: 14px; }
QComboBox, QSpinBox { background: #0d1420; border: 1px solid #43536d; border-radius: 9px; padding: 12px; min-height: 22px; font-size: 15px; }
QComboBox QAbstractItemView { background: #182235; selection-background-color: #275b99; }
QCheckBox { color: #e9eef7; font-size: 14px; spacing: 10px; }
QPushButton { background: #27364d; color: white; border: 1px solid #3a4d69; border-radius: 10px; padding: 13px 22px; font-size: 15px; font-weight: 700; }
QPushButton:hover { background: #344a68; }
QPushButton#primary { background: #2878d0; border: 1px solid #398ce6; }
QPushButton#primary:hover { background: #398ce6; }
QPushButton:disabled { color: #78869a; background: #202b3d; border-color: #2d3b50; }
"""


def card(title: str, body: str) -> QFrame:
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(24, 22, 24, 22)
    heading = QLabel(title)
    heading.setObjectName("cardTitle")
    detail = QLabel(body)
    detail.setObjectName("body")
    detail.setWordWrap(True)
    layout.addWidget(heading)
    layout.addWidget(detail)
    return frame


class InstallerWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart TV OS — Assistente de instalação")
        self.setMinimumSize(1040, 680)
        self.inventory = {}
        self.free_regions = []
        self.windows_present = False
        self.windows_disk_paths = set()
        self.bitlocker_detected = False
        self.validation_label = None

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(42, 30, 42, 26)
        root.setSpacing(18)

        header = QHBoxLayout()
        brand = QLabel("SMART TV OS")
        brand.setStyleSheet("font-size: 15px; font-weight: 800; letter-spacing: 3px; color: #8cc4ff;")
        self.step_label = QLabel("ETAPA 1 DE 4")
        self.step_label.setStyleSheet("font-size: 13px; color: #91a2ba; font-weight: 700;")
        header.addWidget(brand)
        header.addStretch(1)
        header.addWidget(self.step_label)
        root.addLayout(header)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._welcome_page())
        self.pages.addWidget(self._check_page())
        self.pages.addWidget(self._disk_page())
        self.pages.addWidget(self._review_page())
        root.addWidget(self.pages, 1)

        footer = QHBoxLayout()
        self.back_button = QPushButton("Voltar")
        self.back_button.clicked.connect(self.back)
        self.next_button = QPushButton("Continuar")
        self.next_button.setObjectName("primary")
        self.next_button.clicked.connect(self.next)
        footer.addWidget(self.back_button)
        footer.addStretch(1)
        footer.addWidget(self.next_button)
        root.addLayout(footer)
        self.setCentralWidget(central)
        self.setStyleSheet(STYLE)
        self._load_inventory()
        self._update_navigation()
        self.showMaximized()

    def _heading(self, eyebrow: str, title: str, subtitle: str):
        box = QVBoxLayout()
        a = QLabel(eyebrow.upper())
        a.setObjectName("eyebrow")
        b = QLabel(title)
        b.setObjectName("title")
        c = QLabel(subtitle)
        c.setObjectName("subtitle")
        c.setWordWrap(True)
        box.addWidget(a)
        box.addWidget(b)
        box.addWidget(c)
        return box

    def _welcome_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addLayout(self._heading(
            "Bem-vindo", "Preparação do Smart TV OS",
            "Assistente em português para inspecionar o computador e planejar um possível dual boot com Windows 10/11.",
        ))
        layout.addSpacing(10)
        layout.addWidget(card(
            "Meta: preservar o Windows",
            "A instalação futura deverá usar exclusivamente espaço realmente não alocado. "
            "A partição EFI existente deverá ser reutilizada sem formatação. Se a identificação do Windows, "
            "do disco ou da geometria não for inequívoca, o instalador deverá bloquear a operação.",
        ))
        layout.addWidget(card(
            "Antes de qualquer instalação futura",
            "Faça backup dos arquivos e confirme a chave de recuperação do BitLocker. "
            "Esta versão não consegue certificar o estado do BitLocker e não executa alterações no Windows.",
        ))
        warning = QLabel(
            "AVISO: esta versão é somente de diagnóstico e planejamento. Não cria partições, "
            "não formata discos, não instala o sistema e não garante ainda um dual boot funcional."
        )
        warning.setObjectName("warning")
        warning.setWordWrap(True)
        layout.addWidget(warning)
        layout.addStretch(1)
        return page

    def _check_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addLayout(self._heading(
            "Verificação", "Vamos conferir o computador",
            "A leitura é somente de consulta. A pré-detecção de Windows é indicativa; "
            "não comprova sozinha que o volume contém uma instalação funcional.",
        ))
        self.check_summary = QLabel("Inspeção ainda não executada.")
        self.check_summary.setObjectName("body")
        self.check_summary.setWordWrap(True)
        layout.addWidget(card("Resultado da inspeção", ""))
        layout.addWidget(self.check_summary)
        self.warning_list = QLabel("")
        self.warning_list.setObjectName("warning")
        self.warning_list.setWordWrap(True)
        layout.addWidget(self.warning_list)
        layout.addStretch(1)
        return page

    def _disk_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addLayout(self._heading(
            "Destino", "Escolha o disco e o espaço livre",
            "Somente regiões reportadas como Free Space pelo parted podem ser consideradas. Partições existentes não são destinos válidos.",
        ))

        disk_title = QLabel("Disco de destino")
        disk_title.setObjectName("cardTitle")
        self.disk_combo = QComboBox()
        self.disk_combo.currentIndexChanged.connect(self._refresh_selected_disk)
        layout.addWidget(disk_title)
        layout.addWidget(self.disk_combo)

        region_title = QLabel("Região não alocada")
        region_title.setObjectName("cardTitle")
        self.region_combo = QComboBox()
        self.region_combo.currentIndexChanged.connect(self._update_root_limit)
        layout.addWidget(region_title)
        layout.addWidget(self.region_combo)

        efi_title = QLabel("Partição EFI existente no mesmo disco")
        efi_title.setObjectName("cardTitle")
        self.efi_combo = QComboBox()
        layout.addWidget(efi_title)
        layout.addWidget(self.efi_combo)

        root_title = QLabel("Tamanho reservado para o sistema (GiB)")
        root_title.setObjectName("cardTitle")
        self.root_size = QSpinBox()
        self.root_size.setRange(40, 4096)
        self.root_size.setValue(80)
        layout.addWidget(root_title)
        layout.addWidget(self.root_size)

        self.disk_note = QLabel("Selecione manualmente um disco.")
        self.disk_note.setObjectName("warning")
        self.disk_note.setWordWrap(True)
        layout.addWidget(self.disk_note)
        layout.addStretch(1)
        return page

    def _review_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addLayout(self._heading(
            "Revisão", "Confira o planejamento",
            "A validação abaixo é uma simulação. Nenhuma operação de escrita será executada.",
        ))
        self.review_summary = QLabel("Selecione disco, espaço livre e partição EFI na etapa anterior.")
        self.review_summary.setObjectName("body")
        self.review_summary.setWordWrap(True)
        layout.addWidget(card("Resumo do plano", ""))
        layout.addWidget(self.review_summary)

        self.bitlocker_ack = QCheckBox(
            "Reconheço que o estado do BitLocker não é verificado por esta versão. Esta confirmação é apenas ciência e não autoriza instalação."
        )
        self.bitlocker_ack.setVisible(False)
        layout.addWidget(self.bitlocker_ack)

        self.review_ack = QCheckBox(
            "Confirmo que revisei o disco, a região não alocada e a EFI. Entendo que esta validação é apenas uma simulação."
        )
        layout.addWidget(self.review_ack)

        self.validation_label = QLabel(
            "A validação não libera a instalação. O mecanismo de particionamento e cópia do sistema ainda não existe."
        )
        self.validation_label.setObjectName("warning")
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)

        self.validate_button = QPushButton("Validar plano (simulação)")
        self.validate_button.clicked.connect(self.validate_plan)
        layout.addWidget(self.validate_button)
        layout.addStretch(1)
        return page

    def _load_inventory(self):
        try:
            self.inventory = inspect_system()
        except Exception as exc:
            self.inventory = {}
            self.check_summary.setText("Não foi possível inspecionar os discos: " + str(exc))
            self.warning_list.setText("A instalação permanece bloqueada.")
            return

        disks = self.inventory.get("disks", [])
        self.windows_present = bool(
            self.inventory.get("windows_detected") or self.inventory.get("windows_candidates")
        )
        self.windows_disk_paths = set(self.inventory.get("windows_disk_paths", []))
        self.bitlocker_detected = bool(self.inventory.get("bitlocker_detected"))
        self.check_summary.setText(
            "Inicialização UEFI: {uefi}\n"
            "Pré-detecção Windows (os-prober + NTFS único): {windows}\n"
            "Partições NTFS candidatas: {candidates}\n"
            "Associações ambíguas: {ambiguous}\n"
            "Partições EFI confirmadas: {efi}\n"
            "Discos detectados: {disks}\n"
            "Discos com pré-detecção Windows: {windows_disks}\n"
            "BitLocker detectado: {bitlocker}".format(
                uefi="SIM" if self.inventory.get("uefi") else "NÃO",
                windows=(
                    "SIM — " + ", ".join(sorted(self.windows_disk_paths))
                    if self.windows_disk_paths else "NÃO confirmada"
                ),
                candidates=len(self.inventory.get("windows_candidates", [])),
                ambiguous=len(self.inventory.get("windows_ambiguous_entries", [])),
                efi=len(self.inventory.get("efi_partitions", [])),
                disks=len(disks),
                windows_disks=", ".join(self.inventory.get("windows_disk_paths", [])) or "nenhum",
                bitlocker="SIM" if self.bitlocker_detected else "não identificado (estado não certificado)",
            )
        )
        self.warning_list.setText("\n".join("• " + x for x in self.inventory.get("warnings", [])))
        for disk in disks:
            label = "{} — {} — {:.1f} GiB".format(
                disk.get("path"),
                disk.get("model") or "modelo desconhecido",
                (disk.get("size_bytes") or 0) / GIB,
            )
            self.disk_combo.addItem(label, disk.get("path"))
        if disks:
            self.disk_combo.setCurrentIndex(-1)
        else:
            self.disk_note.setText("Nenhum disco foi detectado. Instalação bloqueada.")

    def _refresh_selected_disk(self):
        disk_path = self.disk_combo.currentData()
        self.region_combo.clear()
        self.efi_combo.clear()
        self.free_regions = []
        if not disk_path:
            self.disk_note.setText("Selecione manualmente um disco.")
            return
        disk = next((d for d in self.inventory.get("disks", []) if d.get("path") == disk_path), None)
        if not disk or (disk.get("partition_table") or "").lower() != "gpt":
            self.disk_note.setText("Este disco não foi confirmado como GPT. Nenhum plano pode ser validado.")
            return
        try:
            self.free_regions = inspect_free_regions(disk_path)
        except Exception as exc:
            self.disk_note.setText("Não foi possível ler a geometria do disco: " + str(exc))
            return
        for region in self.free_regions:
            size_gib = region["size_bytes"] / GIB
            start_gib = region["start_bytes"] / GIB
            self.region_combo.addItem(
                "{:.1f} GiB livres — início em {:.3f} GiB".format(size_gib, start_gib),
                region,
            )
        for efi in self.inventory.get("efi_partitions", []):
            if efi.get("disk_path") == disk_path:
                self.efi_combo.addItem(
                    "{} — {:.0f} MiB — {}".format(
                        efi.get("path"), (efi.get("size_bytes") or 0) / (1024 ** 2),
                        efi.get("label") or "EFI",
                    ),
                    efi.get("path"),
                )
        self.efi_combo.setCurrentIndex(-1)
        if not self.free_regions:
            self.disk_note.setText("Nenhuma região não alocada foi confirmada. Não selecione nem formate partições existentes.")
        elif self.efi_combo.count() == 0:
            self.disk_note.setText("Não há EFI System Partition confirmada neste disco. Plano bloqueado.")
        elif disk_path not in self.windows_disk_paths:
            self.disk_note.setText(
                "A pré-detecção de Windows não foi associada a este disco. Por segurança, o plano de dual boot será bloqueado."
            )
        else:
            self.disk_note.setText(
                "Pré-detecção Windows associada a este disco. A existência do sistema ainda precisará de confirmação adicional."
            )
        self._update_root_limit()

    def _update_root_limit(self):
        region = self.region_combo.currentData()
        if not region:
            self.root_size.setEnabled(False)
            return
        max_gib = int(region["size_bytes"] // GIB)
        if max_gib < 40:
            self.root_size.setEnabled(False)
            return
        self.root_size.setEnabled(True)
        self.root_size.setMaximum(max_gib)
        self.root_size.setMinimum(40)
        self.root_size.setValue(min(80, max_gib))

    def _prepare_review(self):
        disk_path = self.disk_combo.currentData()
        region = self.region_combo.currentData()
        efi_path = self.efi_combo.currentData()
        self.review_ack.setChecked(False)
        if not disk_path or not region or not efi_path:
            self.review_summary.setText("Selecione um disco GPT, uma região não alocada e uma EFI do mesmo disco.")
            self.bitlocker_ack.setVisible(self.windows_present or self.bitlocker_detected)
            return
        self.review_summary.setText(
            "Disco: {disk}\n"
            "Região livre: início {start:.3f} GiB; tamanho {size:.1f} GiB\n"
            "Partição raiz planejada: {root} GiB\n"
            "EFI existente: {efi} (reutilizar, sem formatar)\n"
            "Pré-detecção Windows neste disco: {windows}\n"
            "Partições existentes alteradas: NÃO\n"
            "Execução de instalação: DESABILITADA".format(
                disk=disk_path,
                start=region["start_bytes"] / GIB,
                size=region["size_bytes"] / GIB,
                root=self.root_size.value(),
                efi=efi_path,
                windows=(
                    "SIM — ainda requer confirmação adicional" if disk_path in self.windows_disk_paths
                    else "NÃO associada a este disco"
                ),
            )
        )
        self.bitlocker_ack.setVisible(self.windows_present or self.bitlocker_detected)
        self.validation_label.setText(
            "A validação é somente uma simulação. A instalação real continua bloqueada."
        )

    def validate_plan(self):
        disk_path = self.disk_combo.currentData()
        region = self.region_combo.currentData()
        efi_path = self.efi_combo.currentData()
        if not disk_path or not region or not efi_path:
            QMessageBox.warning(self, "Plano incompleto", "Selecione disco, espaço livre e partição EFI.")
            return
        disk = next((d for d in self.inventory.get("disks", []) if d.get("path") == disk_path), {})
        inventory = dict(self.inventory)
        inventory["free_regions"] = [region]
        plan = InstallPlan(
            disk_path=disk_path,
            table=disk.get("partition_table") or "",
            boot_mode="uefi" if self.inventory.get("uefi") else "legacy",
            free_region_start=region["start_bytes"],
            free_region_bytes=region["size_bytes"],
            root_bytes=self.root_size.value() * GIB,
            efi_partition_path=efi_path,
            windows_present=self.windows_present,
            windows_pre_detected=disk_path in self.windows_disk_paths,
            bitlocker_detected=self.bitlocker_detected,
            bitlocker_acknowledged_by_user=self.bitlocker_ack.isChecked(),
            user_confirmed=self.review_ack.isChecked(),
        )
        try:
            result = validate_install_plan(plan, inventory)
        except UnsafeInstallPlan as exc:
            self.validation_label.setText("PLANO BLOQUEADO: " + str(exc))
            self.validation_label.setStyleSheet("color: #ffb0a8; font-size: 15px;")
            return
        self.validation_label.setText(
            "PRÉ-PLANO CONSISTENTE (SIMULAÇÃO). EFI não será formatada; partições existentes não serão alteradas. "
            "Windows/BitLocker não foram verificados e a instalação não está autorizada."
        )
        self.validation_label.setStyleSheet("color: #9fe4c1; font-size: 15px;")

    def back(self):
        index = max(0, self.pages.currentIndex() - 1)
        self.pages.setCurrentIndex(index)
        self._update_navigation()

    def next(self):
        index = self.pages.currentIndex()
        if index == 0:
            self.pages.setCurrentIndex(1)
        elif index == 1:
            if not self.inventory.get("uefi"):
                QMessageBox.warning(self, "UEFI necessário", "Inicialize a mídia em modo UEFI. A instalação está bloqueada.")
                return
            self.pages.setCurrentIndex(2)
        elif index == 2:
            self.pages.setCurrentIndex(3)
            self._prepare_review()
        else:
            self.close()
            return
        self._update_navigation()

    def _update_navigation(self):
        index = self.pages.currentIndex()
        self.step_label.setText("ETAPA {} DE 4".format(index + 1))
        self.back_button.setEnabled(index > 0)
        self.next_button.setText("Encerrar" if index == 3 else "Continuar")


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = InstallerWindow()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
