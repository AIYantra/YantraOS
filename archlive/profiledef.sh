#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# YantraOS — archiso profile definition
# Target: ~/archlive/profiledef.sh
# ──────────────────────────────────────────────────────────────────────────────

iso_name="yantraos"
iso_label="YANTRA_$(date +%Y%m)"
iso_publisher="YantraOS Engineering <builder@yantraos.com>"
iso_application="YantraOS Automated Payload"
iso_version="$(date +%Y.%m.%d)"
install_dir="arch"
buildmodes=('iso')
bootmodes=('bios.syslinux.mbr' 'bios.syslinux.eltorito'
           'uefi-ia32.grub.esp' 'uefi-x64.grub.esp'
           'uefi-ia32.grub.eltorito' 'uefi-x64.grub.eltorito')
arch="x86_64"
pacman_conf="pacman.conf"
airootfs_image_type="erofs"
airootfs_image_tool_options=('-zlz4hc,12' -E ztailpacking)
bootstrap_tarball_compression=(zstd -c -T0 --auto-threads=logical --long -19)
file_permissions=(
  ["/etc/shadow"]="0:0:400"
  ["/etc/gshadow"]="0:0:400"
  ["/root"]="0:0:750"
  ["/root/.automated_script.sh"]="0:0:0755"
  ["/home/yantra_user"]="1000:1000:0700"
  ["/usr/local/bin/choose-mirror"]="0:0:755"
  ["/usr/local/bin/Installation_guide"]="0:0:755"
  ["/usr/local/bin/livecd-sound"]="0:0:755"
)
