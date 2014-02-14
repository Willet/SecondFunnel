package { 
  'mysql-server': ensure => present;
  'libmysqlclient-dev': ensure => present;
  'git': ensure => present;
}

# Python
class python {
    package {
        "build-essential": ensure => latest;
        "python": ensure => installed;
        "python-dev": ensure => installed;
        "python-setuptools": ensure => installed;
	"libxml2-dev": ensure => installed;
        "libxslt-dev": ensure => installed;
        "libjpeg-dev": ensure => installed;
    }
    exec { "easy_install pip":
        path => "/usr/local/bin:/usr/bin:/bin",
        refreshonly => true,
        require => Package["python-setuptools"],
        subscribe => Package["python-setuptools"],
    }
     
    exec { "pip-install-req":
        command => "pip install -r /vagrant/requirements/dev.txt",
        path => "/usr/local/bin:/usr/bin:/bin",
        require => Package['git','mysql-server','libmysqlclient-dev', 'libxml2-dev', 'libxslt-dev'],
    }

    # in case we want to move pip dependencies in here
    #package {
    #    "django": ensure => "1.4.1",provider => pip;
    #    "ordereddict": ensure => "1.1",provider => pip;
    #    "fabric": ensure => "1.6.0",provider => pip;
    #}
}
class { "python": }

package { 'bundler':
  ensure   => 'installed',
  provider => 'gem',
}

exec { 'bundle install':
  command => 'bundle install',
  path => '/opt/vagrant_ruby/bin',
  cwd => '/vagrant',
  logoutput => true,
  require => Package['bundler'],
}

# Apache http://stackoverflow.com/questions/15263337/ubuntu-10-04-puppet-and-apache-apache-service-failing-to-start
package { 'apache2':
  ensure => present,	
}
service { 'apache2':
  ensure  => running,
  enable  => true,
  require => Package['apache2'],
}

# POSTGRESQL
# https://forge.puppetlabs.com/puppetlabs/postgresql
class { 'postgresql::server': 
  postgres_password  => 'postgres',
  pg_hba_conf_defaults => false,
}

postgresql::server::pg_hba_rule { 'local-ident':
  description => "Let postgres user login via ident",
  type => 'local',
  database => 'all',
  user => 'postgres',
  auth_method => 'ident',
  order => '001',
}

postgresql::server::pg_hba_rule { 'local-md5':
  description => "Open up postgresql for access with a password via unix sockets",
  type => 'local',
  database => 'all',
  user => 'all',
  auth_method => 'md5',
  order => '002',
}

postgresql::server::pg_hba_rule { 'host-md5':
  description => "Open up postgresql for access with a password via IPv4",
  type => 'host',
  database => 'all',
  user => 'all',
  auth_method => 'md5',
  address => '0.0.0.0/0',
  order => '003',
}

# COMMON
exec { "apt-update":
  command => "/usr/bin/apt-get update"
}

Exec["apt-update"] -> Package <| |>

