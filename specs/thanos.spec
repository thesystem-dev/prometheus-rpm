%global debug_package %{nil}
%global _missing_build_ids_terminate_build 0

Name:           thanos
Version:        0.40.1
Release:        7%{?dist}
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
Source5: thanos-query-frontend.service
Source6: thanos-receive.service
Source7: thanos-rule.service
Source8: thanos.tmpfiles.conf
Source9: thanos.sysusers
Source10: thanos-query.conf
Source11: thanos-store.conf
Source12: thanos-compact.conf
Source13: thanos-sidecar.conf
Source14: thanos-query-frontend.conf
Source15: thanos-receive.conf
Source16: thanos-rule.conf
Source17: thanos-objectstore.yml.example
Source18: thanos-receive-hashrings.json.example

BuildRequires:  systemd-rpm-macros

ExclusiveArch: x86_64 aarch64

%{?systemd_requires}
%if 0%{?rhel} == 8
Requires(pre):  shadow-utils
%else
%{?sysusers_requires_compat}
%endif

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
install -D -m 0644 %{SOURCE5} %{buildroot}%{_unitdir}/thanos-query-frontend.service
install -D -m 0644 %{SOURCE6} %{buildroot}%{_unitdir}/thanos-receive.service
install -D -m 0644 %{SOURCE7} %{buildroot}%{_unitdir}/thanos-rule.service

# Config directory
install -d -m 0750 %{buildroot}%{_sysconfdir}/thanos
install -D -m 0644 %{SOURCE10} %{buildroot}%{_sysconfdir}/thanos/query.conf
install -D -m 0644 %{SOURCE11} %{buildroot}%{_sysconfdir}/thanos/store.conf
install -D -m 0644 %{SOURCE12} %{buildroot}%{_sysconfdir}/thanos/compact.conf
install -D -m 0644 %{SOURCE13} %{buildroot}%{_sysconfdir}/thanos/sidecar.conf
install -D -m 0644 %{SOURCE14} %{buildroot}%{_sysconfdir}/thanos/query-frontend.conf
install -D -m 0644 %{SOURCE15} %{buildroot}%{_sysconfdir}/thanos/receive.conf
install -D -m 0644 %{SOURCE16} %{buildroot}%{_sysconfdir}/thanos/rule.conf
install -D -m 0644 %{SOURCE17} %{buildroot}%{_sysconfdir}/thanos/objectstore.yml.example
install -D -m 0644 %{SOURCE18} %{buildroot}%{_sysconfdir}/thanos/receive-hashrings.json.example

# Runtime directory
install -d -m 0750 %{buildroot}/var/lib/thanos
install -D -m 0644 %{SOURCE8} %{buildroot}%{_tmpfilesdir}/thanos.conf

# sysusers (EL8+)
install -D -m 0644 %{SOURCE9} %{buildroot}%{_sysusersdir}/thanos.conf

%pre
%if 0%{?rhel} == 8
getent group thanos >/dev/null 2>&1 || groupadd -r thanos >/dev/null 2>&1 || :
getent passwd thanos >/dev/null 2>&1 || useradd -r -g thanos -d /var/lib/thanos -s /sbin/nologin -c "Thanos service user" thanos >/dev/null 2>&1 || :
%else
%sysusers_create_compat %{SOURCE9}
%endif

%post
%systemd_post thanos-query.service
%systemd_post thanos-store.service
%systemd_post thanos-compact.service
%systemd_post thanos-sidecar.service
%systemd_post thanos-query-frontend.service
%systemd_post thanos-receive.service
%systemd_post thanos-rule.service
if [ $1 -eq 1 ] && [ -x /usr/bin/systemd-tmpfiles ]; then
  /usr/bin/systemd-tmpfiles --create %{_tmpfilesdir}/thanos.conf >/dev/null 2>&1 || :
fi

%preun
%systemd_preun thanos-query.service
%systemd_preun thanos-store.service
%systemd_preun thanos-compact.service
%systemd_preun thanos-sidecar.service
%systemd_preun thanos-query-frontend.service
%systemd_preun thanos-receive.service
%systemd_preun thanos-rule.service

%postun
%systemd_postun_with_restart thanos-query.service
%systemd_postun_with_restart thanos-store.service
%systemd_postun_with_restart thanos-compact.service
%systemd_postun_with_restart thanos-sidecar.service
%systemd_postun_with_restart thanos-query-frontend.service
%systemd_postun_with_restart thanos-receive.service
%systemd_postun_with_restart thanos-rule.service

%files
%{_bindir}/thanos
%{_unitdir}/thanos-query.service
%{_unitdir}/thanos-store.service
%{_unitdir}/thanos-compact.service
%{_unitdir}/thanos-sidecar.service
%{_unitdir}/thanos-query-frontend.service
%{_unitdir}/thanos-receive.service
%{_unitdir}/thanos-rule.service
%dir %attr(0750,root,thanos) %{_sysconfdir}/thanos
%config(noreplace) %attr(0640,root,thanos) %{_sysconfdir}/thanos/query.conf
%config(noreplace) %attr(0640,root,thanos) %{_sysconfdir}/thanos/store.conf
%config(noreplace) %attr(0640,root,thanos) %{_sysconfdir}/thanos/compact.conf
%config(noreplace) %attr(0640,root,thanos) %{_sysconfdir}/thanos/sidecar.conf
%config(noreplace) %attr(0640,root,thanos) %{_sysconfdir}/thanos/query-frontend.conf
%config(noreplace) %attr(0640,root,thanos) %{_sysconfdir}/thanos/receive.conf
%config(noreplace) %attr(0640,root,thanos) %{_sysconfdir}/thanos/rule.conf
%config(noreplace) %attr(0640,root,thanos) %{_sysconfdir}/thanos/objectstore.yml.example
%config(noreplace) %attr(0640,root,thanos) %{_sysconfdir}/thanos/receive-hashrings.json.example
%attr(0750,thanos,thanos) %dir /var/lib/thanos
%{_tmpfilesdir}/thanos.conf
%{_sysusersdir}/thanos.conf

%changelog
* Mon Feb 16 2026 James Wilson <packages@thesystem.dev> - 0.40.1-7
- Run thanos-sidecar as prometheus so shipper metadata writes succeed on Prometheus TSDB paths
- Keep access to /etc/thanos config via thanos supplementary group

* Mon Feb 16 2026 James Wilson <packages@thesystem.dev> - 0.40.1-6
- Add component config templates under /etc/thanos and example objectstore/hashring configs
- Set explicit Thanos listener defaults with documented hardening alternatives

* Sun Feb 15 2026 James Wilson <packages@thesystem.dev> - 0.40.1-5
- Add systemd units for thanos query-frontend, receive, and rule components

* Thu Feb 12 2026 James Wilson <packages@thesystem.dev> - 0.40.1-4
- Fix EL8 PREIN regression; create thanos account in %pre on EL8 and use sysusers compat on EL9-EL10

* Wed Feb 11 2026 James Wilson <packages@thesystem.dev> - 0.40.1-3
- Create thanos account in %pre via sysusers for correct file ownership on install

* Sun Feb 08 2026 James Wilson <packages@thesystem.dev> - 0.40.1-2
- Add RestrictAddressFamilies to compact/sidecar/store unit hardening

* Wed Dec 17 2025 James Wilson <packages@thesystem.dev> - 0.40.1-1
- Initial RPM package
