Name:		joda-time
Version:	2.15.1
Release:	2
Summary:	Java date and time library
Group:		Development/Java
License:	ASL 2.0
URL:		https://www.joda.org/joda-time/
Source0:	https://github.com/JodaOrg/joda-time/archive/refs/tags/v%{version}.tar.gz#/joda-time-%{version}.tar.gz
# Gradle 9.9.1 strictly pins 2.14.0. No prebuilt jars.
Source1:	https://github.com/JodaOrg/joda-time/archive/refs/tags/v2.14.0.tar.gz#/joda-time-2.14.0.tar.gz

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
2.15.0 fixes DelegatedDurationField.equals. 2.15.1 stays the default
jar. Gradle 9.9.1 strictly pins 2.14.0, so that jar is installed
beside it, with its own zone tables. Tests are skipped.
The zone tables are compiled after the jar is packed, because the
exec plugin that upstream uses for that is not packaged.

%prep
%setup -q -n joda-time-%{version}
%setup -q -T -D -a 1 -n joda-time-%{version}
find . \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -delete
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

export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java}"
mkdir -p joda214/classes
find joda-time-2.14.0/src/main/java -name '*.java' ! -name 'module-info.java' > joda214/sources.list
test -s joda214/sources.list
"$JAVA_HOME/bin/javac" --release 8 -encoding UTF-8 -Xlint:-options \
	-cp %{_javadir}/joda-convert.jar \
	-d joda214/classes @joda214/sources.list
"$JAVA_HOME/bin/java" -Dorg.joda.time.DateTimeZone.Provider=org.joda.time.tz.UTCProvider \
	-cp "joda214/classes:%{_javadir}/joda-convert.jar" org.joda.time.tz.ZoneInfoCompiler \
	-src joda-time-2.14.0/src/main/java/org/joda/time/tz/src \
	-dst joda214/classes/org/joda/time/tz/data \
	africa antarctica asia australasia europe northamerica southamerica etcetera backward
test -s joda214/classes/org/joda/time/tz/data/ZoneInfoMap
"$JAVA_HOME/bin/jar" cf joda214/joda-time.jar -C joda214/classes .
cat > joda214/joda-time.pom << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>joda-time</groupId>
  <artifactId>joda-time</artifactId>
  <version>2.14.0</version>
  <name>Joda-Time</name>
  <description>Date and time library with chronology support.</description>
  <url>https://www.joda.org/joda-time/</url>
  <licenses>
    <license>
      <name>Apache License, Version 2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
</project>
EOF

%install -p
sysjar install --buildroot %{buildroot} \
	--artifact joda214/joda-time.pom:joda214/joda-time.jar \
	--file-name joda-time-2.14.0 \
	--filelist .mfiles214
# 2.15.1 owns joda-time.sysjar. 2.14.0 keeps a second index.
/bin/mv %{buildroot}/usr/share/sysjar/index/joda-time/joda-time.sysjar \
	%{buildroot}/usr/share/sysjar/index/joda-time/joda-time-2.14.0.sysjar
sed -i 's|/usr/share/sysjar/index/joda-time/joda-time\.sysjar|/usr/share/sysjar/index/joda-time/joda-time-2.14.0.sysjar|' .mfiles214

%install -a
while IFS= read -r line; do
	grep -qxF -- "$line" .mfiles || printf '%s\n' "$line" >> .mfiles
done < .mfiles214

%check -a
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java}"
cat > JodaSmoke.java << 'EOF'
import org.joda.time.DateTime;
import org.joda.time.DateTimeZone;
public class JodaSmoke {
	public static void main(String[] args) {
		DateTimeZone zone = DateTimeZone.forID("Europe/London");
		DateTime dt = new DateTime(0L, zone);
		int year = dt.getYear();
		if (year != 1970) {
			throw new AssertionError(year);
		}
		System.out.println(args[0] + " " + year + " " + zone.getID());
	}
}
EOF
convert=%{_javadir}/joda-convert.jar
"$JAVA_HOME/bin/javac" --release 8 -encoding UTF-8 -Xlint:-options \
	-cp "%{buildroot}%{_javadir}/joda-time.jar:$convert" JodaSmoke.java
"$JAVA_HOME/bin/java" -cp "%{buildroot}%{_javadir}/joda-time.jar:$convert:." JodaSmoke joda215_ok > check215.log
cat check215.log
grep -F -q 'joda215_ok 1970 Europe/London' check215.log
"$JAVA_HOME/bin/javac" --release 8 -encoding UTF-8 -Xlint:-options \
	-cp "%{buildroot}%{_javadir}/joda-time-2.14.0.jar:$convert" JodaSmoke.java
"$JAVA_HOME/bin/java" -cp "%{buildroot}%{_javadir}/joda-time-2.14.0.jar:$convert:." JodaSmoke joda214_ok > check214.log
cat check214.log
grep -F -q 'joda214_ok 1970 Europe/London' check214.log

%files -f .mfiles
%doc LICENSE.txt NOTICE.txt README.md RELEASE-NOTES.txt
