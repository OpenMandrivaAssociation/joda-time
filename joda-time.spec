Name:		joda-time
Version:	2.15.1
Release:	1
Summary:	Java date and time library
Group:		Development/Java
License:	ASL 2.0
URL:		https://www.joda.org/joda-time/
Source0:	https://github.com/JodaOrg/joda-time/archive/refs/tags/v%{version}.tar.gz#/joda-time-%{version}.tar.gz

BuildArch:	noarch
Obsoletes:	%{name}-javadoc < %{version}
BuildRequires:	mvn(org.joda:joda-convert)
# Literal, so the first rpmbuild -bs records them before sysjar is installed.
BuildRequires:	maven
BuildRequires:	java-current-devel
BuildSystem:	maven

%description
Joda-Time replaces the JDK date and time classes and adds chronology
support. 2.15.1 is the current release. Its zone data is 2026f, and
2.15.0 fixes DelegatedDurationField.equals. Tests are skipped.
The zone tables are compiled after the jar is packed, because the
exec plugin that upstream uses for that is not packaged.

%prep
%setup -q -n joda-time-%{version}
# exec-maven-plugin compiles the IANA zone sources. It is not packaged.
# The no-tzdb classifier is a second jar we do not ship.
python - <<'PY'
import xml.etree.ElementTree as ET
from pathlib import Path

ET.register_namespace("", "http://maven.apache.org/POM/4.0.0")
ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")

def local(tag):
    return tag.rsplit("}", 1)[-1]

path = Path("pom.xml")
tree = ET.parse(path)
root = tree.getroot()
removed_plugin = 0
removed_exec = 0
for parent in root.iter():
    for child in list(parent):
        if local(child.tag) == "plugin":
            artifact = ""
            for item in child:
                if local(item.tag) == "artifactId":
                    artifact = (item.text or "").strip()
            if artifact == "exec-maven-plugin":
                parent.remove(child)
                removed_plugin += 1
            continue
        if local(child.tag) != "execution":
            continue
        ident = ""
        for item in child:
            if local(item.tag) == "id":
                ident = (item.text or "").strip()
        if ident == "no-tzdb":
            parent.remove(child)
            removed_exec += 1
if removed_plugin != 1 or removed_exec != 1:
    raise SystemExit(f"plugin={removed_plugin} exec={removed_exec}")
tree.write(path, encoding="UTF-8", xml_declaration=True)
PY

%build -a
# UTCProvider stops DateTimeZone from reading the tables this compiler writes.
java -Dorg.joda.time.DateTimeZone.Provider=org.joda.time.tz.UTCProvider \
	-cp target/classes org.joda.time.tz.ZoneInfoCompiler \
	-src src/main/java/org/joda/time/tz/src \
	-dst target/classes/org/joda/time/tz/data \
	africa antarctica asia australasia europe northamerica southamerica etcetera backward
test -s target/classes/org/joda/time/tz/data/ZoneInfoMap
jar uf target/joda-time-%{version}.jar -C target/classes org/joda/time/tz/data
jar tf target/joda-time-%{version}.jar | grep -q '^org/joda/time/tz/data/ZoneInfoMap$'

%files -f .mfiles
%doc LICENSE.txt NOTICE.txt README.md RELEASE-NOTES.txt
