import os
import xml.etree.ElementTree as ET
from packaging.version import parse as parse_version

PARENT_POM = 'pom.xml'
PARENT_DIR = os.path.dirname(os.getcwd())

def extract_dep_versions(pom_path):
    tree = ET.parse(pom_path)
    root = tree.getroot()
    ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
    props = root.find('m:properties', ns)
    dep_versions = []
    if props is not None:
        for prop in props:
            if prop.tag.endswith('.version'):
                name = prop.tag.split('}', 1)[-1].replace('.version', '')
                dep_versions.append((name, prop.text.strip()))
    return dep_versions

def check_overrides(pom_path, dep_versions):
    tree = ET.parse(pom_path)
    root = tree.getroot()
    ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
    # Check for overridden properties
    props = root.find('m:properties', ns)
    if props is not None:
        for name, parent_version in dep_versions:
            prop_tag = f'{name}.version'
            for prop in props:
                if prop.tag.endswith(prop_tag):
                    override_version = prop.text.strip()
                    marker = compare(override_version, parent_version)
                    print(f'         Overrides property: {prop_tag} ({override_version}) parent: ({parent_version}) {marker}')
    # Check for overridden dependency versions
    for dep, parent_version in dep_versions:
        # found = False
        for dep_elem in root.findall('.//m:dependency', ns):
            art = dep_elem.find('m:artifactId', ns)
            ver = dep_elem.find('m:version', ns)
            if art is not None and art.text == dep and ver is not None:
                override_version = ver.text.strip()
                marker = compare(override_version, parent_version)
                print(f'         Overrides dependency version: {dep} ({override_version}) parent: ({parent_version}) {marker}')
                found = True
        # if not found:
        #     print(f'  No override for dependency: {dep}')


def compare(override_version, parent_version):
    marker = ""
    try:
        if parse_version(parent_version) < parse_version(override_version):
            marker = " !!!!"
    except Exception as e:
        print (f'Error comparing versions: {parent_version} and {override_version}: {e}')
        pass
    return marker


def main():
    dep_versions = extract_dep_versions(PARENT_POM)
    # for dep, version in dep_versions:
    #     print(f'{dep} {version}')
    for dir_name in os.listdir(PARENT_DIR):
        dir_path = os.path.join(PARENT_DIR, dir_name)
        if not os.path.isdir(dir_path):
            continue
        if os.path.basename(dir_path) == os.path.basename(os.getcwd()):
            continue
        pom = os.path.join(dir_path, 'pom.xml')
        if not os.path.isfile(pom):
            continue
        print(f'{pom.partition("modules/")[2]}')
        check_overrides(pom, dep_versions)

if __name__ == '__main__':
    main()