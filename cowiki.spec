# TODO
#  - lighttpd integration possible <http://wiki.lighttpd.net/33.html>.

# snapshot: DATE
%define _snap 2005-02-20

%if 0%{?_snap}
%define _source http://snaps.cowiki.org/%{name}-%{version}-dev-%{_snap}.tar.gz
%else
%define _source http://cowiki.org/download/%{name}-%{version}.tar.gz
%endif
%define _rel 0.20

Summary:	Web collaboration tool
Name:		cowiki
Version:	0.3.4
Release:	%{?_snap:0.%(echo %{_snap} | tr -d -).}%{_rel}
Epoch:		0
License:	GPL
Group:		Applications/WWW
Source0:	%{_source}
# Source0-md5:	6351667cdfbf3b6e8937af855a4414ba
Patch0:		%{name}-FHS.patch
URL:		http://cowiki.org/
BuildRequires:	rpmbuild(macros) >= 1.177
Requires:	php >= 5.0.2
Requires:	php-mysql
BuildArch:	noarch
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%define		_appdir %{_datadir}/%{name}
%define		_sysconfdir	/etc/%{name}
%define		_apache1dir	/etc/apache
%define		_apache2dir	/etc/httpd

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

%prep
%setup -q %{?_snap:-n %{name}-%{version}-dev-%{_snap}}
%patch0 -p1

mv includes/cowiki/core.conf-dist .
rm -f {htdocs,includes/cowiki}/.cvsignore
mv htdocs/.htaccess .

%install
rm -rf $RPM_BUILD_ROOT
install -d $RPM_BUILD_ROOT{%{_appdir},%{_sysconfdir},/var/lib/%{name}}

cp -a htdocs includes $RPM_BUILD_ROOT%{_appdir}

sed -e '
    s,CHECK_INTERVAL = .*,CHECK_INTERVAL = "-1",
    s,RETURN_PATH = .*,RETURN_PATH = "your.bounce.email@localhost",
    s,ABUSE_PATH = .*,ABUSE_PATH = "abuse@localhost",
    s,ROOT_PASSWD = .*,ROOT_PASSWD = "XXX",
    s,LOOKUP_DNS = .*,LOOKUP_DNS = off,
    s,TEMP = .*,TEMP = "/var/lib/%{name}/",

' core.conf-dist > $RPM_BUILD_ROOT%{_sysconfdir}/core.conf
echo -e '\n; vim: ft=dosini' >> $RPM_BUILD_ROOT%{_sysconfdir}/core.conf

# unfortunately cowiki works only as vhost root
cat <<EOF >> $RPM_BUILD_ROOT%{_sysconfdir}/apache.conf
<Directory /usr/share/cowiki/htdocs>
    Allow from all
</Directory>

<VirtualHost *>
	ServerName cowiki
	DocumentRoot /usr/share/cowiki/htdocs

EOF
sed -ne '/BEGIN/,/END/p' .htaccess >> $RPM_BUILD_ROOT%{_sysconfdir}/apache.conf
cat <<EOF >> $RPM_BUILD_ROOT%{_sysconfdir}/apache.conf
</VirtualHost>
EOF

%clean
rm -rf $RPM_BUILD_ROOT

%post
# apache1
if [ -d %{_apache1dir}/conf.d ]; then
	ln -sf %{_sysconfdir}/apache.conf %{_apache1dir}/conf.d/99_%{name}.conf
	if [ -f /var/lock/subsys/apache ]; then
		/etc/rc.d/init.d/apache restart 1>&2
	fi
fi
# apache2
if [ -d %{_apache2dir}/httpd.conf ]; then
	ln -sf %{_sysconfdir}/apache.conf %{_apache2dir}/httpd.conf/99_%{name}.conf
	if [ -f /var/lock/subsys/httpd ]; then
		/etc/rc.d/init.d/httpd restart 1>&2
	fi
fi

if [ "$1" = 1 ]; then
%banner %{name} -e <<EOF
Install the database using the appropriate "misc/database/*.sql" schema.
You must setup authorization and root password in:
- %{_sysconfdir}/core.conf

EOF
fi

%preun
if [ "$1" = "0" ]; then
	# apache1
	if [ -f %{_apache1dir}/apache.conf ]; then
		rm -f %{_apache1dir}/conf.d/99_%{name}.conf
		if [ -f /var/lock/subsys/apache ]; then
			/etc/rc.d/init.d/apache restart 1>&2
		fi
	fi
	# apache2
	if [ -d %{_apache2dir}/httpd.conf ]; then
		rm -f %{_apache2dir}/httpd.conf/99_%{name}.conf
		if [ -f /var/lock/subsys/httpd ]; then
			/etc/rc.d/init.d/httpd restart 1>&2
		fi
	fi

	# nuke cache
	# FIXME could suffer too many arguments error
	rm -f /var/lib/%{name}/*
fi

%files
%defattr(644,root,root,755)
%doc ChangeLog INSTALL* NEWS 
%doc README.IDIOM README.PLUGIN SKEL.PLUGIN
%doc misc/database
%dir %{_sysconfdir}
%attr(640,root,root) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/apache.conf
%attr(640,root,http) %config(noreplace) %verify(not md5 mtime size) %{_sysconfdir}/core.conf
%{_appdir}
%dir %attr(770,root,http) /var/lib/%{name}
