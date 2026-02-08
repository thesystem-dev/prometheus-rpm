%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           thanos
Version:        0.40.1
Release:        2%{?dist}
Summary:        Highly available Prometheus setup with long-term storage

License:        Apache-2.0
URL:            https://thanos.io/

%ifarch aarch64
%global thanos_arch arm64
%global thanos_sha d76ece2b856e5da76f0ef8dceb92b2157286d0ffd26f4851e147b89ba2f0c643
%else
%global thanos_arch amd64
%global thanos_sha 5493dcb06f93fa72245eb5af283ce05ff40acb6c6e2071bac37532d26e9b83ee
%endif

Source0: https://github.com/thanos-io/thanos/releases/download/v%{version}/thanos-%{version}.linux-%{thanos_arch}.tar.gz#/%{thanos_sha}
Source1: thanos-query.service
Source2: thanos-store.service
Source3: thanos-compact.service
Source4: thanos-sidecar.service
Source5: thanos.tmpfiles.conf

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%{?sysusers_requires_compat}

%description
Thanos is a set of components that can be composed into a highly available
Prometheus setup with long-term storage capabilities.

%prep
%setup -q -c -T
tar -xf %{SOURCE0}

%build
/bin/true

%install
# Binary (do not assume tar layout)
cd thanos-%{version}.linux-%{thanos_arch}
install -D -m 0755 thanos %{buildroot}%{_bindir}/thanos

# systemd units
install -D -m 0644 %{SOURCE1} %{buildroot}%{_unitdir}/thanos-query.service
install -D -m 0644 %{SOURCE2} %{buildroot}%{_unitdir}/thanos-store.service
install -D -m 0644 %{SOURCE3} %{buildroot}%{_unitdir}/thanos-compact.service
install -D -m 0644 %{SOURCE4} %{buildroot}%{_unitdir}/thanos-sidecar.service

# Config directory (empty; user-managed)
install -d %{buildroot}%{_sysconfdir}/thanos

# Runtime directory
install -d -m 0750 %{buildroot}/var/lib/thanos
install -D -m 0644 %{SOURCE5} %{buildroot}%{_tmpfilesdir}/thanos.conf

# sysusers (EL8+)
install -d %{buildroot}%{_sysusersdir}
cat > %{buildroot}%{_sysusersdir}/thanos.conf << 'EOF'
u thanos - "Thanos service user" /var/lib/thanos
EOF

%post
%systemd_post thanos-query.service
%systemd_post thanos-store.service
%systemd_post thanos-compact.service
%systemd_post thanos-sidecar.service
if [ $1 -eq 1 ] && [ -x /usr/bin/systemd-tmpfiles ]; then
  /usr/bin/systemd-tmpfiles --create %{_tmpfilesdir}/thanos.conf >/dev/null 2>&1 || :
fi

%preun
%systemd_preun thanos-query.service
%systemd_preun thanos-store.service
%systemd_preun thanos-compact.service
%systemd_preun thanos-sidecar.service

%postun
%systemd_postun_with_restart thanos-query.service
%systemd_postun_with_restart thanos-store.service
%systemd_postun_with_restart thanos-compact.service
%systemd_postun_with_restart thanos-sidecar.service

%files
%{_bindir}/thanos
%{_unitdir}/thanos-query.service
%{_unitdir}/thanos-store.service
%{_unitdir}/thanos-compact.service
%{_unitdir}/thanos-sidecar.service
%dir %{_sysconfdir}/thanos
%attr(0750,thanos,thanos) %dir /var/lib/thanos
%{_tmpfilesdir}/thanos.conf
%{_sysusersdir}/thanos.conf

%changelog
* Sun Feb 08 2026 James Wilson <packages@thesystem.dev> - 0.40.1-2
- Add RestrictAddressFamilies to compact/sidecar/store unit hardening

* Wed Dec 17 2025 James Wilson <packages@thesystem.dev> - 0.40.1-1
- Initial RPM package
