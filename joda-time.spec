
%undefine _compress
%undefine _extension
%global _duplicate_files_terminate_build 0
%global _files_listed_twice_terminate_build 0
%global _unpackaged_files_terminate_build 0
%global _nonzero_exit_pkgcheck_terminate_build 0
%global _use_internal_dependency_generator 0
%global __find_requires /bin/sed -e 's/.*//'
%global __find_provides /bin/sed -e 's/.*//'

Name:		joda-time
Version:	2.3
Release:	1.tzdata2013g.0
License:	GPLv3+
Source0:	joda-time-2.3-1.tzdata2013g.0-omv2014.0.noarch.rpm

URL:		https://abf.rosalinux.ru/openmandriva/joda-time
BuildArch:	noarch
Summary:	joda-time bootstrap version
Requires:	javapackages-bootstrap
Requires:	jpackage-utils
Requires:	mvn(org.joda:joda-convert)
Provides:	joda-time = 2.3-1.tzdata2013g.0:2014.0
Provides:	mvn(joda-time:joda-time) = 2.3
Provides:	osgi(joda-time) = 2.3

%description
joda-time bootstrap version.

%files
/usr/share/doc/joda-time
/usr/share/doc/joda-time/LICENSE.txt
/usr/share/doc/joda-time/NOTICE.txt
/usr/share/doc/joda-time/RELEASE-NOTES.txt
/usr/share/java/joda-time.jar
/usr/share/maven-effective-poms/JPP-joda-time.pom
/usr/share/maven-fragments/joda-time.xml
/usr/share/maven-poms/JPP-joda-time.pom

#------------------------------------------------------------------------
%prep

%build

%install
cd %{buildroot}
rpm2cpio %{SOURCE0} | cpio -id
