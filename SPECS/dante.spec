%define lname	libsocks0
Name:           dante
Version:        1.4.1
Release:        180.2
Summary:        A Free Socks v4 and v5 Client Implementation
License:        BSD-3-Clause
Group:          Productivity/Networking/Security
Url:            http://www.inet.no/dante/
Source0:        https://www.inet.no/dante/files/dante-%{version}.tar.gz
Source1:        sockd.service
Source2:        baselibs.conf
Source3:        %{name}-rpmlintrc
Source4:        sockd.tmpfilesd
Patch2:         dante-1.4.0-sockd_conf_man_format.patch
Patch3:         dante-1.4.0-socksify_man_format.patch
Patch4:         dante-1.4.0-glibc-2.17.patch
Patch5:         dante-1.4.0-sendbuf_macro.patch
Patch6:         dante-1.4.1-gcc5-fixes.patch
Patch7:         dante-1.4.1-rhel7-fixes.patch
Patch8:         dante-1.4.1-add-mptcp.patch
Patch9:         dante-1.4.1-nl.patch
Patch10:         dante-1.4.1-configure.patch
Patch11:         dante-1.4.1-header_file_conflict.patch
Patch12:         dante-1.4.1-conf_file.patch
BuildRequires:  autoconf >= 2.61
BuildRequires:  automake
BuildRequires:  bison
BuildRequires:  cyrus-sasl-devel
BuildRequires:  flex
BuildRequires:  krb5-devel
BuildRequires:  libtool
BuildRequires:  pam-devel
BuildRequires:  libcurl-devel
BuildRequires:  json-c-devel
BuildRequires:  libnl3-devel
BuildRoot:      %{_tmppath}/%{name}-%{version}-build
Requires: libcurl
Requires: json-c
Requires: libnl3

%description
Dante is a free implementation of the following proxy protocols: socks
version 4, socks version 5 (rfc1928), and msproxy. It can be used as a
firewall between networks. It is being developed by Inferno Nettverk
A/S, a Norwegian consulting company. Commercial support is available.

%package -n %{lname}
Summary:        A Free Socks v4 and v5 Client Implementation
Group:          Productivity/Networking/Security

%description -n %{lname}
Dante is a free implementation of the following proxy protocols: socks
version 4, socks version 5 (rfc1928), and msproxy. It can be used as a
firewall between networks. It is being developed by Inferno Nettverk
A/S, a Norwegian consulting company. Commercial support is available.

This package contains the dynamic libraries required to make existing
applications become socks clients.

%package -n dante-server
Summary:        A Free Socks v4/v5 Server Implementation
Group:          Productivity/Networking/Other
Requires:       dante
Provides:       dantesrv = %{version}
Obsoletes:      dantesrv < %{version}
%{?systemd_requires}

%description -n dante-server
This package contains the socks proxy daemon and its documentation. The
sockd is the server part of the Dante socks proxy package and allows
socks clients to connect through it to the network.

%package -n dante-devel
Summary:        Include Files and Libraries mandatory for Development
Group:          Development/Libraries/C and C++
Requires:       %{lname} = %{version}
Provides:       dantedev = %{version}
Obsoletes:      dantedev < %{version}

%description -n dante-devel
This package contains all necessary include files and libraries needed
to develop applications that require these.

%prep
%setup -q
%patch2
%patch3
%patch4
%patch5 -p1
%patch6 -p1
%patch7 -p1
%patch8 -p1
%patch9 -p0
%patch10 -p2
%patch11 -p0
%patch12 -p0

%build
DANTELIBC=`find /%{_lib}/ -maxdepth 1 -iname "libc.so.*"`
echo >> acinclude.m4
sed -i -e 's:AM_CONFIG_HEADER:AC_CONFIG_HEADERS:' configure.ac
autoreconf --force --install --verbose

# optflags contains -grecord-gcc-switches which is breaking configure
#CFLAGS="%%{optflags} -fno-strict-aliasing" \
CFLAGS=$(echo "%{optflags}" | sed "s|-grecord-gcc-switches||")
%configure \
	--disable-static \
	--with-pic \
        --enable-preload \
        --enable-clientdl \
        --enable-serverdl \
        --without-libwrap \
        --enable-drt-fallback \
	--enable-shared \
	--with-libc=$DANTELIBC
#	--with-libc=$DANTELIBC \
#	--disable-client \
#	--without-gssapi \
#	--without-krb5 \
#	--without-ldap
make %{?_smp_mflags} V=1

%install
make DESTDIR=%{buildroot} install %{?_smp_mflags}
#set library as executable - prevent ldd from complaining
chmod +x %{buildroot}%{_libdir}/*.so.*.*
install -d 	%{buildroot}%{_unitdir} \
	   	%{buildroot}%{_bindir} \
	   	%{buildroot}%{_sbindir} \
        %{buildroot}%{_sysconfdir}
install -m 644 example/socks.conf %{buildroot}/%{_sysconfdir}
install -m 644 example/sockd.conf %{buildroot}/%{_sysconfdir}
install -m 644 %{SOURCE1}	  %{buildroot}/%{_unitdir}/sockd.service
ln -sf          ../../%{_unitdir}/sockd.service	%{buildroot}%{_sbindir}/rcsockd
install -D -m 0644 -p %{SOURCE4} %{buildroot}%{_sysconfdir}/tmpfiles.d/sockd.conf
#
# fix bug #23141
#
mv %{buildroot}%{_bindir}/socksify %{buildroot}%{_bindir}/socksify.old
sed -e 's|libdl.so|/%{_lib}/libdl.so.2|' < %{buildroot}%{_bindir}/socksify.old > %{buildroot}%{_bindir}/socksify
#
rm %{buildroot}%{_bindir}/socksify.old
find %{buildroot} -type f -name "*.la" -delete -print

rm Makefile* SPECS/Makefile*

%post
/sbin/ldconfig
%systemd_post sockd.service

%pre
getent group sockd >/dev/null || groupadd -r sockd -g 498 &>/dev/null
getent passwd sockd >/dev/null || \
useradd -r -u 498 -g sockd -d / -s /sbin/nologin \
        -c "sockd" sockd &>/dev/null

%preun
%systemd_preun trafficserver.service

%postun
/sbin/ldconfig
%systemd_postun_with_restart trafficserver.service

%files
%defattr(-,root,root)
#files beginning with two capital letters are docs: BUGS, README.foo etc.
%doc [A-Z][A-Z]*
%{_libdir}/libdsocks.so
%attr(755,root,root) %{_bindir}/socksify
%{_mandir}/man1/socksify.1.gz
%{_mandir}/man5/socks.conf.5.gz
%config(noreplace) %{_sysconfdir}/socks.conf

%files -n %{lname}
%defattr(-,root,root)
%{_libdir}/libsocks.so.0.1.1
%{_libdir}/libsocks.so.0

%files -n dante-server
%defattr(-,root,root)
#doc [A-Z][A-Z]*
%{_mandir}/man8/sockd.8.gz
%{_mandir}/man5/sockd.conf.5.gz
%attr(755,root,root) %{_sbindir}/sockd
%config(noreplace) %{_sysconfdir}/sockd.conf
%{_unitdir}/sockd.service
%config(noreplace) %{_sysconfdir}/tmpfiles.d/sockd.conf
%{_sbindir}/rcsockd

%files -n dante-devel
%defattr(-,root,root)
#doc [A-Z][A-Z]*
%{_libdir}/libsocks.so
%{_includedir}/*.h

%changelog
* Sat Sep 19 2015 Bryan Seitz <seitz@ghettoforge.org> - 1.4.1-176.8
- Add tmpfiles.d and move pid file
- Fix sockd.service

* Sat Sep 19 2015 Bryan Seitz <seitz@ghettoforge.org> - 1.4.1-176.7
- Import into GhettoForge
