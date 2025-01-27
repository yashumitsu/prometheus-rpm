%global debug_package %{nil}
%global fix_name speedtest-exporter

Name:    speedtest_exporter
Version: 1.0.6
Release: 1%{?dist}
Summary: Speedtest exporter
License: ASL 2.0
URL:     https://github.com/heathcliff26/speedtest-exporter

Source0: https://github.com/heathcliff26/speedtest-exporter/archive/refs/tags/v%{version}.tar.gz
Source1: %{name}.service
Source2: %{name}.default

%{?systemd_requires}
%if 0%{?fedora} >= 19
BuildRequires: systemd-rpm-macros
%endif
BuildRequires: go

%description

A prometheus exporter that monitors network speed using the speedtest.net api.

%prep
%setup -q -n %{fix_name}-%{version}

%build
export GOTOOLCHAIN=auto
export RELEASE_VERSION="%{version}"
make build

%install
mkdir -vp %{buildroot}%{_sharedstatedir}/prometheus
install -D -m 755 ./bin/%{fix_name} %{buildroot}%{_bindir}/%{name}
install -D -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service
install -D -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/default/%{name}

%pre
getent group prometheus >/dev/null || groupadd -r prometheus
getent passwd prometheus >/dev/null || \
  useradd -r -g prometheus -d %{_sharedstatedir}/prometheus -s /sbin/nologin \
          -c "Prometheus services" prometheus
exit 0

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}.service

%files
%defattr(-,root,root,-)
%{_bindir}/%{name}
%{_unitdir}/%{name}.service
%config(noreplace) %{_sysconfdir}/default/%{name}
%dir %attr(755, prometheus, prometheus)%{_sharedstatedir}/prometheus
