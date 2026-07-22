from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent
CALAMARES = ROOT / "archlive/airootfs/etc/calamares"


class InstallerProfileTests(unittest.TestCase):
    def test_pinned_calamares_is_built_for_the_iso(self) -> None:
        package_list = (ROOT / "archlive/packages.x86_64").read_text(encoding="utf-8")
        forge = (ROOT / "archlive/forge_sovereign_iso.sh").read_text(encoding="utf-8")
        pkgbuild = (ROOT / "archlive/calamares/PKGBUILD").read_text(encoding="utf-8")

        self.assertIn("\ncalamares\n", package_list)
        self.assertIn("makechrootpkg", forge)
        self.assertIn("repo-add", forge)
        self.assertIn("build_calamares", forge)
        self.assertIn("pkgver=3.4.2", pkgbuild)
        self.assertIn("733bbbb00dc9f84874bd5c22960952f317ea2537565431179fa2152b2fbfdccc", pkgbuild)
        self.assertIn("-DWITH_PYTHONQT=ON", pkgbuild)

    def test_installer_enforces_the_yantra_btrfs_layout(self) -> None:
        partition = (CALAMARES / "modules/partition.conf").read_text(encoding="utf-8")
        mount = (CALAMARES / "modules/mount.conf").read_text(encoding="utf-8")

        for expected in (
            "defaultPartitionTableType: gpt",
            "requiredPartitionTableType: gpt",
            "createHybridBootloaderLayout: true",
            "defaultFileSystemType: btrfs",
            "allowManualPartitioning: false",
            "recommendedSize: 512MiB",
            "enableLuksAutomatedPartitioning: false",
        ):
            self.assertIn(expected, partition)
        for expected in ("/@", "/@home", "/@log", "/@yantra-snapshots", "compress=zstd:1", "noatime"):
            self.assertIn(expected, mount)

    def test_target_initramfs_does_not_reuse_the_archiso_preset(self) -> None:
        settings = (CALAMARES / "settings.conf").read_text(encoding="utf-8")
        unpackfs = (CALAMARES / "modules/unpackfs.conf").read_text(encoding="utf-8")
        preset = (CALAMARES / "files/linux.preset").read_text(encoding="utf-8")
        cleanup = (CALAMARES / "modules/remove-archiso-initramfs.conf").read_text(encoding="utf-8")
        grub_entry = (CALAMARES / "files/09_yantraos").read_text(encoding="utf-8")
        finalizer = (ROOT / "archlive/airootfs/usr/local/lib/yantra/calamares-finalize").read_text(encoding="utf-8")

        self.assertIn("/arch/boot/x86_64/vmlinuz-linux", unpackfs)
        self.assertIn("destination: /boot/vmlinuz-linux", unpackfs)
        self.assertIn("destination: /etc/mkinitcpio.d/linux.preset", unpackfs)
        self.assertIn('ALL_kver="/boot/vmlinuz-linux"', preset)
        self.assertNotIn("archiso", preset)
        self.assertIn("rm -f /etc/mkinitcpio.conf.d/archiso.conf", cleanup)
        self.assertIn("destination: /etc/grub.d/09_yantraos", unpackfs)
        self.assertIn("search --no-floppy --fs-uuid --set=root ${ESP_UUID}", grub_entry)
        self.assertIn("rootflags=subvol=@", grub_entry)
        self.assertIn("/boot/efi/vmlinuz-linux", finalizer)
        self.assertIn("/boot/efi/initramfs-linux.img", finalizer)
        self.assertLess(
            settings.index("shellprocess@remove-archiso-initramfs"),
            settings.index("\n      - initcpio\n"),
        )

    def test_target_migration_preserves_daemon_boundaries(self) -> None:
        services = (CALAMARES / "modules/services-systemd.conf").read_text(encoding="utf-8")
        finalizer = (ROOT / "archlive/airootfs/usr/local/lib/yantra/calamares-finalize").read_text(encoding="utf-8")
        users = (CALAMARES / "modules/users.conf").read_text(encoding="utf-8")

        self.assertIn("yantra-sandbox-broker.service", services)
        self.assertIn("yantra-host-executor.service", services)
        self.assertIn("systemd-sysusers", finalizer)
        self.assertIn("systemd-tmpfiles --create", finalizer)
        self.assertIn("userdel -r yantra_live", finalizer)
        self.assertIn("/etc/sudoers.d/10-yantra-live", finalizer)
        self.assertIn("YANTRA_SECRETS_SOURCE", finalizer)
        self.assertIn("chattr +C /var/lib/yantra/chromadb", finalizer)
        self.assertIn("yantra_daemon", users)
        self.assertIn("yantra_live", users)


if __name__ == "__main__":
    unittest.main()
