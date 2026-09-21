# Отключаем debugsource / debug_package для Rust
%global _debugsource_template %{nil}
%global debug_package %{nil}

Name:           klag_exporter
Version:        0.1.27
Release:        1%{?dist}
Summary:        High-performance Kafka consumer group lag exporter for Prometheus and OTLP
License:        MIT
URL:            https://github.com/%{gh_owner}/%{gh_project}

Source0:        %{url}/archive/refs/tags/%{upstream_tag}.tar.gz#/%{name}-%{version}.tar.gz
Source1:        %{name}.service
Source2:        %{name}.default
# --- Klag exporter config defaults ---
Source3:		%{name}.toml

# --- Rust toolchain ---
BuildRequires:  rust >= 1.78
BuildRequires:  cargo

# --- C/C++ компиляция (для bundled librdkafka) ---
BuildRequires:  cmake
BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  pkgconfig

# --- libclang (для bindgen) ---
BuildRequires:  clang-devel

# --- Зависимости librdkafka (SSL, SASL, сжатие, OAuth) ---
BuildRequires:  openssl-devel
BuildRequires:  cyrus-sasl-devel
BuildRequires:  zlib-devel
BuildRequires:  libcurl-devel
BuildRequires:  lz4-devel
BuildRequires:  libzstd-devel

# --- Python (используется в сборочных скриптах librdkafka) ---
BuildRequires:  python3

# --- systemd integration ---
%{?systemd_requires}
%if 0%{?fedora} >= 19
BuildRequires:  systemd-rpm-macros
%endif

# --- Runtime dependencies ---
# librdkafka компилируется статически, но openssl / sasl линкуются динамически
Requires:       openssl-libs
Requires:       cyrus-sasl-lib
Requires:       systemd

%description
klag-exporter is a high-performance Apache Kafka consumer group lag exporter
written in Rust. It calculates both offset lag and time lag (latency in seconds)
with accurate timestamp-based measurements, and exposes metrics natively via
Prometheus HTTP endpoint and OpenTelemetry OTLP.

%prep
%autosetup -n %{gh_project}-%{version}

# Готовим оффлайн-сборку Cargo: скачиваем все крейты в vendor/
cargo vendor --locked vendor
mkdir -p .cargo
cat > .cargo/config.toml <<'EOF'
[source.crates-io]
replace-with = "vendored-sources"

[source.vendored-sources]
directory = "vendor"
EOF

%build
# Собираем релизный бинарник. rdkafka по умолчанию собирает librdkafka из bundled-сорцов.
cargo build --release --offline

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

