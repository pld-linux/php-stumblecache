# TODO
# - add php55 support

# Conditional build:
%bcond_without	tests		# build without tests

%define		php_name	php%{?php_suffix}
%define		modname	stumblecache
Summary:	StumbleCache is a mmap backed caching extension for PHP
Name:		%{php_name}-%{modname}
Version:	1.0.0
Release:	0.1
License:	PHP 3.01
Group:		Development/Languages/PHP
Source0:	https://github.com/stumbleupon/stumblecache/archive/master/%{modname}-%{version}.tar.gz
# Source0-md5:	9dc64c217d4e0ae0bd6da7aece246ea4
URL:		https://github.com/stumbleupon/stumblecache
BuildRequires:	%{php_name}-devel
BuildRequires:	%{php_name}-pecl-igbinary-devel >= 1.1.2
BuildRequires:	rpmbuild(macros) >= 1.666
%if %{with tests}
BuildRequires:	%{php_name}-cli
BuildRequires:	%{php_name}-pcre
BuildRequires:	%{php_name}-pecl-igbinary
BuildRequires:	%{php_name}-session
BuildRequires:	%{php_name}-spl
%endif
%{?requires_php_extension}
Provides:	php(%{modname}) = %{version}
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Stumblecache is a high performance shared memory cache that scales to
tens of gigabytes of cache, thousands of requests per second, and high
update rates. It was created to allow Stumbleupon to cache large
amounts of short ttl url data on our webserver and worker tiers.

You can think of it as a replacement for the user caching portion of
apc, though different tradeoffs have been made and stumblecache will
be less space efficient in most cases.

- MMAP based
- Fixed allocations ie. 500k 2k cache blocks

%prep
%setup -qc
mv %{modname}-*/* .

%build
phpize
%configure
%{__make}

%if %{with tests}
# simple module load test
%{__php} -n -q \
	-d extension_dir=modules \
	-d extension=%{php_extensiondir}/spl.so \
	-d extension=%{php_extensiondir}/session.so \
	-d extension=%{php_extensiondir}/igbinary.so \
	-d extension=%{php_extensiondir}/pcre.so \
	-d extension=%{modname}.so \
	-m > modules.log
grep %{modname} modules.log

cat <<'EOF' > run-tests.sh
#!/bin/sh
export NO_INTERACTION=1 REPORT_EXIT_STATUS=1 MALLOC_CHECK_=2
%{__make} test \
	PHP_EXECUTABLE=%{__php} \
	PHP_TEST_SHARED_SYSTEM_EXTENSIONS="spl session pcre" \
	RUN_TESTS_SETTINGS="-q $*"
EOF

chmod +x run-tests.sh
./run-tests.sh -w failed.log
test -f failed.log -a ! -s failed.log
%endif

%install
rm -rf $RPM_BUILD_ROOT
%{__make} install \
	EXTENSION_DIR=%{php_extensiondir} \
	INSTALL_ROOT=$RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d
cat <<'EOF' > $RPM_BUILD_ROOT%{php_sysconfdir}/conf.d/%{modname}.ini
; Enable %{modname} extension module
extension=%{modname}.so
EOF

%clean
rm -rf $RPM_BUILD_ROOT

%post
%php_webserver_restart

%postun
if [ "$1" = 0 ]; then
	%php_webserver_restart
fi

%files
%defattr(644,root,root,755)
%doc CREDITS EXPERIMENTAL
%config(noreplace) %verify(not md5 mtime size) %{php_sysconfdir}/conf.d/%{modname}.ini
%attr(755,root,root) %{php_extensiondir}/%{modname}.so
