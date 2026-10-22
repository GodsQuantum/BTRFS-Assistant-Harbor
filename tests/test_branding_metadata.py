"""CI guard: native Qt Harbor branding matches releases and translations."""
from pathlib import Path
import configparser
import re
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]

class BrandingTest(unittest.TestCase):
    def test_three_localized_readmes_and_correct_links(self):
        for name in ('README.md','README.fr.md','README.zh-CN.md'):
            text=(ROOT/name).read_text()
            with self.subTest(name=name):
                self.assertTrue('branding/logo.svg' in text or 'branding/logo-mark.svg' in text)
                self.assertIn('branding/workflow.svg',text)
                self.assertLess(len(text),4500)
                self.assertIn('docs/WORKSTATION_BACKUPS',text)
                self.assertIn('Snapshots in. Systems back.',text)
                self.assertIn('GodsQuantum/BTRFS-Assistant-Harbor/releases/latest',text)
                self.assertIn('GPL-3.0-or-later',text)
                self.assertIn('NFS',text)
                self.assertIn('macOS/APFS',text)
                self.assertNotIn('btrfs-harbor/actions/',text.lower())
                self.assertNotIn('Tauri 2',text)
                for page in ('README.md','README.fr.md','README.zh-CN.md'):
                    self.assertIn(page,text)

    def test_svg_sources_are_valid_and_native_window_icon_matches(self):
        for name in ('branding/logo.svg','branding/logo-mark.svg','branding/social-preview.svg',
                     'branding/workflow.svg','icons/btrfs-assistant-harbor.svg'):
            root=ET.parse(ROOT/name).getroot()
            with self.subTest(name=name):
                self.assertTrue(root.tag.endswith('svg'))
                self.assertTrue(root.attrib.get('viewBox'))
        qrc=(ROOT/'icons/icons.qrc').read_text()
        main=(ROOT/'src/main.cpp').read_text()
        self.assertIn('<file>btrfs-assistant-harbor.svg</file>',qrc)
        self.assertIn('QIcon(":/icons/btrfs-assistant-harbor.svg")',main)
        version = self.release_version()
        self.assertIn(f'setApplicationVersion("{version}")', main)
        self.assertEqual((ROOT/'icons/btrfs-assistant-harbor.svg').read_bytes(),
                         (ROOT/'branding/logo-mark.svg').read_bytes())

    def test_desktop_and_appstream_are_branded(self):
        cfg=configparser.ConfigParser(interpolation=None,strict=True)
        cfg.read(ROOT/'src/btrfs-assistant-harbor.desktop',encoding='utf-8')
        section=cfg['Desktop Entry']
        self.assertEqual(section['Name'],'Btrfs Assistant Harbor')
        self.assertEqual(section['Icon'],'btrfs-assistant-harbor')
        self.assertEqual(section['Exec'],'btrfs-assistant-harbor-launcher')
        self.assertIn('Name[zh_CN]',section)
        metadata=ET.parse(ROOT/'src/btrfs-assistant-harbor.metainfo.xml').getroot()
        self.assertEqual(metadata.findtext('name'),'Btrfs Assistant Harbor')
        self.assertEqual(metadata.findtext('project_license'),'GPL-3.0-or-later')
        self.assertIn('GodsQuantum/BTRFS-Assistant-Harbor',ET.tostring(metadata,encoding='unicode'))

    @staticmethod
    def release_version():
        cmake = (ROOT/'CMakeLists.txt').read_text()
        match = re.search(r'project\(btrfs-assistant-harbor VERSION ([0-9]+\.[0-9]+\.[0-9]+) LANGUAGES', cmake)
        if match is None:
            raise AssertionError("CMake stable semantic version is missing")
        return match.group(1)

    def test_packages_share_stable_semver(self):
        version = self.release_version()
        self.assertIn(f'VERSION {version} LANGUAGES', (ROOT/'CMakeLists.txt').read_text())
        self.assertIn(f'VERSION = "{version}-1"',(ROOT/'packaging/debian/build_preview.py').read_text())
        self.assertIn(f'Version: {version}',(ROOT/'packaging/fedora/btrfs-assistant-harbor.spec').read_text())
        self.assertIn(f'pkgver={version}',(ROOT/'packaging/arch/PKGBUILD.in').read_text())
        self.assertIn(f"{version}-1+deb13",(ROOT/'.github/workflows/certification.yml').read_text())
        for path in ('CHANGELOG.md','CONTRIBUTING.md','SECURITY.md','branding/BRAND.md','branding/PRESSKIT.md'):
            self.assertTrue((ROOT/path).is_file(),path)

if __name__=='__main__':
    unittest.main()
