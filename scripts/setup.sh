#!/bin/bash
# setup script for ubuntu 12.04+, Mint Linux*, Mac OSX10.5+
# * - should work on Mint Linux and Debian

OS=`uname`
AWSOS=''
HOME=~
if [ ${OS} = "Darwin" ]; then
    # We'll use 'brew' for Mac users
    ruby -e "$(curl -fsSL https://raw.github.com/mxcl/homebrew/go)"    
    brew install python2.7 git
    brew install mysql pip
    AWS_OS="macosx"
elif [ ${OS} = "Linux" ]; then
    if [ `whoami` != "root" ]; then
        echo "ERROR: This script must be run as root or with sudo."
        exit 1
    fi
    apt-get install git-core python2.7
    apt-get install python-pip python-dev build-essential libmysqlclient-dev libxslt1.1 libxslt1-dev python-pyopenssl
    AWS_OS="linux"
else
    echo "ERROR: Operating system, ${OS}, not supported."
    exit 1
fi

# commands that are common across both OS
export WORKON_HOME="~/Envs"
export PROJECT_NAME="SecondFunnel"
mkdir -p $WORKON_HOME

cd $WORKON_HOME
git clone --recursive git@github.com/Willet/SecondFunnel.git $PROJECT_NAME

sudo pip install virtualenv
sudo pip install virtualenvwrapper

source /usr/local/bin/virtualenvwrapper
mkvirtualenv $PROJECT_NAME -p $(which python2.7)

# Add lines to our profile
echo ' ' >> ~/.bash_profile
echo '# Workon is virtualenv-wrapper specific, so we source it to allow the current user' >> ~/.bash_profile
echo '# to use it.' >> ~/.bash_profile
echo 'source /usr/local/bin/virtualenvwrapper.sh' >> ~/.bash_profile
echo 'export WORKON_HOME=~/Envs' >> ~/.bash_profile


# fix permissions (grant to original user)
USER=$(whoami | awk '{print $1}')
chown -R $USER:$USER $WORKON_HOME/$PROJECT_NAME

#add postactivates
echo 'export GEM_HOME="$VIRTUAL_ENV/gems"' >> $WORKON_HOME/postactivate
echo 'export GEM_PATH=""' >> $WORKON_HOME/postactivate
echo 'export PATH=$PATH:$GEM_HOME/bin' >> $WORKON_HOME/postactivate

cd $WORKON_HOME/$PROJECT_NAME
source $WORKON_HOME/$PROJECT_NAME/bin/activate

# pips
sudo pip install -r $WORKON_HOME/$PROJECT_NAME/requirements/dev.txt

#ruby
gem install bundler
bundle install

# rabbitmq
if [ ${OS} = "Darwin" ]; then
    brew install rabbitmq
elif [ ${OS} = "Linux" ]; then
    URL='http://www.rabbitmq.com/releases/rabbitmq-server/v3.1.1/rabbitmq-server_3.1.1-1_all.deb'
    FILE=`mktemp` ;
    wget "$URL" -qO $FILE && dpkg -i $FILE
    rm $FILE
fi

# AWS Beanstalk CLI
cd $WORKON_HOME/$PROJECT_NAME/
mkdir .AWS-ElasticBeanstalk-CLI
cd .AWS-ElasticBeanstalk-CLI
curl "https://s3.amazonaws.com/elasticbeanstalk/cli/AWS-ElasticBeanstalk-CLI-2.4.0.zip" -o AWS_CLI.zip
unzip AWS-CLI.zip > /dev/null
rm AWS-CLI.zip
cp -r AWS-ElasticBeanstalk-CLI-2.4.0/* .
echo "export PATH=$PATH:$WORKON_HOME/$PROJECT_NAME/.AWS-ElasticBeanstalk-CLI/eb/'"$AWS_OS"'/python2.7/" >> $WORKON_HOME/postactivate
source $WORKON_HOME/$PROJECT_NAME/bin/activate
cd ..
cp -r .AWS-ElasticBeanstalk-CLI/AWSDevTools/Linux/scripts/* scripts/
cp .AWS-ElasticBeanstalk-CLI/AWSDevTools/Linux/AWSDevTools-RepositorySetup.sh .
sh AWSDevTools-RepositorySetup.sh
rm AWSDevTools-RepositorySetup.sh
if [ ! -d "$HOME/.ssh" ]; then
    # User needs an ssh key                                                                                                                                                       
    echo "Enter your email address: "
    read emailaddr
    ssh-keygen -t rsa -C "$emailaddr"
fi
cat ~/.ssh/id_rsa.pub >> ssh_keys

# re-fix
chown -R $USER:$USER $WORKON_HOME/$PROJECT_NAME

# Finalize AWS setup
echo 'AWSAccessKeyId = ACCESS_KEY' >> aws_credential_file
echo 'AWSSecretKey = SECRET_KEY' >> aws_credential_file
echo 'secondfunnel-dev_RdsMasterPassword = gfhjkmlkzHLC' >> aws_credential_file
git aws.config

# make sure everything is working
eb status
python manage.py syncdb && python manage.py migrate && python manage.py collectstatic

# Theming
cd $WORKON_HOME
git clone git@github.com/Willet/SecondFunnel-Themes.git
chown -R $USER:$USER $WORKON_HOME/SecondFunnel-Themes
cd $PROJECT_NAME
echo "$WORKON_HOME/SecondFunnel-Themes" | python manage.py theming

# Fixtures
fixtures = ( "./apps/assets/fixtures/init_dev.json" "./apps/pinpoint/fixtures/init_dev.json" "./secondfunnel/fixtures/init_dev.json" "apps/analytics/fixtures/data.json" )
for fixture in "${fixtures[@]}"
do
    python manage.py loaddata fixture
done

# Finalize and Done
cp scripts/runserver.sh runserver
echo "Setup complete."