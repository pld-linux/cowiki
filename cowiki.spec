# TODO
#  - lighttpd integration possible <http://wiki.lighttpd.net/33.html>.

%define _snap 2006-02-06
%define _rel 0.2
Summary:	Web collaboration tool
Summary(pl):	Narzêdzie do wspó³pracy i wspó³tworzenia w sieci
Name:		cowiki
Version:	0.4.0
Release:	%{?_snap:0.%(echo %{_snap} | tr -d -).}%{_rel}
Epoch:		0
License:	GPL
Group:		Applications/WWW
Source0:	http://snaps.cowiki.org/%{name}-%{version}-interim-%{_snap}.tar.gz
# Source0-md5:	522d3d73abc928516b1982f258633da5
Source1:	%{name}.conf
Patch0:		%{name}-FHS.patch
Patch1:		%{name}-config.patch
URL:		http://cowiki.org/
BuildRequires:	rpmbuild(macros) >= 1.268
Requires:	php >= 4:5.0.2
Requires:	php-dom
Requires:	php-mysql
Requires:	webapps
BuildArch:	noarch
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_webapps	/etc/webapps
%define		_webapp		%{name}
%define		_sysconfdir	%{_webapps}/%{_webapp}
%define		_appdir		%{_datadir}/%{_webapp}

%description
coWiki is a sophisticated but easy to use web collaboration tool that
helps you and your co-workers to create and organize web documents,
weblogs and knowledgebases or any other document structures directly
in their HTML browser. You may evolve ideas and gain a concomitant XML
documentation of your brainstorming without having to concentrate on
complicated structural syntaxes.

%description -l pl
coWiki to wyszukane, ale ³atwe w u¿yciu narzêdzie do pracy zespo³owej
przez WWW pomagaj±ce wspó³pracownikom tworzyæ i organizowaæ dokumenty
WWW, weblogi, bazy wiedzy lub dowolne inne struktury dokumentów
bezpo¶rednio w przegl±darce HTML. Mo¿na rozwijaæ idee i otrzymywaæ
towarzysz±c± dokumentacjê XML burzy mózgów bez potrzeby koncentrowania
siê na skomplikowanej sk³adni strukturalnej.

%package setup
Summary:	coWiki setup package
Summary(pl):	Pakiet do wstêpnej konfiguracji coWiki
Group:		Applications/WWW
Requires:	%{name} = %{epoch}:%{version}-%{release}

%description setup
Install this package to configure initial coWiki installation. You
should uninstall this package when you're done, as it considered
insecure to keep the setup files in place.

%description setup -l pl
Ten pakiet nale¿y zainstalowaæ w celu wstêpnej konfiguracji coWiki po
pierwszej instalacji. Potem nale¿y go odinstalowaæ, jako ¿e
pozostawienie plików instalacyjnych mog³oby byæ niebezpieczne.

%prep
%setup -q %{?_snap:-n %{name}-%{version}-interim-%{_snap}}
%patch0 -p1
%patch1 -p1

mv includes/cowiki/core.conf-dist .
rm {htdocs,includes/cowiki}/.cvsignore
mv htdocs/.htaccess .
rm htdocs/setup/LICENSE # GPL

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_appdir},%{_sysconfdir},/var/cache/%{name}}

cp -a htdocs includes misc $RPM_BUILD_ROOT%{_appdir}
install core.conf-dist $RPM_BUILD_ROOT%{_sysconfdir}/core.conf
install %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/apache.conf
install %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/httpd.conf

# for setup
install LICENSE $RPM_BUILD_ROOT%{_appdir}/htdocs/setup
install core.conf-dist $RPM_BUILD_ROOT%{_appdir}/includes/cowiki/core.conf-dist
touch $RPM_BUILD_ROOT%{_appdir}/htdocs/install.seal

%clean
rm -rf $RPM_BUILD_ROOT

%post
if [ "$1" = 1 ]; then
%banner %{name} -e <<EOF
Install the database using the appropriate "misc/database/*.sql" schema.
You must setup authorization and coWiki root password in:
- %{_sysconfdir}/core.conf

EOF
fi

%preun
if [ "$1" = "0" ]; then
	# nuke cache
	# FIXME could suffer too many arguments error
	rm -f /var/cache/%{name}/*
fi

%post setup
chgrp http %{_appdir}/{htdocs/include.path,htdocs,includes/cowiki}
chmod g+w %{_appdir}/{htdocs/include.path,htdocs,includes/cowiki}
rm -f %{_appdir}/htdocs/install.seal

%postun setup
if [ "$1" = "0" ]; then
	chgrp root %{_appdir}/{htdocs/include.path,htdocs,includes/cowiki}
	chmod g-w %{_appdir}/{htdocs/include.path,htdocs,includes/cowiki}
	touch %{_appdir}/htdocs/install.seal
fi

%triggerin -- apache1
%webapp_register apache %{_webapp}

%triggerun -- apache1
%webapp_unregister apache %{_webapp}

%triggerin -- apache < 2.2.0, apache-base
%webapp_register httpd %{_webapp}

%triggerun -- apache < 2.2.0, apache-base
%webapp_unregister httpd %{_webapp}

# cache dir moved
%triggerun -- %{name} < 0.4.0-0.20050618.3
# FIXME could suffer too many arguments error
rm -f /var/lib/%{name}/*

%triggerpostun -- %{name} < 0.4.0-0.20060206.0.2
# rescue app config
if [ -f /etc/%{name}/core.conf.rpmsave ]; then
	mv -f %{_sysconfdir}/core.conf{,.rpmnew}
	mv -f /etc/%{name}/core.conf.rpmsave %{_sysconfdir}/core.conf
fi
# migrate from apache-config macros
if [ -f /etc/%{name}/apache.conf.rpmsave ]; then
	if [ -d /etc/apache/webapps.d ]; then
		cp -f %{_sysconfdir}/apache.conf{,.rpmnew}
		cp -f /etc/%{name}/apache.conf.rpmsave %{_sysconfdir}/apache.conf
	fi

	if [ -d /etc/httpd/webapps.d ]; then
		cp -f %{_sysconfdir}/httpd.conf{,.rpmnew}
		cp -f /etc/%{name}/apache.conf.rpmsave %{_sysconfdir}/httpd.conf
	fi
	rm -f /etc/%{name}/apache.conf.rpmsave
fi

# migrating from earlier apache-config?
if [ -L /etc/apache/conf.d/99_%{name}.conf ]; then
	rm -f /etc/apache/conf.d/99_%{name}.conf
	/usr/sbin/webapp register apache %{_webapp}
	%service -q apache reload
fi
if [ -L /etc/httpd/httpd.conf/99_%{name}.conf ]; then
	rm -f /etc/httpd/httpd.conf/99_%{name}.conf
	/usr/sbin/webapp register httpd %{_webapp}
	%service -q httpd reload
fi

%files
%defattr(644,root,root,755)
%doc ChangeLog INSTALL* NEWS
%doc README.IDIOM README.PLUGIN SKEL.PLUGIN
%doc misc/database
%dir %attr(750,root,http) %{_sysconfdir}
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/apache.conf
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/httpd.conf
%attr(640,root,http) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/core.conf

%dir %{_appdir}
%{_appdir}/misc
%dir %{_appdir}/includes
%dir %{_appdir}/includes/cowiki
%{_appdir}/includes/cowiki/class
%{_appdir}/includes/cowiki/locale
%{_appdir}/includes/cowiki/plugin
%{_appdir}/includes/cowiki/*.php
%dir %{_appdir}/htdocs
%{_appdir}/htdocs/img
%{_appdir}/htdocs/tpl
%{_appdir}/htdocs/*.txt
%{_appdir}/htdocs/*.php
%{_appdir}/htdocs/favicon.ico
%{_appdir}/htdocs/include.path

%dir %attr(770,root,http) /var/cache/%{name}

# setup seal
%config(noreplace,missingok) %verify(not md5 mtime size) %{_appdir}/htdocs/install.seal

%files setup
%defattr(644,root,root,755)
%{_appdir}/htdocs/setup
%{_appdir}/htdocs/install.pending
%{_appdir}/includes/cowiki/core.conf-dist
