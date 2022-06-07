echo_time() {
    echo "$(date +%F_%T) $*"
}

# Paths
: ${SOURCE_PATH:=$HOME/wikiloves}
: ${TOOLFORGE_PATH:=$HOME/www/python/}
: ${VIRTUAL_ENV_PATH:=$TOOLFORGE_PATH/venv-bastion}
: ${APP_PATH:=$TOOLFORGE_PATH/src}
