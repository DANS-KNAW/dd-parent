#
# Copyright (C) 2022 DANS - Data Archiving and Networked Services (info@dans.knaw.nl)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import os
import xml.etree.ElementTree as ET
from packaging.version import parse as parse_version

PARENT_POM = 'pom.xml'
PARENT_DIR = os.path.dirname(os.getcwd())
NS = {'m': 'http://maven.apache.org/POM/4.0.0'}

def extract_dep_versions(pom_path):
    tree = ET.parse(pom_path)
    root = tree.getroot()
    props = root.find('m:properties', NS)
    dep_versions = []
    for prop in props or []:
        if prop.tag.endswith('.version'):
            name = prop.tag.split('}', 1)[-1].replace('.version', '')
            dep_versions.append((name, prop.text.strip()))
    return dep_versions

def check_overrides(pom_path, dep_versions):
    tree = ET.parse(pom_path)
    root = tree.getroot()
    parent_version_elem = root.find("m:parent/m:version", NS)
    parent_version_text = parent_version_elem.text.strip() if parent_version_elem is not None and parent_version_elem.text else ""
    print(f'{parent_version_text:<15} {pom_path.partition("modules/")[2]}')
    # Check for overridden properties
    props = root.find('m:properties', NS)
    for name, parent_version in dep_versions:
        prop_tag = f'{name}.version'
        for prop in props or []:
            overridden_version = prop.text.strip()
            if prop.tag.endswith(prop_tag) and overridden_version != parent_version:
                print(f'         Overrides property: {prop_tag} {show_versions(overridden_version, parent_version)}')
    # Check for overridden dependency versions
    for dep, parent_version in dep_versions:
        for dep_elem in root.findall('.//m:dependency', NS):
            art = dep_elem.find('m:artifactId', NS)
            ver = dep_elem.find('m:version', NS)
            if art is not None and art.text == dep and ver is not None:
                overridden_version = ver.text.strip()
                if  overridden_version[0].isdigit() and overridden_version != parent_version:
                    print(f'         Overrides version: {dep} {show_versions(overridden_version, parent_version)}')


def show_versions(override_version, parent_version):
    marker = ""
    if not override_version.startswith("$"):
        try:
            if parse_version(parent_version) < parse_version(override_version):
                marker = "!!!!" # parent version is behind
        except Exception:
            marker = "????" # not able to compare version
    return f'({override_version}) parent: ({parent_version}) {marker}'

def find_poms(parent_dir):
    poms = []
    for root, dirs, files in os.walk(parent_dir):
        if 'target' in dirs:
            dirs.remove('target')
        if 'pom.xml' in files:
            poms.append(os.path.join(root, 'pom.xml'))
    return poms


def main():
    dep_versions = extract_dep_versions(PARENT_POM)
    for pom in sorted(find_poms(PARENT_DIR)):
        if os.path.abspath(pom) != os.path.abspath(PARENT_POM):
            check_overrides(pom, dep_versions)

if __name__ == '__main__':
    main()