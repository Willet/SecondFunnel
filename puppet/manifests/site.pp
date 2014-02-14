package {
  ['mysql-server', 'libmysqlclient-dev', 'git']: 
  ensure => present;
}

# Python
class python {
  package { 'build-essential': ensure => latest }
  
  package {
    [
      'python', 
      'python-dev', 
      'python-setuptools', 
      'libxml2-dev', 
      'libxslt-dev', 
      'libjpeg-dev',
    ]: 
    ensure => installed,
    require => Package['build-essential'],
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
}
class { "python": }

# Ruby
package { 'bundler':
  ensure   => 'installed',
  provider => 'gem',
}

exec { 'bundle install':
  command => 'bundle install',
  path => '/usr/local/bin',
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

postgresql::server::role { 'vagrant':
  createdb => true,
}

postgresql::server::pg_hba_rule { 'local-ident-postgres':
  description => "Let postgres user login via ident",
  type => 'local',
  database => 'all',
  user => 'postgres',
  auth_method => 'ident',
  order => '001',
}

postgresql::server::pg_hba_rule { 'local-ident-vagrant':
  description => "Let vagrant user login via ident",
  type => 'local',
  database => 'all',
  user => 'vagrant',
  auth_method => 'ident',
  order => '002',
}

postgresql::server::pg_hba_rule { 'local-md5':
  description => "Open up postgresql for access with a password via unix sockets",
  type => 'local',
  database => 'all',
  user => 'all',
  auth_method => 'md5',
  order => '005',
}

postgresql::server::pg_hba_rule { 'host-md5':
  description => "Open up postgresql for access with a password via IPv4",
  type => 'host',
  database => 'all',
  user => 'all',
  auth_method => 'md5',
  address => '0.0.0.0/0',
  order => '010',
}

# COMMON
exec { "apt-update":
  command => "/usr/bin/apt-get update"
}

Exec["apt-update"] -> Package <| |>
