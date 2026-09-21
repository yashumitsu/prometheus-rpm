# Отключаем debugsource / debug_package для Rust
%global _debugsource_template %{nil}
%global debug_package %{nil}

# https://github.com/softwaremill/klag-exporter
%global gh_owner      softwaremill
%global gh_project    klag-exporter
%global upstream_tag  v0.1.27
%global upstream_arch linux-x86_64

Name:           klag-exporter
Version:        0.1.27
Release:        1%{?dist}
Summary:        High-performance Kafka consumer group lag exporter for Prometheus and OTLP
License:        MIT
URL:            https://github.com/%{gh_owner}/%{gh_project}

Source0:		%{url}/archive/refs/tags/v%{version}.tar.gz#/%{name}-%{version}.tar.gz
Source1:        %{name}.service
Source2:        %{name}.default
# --- Klag exporter config defaults ---
Source3:		%{name}.toml

# --- systemd integration ---
%{?systemd_requires}
%if 0%{?fedora} >= 19
BuildRequires:  systemd-rpm-macros
%endif

%description
klag-exporter is a high-performance Apache Kafka consumer group lag exporter
written in Rust. It calculates both offset lag and time lag (latency in seconds)
with accurate timestamp-based measurements, and exposes metrics natively via
Prometheus HTTP endpoint and OpenTelemetry OTLP.

%prep
%autosetup -n %{gh_project}-%{version}

%install
install -Dpm0755 target/release/klag-exporter %{buildroot}%{_bindir}/%{name}
install -Dpm0644 %{SOURCE1} %{buildroot}%{_unitdir}/%{name}.service
install -Dpm0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/default/%{name}
install -Dpm0644 %{SOURCE3} %{buildroot}%{_sysconfdir}/%{name}/%{name}.toml

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
%{defattr(-,root,root,-)
%%{_bindir}/%{name}
{_unitdir}/%{name}.service
%config(noreplace) %{_sysconfdir}/default/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.toml
%dir %attr(0755,prometheus,prometheus) %{_sharedstatedir}/prometheus

